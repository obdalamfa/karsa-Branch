---
judul: WASD terbalik
tipe: bug
status: selesai
ditemukan: 2026-08-26
commit_perbaikan: 09ef02f
tindak_lanjut: "[[Arah WASD belum terverifikasi]]"
tags: [bug, kontrol, status/selesai]
---

# 🐞 WASD terbalik keempat arahnya

## Gejala

Menekan W membuat karakter jalan mundur. Keempat arah salah, bukan cuma satu.

## Sebab

Kode mencampur **koordinat lokal** (`self.x`) dengan **koordinat dunia**
(`camera.world_x`). Parent `Player3D` bukan identitas, sehingga basis arah
meleset 180°.

## Perbaikan (09ef02f)

Basis diturunkan dari vektor kamera→pemain memakai koordinat **dunia di kedua
sisi**, diverifikasi lewat proyeksi lensa Panda3D pada yaw 0°, 90°, dan 215°.

## Perbaikan kedua (d8da814)

Basis arah diambil dari vektor hadap kamera milik Panda3D
(`getQuat(render).getForward()`), bukan dari selisih posisi kamera–pemain yang
tandanya disetel empiris. Versi lama rapuh: begitu ada yang menyentuh kamera,
keempat arah terbalik lagi — **dan itu sudah terjadi dua kali**.

## Status sekarang

Kodenya sudah tidak rapuh, tapi kebenarannya **belum terbukti** →
[[Arah WASD belum terverifikasi]].

## Tautan

[[2026-08-26 — Perbaiki render, kontrol, loop permainan]] ·
[[2026-08-27 — Tata letak, avatar native, tukang mesh]]
