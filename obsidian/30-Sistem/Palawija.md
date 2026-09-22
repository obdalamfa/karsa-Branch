---
judul: Palawija
tipe: sistem
modul: game/crops.py
baris: 633
status: jalan
tags: [sistem, tani, status/jalan]
---

# Palawija — katalog tanaman desa

`game/crops.py`. Sayur, palawija, padi, dan **pohon**.

## Kenapa modul ini ada terpisah dari `data.py`

`data.py` sudah punya `CROPS` dengan delapan tanaman, tapi bentuk datanya hanya
cukup untuk "tanam → tunggu → panen": nama, hari, harga, musim. Tidak ada
kebutuhan air, tidak ada jumlah hasil, tidak ada tanaman yang bisa dipetik
berulang, dan sama sekali tidak ada pohon.

Permintaan pemilik: palawija, pohon yang bisa ditanam, dan **aturan yang
kelihatan**.

## Aturan pendaftarannya rapi, dan itu disengaja

Modul ini **tidak menulis ulang `data.py`** (file itu dipegang agen ekonomi).
Ia **mendaftarkan diri** ke `data.CROPS` saat diimpor, dengan aturan ketat:
hanya kunci yang belum ada yang ditambahkan. Harga dan hari yang sudah ditulis
di `data.py` selalu menang.

Jadi agen ekonomi boleh memindahkan harga ke `data.py` kapan saja dan modul ini
tunduk otomatis. Ini pola yang layak ditiru saat beberapa agen menulis ke pohon
kerja yang sama.

## Status sambungan

Dipanggil `world.py`.

## Tautan

[[Ekonomi]] · [[Ternak]]
