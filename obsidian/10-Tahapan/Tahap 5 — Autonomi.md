---
judul: Tahap 5 — Autonomi
tipe: tahap
nomor: 5
status: selesai
ringkas: choose_action() akhirnya punya pemanggil — NPC berjalan ke perabot dan motifnya pulih
dikerjakan_oleh: branch claude/nice-shamir-93f5de (Fase 6a–6c)
tags: [tahap, status/selesai, npc]
---

# Tahap 5 — Autonomi ✅

**Termurah, dampak paling besar** — dan sejak 2026-09-22 ia **tidak lagi
menganggur**. `choose_action()` dan `autonomy_candidates()` sudah dibangun dan
teruji berbulan-bulan tanpa satu pun pemanggil; sekarang desa mulai hidup
sendiri.

## Rantai pemanggilnya, diperiksa 2026-09-22

```
game/npc.py:92            brains.pilih_otonom(...)        ← NPC hidup, bukan tes
  └─ npc_brain.py:157       autonomy_candidates(world, …)   (objects.py:148)
  └─ npc_brain.py:159       choose_action(mv, candidates…)  (motives.py:295)
game/npc.py:67            brains.selesaikan_otonom(...)   ← motif benar-benar pulih
```

`npc_brain.pilih_otonom()` menyebut dirinya sendiri dengan jujur di docstring:
*"Ini panggilan PERTAMA bagi dua fungsi yang selama ini tidak punya
pemanggil."*

Yang penting: pemanggilnya `game/npc.py`, **bukan** cuma `gauntlet/check.py`.
Kalau hanya harness yang memanggil, yatimnya hanya berpindah satu tingkat —
itu aturan 4 di `CLAUDE.md`, dan di sini ia terpenuhi.

## Pembagian tugas yang rapi

`pilih_otonom()` **tidak** mencari jalan — itu tetap tugas `PathGrid` lewat
`plan_path`. Ia hanya menjawab "perabot mana untuk kebutuhan paling mendesak",
dan hanya kalau `motive_urgent()` benar. Kalau `world` None ia mengembalikan
None supaya pemanggil jatuh ke jadwal biasa; jadi autonomi menambah perilaku
tanpa pernah menghapus yang lama.

## Tiga fase yang membangunnya

| Commit | Isi |
|---|---|
| `0b551bf` | Fase 6a — jembatan dua model motif + `target_otonom` (pemilih perabot) |
| `074884a` | Fase 6b — otonomi nyata: NPC **berjalan** ke perabot dan motif pulih saat tiba |
| `60c7e83` | Fase 6c — NPC **memakai** perabot selama durasi sebelum motif pulih |
| `02bfe64` | kecepatan gerak NPC realistis (bukan teleport) + label aksi saat memakai |

Fase 6c itu yang membuat bedanya terasa: motif yang pulih **selama** aksi
berjalan adalah prinsip yang sama dengan [[Antrian Aksi]] — pemain melihat
sebab-akibatnya, bukan hadiah yang muncul tiba-tiba.

## Catatan kejujuran

Kerja ini **bukan** dari sesi vault. Ia mendarat di branch
`claude/nice-shamir-93f5de` dan masuk ke sini lewat merge
[[2026-09-22 — Merge base, CI terbukti hijau]]. Yang diverifikasi sesi ini:
rantai pemanggil di atas, dan bahwa pemanggilnya kode game yang hidup.

## Tautan

[[Motif]] · [[Objek dan Interaksi]] · [[Tahap 4 — Wishes]] · [[Tahap 6 — Traits dan moodlets]]
