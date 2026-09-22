---
judul: Beranda
tipe: moc
proyek: Lembah Karsa 3D
diperbarui: 2026-09-22
tags: [moc, beranda]
---

# 🌾 Catatan Lembah Karsa 3D

Vault ini adalah **buku kerja proyek**: apa yang sudah jadi, apa yang masih
rusak, dan atas bukti apa itu dinyatakan. Kode sumbernya ada di `../game/`;
catatan ini tidak menggantikannya, ia menjelaskan *kenapa* kodenya begitu.

> [!info] Cara membuka
> Obsidian → **Open folder as vault** → pilih folder `obsidian/` di repo ini.
> Semua konfigurasi (tema, graph, templat) ikut tersimpan di `.obsidian/`.

---

## Mulai dari sini

| Kalau kamu mau… | Buka |
|---|---|
| tahu keadaan proyek hari ini | [[Status Sekarang]] |
| tahu urutan kerja berikutnya | [[Peta Progres]] |
| cari modul kode tertentu | [[Peta Kode]] |
| tahu apa yang masih berutang | [[Utang Teknis]] |
| menambah catatan baru | [[Aturan Pencatatan]] |

---

## Ringkas satu layar

- **Game**: farming RPG Nusantara 3D, Python + [Ursina](https://www.ursinaengine.org/), kamera isometric tetap.
- **Ukuran**: 19.514 baris di `game/`, 50 modul, 12+ scene.
- **Riwayat**: 6 commit, 2026-05-27 → 2026-08-27.
- **Tahapan**: [[Tahap 0 — Amankan kerja|0]] ✅ · [[Tahap 1 — Jaring pengaman|1]] ✅ · [[Tahap 2 — Verifikasi modul yatim|2]] 🔨 · [[Tahap 3 — Performa|3]]–[[Tahap 8 — Audio|8]] ⬜
- **Yang paling menghambat**: frame rate 4–29 FPS yang belum pernah diprofil → [[Tahap 3 — Performa]].

---

## Tahapan

```dataview
TABLE status, ringkas FROM "10-Tahapan" SORT file.name ASC
```

*(blok di atas butuh plugin **Dataview**; tanpa plugin ia cuma tampil sebagai kode — daftar manualnya ada di [[Peta Progres]].)*

---

## Jurnal sesi terbaru

- [[2026-09-22 — Vault Obsidian dibuat]] — pencatatan progres dipindah ke vault ini
- [[2026-08-27 — Dua jebakan pembeku pemain]] — ESC dan pie menu tidak lagi mengunci pemain
- [[2026-08-27 — Tata letak, avatar native, tukang mesh]] — skinning C++ 22× lebih murah
- [[2026-08-26 — Tahap 2 sambungkan modul yatim]] — alat di tangan, ternak berakibat
- [[2026-08-26 — Tahap 1 jaring pengaman regresi]] — `tools/regress.py` lahir
- [[2026-08-26 — Perbaiki render, kontrol, loop permainan]] — empat bug akar
- [[2026-05-27 — Commit awal]] — titik nol

Semua sesi: folder `20-Sesi/`.

---

## Bug yang pernah nyata

[[Mesh NodePath dipakai bersama]] · [[WASD terbalik]] · [[Terjepit permanen]] ·
[[Pendaratan scene di luar peta]] · [[Pemain beku saat panel terbuka]] ·
[[Arah WASD belum terverifikasi]] 🔴

---

## Sistem

[[Motif]] · [[Antrian Aksi]] · [[Objek dan Interaksi]] · [[Ternak]] ·
[[Ekonomi]] · [[Palawija]] · [[Avatar Vitaboy]] · [[Tata Letak Scene]] ·
[[Regresi]] · [[Dungeon dan Combat]]
