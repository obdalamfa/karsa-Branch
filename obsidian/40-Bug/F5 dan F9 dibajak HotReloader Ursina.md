---
judul: "F5 dan F9 dibajak HotReloader Ursina"
tipe: bug
status: selesai
ditemukan: "2026-10-18"
commit_perbaikan: (cabang bangun-B, "Matikan development_mode Ursina")
dijaga_oleh: _bench/probes/probe_tombol_f.py
tags: [bug, status/selesai, input, simpan-muat]
---

# 🐞 F5 dan F9 dibajak HotReloader Ursina

F5 (Simpan) dan F9 (Muat) milik game ternyata juga milik Ursina. Tidak ada
probe yang melihatnya, karena semua probe memanggil `Game3D.input()` langsung
dan melewati dispatcher Ursina tempat pembajaknya duduk.

## Gejala

Pemain menekan F5 untuk menyimpan. Dunia hilang, game dibangun ulang dari
awal, dan tekstur di `assets/textures/` diam-diam diganti.

## Sebab

Ursina 8.3 menyalakan `development_mode` sendiri kecuali folder induk aset
punya `src` DAN `python` (`ursina/application.py:17-20`). Repo ini tidak punya
keduanya. Dalam mode itu Ursina membuat `HotReloader` (dibuat sebelum
`GameHandler`, jadi menerima tombol lebih dulu) dengan peta:
`f5 → reload_code`, `f6 → reload_textures`, `f7 → reload_models`,
`f8 → reload_shaders`, `f9 → toggle_hotreloading`.

## Diukur (jalur `python main.py` + `app.input`, probe_tombol_f.py)

Pendengar tombol di HUD: `HotReloader, window.input_entity, Button(cog),
GameHandler`.

| tombol | sebelum | sesudah |
|---|---|---|
| F5 | `reload_code`: `scene.clear()`, pemain hancur (`pemain_utuh` True→False), main.py di-exec ulang dengan `__file__` milik hot_reloader.py → "Folder assets tidak ditemukan" → `make_assets` **menulis ulang 64 berkas `assets/textures/*.png`** (4096/4096 piksel `grass.png` berbeda) → `Game3D` kedua dibangun | flash "[F5] Game Tersimpan!", save ada, 1 `Game3D`, 0 tekstur ditimpa |
| F9 | `toggle_hotreloading` → `ModuleNotFoundError: Xlib` (Linux); save tidak dimuat (gold tetap 7, bukan 4321) | flash "[F9] Game Dimuat!", gold 4321, jendela tetap 1280×720 |
| F6 | `reload_textures` ikut jalan, papan tetap terbuka | papan terbuka, tanpa HotReloader |
| F7 | `reload_models` | tidak ada pendengar selain GameHandler |

Di Windows, F9 kemungkinan memperkecil jendela ke separuh dan membuatnya
always-on-top (`hotreload_window_settings`) — dibaca dari kode, **belum
terverifikasi** (tidak ada mesin Windows).

## Perbaikan

`Ursina(..., development_mode=False, fullscreen=False, editor_ui_enabled=True)`
di `game/app.py`. `editor_ui_enabled=True` supaya F3 tetap menyalakan
`fps_counter` (anak `editor_ui`); diukur: F3 → 4 overlay tampak. Overlay debug
saat boot: sebelum `[cog_button]`, sesudah `[]`.

## Uji mutasi

- `development_mode` dibuang (kembali ke bawaan) → F5 menimpa 64 tekstur,
  F9 exception Xlib (= larian "sebelum").
- `editor_ui_enabled=True` dibuang → F3 tidak menampakkan overlay apa pun.
- `fullscreen=False` → None: **tidak ada beda terukur** di Xvfb (jendela
  tetap 1280×720 karena `size` diberikan). Penjaga untuk versi Ursina lain,
  bukan perbaikan terbukti.

## Pelajaran

Aturan #2 lagi: alat ukur yang memanggil `Game3D.input()` mengukur dunia tanpa
mesin. Tombol harus ditekan lewat `app.input`.
