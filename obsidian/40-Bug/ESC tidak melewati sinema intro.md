---
judul: "ESC tidak melewati sinema intro"
tipe: bug
status: selesai
ditemukan: "2026-10-18"
commit_perbaikan: (cabang bangun-B, "ESC melewati sinema")
dijaga_oleh: _bench/probes/probe_buy_sinema.py (fase S)
tags: [bug, status/selesai, input, sinema]
---

# 🐞 ESC tidak melewati sinema intro

Sinema intro menulis "[SPACE] lanjut   [ESC] lewati", dan `Sinema.input`
memang menangani ESC (memberi beat lore yang terlewat, lalu `selesai()`).
Tapi ESC tidak pernah sampai ke sana: jaring ESC global di `game/app.py`
(`mode not in ('hud', 'chargen')` → `close_all()` + `mode = 'hud'`) duduk di
depan rute `'sinema'`.

## Gejala (diukur lewat `g.app.input`)

Sebelum: setelah ESC mode = `'hud'`, tetapi `sinema.aktif` tetap True,
**6 entity UI sinema tetap di layar** (letterbox, judul, narasi, petunjuk),
dan `'datang'` tidak masuk `sinema_selesai`. Ini juga yang mencemari foto
pembanding lama Majelis Batin di scratchpad (dicapai lewat ESC).

Sesudah: `sinema.aktif` False, 0 UI sinema, `'datang'` tercatat selesai,
mode `'hud'`.

## Perbaikan

ESC saat `mode == 'sinema'` dan `sinema.aktif` diserahkan ke
`sinema.input` SEBELUM jaring ESC. Kalau runner sudah tidak aktif, jaring
dan `_pulihkan_mode_yatim` tetap menangani mode yang macet.

## Uji mutasi

Rute ESC-sinema dimatikan → fase S 0/2 (aktif=True, 6 UI tersisa).

## Pelajaran

Jaring pengaman yang menangkap semua mode juga menangkap mode yang punya
ESC-nya sendiri. Lihat juga [[Bangun-Beli yatim satu frame setelah L]].
