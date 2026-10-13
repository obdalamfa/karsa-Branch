---
judul: "M1: regresi 14/14 lagi — ubin dilebur tak lagi membekukan cahaya, cek HUD dibaca sebelum motif meluruh"
tipe: sesi
tanggal: 2026-10-13
commit: 12eccfc
skala: 7 file sumber, +107 / −5 baris
tags: [sesi]
---

# 2026-10-13 — M1: regresi 14/14 lagi — ubin dilebur tak lagi membekukan cahaya, cek HUD dibaca sebelum motif meluruh

## Pesan commit

_lebur_ubin_statis memasang net state ubin (berisi salinan sm_ambient/
sm_sun_*) di node gabungan, sehingga tanah tidak pernah ikut siang-malam.
cek_hud_terbaca membandingkan piksel lama dengan warna entity setelah
arah_maju/motif_waras memutar frame. Bukti: 3 larian penuh 14/14.

## Berkas yang berubah

| Berkas | + | − |
|---|---:|---:|
| `_bench/progress.jsonl` | +6 | −0 |
| `game/world.py` | +12 | −0 |
| `obsidian/00-Peta/Status Sekarang.md` | +7 | −0 |
| `obsidian/10-Tahapan/Gauntlet Oktober 2026 — 10 Milestone.md` | +1 | −1 |
| `obsidian/40-Bug/Cek HUD membaca keadaan setelah motif meluruh.md` | +31 | −0 |
| `obsidian/40-Bug/Ubin dilebur membekukan cahaya siang-malam.md` | +40 | −0 |
| `tools/regress.py` | +10 | −4 |

## Bukti

- Sebelum: 11/14. beach `cahaya_global` turun cuma 11 (114,115,80→111,110,79); `hud_terbaca` gagal di clinic dan naga_cave dengan layar (108,196,128), hijau OK.
- Sesudah: `xvfb-run python tools/regress.py`, tiga larian penuh berturut-turut, ketiganya 14/14 dengan 0 pemeriksaan gagal (boot 2,9 / 3,1 / 3,0 dtk).
- `_bench/regress/_cahaya_b.png` kini gelap merata.

## Yang belum beres

- Pohon kelapa di beach tampil hitam pekat (terlihat di `_cahaya_a.png`). Sebabnya belum diselidiki; masuk M5.
- Belum dicek di CI GitHub. Itu terjadi otomatis saat push.

## Tautan

[[Status Sekarang]] · [[Peta Progres]]
