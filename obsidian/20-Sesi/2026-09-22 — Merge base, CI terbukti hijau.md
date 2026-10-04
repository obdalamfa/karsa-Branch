---
judul: Merge base, CI terbukti hijau
tipe: sesi
tanggal: 2026-09-22
commit: 342facf
tags: [sesi, ci, merge, otonomi]
---

# 2026-09-22 — Merge base, CI terbukti hijau

Dua hal yang sebelumnya tercatat sebagai "belum terbukti" sekarang terbukti,
dan satu tahap yang tercatat "belum" ternyata sudah selesai di tangan orang
lain.

## 1. CI benar-benar jalan di GitHub

Catatan sebelumnya menulis jujur: *"workflow-nya sendiri belum pernah jalan di
GitHub."* Sekarang sudah — **4 larian, semuanya `success`**:

| Larian | Commit | Hasil |
|---|---|---|
| push + pull_request | `1424196` | ✅ success ×2 |
| push + pull_request | `fa34b26` | ✅ success ×2 |

Langkah "Jalankan regresi semua scene" berstatus `success`, dan `regress.py`
keluar dengan kode 1 kalau **satu** pemeriksaan pun gagal — jadi hijaunya
langkah itu sendiri yang membuktikan 14/14. Artifact `bukti-regresi` terunggah
**3,28 MB** (tangkapan layar + laporan), jadi langkah bukti juga bekerja.

Nama paket apt yang ditebak untuk `ubuntu-latest` (`libgl1`, `libglu1-mesa`,
`libgl1-mesa-dri`) ternyata benar; tebakan itu tidak perlu lagi dicatat sebagai
risiko.

## 2. PR konflik karena base bergerak jauh

`mergeable_state: dirty`. Base branch maju belasan commit: editor objek
(Fase 5a–5d), **otonomi NPC (Fase 6a–6c)**, harness `gauntlet/`, model
guardian, `ursina_editor/`.

Base di-merge ke sini (bukan rebase — riwayat orang lain tidak ditulis ulang).
Tiga konflik, dan **dua di antaranya karena dua agen memperbaiki hal yang sama
secara terpisah**:

| Berkas | Resolusi |
|---|---|
| `tools/regress.py` | keduanya menemukan `cek_motif_waras` bergantung urutan scene ([[Pemeriksaan motif mengotori keadaan]]). Mereka menyetel ulang `lapar` tiap scene; sesi ini menyalin-dan-memulihkan. Yang kedua dipakai karena tidak meninggalkan bekas untuk pemeriksaan sesudahnya; **penjelasan sebabnya diambil dari versi mereka**, yang lebih tepat: laju peluruhan Lapar `HUNGER_RATIO * (100 + lapar)` menuju **nol** di dasar −100 |
| `requirements.txt` | versi base dipakai utuh — ia lebih lengkap (`pygame-ce` vs `pygame`, `numpy` untuk `make_assets.py`) dan mencakup semua yang ditambahkan sesi ini |
| `.gitignore` | versi base dipakai, ditambah `.venv/` dan `venv/` yang tidak ada di sana |

Tidak ada perilaku yang hilang dari kedua sisi.

## 3. Tahap 5 ternyata sudah selesai

`choose_action()` dan `autonomy_candidates()` — dua fungsi yang vault ini
catat sebagai "nol pemanggil" beberapa jam sebelumnya — sekarang dipanggil dari
`game/npc.py`, kode game yang hidup, bukan cuma dari harness.
→ [[Tahap 5 — Autonomi]]

Catatan lama itu benar saat ditulis. Yang membuatnya usang bukan kesalahan,
tapi kerja orang lain yang mendarat di branch sebelah — dan itulah alasan
[[Status Sekarang]] harus ditulis ulang, bukan ditambal.

## Bukti

- `pip uninstall pygame && pip install -r requirements.txt` → `pygame-ce 2.5.8`, **dependensi persis seperti CI**.
- Regresi atas hasil merge: **14/14 lulus, 0 pemeriksaan gagal**.
- 4 larian CI di GitHub: semua `success`; artifact 3,28 MB terunggah.
- Rantai pemanggil otonomi diperiksa dengan `grep`: `game/npc.py:92` dan `:67`.

## Yang belum beres

- `entity_mesh.py` **masih yatim** (458 baris, nol pemanggil) — diperiksa lagi sesudah merge → [[Utang Teknis]].
- [[Arah WASD basis sumbu salah]] masih terbuka; regresi tidak menguji arah.
- 92 `.pyc` masih dilacak; `.gitignore` sudah ada tapi tidak berlaku surut.

## Tautan

Sebelumnya: [[2026-09-22 — Regresi jalan sungguhan, CI dipasang]] ·
[[Tahap 5 — Autonomi]] · [[Regresi]] · [[Status Sekarang]]
