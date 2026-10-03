---
judul: Mesh NodePath dipakai bersama
tipe: bug
status: selesai
kambuh: 2
ditemukan: 2026-08-26
commit_perbaikan: 09ef02f
dijaga_oleh: geom_nol
tags: [bug, render, status/selesai]
---

# 🐞 Mesh NodePath dipakai bersama

**Bug paling mahal di proyek ini — kambuh dua kali.**

## Gejala

Dinding, rumah, dan perabot **tidak pernah muncul**. Lebih jauh: setiap NPC
humanoid dan mob hilang kecuali yang terakhir dibuat.

## Sebab

Mesh Ursina adalah **NodePath Panda3D**, dan NodePath hanya boleh punya
**satu parent**. Mesh cache diberikan ke ratusan `Entity`, sehingga setiap
`Entity` baru **mencuri node** dari yang sebelumnya. Hanya entity terakhir yang
punya geometri.

## Perbaikan

- `meshes.py` → `_instance`
- `entities.py` → `_model_instance`, jalur `.obj`

## Kambuh

| Kali | Tempat |
|---|---|
| 1 | `meshes.py` |
| 2 | `entities.py` (jalur `.obj`) — diam-diam menghapus NPC dan mob |

Karena kambuh, `build_tool()` di `tool_models.py` sengaja dibuat **tanpa
cache** ([[2026-08-26 — Tahap 2 sambungkan modul yatim]]). Itu keputusan sadar:
lebih baik bayar ongkos membangun ulang daripada mengulang bug ini ketiga kali.

## Yang menjaganya sekarang

Pemeriksaan `geom_nol` di [[Regresi]] — boot tiap scene dan cari entity
bergeometri nol.

## Tautan

[[2026-08-26 — Perbaiki render, kontrol, loop permainan]] · [[Peta Kode]]
