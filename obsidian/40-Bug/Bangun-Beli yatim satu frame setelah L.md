---
judul: "Bangun/Beli yatim satu frame setelah [L]"
tipe: bug
status: selesai
ditemukan: "2026-10-18"
commit_perbaikan: (cabang bangun-B, "Bangun/Beli tidak lagi yatim")
dijaga_oleh: _bench/probes/probe_buy_sinema.py (fase L)
tags: [bug, status/selesai, input, mode]
---

# 🐞 Bangun/Beli yatim satu frame setelah [L]

[L] membuka panel Bangun/Beli (Sims S7), tapi `_pulihkan_mode_yatim` di
`game/app.py` tidak mengenal mode `'buy'`. Mode tak dikenal dikembalikan ke
HUD tiap frame, jadi satu frame setelah [L] mode sudah `'hud'` lagi: panel
tetap tergambar, W/S menggerakkan pemain alih-alih pilihan katalog, dan ESC
tidak menutupnya (ESC di HUD menyimpan game). Komentar di atas rute `'buy'`
menganggap panelnya bisa dinavigasi; tidak ada yang pernah memeriksanya
melewati satu frame.

## Diukur (lewat `g.app.input`, HUD dicapai dengan SPACE)

| cek | sebelum | sesudah |
|---|---|---|
| [L] lalu 3 frame | mode=hud, 15 entity panel menyala | mode=buy, 15 menyala |
| [S] menggeser pilihan | `_buy_sel` 0→0, mode=hud | 0→1, mode=buy |
| ESC | mode=hud, **15 entity tertinggal** | mode=hud, 0 tertinggal |

## Perbaikan

- `_pulihkan_mode_yatim`: `'buy'` yatim hanya kalau tidak satu pun
  `_buy_ents` menyala.
- `close_all` mematikan `_buy_ents`: jaring ESC global memanggil `close_all`
  SEBELUM rute `'buy'`, jadi ESC milik `buy_input` tidak pernah tercapai.

## Uji mutasi

- pendaftaran `'buy'` dibuang → fase L 0/3.
- pembersihan di `close_all` dibuang → "ESC menutup panel" GAGAL (15 entity).

## Pelajaran

Mode baru wajib didaftarkan di dua tempat: rute input setelah jaring ESC dan
`_pulihkan_mode_yatim` -- pola yang sama dengan `'sinema'` dan `'batin'`
([[Majelis Batin hilang di merge 5683e79]]).
