---
judul: "Kalpataru Swarga lebih kecil dan tidak menyilaukan, butir cahaya dikurangi"
tipe: sesi
tanggal: 2026-10-18
commit: a0524e2
skala: 1 file sumber, +23 / −16 baris
tags: [sesi]
---

# 2026-10-18 — Kalpataru Swarga lebih kecil dan tidak menyilaukan, butir cahaya dikurangi

## Pesan commit

Tajuk dulu satu gumpalan cahaya rata selebar seperempat layar. Kini skala
0,75 dan gradasi daun curam (puncak terang, perut gelap); daun yang ikut
cahaya scene sempat dicoba tapi memberi pita toon bergaris. Butir cahaya
pohon 22 -> 10, butir di seluruh pulau 35 -> 18.

## Berkas yang berubah

| Berkas | + | − |
|---|---:|---:|
| `game/scenes/kahyangan.py` | +23 | −16 |

## Bukti

<!-- ISI MANUAL. Angka, larian regresi, atau probe — skrip sengaja tidak
     menebak bagian ini. Lihat [[Aturan Pencatatan]]. -->

Sesi ini juga mencakup `c380bad` (gua naga + dungeon) dan, dari 2026-10-08,
`f20bb18`/`fc2ad01`/`bab86f4` (hutan lereng, mulut gua, tebing menerus).

- Regresi penuh 2026-10-18: `python tools/regress.py` -> **8/14 scene lulus**.
  Yang gagal: `hud_terbaca` (town, lake, beach, shop -- berpindah-pindah scene
  antar-larian), `cahaya_global` (cemetery), `pemain_valid` swarga (5,5).
  Ketiganya sudah gagal SEBELUM perubahan sesi ini (larian 2026-10-08 di
  `interior/blender-satu` gagal dengan jenis yang sama).
- `mountain` + `naga_cave` lulus; `python tools/interior_check.py` -> 6/6 ruangan,
  dunia LULUS.
- Tidak ada kebocoran entity: `house` 591 entity baik sendirian maupun
  sesudah `mountain`.
- Probe `_bench/probes/foto_scene.py` (menutup Buat Karakter lewat
  `g.input('enter')`, dungeon lewat `_generate_and_enter_dungeon`):
  dungeon lantai 2 & 12, gua naga, swarga, lereng -- diperiksa visual.
- Dungeon SEBELUM: lantai putih terbakar bloom, bijih tidak tergambar sama
  sekali (builder bawaan membaca peta placeholder, bukan `state.dungeon_tiles`).

## Yang belum beres

<!-- ISI MANUAL. Ditulis apa adanya, termasuk yang alat ukurnya belum bisa
     dipercaya. -->

- `pemain_valid` swarga: pemain mendarat di (5,5) yang tak-walkable pada
  larian regress; berkas `swarga.json` juga beda dari kodenya (judul + ubin
  (15,2)) sejak merge kahyangan. Belum diperbaiki.
- Performa `mountain` berayun 41-160 ms/frame sejak hutan 69 pohon; belum
  diprofil.
- Dungeon: bijih tergambar tapi kecil; belum diuji menambang lalu scene
  dimuat ulang (seharusnya bijih hilang karena builder terpanggil ulang --
  belum terverifikasi).
- Potret Sang Hyang Naga di kotak dialog kosong.
- Panel "Tutorial 1/7" tampil di tengah sinema.

## Tautan

[[Status Sekarang]] · [[Peta Progres]]
