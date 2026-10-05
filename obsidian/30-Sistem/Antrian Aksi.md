---
judul: Antrian Aksi
tipe: sistem
modul: game/action_queue.py
baris: 119
status: jalan
tags: [sistem, sims, status/jalan]
---

# Antrian Aksi — bagaimana klik menjadi perbuatan

`game/action_queue.py`. **Loop permainan yang sebenarnya ada di sini.** Sebelum
modul ini, motif hanya turun dan tidak ada apa pun yang menaikkannya —
permainan tidak punya loop.

## Model The Sims

Aksi masuk **antrian**, bukan langsung dijalankan. Pemain boleh menumpuk
beberapa perintah dan sim mengerjakannya berurutan.

```python
PRIORITY_PLAYER      = 50   # perintah langsung pemain
PRIORITY_AUTONOMOUS  = 2    # pilihan sim sendiri
PRIORITY_IDLE        = 0
```

Aksi otonom masuk dengan prioritas rendah sehingga **selalu kalah** dari
perintah pemain — itu yang membuat sim terasa punya kehendak sendiri tanpa
pernah membangkang perintah langsung.

## Motif diberikan selama aksi, bukan di akhir

Penting untuk keterbacaan: pemain melihat termometer merangkak naik dan
langsung paham sebab-akibatnya. Hadiah yang muncul tiba-tiba di akhir tidak
mengajarkan apa pun.

## Di tangan pemain

**X** menandai tile, **C** mengeksekusi seluruh antrian sekaligus (`PLAY.md`).

## Tautan

[[Motif]] · [[Objek dan Interaksi]] · [[Tahap 4 — Wishes]]
