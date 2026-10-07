---
judul: "Topi pas di kepala, rambut sesuai suku, tidak semua warga bertopi"
tipe: sesi
tanggal: 2026-10-05
commit: 17d570b
skala: 45 file sumber, +20944 / −23 baris
tags: [sesi]
---

# 2026-10-05 — Topi pas di kepala, rambut sesuai suku, tidak semua warga bertopi

## Pesan commit

- Ukuran kepala untuk topi dikoreksi skala besarkan_kepala (sebelumnya
  diukur dari pose istirahat: rambut menembus topi, caping jatuh ke mata);
  sendi diperbarui sebelum topi ditempel.
- Topi model Blender (tools/blender_topi.py -> assets/models/topi).
- Topi hanya untuk yang beralasan: caping petani, koboi, bajak laut, kru,
  mahkota swarga, pita Cici. Pak Guru, Joko, Arya, Maya, Jaka tanpa topi.
- Rambut warga dicelup lewat topeng geometri (RAMBUT_NPC): Pak Guru hitam,
  Petapa putih, Cici cokelat, dst.
- Wajah per gender (wajah.py); potret dirender dengan sistem koordinat
  game, kamera di depan wajah, sayap bidadari disembunyikan.

Regress: 13/14 scene lulus; swarga cahaya_global juga gagal di HEAD
sebelumnya (bukan regresi baru).

## Berkas yang berubah

| Berkas | + | − |
|---|---:|---:|
| `assets/blend/topi.blend` | +- | −- |
| `assets/models/topi/bajak_laut.mtl` | +32 | −0 |
| `assets/models/topi/bajak_laut.obj` | +3770 | −0 |
| `assets/models/topi/bandana.mtl` | +22 | −0 |
| `assets/models/topi/bandana.obj` | +1579 | −0 |
| `assets/models/topi/baret.mtl` | +12 | −0 |
| `assets/models/topi/baret.obj` | +771 | −0 |
| `assets/models/topi/bucket.mtl` | +22 | −0 |
| `assets/models/topi/bucket.obj` | +1394 | −0 |
| `assets/models/topi/caping.mtl` | +32 | −0 |
| `assets/models/topi/caping.obj` | +2145 | −0 |
| `assets/models/topi/ikat.mtl` | +12 | −0 |
| `assets/models/topi/ikat.obj` | +831 | −0 |
| `assets/models/topi/koboi.mtl` | +22 | −0 |
| `assets/models/topi/koboi.obj` | +1788 | −0 |
| `assets/models/topi/mahkota.mtl` | +22 | −0 |
| `assets/models/topi/mahkota.obj` | +1516 | −0 |
| `assets/models/topi/mahkota_bunga.mtl` | +52 | −0 |
| `assets/models/topi/mahkota_bunga.obj` | +5144 | −0 |
| `assets/models/topi/peci.mtl` | +22 | −0 |
| `assets/models/topi/peci.obj` | +730 | −0 |
| `assets/models/topi/pita.mtl` | +12 | −0 |
| `assets/models/topi/pita.obj` | +402 | −0 |
| `assets/textures/potret/arya.png` | +- | −- |
| `assets/textures/potret/bidadari.png` | +- | −- |
| `assets/textures/potret/bowo.png` | +- | −- |
| `assets/textures/potret/budi.png` | +- | −- |
| `assets/textures/potret/cici.png` | +- | −- |
| `assets/textures/potret/dewa_angin.png` | +- | −- |
| `assets/textures/potret/jaka_ronda.png` | +- | −- |

*…dan 15 file lain.*

## Bukti

<!-- ISI MANUAL. Angka, larian regresi, atau probe — skrip sengaja tidak
     menebak bagian ini. Lihat [[Aturan Pencatatan]]. -->

- Regresi `python tools/regress.py` (larian penuh): 11/14 scene lulus; mountain & clinic gagal `hud_terbaca` lalu **lulus** saat diuji sendiri; swarga gagal `cahaya_global` — **juga gagal** saat `rupa_pemain.py`/`wajah.py` dikembalikan ke HEAD dc6a63a, jadi bukan regresi baru.
- Potret 18 warga dirender ulang (`tools/potret.py`) dan diperiksa visual sebagai lembar kontak: topi duduk di kepala, wajah menghadap kamera.
- Close-up dalam game lewat jalur asli `Game3D` (skrip closeface di scratchpad, **tidak** ter-commit): topi Arya, Budi, Jaka, Joko, Kapten, Kru, Maya, Ningsih pas — diambil sebelum topi Arya/Joko/Maya/Jaka dilepas. Susunan topi akhir hanya dicek lewat potret.
- Sebab utama: [[Topi diukur dari kepala sebelum diperbesar]] · [[Potret beda sistem koordinat]].

## Yang belum beres

<!-- ISI MANUAL. Ditulis apa adanya, termasuk yang alat ukurnya belum bisa
     dipercaya. -->

- Bowo, Cici, Petapa terlalu kecil/duduk sehingga tidak tertangkap close-up dalam game; topi mereka hanya terverifikasi lewat potret.
- Pak Guru tanpa peci karena jambul jabrik adalah geometri kepala — perlu model rambut baru kalau peci ingin kembali.
- Pewarnaan rambut berbasis topeng geometri (ambang tinggi 0,60/0,70); Mbok Jum sengaja dikecualikan karena hasilnya lebih buruk dari uban aslinya.
- Tidak ada pemeriksaan regresi otomatis untuk posisi topi.
- Swarga gagal `cahaya_global` di regresi (juga di 17d570b dan HEAD sebelumnya) — belum diselidiki.
- `hud_terbaca` gagal acak tergantung urutan scene pada larian penuh; lulus kalau scene diuji sendiri.
- Bug pemilik yang masih antri: suasana semua scene disamakan dengan farm (#2/#9), animasi pakai alat (#11), kedip farm (#3) belum dikonfirmasi pemilik, pohon/kelapa dan interior gua via Blender.

## Tautan

[[Status Sekarang]] · [[Peta Progres]]
