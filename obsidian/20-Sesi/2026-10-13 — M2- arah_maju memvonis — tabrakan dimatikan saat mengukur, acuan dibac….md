---
judul: "M2: arah_maju memvonis — tabrakan dimatikan saat mengukur, acuan dibaca sebelum berjalan"
tipe: sesi
tanggal: 2026-10-13
commit: bf698c5
skala: 5 file sumber, +57 / −29 baris
tags: [sesi]
---

# 2026-10-13 — M2: arah_maju memvonis — tabrakan dimatikan saat mengukur, acuan dibaca sebelum berjalan

## Pesan commit

Simpangan yang membuat cek ini cuma melapor berasal dari alat ukurnya:
langkah diagonal meluncur di dinding (yaw 135: clinic 40, studio 41 deg),
lereng/dorongan keluar petak terjepit (mountain 66/168 deg), dan arah
kamera dibaca setelah kamera tertinggal. Sesudah diperbaiki: 42/42
pengukuran 0 deg, 2 larian penuh 14/14. Rumus (.x,.y) lama dipasang
kembali di player.py -> farm/town/house GAGAL 180 deg.

## Berkas yang berubah

| Berkas | + | − |
|---|---:|---:|
| `_bench/progress.jsonl` | +7 | −0 |
| `obsidian/00-Peta/Status Sekarang.md` | +2 | −2 |
| `obsidian/00-Peta/Utang Teknis.md` | +11 | −1 |
| `obsidian/10-Tahapan/Gauntlet Oktober 2026 — 10 Milestone.md` | +1 | −1 |
| `tools/regress.py` | +36 | −25 |

## Bukti

- Sebelum (larian penuh, tabrakan hidup): mountain 66°/168°, clinic 40°, studio 41° di yaw 135; jarak 4,4–24,7 satuan per 40 frame; 7 scene punya yaw "terhalang".
- Sesudah: 14 scene × 3 yaw = 42 pengukuran, semuanya 0°, jarak 7,6–11 satuan, tidak ada yang terhalang.
- Uji mutasi: rumus basis lama `(.x,.y)` dipasang kembali di `game/player.py` → farm, town, dan house **GAGAL** `yaw0: W menyimpang 180 deg`. Berkasnya lalu dipulihkan dari salinan.
- Dua larian penuh dengan vonis aktif: 14/14 dan 14/14.

## Yang belum beres

- Cek ini hanya menguji W. A/S/D dijaga oleh cek global `arah WASD` (sekali per larian), bukan per scene × yaw.
- Sebab angka 180° yang dulu muncul di larian panjang tidak direproduksi hari ini, jadi masih belum terverifikasi.

## Tautan

[[Status Sekarang]] · [[Peta Progres]]
