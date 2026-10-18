---
judul: "arah_maju terlempar portal di mesin lambat"
tipe: bug
status: selesai
ditemukan: "2026-10-16"
commit_perbaikan: 294f869
dijaga_oleh: arah_maju, scene_tetap, _bench/probes/probe_regress_lambat.py
tags: [bug, status/selesai, alat-ukur]
---

# 🐞 arah_maju terlempar portal di mesin lambat

Ini bug alat ukur, bukan bug game. Portal memang harus memindahkan scene.

## Gejala

Di larian penuh mesin sesi 16 Okt 2026, empat dari lima larian memberi:

- farm termuat **689** entity, padahal biasanya 1179;
- `arah_maju`: "yaw270: W menyimpang 157 deg (jarak 26.00u)";
- `cahaya_global`: "(39, 40, 43) -> (29, 31, 35)" (turun 27 < 30).

`regress.py farm` sendirian lulus. CI GitHub hijau. Waktu itu sebabnya belum
terverifikasi (lihat callout di [[Gauntlet Oktober 2026 — 10 Milestone]]).

## Sebab (terukur 18 Okt 2026)

1. `cek_arah_maju` mematikan tabrakan (`world.is_walkable = lambda: True`)
   lalu menahan W **tepat 40 frame**. Jarak tempuhnya Σ v·dt, jadi ikut lama
   frame: fisika `v += 85·dt`, `v *= exp(-14·dt)` di `player.py` memberi
   3,1 u pada dt 16 ms, 9,7 u pada 68 ms, dan **11,04–11,16 u pada
   100–130 ms**. Komentar lama "40 frame memberi 3-4 satuan" hanya benar di
   mesin 60 fps.
2. Farm mulai di petak (19,5) = dunia (38, 10). Di yaw 270, W bergerak ke +x.
   Portal `[25,5,'greenhouse',7,10]` terpicu begitu x ≥ 49, yaitu **11,0 u**.
   Jadi portal hanya terjangkau di jendela dt sempit ~0,10–0,13 s. Itulah
   keadaan mesin sesi 16 Okt (111–124 ms/frame). Satu larian yang lulus
   (109 ms) ada di tepi jendela.
3. `finally` di cek itu memulihkan posisi, tapi **tidak memulihkan scene**.
   `cahaya_global` dan jumlah entity lalu mengukur greenhouse (689), dengan
   pemain di koordinat farm.
4. Angkanya cocok persis: lompatan dari (38,10) ke tujuan greenhouse
   (7,10)·2 = (14,20) adalah hypot(−24, 10) = **26,00 u**, sudut
   atan2(10, −24) = **157,4°**.

Ada celah kedua yang lebih diam. Di larian penuh kecepatan normal, naga_cave
terlempar **dua kali**: naga_cave(7,5) → swarga, lalu swarga(15,22) →
naga_cave(7,6). Cek itu LULUS "0:0d/8.5u" hanya karena kebetulan geometri.
Itu pengukuran tidak sah yang lolos tanpa suara.

Hipotesis "sendirian vs penuh" terbantah. Farm adalah scene pertama di kedua
mode, dan jalurnya identik sampai farm diperiksa.

## Perbaikan (294f869)

- Loop W berhenti begitu jarak ≥ **3,0 u** atau scene berganti. Batas 40
  frame tetap ada. Jarak tempuh kini lepas dari dt.
- Kalau scene tetap berganti, itu dicatat sebagai kegagalan eksplisit "alat
  ukur terlempar portal ke … -- bukan vonis arah". Scene dipulihkan lewat
  jalur transisi asli `app.py`.
- Jaring umum `scene_tetap` di loop utama: kalau `world.scene_name` atau
  `state.scene_name` bukan scene yang sedang diperiksa, barisnya GAGAL.
  Angka satu baris tidak boleh diam-diam milik scene lain.
- `_bench/probes/probe_regress_lambat.py` menjalankan `regress.py` ASLI
  dengan `--lambat=MS` (sleep per frame lewat taskMgr) dan mencatat setiap
  portal yang terpicu. Jendela dt 0,10–0,13 s jadi bisa diulang di mesin cepat.

## Bukti

Semua lewat `main()` asli `regress.py` dan jalur `app.py`. Probe hanya
membungkus fungsi `cek_*`, `Player3D.tick`, dan `_check_portals`.

| larian | hasil |
|---|---|
| regress.py LAMA, farm, `--lambat=50` | GAGAL 116,9 ms/frame, **689** entity, "yaw270: W menyimpang 157 deg"; log PORTAL farm(25,5)→greenhouse pada tick 225 di dalam `cek_arah_maju` |
| regress.py BARU, farm, `--lambat=50` | LULUS 121,9 ms/frame, **1179** entity, "W 0:0d/3.0u 135:0d/3.0u 270:0d/3.0u", **0** PORTAL |
| regress.py BARU, 14 scene, dibungkus probe tanpa perlambatan | 14/14 LULUS, **0** PORTAL (versi lama: 2 PORTAL tersembunyi di naga_cave) |
| regress.py BARU, larian biasa 14 scene | 14/14 LULUS, 0 pemeriksaan gagal, lima menit 8/8; CI GitHub hijau pada 3cc9aba (2 larian) |
| BARU + mutasi basis arah (komponen .y untuk .z, di memori) | GAGAL "yaw135: W menyimpang 179 deg (jarak 3.01u); yaw270: W menyimpang 146 deg (jarak 3.06u)" |

### Uji mutasi

Batas 3 u tidak boleh menumpulkan cek arah. Bug basis sumbu lama dipasang di
memori lewat `--mutasi-basis` (bentuk [[Arah WASD basis sumbu salah]]).
Hasilnya tetap merah, 179° dan 146°, cocok dengan tabel di nota bug itu
(178,6° / 146,0°).

## Yang belum beres

- Risiko yang sudah ada dan tidak diperbaiki di sini: di mesin SANGAT cepat
  (~140 fps), 40 frame menurut model hanya memberi ~1,2 u, di bawah ambang
  "terhalang" 1,5 u. Cek bisa gagal "W tidak menggerakkan pemain". Belum
  terverifikasi.
- `time.sleep` adalah proksi mesin lambat: dt-nya sama, tapi sebaran beban
  CPU-nya tidak.
- Temuan sampingan, belum diprobe: kecepatan jalan stabil game ikut frame
  rate (model `player.py`: ~5,4 u/s pada 60 fps, ~2,4 u/s pada ~8,5 fps;
  `PLAYER_SPEED` 6 tak pernah tercapai). Ini bertentangan dengan komentar
  "60 FPS dan 8 FPS terasa sama", yang hanya benar untuk gesekannya. Jangan
  disentuh tanpa probe sendiri (aturan 5 CLAUDE.md).
