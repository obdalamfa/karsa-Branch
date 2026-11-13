---
judul: "Gauntlet: tiga assertion basi dibalikkan ke invarian aslinya"
tipe: sesi
tanggal: 2026-11-13
commit: 096bb31
skala: 7 file sumber, +104 / −29 baris
tags: [sesi]
---

# 2026-11-13 — Gauntlet: tiga assertion basi dibalikkan ke invarian aslinya

## Pesan commit

`gauntlet/check.py` gagal di titik-titik yang tidak ada hubungannya dengan
kode yang sedang dikerjakan. Ketiganya tipe yang sama: assertion memakukan
angka atau rumus lama, lalu kode aslinya berubah sah dan assertion-nya yang
jadi bohong.

Kristal gua. Sejak `pijar` dipakai, warna yang tampil adalah warna entity
DIKALI warna vertex yang dipanggang, bukan warna entity saja. Batas `peak`
dulu `max(ent.color)*1.5` -- angka 1.5 itu mengira-ngira puncak panggang.
Sekarang yang diukur hasil kalinya, jadi assertion bicara soal warna yang
benar-benar terlihat. Pengukuran menunjukkan sisa masalah nyata: palet lama
(70+18k, 196+14k, 206+10k) memuncak 1.0493 dan kanal terangnya terpotong di
1,0 sehingga gradasi faset hilang. Palet diturunkan ke (70+14k, 196+9k,
206+4k) -- puncak 0.9936, aman di bawah 1,0 -- di gua naga maupun dungeon.

Palet editor. `palet()` sudah lama memuat satu entri per jenis ubin (67),
sedangkan assertion masih memaku 51. Bukan cuma angkanya yang basi: 15 ubin
hasil `scenes/props.py` tidak punya tekstur DAN tidak punya warna cadangan,
jadi semuanya jatuh ke abu-abu anonim yang sama dan palet berhenti bisa
dibedakan. `WARNA_CADANGAN` sekarang menutup seluruh kelompok itu, dan
`karsa_panel` menghitung baris dari isi palet (`KOLOM_PALET`,
`baris_palet()`) alih-alih `51 // 4` -- literal itu bug tata letak sungguhan,
tombol palet menimpa panel objek karena 67 ubin tidak muat di 12 baris.

Daftar scene editor. `daftar()` mengambil dari `SCENE_BUILDERS`, assertion
memaku 15, dan `lawang` membuatnya 16. Yang diperiksa sekarang sumbernya
(daftar editor == kamus builder game) plus tiap scene yang ditawarkan harus
benar-benar bisa dimuat -- scene yang muncul di panel tapi gagal dibuka lebih
buruk daripada scene yang tidak muncul.

Hasil: `gauntlet/check.py` 20/20 lulus, `regress.py --offscreen` 15/15 scene
lulus tanpa pemeriksaan gagal.

## Berkas yang berubah

| Berkas | + | − |
|---|---:|---:|
| `_bench/progress.jsonl` | +2 | −0 |
| `game/scenes/rock_sanctuary.py` | +7 | −2 |
| `gauntlet/check.py` | +45 | −15 |
| `gauntlet/results.json` | +1 | −1 |
| `ursina_editor/README.md` | +5 | −3 |
| `ursina_editor/karsa_panel.py` | +4 | −4 |
| `ursina_editor/karsa_tiles.py` | +40 | −4 |

## Bukti

<!-- ISI MANUAL. Angka, larian regresi, atau probe — skrip sengaja tidak
     menebak bagian ini. Lihat [[Aturan Pencatatan]]. -->

- `python gauntlet/check.py` → **20/20 pemeriksaan lulus, exit 0**. Dua
  larian pertama berhenti di assertion berikutnya yang basi (palet 51,
  lalu daftar scene 15); sesudah ketiganya diperbaiki baru tuntas.
- `python tools/regress.py --offscreen` → **15/15 scene lulus, 0 pemeriksaan
  gagal, boot 5,4 detik, exit 0**; baris regresi panjang semua lulus
  (`tampilan` 74/74, `dua desa` 154/154, `sinema/judul` 36/36, `majelis
  batin` 26/26, `animasi gerak` 23/23, `lore gua` 19/19).
- Kristal: angka 1,5 pada assertion lama bukan ambang, melainkan tebakan
  puncak panggang. Diukur ulang pada normal 12 shard `naga_cave`: terang
  terpanggang memuncak **1,1878** (`terang = .62 + .48·max(0,n·arah) +
  .12·max(0,n.y)`), jadi yang relevan adalah hasil kali warna entity ×
  warna vertex. Palet lama memuncak **1,0493** → kanal terpotong di 1,0;
  palet baru memuncak **0,9936**. Assertion sekarang memeriksa hasil kali
  itu (`peak <= 0,999`), bukan warna entity sendirian.
- Palet: `palet()` = **67 entri** (satu per `TILE_IDS`), **47 bertekstur**,
  15 di antaranya dulu tanpa tekstur dan tanpa warna → semua abu-abu
  `(150,150,150)` yang sama. `WARNA_CADANGAN` kini 19 nama.
- Uji suntik membuktikan assertion baru memang menggigit: membuang `PPN`
  dari `WARNA_CADANGAN` menghasilkan `[(66, 'PPN')]`, membuang `KLK` dan
  `SWR` menghasilkan `[(63,'KLK'), (65,'SWR')]`. Tanpa suntikan itu,
  assertion yang selalu hijau tidak bisa dibedakan dari assertion yang mati.
- Tata letak: `baris_palet()` = **17** baris (67 ubin / 4 kolom, dibulatkan
  ke atas); literal lama `51 // 4` = 12 baris, jadi 5 baris tombol palet
  menimpa panel objek di bawahnya.
- Daftar scene: 16 nama = `SCENE_BUILDERS`; `lawang` yang baru. Loop baru
  memuat kesepuluh-enam scene lewat `ksc.muat` dan memeriksa `w`, `h`,
  `len(tiles) == h`, dan sumbernya `data`/`kode` — semua 16 punya berkas
  JSON, jadi loop ini membaca data, tidak menjalankan builder.

## Yang belum beres

<!-- ISI MANUAL. Ditulis apa adanya, termasuk yang alat ukurnya belum bisa
     dipercaya. -->

- Palet kristal di `build_dungeon` ikut diturunkan supaya sama dengan gua
  naga, tetapi **tidak diukur**: `GameState` bawaan menghasilkan 0 ubin CRYS
  di scene dungeon, jadi yang diperiksa hanya jalur `build_cavern`.
- Assertion palet memeriksa bahwa setiap ubin punya warna, bukan bahwa
  warnanya masuk akal. Dua ubin bisa saja diberi warna yang nyaris sama dan
  pemeriksaan tetap hijau; membedakannya perlu mata.
- Tiga warga belum punya model Blender: Kades Hardjo, Mbah Rukmi, Sekar.
  Cerita Dua Desa sudah bisa dimainkan, tetapi tiga tokoh utamanya masih
  siluet.
- Dua papan permintaan berdampingan dan belum diputuskan mana yang
  dipertahankan: Papan Permintaan Warga vs Papan Titipan.
- `regress.py` menjalankan probe Dua Desa hanya saat tidak memfilter scene
  (`if not minta:`), jadi `--scene` tertentu tidak ikut memeriksa Dua Desa.
- Empat larian regresi lebih awal mati mendadak tanpa traceback (Panda
  offscreen "window closed" → `userExit`); larian ulang yang identik lulus.
  Penyebabnya belum terbukti, jadi hasil regresi masih perlu dicurigai
  saat ia gagal sendiri tanpa jejak.

## Tautan

[[Status Sekarang]] · [[Peta Progres]]
