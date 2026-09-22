---
judul: Ternak
tipe: sistem
modul: game/husbandry.py
baris: 434
status: jalan
tags: [sistem, tani, status/jalan]
---

# Ternak — cara mengurus hewan, dan cara pemain **melihat** aturannya

`game/husbandry.py`. Permintaan pemilik: *"cara ngurus hewan juga dijelasin."*

Sebelum modul ini, mengurus hewan berarti tiga tombol tanpa akibat: Belai
(+8 senang), Beri Makan (+1 hati), Ambil Hasil (hasil muncul dari udara kalau
hati ≥ 2). Tidak ada yang bisa salah, jadi tidak ada yang perlu dipelajari —
dan karena tidak ada yang perlu dipelajari, tidak ada yang bisa dijelaskan.

## Loop harian

```
pagi   : kenyang −45, air −55, bersih −30
siang  : pemain beri makan (+60), beri minum (penuh), bersihkan (penuh)
malam  : kalau kenyang ≥ 40, air ≥ 30, bersih ≥ 25 dan tidak sakit,
         hitungan produksi maju satu hari
lalai  : kenyang atau air menyentuh 0 → +1 hari lalai; 3 hari lalai → SAKIT
sakit  : tidak menghasilkan apa pun, hati turun tiap hari
```

## Aturan yang tidak bisa dilihat pemain bukan aturan

Bagian yang sama pentingnya dengan simulasinya: `status_lines()` dan
`short_status()` menyediakan teks keadaan siap pakai supaya semua aturan di
atas muncul di pie menu dan di panel Tani & Ternak.

## Status sambungan

`TimeController.advance_day()` → `husbandry.daily_tick()`, disambungkan di
[[2026-08-26 — Tahap 2 sambungkan modul yatim]]. Sebelum itu modul ini **yatim**
— 434 baris tanpa satu pun pemanggil.

Diuji lima hari: hari 1 dua ternak siap dipanen, lalu lapar, hari 4 semua jatuh
sakit karena dilalaikan.

## Tautan

[[Ekonomi]] · [[Palawija]] · [[Tahap 2 — Verifikasi modul yatim]]
