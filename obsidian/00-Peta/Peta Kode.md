---
judul: Peta Kode
tipe: peta
diperbarui: 2026-09-22
tags: [moc, kode]
---

# Peta Kode

19.514 baris di `game/`. Tabel ini bukan salinan `docs/CODE_MAP.md` (880 baris,
lebih rinci) — ini pintu masuknya: modul mana untuk urusan apa, dan modul mana
yang statusnya perlu diwaspadai.

## Tulang punggung

| Modul | Baris | Untuk apa |
|---|---:|---|
| `game/app.py` | 780 | Aplikasi Ursina + game loop + gerbang mode panel |
| `game/player.py` | 1197 | Kontroler pemain, gerak, alat, tabrakan |
| `game/world.py` | 1124 | Renderer tile 3D, tanah, tanaman |
| `game/panels.py` | 1145 | HUD, dialog, semua panel UI |
| `game/entities.py` | 603 | NPC, mob, wild entity + visualnya |
| `game/data.py` | 698 | Data NPC, crop, quest, mob |
| `game/state.py` | 177 | GameState + save/load JSON |
| `game/config.py` | 107 | Konstanta + tile ID |

## Sistem permainan

| Modul | Baris | Catatan | Nota |
|---|---:|---|---|
| `motives.py` | 327 | 8 motif ala TS1 | [[Motif]] |
| `action_queue.py` | 119 | antrian aksi | [[Antrian Aksi]] |
| `objects.py` | 181 | 16 perabot, 20 interaksi | [[Objek dan Interaksi]] |
| `husbandry.py` | 434 | ternak harian | [[Ternak]] |
| `economy.py` | 388 | harga, jual-beli | [[Ekonomi]] |
| `crops.py` | 633 | pertumbuhan tanaman | [[Palawija]] |
| `behavior_vm.py` | 459 | VM perilaku NPC | [[Tahap 5 — Autonomi]] |
| `npc_brain.py` | 125 | otak NPC, pemanggil `behavior_vm` | |
| `pathfinder.py` | 494 | jalur NPC & pemain | |
| `dungeon.py` | 185 | generator dungeon | [[Dungeon dan Combat]] |

## Rupa dan avatar

| Modul | Baris | Catatan | Nota |
|---|---:|---|---|
| `animator.py` | 783 | animasi | [[Avatar Vitaboy]] |
| `vitaboy_baked.py` | 725 | jalur native Panda3D (C++) | [[Avatar Vitaboy]] |
| `vitaboy_npc.py` | 168 | **satu** pabrik avatar + tabel outfit | [[Avatar Vitaboy]] |
| `meshes.py` | 711 | mesh prosedural | [[Mesh NodePath dipakai bersama]] |
| `entity_style.py` | 598 | ANGKA bahasa rupa entitas | |
| `entity_mesh.py` | 458 | tukang mesh — ⚠️ **nol pemanggil** | [[Utang Teknis]] |
| `scenes/layout.py` | 123 | tata letak ala Stardew | [[Tata Letak Scene]] |
| `scenes/zone_paint.py` | 199 | pewarnaan zona | [[Tata Letak Scene]] |

## Alat bantu (`tools/`)

| Skrip | Untuk apa |
|---|---|
| `regress.py` | jaring pengaman, 6 pemeriksaan → [[Regresi]] |
| `capture.py` | tangkapan layar untuk bukti |
| `progress_page.py` | halaman progres HTML dari `_bench/` |
| `gen_textures.py` | generate tekstur ke `assets/` |
| `bake_vitaboy.py`, `bake_all.sh` | bake avatar TSO → GLB |
| `blender_gen_models.py` | model lewat Blender |
| `catat_obsidian.py` | **tulis catatan sesi ke vault ini** → [[Aturan Pencatatan]] |

## Otomatisasi

| Berkas | Untuk apa |
|---|---|
| `.github/workflows/regresi.yml` | jalankan 14 scene tiap push & PR di atas Xvfb + Mesa, unggah bukti → [[Regresi]] |
| `requirements.txt` | `ursina`, `pygame`, `pillow` — dua terakhir sempat hilang dan membuat game tidak bisa di-import di mesin bersih |

## Dokumen panjang di `docs/`

`CODE_MAP.md` (880) · `READABILITY.md` (1021) · `BAR_STRANGERVILLE.md` (823) ·
`ENTITY_VISUAL_LANGUAGE.md` (801) · `PLAY_SIMS1.md` (808) ·
`TATA_LETAK.md` (201) · `TAHAPAN.md` (124)

Vault ini **menunjuk** ke dokumen-dokumen itu, tidak menyalinnya. Kalau isi
dokumen dan catatan bertabrakan, dokumen di `docs/` yang menang untuk detail,
catatan ini yang menang untuk status.
