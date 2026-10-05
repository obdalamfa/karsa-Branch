---
judul: "Wajah chibi dari wajah.py di rig GLB, mata dipaskan, topi bajak laut"
tipe: sesi
tanggal: 2026-10-05
commit: dc6a63a
skala: 2 file sumber, +90 / −12 baris
tags: [sesi]
---

# 2026-10-05 — Wajah chibi dari wajah.py di rig GLB, mata dipaskan, topi bajak laut

## Pesan commit

- rupa_pemain.wajah_chibi: struktur muka versi chibi (lukis_wajah_chibi)
  dipakai di kepala DAN cangkang rambut TSO (yang ikut memuat wajah lama).
  Mata 0,68x dan sedikit dipipihkan, iris cokelat tua; kulit dicelup dulu
  lalu wajah dilukis di atasnya (urutan sebaliknya melunturkan mata);
  wajah.py menerima kulit_tetap dan lewati_rambut. Kepala 1,16x lewat
  sendi HEAD (versi lama 2,90x kebesaran).
- Topi Kapten Kuro jadi topi bajak laut yang menutup ubun-ubun.
- Batas topi: dasar 0,3 tinggi kepala di bawah puncak.

Topi dari primitif runtime masih kasar; model mesh di Blender menyusul.

## Berkas yang berubah

| Berkas | + | − |
|---|---:|---:|
| `game/rupa_pemain.py` | +81 | −9 |
| `game/wajah.py` | +9 | −3 |

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
