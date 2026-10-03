---
judul: Tata Letak Scene
tipe: sistem
modul: game/scenes/layout.py, game/scenes/zone_paint.py
baris: 123 + 199
status: jalan
tags: [sistem, tata-letak, status/jalan]
---

# Tata Letak Scene — peta yang bisa dibaca dari kodenya

`game/scenes/layout.py` + `game/scenes/zone_paint.py`, lahir di
[[2026-08-27 — Tata letak, avatar native, tukang mesh]]. Prinsipnya diekstrak
dari peta Stardew Valley / Harvest Moon ke `docs/TATA_LETAK.md` (201 baris).

## Masalah yang diselesaikan

Tiap scene sebelumnya menulis `for y in range(...): for x in ...`
sendiri-sendiri. Akibatnya bentuk zona **hanya terlihat kalau kode
dijalankan**, dan tidak ada satu pun rancangan yang bisa dibaca dari sumbernya.
Padahal `docs/TATA_LETAK.md` P3 menuntut zona berupa persegi utuh — itu hal
yang harus kelihatan di sumbernya, bukan cuma di layar.

## Konvensi

- Semua fungsi menulis **langsung** ke matriks `m[y][x]`.
- Aman terhadap tepi peta: indeks di luar batas **diabaikan**, bukan melempar.
  Sengaja — peta dirancang dengan menumpuk bentuk, dan bentuk yang sedikit
  menjorok keluar adalah hal biasa saat menyetel.
- Koordinat di seluruh proyek: `m[y][x]`, x ke timur, y ke selatan.

## Pewarnaan zona

`zone_paint.py` mewarnai zona supaya area **terbaca fungsinya** sebelum pemain
membaca satu kata pun. Dipakai `farm.py`, `props.py`, `scene_base.py`.

## Tautan

[[Peta Kode]] · [[Tahap 7 — Misteri dan entitas]]
