---
judul: Pemeriksaan HUD membandingkan tangkapan lama
tipe: bug
status: terbuka
berat: sedang
ditemukan: 2026-10-07
ditemukan_oleh: dua larian regresi di pohon hasil merge (14 scene lalu 4 scene)
dijaga_oleh:
tags: [bug, uji, status/terbuka]
---

# 🐞 Pemeriksaan HUD membandingkan tangkapan lama

`hud_terbaca` menuduh `house` dan `naga_cave` gagal di larian 14 scene, lalu
**meluluskan keduanya** di larian 4 scene — pohon yang sama, perintah yang sama.
Cacatnya ada di alat ukur, bukan di HUD.

Ini kali **ketiga** di repo ini alat ukurnya yang salah, dan kali **kedua**
penyebabnya satu pemeriksaan mengubah keadaan yang dibaca pemeriksaan lain.
Yang pertama [[Pemeriksaan motif mengotori keadaan]].

## Gejala

```
larian 14 scene   house      GAGAL  hud_terbaca  1 bar tertimbun
                  naga_cave  GAGAL  hud_terbaca  1 bar tertimbun
                             (bar layar(108,196,128) bukan (226,178,70))

larian 4 scene    house      LULUS
                  naga_cave  LULUS
```

Nota sesi base 2026-10-05 sudah menulis gejalanya — "gagal acak tergantung
urutan scene pada larian penuh; lulus kalau scene diuji sendiri" — tapi
sebabnya belum ditunjuk. Dua larian di atas memperlihatkan kedua sisinya di
mesin yang sama.

## Sebab

Potretnya dan warna yang dibandingkan diambil pada **waktu yang berbeda**:

1. `tools/regress.py:1308-1319` — PNG diambil **sekali**, sebelum pemeriksaan
   apa pun yang mengubah keadaan.
2. `tools/regress.py:1330` — `cek_motif_waras(g)` jalan, dan ia **men-tick
   state hidup** (begitu kata docstring-nya sendiri).
3. `tools/regress.py:1336` — `cek_hud_terbaca(g, png)` membandingkan PNG lama
   itu dengan `e.color` yang dibaca **saat itu**.

`game/panels.py:1298` menyetel warna bar dari nilai motif saat itu: hijau
normal, `_MOTIVE_WARN = (226,178,70)` (`panels.py:1176`) saat rendah, merah
saat ≤0,25. Angkanya cocok sempurna:

| | |
|---|---|
| di layar | `(108,196,128)` — fill hijau `rgb(120,200,130)` (`panels.py:841`) diredam kotak 93% opak |
| diminta `e.color` | `(226,178,70)` — `_MOTIVE_WARN` |

Jadi tick di langkah 2 mendorong bar melewati ambang peringatan; warna hidupnya
berubah **sesudah** potretnya diambil. Di larian 14 scene motif sudah meluruh
cukup jauh saat sampai `house` (scene ke-7) dan `naga_cave` (ke-13) untuk duduk
dekat ambang itu; di larian 4 scene belum. Dari situ "acak tergantung
urutan"-nya: yang berubah bukan HUD-nya, melainkan seberapa dekat motif ke
ambang saat scene itu tiba.

## Perbaikan

**Belum dipasang.** Diusulkan di
[komentar PR #13](https://github.com/obdalamfa/karsa-Branch/pull/13#issuecomment-6046083991),
tidak di-push: `tools/regress.py` bukan berkas yang diubah PR itu, dan
melebarkan PR vault jadi perbaikan harness adalah keputusan pemilik repo.

Dua bentuk yang diusulkan:

1. **Pindahkan urutannya** — pemeriksaan apa pun yang membaca PNG (`hud_kontras`,
   `hud_terbaca`) jalan **sebelum** `cek_motif_waras`. Dua baris pindah.
2. **Potret warnanya bersama PNG-nya** — simpan `[tuple(e.color) for e in fills]`
   di frame yang sama saat PNG ditulis, lalu bandingkan piksel dengan potret itu,
   bukan dengan `e.color` yang hidup. Lebih tahan banting kalau urutan tidak
   mau dikunci.

Bentuk 1 cukup untuk kegagalan ini. Bentuk 2 juga menutup kasus umumnya: HUD
apa pun yang warnanya bergantung keadaan akan kena masalah yang sama.

## Yang menjaganya sekarang

**Tidak ada**, dan itu bagian dari masalahnya. Penjaga yang menuduh palsu bukan
penjaga: ia melatih orang mengabaikan warna merah. Di larian yang sama,
`cahaya_global` gagal **nyata** di `beach` dan `swarga` — deterministik, lolos
urutan — dan kegagalan nyata itu duduk di daftar yang sama dengan dua tuduhan
palsu ini. Lihat [[Regresi]] dan [[Status Sekarang]].

## Tautan

[[Pemeriksaan motif mengotori keadaan]] · [[Regresi]] · [[Status Sekarang]] ·
[[Utang Teknis]]
