---
judul: Arah WASD belum terverifikasi
tipe: bug
status: terbuka
berat: tinggi
ditemukan: 2026-08-27
tags: [bug, kontrol, status/terbuka]
---

# 🔴 Arah WASD belum terverifikasi benar

**Terbuka.** Ini utang paling berbahaya di proyek, bukan karena dampaknya
besar, tapi karena tidak ada cara memastikan ia beres.

## Keadaannya

Probe proyeksi layar menghasilkan angka yang **saling bertentangan**: W dan S
sama-sama terbaca "atas". Artinya **alat ukurnya** yang tidak bisa dipercaya,
bukan kodenya.

## Aturan yang berlaku sampai ada probe kokoh

> **Jangan ubah tanda lagi sebelum ada probe arah yang kokoh.**

Alasannya empiris: tanda sudah dibalik dua kali, tiap kali "diperbaiki"
berdasarkan pengamatan mata, dan tiap kali balik lagi begitu ada yang menyentuh
kamera. Membalik tanda dengan alat ukur rusak adalah melempar koin, bukan
memperbaiki.

## Bentuk probe yang dibutuhkan

Pelajaran dari [[Pemain beku saat panel terbuka]]: probe harus menempuh
**jalur asli** (`Game3D.update`), bukan memanggil `player.tick()` langsung.
Untuk arah, itu berarti mengukur perpindahan di **koordinat dunia** relatif
terhadap vektor hadap kamera saat itu, di beberapa yaw kamera berbeda, dengan
satu definisi "atas layar" yang tidak berubah di tengah pengukuran.

## Yang sudah diketahui benar

Gerakan **terjadi**: 4,65 unit/detik keempat arah tanpa exception
(commit `d8da814`), dan 21,13 unit sesudah perbaikan pembeku (`7ed8d59`).
Yang belum pasti hanya **pemetaan tombol ke arah layar**.

## Tautan

[[WASD terbalik]] · [[Status Sekarang]] · [[Regresi]]
