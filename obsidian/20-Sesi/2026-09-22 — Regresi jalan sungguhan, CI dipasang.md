---
judul: Regresi jalan sungguhan, CI dipasang
tipe: sesi
tanggal: 2026-09-22
commit:
tags: [sesi, regresi, ci, bug, boot]
---

# 2026-09-22 — Regresi jalan sungguhan, CI dipasang

Sesi sebelumnya menutup catatan dengan kalimat jujur: *"mesin ini tidak punya
`ursina`/`panda3d`, jadi regresi tidak dijalankan ulang."* Sesi ini mencabut
kalimat itu — pustakanya dipasang, dan larian pertamanya langsung menemukan
bug yang membunuh game di mesin bersih.

## 1. Regresi ternyata tidak bisa jalan sama sekali

Tiga penghalang, ditemukan berurutan:

| Penghalang | Apa yang terjadi |
|---|---|
| `requirements.txt` cuma berisi `ursina` | `import pygame` gagal → game tidak bisa di-*import*, apalagi boot |
| tidak ada display | `Could not open window` → dipecahkan dengan Xvfb |
| font HUD tidak ketemu | `OSError: Could not load font file: Montserrat-Bold.ttf` |

Yang ketiga bukan masalah lingkungan — itu **bug nyata** →
[[Font HUD tidak ketemu di mesin bersih]]. Panda3D mencari font di model-path
tanpa menelusuri subfolder; Ursina cuma memasukkan akar repo; fontnya ada di
`assets/fonts/`. Di Windows ia lolos karena `C:/Windows/Fonts` ikut dicari dan
pemilik memang punya Montserrat terpasang.

Diperbaiki di `game/app.py` — satu tempat, dipakai `main.py`, `regress.py`, dan
`capture.py` sekaligus.

## 2. Larian penuh pertama dalam sejarah proyek ini

```
14/14 scene lulus, 0 pemeriksaan gagal, boot 3,6 detik
```

Angka sebenarnya, bukan warisan:

| scene | ms/frame | entity |  | scene | ms/frame | entity |
|---|---:|---:|---|---|---:|---:|
| mountain | 119,6 | 2177 |  | greenhouse | 53,9 | 488 |
| town | 102,6 | 1884 |  | shop | 49,5 | 405 |
| farm | 96,8 | 1257 |  | studio | 47,3 | 384 |
| beach | 84,2 | 1728 |  | smith | 47,2 | 385 |
| naga_cave | 82,2 | 530 |  | clinic | 46,6 | 385 |
| lake | 72,3 | 686 |  | house | 46,4 | 418 |
| swarga | 71,9 | 1379 |  | | | |
| cemetery | 70,5 | 983 |  | | | |

> [!warning] Angka ini dirender CPU
> Runner tidak punya GPU; Mesa merender lewat perangkat lunak. Jadi ms/frame di
> sini **bukan** FPS sebenarnya dan tidak sebanding dengan 4–29 FPS yang
> dilaporkan pemilik. Gunanya satu: melihat **tren** antar-commit dan urutan
> relatif antar-scene. Lihat [[Tahap 3 — Performa]].

Catatan penting: dokumen lama menyebut **"5/5 scene lulus"**. Sekarang ada
**14 scene** — `beach`, `swarga`, `mountain`, `cemetery`, `clinic`, `studio`,
`smith`, `greenhouse`, `naga_cave`, `town` tidak pernah ikut terhitung di angka
itu. Klaim lama bukan bohong, cuma sudah jauh tertinggal.

## 3. Satu kegagalan, dan ia ada di alat ukurnya

Larian 14 scene pertama: `swarga` GAGAL, `motif_waras`. Tapi `swarga`
sendirian LULUS, dan berdua dengan `farm` juga LULUS.

Sebabnya pemeriksaan itu memajukan keadaan motif **yang nyata** empat jam-sim
di setiap scene tanpa memulihkannya; setelah belasan kali, Lapar mendatar di
−98,0000 dan berhenti turun. Yang gagal bukan `swarga`, melainkan **scene
ke-14 apa pun** → [[Pemeriksaan motif mengotori keadaan]].

Diperbaiki tanpa melemahkan uji: keadaan disalin, Lapar diangkat dari dasar,
lalu semuanya dipulihkan di `finally`.

## 4. CI, supaya jaringnya benar-benar terpasang

`.github/workflows/regresi.yml` menjalankan 14 scene di tiap push dan PR, di
atas Xvfb + Mesa, lalu mengunggah tangkapan layar dan laporan sebagai artifact.

Sebelum ini `tools/regress.py` cuma bekerja kalau ada yang **ingat**
mengetiknya. Jaring yang digantung tapi tidak pernah dipasang.

## Bukti

- `python tools/regress.py` → **14/14 lulus, 0 pemeriksaan gagal** (dijalankan di sesi ini, bukan dikutip).
- `_bench/probes/probe_font.py` → GAGAL sebelum perbaikan, KETEMU sesudah.
- Peluruhan Lapar diukur sampai mendatar: tick 15 → −98,0000 → −98,0000.
- `swarga` sendirian LULUS; `farm swarga` LULUS — membuktikan kegagalan tadi bergantung urutan.
- YAML workflow divalidasi parser; `tools/catat_obsidian.py --status` bersih.

## Yang belum beres

- **Workflow-nya sendiri belum pernah jalan di GitHub.** Ia baru terbukti lewat perintah yang identik di mesin ini. Larian pertamanya di PR inilah buktinya — kalau merah, itu urusan sesi ini juga.
- Nama paket apt (`libgl1`, `libglu1-mesa`, `libgl1-mesa-dri`) diambil untuk `ubuntu-latest`; belum diuji di runner sungguhan.
- [[Arah WASD belum terverifikasi]] masih terbuka — regresi tidak menguji arah.
- `entity_mesh.py` masih yatim → [[Utang Teknis]].

## Tautan

Sebelumnya: [[2026-09-22 — Vault Obsidian dibuat]] ·
[[Regresi]] · [[Status Sekarang]] · [[Tahap 1 — Jaring pengaman]]
