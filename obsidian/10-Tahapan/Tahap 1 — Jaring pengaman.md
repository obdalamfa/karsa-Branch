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
sekarang apa adanya. Hasil terakhir: **14/14 scene lulus, 0 pemeriksaan
gagal** — dijalankan sungguhan 2026-09-22, bukan dikutip dari commit.

Tahap ini baru benar-benar tuntas di sesi itu, karena dua hal:

1. Jaringnya ternyata **tidak bisa dijalankan di mesin bersih** sama sekali —
   `requirements.txt` tidak menyebut `pygame`/`pillow`, dan font HUD tidak
   ketemu ([[Font HUD tidak ketemu di mesin bersih]]).
2. Jaring yang hanya jalan kalau diingat bukan jaring. Sekarang ia dipasang di
   CI: `.github/workflows/regresi.yml` menjalankannya tiap push dan PR.

## Tautan

Sesi: [[2026-08-26 — Tahap 1 jaring pengaman regresi]] ·
Lanjut ke [[Tahap 2 — Verifikasi modul yatim]]
