---
judul: "Penunjuk: sasaran halus di dalam tempat, dungeon, dan penunjuk Cerita Dua Desa"
tipe: sesi
tanggal: 2026-11-03
commit: a6d2efb
skala: 3 file sumber, +264 / −30 baris
tags: [sesi]
---

# 2026-11-03 — Penunjuk: sasaran halus di dalam tempat, dungeon, dan penunjuk Cerita Dua Desa

## Pesan commit

- Bengkel: di dalamnya menunjuk Pak Budi ([U] bengkel)
- Penambang: bijih yang masih kurang (tembaga dulu, lalu besi) terdekat
- Pendekar: lawan hidup terdekat; Boss: penguasa gua bila ada di lantai
- Misteri Kuburan: makhluk liar yang SUNGGUH bisa ditangkap [Shift+F].
  Kuburan Tua tidak punya satu pun (ecology.WILD_POPULASI); syarat
  tahapnya dihitung dari tangkapan liar mana pun
- Penunjuk kedua biru-hijau untuk Cerita Dua Desa (dua_desa_stage):
  Kades Hardjo, Mbah Rukmi, papan titipan Balai Desa/Lawang (atau papan
  saat kerukunan belum cukup), longsor Lawang pada hari gotong royong.
  Diam selama tutorial; melayang lebih tinggi dan panah satu tingkat di
  bawah panah emas supaya tidak bertumpuk

probe_tampilan 69/69 (dua larian). Mutasi 'Dua Desa mati' (3 GAGAL) dan
'Kuburan lama' tertangkap; cek lawan diberi toleransi 1,5 petak karena
mob bergerak di antara frame.

## Berkas yang berubah

| Berkas | + | − |
|---|---:|---:|
| `game/app.py` | +3 | −0 |
| `game/penunjuk.py` | +163 | −25 |
| `tools/probe_tampilan.py` | +98 | −5 |

## Bukti

<!-- ISI MANUAL. Angka, larian regresi, atau probe — skrip sengaja tidak
     menebak bagian ini. Lihat [[Aturan Pencatatan]]. -->

- Permintaan pemilik: "kerjakan ketiganya", yaitu sasaran halus di dalam
  tempat, bijih/mob di dungeon, dan penunjuk Cerita Dua Desa.
- Temuan desain (bukan bug kode): tahap "Misteri Kuburan — tangkap 1 makhluk
  halus" dihitung dari `captured_supernatural`, dan angka itu naik pada
  tangkapan [Shift+F] makhluk liar mana pun. `ecology.WILD_POPULASI` tidak
  menaruh satu makhluk pun di cemetery. Penunjuk kini mengarah ke makhluk liar
  yang benar-benar bisa ditangkap. Apakah kuburan perlu diberi makhluk halus
  sungguhan adalah keputusan pemilik.
- `probe_tampilan` lulus 69/69 dalam dua larian berturut-turut. Cek baru:
  - Pak Budi di dalam Bengkel
  - makhluk liar (bukan kuburan)
  - bijih tembaga di dungeon lv3 (21 bijih)
  - lawan terdekat
  - bos di lantai
  - penunjuk Dua Desa diam selama tutorial, lalu menunjuk Kades, papan
    titipan Balai Desa (20,8), dan longsor Lawang (4,2)
- Mutasi yang tertangkap:
  - Dua Desa mati → 3 GAGAL
  - kuburan lama → GAGAL
- Pelajaran alat ukur: cek lawan versi pertama mencocokkan petak persis dan
  sempat GAGAL tanpa sebab karena mob bergerak di antara frame. Kini
  toleransinya 1,5 petak.
- Regresi penuh lokal: 15/15 scene, 0 pemeriksaan gagal. CI hijau di
  a6d2efb.

## Yang belum beres

<!-- ISI MANUAL. Ditulis apa adanya, termasuk yang alat ukurnya belum bisa
     dipercaya. -->

- Keputusan pemilik: Kuburan Tua sebagai tempat "Misteri Kuburan" tidak
  punya makhluk untuk ditangkap.
- Dua penunjuk tampil bersamaan sesudah tutorial. Kalau terlalu ramai, perlu
  saklar.
- Tahap Dua Desa 4–5 menunjuk papan titipan selama kerukunan belum cukup.
  Lomba Antar-Desa (sumber kerukunan lain) tidak ditunjuk.

## Tautan

[[Status Sekarang]] · [[Peta Progres]]
