---
judul: Arah WASD akhirnya terukur dan diperbaiki
tipe: sesi
tanggal: 2026-10-04
commit:
tags: [sesi, bug, kontrol, bukti]
---

# 2026-10-04 — Arah WASD akhirnya terukur dan diperbaiki

Utang 🔴 tertua di vault ini, terbuka lima minggu, tutup hari ini. Bukan karena
perbaikannya sulit — dua baris — tapi karena selama ini tidak ada alat ukur
yang bisa dipercaya untuk memutuskan apa yang salah.

## 1. Kenapa probe lama memberi hasil bertentangan

Catatan lama: *"W dan S sama-sama terbaca atas, jadi alat ukurnya yang tidak
bisa dipercaya."* Sebabnya ketemu hari ini: **kamera mengikuti pemain.** Kalau
yang diukur pergeseran pemain **di layar**, jawabannya selalu "hampir nol, arah
acak" — apa pun tombol yang ditekan. Pengukurannya mustahil, bukan kodenya yang
tidak terukur.

`_bench/probes/probe_arah_wasd.py` memecahnya:

1. tombol ditekan lewat `held_keys`, frame dijalankan lewat **jalur asli** (`Game3D.update` → `player.tick`, termasuk gerbang `panels.mode`);
2. yang diukur perpindahan **dunia**, bukan layar;
3. arah dunia itu baru diubah ke arah layar lewat peta yang dikalibrasi dari **dua titik bantu nyata** — entity di (pemain + 1X) dan (pemain + 1Z) — yang diproyeksikan lensa Panda3D pada frame yang sama, kamera diam. Engine mengerjakan konversi Y-up/Z-up, jadi tidak ada konvensi yang ditebak;
4. determinan peta diperiksa: kamera tegak lurus ke bawah memang membuatnya singular, dan di situ probe **wajib** bilang "tidak bisa diukur".

Hasil pertamanya langsung konsisten: W↔S berlawanan 179,5°, A↔D 180,0°, di
keempat yaw. Alat ukurnya bisa dipercaya — dan ia melaporkan keempat arah
salah.

## 2. Yang lebih dalam daripada salah tanda

Probe juga menunjukkan W/S bergerak di diagonal dunia `(1,1)` sementara A/D di
sumbu `(1,0)`. Dua vektor itu **45° terpisah**, padahal "maju" dan "kanan"
wajib 90°. Basisnya bukan terbalik — ia **miring**.

`_bench/probes/probe_basis_kamera.py` memastikan sebabnya: kodenya membaca
`(.x, .y)` padahal bidang mendatar Ursina adalah `(x, z)` dan `y` sumbu atas.
Delapan yaw, dibandingkan basis layar sejati: rumus lama menyimpang
0°/91°/146°/179°/180°/179°/146°/91°, `dot(maju,kanan)` sampai ±0,829; rumus
`(.x,.z)` **tepat 0,0° dan dot 0,000 di kedelapan yaw**.

Rinciannya di [[Arah WASD basis sumbu salah]].

## 3. Kenapa bug ini selamat dari dua kali perbaikan

**Di yaw 0, dan hanya di yaw 0, kedua rumus memberi angka yang sama.** Yang
diuji selalu yaw awal.

## 4. Penjaga pertama saya jatuh ke jebakan yang sama

Pemeriksaan `arah_maju` ditambahkan ke [[Regresi]] — menguji **perilaku**
(tahan W, ukur perpindahan, bandingkan dengan arah kamera→fokus), bukan rumus,
supaya ia tidak bisa ikut salah bersama kodenya.

Versi pertamanya hanya memakai yaw yang sedang aktif. Diuji dengan cara
mengembalikan bug lama:

```
farm  LULUS      <- penjaganya TIDAK menangkap apa pun
town  LULUS
```

Penjaga yang dibuat untuk bug ini jatuh ke jebakan yang menyelamatkan bug ini.
Sesudah ia menyapu tiga yaw (aktif, 135°, 270°):

```
farm  GAGAL   arah_maju: yaw135: W menyimpang 179 deg      exit 1
```

Aturan yang pantas ditulis: **penjaga yang belum pernah dilihat gagal bukan
penjaga.** Itu bukan tambahan ketelitian — tanpa langkah itu, commit ini akan
mengklaim perlindungan yang tidak ada.

## 5. Penjaganya belum lolos, dan itu tidak ditutupi

Versi keempat pemeriksaan `arah_maju` menangkap bug sungguhan, tapi di larian
**14 scene** ia menuduh enam scene sehat — dua di antaranya "menyimpang 180
derajat". `town` yang dituduh itu **LULUS** saat dijalankan sendirian, dan
**LULUS** saat dijalankan sesudah `farm`.

Kegagalannya bergantung pada panjang larian, bukan pada kode yang diperiksa.
Kontaminasi antar-scene, sumbernya belum ketemu — meski posisi dan kecepatan
pemain sudah disalin-dan-dipulihkan.

Jadi ia **diturunkan jadi lapor-saja**: angkanya tetap tercetak supaya
penyimpangan besar terlihat, tapi tidak memvonis. Itu bukan menonaktifkan tes
yang menemukan bug — itu menolak mengirim alat ukur yang salah menuduh. Penjaga
yang menuduh enam scene sehat akan dimatikan orang berikutnya, dan sesudah itu
bug sungguhan lewat tanpa suara.

Yang menjaga arah sekarang: dua probe ter-commit, bisa dijalankan siapa pun.
Utangnya terbuka di [[Utang Teknis]], bukan dicatat selesai.

## Bukti

- `probe_basis_kamera.py` → 8 yaw, rumus lama menyimpang sampai 180°, rumus baru 0,0°.
- `probe_arah_wasd.py` → sesudah perbaikan: keempat arah benar di 4 yaw; W↔S 180,0°, A↔D 179,0°.
- `regress.py farm` dengan bug dipasang kembali → **GAGAL**, exit 1.
- Regresi penuh sesudah perbaikan → 14/14 lulus (dengan `arah_maju` lapor-saja).
- Larian 14 scene dengan `arah_maju` memvonis → 8/14, dan enam tuduhannya terbukti palsu saat scene-nya diuji sendirian.

## Yang belum beres

- **Pemeriksaan `arah_maju` belum jadi penjaga sungguhan** — lihat babak 5 di atas. Ini utang yang dibuat sesi ini sendiri, dan dicatat sebagai utang.
- Rumus **cadangan** di `player.py` (dipakai kalau `base` belum ada, mis. unit test murni) tidak ikut terukur — probe menempuh jalur Panda3D. Ditandai eksplisit di kodenya sebagai belum terverifikasi.
- A, S, dan D hanya diuji oleh probe, bukan oleh regresi; `arah_maju` menguji W saja supaya larian tidak jadi empat kali lebih lama. W yang benar di tiga yaw sudah menutup kelas bug ini.
- 14 probe lain yang dikutip komentar kode masih hilang → [[2026-10-03 — Probe pertama yang bisa diperiksa]].

## Tautan

[[Arah WASD basis sumbu salah]] · [[WASD terbalik]] · [[Regresi]] · [[Status Sekarang]]
