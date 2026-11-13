---
judul: "Bangun/Beli yatim satu frame setelah [L]"
tipe: bug
status: selesai
ditemukan: "2026-10-18"
commit_perbaikan: (cabang bangun-B, "Bangun/Beli tidak lagi yatim")
dijaga_oleh: tools/probe_buy_sinema.py (fase L; baris 'buy/sinema' di tools/regress.py)
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

## Penjaga di regresi

Sampai perbaikan-B probe ini tinggal di `_bench/probes/` tanpa pemanggil:
mutasi 'buy' dibuang dari `_pulihkan_mode_yatim` membuat probe_batin dan lima menit tetap hijau, dan
`tools/regress.py` keluar 0 (diukur verifikator). Sekarang probe di `tools/`
dan disambung ke regresi; mutasi yang sama di regresi penuh: buy/sinema 3/6, regresi keluar 1.

## Tata letak yang ikut terbuka

Begitu panel tidak lagi yatim, isinya benar-benar terbaca -- dan tidak muat:
baris katalog mulai y 0,15 berjarak 0,052 di latar 0,66, sehingga petunjuk
tombol menimpa baris Perapian, Kulkas dan Televisi di luar bingkai, judul
menyentuh bingkai atas (foto verifikator). Latar kini 0,64 x 0,72 di y -0,10,
baris berjarak 0,036. Cek tata letak fase L: sebelum GAGAL (judul, petunjuk,
Perapian keluar latar), sesudah bersih (14 teks); mutasi jarak baris lama
→ 5/6 ('BANGUN / BELI' menimpa '> Kursi'). Masih terbuka: flash dan popup
tutorial HUD tergambar di atas panel tengah mana pun (bukan khusus panel ini).

## Pelajaran

Mode baru wajib didaftarkan di dua tempat: rute input setelah jaring ESC dan
`_pulihkan_mode_yatim` -- pola yang sama dengan `'sinema'` dan `'batin'`
([[Majelis Batin hilang di merge 5683e79]]).
