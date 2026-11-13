---
judul: "Makhluk liar tampil sebagai kotak putih melayang"
tipe: bug
status: selesai
ditemukan: "2026-10-26"
commit_perbaikan: (lihat nota sesi 2026-10-26)
dijaga_oleh: tools/probe_tampilan.py ("tidak ada kotak polos di dunia")
tags: [bug, status/selesai, grafis, yatim]
---

# 🐞 Makhluk liar tampil sebagai kotak putih melayang

## Gejala

Di kebun, desa, dan danau ada kotak putih yang melayang di udara dan selalu
menghadap kamera. Kotak itu terlihat di hampir semua tangkapan HUD,
tiga di kebun pada siang hari.

## Sebab

Ada tiga sebab bertumpuk:

1. `EntitiesManager` hanya membangun model makhluk liar untuk scene
   `mountain`. Di scene lain, jamur lari dan kunang-kunang dibuat sebagai
   `Entity(model='quad', billboard=True)` tanpa tekstur.
2. Model chibi untuk keduanya sudah ada di
   `animal_models.build_wild_entity`, tapi fungsi itu **tidak punya
   pemanggil** (aturan #4).
3. Fungsi yatim itu juga rusak. `_WILD_SCALES`, `_EYE_W`, `_EYE_PU`, dan
   `_BLUSH` terhapus di commit ae03456, dan satu mesh `soft_cube` dibagi ke
   semua bagian (aturan #3).

Diukur dengan memproyeksikan setiap GeomNode ke layar. Tiap kotak di
tangkapan adalah `quad` 0,5 × 0,5 di y = 0,45, pada koordinat makhluk liar.

## Perbaikan

- `entities.py` memanggil `build_wild_entity` untuk semua jenis di luar
  `build_wild` gunung.
- Konstanta dipulihkan dari ae03456.
- Tiap bagian mendapat mesh sendiri.
