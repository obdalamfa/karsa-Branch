---
judul: Objek dan Interaksi
tipe: sistem
modul: game/objects.py
baris: 181
status: jalan
pemanggil: 7
tags: [sistem, sims, status/jalan]
---

# Objek dan Interaksi — iklan yang menutup loop

`game/objects.py`. 16 perabot, 20 interaksi. **Ini yang menutup loop
permainan**: sebelumnya motif hanya bisa turun, jadi tekanan yang dibangun
[[Motif]] tidak punya jalan keluar.

## Iklan menempel pada INTERAKSI, bukan objek

Kompor tidak "memberi +45 lapar". Interaksi **Masak** pada kompor yang
mengiklankan lapar, sementara **Bersihkan** pada kompor yang sama mengiklankan
higiene ruangan. Satu objek menawarkan beberapa janji berbeda, dan sim memilih
di antaranya lewat skor (`motives.score_interaction`).

Ini arsitektur The Sims, dan alasannya praktis: menambah perabot baru tidak
perlu menyentuh mesin motif sama sekali.

## Enam kebutuhan yang ditampilkan

Mengikuti The Sims 3: lapar, kandung, energi, sosial, higiene, senang. Nyaman
dan ruang tetap ada di mesin tapi tidak lagi ditampilkan sebagai kebutuhan —
keduanya akan jadi moodlet di [[Tahap 6 — Traits dan moodlets]].

## Yang menganggur di sini

`autonomy_candidates()` (baris 148) mengembalikan kandidat (objek, interaksi,
jarak) untuk `motives.choose_action`. **Nol pemanggil** → [[Tahap 5 — Autonomi]].

## Alat di tangan

`tool_models.py` memasang model alat ke bahu kanan pemain lewat
`Player3D.refresh_held_tool()`. `build_tool()` sengaja **tanpa cache** →
[[Mesh NodePath dipakai bersama]].

## Tautan

[[Motif]] · [[Antrian Aksi]] · [[2026-08-26 — Tahap 2 sambungkan modul yatim]]
