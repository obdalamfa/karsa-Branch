---
judul: "M4 r4-r5: zoom kamera roda mouse (8-24, bawaan 19); farm_wide dipotret dari jarak 13"
tipe: sesi
tanggal: 2026-10-15
commit: de8b818
skala: 7 file sumber, +238 / −113 baris
tags: [sesi]
---

# 2026-10-15 — M4 r4-r5: zoom kamera roda mouse (8-24, bawaan 19); farm_wide dipotret dari jarak 13

## Pesan commit

Kamera terkunci di jarak 19 adalah celah terbesar r3. Memotret lebih dekat
lewat --dist berarti memotret sudut yang tidak bisa dicapai pemain, jadi
zoom dipasang sungguhan di app.input (hanya mode hud) dan gauntlet_capture
memakainya lewat g.input('scroll up'). Fixture ladang: tanaman setengah
sampai siap panen. r4/r5 tetap kalah (cahaya datar, ladang tanpa tepi
rumput, tanaman identik). Regresi 14/14.

## Berkas yang berubah

| Berkas | + | − |
|---|---:|---:|
| `_bench/progress.jsonl` | +1 | −0 |
| `game/app.py` | +12 | −1 |
| `game/config.py` | +1 | −0 |
| `obsidian/10-Tahapan/Gauntlet Oktober 2026 — 10 Milestone.md` | +1 | −1 |
| `tools/fixtures/buat_save_ladang.py` | +8 | −7 |
| `tools/fixtures/ladang_hari10_save.json` | +211 | −103 |
| `tools/gauntlet_capture.py` | +4 | −1 |

## Bukti

| Ronde | Vonis | Celah terbesar menurut kritikus |
|---|---|---|
| r4 (jarak 8,5) | — (dilihat sendiri, tidak diadu) | terlalu dekat: petak besar, tanaman kecil |
| r5 (jarak 13) | patokan menang | ladang memenuhi layar tanpa tepi rumput/horizon; cahaya datar; tanaman identik; penanda biru mengacaukan |

- Zoom terbukti lewat jalur asli: `capture.py --keys "scroll up,..."` memanggil `g.input()`, dan bingkai r4/r5 jelas lebih dekat dari r3 (jarak 19).
- Regresi penuh 14/14 setelah zoom dipasang.

## Yang belum beres

- **M4 ditutup tanpa menang** (0/5). Celah tersisa: cahaya matahari terarah + bayangan, tepi rumput/bunga di sekeliling ladang, variasi model tanaman, dan penanda air yang lebih halus. Semuanya pekerjaan seni yang tidak muat di sisa jadwal gauntlet.
- Keputusan untuk sisa jadwal: M5/M6 (scene lain mengalahkan AWL) kemungkinan besar bernasib sama selama cahaya dunia belum diperbaiki. Slot tersisa lebih berguna untuk M7/M8/M10, yang bisa dibuktikan.
- Zoom belum punya tombol keyboard dan belum diumumkan di HUD kontrol.

## Tautan

[[Status Sekarang]] · [[Peta Progres]]
