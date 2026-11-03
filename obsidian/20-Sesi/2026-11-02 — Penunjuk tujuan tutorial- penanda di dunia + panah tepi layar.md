---
judul: "Penunjuk tujuan tutorial: penanda di dunia + panah tepi layar"
tipe: sesi
tanggal: 2026-11-02
commit: 1a008db
skala: 3 file sumber, +445 / −0 baris
tags: [sesi]
---

# 2026-11-02 — Penunjuk tujuan tutorial: penanda di dunia + panah tepi layar

## Pesan commit

game/penunjuk.py menjawab 'ke mana' untuk tiap langkah tutorial: kotak
pos, tanah untuk dicangkul, petak siap tanam, tanaman haus, pintu rumah
lalu kasur, tanaman matang, Peti Kirim. Target di scene lain ditunjuk
lewat portal (BFS graf portal). Target lengket sampai tidak berlaku.

Rupa: ketupat emas melayang + cincin berdenyut di tanah; di luar layar
atau di balik pojok HUD, panah emas di tepi dengan label beralas.

Proyeksi layar memakai sumbu depan +z (Ursina memasang Panda yup-left);
versi pertama membaca +y dan menganggap titik di samping ada di belakang
kamera -- tertangkap lewat pengukuran di empat yaw, kini dijaga probe.

probe_tampilan 55/55; mutasi 'sumbu salah' dan 'tak dipanggil'
tertangkap.

## Berkas yang berubah

| Berkas | + | − |
|---|---:|---:|
| `game/app.py` | +8 | −0 |
| `game/penunjuk.py` | +374 | −0 |
| `tools/probe_tampilan.py` | +63 | −0 |

## Bukti

<!-- ISI MANUAL. Angka, larian regresi, atau probe — skrip sengaja tidak
     menebak bagian ini. Lihat [[Aturan Pencatatan]]. -->

- Permintaan pemilik: "lanjutkan". Diambil dari keluhan sebelumnya soal
  tutorial: kalimat tanpa arah, dan target (kotak pos, rumah, Peti Kirim) tidak
  menonjol dari kejauhan.
- Bug alat ukur yang tertangkap sendiri: proyeksi layar versi pertama membaca
  `p3.y` sebagai kedalaman. Ursina memasang Panda dengan `yup-left`, sehingga
  depan kamera adalah +z. Diukur di yaw 0/90/180/270: titik 4 petak di kanan
  pemain keluar `None` ("di belakang kamera"). Sesudah diperbaiki, x layar
  ±0,65 sesuai `camera.right`.
- Percobaan kedua juga salah: posisi diambil dari `world_position` (koordinat
  Ursina) lalu dibandingkan dengan render Panda. Sekarang dibaca lewat
  `node.getPos(base.cam)`.
- `probe_tampilan` lulus 55/55, termasuk 6 cek penunjuk: kotak pos, sembunyi
  saat panel terbuka, arah di 4 yaw, pintu rumah, kasur, dan hilang setelah
  tamat.
- Mutasi yang tertangkap:
  - sumbu kedalaman dikembalikan ke `.y` → 1 GAGAL
  - `tick` tidak dipanggil → 3 GAGAL
- Regresi penuh lokal: 15/15 scene, 0 pemeriksaan gagal.

## Yang belum beres

<!-- ISI MANUAL. Ditulis apa adanya, termasuk yang alat ukurnya belum bisa
     dipercaya. -->

- Belum ada penunjuk untuk quest utama sesudah tutorial (Ekonomi Desa,
  Bengkel, Gua); `target_langkah` baru mengenal ketujuh langkah tutorial.
- Penunjuk tidak membedakan ketinggian. Target di lantai dua atau di balik
  dinding tetap ditunjuk lurus.
- Panah tepi di pita tengah bisa menimpa kotak dialog yang sedang terbuka.
  Dalam praktik tidak terjadi karena penunjuk hanya tampil di mode HUD.
- Rasa dan ukuran penanda belum dinilai pemilik di layarnya.

## Tautan

[[Status Sekarang]] · [[Peta Progres]]
