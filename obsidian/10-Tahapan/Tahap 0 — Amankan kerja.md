---
judul: Tahap 0 — Amankan kerja
tipe: tahap
nomor: 0
status: selesai
ringkas: Seluruh sesi masuk git, berhenti bergantung pada working tree
commit: 09ef02f
tags: [tahap, status/selesai]
---

# Tahap 0 — Amankan kerja ✅

**Selesai** di commit `09ef02f`: 96 file, 12.296 baris.

## Kenapa ini nomor nol

Sebelum commit itu seluruh hasil sesi hidup di working tree tanpa jaring apa
pun, dan satu agen pernah menjalankan `git stash` di tengah kerja agen lain.
Kerja yang tidak ter-commit bukan kerja yang selesai — ia cuma kerja yang belum
hilang.

## Akibat yang masih terasa

Commit besar itu juga menyeret `__pycache__` masuk. Lihat [[Utang Teknis]]
(92 file `.pyc` tercatat di git, belum ada `.gitignore` root).

## Tautan

Sesi: [[2026-08-26 — Perbaiki render, kontrol, loop permainan]] ·
Lanjut ke [[Tahap 1 — Jaring pengaman]]
