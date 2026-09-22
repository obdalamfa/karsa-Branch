---
judul: Terjepit permanen
tipe: bug
status: selesai
ditemukan: 2026-08-26
commit_perbaikan: 09ef02f
dijaga_oleh: pemain_valid
tags: [bug, kontrol, status/selesai]
---

# 🐞 Terjepit permanen

## Gejala

Laporan pemilik: *"stuck di tempat yang tidak seharusnya"*. Pemain tidak bisa
bergerak ke arah mana pun.

## Sebab

Semua uji tabrakan memakai **tile saat ini** sebagai jangkar. Kalau pemain
sampai berdiri di atas tile terblokir, `tx_cur`/`tz_cur` ikut terblokir
sehingga **setiap** arah ditolak. Diukur di `_bench/probes/probe_stuck.py`:
di tile terblokir, keempat arah menghasilkan perpindahan 0,00.

Pemain bisa sampai di sana lewat banyak jalan yang wajar: ganti scene, pohon
tumbuh di petaknya, medan berubah, atau memuat save dengan koordinat basi.
Jadi ini bukan kasus mustahil.

## Perbaikan

`player.py` sekarang **mengizinkan gerak apa pun yang mendarat di tile yang
bisa dijalani**, tanpa peduli tile asal terblokir. Selalu ada jalan keluar.

## Tapi itu baru gejalanya

Akarnya ditemukan belakangan oleh [[Regresi]]:
[[Pendaratan scene di luar peta]] — pemain didaratkan di koordinat yang tidak
ada di peta tujuan. Perbaikan di `player.py` menambal akibatnya; perbaikan di
`126cea8` menambal sebabnya. Keduanya tetap perlu.

## Yang menjaganya sekarang

Pemeriksaan `pemain_valid` di [[Regresi]].

## Tautan

[[2026-08-26 — Perbaiki render, kontrol, loop permainan]] · [[Pendaratan scene di luar peta]]
