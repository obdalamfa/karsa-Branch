---
judul: "M8: keinginan aktif terlihat di pelacak HUD"
tipe: sesi
tanggal: 2026-10-15
commit: a3866d9
skala: 6 file sumber, +69 / −10 baris
tags: [sesi]
---

# 2026-10-15 — M8: keinginan aktif terlihat di pelacak HUD

## Pesan commit

Janji hanya terlihat di panel p, jadi pemain yang menutup panel lupa apa
yang dijanjikan. Kini satu baris 'Keinginan: <teks> maju/butuh +N' di bawah
pelacak tutorial/quest (wishes.baris_hud), kotaknya memanjang mengikuti, ikut
minggir saat panel atau Buat Karakter terbuka, dan hilang setelah dibayar.
probe_wishes 20/20 (muncul 0/5, di dalam layar, hilang setelah lunas).
Regresi 14/14.

## Berkas yang berubah

| Berkas | + | − |
|---|---:|---:|
| `_bench/progress.jsonl` | +1 | −0 |
| `game/chargen.py` | +4 | −2 |
| `game/panels.py` | +27 | −7 |
| `game/wishes.py` | +16 | −0 |
| `obsidian/10-Tahapan/Gauntlet Oktober 2026 — 10 Milestone.md` | +1 | −1 |
| `tools/probe_wishes.py` | +20 | −0 |

## Bukti

- `tools/probe_wishes.py`: 20/20. Tiga pemeriksaan baru: baris HUD `'Keinginan: Panen 5 hasil kebun apa pun  0/5'` muncul setelah panel ditutup, bounds x -0.865..-0.475 / y 0.247..0.266 ada di dalam layar, dan baris kosong lagi setelah janji dibayar.
- Tangkapan `_bench/probe/wishes_hud_janji.png` diperiksa mata: kotak pelacak memanjang dan tidak menindih roda alat.
- Regresi penuh 14/14 (termasuk "HUD di layar").

## Yang belum beres

- Keinginan belum muncul di **dialog berpotret** (DoD menyebut "dialog/HUD"; yang selesai baru HUD).
- Baris ini dijaga probe, bukan regresi: `hud_terbaca` hanya memeriksa bar, dan regresi berjalan tanpa janji aktif.
- Baris HUD tidak di-ellipsis. Janji dengan teks sangat panjang memperlebar kotak; batasnya hanya dijamin oleh pengecekan "di dalam layar" di probe.

## Tautan

[[Status Sekarang]] · [[Peta Progres]]
