---
judul: Motif
tipe: sistem
modul: game/motives.py
baris: 327
status: jalan
pemanggil: 9
tags: [sistem, sims, status/jalan]
---

# Motif — mesin kebutuhan ala The Sims 1

`game/motives.py`. Menggantikan tiga need seragam yang lama (lapar, sosial,
senang — semuanya meluruh dalam 3,5–5,8 **hari** in-game) dengan **delapan
motif** berskala −100..+100 dan laju peluruhan asli TS1. Konstantanya diambil
dari `VMTS1MotiveDecay.Constants` lewat FreeSO; lihat `docs/PLAY_SIMS1.md` §6.

```
lapar · nyaman · higiene · kandung · energi · senang · sosial · ruang
```

## Kenapa ini soal playability, bukan kesetiaan

Need lama tidak pernah mendesak. Tiga motif yang semuanya butuh berhari-hari
untuk turun berarti pemain tidak pernah merasakan tekanan, dan tanpa tekanan
tidak ada alasan melakukan apa pun.

TS1 memakai **tiga tempo**:

| Tempo | Motif | Fungsinya |
|---|---|---|
| cepat | Nyaman ~6,7 jam, Kamar Kecil ~8 jam | menginterupsi terus-menerus |
| sedang | Lapar ~11,6 jam, Energi 16 jam | membentuk struktur **hari** |
| lambat | Higiene ~20 jam, Sosial berhari-hari | membentuk struktur **minggu** |

Tiga skala waktu adalah **minimum** untuk menghasilkan ritme.

## Dua sifat yang sengaja dipertahankan

1. **Lapar satu-satunya motif non-linear** — turun cepat saat kenyang,
   melambat saat lapar.
2. **Lapar menaikkan laju Kamar Kecil.** Satu-satunya kopling antar-motif di
   seluruh sistem, dan sumber sebagian besar komedi TS1.

## Status sambungan

Dipakai 9 modul: `interaction_controller`, `time_controller`, `npc_brain`,
`behavior_vm`, `state`, `objects`, `action_queue`, `panels`, dan
`tools/regress.py` (pemeriksaan `motif_waras`).

⚠️ Kecuali satu: **`choose_action()` (baris 295) nol pemanggil** →
[[Tahap 5 — Autonomi]].

## Rencana ke depan

[[Tahap 6 — Traits dan moodlets]] memangkas delapan motif jadi enam ala TS3;
Nyaman dan Ruangan naik status jadi moodlet.

## Tautan

[[Objek dan Interaksi]] · [[Antrian Aksi]] · [[Regresi]]
