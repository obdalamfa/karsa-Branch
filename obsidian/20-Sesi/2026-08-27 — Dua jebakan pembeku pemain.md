---
judul: Perbaiki "jalan saja tidak bisa" — dua jebakan pembeku pemain
tipe: sesi
tanggal: 2026-08-27
commit: 7ed8d59
skala: app.py +35, regress.py +27
tags: [sesi, bug, kontrol]
---

# 2026-08-27 — Dua jebakan pembeku pemain

Commit `7ed8d59`, commit terakhir sejauh ini.

## Gejala dan sebabnya

`player.tick()` hanya dipanggil kalau `panels.mode == 'hud'` (`app.py`).
Artinya **mode panel apa pun yang macet membekukan pemain sepenuhnya**: tidak
jalan, waktu berhenti, motif berhenti meluruh. Diukur lewat jalur asli
`Game3D.update` di `_bench/probes/probe_beku.py`:

```
mode=hud     3,11 unit  bergerak
mode=dialog  0,00 unit  MEMBEKU
mode=panel   0,00 unit  MEMBEKU
mode=pie     0,00 unit  MEMBEKU
```

## Dua jebakan

1. **ESC tidak berfungsi di mode `dialog`** — pemain terkunci selamanya tanpa
   jalan keluar. Sekarang ESC ditangani di paling atas `input()`, sebelum
   percabangan mode, jadi tidak ada mode yang bisa menahannya. Chargen sengaja
   dikecualikan karena memang layar wajib.
2. **Pie menu objek hanya bisa ditutup dengan memilih atau ESC.** Pemain yang
   menekan WASD merasa game menggantung. Sekarang bergerak membatalkan menu —
   afordans yang sama dengan The Sims.

Sesudah perbaikan: **21,13 unit**, mode kembali ke `hud`.

## Ironi yang layak dicatat

Pie menu objek itu ditambahkan **sendiri** di commit sebelumnya untuk menutup
loop permainan — pintu masuk baru ke keadaan beku, tanpa memeriksa jalan
keluarnya.

## Kenapa lolos dari tiga probe sebelumnya

Ketiganya memanggil `player.tick()` **langsung**, melewati gerbang mode di
`app.py`. Alat ukur yang salah, bukan kode. Ini pelajaran yang sama dengan
[[Arah WASD belum terverifikasi]]: probe yang tidak menempuh jalur asli
mengukur dunia yang tidak ada.

Karena itu `tools/regress.py` sekarang punya pemeriksaan **`bisa_keluar`** yang
menguji ESC dari mode `dialog`/`panel`/`pie` di tiap scene → [[Regresi]].

## Bukti

Regresi **5/5 lulus**.

## Tautan

Bug: [[Pemain beku saat panel terbuka]] ·
Berikutnya: [[2026-09-22 — Vault Obsidian dibuat]]
