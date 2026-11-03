---
judul: "Panel Warung, Dapur, Bengkel, Papan, Keinginan, Ekosistem digambar berbaris"
tipe: sesi
tanggal: 2026-10-30
commit: 71a0b10
skala: 6 file sumber, +591 / −9 baris
tags: [sesi]
---

# 2026-10-30 — Panel Warung, Dapur, Bengkel, Papan, Keinginan, Ekosistem digambar berbaris

## Pesan commit

- game/panel_daftar.py: baris berkeping nomor, ikon barang, judul dan
  keterangan, kolom kanan berjangkar tetap (lurus di font proporsional),
  pil status SIAP/KURANG/PUNYA; tab kapsul BELI/JUAL dan Bengkel
- data dan urutan sama dengan teks lama, jadi angka yang tergambar = baris
  yang dijalankan panel_action; teks mentah tetap di _panel_teks
- Ekosistem dua kolom dengan bilah sungguhan (dulu meluber keluar kartu)
- Bugfix: Bengkel bertab (Q/E). Perkakas dulu bernomor [10]-[14] sementara
  input hanya satu digit; Perahu Kayu (satu-satunya jalan berlayar) tak
  pernah bisa dibuat
- probe_tampilan 49/49 (beli lewat [1], perahu lewat [E][E][1]); dua
  mutasi tertangkap. probe_wishes membaca _panel_teks, 21/21

## Berkas yang berubah

| Berkas | + | − |
|---|---:|---:|
| `game/app.py` | +2 | −0 |
| `game/panel_daftar.py` | +454 | −0 |
| `game/panels.py` | +35 | −3 |
| `obsidian/40-Bug/Perkakas bengkel bernomor 10-14 tak bisa dibuat.md` | +43 | −0 |
| `tools/probe_tampilan.py` | +47 | −2 |
| `tools/probe_wishes.py` | +10 | −4 |

## Bukti

<!-- ISI MANUAL. Angka, larian regresi, atau probe — skrip sengaja tidak
     menebak bagian ini. Lihat [[Aturan Pencatatan]]. -->

- Permintaan pemilik: "lanjutkan tata panel warung dan lainnya".
- Tangkapan garis dasar keenam panel memperlihatkan dua cacat selain rupa:
  - Ekosistem meluber keluar kartu dan menimpa kepingan ESC.
  - Bengkel bernomor sampai [14], padahal input hanya satu digit →
    [[Perkakas bengkel bernomor 10-14 tak bisa dibuat]].
- `tools/probe_tampilan.py` lulus 49/49. Panel dibuka lewat tombol aslinya di
  tempatnya (K di shop, O di house, U di smith). [1] di Warung membeli Benih
  Lobak 3 → 4; [E][E][1] di Bengkel membuat Perahu Kayu 0 → 1.
- Mutasi yang tertangkap:
  - rute tab Bengkel dibuang → 2 GAGAL
  - panel kembali jadi tabel teks → 6 GAGAL
- `probe_wishes` kini membaca `_panel_teks` dan batas teks kanvas: 21/21.
- Regresi penuh lokal: 14/14 scene, 0 pemeriksaan gagal, termasuk "tampilan"
  49/49 dan "panel wishes" 13/13.

## Yang belum beres

<!-- ISI MANUAL. Ditulis apa adanya, termasuk yang alat ukurnya belum bisa
     dipercaya. -->

- Rasa tampilan belum dinilai pemilik di layarnya sendiri.
- Warung beli halaman 2 (ternak) dan Dapur halaman 2 belum dipotret.
  Isinya memakai baris yang sama, tapi belum dilihat.
- Ikon beberapa barang (perahu, ternak) kecil atau hanya berupa cakram warna,
  karena belum ada gambarnya.
- Tebing mulut gua di mountain masih menunggu keputusan pemilik.

## Tautan

[[Status Sekarang]] · [[Peta Progres]]
