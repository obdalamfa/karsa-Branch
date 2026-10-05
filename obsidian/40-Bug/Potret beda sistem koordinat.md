---
judul: Potret beda sistem koordinat
tipe: bug
status: selesai
kambuh: 0
ditemukan: 2026-10-05
commit_perbaikan: 17d570b
dijaga_oleh: belum ada
tags: [bug, alat, status/selesai]
---

# 🐞 Potret beda sistem koordinat

## Gejala

Di potret kotak dialog, topi tampil sebagai piringan besar di belakang kepala;
setelah diperbaiki, kamera malah memotret bagian belakang kepala.

## Sebab

`tools/potret.py` membuka ShowBase biasa (Z-atas), sedangkan game memakai
`coordinate-system y-up-left` dari Ursina. Topi OBJ (Assimp) dimuat mengikuti
sistem koordinat aktif, rig GLB tidak — jadi keduanya tidak sejajar. Di
sistem y-up-left, arah depan wajah juga terbalik dari asumsi kamera lama.

## Perbaikan

`loadPrcFileData('', 'coordinate-system y-up-left')` di `tools/potret.py`, dan
kamera dipindah ke `z = -1,0`.

## Pelajaran

Sama dengan aturan #2 di CLAUDE.md: alat di luar game harus menempuh
konfigurasi yang sama dengan game, atau ia mengukur dunia yang tidak ada.
