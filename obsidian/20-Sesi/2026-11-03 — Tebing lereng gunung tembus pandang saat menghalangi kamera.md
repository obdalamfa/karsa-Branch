---
judul: "Tebing lereng gunung tembus pandang saat menghalangi kamera"
tipe: sesi
tanggal: 2026-11-03
commit: a007fac
skala: 4 file sumber, +194 / −5 baris
tags: [sesi]
---

# 2026-11-03 — Tebing lereng gunung tembus pandang saat menghalangi kamera

## Pesan commit

Permintaan pemilik. Di mulut gua (18,4) tebing menutup ~85% layar:
cutaway lama hanya memendekkan dinding tepat di garis kamera-fokus.

- world.update_tembus: tiap tebing punya kotak batas; lima sinar kamera
  -> tubuh pemain (kaki, dada, kepala, bahu kiri-kanan). Yang kena
  memudar halus ke alfa 0,22, yang lain kembali pejal. Mulut gua ikut.
- Tebing luar tidak lagi dipangkas cutaway; dinding gua (probe_gua) tetap.
- Tiga jebakan, semuanya diukur: setter Ursina  memanggil .h
  milik Color (warna tebing Vec4) -> galat tertelan; skala alfa di entity
  tidak sampai ke shader (Ursina mewarnai MODEL) -> dipasang di model;
  puluhan ubin bertumpuk menjumlah jadi pejal -> bin depan-ke-belakang
  dengan tulis depth, hanya selaput terdepan yang tampak.
- probe_tampilan 56/56: 12 posisi x sudut, garis ke kepala pemain tak
  menembus tebing pejal. Mutasi 'tak dipanggil' dan 'alfa di entity'
  tertangkap.

## Berkas yang berubah

| Berkas | + | − |
|---|---:|---:|
| `game/app.py` | +3 | −0 |
| `game/scenes/rock_sanctuary.py` | +17 | −5 |
| `game/world.py` | +133 | −0 |
| `tools/probe_tampilan.py` | +41 | −0 |

## Bukti

<!-- ISI MANUAL. Angka, larian regresi, atau probe — skrip sengaja tidak
     menebak bagian ini. Lihat [[Aturan Pencatatan]]. -->

- Keputusan pemilik (3 Nov 2026): "tebing dibuat tembus pandang jika
  menghalangi pandangan kamera". Pertanyaan ini terbuka sejak 22 Okt.
- Tangkapan sebelum: 12 kombinasi posisi (18,4)/(14,4)/(20,8) dengan yaw
  0/90/180/270. Dari (18,4) di yaw 90/180 layar tertutup tebing penuh.
- Tiga jebakan, semuanya ditemukan dengan pengukuran, bukan tebakan:
  1. `ent.alpha = a` melempar AttributeError: setter Ursina memanggil `.h`
     milik Color, sedangkan warna tebing Vec4. Galatnya tertelan `try`.
  2. `ent.setAlphaScale` di entity tidak sampai ke shader. Ursina mewarnai
     MODEL: entity (1,1,1,0,22) tetap pejal, model (r,g,b,0,20) tembus.
  3. Puluhan ubin bertumpuk: 1 − 0,78¹⁰ ≈ 92% pejal (tangkapan abu-abu
     rata). Diatasi dengan cull bin `front_to_back` plus tulis depth, sehingga
     hanya selaput terdepan yang tampak.
- Sesudah: pemain terlihat di 12/12 tangkapan.
- `probe_tampilan` lulus 56/56, termasuk cek baru: garis kamera ke kepala
  pemain tidak menembus tebing pejal di 12 posisi × sudut (34 tebing pudar).
- Mutasi yang tertangkap:
  - `update_tembus` tidak dipanggil → GAGAL
  - alfa di entity → GAGAL
- Regresi penuh lokal: 15/15 scene, 0 pemeriksaan gagal, "bentuk gua" 8/8
  (dinding gua tetap memakai cutaway lama). CI hijau di a007fac.

## Yang belum beres

<!-- ISI MANUAL. Ditulis apa adanya, termasuk yang alat ukurnya belum bisa
     dipercaya. -->

- Pesan commit a007fac kehilangan satu kata (`alpha`). Backtick dalam
  heredoc dibaca shell; tidak ditulis ulang karena cabang dipakai bersama.
- Tembus pandang hanya untuk tebing luar lereng gunung dan mulut gua.
  Dinding gua (dungeon, Gua Sang Hyang) tetap memakai cutaway pemangkas
  yang dijaga `probe_gua`.
- Belum diukur ongkosnya di GPU pemilik: lima sinar × ~227 tebing, dihitung
  hanya saat kamera bergeser ≥ 0,1.
- Rasa transparansi (alfa 0,22) belum dinilai pemilik.

## Tautan

[[Status Sekarang]] · [[Peta Progres]]
