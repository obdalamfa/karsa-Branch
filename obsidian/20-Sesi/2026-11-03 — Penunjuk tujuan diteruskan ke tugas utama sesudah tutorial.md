---
judul: "Penunjuk tujuan diteruskan ke tugas utama sesudah tutorial"
tipe: sesi
tanggal: 2026-11-03
commit: 81a7157
skala: 2 file sumber, +175 / −11 baris
tags: [sesi]
---

# 2026-11-03 — Penunjuk tujuan diteruskan ke tugas utama sesudah tutorial

## Pesan commit

target_quest mengikuti syarat sungguhan QuestController._stage_done
(tahap pertama yang belum terpenuhi, bukan angka quest_stage mentah):
Bengkel untuk alat/pickaxe/pedang, tangga di Gua Sang Hyang lalu tangga
turun tiap lantai dungeon, Kuburan Tua, Gua Sang Hyang untuk Naga.
Tujuan berupa tempat ditunjuk lewat pintunya dan padam di dalam. Dari
dungeon (tanpa portal) ke luar: tangga naik.

probe_tampilan 62/62 (6 cek quest baru, adegan tiba ditandai sudah
ditonton supaya tidak menelan mode HUD). Mutasi target_quest -> None:
5 GAGAL.

## Berkas yang berubah

| Berkas | + | − |
|---|---:|---:|
| `game/penunjuk.py` | +93 | −9 |
| `tools/probe_tampilan.py` | +82 | −2 |

## Bukti

<!-- ISI MANUAL. Angka, larian regresi, atau probe — skrip sengaja tidak
     menebak bagian ini. Lihat [[Aturan Pencatatan]]. -->

- Permintaan pemilik: "lanjutkan", yaitu menerima tawaran meneruskan
  penunjuk ke quest utama.
- Target mengikuti `QuestController._stage_done`, bukan `quest_stage`
  mentah. Angka mentah bisa tertinggal karena baru maju saat
  `check_quest_progress` dipanggil.
- `probe_tampilan` lulus 62/62. Enam cek quest baru:
  - Bengkel dari kebun, dan padam di dalam Bengkel
  - Gua Sang Hyang dari lereng
  - Kuburan dari desa
  - tangga turun di dungeon, dan tangga naik untuk keluar
- Probe sendiri sempat salah dua kali:
  - Adegan tiba di tempat baru menelan mode HUD, sehingga sisa probe ikut
    GAGAL berantai.
  - Pickaxe sisa cek sebelumnya membuat tahap 4 dianggap selesai; penunjuk
    benar pindah ke tangga.

  Keduanya diperbaiki di probe, bukan di game.
- Mutasi `target_quest` → None: 5 GAGAL.
- Regresi penuh lokal: 15/15 scene, 0 pemeriksaan gagal. CI hijau di
  81a7157.

## Yang belum beres

<!-- ISI MANUAL. Ditulis apa adanya, termasuk yang alat ukurnya belum bisa
     dipercaya. -->

- Di dalam tempat tujuan (Bengkel, Kuburan, Gua Sang Hyang) penunjuk padam.
  Belum ada sasaran yang lebih halus, misalnya NPC Budi, makhluk halus di
  kuburan, atau sarang naga.
- Tahap 6–7 di dalam dungeon tidak menunjuk apa pun. Bijih dan mob tersebar,
  dan memilih satu target terdekat belum dikerjakan.
- Cerita Dua Desa (alur kedua, `dua_desa_stage`) belum punya penunjuk.

## Tautan

[[Status Sekarang]] · [[Peta Progres]]
