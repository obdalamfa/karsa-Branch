---
judul: "Kotak dialog ala Harvest Moon dengan potret, pembuka sesuai jam/tempat"
tipe: sesi
tanggal: 2026-10-05
commit: 81f29cd
skala: 25 file sumber, +496 / −33 baris
tags: [sesi]
---

# 2026-10-05 — Kotak dialog ala Harvest Moon dengan potret, pembuka sesuai jam/tempat

## Pesan commit

- game/percakapan.py: kalimat pembuka per warga menurut kegiatan jadwal,
  tempat (di luar tempat biasanya), hujan, dan waktu (pagi..larut);
  disisipkan sebelum baris hati/quest lama, jadi cerita lama utuh.
- Kotak dialog: kertas krem berbingkai kayu, potret di kiri, papan nama,
  teks mesin ketik (E/Spasi menuntaskan dulu, lalu lanjut). Geometri
  kotak dipusatkan; cabang pilihan tidak lagi menggeser kotak sendiri.
- tools/potret.py merender potret 18 aktor dari GLB-nya sendiri ke
  assets/textures/potret/ (near clip lensa harus < 1 m).

## Berkas yang berubah

| Berkas | + | − |
|---|---:|---:|
| `assets/blend/characters_vitaboy.blend` | +- | −- |
| `assets/blend/characters_vitaboy.blend1` | +- | −- |
| `assets/textures/potret/arya.png` | +- | −- |
| `assets/textures/potret/bidadari.png` | +- | −- |
| `assets/textures/potret/bowo.png` | +- | −- |
| `assets/textures/potret/budi.png` | +- | −- |
| `assets/textures/potret/cici.png` | +- | −- |
| `assets/textures/potret/dewa_angin.png` | +- | −- |
| `assets/textures/potret/jaka_ronda.png` | +- | −- |
| `assets/textures/potret/joko.png` | +- | −- |
| `assets/textures/potret/kapten_kuro.png` | +- | −- |
| `assets/textures/potret/kru_kuro.png` | +- | −- |
| `assets/textures/potret/maya.png` | +- | −- |
| `assets/textures/potret/mbok_jum.png` | +- | −- |
| `assets/textures/potret/ningsih.png` | +- | −- |
| `assets/textures/potret/pak_guru.png` | +- | −- |
| `assets/textures/potret/petapa_srimana.png` | +- | −- |
| `assets/textures/potret/player.png` | +- | −- |
| `assets/textures/potret/raka.png` | +- | −- |
| `assets/textures/potret/sari.png` | +- | −- |
| `game/app.py` | +6 | −1 |
| `game/panels.py` | +92 | −32 |
| `game/percakapan.py` | +234 | −0 |
| `tools/blender_seragam.py` | +73 | −0 |
| `tools/potret.py` | +91 | −0 |

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
