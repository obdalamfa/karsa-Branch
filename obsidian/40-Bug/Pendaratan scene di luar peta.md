---
judul: Pendaratan scene di luar peta
tipe: bug
status: selesai
ditemukan: 2026-08-26
ditemukan_oleh: tools/regress.py (larian pertama)
commit_perbaikan: 126cea8
dijaga_oleh: pemain_valid
tags: [bug, scene, status/selesai]
---

# 🐞 Pendaratan scene di luar peta

**Bug pertama yang ditemukan [[Regresi]], pada larian pertamanya.**

## Gejala

Masuk `house` atau `shop` mendaratkan pemain di **(19,5)** — padahal `house`
cuma **15 kolom**.

## Sebab

Koordinat dibawa **apa adanya** lintas scene, dan pencarian pengaman yang lama
hanya melebar radius 5 — tidak pernah sampai ke tepi peta. Kalau koordinat
asalnya sudah di luar peta tujuan, radius 5 tidak akan menemukan apa pun.

Ini **akar** dari gejala yang sebelumnya cuma ditambal di sisi pemain
([[Terjepit permanen]]).

## Perbaikan

`_land_player_safely()`:

1. **jepit** koordinat ke batas peta dulu,
2. baru cari **cincin demi cincin** selebar peta.

Dipakai bersama oleh pendaratan awal **dan** transisi scene — menggantikan dua
salinan kode yang berbeda. Dua salinan yang berbeda untuk satu urusan adalah
bug yang menunggu giliran.

## Bukti

5/5 scene lulus. Pendaratan sesudah perbaikan: `house` (13,4), `shop` (12,3),
`lake` (13,3).

## Tautan

[[2026-08-26 — Tahap 1 jaring pengaman regresi]] · [[Tahap 1 — Jaring pengaman]]
