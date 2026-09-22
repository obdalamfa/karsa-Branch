---
judul: Tahap 1 — Jaring pengaman
tipe: tahap
nomor: 1
status: selesai
ringkas: tools/regress.py — boot tiap scene, buktikan ia dirender
commit: 126cea8
tags: [tahap, status/selesai]
---

# Tahap 1 — Jaring pengaman ✅

`tools/regress.py` (264 baris saat lahir) mem-boot tiap scene, membuktikan ia
benar dirender, dan memeriksa hal-hal yang memang **pernah** rusak di proyek
ini. Rinciannya di [[Regresi]].

## Kenapa ini duluan, bukan fitur

Verifikasi manual sudah gagal **dua kali** dalam satu sesi: WASD dinyatakan
beres padahal belum, dan dua kali sebuah metode disisipkan di tengah fungsi
sehingga fungsi induknya mati total. Keduanya ketahuan cuma karena kebetulan
diuji ulang. Yang ketiga tidak akan ketahuan.

## Larian pertama langsung membayar ongkosnya

Masuk `house`/`shop` mendaratkan pemain di (19,5) padahal `house` cuma 15
kolom → [[Pendaratan scene di luar peta]]. Itu **akar** dari gejala yang
sebelumnya cuma ditambal di sisi pemain ([[Terjepit permanen]]).

## Status penyelesaian

Perintahnya jalan, mengeluarkan tabel LULUS/GAGAL, dan melaporkan kondisi
sekarang apa adanya. Hasil terakhir yang tercatat: **5/5 scene lulus**
(commit `7ed8d59`).

> [!caution] Belum diuji ulang sejak 2026-08-27
> Sesi 2026-09-22 tidak punya `ursina`/`panda3d`, jadi angka itu warisan
> commit, bukan larian baru. Lihat [[Status Sekarang]].

## Tautan

Sesi: [[2026-08-26 — Tahap 1 jaring pengaman regresi]] ·
Lanjut ke [[Tahap 2 — Verifikasi modul yatim]]
