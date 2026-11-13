---
judul: "Catatan gua tanpa isi dan fragmen III di lantai 14"
tipe: bug
status: selesai
ditemukan: "2026-10-29"
commit_perbaikan: 06d5587
dijaga_oleh: tools/probe_lore_gua.py (regresi, baris "lore gua")
tags: [bug, status/selesai, gua, lore]
---

# 🐞 Catatan gua tanpa isi dan fragmen III di lantai 14

Lima cacat bertumpuk di lore gua bertingkat, dan tidak satu pun melempar
error. Crash `s.lore_found` yang dicatat `docs/CODE_MAP.md` (2026-08-21)
sudah diperbaiki lebih dulu. Sisanya baru terlihat saat probe benar-benar
turun lewat tangga.

## Gejala

Tiba di lantai 3, 7, dan 12 tidak memunculkan apa-apa. Panel Catatan [N]
lalu memuat `[dungeon_3]`, `[dungeon_7]`, dan `[dungeon_12]` tanpa isi.
Fragmen Prasasti III tidak pernah bisa didapat.

## Sebab (diukur dengan probe_lore_gua.py di 630c805: 10/17)

1. `check_dungeon_lore` mencatat id `dungeon_3/7/12` ke `lore_collected`, tapi
   id itu tidak punya entri `LORE_ITEMS`. Panel jatuh ke id mentah tanpa teks.
2. Tabel `FRAGMEN_GUA` menaruh fragmen III di lantai 14. `DUNGEON_MAX_LEVEL`
   adalah 13, jadi lantai itu tidak pernah dibuat.
3. Tangga memanggil `check_dungeon_lore` tanpa `panels`. Pesannya masuk
   `_pending_lore_msg`, yang baru disampaikan sesudah tidur, dan lantai
   berikutnya menimpanya lebih dulu: pesan lantai 3 sudah tergantikan di
   lantai 5. Pesan lamanya juga 80–100 huruf dalam satu baris.
4. Panel [N] memotong mati di baris 28. Dengan sembilan catatan koleksi
   lengkap butuh 39 baris, dan yang terpotong justru yang terbaru.
5. Flash "[N] Catatan baru" tetap menutupi panel yang dibuka untuk membacanya.

## Perbaikan (06d5587)

- `found_at` jadi satu-satunya sumber: `check_dungeon_lore` memberikan semua
  `LORE_ITEMS` ber-`found_at` `dungeon_<lantai>`. `FRAGMEN_GUA` dihapus.
- Tiga entri `LORE_ITEMS` baru dengan id lama, karena save yang sudah ada
  menyimpan id itu: Prasasti Kutukan, Buku Harian Penambang, dan Dinding
  Bercahaya.
- Fragmen III pindah ke lantai 13, arena Bhutakala dengan danau legendaris.
- `app.py` menyampaikan pesan tertunda sesudah scene baru termuat. Isinya
  judul ditambah isi catatan, dibungkus 48 huruf; lebarnya terukur 0,32–0,36
  lebar layar.
- Panel [N] berhalaman tanpa membelah catatan, dibuka di halaman terbaru, dan
  pindah halaman dengan Q/R. Flash yang menutupinya disingkirkan.

## Yang menjaganya sekarang

`tools/probe_lore_gua.py`, baris "lore gua" di [[Regresi]]. Di 630c805:
10/17, dengan tujuh GAGAL yang masing-masing satu cacat di atas. Sesudah
perbaikan: lulus semua.

## Tautan

[[Dungeon dan Combat]] · [[Pemain terpantul dari dasar gua]]
