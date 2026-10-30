---
judul: "M3: gauntlet_capture memotret 9 slug patokan dari game asli lalu memasangkannya buta"
tipe: sesi
tanggal: 2026-10-14
commit: ab1df9a
skala: 3 file sumber, +166 / −4 baris
tags: [sesi]
---

# 2026-10-14 — M3: gauntlet_capture memotret 9 slug patokan dari game asli lalu memasangkannya buta

## Pesan commit

capture.py ternyata memotret layar Buat Karakter, bukan dunia, sejak chargen
ditambahkan: tanpa save, panel itu menutupi scene. Kini memasang fixture save
yang sama dengan regress.py (dan membuangnya lagi). gauntlet_capture menolak
tangkapan yang scene-nya tak berganti (CAPTURE_WARN).

Bar A Short Hike tidak bisa diambil (403 kebijakan jaringan); patokan AWL
yang sudah ada dipakai sebagai bar pengganti.

## Berkas yang berubah

| Berkas | + | − |
|---|---:|---:|
| `obsidian/10-Tahapan/Gauntlet Oktober 2026 — 10 Milestone.md` | +9 | −2 |
| `tools/capture.py` | +26 | −2 |
| `tools/gauntlet_capture.py` | +131 | −0 |

## Bukti

- Larian pertama `gauntlet_capture.py` menghasilkan 9/9 PNG, tapi kesembilannya memotret panel **Buat Karakter** (lembar kontak diperiksa mata). Akar masalahnya: `capture.py` tidak memasang save, jadi chargen terbuka. Semua tangkapan `capture.py` sejak chargen ditambahkan (0943a09) terkena ini.
- Setelah perbaikan: 9/9 tangkapan memotret scene yang diminta (farm, town, house, naga_cave; jam 10–17.47), dan 9 lembar A/B buta beserta kuncinya ada di `_bench/gauntlet/r1/`.
- Berkas save fixture tidak tertinggal di root repo setelah larian.
- Jaringan: `store.steampowered.com`, `shared.akamai.steamstatic.com`, `cdn.cloudflare.steamstatic.com`, `en.wikipedia.org`, dan `ashorthike.com` → 403 di proxy (`connect_rejected`).

## Yang belum beres

- *A Short Hike* belum bisa jadi bar sampai akses jaringan dibuka. Sementara ini dipakai AWL.
- `village_wide` (`--dist 22`) tampak hampir sama dengan `character_midshot`. Jarak kamera kemungkinan dibatasi; sudutnya perlu disetel di M4/M5.
- `evening_light` (17.47) hampir tidak menghangat dibanding siang. Ini temuan untuk M4.
- Kritikus belum dijalankan; itu kerja M4.

## Tautan

[[Status Sekarang]] · [[Peta Progres]]
