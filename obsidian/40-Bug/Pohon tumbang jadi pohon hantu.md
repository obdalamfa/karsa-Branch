---
judul: "Pohon tumbang jadi pohon hantu"
tipe: bug
status: selesai
ditemukan: "2026-10-18"
commit_perbaikan: (lihat commit "Pohon tumbang benar-benar rebah dan lenyap")
dijaga_oleh: _bench/probes/probe_pohon_tumbang.py (belum disambung ke regress.py)
tags: [bug, status/selesai, kapak, ditelan-except]
---

# 🐞 Pohon tumbang jadi pohon hantu

Setiap pohon yang ditebang dengan Kapak meninggalkan replika yang berdiri
tegak selamanya di tempatnya. Ubinnya sudah jadi rumput/tanah, kayu sudah
masuk tas, tapi "pohonnya" tetap terlihat. Replika berinduk `scene`, bukan
dunia scene, jadi ikut terbawa ke scene lain: probe melihat replika
pohon_mati dari cemetery masih ada setelah pindah ke mountain.

Ada sejak commit awal (454467a): `_animate_falling_tree` tidak pernah
berjalan sampai selesai.

## Sebab

Dua bug, keduanya ditelan `except Exception: pass` di
`interaction_controller.use_tool_at`:

1. `falling_root.animate_rotation(..., curve='ease_in_out')`. Ursina 8.3
   memanggil `curve(t)`, jadi string melempar `TypeError: 'str' object is
   not callable`. Fungsi berhenti di situ: tidak rebah, tidak tenggelam,
   dan `invoke(destroy, falling_root, delay=1.8)` tidak pernah dijadwalkan.
2. Batang replika memakai `model='cylinder'`, yang tidak ada di Ursina 8.3
   ("missing model: 'cylinder'"). Pohon berdiri memakai `soft_capsule_mesh`
   lewat `world._e`, jadi replika selalu tanpa batang.

## Bukti (probe jalur app.py)

`_bench/probes/probe_pohon_tumbang.py`: Kapak dipilih, pemain menghadap
pohon, `g.input('space')` -> app.input -> use_tool_at. Replika dicatat dari
`animate_rotation` sebelum animasinya jalan.

| | sebelum | sesudah |
|---|---|---|
| rotasi setelah 0,5 s (cemetery, mountain, farm) | (0,0,0) | 71-75 derajat |
| replika masih ada setelah 4 s | ya, ketiganya | tidak |
| anak replika farm | 3 tajuk, batang tanpa model | batang + 3 tajuk |
| anak replika cemetery DT | kosong | pohon_mati.obj milik sendiri |

Di 294f869 (sebelum pohon Blender) replika mountain juga masih ada setelah
4 s nyata (3 bola tajuk), jadi ini bukan akibat pohon Blender.

Mutasi: kurva dikembalikan ke string `'ease_in_out'` -> probe GAGAL
"replika tidak rebah" + "replika masih berdiri setelah 4 s (pohon hantu)"
di ketiga scene.

## Yang belum

- `except Exception: pass` di use_tool_at masih menelan apa pun yang lain;
  sengaja tidak disentuh di sini (berkas itu milik alur kerja lain).
- Probe belum disambung ke `tools/regress.py`: menebang mengubah ubin dan
  memuat ulang scene, jadi butuh tempat di ujung urutan pemeriksaan.
