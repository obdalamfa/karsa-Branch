---
judul: CI menolak penjaga yang saya nyatakan lolos
tipe: sesi
tanggal: 2026-10-06
commit: 13e20bc
tags: [sesi, uji, ci, koreksi]
---

# 2026-10-06 — CI menolak penjaga yang saya nyatakan lolos

Beberapa jam sebelumnya saya menulis bahwa pemeriksaan `arah_maju` "lolos,
diuji dua arah". **CI tidak setuju**: larian di runner GitHub gagal pada
commit berikutnya, exit 1 di langkah regresi.

Itu persis nilai dari punya CI. Klaim saya waktu itu benar untuk mesin ini dan
untuk urutan scene yang kebetulan saya jalankan — dan tidak lebih luas.

## Satu hambatan yang harus dibereskan lebih dulu

Log CI **tidak bisa dibaca dari sesi ini**: klien API menolak redirect ke host
penyimpanan tempat GitHub menyajikan log dan artifact. Jadi yang terlihat hanya
"exit code 1" tanpa tahu scene mana.

Diperbaiki di workflow: langkah baru menempelkan `_bench/regress/report.md` ke
**ringkasan job** (`$GITHUB_STEP_SUMMARY`), dengan `if: always()`. Tabel
LULUS/GAGAL sekarang terbaca langsung di halaman Actions, tanpa mengunduh apa
pun. Kegagalan berikutnya tidak akan buta lagi.

## Dua cacat tersisa di alat ukur, keduanya diukur

**1. Jendela berpatok frame, padahal gerak berpatok jam dinding.**
`player.tick(dt)` memakai dt nyata, jadi "10 frame" di mesin lambat memberi
perpindahan jauh lebih besar daripada di mesin cepat — dan penyimpangan akibat
menggeser rintangan menumpuk bersama **jarak**, bukan bersama frame. Patokan
frame membuat pemeriksaan lulus di satu mesin dan gagal di mesin lain tanpa ada
yang berubah di kode game. Jendela sekarang ditutup oleh **jarak 0,40 satuan**,
dengan batas aman 60 frame.

**2. Jendela setengah jalan tetap memvonis.** Sesudah perbaikan pertama,
`town` yaw270 dan `beach` yaw0 gagal 180° — **tereproduksi lokal**, jadi bukan
khas runner. `_bench/probes/probe_acuan.py` membandingkan tiga acuan pada
keadaan yang sama:

```
scene   yaw   A kamera->fokus   B hadap kamera   C gerak nyata   A-B   B-C   A-C
town      0   (+0.00,+15.75)    (-0.00, +0.83)   (+0.00,+0.42)   0.0   0.0   0.0
town    270   (+15.75, +0.00)   (+0.83, +0.00)   (+0.45,+0.00)   0.0   0.0   0.0
beach     0   (+0.00,+15.75)    (-0.00, +0.83)   (+0.00,+0.46)   0.0   0.0   0.0
```

**Ketiganya sepakat 0,0 derajat.** Game benar, acuan benar. Yang salah:
gerbangnya cuma `jarak < 0,20`, jadi pemain yang tertahan dinding lalu
**terdorong mundur** 0,2–0,4 satuan lolos gerbang dan divonis menyimpang 180°.
Sekarang hanya jendela yang **benar-benar mencapai** 0,40 satuan yang boleh
memvonis; sisanya dilaporkan `terhalang`.

## Bukti

```
larian bersih 1    14/14 lulus, 0 gagal            exit 0
larian bersih 2    14/14 lulus, 0 gagal            exit 0     <- berturut-turut
dengan bug          0/7 lulus, 7 gagal (179 deg)   exit 1
                    farm town house lake beach smith swarga
```

Dua larian berturut-turut sengaja: versi sebelumnya juga pernah hijau sekali
lalu merah, jadi satu larian bukan bukti stabilitas.

## Pelajaran

Tiga kali berturut-turut cacatnya ada di alat ukur, bukan di game, dan tiap
kali dengan cara baru. Yang menghentikan pola itu bukan analisis yang lebih
pintar — tapi **mesin kedua yang tidak peduli pada keyakinan saya**. Nilai CI
di sini bukan menangkap regresi game; ia menangkap klaim saya sendiri.

## Tautan

[[2026-10-06 — Penjaga arah jadi penjaga sungguhan]] · [[Regresi]] · [[Arah WASD basis sumbu salah]]
