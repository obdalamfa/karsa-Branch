---
judul: "scatter_obj_props no-op sejak merge 5683e79"
tipe: bug
status: selesai
ditemukan: "2026-10-18"
commit_perbaikan: 7966797, 12bf1d0
dijaga_oleh: tools/regress.py (cek_model_blender, HARAPAN_MODEL lake/cemetery)
tags: [bug, status/selesai, aturan-4, ditelan-except]
---

# 🐞 scatter_obj_props no-op sejak merge 5683e79

Lake dan cemetery tampil tanpa satu pun model sebaran (lentera, pagar
bambu, peti sayur, jerami) sejak 9 Sep 2026. Tidak ada error, tidak ada log.

## Sebab — mati dua lapis

1. Merge 5683e79 (feature/3d-mobs) membawa `scatter_obj_props`, yang
   meng-import `make_obj_entity` dari `game/entities.py`. Fungsi itu hilang
   di merge yang sama. Kegagalannya ditelan `except Exception: return`.
2. Sejak Fase 3 (4a425d3, 29 Sep) game memuat scene dari `lake.json` /
   `cemetery.json`, yang menyimpan builder `'default'`. `lake_builder` dan
   `cemetery_builder` (satu-satunya pemanggil scatter) hanya hidup di
   jalur cadangan kode. Probe Game3D: `builder_name='default'`, scatter
   dipanggil 0x di kedua scene.

Penjaganya juga mati: cek "dressing >= 8" di `tools/smoke_boot.py` tidak
pernah dijalankan CI, menyetub `load_model_file`, dan asersi mountain-nya
sudah basi.

## Perbaikan

- 7966797: kegagalan import / model hilang jadi `logging.error`.
- 12bf1d0: `make_obj_entity` dipulihkan (salinan model baru per entity),
  spesifikasi sebaran pindah ke `props.SEBARAN_OBJ` yang dibaca
  `default_prop_builder` di kedua jalur, dua builder kustom dibuang.

## Bukti

`regress.py cemetery lake` lewat Game3D: LULUS dengan cemetery lantern 4 +
pagar_bambu 3, lake lantern 3 + peti 2 + jerami 2. Mutasi
`make_obj_entity` diganti nama (= keadaan sejak 5683e79): GAGAL
"lantern 0/4, pagar_bambu 0/3" dan "lantern 0/3, prop_jerami 0/2,
prop_peti_sayur 0/2", dan log error scatter berbunyi.

## Pelajaran

Aturan #4 kena alat ujinya sendiri: modul ada, pemanggil ada, tapi
pemanggil itu tidak pernah dipanggil, dan penjaganya tidak pernah jalan.
