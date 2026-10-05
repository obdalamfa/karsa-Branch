---
judul: Topi diukur dari kepala sebelum diperbesar
tipe: bug
status: selesai
kambuh: 0
ditemukan: 2026-10-05
commit_perbaikan: 17d570b
dijaga_oleh: belum ada (hanya potret + close-up visual)
tags: [bug, render, karakter, status/selesai]
---

# 🐞 Topi diukur dari kepala sebelum diperbesar

## Gejala

Rambut menembus topi; tepi caping jatuh setinggi mata; topi terlihat melayang
atau tenggelam tergantung warga.

## Sebab

`besarkan_kepala` menskalakan sendi HEAD 1,16×, tetapi `_kepala_bounds`
(`getTightBounds`) membaca pose **istirahat** yang belum diskalakan. Topi
diletakkan untuk kepala yang lebih kecil daripada yang dirender. Selain itu
sendi yang diekspos belum memuat skala saat `wrtReparentTo`, sehingga
transform-nya basi.

## Perbaikan

`game/rupa_pemain.py`: batas kepala diskalakan terhadap pivot sendi HEAD
(`getNetTransform`), dan `_tempel()` memanggil `a.update(force=True)` sebelum
topi digantung di sendi.

## Pelajaran

Ukuran yang dipakai untuk menempel sesuatu harus diukur di ruang yang **sama**
dengan yang dirender — termasuk skala sendi yang dikendalikan.
