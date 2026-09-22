---
judul: Status Sekarang
tipe: peta
diperbarui: 2026-09-22
commit_acuan: 7ed8d59
tags: [moc, status]
---

# Status Sekarang

Keadaan proyek pada commit `7ed8d59` (2026-08-27), diperiksa ulang 2026-09-22.

> [!warning] Batas bukti catatan ini
> Sesi 2026-09-22 berjalan di mesin tanpa `ursina`/`panda3d`, jadi
> `tools/regress.py` **tidak bisa dijalankan ulang di sini**. Status
> "5/5 lulus" diambil dari bukti commit `7ed8d59`, bukan dari larian baru.
> Semua klaim di bawah yang ditandai 🔍 diverifikasi ulang lewat pembacaan
> kode dan `grep` di sesi ini — itu yang bisa dipertanggungjawabkan tanpa GPU.

## Yang berdiri

| Hal | Bukti |
|---|---|
| Render scene, kamera isometric, kontrol dasar | [[2026-08-26 — Perbaiki render, kontrol, loop permainan]] |
| Jaring regresi 6 pemeriksaan + ms/frame | [[Regresi]], `tools/regress.py` |
| Mesin motif TS1 (8 motif, decay, advertising) | [[Motif]] · 9 modul memanggilnya 🔍 |
| Antrian aksi (X tandai, C eksekusi) | [[Antrian Aksi]] |
| Ternak berakibat: lapar → sakit kalau dilalaikan | [[Ternak]] |
| Alat terlihat di tangan pemain | [[2026-08-26 — Tahap 2 sambungkan modul yatim]] |
| Avatar Vitaboy jalur native C++ (0,288 ms/avatar) | [[Avatar Vitaboy]] |
| ESC selalu bisa keluar dari mode panel apa pun | [[Pemain beku saat panel terbuka]] |

## Yang masih terbuka

| Hal | Berat | Catatan |
|---|---|---|
| Arah WASD belum terverifikasi benar | 🔴 | [[Arah WASD belum terverifikasi]] — alat ukurnya yang rusak, bukan kodenya |
| 4–29 FPS, belum pernah diprofil | 🔴 | [[Tahap 3 — Performa]] |
| `entity_mesh.py` (458 baris) nol pemanggil 🔍 | 🟠 | [[Utang Teknis]] — pola yatim yang sama seperti [[Tahap 2 — Verifikasi modul yatim]] |
| `choose_action()` / `autonomy_candidates()` nol pemanggil 🔍 | 🟠 | [[Tahap 5 — Autonomi]] — sudah jadi, belum disambung |
| 92 file `.pyc` ikut ter-commit 🔍 | 🟡 | [[Utang Teknis]] |
| `PLAY.md` menunjuk baris & flag yang sudah tidak ada 🔍 | 🟡 | [[Utang Teknis]] |

## Tahap yang sedang jalan

[[Tahap 2 — Verifikasi modul yatim]] — dua modul yatim lama sudah tersambung,
tapi satu modul yatim **baru** muncul di commit berikutnya. Tahap ini belum
boleh ditutup.

## Langkah berikutnya yang masuk akal

1. Sambungkan atau buang `entity_mesh.py` — tutup [[Tahap 2 — Verifikasi modul yatim]].
2. Bangun probe arah yang kokoh, baru sentuh tanda WASD → [[Arah WASD belum terverifikasi]].
3. Profil frame, mulai optimasi aman → [[Tahap 3 — Performa]].
