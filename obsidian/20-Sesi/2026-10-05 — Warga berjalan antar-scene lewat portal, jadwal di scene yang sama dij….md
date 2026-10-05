---
judul: "Warga berjalan antar-scene lewat portal, jadwal di scene yang sama dijalankan"
tipe: sesi
tanggal: 2026-10-05
commit: 30d2bb9
skala: 2 file sumber, +387 / −183 baris
tags: [sesi]
---

# 2026-10-05 — Warga berjalan antar-scene lewat portal, jadwal di scene yang sama dijalankan

## Pesan commit

- game/perjalanan.py: rute BFS di graf portal; maju lurus di luar layar.
- entities: warga ber-rute tidak lagi teleport; di scene pemain aktornya
  berjalan ke pintu lalu menghilang, tiba = dibangun di pintu masuk dan
  berjalan ke tujuannya (_tick_perjalanan, _bangun_aktor, _hapus_aktor).
- Perubahan jadwal di scene yang sama kini sampai ke aktornya (dulu
  aktor memegang titik jadwal lama dan menimpa pos tiap frame).

Belum diuji panjang di permainan; regress farm/town/shop dijalankan.

## Berkas yang berubah

| Berkas | + | − |
|---|---:|---:|
| `game/entities.py` | +298 | −183 |
| `game/perjalanan.py` | +89 | −0 |

## Bukti

<!-- ISI MANUAL. Angka, larian regresi, atau probe — skrip sengaja tidak
     menebak bagian ini. Lihat [[Aturan Pencatatan]]. -->

- Bukti spesifik untuk commit ini **tidak tercatat** saat dikerjakan (sesi panjang, catatan ditulis belakangan). Diperiksa visual lewat tangkapan layar; regresi penuh pertama sesudahnya ada di 17d570b.

## Yang belum beres

<!-- ISI MANUAL. Ditulis apa adanya, termasuk yang alat ukurnya belum bisa
     dipercaya. -->

- Swarga gagal `cahaya_global` di regresi (juga di 17d570b dan HEAD sebelumnya) — belum diselidiki.
- `hud_terbaca` gagal acak tergantung urutan scene pada larian penuh; lulus kalau scene diuji sendiri.
- Bug pemilik yang masih antri: suasana semua scene disamakan dengan farm (#2/#9), animasi pakai alat (#11), kedip farm (#3) belum dikonfirmasi pemilik, pohon/kelapa dan interior gua via Blender.

## Tautan

[[Status Sekarang]] · [[Peta Progres]]
