---
judul: "Warga beragam suku dan topi yang pas di kepala (runtime)"
tipe: sesi
tanggal: 2026-10-05
commit: f1f0e3e
skala: 2 file sumber, +236 / −44 baris
tags: [sesi]
---

# 2026-10-05 — Warga beragam suku dan topi yang pas di kepala (runtime)

## Pesan commit

- terapkan_npc: warna kulit tiap warga mengikuti keragaman Nusantara
  (Papua, Ambon, Jawa, Batak, Bugis, Minang, Bali, Sunda, Tionghoa,
  Arab-Indonesia, Jepang). Celup kulit memakai acuan warna dari tekstur
  wajah warga itu sendiri dengan bobot lembut yang diburamkan: batas
  tegas membuat kulit belang, uji generik ikut mencelup kain cokelat.
- Topi hasil Blender (diukur dari pose istirahat, sering melayang atau
  jatuh ke mata) disembunyikan dan diganti topi runtime yang diukur dari
  node kepala TERTINGGI -- node pertama bisa kacamata TSO 5 cm.
- Pewarnaan memakai numpy dan di-cache per warga.

## Berkas yang berubah

| Berkas | + | − |
|---|---:|---:|
| `game/entities.py` | +7 | −0 |
| `game/rupa_pemain.py` | +229 | −44 |

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
