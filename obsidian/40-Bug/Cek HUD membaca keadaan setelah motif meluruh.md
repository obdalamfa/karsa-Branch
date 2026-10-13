---
judul: "Cek HUD membaca keadaan setelah motif meluruh"
tipe: bug
status: selesai
ditemukan: "2026-10-13"
commit_perbaikan: (sesi gauntlet M1, 2026-10-13)
dijaga_oleh: hud_terbaca
tags: [bug, status/selesai, alat-ukur]
---

# 🐞 Cek HUD membaca keadaan setelah motif meluruh

Ini bug alat ukur, bukan bug game.

## Gejala

`hud_terbaca` gagal acak di larian penuh, misalnya `bar5 layar(108,…)`
di clinic dan naga_cave, padahal lulus kalau scene dijalankan sendiri.

## Sebab

Tangkapan layar diambil lebih dulu. Setelah itu `arah_maju` dan
`motif_waras` memutar `taskMgr`, baru `hud_terbaca` membaca `entity.color`.
Di sela itu motif meluruh melewati ambang OK→WARN. Hasilnya, layar menunjukkan
hijau (108,196,128) sementara entity-nya kini meminta kuning. Kedua sumber
yang dibandingkan berasal dari dua saat yang berbeda.

## Perbaikan

`hud_kontras` dan `hud_terbaca` kini dijalankan tepat setelah tangkapan,
sebelum cek lain menjalankan frame.
