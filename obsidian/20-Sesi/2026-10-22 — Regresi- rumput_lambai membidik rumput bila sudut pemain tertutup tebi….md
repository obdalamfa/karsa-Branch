---
judul: "Regresi: rumput_lambai membidik rumput bila sudut pemain tertutup tebing"
tipe: sesi
tanggal: 2026-10-22
commit: 13f424d
skala: 2 file sumber, +34 / −2 baris
tags: [sesi]
---

# 2026-10-22 — Regresi: rumput_lambai membidik rumput bila sudut pemain tertutup tebing

## Pesan commit

Sejak gua dan hutan integrasi/satu, mountain dibuka di mulut gua yang
dikepung tebing menerus; rumput tinggal ~0,3% layar dan cek memvonis
"rumput beku" padahal rumputnya hanya tidak tampak (branch itu sendiri
memberi tangkapan yang sama). Kalau potretan pertama < 0,5%, cek kini
mengulang SEKALI dengan kamera dibidik tegak ke rumput terdekat. Ambang
tetap 0,5%.

Mutasi: grass_shader.update_time jadi no-op -> mountain dan farm tetap
GAGAL 0,00% sesudah dibidik. Regresi penuh 14/14, kamera Q/E 11/11.

## Berkas yang berubah

| Berkas | + | − |
|---|---:|---:|
| `_bench/progress.jsonl` | +3 | −0 |
| `tools/regress.py` | +31 | −2 |

## Bukti

<!-- ISI MANUAL. Angka, larian regresi, atau probe — skrip sengaja tidak
     menebak bagian ini. Lihat [[Aturan Pencatatan]]. -->

Sesi ini menggabungkan tiga hal ke `ccr-ae8cd761-mj4kbu` (PR #15):

1. **Majelis Batin** (bangun-B + perbaiki-B), lulus verifikasi adversarial ulang.
2. **Gua naga dan hutan lebat** dari `integrasi/satu`, atas permintaan pemilik
   ("gunakan gua yang sudah diperbaiki bentuknya, begitu juga hutan").
3. **[Q]/[E] memutar kamera 45 derajat**, atas permintaan pemilik. Interaksi
   pindah ke [F], tangkap ke [Shift]+[F]. Pilihan tombol dan "lompat 45 per
   tekan" diputuskan pemilik.

Angka:

- Mountain sesudah merge gua, sebelum perbaikan alat ukur: `rumput_lambai`
  GAGAL 0,34% / 0,31% / 0,31% (3 larian). Pra-merge 0eea292: LULUS. Branch
  `integrasi/satu` sendiri: tangkapan identik (tebing menutup layar), gagal di
  `cahaya_global`.
- Sesudah bidik-rumput: mountain LULUS. Mutasi `update_time` no-op → mountain
  dan farm GAGAL 0,00% sesudah dibidik (sudut pemain 0,09% / 0,16%).
- `tools/probe_kamera_qe.py` 11/11. Mutasi handler Q/E mati → 9/11; mutasi
  `kinds` dicabut → probe meledak. Menemukan bug nyata:
  [[Interaksi di lapangan terbuka melempar TypeError]].
- Regresi penuh: **14/14 scene lulus, 0 gagal**; lima menit 8/8, majelis
  batin 26/26, buy/sinema 6/6, kamera Q/E 11/11.

## Yang belum beres

- **Tebing mountain menutup ~85% layar di mulut gua** (18,4). Alat ukurnya
  kini membidik rumput, tapi rupa yang dilihat pemain tetap: dari sudut
  bawaan, tebing menerus mendominasi. Cutaway tidak memangkas tebing yang di
  samping. [Q]/[E] membantu sedikit. Belum diperbaiki — keputusan rupa.
- Pohon Blender (bangun-C/perbaiki-C) belum di-merge: verifikator ulang
  menolak karena `model_tegak` memakai tabel `_Z_ATAS` yang sama dengan kode
  yang diujinya (lentera rebah lolos). Kini juga akan bentrok dengan
  `rock_sanctuary.py`/`props.py` dari merge gua.
- Cahaya (bangun-D) belum di-merge: verifikator menemukan ubin tanah salah
  (papan kayu di bawah pemain, kotak rumput di kaki pohon) di build bawaan.
  Agen perbaikannya terhenti batas sesi.
- [Q] benih-sebelumnya dilepas; benih kini hanya maju dengan [R].

## Tautan

[[Status Sekarang]] · [[Peta Progres]]
