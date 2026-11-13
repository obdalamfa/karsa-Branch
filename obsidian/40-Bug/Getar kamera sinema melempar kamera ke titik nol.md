---
judul: "Getar kamera sinema melempar kamera ke titik nol"
tipe: bug
status: selesai
ditemukan: "2026-10-23"
commit_perbaikan: f30fca8
dijaga_oleh: dibaca dari kode; belum ada probe piksel
tags: [bug, status/selesai, sinema]
---

# 🐞 Getar kamera sinema melempar kamera ke titik nol

## Gejala

Adegan 'mulut_gua' dan 'naga' memakai beat `('goyang', kekuatan, detik)`.
Selama beat itu, kamera tidak bergetar di tempatnya. Ia pindah ke dekat titik
nol dunia, lalu melompat kembali saat adegan berlanjut.

## Sebab

`Sinema.tick` mengisi `camera.x` dan `camera.y` dengan
`uniform(-kuat, kuat)`, yaitu angka sekecil ±0,012. Itu POSISI DUNIA kamera,
bukan simpangan, jadi kamera berpindah ke (≈0, ≈0, z).

Di akhir getaran keduanya di-nol-kan lagi. Kamera baru kembali ke tempatnya
saat beat `kamera` berikutnya atau saat pengikut kamera di HUD menariknya
dengan lerp.

## Perbaikan

Tiap frame getaran, kamera lebih dulu ditaruh di posisi sahnya
(`_snap_camera_to_player`). Getaran ditambahkan sebagai simpangan, dengan
kekuatan dikali 60 karena angka lamanya dinyatakan dalam satuan layar. Di
akhir getaran, kamera di-snap lagi.

## Yang belum beres

- Ditemukan dengan membaca kode saat menulis beat sinema baru (23 Okt 2026).
  Belum ada tangkapan atau probe yang mengukur posisi kamera selama getaran.
  Probe sinema hanya memastikan adegan berjalan sampai habis.
