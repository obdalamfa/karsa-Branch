---
judul: "Pemain terpantul dari dasar gua"
tipe: bug
status: selesai
ditemukan: "2026-10-29"
commit_perbaikan: 184931c
dijaga_oleh: tools/probe_lore_gua.py (regresi, baris "lore gua")
tags: [bug, status/selesai, gua]
---

# 🐞 Pemain terpantul dari dasar gua

## Gejala

Tiba di lantai 13 (arena Bhutakala) lalu diam: pemain langsung dikembalikan
ke lantai 12 yang baru diacak. Hanya pemain yang masih menahan tombol gerak
saat tiba yang bisa tinggal.

## Sebab (diukur)

`generate_dungeon_level(13)` menaruh `STAIRS_UP` tepat di titik muncul
(12,15). Sesudah ganti scene `app.py` memberi cooldown portal 0,5 detik,
tapi frame muat lantai baru sendiri sering lebih panjang dari itu. Begitu
cooldown habis, `_check_portals` membaca tangga di bawah kaki pemain.

Terukur dua kali: pemain diam terpantul 0,83 detik sesudah tiba (skrip cek
sekali pakai, tanpa jendela) dan 0,62 detik (`probe_lore_gua.py`, jendela
sungguhan). Lantai lain memisahkan titik muncul dan tangga
(`up_y = spawn_y - 1`), jadi hanya dasar gua yang kena.

Ditemukan tanpa sengaja: probe lore gua yang naik-turun dari lantai 13
ternyata naik dari lantai 12.

## Perbaikan (184931c)

`STAIRS_UP` dipindah satu ubin di belakang titik muncul, ke (12,16).

## Yang menjaganya sekarang

Cek "pemain yang diam di lantai 13 tetap di sana (3 dtk)" di
`tools/probe_lore_gua.py`, baris "lore gua" di [[Regresi]]. Sebelum
perbaikan GAGAL ("terpantul ke lantai 12 setelah 0.62 dtk"), sesudahnya
LULUS, dan naik-turun ulang kembali berjalan 13→12→13.

## Tautan

[[Catatan gua tanpa isi dan fragmen III di lantai 14]] · [[Dungeon dan Combat]]
