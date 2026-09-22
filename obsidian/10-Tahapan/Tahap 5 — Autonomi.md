---
judul: Tahap 5 — Autonomi
tipe: tahap
nomor: 5
status: belum
ringkas: choose_action() sudah teruji, belum ada yang memanggilnya
tags: [tahap, status/belum, npc]
---

# Tahap 5 — Autonomi ⬜

**Termurah, dampak paling besar.** `choose_action()` dan
`autonomy_candidates()` sudah dibangun dan teruji; belum ada yang memanggilnya.
Begitu tersambung ke NPC, desa mulai hidup sendiri.

## Diperiksa ulang 2026-09-22

```
motives.py:295   def choose_action(motives, candidates, rng)
objects.py:148   def autonomy_candidates(world, tx, ty, radius=8)

grep -rn "autonomy_candidates\|choose_action" --include=*.py .
  → hanya dua baris definisi di atas. Nol pemanggil.
```

Masih persis seperti yang dicatat `docs/TAHAPAN.md`. Ini yatim jenis lain:
bukan modul utuh yang menganggur ([[Utang Teknis]]), tapi dua fungsi matang di
dalam modul yang justru sibuk dipakai untuk hal lain.

## Jalur sambungan yang sudah tersedia

`entities.py` → `npc_brain.py` → `behavior_vm.py` (459 baris) sudah jadi rantai
yang hidup. Titik sambung yang wajar adalah otak NPC: saat NPC menganggur,
minta kandidat dari `autonomy_candidates()`, pilih lewat `choose_action()`,
jalankan lewat VM perilaku.

## Tautan

[[Motif]] · [[Objek dan Interaksi]] · [[Tahap 4 — Wishes]]
