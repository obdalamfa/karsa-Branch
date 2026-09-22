---
judul: Font HUD tidak ketemu di mesin bersih
tipe: bug
status: selesai
berat: tinggi
ditemukan: 2026-09-22
ditemukan_oleh: percobaan menjalankan regresi headless
dijaga_oleh: seluruh regresi (game tidak bisa boot tanpa ini)
tags: [bug, boot, aset, status/selesai]
---

# 🐞 Font HUD tidak ketemu di mesin bersih

**Game mati saat boot di mesin mana pun yang tidak kebetulan sudah memasang
Montserrat.** Ini bukan bug kosmetik — ia membunuh game di baris pertama HUD.

## Gejala

```
OSError: Could not load font file: Montserrat-Bold.ttf
  panels.py:58  _txt('06:00', ...)
  panels.py:116 _build_hud()
```

Fontnya **ada** di `assets/fonts/Montserrat-Bold.ttf`. Yang salah bukan
asetnya, tapi cara ia dicari.

## Sebab, diukur

Panda3D mencari font di **model-path**, dan pencariannya **tidak menelusuri
subfolder**. Ursina hanya memasukkan akar repo ke model-path. Fontnya satu
tingkat lebih dalam, jadi tidak pernah ketemu.

Diukur di `_bench/probes/probe_font.py`:

```
akar repo di model-path (seperti main.py)      GAGAL
assets/fonts ikut di model-path                KETEMU
file ada di disk: True
```

## Kenapa tidak pernah ketahuan

Ursina juga memasukkan `C:/Windows/Fonts` ke model-path. Di mesin Windows yang
sudah memasang Montserrat — dan pemilik proyek ini jelas memasangnya — game
jalan normal. Bug ini hanya muncul di mesin bersih: komputer orang lain, mesin
baru, dan **CI**.

Ini pola yang layak diingat: aset yang ketemu lewat kebetulan lingkungan
pengembang adalah aset yang belum tersambung.

## Perbaikan

`game/app.py` menambahkan `assets/fonts` ke model-path Panda3D saat modul
diimpor — satu tempat, dipakai bersama oleh `main.py`, `tools/regress.py`, dan
`tools/capture.py`.

Sekalian: `regress.py` dan `capture.py` menunjuk
`application.fonts_folder = ROOT / 'fonts'`, folder yang **tidak ada**.
Diperbaiki ke `assets/fonts`.

## Bukti sesudah perbaikan

Regresi 14 scene jalan sampai selesai di mesin tanpa GPU dan tanpa font sistem:
**14/14 lulus**. Sebelum perbaikan, larian yang sama mati sebelum satu scene
pun sempat diuji.

## Tautan

[[2026-09-22 — Regresi jalan sungguhan, CI dipasang]] · [[Regresi]] · [[Status Sekarang]]
