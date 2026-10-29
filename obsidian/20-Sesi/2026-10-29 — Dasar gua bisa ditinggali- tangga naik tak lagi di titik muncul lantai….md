---
judul: "Dasar gua bisa ditinggali: tangga naik tak lagi di titik muncul lantai 13"
tipe: sesi
tanggal: 2026-10-29
commit: 184931c
skala: 3 file sumber, +36 / −8 baris
tags: [sesi]
---

# 2026-10-29 — Dasar gua bisa ditinggali: tangga naik tak lagi di titik muncul lantai 13

## Pesan commit

Arena Bhutakala menaruh STAIRS_UP tepat di titik muncul (12,15). Begitu
cooldown portal 0,5 detik habis (frame muat lantai baru sendiri sering
lebih panjang), pemain yang diam terlempar balik ke lantai 12: terukur
0,62-0,83 detik sesudah tiba. Ditemukan probe lore gua, yang naik-turun
ulangnya ternyata berangkat dari lantai 12.

- dungeon.py: STAIRS_UP satu ubin di belakang titik muncul, (12,16),
  seperti lantai lain yang sudah memisahkan keduanya.
- probe_lore_gua: cek "pemain yang diam di lantai 13 tetap di sana
  (3 dtk)". GAGAL sebelum perbaikan, LULUS sesudahnya; 19/19.

Regresi penuh 14/14 scene, 0 pemeriksaan gagal, "lore gua" 19/19.

## Berkas yang berubah

| Berkas | + | − |
|---|---:|---:|
| `game/dungeon.py` | +6 | −2 |
| `tools/probe_lore_gua.py` | +26 | −5 |
| `tools/regress.py` | +4 | −1 |

## Bukti

> [!info] Ditemukan saat mengerjakan lore gua, lalu diperbaiki atas pilihan
> pemilik: "Ya, commit terpisah".

- Pantulan diukur sebelum diperbaiki, dua kali, lewat tangga sungguhan:
  - skrip cek sekali pakai (tanpa jendela, turun 12→13): pemain berdiri di
    (12,15), yang ternyata STAIRS_UP, lalu diam dan pindah ke lantai 12
    sesudah 0,83 dtk;
  - `probe_lore_gua.py` dengan cek baru, sebelum perbaikan: 18/19, GAGAL
    "terpantul ke lantai 12 setelah 0.62 dtk".
- Sesudah 184931c: probe 19/19. Naik-turun ulang kembali berangkat dari
  lantai 13 (13→12→13), bukan dari 12.
- Regresi penuh: 14/14 scene, 0 pemeriksaan gagal, "lore gua" 19/19
  (9 mnt 47 dtk).

## Yang belum beres

- Cooldown portal 0,5 detik tetap bisa habis dalam satu frame muat yang
  panjang. Arena lantai 13 satu-satunya tempat di gua yang mendaratkan
  pemain di atas tangga, jadi pantulannya hilang, tapi cooldown-nya sendiri
  tetap rapuh untuk portal mana pun yang kelak mendaratkan pemain di atas
  ubin portal.

## Tautan

[[Status Sekarang]] · [[Peta Progres]] · [[Pemain terpantul dari dasar gua]] · [[Regresi]]
