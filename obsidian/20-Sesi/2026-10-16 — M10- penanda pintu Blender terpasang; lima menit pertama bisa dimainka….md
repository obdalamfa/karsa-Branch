---
judul: "M10: penanda pintu Blender terpasang; lima menit pertama bisa dimainkan sampai panen"
tipe: sesi
tanggal: 2026-10-16
commit: 3e7d19f
skala: 9 file sumber, +361 / −22 baris
tags: [sesi]
---

# 2026-10-16 — M10: penanda pintu Blender terpasang; lima menit pertama bisa dimainkan sampai panen

## Pesan commit

- world._pasang_penanda_pintu: mulut_gua, gapura_swarga, lubang_dungeon
  (aset 08bbf5b tanpa pemanggil) dipasang di portal gunung->gua, gua->swarga
  dan tangga dungeon; rotasi/geser diukur dari tangkapan.
- tools/probe_lima_menit.py: game baru -> Buat Karakter -> sinema -> ikuti
  petunjuk tutorial sampai panen. Menemukan tiga bug nyata:
  * tutorial & prompt menyuruh [R], yang mengganti benih -> [E]
  * [E] di depan kotak pos membuka menu peti -> kotak pos yang dihadap menang
  * say_batin/say_batin_once hilang -> cangkul pertama AttributeError
  Petunjuk tidur -> [T]. Probe 8/8, regresi 14/14.

## Berkas yang berubah

| Berkas | + | − |
|---|---:|---:|
| `_bench/progress.jsonl` | +1 | −0 |
| `game/controllers/interaction_controller.py` | +33 | −17 |
| `game/data.py` | +1 | −1 |
| `game/panels.py` | +26 | −0 |
| `game/tutorial.py` | +3 | −3 |
| `game/world.py` | +51 | −0 |
| `obsidian/10-Tahapan/Gauntlet Oktober 2026 — 10 Milestone.md` | +1 | −1 |
| `obsidian/40-Bug/Tutorial menyuruh R, cangkul pertama crash.md` | +51 | −0 |
| `tools/probe_lima_menit.py` | +194 | −0 |

## Bukti

- Sebelum: `grep` nama model → `gapura_swarga` 0, `lubang_dungeon` 0, `mulut_gua` 0 (yang 1 hanya nama adegan di cutscene).
- Tangkapan dari game asli: gapura simetris dengan celah di portal naga_cave→swarga (setelah digeser −2,1); mulut gua menghadap jalur dari desa (setelah diputar 180°); lubang dungeon di tangga (13,10).
- `probe_lima_menit.py` pertama kali: 2/3. Petunjuk `r` → `mail_read=False`. Lalu `e` pun gagal (`open_object_menu -> True`, mode `pie`). Lalu `AttributeError: say_batin_once` di cangkul pertama. Lalu tidur dengan `[E]` sesuai petunjuk tidak mengganti hari.
- Sesudah: **8/8**. Game baru (tanpa save) → Buat Karakter → sinema → surat → cangkul 3 → tanam 3 → siram 3 → tidur 2× → panen 3 lobak di hari 3.
- Regresi penuh 14/14. Save probe dibuang setelah jalan.

## Yang belum beres

- Pohon Blender (`pohon_tropis`, `kenney_tree_*`) masih 0 pemanggil. Yang dipasang slot ini baru penanda gua/gapura/dungeon.
- Probe mulai dari Buat Karakter, bukan layar judul.
- Perpindahan antar-petak di probe memakai `set_tile_pos` (WASD dijaga `arah_maju`), dan pindah scene memakai `scene_name`, bukan berjalan melewati portal.
- Probe belum masuk `regress.py`, jadi belum jalan otomatis di CI.
- Sisa Majelis Batin (`Batin`, `open_batin_check`) masih hilang.

## Tautan

[[Status Sekarang]] · [[Peta Progres]]
