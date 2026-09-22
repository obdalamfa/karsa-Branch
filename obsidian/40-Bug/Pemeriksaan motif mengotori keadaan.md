---
judul: Pemeriksaan motif mengotori keadaan
tipe: bug
status: selesai
berat: sedang
ditemukan: 2026-09-22
ditemukan_oleh: larian regresi 14 scene pertama
dijaga_oleh: motif_waras (sekarang bebas urutan)
tags: [bug, uji, status/selesai]
---

# 🐞 Pemeriksaan motif mengotori keadaan yang diperiksanya

Bug di **alat ukur**, bukan di game — jenis yang paling mahal, karena ia
menuduh kode yang sehat.

## Gejala

Larian 14 scene pertama:

```
swarga    GAGAL   motif_waras: lapar tidak turun setelah 4 jam
```

Tapi `swarga` yang dijalankan **sendirian** → LULUS. Dijalankan berdua dengan
`farm` → LULUS. Kegagalan hanya muncul kalau ia scene **terakhir dari banyak**.

## Sebab, diukur

`cek_motif_waras` memajukan keadaan motif **yang sebenarnya** empat jam-sim,
di **setiap** scene, dan tidak pernah memulihkannya. Bekasnya menumpuk.

Laju peluruhan Lapar non-linear — melambat justru saat sim sudah lapar (sifat
asli TS1, lihat [[Motif]]). Setelah belasan kali maju empat jam, penurunannya
lebih kecil daripada satu poin utuh yang bisa dibukukan `tick()`, jadi nilainya
**mendatar**:

```
tick 14  lapar -98,0000
tick 15  lapar -98,0000   <- berhenti turun; pemeriksaan menyatakan GAGAL
```

Jadi yang gagal bukan `swarga`, melainkan **scene ke-14 apa pun**. Kegagalannya
berpindah-pindah mengikuti urutan argumen — tanda khas cacat alat ukur.

## Perbaikan

Pemeriksaan tetap menguji **mesin yang nyata** (bukan instance tiruan, supaya
mesin motif yang membeku tetap ketahuan), tapi sekarang:

1. menyalin kedelapan nilai motif **dan** akumulator pecahannya,
2. mengangkat Lapar menjauh dari dasar supaya peluruhan bisa terukur,
3. memulihkan semuanya di blok `finally`.

Hasilnya bebas urutan: 14/14 lulus, dan tiap scene diuji dengan keadaan yang
sama.

## Pelajaran yang berulang

Ini kali **ketiga** proyek ini tertipu alat ukurnya sendiri:

| Kali | Kejadian |
|---|---|
| 1 | tiga probe memanggil `player.tick()` langsung → [[Pemain beku saat panel terbuka]] lolos |
| 2 | probe proyeksi layar saling bertentangan → [[Arah WASD belum terverifikasi]] |
| 3 | pemeriksaan motif mengotori keadaannya sendiri (nota ini) |

Aturan yang pantas ditarik: **pemeriksaan tidak boleh meninggalkan bekas pada
apa yang diperiksanya.**

## Tautan

[[Regresi]] · [[Motif]] · [[2026-09-22 — Regresi jalan sungguhan, CI dipasang]]
