---
judul: Tahap 3 — Performa
tipe: tahap
nomor: 3
status: belum
ringkas: 4–29 FPS, belum pernah diprofil, jumlah entity terus naik
tags: [tahap, status/belum, performa]
---

# Tahap 3 — Performa ⬜

4–29 FPS, **belum pernah diprofil**, dan jumlah entity terus naik — 1126 entity
tercatat di kandang. Setiap perbaikan visual sejauh ini dinikmati lewat
slideshow, bukan lewat game yang berjalan.

## Dua jalan

1. **Optimasi bertahap** — batching, culling, kurangi entity. Aman, bisa diukur langkah demi langkah.
2. **Perombakan renderer** — berisiko, membalik banyak keputusan.

Mulai dari yang pertama **sambil mengukur**. Kalau mentok di bawah 30 FPS, itu
keputusan besar tentang seberapa jauh Ursina sanggup dibawa — dan itu keputusan
pemilik, bukan keputusan agen.

## Garis dasar pertama — 2026-09-22

Untuk pertama kalinya ada angka per scene, lengkap dengan jumlah entity:

| scene | ms/frame | entity |   | scene | ms/frame | entity |
|---|---:|---:|---|---|---:|---:|
| mountain | 119,6 | 2177 |   | greenhouse | 53,9 | 488 |
| town | 102,6 | 1884 |   | shop | 49,5 | 405 |
| farm | 96,8 | 1257 |   | studio | 47,3 | 384 |
| beach | 84,2 | 1728 |   | smith | 47,2 | 385 |
| naga_cave | 82,2 | 530 |   | clinic | 46,6 | 385 |
| lake | 72,3 | 686 |   | house | 46,4 | 418 |
| swarga | 71,9 | 1379 |   | | | |
| cemetery | 70,5 | 983 |   | | | |

> [!warning] Ini dirender CPU, bukan GPU
> Runner tidak punya GPU; Mesa merender lewat perangkat lunak. Angka-angka ini
> **tidak** boleh dipakai untuk mengklaim FPS, dan tidak sebanding dengan 4–29
> FPS di mesin pemilik. Gunanya dua: melihat **tren** antar-commit lewat CI,
> dan melihat **urutan relatif** antar-scene.

Yang sudah bisa dibaca dari sini, dan berlaku di mesin mana pun: biaya frame
naik mengikuti jumlah entity. `mountain` (2177 entity) 2,6× lebih mahal
daripada `house` (418 entity). Jadi jalan optimasi pertama yang masuk akal
bukan mengganti renderer, melainkan **mengurangi jumlah entity** — batching dan
culling menyerang persis sumbu ini.

## Alat ukur yang sudah ada

- `tools/regress.py` mencatat **ms per frame** per scene → [[Regresi]], dan sejak 2026-09-22 ia jalan otomatis di CI tiap push, jadi tren performa terekam sendiri tanpa ada yang perlu ingat mengukurnya.
- Probe di `_bench/probes/` (gitignored) sudah dipakai untuk mengukur avatar: 0,288 ms native lawan 6,387 ms Python → [[Avatar Vitaboy]]. Itu contoh bentuk pengukuran yang diharapkan di tahap ini.

## Yang sudah mengurangi beban tanpa diniatkan

- Cache warna kabut di `app.py`, menghindari setter Ursina yang mahal tiap frame ([[2026-08-27 — Tata letak, avatar native, tukang mesh]]).
- Jalur avatar native Panda3D — 22× lebih murah per frame.

## Tautan

[[Status Sekarang]] · [[Tahap 4 — Wishes]]
