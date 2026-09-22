---
judul: Avatar Vitaboy
tipe: sistem
modul: game/vitaboy_npc.py, game/vitaboy_baked.py, game/vitaboy/
baris: 168 + 725 + ~1.500
status: jalan
tags: [sistem, rupa, performa, status/jalan]
---

# Avatar Vitaboy — satu pabrik, dua backend

`game/vitaboy_npc.py` adalah **satu-satunya pintu**: `build_vitaboy_avatar()`.

## Kenapa semua lewat satu pintu

Sebelumnya `entities.py` dan `player.py` masing-masing memanggil
`VitaboyAvatar(...)` langsung, dengan `try/except` sendiri-sendiri dan tabel
outfit sendiri-sendiri. Akibatnya: **dua tabel outfit** yang tumpang tindih dan
tidak pernah diadu, dan tidak ada satu tempat pun untuk mengganti backend
skinning.

## Dua backend, urutannya ditentukan pengukuran

1. `vitaboy_baked.NativeAvatar` — `Character` Panda3D, skinning + interpolasi
   keyframe di **C++**.
2. `vitaboy.VitaboyAvatar` — skinning di **Python**, menulis ulang vertex
   buffer tiap frame.

Diukur di `_bench/probes/probe_native_wire.py` (8 avatar, 800×450, pandagl):

```
frame kosong (tanpa avatar)      9,34 ms
8 NativeAvatar                  11,64 ms  →  0,288 ms per avatar
8 VitaboyAvatar                 60,43 ms  →  6,387 ms per avatar
```

**22× lebih murah per frame.** Membangunnya juga lebih cepat setelah AnimBundle
panas: 15–25 ms lawan 76–90 ms per avatar. Ongkos tambahannya satu: bake
AnimBundle sekali per proses, ~2,6 detik, jatuh di `load_scene` pertama yang
berisi manusia.

Jalur Python **tidak dibuang** — ia jaring kalau `Character` gagal dibangun di
suatu mesin.

## Gagal-lunak tanpa aset TSO

Tanpa install The Sims Online, kedua jalur mengembalikan `None` dan pemanggil
turun ke mesh prosedural. Game harus tetap bisa dibuka dan berjalan penuh
kecepatan di mesin tanpa aset TSO — syarat BRIEF §11, diuji
`_bench/probes/probe_no_tso.py`.

## ⚠️ `PLAY.md` sudah basi soal ini

`PLAY.md` menyuruh mengedit `game/entities.py:736` → `_USE_VITABOY_HUMANS = True`.
Flag itu **tidak ada lagi di mana pun** (diperiksa 2026-09-22), dan
`entities.py` cuma 603 baris. Vitaboy sekarang aktif secara default dengan
gagal-lunak di atas → [[Utang Teknis]].

## Bake ulang

```bash
bash tools/bake_all.sh
ANIM=a2o-soc-greet-bow1 SUFFIX=greet bash tools/bake_all.sh
```

## Tautan

[[2026-08-27 — Tata letak, avatar native, tukang mesh]] · [[Tahap 3 — Performa]]
