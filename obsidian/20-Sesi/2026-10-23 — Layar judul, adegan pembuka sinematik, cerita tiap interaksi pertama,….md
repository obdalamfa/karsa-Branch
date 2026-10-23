---
judul: "Layar judul, adegan pembuka sinematik, cerita tiap interaksi pertama, menu radial"
tipe: sesi
tanggal: 2026-10-23
commit: f30fca8
skala: 5 file sumber, +1235 / −99 baris
tags: [sesi]
---

# 2026-10-23 — Layar judul, adegan pembuka sinematik, cerita tiap interaksi pertama, menu radial

## Pesan commit

Permintaan pemilik: sinema dan cerita untuk intro dan tutorial di setiap
interaksi baru, menu yang lebih menarik, dan bentuk interaksi dengan
karakter dan barang diperbaiki.

- game/menu_judul.py: layar judul (Lanjutkan / Permainan Baru / Panduan /
  Keluar), kamera mengorbit dunia di belakang menu, gradasi gelap,
  keyboard + mouse. Hanya run() yang membukanya (Game3D(layar_judul=True));
  Permainan Baru di atas save minta konfirmasi dan save lama tidak dihapus.
- cutscene.py: beat baru kartu / gelap / tujuan / kamera mengorbit;
  adegan pembuka 'datang' ditulis ulang; 13 adegan interaksi pertama
  (surat, cangkul, tanam, siram, pagi kedua, peti kirim, warga, ternak,
  desa, pantai, danau, gunung, kuburan) dipicu dari state, hanya di HUD,
  tiap adegan ditutup langkah tutorial berikutnya. Save lama tidak diputar
  susulan (tandai_yang_sudah_lewat). Kamera pemain dipulihkan sesudah
  adegan, jadi arah WASD tidak bergeser.
- Menu radial ala Sims menggantikan kotak daftar ungu: nama di cakram
  tengah, kapsul pilihan melingkar dan menjulur keluar, efek motif di
  tengah, Q/E geser, F/SPACE lakukan, mouse sorot/klik, hingga 8 pilihan
  (dulu pilihan ke-7 hilang diam-diam).
- Bug lama: beat 'goyang' mengisi posisi dunia kamera dengan 0,01 (kamera
  terlempar ke titik nol); pelacak tutorial tertinggal di atas sinema;
  flash sambutan menimpa adegan pembuka dan masih menyebut [E].
- tools/probe_sinema.py: 35 cek lewat g.app.input dari jalur run().

## Berkas yang berubah

| Berkas | + | − |
|---|---:|---:|
| `game/app.py` | +109 | −44 |
| `game/cutscene.py` | +365 | −13 |
| `game/menu_judul.py` | +244 | −0 |
| `game/panels.py` | +168 | −42 |
| `tools/probe_sinema.py` | +349 | −0 |

## Bukti

Permintaan pemilik: "buat cinematic dan story untuk kebutuhan intro dan
tutorial, ada di setiap interaksi baru, buat menu lebih menarik", lalu
"interaksi sama karakter dan barang diperbaiki bentuknya".

- `tools/probe_sinema.py` (baru, baris "sinema/judul" di regress.py)
  menempuh `Game3D(layar_judul=True)`, jalur `run()`, lewat `g.app.input`:
  **36/36**. Isinya: layar judul (orbit, W/S, Panduan, ESC, Permainan Baru,
  Lanjutkan, konfirmasi menimpa save), adegan pembuka (kartu, tirai, orbit,
  tujuan tutorial, kamera pemain dipulihkan), adegan 'surat' dan 'kota',
  menu radial kasur dan 8 opsi berlabel panjang (tanpa tindih).
- Uji mutasi, tiap mutasi tertangkap tepat di ceknya:

  | mutasi | hasil |
  |---|---|
  | kamera pemain tidak dipulihkan | GAGAL "sesudah adegan surat sudut kamera dipulihkan" |
  | pemicu interaksi pertama dicabut | GAGAL 5 cek (surat, tujuan, kamera, kota, ESC) |
  | syarat 'warga' versi lama | GAGAL "warga belum tercatat sebelum bicara" |
  | kapsul radial dipusatkan | GAGAL "8 pilihan: tidak saling tindih" |

  Dua cacat alat uji ditemukan dan dibetulkan sebelum hasil itu sah.
  (1) Adegan pembuka mengorbit +140, −60, −80 = 0° bersih, jadi cek
  kamera di sana tidak menguji apa pun. (2) Larian mutasi berbagi satu
  berkas save.
- Regresi penuh, kode final (c60021a): **14/14 scene, 0 gagal**. Lima menit
  8/8 (kini menonton adegan cangkul/tanam/siram), majelis batin 26/26,
  buy/sinema 6/6, kamera Q/E 11/11. CI GitHub hijau di c60021a (2 larian).
- CI merah di antara (4751851, de53b65): ketiga probe game baru tertelan
  adegan baru (lima menit 4/8, batin 2/28, kamera 9/11). Diperbaiki di c60021a.
- Ditemukan di jalan, nyata:
  [[Getar kamera sinema melempar kamera ke titik nol]] dan
  [[Menu interaksi memotong pilihan ketujuh]]. Juga: putaran Q/E jadi
  lompatan satu frame di mesin lambat (lerp jenuh di dt ≥ 0,083), diganti
  transisi 0,25 dtk. Pelacak tutorial tertinggal di atas sinema. Flash
  sambutan menimpa adegan pembuka dan masih menyebut [E].
- Bug sendiri yang tertangkap sebelum commit: syarat 'warga' memakai
  `npc_dialog_index`, yang diisi 0 untuk semua warga sejak mereka muncul.
  Adegan "Orang Lembah" tercatat ditonton di frame pertama.

## Yang belum beres

- Belum ada probe piksel untuk getaran kamera sinema. Perbaikannya baru
  dibaca dari kode.
- ms/frame di larian regresi terakhir sekitar 2× biasanya (farm 133). Sebabnya
  **belum terverifikasi**: beban mesin atau perubahan ini. Layar judul tidak
  ikut regresi, dan menu radial hanya hidup saat dibuka.
- Adegan cerita berupa teks dan gerak kamera. Belum ada suara, potret
  pembicara, atau animasi karakter khusus adegan.
- Teks dan cerita ditulis tanpa ditinjau pemilik. Nada dan isinya
  (Paman Arsa, Naga Bumi, desa) mengikuti lore yang sudah ada di data.py.
- Tebing mulut gua di mountain masih menutupi ~85% layar (menunggu keputusan pemilik).

## Tautan

[[Status Sekarang]] · [[Peta Progres]]
