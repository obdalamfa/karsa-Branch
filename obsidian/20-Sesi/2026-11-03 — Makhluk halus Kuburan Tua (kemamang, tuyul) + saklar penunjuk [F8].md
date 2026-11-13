---
judul: "Makhluk halus Kuburan Tua (kemamang, tuyul) + saklar penunjuk [F8]"
tipe: sesi
tanggal: 2026-11-03
commit: 7150ab1
skala: 10 file sumber, +194 / −22 baris
tags: [sesi]
---

# 2026-11-03 — Makhluk halus Kuburan Tua (kemamang, tuyul) + saklar penunjuk [F8]

## Pesan commit

Keputusan pemilik: tahap "Misteri Kuburan - tangkap 1 makhluk halus"
kini punya makhluk halus sungguhan di Kuburan Tua. Dulu kuburan tidak
punya satu pun makhluk yang bisa ditangkap (ecology.WILD_POPULASI).

- kemamang: api arwah biru melayang, malam saja, tidak disinari lampu
  dunia supaya menyala dalam gelap
- tuyul: makhluk kecil plontos berkain putih, kapan saja, lari kalau
  didekati (seperti jamur lari), peluang tangkap 40%
- kolam ekologi baru 'makhluk_kuburan' (cap 20, pulih pelan), tampil di
  panel Ekosistem; item jual 60G/75G
- penunjuk tahap Misteri Kuburan kembali ke Kuburan Tua, lalu ke makhluk
  halus terdekat ('Makhluk halus [Shift+F]')

Saklar [F8] (disimpan di save, state.penunjuk_mode): keduanya / tugas
utama saja / Cerita Dua Desa saja / mati. Tercantum di Panduan F1.

probe_tampilan 74/74: kuburan berpenghuni di game baru, model bukan
kotak polos, penunjuk ke makhluk halus, [Shift]+[F] menangkapnya dan
syarat tahap 8 terpenuhi, [F8] memutar empat mode. Mutasi 'kuburan
kosong' (5 GAGAL) dan 'F8 mati' tertangkap.

## Berkas yang berubah

| Berkas | + | − |
|---|---:|---:|
| `game/animal_models.py` | +41 | −0 |
| `game/app.py` | +7 | −0 |
| `game/data.py` | +4 | −0 |
| `game/ecology.py` | +10 | −0 |
| `game/entities.py` | +5 | −4 |
| `game/panel_daftar.py` | +1 | −0 |
| `game/panel_kartu.py` | +1 | −0 |
| `game/penunjuk.py` | +33 | −10 |
| `game/state.py` | +2 | −0 |
| `tools/probe_tampilan.py` | +90 | −8 |

## Bukti

<!-- ISI MANUAL. Angka, larian regresi, atau probe — skrip sengaja tidak
     menebak bagian ini. Lihat [[Aturan Pencatatan]]. -->

- Keputusan pemilik: "mau untuk semuanya", yaitu kuburan diberi makhluk
  halus dan dua penunjuk diberi saklar.
- `probe_tampilan` lulus 74/74:
  - game baru punya kemamang dan tuyul di cemetery
  - model chibi, bukan kotak polos
  - penunjuk desa → Kuburan Tua → "Makhluk halus [Shift+F]"
  - [Shift]+[F] menangkap, dan `_stage_done(8)` jadi True
  - [F8] memutar 4 mode
- Mutasi yang tertangkap:
  - kuburan kosong → 5 GAGAL
  - F8 mati → 1 GAGAL
- Tangkapan: kemamang biru terlihat menyala di malam hari. Tuyul lari saat
  didekati, sehingga sulit dipotret dari dekat; modelnya dibuktikan probe.
- Regresi penuh lokal: 15/15 scene, 0 pemeriksaan gagal. CI hijau di
  7150ab1.

## Yang belum beres

<!-- ISI MANUAL. Ditulis apa adanya, termasuk yang alat ukurnya belum bisa
     dipercaya. -->

- Model tuyul belum dinilai dari dekat; ukurannya dinaikkan ke 0,85 setelah
  tangkapan pertama terlalu kecil.
- Peluang tangkap tuyul 40% dan kolam 20, belum diuji dalam permainan
  panjang.

## Tautan

[[Status Sekarang]] · [[Peta Progres]]
