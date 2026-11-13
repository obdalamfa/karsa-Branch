---
judul: "Mob penyerang: papan nama + HP, aura, cincin ancaman, angka, gaya serang"
tipe: sesi
tanggal: 2026-11-03
commit: f004c34
skala: 6 file sumber, +369 / −9 baris
tags: [sesi]
---

# 2026-11-03 — Mob penyerang: papan nama + HP, aura, cincin ancaman, angka, gaya serang

## Pesan commit

Permintaan pemilik: "mobs yang sifatnya menyerang diperbagus". Tangkapan
deretan tujuh mob + bos di gua:

- bilah HP dua kubus tipis yang ikut diputar mob_gerak -> garis miring;
  kini papan billboard: nama jenis + bilah bersudut bulat (oranye saat
  HP < 35%)
- mob tenggelam di lantai gelap -> aura lembut berwarna watak (merah,
  api oranye banaspati, ungu kuntilanak, hijau leak) di kaki
- ancang-ancang tak menunjukkan jangkauan -> cincin merah mengisi selama
  windup, jari-jarinya = radius kena sungguhan (atk_r x 1,35)
- angka kerusakan melayang: putih ke mob, merah ke pemain
- gaya serang per jenis (mob.GAYA_SERANG): windup, jangkauan, jeda, dan
  TERJANG (kelelawar, tikus, leak, kuntilanak, pocong melompat maju di
  ujung ancang-ancang). Dulu semua 380 ms / 1 petak / 1000 ms.

Jebakan tertangkap tangkapan: aura di bawah lantai (GROUND_H), Text
bawaan menempel ke camera.ui, setter alpha Ursina pada Vec4.

probe_gerak 23/23: papan + aura, bilah menyusut, angka muncul, cincin =
jangkauan (8,10 vs 8,10), padam saat mati, terjang lewat AI sungguhan
(pemain mundur 1,6 petak tetap kena). Mutasi tanpa-terjang, rupa tak
dipasang, papan bukan billboard tertangkap; satu cek orientasi palsu
(lulus juga pada mutasi) dibuang.

## Berkas yang berubah

| Berkas | + | − |
|---|---:|---:|
| `_bench/progress.jsonl` | +1 | −0 |
| `game/entities.py` | +29 | −3 |
| `game/mob.py` | +35 | −4 |
| `game/mob_gerak.py` | +10 | −2 |
| `game/mob_rupa.py` | +197 | −0 |
| `tools/probe_gerak.py` | +97 | −0 |

## Bukti

<!-- ISI MANUAL. Angka, larian regresi, atau probe — skrip sengaja tidak
     menebak bagian ini. Lihat [[Aturan Pencatatan]]. -->

- Permintaan pemilik: "mobs yang sifatnya menyerang diperbagus".
- Garis dasar: tangkapan deretan tujuh mob dan bos di dungeon lv5 yang
  diratakan. Hasilnya:
  - bilah HP miring
  - mob gelap di lantai gelap
  - ancang-ancang tanpa jangkauan
  - tanpa angka kerusakan
  - semua mob memakai gaya serang yang sama
- Tiga jebakan tertangkap lewat tangkapan:
  - aura di y = 0,04, di bawah lantai GROUND_H 0,2
  - Text bawaan menempel ke camera.ui
  - setter `alpha` pada Vec4 (sama dengan tebing)
- `probe_gerak` lulus 23/23. Cincin 8,10 = 2 × 1,5 × 1,35 × 2. Kelelawar
  menerjang pemain yang mundur 1,6 petak, HP 100 → 95.
- Mutasi yang tertangkap: tanpa terjang, rupa tidak dipasang, papan bukan
  billboard.
- Pelajaran alat ukur: cek "orientasi papan tetap" lulus juga pada mutasi
  papan non-billboard. `mob_gerak` menimpa `rotation_y` tiap frame, dan
  efek billboard diterapkan saat cull, sehingga tidak terbaca `getQuat`.
  Cek itu dibuang dan diganti cek struktur.
- Regresi penuh lokal: 15/15 scene, 0 pemeriksaan gagal. CI hijau di
  f004c34.

## Yang belum beres

<!-- ISI MANUAL. Ditulis apa adanya, termasuk yang alat ukurnya belum bisa
     dipercaya. -->

- Keseimbangan berubah: jangkauan genderuwo 1,5, banaspati 1,6, bos 1,9
  (dulu 1,0/1,5), plus terjangan. Belum dimainkan sampai lantai 10.
- Belum ada serangan jarak jauh (misalnya bola api banaspati). Semua mob
  masih menyerang jarak dekat.
- HP pemain turun pelan di tangkapan dungeon walau `damage=0`. Sudah begitu
  sebelum perubahan ini dan belum diselidiki.

## Tautan

[[Status Sekarang]] · [[Peta Progres]]
