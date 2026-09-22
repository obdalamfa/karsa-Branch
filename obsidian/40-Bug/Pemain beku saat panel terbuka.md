---
judul: Pemain beku saat panel terbuka
tipe: bug
status: selesai
ditemukan: 2026-08-27
commit_perbaikan: 7ed8d59
dijaga_oleh: bisa_keluar
tags: [bug, kontrol, ui, status/selesai]
---

# 🐞 Pemain beku saat panel terbuka

Laporan pemilik: *"jalan saja tidak bisa"*.

## Sebab

`player.tick()` hanya dipanggil kalau `panels.mode == 'hud'` (`app.py`).
Mode panel apa pun yang macet **membekukan pemain sepenuhnya**: tidak jalan,
waktu berhenti, motif berhenti meluruh.

Diukur lewat jalur asli `Game3D.update` di `_bench/probes/probe_beku.py`:

```
mode=hud     3,11 unit  bergerak
mode=dialog  0,00 unit  MEMBEKU
mode=panel   0,00 unit  MEMBEKU
mode=pie     0,00 unit  MEMBEKU
```

## Dua jebakan yang membuat mode itu macet

1. **ESC tidak berfungsi di mode `dialog`** — pemain terkunci selamanya.
   Sekarang ESC ditangani di **paling atas** `input()`, sebelum percabangan
   mode, jadi tidak ada mode yang bisa menahannya. Chargen dikecualikan karena
   memang layar wajib.
2. **Pie menu objek** hanya bisa ditutup dengan memilih atau ESC; pemain yang
   menekan WASD merasa game menggantung. Sekarang **bergerak membatalkan
   menu**, afordans yang sama dengan The Sims.

Sesudah perbaikan: **21,13 unit**, mode kembali ke `hud`.

## Ironinya

Pie menu objek ditambahkan sendiri di commit sebelumnya untuk menutup loop
permainan — pintu masuk baru ke keadaan beku, **tanpa memeriksa jalan
keluarnya**. Tiap pintu masuk ke mode wajib punya pemeriksaan jalan keluar.

## Kenapa tiga probe sebelumnya gagal menangkapnya

Ketiganya memanggil `player.tick()` **langsung**, melewati gerbang mode di
`app.py`. **Alat ukur yang salah, bukan kode** — pelajaran yang sama dengan
[[Arah WASD belum terverifikasi]].

## Yang menjaganya sekarang

Pemeriksaan **`bisa_keluar`** di [[Regresi]]: menguji ESC dari mode
`dialog`/`panel`/`pie` di tiap scene.

## Tautan

[[2026-08-27 — Dua jebakan pembeku pemain]]
