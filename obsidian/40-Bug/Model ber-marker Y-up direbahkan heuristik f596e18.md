---
judul: "Model ber-marker Y-up direbahkan heuristik f596e18"
tipe: bug
status: selesai
ditemukan: "2026-10-18"
commit_perbaikan: db5ec5d
dijaga_oleh: tools/regress.py (cek_model_tegak)
tags: [bug, status/selesai, render, model-blender]
---

# 🐞 Model ber-marker Y-up direbahkan heuristik f596e18

Mercusuar beach tampil sebagai gumpalan rebah, dan kurofune terbaring
setengah di bawah tanah. Pohon, peti, dan prop lain ikut rebah begitu
dipasang.

## Sebab

`load_model_file` (sejak f596e18) memberi `setP(-90)` pada tiap model OBJ
yang bounds-nya `d.y > d.z`. Tebakan itu tepat terbalik: berkas yang sudah
dikonversi ke Y-atas oleh `fix_obj_axes.py` (baris pertama
`# axis-converted-to-Y-up`) justru direbahkan, sedangkan berkas Z-atas
dibiarkan rebah.

Heuristiknya hanya aktif dengan ShowBase. Probe offscreen tanpa ShowBase
melihat model tegak dan lulus palsu.

## Perbaikan (db5ec5d)

Prefiks `pohon_` / `prop_` yang ber-marker tidak diputar. Empat berkas
Z-atas tanpa marker (`pohon_bambu`, `lantern`, `sumur`, `pagar_bambu`)
masuk tabel eksplisit `_Z_ATAS` dengan `setP(+90)`. humanoid, petapa_*,
npc_*, mob_*, naga TIDAK disentuh.

## Bukti (Game3D, tinggi/dasar dunia vs sumbu-atas berkas)

294f869: 11 dari 12 model rebah (kelapa dz 5,10 > dy 4,01; mercusuar
tinggi 2,37 dari 7,17; kurofune dasar -4,06). Sesudah: 0. Mutasi (cabang
marker dan `_Z_ATAS` dimatikan) -> beach GAGAL
"prop_mercusuar_rusak tinggi 2.37/7.17".

Beach dua kondisi lewat Game3D: `lighthouse_fixed=False` -> 38 tegak
(37 kelapa + mercusuar rusak); `True` -> 39 tegak (37 kelapa, mercusuar,
kurofune; kurofune dasar -0,21, puncak 12,7).

## Yang belum

humanoid, petapa_srimana, petapa_srimana_galak masih rebah menurut ukuran
yang sama. Di luar perbaikan ini; calon kerja terpisah, belum diperiksa
mata.
