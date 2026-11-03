---
judul: "\"Ya, berikan.\" tidak pernah menyerahkan hadiah"
tipe: bug
status: selesai
ditemukan: "2026-10-29"
commit_perbaikan: (lihat nota sesi 2026-10-30, Cerita Dua Desa babak 1-2 masuk PR #15)
dijaga_oleh: belum ada baris di tools/regress.py; baru harness di luar repo (uji_dua_desa.py)
tags: [bug, status/selesai, gameplay, dialog]
---

# 🐞 "Ya, berikan." tidak pernah menyerahkan hadiah

## Gejala

Beri Hadiah di menu warga membuka dialog "Beri 1 … sebagai hadiah ke …?".
Memilih "Ya, berikan." menjawab "Hadiah berhasil diberikan!", tapi barangnya
tetap di tas dan hati warga tidak bertambah. Hadiah yang sama bisa "diberikan"
berulang-ulang.

## Sebab

Pilihan "Ya, berikan." di node `gift_confirm` (`game/data.py`) hanya punya
`'next': 'gift_yes'`, tanpa efek apa pun. Pekerjaannya ada di
`InteractionController.complete_gift_gifting`, yang mengurangi barang dan
menambah hati, dan dibungkus `Player.complete_gift_gifting`. Tapi method itu
tidak punya pemanggil: `git grep complete_gift_gifting 3d51c68 -- game` hanya
menemukan dua definisinya. Ini aturan 4 di `CLAUDE.md` (modul tanpa pemanggil =
efeknya nol), dalam bentuk satu method.

Ditemukan 2026-10-29 saat menguji barang favorit Cerita Dua Desa babak 1.
Hadiah favorit tidak mungkin terbukti karena hadiah biasa pun tidak pernah
sampai.

## Perbaikan

- "Ya, berikan." kini membawa efek `serahkan_hadiah`. `UIManager` (efek
  dialog di `game/panels.py`) menjalankannya dengan memanggil
  `complete_gift_gifting`.
- `give_gift` menyimpan `(npc_id, barang)` di `_hadiah_tertunda`, jadi barang
  yang diserahkan persis barang yang ditanyakan di dialog.
- Barang favorit (`favorit` di data warga) bernilai tiga kali hadiah biasa.

## Bukti

Harness `uji_dua_desa.py` memilih hadiah lewat pie dan tombol sungguhan di
PR #15 (37/37 lulus):

- Ikan ke Sekar (favorit): ikan 1 → 0, hati 0 → 3,1.
- Jagung (kesukaan biasa): hati 3,1 → 4,2.
- Warga lama ikut jalan: Arya 0 → 1,1.

Tambahan +0,1 datang dari `_end_dialog`, yang memberi +0,1 hati untuk tiap
dialog yang selesai (perilaku lama).

## Yang menjaganya sekarang

**Belum ada baris di `tools/regress.py`.** Yang memeriksanya baru harness di
luar repo (folder catatan sesi), jadi bug ini bisa kambuh tanpa ketahuan
sampai baris regresinya ditulis → [[Regresi]].

## Tautan

[[Status Sekarang]]
