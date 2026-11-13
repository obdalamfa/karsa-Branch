---
judul: "Palung farm terkubur di scatter_obj_props sejak merge 60734dd"
tipe: bug
status: selesai
ditemukan: "2026-10-18"
commit_perbaikan: f5caff7
dijaga_oleh: tools/regress.py (cek_palung)
tags: [bug, status/selesai, ternak, aturan-4]
---

# 🐞 Palung farm terkubur di scatter_obj_props sejak merge 60734dd

Kandang farm tidak punya palung minum sejak 11 Sep 2026. "Beri Minum" tidak
pernah muncul di pie ternak, padahal itu satu-satunya jalan mengisi air hewan
kandang (`husbandry.water` hanya dipanggil dari `_beri_minum`). Tidak ada
error, tidak ada log.

## Sebab

Di `game/scenes/props.py` blok pembangun palung

```python
world.trough = None
if getattr(scene, 'name', '') == 'farm':
    build_trough(world, *TROUGH_TILE)
```

dulu ada di akhir `default_prop_builder` (masih begitu di 18989fe). Merge
60734dd menyisipkan `scatter_obj_props` di antara loop ubin dan blok itu.
Indentasinya tetap 4 spasi, jadi blok itu jadi bagian **badan scatter**.
Scatter tidak pernah dipanggil farm, dan lagi pula keluar lebih awal lewat
`except: return` karena `make_obj_entity` tidak ada. Akibatnya
`world.trough` tidak pernah dibangun.

## Bukti (probe jalur app.py, Game3D)

Probe membuka pie dengan callback yang sama dengan app.py dan memilih
lewat `g.input(<digit>)`. Kelima ternak kandang dibuat haus (air 10%).

| | sebelum (294f869) | sesudah (f5caff7) |
|---|---|---|
| `world.trough` | None | ubin (18,4) |
| opsi pie sapi_betsy | belai, gosok, ambil_hasil, beri_makan | + beri_minum |
| pesan | "Tidak ada palung minum di sini." | "Palung diisi untuk Betsy. Air 10% -> 100%. (5 ekor ikut minum)" |
| air kelima ternak | tetap 10 | 100 |

Mutasi: blok dikembalikan ke ekor scatter, lalu `regress.py farm` GAGAL
`palung: world.trough tidak dibangun di farm`. Sesudah perbaikan LULUS.
Entity farm naik dari 1179 ke 1187 (7 papan + 1 air).

Bingkai patokan `farm_wide` tidak memuat palung. Beda sebelum/sesudah
0,28% piksel, hampir semuanya jam HUD (10:34 vs 10:28). Sisanya setara
derau dua tangkapan berurutan (0,05%).

## Yang menjaganya sekarang

`cek_palung` di `tools/regress.py` untuk scene farm: `world.trough` harus
ada, dan `_build_pie_options` (fungsi yang dipanggil app.input saat klik)
harus menawarkan `beri_minum` ke ternak kandang.

## Pelajaran

Bentuk kegagalannya sama dengan "metode disisipkan di tengah fungsi sehingga
fungsi induknya mati" yang tercatat di docstring regress.py: merge
menyisipkan kode di tengah fungsi dan menelan ekornya. Bug ini bertahan
sebulan karena tidak ada alat yang pernah memeriksa apakah palungnya ada.
