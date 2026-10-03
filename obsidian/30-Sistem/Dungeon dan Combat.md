---
judul: Dungeon dan Combat
tipe: sistem
modul: game/dungeon.py, game/mob.py
baris: 185 + 98
status: jalan
pemanggil: 12
tags: [sistem, combat, status/jalan]
---

# Dungeon dan Combat

`game/dungeon.py` — generator dungeon roguelike, port dari versi 2D (v17),
algoritma identik dan **tidak bergantung pada rendering**. Itu sebabnya ia
salah satu bagian paling stabil di proyek ini.

```python
generate_dungeon_level() -> (grid_2d, spawn_x, spawn_y, mob_specs_list)

grid_2d   : list[list[int]] tile ID, 24×18
spawn_x/y : koordinat tile awal pemain
mob_specs : {kind, x, y, hp, max_hp, damage, speed, drops, xp, is_boss, ...}
```

## Aturan mainnya

- 15 level bertingkat, ore + mob per level, **Boss Naga di level 15**.
- 7 jenis mob; mob mengejar pemain dalam radius 6–8 tile.
- **Z** = ayun pedang (butuh pedang dari Bengkel Budi, radius ~1,5 tile).
- KO → respawn di rumah dengan penalti energi.

## Status sambungan

12 modul menyebutnya — termasuk `tools/regress.py`, jadi dungeon ikut terjaga
[[Regresi]].

## Tautan

[[Peta Kode]] · [[Tahap 7 — Misteri dan entitas]] · [[Tahap 8 — Audio]]
