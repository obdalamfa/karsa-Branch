---
judul: Peta Progres
tipe: peta
diperbarui: 2026-09-22
tags: [moc, progres]
---

# Peta Progres

Urutan tahap diambil dari `docs/TAHAPAN.md`. Urutannya bukan selera: tiap tahap
membuka tahap berikutnya, dan tahap yang dilompati menagih ongkosnya belakangan.

Satu pengecualian yang nyata: **Tahap 5 selesai sebelum Tahap 3 dan 4**. Ia
dikerjakan di branch `claude/nice-shamir-93f5de` dan memang tahap termurah —
mesinnya sudah ada, cuma belum disambung. Urutan ideal kalah dari kerja yang
sudah terjadi, dan vault mencatat yang terjadi.

| Tahap | Status | Inti | Catatan |
|---|---|---|---|
| 0 | ✅ selesai | amankan kerja di git | [[Tahap 0 — Amankan kerja]] |
| 1 | ✅ selesai | jaring pengaman regresi, kini otomatis di CI | [[Tahap 1 — Jaring pengaman]] |
| 2 | ✅ selesai | verifikasi modul yang terlanjur ada | [[Tahap 2 — Verifikasi modul yatim]] |
| 3 | ⬜ belum | performa — garis dasar per scene sudah ada | [[Tahap 3 — Performa]] |
| 4 | ⬜ belum | Wishes — alasan untuk peduli | [[Tahap 4 — Wishes]] |
| 5 | ✅ selesai | autonomi NPC — NPC berjalan ke perabot | [[Tahap 5 — Autonomi]] |
| 6 | ⬜ belum | traits dan moodlets | [[Tahap 6 — Traits dan moodlets]] |
| 7 | ⬜ belum | misteri dan entitas | [[Tahap 7 — Misteri dan entitas]] |
| 8 | ⬜ belum | audio | [[Tahap 8 — Audio]] |

## Garis waktu commit

```mermaid
timeline
    title Riwayat Lembah Karsa 3D
    2026-05-27 : 454467a commit awal
    2026-08-26 : 09ef02f empat bug akar + loop permainan
               : 126cea8 Tahap 1 regresi
               : 2a0a26f Tahap 2 modul yatim
    2026-08-27 : d8da814 tata letak + avatar native
               : 7ed8d59 dua jebakan pembeku pemain
    2026-09-22 : vault Obsidian dibuat
               : regresi jalan sungguhan 14/14, CI dipasang
               : CI terbukti hijau di GitHub; base di-merge
               : Tahap 5 otonomi selesai (branch sebelah)
    2026-10-03 : Tahap 2 ditutup — entity_mesh terbukti + ditandai
    2026-10-04 : arah WASD terukur di 8 yaw dan diperbaiki
```

## Yang TIDAK dikejar

**Open world ala The Sims 3.** 15 scene terpisah dengan frame rate segini
membuat itu lubang tanpa dasar. Yang dikejar cukup menghilangkan *rasa*
loading: transisi instan, kamera mempertahankan sudut, mendarat di tempat yang
masuk akal. Penyimpangan ini disengaja dan tidak akan diakui sebagai kesetaraan
dengan TS3.

## Lihat juga

[[Status Sekarang]] · [[Utang Teknis]] · [[Peta Kode]]
