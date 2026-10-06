---
judul: Arah WASD terbalik dan miring — basis membaca sumbu yang salah
tipe: bug
status: selesai
berat: tinggi
ditemukan: 2026-08-27
diperbaiki: 2026-10-04
dijaga_oleh: arah_maju (tiga yaw, jendela 10 frame) + dua probe ter-commit
tags: [bug, kontrol, status/selesai]
---

# 🐞 Arah WASD: basis membaca sumbu yang salah

**Selesai 2026-10-04.** Sebelumnya nota ini berjudul *"Arah WASD belum
terverifikasi"* dan berstatus terbuka selama lima minggu — bukan karena sulit
diperbaiki, tapi karena tidak ada alat ukur yang bisa dipercaya untuk
memutuskan apa yang salah.

## Yang sebenarnya rusak

```python
fwd_x,   fwd_z   = -_f.x, -_f.y     # SALAH
right_x, right_z =  _r.x,  _r.y     # SALAH
```

Alasan yang tertulis dulu — *"Panda3D Z-up: y mendatar = z Ursina"* — tidak
berlaku di tempat itu. `getQuat(render)` relatif terhadap **akar Ursina**, dan
di Ursina bidang mendatar adalah `(x, z)` sementara `y` adalah sumbu **atas**.
Jadi yang dibaca justru komponen vertikal.

```python
fwd_x,   fwd_z   = _f.x, _f.z       # benar
right_x, right_z = _r.x, _r.z       # benar
```

## Diukur, delapan yaw

`_bench/probes/probe_basis_kamera.py` membandingkan basis yang dipakai dengan
basis layar yang diturunkan dari posisi kamera — tanpa satu tanda pun ditebak:

| yaw | `(.x,.y)` dinegasikan | `(.x,.z)` apa adanya |
|---:|---|---|
| 0 | tepat | tepat |
| 45 | 91,4° menyimpang | tepat |
| 90 | 146,0°, **"kanan" = (0,0)** | tepat |
| 135 | 178,6° menyimpang | tepat |
| 180 | **180,0° terbalik** | tepat |
| 225 | 178,6° menyimpang | tepat |
| 270 | 146,0° menyimpang | tepat |
| 315 | 91,4° menyimpang | tepat |

`dot(maju, kanan)` dulu sampai ±0,829 — dua vektor yang **wajib** tegak lurus
ternyata miring sampai 56°. Dengan `(.x,.z)`: 0,000 di kedelapan yaw.

Di yaw 90 dan 270 vektor "kanan" **runtuh jadi nol** lalu jatuh ke cadangan
`(1,0)`. Itu menjelaskan gejala yang paling membingungkan: A dan D selalu
bergerak di sumbu X dunia apa pun arah kamera.

## Kenapa ia selamat dari dua kali perbaikan

**Di yaw 0, dan hanya di yaw 0, kedua rumus memberi angka yang sama.** Yang
diuji selalu yaw awal. Dua agen sebelumnya membalik tanda, melihat yaw awal
benar, dan menyatakan beres.

## Kenapa probe lama memberi hasil bertentangan

Catatan lama: *"W dan S sama-sama terbaca atas"*. Sebabnya ketemu:
**kamera mengikuti pemain.** Kalau yang diukur pergeseran pemain **di layar**,
jawabannya selalu "hampir nol, arah acak" — apa pun tombolnya. Bukan kodenya
yang tidak bisa diukur; alat ukurnya yang mustahil.

`_bench/probes/probe_arah_wasd.py` memecahnya: ukur perpindahan **dunia**, lalu
ubah ke arah layar lewat peta yang dikalibrasi dari dua titik bantu nyata yang
diproyeksikan lensa Panda3D pada frame yang sama. Determinan peta itu diperiksa
— kamera yang memandang tegak lurus ke bawah memang membuatnya singular, dan
di situ probe **wajib** bilang "tidak bisa diukur", bukan mengarang arah.

Sesudah perbaikan, keempat arah benar di keempat yaw yang diuji:

```
yaw  45   W 91,6 deg ATAS   S 271,6 BAWAH   A 178,7 KIRI   D 357,6 KANAN
yaw 135   W 90,0 deg ATAS   S 270,0 BAWAH   A 180,6 KIRI   D 359,5 KANAN
yaw 225   W 88,4 deg ATAS   S 268,4 BAWAH   A 182,0 KIRI   D   1,7 KANAN
yaw 315   W 90,0 deg ATAS   S 270,0 BAWAH   A 180,4 KIRI   D 359,5 KANAN
W<->S berlawanan 180,0 deg      A<->D berlawanan 179,0 deg
```

## Penjaganya: `arah_maju`, dan dua probe ter-commit

> [!success] Pemeriksaan `arah_maju` memvonis sejak 2026-10-06
> Diuji dua arah: 14/14 lulus dengan perbaikan, 6/6 GAGAL (177–179°) saat bug
> dipasang kembali — termasuk `house` dan `smith`, dua ruang kecil yang dulu
> memberi hasil palsu. Riwayat lima versinya ada di [[Regresi]].

## Penjaga yang gagal empat kali

Pemeriksaan `arah_maju` di [[Regresi]] menguji **perilaku**: tahan W lewat
`held_keys`, jalankan frame lewat jalur asli, bandingkan perpindahan dunia
dengan arah kamera→fokus. Rumus basisnya **tidak disalin** ke harness —
salinan yang ikut salah tidak menjaga apa pun.

Versi **pertama** penjaga itu hanya memakai yaw yang sedang aktif. Diuji dengan
cara mengembalikan bug lama: **farm dan town tetap LULUS.** Penjaganya jatuh ke
jebakan yang sama dengan bug yang hendak dijaganya. Sesudah ia menyapu tiga yaw:

```
farm   GAGAL   arah_maju: yaw135: W menyimpang 179 deg
```

Itu sebabnya aturannya layak ditulis: **penjaga yang belum pernah dilihat gagal
bukan penjaga.**

### Versi keempat belum lolos, dan sebabnya bukan yang saya kira

Dengan keadaan pemain disalin-dan-dipulihkan dan scene terhalang tidak dihukum,
tiga scene yang diuji berurutan lulus. Tapi larian **14 scene penuh**:

```
8/14 scene lulus, 6 pemeriksaan gagal
  town  yaw0: W menyimpang 180 deg      lake      yaw135: 33 deg
  beach yaw0: W menyimpang 180 deg      cemetery  yaw135: 32 deg
  shop  yaw135: 34 deg                  studio    yaw135: 34 deg
```

Lalu `town` diuji sendirian: **LULUS**. Diuji sesudah `farm`: **LULUS**.

Dugaan saat itu: kontaminasi antar-scene. **Salah.** `probe_kontaminasi.py`
mengukur selisih posisi lokal lawan dunia **0,000 di keempat belas scene**, dan
instrumentasi di dalam pemeriksaannya menunjukkan posisi masuk = posisi keluar.

Sebab sebenarnya ada dua, keduanya di alat ukur: **acuan diambil sesudah
pemain berjalan** (kamera sudah ikut bergeser dan dipotong dinding — itu
sumber tuduhan 180° yang hanya muncul di scene berbangunan), dan **jendela ukur
terlalu panjang** (penyimpangan karena menggeser rintangan menumpuk: 11° pada
10 frame menjadi 36° pada 40 frame).

Versi kelima mengukur di jendela 10 frame dengan acuan pra-jalan, ambang 45°.
Rinciannya di [[Regresi]] dan
[[2026-10-06 — Penjaga arah jadi penjaga sungguhan]].

## Tautan

[[WASD terbalik]] · [[Regresi]] · [[2026-10-04 — Arah WASD akhirnya terukur dan diperbaiki]]
