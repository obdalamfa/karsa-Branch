---
judul: Perbaiki render, kontrol, dan tambahkan loop permainan
tipe: sesi
tanggal: 2026-08-26
commit: 09ef02f
skala: 96 file, 12.296 baris
tags: [sesi, bug, render]
---

# 2026-08-26 — Empat bug akar + loop permainan

Commit `09ef02f`. Empat bug **akar** yang ditemukan lewat pengukuran, bukan
tebakan. Ini juga commit yang menutup [[Tahap 0 — Amankan kerja]].

## Empat bug

1. **Mesh NodePath dipakai bersama** → [[Mesh NodePath dipakai bersama]].
   Sebab kenapa dinding, rumah, dan perabot tidak pernah muncul. Jalur
   `entities.py` diam-diam juga menghapus setiap NPC humanoid dan mob kecuali
   yang terakhir.
2. **Kamera pitch 12°**, praktis sejajar tanah. Sekarang 34°, jarak 19.
   `CAM_HEIGHT`/`CAM_BACK` ternyata konstanta mati — dibuang.
3. **WASD terbalik keempat arahnya** → [[WASD terbalik]]. Kode mencampur
   koordinat lokal (`self.x`) dengan koordinat dunia (`camera.world_x`).
4. **Terjepit permanen** → [[Terjepit permanen]]. Semua uji tabrakan memakai
   tile saat ini sebagai jangkar.

## Sistem baru di commit yang sama

| Modul | Isi |
|---|---|
| `motives.py` | 8 motif, laju peluruhan asli TS1, kurva kontribusi, advertising, roulette berbobot → [[Motif]] |
| `objects.py` | 16 perabot, 20 interaksi; iklan menempel pada interaksi → [[Objek dan Interaksi]] |
| `action_queue.py` | antrian aksi; motif diisi selama aksi berjalan → [[Antrian Aksi]] |
| `panels.py` | panel termometer motif (rangkanya ada tapi kosong sebelumnya) |

Plus pagar prosedural, 9 spesies binatang, model alat, [[Ekonomi]], dan
[[Palawija]].

## Bukti

Tangkapan layar dan log di `_bench/` (gitignored). Verifikasi arah WASD
memakai proyeksi lensa Panda3D pada yaw 0°, 90°, dan 215°.

## Yang belum beres

Verifikasi arah itu belakangan terbukti rapuh — lihat
[[Arah WASD belum terverifikasi]]. Dan commit sebesar ini menyeret
`__pycache__` masuk ke git ([[Utang Teknis]]).

## Tautan

Berikutnya: [[2026-08-26 — Tahap 1 jaring pengaman regresi]]
