---
judul: Penjaga arah jadi penjaga sungguhan — dan diagnosis lama saya salah
tipe: sesi
tanggal: 2026-10-06
commit:
tags: [sesi, uji, koreksi]
---

# 2026-10-06 — Penjaga arah akhirnya menjaga

Utang yang **sesi sebelumnya ciptakan sendiri** ditutup: pemeriksaan
`arah_maju` kembali memvonis, dan kali ini terbukti dua arah.

## Koreksi: diagnosis lama saya salah

Nota sebelumnya menyebut sebabnya **"kontaminasi antar-scene"** — pemain
tergeser dan kamera masih bergerak dari pemeriksaan scene sebelumnya. Itu
**tidak benar**, dan sekarang terukur.

`_bench/probes/probe_kontaminasi.py` menguji hipotesis pertama (posisi lokal
versus dunia): selisih **0,000 di keempat belas scene**, parent pemain
identitas. Lalu instrumentasi di dalam pemeriksaannya sendiri menunjukkan
posisi masuk = posisi keluar di tiap scene. Pemulihan keadaan bekerja persis
seperti seharusnya.

Dugaan itu masuk akal — cacat sebelumnya memang kontaminasi — tapi masuk akal
bukan bukti.

## Sebab yang sebenarnya, dua lapis

**1. Acuan diambil sesudah pemain berjalan.** Vektor "atas layar" dihitung dari
kamera→fokus **setelah** 40 frame berjalan. Di situ kamera sudah ikut bergeser
mengikuti pemain dan sempat disesuaikan pemotong dinding. Itu yang melahirkan
tuduhan **180°** di scene berbangunan (`town`, `beach`) dan tidak pernah di
lapangan terbuka (`farm`, `mountain`). Acuan sekarang diambil **sebelum**
tombol ditekan.

**2. Jendela ukurnya terlalu panjang.** Penyimpangan karena pemain menggeser
rintangan **menumpuk bersama jarak**. Diukur di scene yang sama, dua jendela
sekaligus:

| scene | 10 frame | 40 frame |
|---|---:|---:|
| lake | 11,0° | 36,0° |
| cemetery | 10,8° | 36,1° |
| mountain | 11,4° | 34,4° |
| town | 2,8° | 30,3° |
| farm | 0,0° | 0,0° |

Angka 40-frame itulah yang menuduh enam scene sehat. Yang tumbuh bukan
kesalahan arah — melainkan jarak geser di sepanjang dinding.

Vonis sekarang memakai **jendela 10 frame**, ambang **45°**. Sisa 11° adalah
tikungan saat pemain berakselerasi dari diam; ambangnya memberi ruang empat
kali lipat, sementara bug yang sesungguhnya mengukur **179°**.

## Bukti, dua arah

```
dengan perbaikan      14/14 scene lulus, 0 pemeriksaan gagal      exit 0
dengan bug dipasang    0/6  scene lulus, 6 pemeriksaan gagal      exit 1
                       farm town house lake beach smith  → 177-179 deg
```

Yang paling berarti: `house` dan `smith` — dua ruang kecil yang dulu memberi
hasil palsu — sekarang ikut menangkap bug dengan benar.

## Pelajaran yang pantas disimpan

Alat ukur yang salah bisa salah **dua kali berturut-turut dengan cara berbeda**,
dan tebakan pertama tentang sebabnya bisa keliru meski cacat sejenis baru saja
ditemukan di tempat lain. Yang menyelesaikannya bukan dugaan yang lebih baik,
tapi mengukur dua kandidat **berdampingan** di scene yang sama.

## Yang belum beres

- Empat belas probe lain yang dikutip komentar kode masih hilang → [[2026-10-03 — Probe pertama yang bisa diperiksa]].
- [[Tahap 3 — Performa]] tetap butuh mesin ber-GPU.

## Tautan

[[Arah WASD basis sumbu salah]] · [[Regresi]] · [[2026-10-04 — Arah WASD akhirnya terukur dan diperbaiki]] · [[Status Sekarang]]
