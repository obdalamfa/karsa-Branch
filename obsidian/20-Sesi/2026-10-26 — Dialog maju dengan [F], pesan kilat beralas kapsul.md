---
judul: "Dialog maju dengan [F], pesan kilat beralas kapsul"
tipe: sesi
tanggal: 2026-10-26
commit: 82ec1b9
skala: 3 file sumber, +53 / −10 baris
tags: [sesi]
---

# 2026-10-26 — Dialog maju dengan [F], pesan kilat beralas kapsul

> [!info] Nota ini menutup satu rangkaian kerja atas permintaan pemilik:
> "lanjutkan peningkatan gameplay, grafik dan animasi. perhatikan lagi tampilan
> HUD masih sangat jelek si, menu-menu dan tutorial". Commit-nya:
> - 81a5614: makhluk liar tampil sebagai kotak putih, diperbaiki
> - 774830c dan 94c77ed: panel kartu, inventori bergrid, peta dari portal, menu jeda
> - 20617a9: HUD
> - b195c58: probe tampilan masuk regresi
> - 82ec1b9: dialog dan pesan kilat

## Pesan commit

- F (tombol interaksi sejak 22 Okt) melanjutkan dialog dan memilih
  jawaban; W/S menggeser pilihan. Petunjuk '[E / SPASI]' diganti
  '[F / SPASI]': E kini memutar kamera.
- Pesan kilat: alas kapsul gelap selebar teksnya, teks emas.
- probe_tampilan 36/36; mutasi 'dialog tanpa F' tertangkap.

## Berkas yang berubah

| Berkas | + | − |
|---|---:|---:|
| `game/app.py` | +8 | −4 |
| `game/panels.py` | +16 | −6 |
| `tools/probe_tampilan.py` | +29 | −0 |

## Bukti

<!-- ISI MANUAL. Angka, larian regresi, atau probe — skrip sengaja tidak
     menebak bagian ini. Lihat [[Aturan Pencatatan]]. -->

- Tangkapan garis dasar dibuat lebih dulu, lewat jalur asli (`g.app.input`, game
  baru). Hasilnya:
  - Panel I/J/M/H/P berisi dump teks ASCII.
  - Ada kotak putih melayang di kebun.
  - ESC di HUD hanya menyimpan.
- Kotak putih dilacak dengan memproyeksikan semua GeomNode ke layar, lalu
  mendaftar entity quad di dunia → [[Makhluk liar tampil sebagai kotak putih]].
- Ditemukan tiga modul yatim lagi (aturan #4), yang kini disambungkan:
  - `animal_models.build_wild_entity` (sekaligus rusak: konstanta terhapus,
    mesh dibagi)
  - grid inventori `_render_inventory_grid` dan `navigate_inventory`
  - cangkang menu jeda `_build_pause`
- Peta ASCII lama salah. Kuburan digambar tersambung ke Desa, padahal portalnya
  ke Lereng, dan Pantai tidak ada. Peta baru dibaca dari `SCENES[*].portals`.
- `tools/probe_tampilan.py` lulus 36/36. Lima mutasi tertangkap:
  - kotak polos kembali → 3 GAGAL
  - panel kembali jadi dump teks → 5
  - ESC hanya menyimpan → 3
  - inventori tanpa tombol → 2
  - dialog tanpa F → 1

  Versi pertama probe meloloskan mutasi kotak polos karena tekstur kosong
  Ursina bukan `None`. Kriterianya diperbaiki, lalu mutasi diulang.
- Regresi penuh lokal (sebelum 82ec1b9): 14/14 scene, 0 pemeriksaan gagal.
  Baris global semuanya lulus, termasuk "tampilan" 33/33. Sesudah 82ec1b9
  `probe_tampilan` lulus 36/36.
- CI: 774830c GAGAL (majelis batin 25/26). Penyebabnya kartu kecil yang
  diperbesar untuk bayangannya sampai menimpa kepingan tombol HUD. Diperbaiki
  di 94c77ed, dan CI hijau di 94c77ed, 20617a9, dan a48682d.

## Yang belum beres

<!-- ISI MANUAL. Ditulis apa adanya, termasuk yang alat ukurnya belum bisa
     dipercaya. -->

- Rasa tampilan belum dinilai pemilik. Semua tangkapan dibuat di render CPU
  1280×720; skala di layar lain belum dilihat.
- Panel Hubungan membuat sekitar 340 entity setiap kali dibuka (10 hati × 27
  NPC). Belum diukur di mesin pemilik.
- Panel teks (Warung, Dapur, Bengkel, Ekosistem, Papan, Keinginan) baru
  mendapat bingkai dan tipografi, belum ditata ulang seperti Jurnal/Peta.
- Kotak dialog masih bergaya perkamen krem (sengaja, khas percakapan). Ia
  belum senada dengan kartu gelap.
- Tebing mulut gua di mountain masih menunggu keputusan pemilik.

## Tautan

[[Status Sekarang]] · [[Peta Progres]]
