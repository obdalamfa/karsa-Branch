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

## Alat ukur yang sudah ada

- `tools/regress.py` mencatat **ms per frame** per scene → [[Regresi]]. Angkanya ada supaya regresi performa **terlihat**, bukan cuma terasa.
- Probe di `_bench/probes/` (gitignored) sudah dipakai untuk mengukur avatar: 0,288 ms native lawan 6,387 ms Python → [[Avatar Vitaboy]]. Itu contoh bentuk pengukuran yang diharapkan di tahap ini.

## Yang sudah mengurangi beban tanpa diniatkan

- Cache warna kabut di `app.py`, menghindari setter Ursina yang mahal tiap frame ([[2026-08-27 — Tata letak, avatar native, tukang mesh]]).
- Jalur avatar native Panda3D — 22× lebih murah per frame.

## Tautan

[[Status Sekarang]] · [[Tahap 4 — Wishes]]
