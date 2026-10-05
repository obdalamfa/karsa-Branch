---
judul: Tahap 4 — Wishes
tipe: tahap
nomor: 4
status: belum
ringkas: Keinginan kontekstual ala TS3 — arah tanpa mencabut kebebasan
tags: [tahap, status/belum, gameplay]
---

# Tahap 4 — Wishes ⬜

**Ini yang membuat game punya alasan untuk dipedulikan.** Sekarang sudah ada
kebutuhan ([[Motif]]), objek ([[Objek dan Interaksi]]), aksi, dan antrian
([[Antrian Aksi]]) — tapi pemain bisa main lima menit lalu bertanya "terus?".

## Jawaban The Sims 3

Sim memunculkan keinginan kontekstual, pemain menjanjikan beberapa,
memenuhinya membayar Lifetime Happiness. Itu memberi arah **tanpa** mencabut
kebebasan — dan "kebebasannya seru" adalah kata-kata pemilik sendiri.

## Prioritas

Prioritas tertinggi setelah fondasi bersih. **Di atas seni apa pun.**

## Bahan yang sudah ada

| Bahan | Modul | Status |
|---|---|---|
| motif + advertising + roulette berbobot | `motives.py` | jalan |
| kandidat objek di sekitar | `objects.autonomy_candidates()` | ada, nol pemanggil |
| antrian aksi pemain | `action_queue.py` | jalan |

Wish pada dasarnya adalah kandidat aksi yang dipromosikan jadi janji. Sebagian
besar mesinnya sudah berdiri — lihat [[Tahap 5 — Autonomi]] yang memakai bahan
yang sama.

## Tautan

[[Peta Progres]] · [[Tahap 6 — Traits dan moodlets]]
