---
judul: "Menu interaksi memotong pilihan ketujuh"
tipe: bug
status: selesai
ditemukan: "2026-10-23"
commit_perbaikan: f30fca8
dijaga_oleh: tools/probe_sinema.py ("semua pilihan tampil", baris "sinema/judul" di regress.py)
tags: [bug, status/selesai, ui]
---

# 🐞 Menu interaksi memotong pilihan ketujuh

## Gejala

Menu interaksi warga (pie menu) punya tujuh pilihan: Sapa, Ngobrol, Beri
Hadiah, Tanya Kabar, Puji, Ajak Tinggal Bersama, dan Gombal. Yang tampil
hanya enam. Pilihan ketujuh tidak bisa dipilih dengan panah. Ia hanya
terjangkau lewat tombol angka [7], yang tidak pernah ditulis di layar.

## Sebab

Kotak daftar lama membangun tepat enam baris teks (`range(6)`) lalu mengisi
`self._pie_items[i]` hanya untuk `i < len(...)`. Opsi ke-7 dan seterusnya
dibuang tanpa tanda.

## Perbaikan

Menu radial baru menampung hingga 8 kapsul (`_PIE_MAKS`). Ditemukan di
tangkapan pertama menu radial: Pak Hadi, 7 opsi, tampil 6.

## Bukti

`tools/probe_sinema.py` menuntut jumlah kapsul yang tampil = jumlah opsi, dan
memeriksa kapsul tidak saling tindih dengan 8 opsi berlabel panjang.
