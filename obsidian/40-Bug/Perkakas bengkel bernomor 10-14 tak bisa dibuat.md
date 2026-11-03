---
judul: "Perkakas bengkel bernomor 10-14 tak bisa dibuat (termasuk Perahu Kayu)"
tipe: bug
status: selesai
ditemukan: "2026-10-30"
commit_perbaikan: (lihat nota sesi 2026-10-30, panel berbaris)
dijaga_oleh: tools/probe_tampilan.py ("Bengkel: Perahu Kayu bisa dibuat")
tags: [bug, status/selesai, gameplay, ui]
---

# 🐞 Perkakas bengkel bernomor 10-14 tak bisa dibuat

## Gejala

Panel Bengkel [U] mencantumkan lima perkakas sebagai [10] Perahu Kayu, [11]
Jala Ikan, [12] Obor, [13] Peti Kayu, dan [14] Pagar. Tidak satu pun bisa
dibuat.

Perahu Kayu hanya bisa didapat dari bengkel, dan berlayar dari dermaga pantai
(`try_sail`) menuntut `perahu` di tas. Akibatnya pelayaran tidak pernah bisa
dicapai pemain.

## Sebab

`app.input` meneruskan tombol ke `panel_action(int(key))` hanya untuk satu
digit (`key.isdigit()`), sehingga nomor tertinggi yang bisa ditekan adalah 9.
`_craft_item` sebenarnya sanggup menangani indeks 10-14, tapi tidak ada tombol
yang bisa mengirimnya.

Ditemukan dari tangkapan panel saat menata ulang Bengkel. Lima baris itu
tergambar bernomor dua digit.

## Perbaikan

Bengkel kini bertab: Pickaxe, Pedang, dan Perkakas, dipindah dengan Q/E/TAB.
Angka 1-9 berlaku di dalam tab, lalu dipetakan ke indeks global
`_craft_item` di `panel_action`.

## Bukti

`probe_tampilan` membuka bengkel lewat [U] di scene smith, menekan [E][E],
lalu [1]. Hasilnya `perahu` 0 → 1. Mutasi "rute tab dibuang" membuat 2 cek
GAGAL.
