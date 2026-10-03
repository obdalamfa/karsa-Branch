---
judul: Tahap 1 — jaring pengaman regresi, plus bug pertama yang ditemukannya
tipe: sesi
tanggal: 2026-08-26
commit: 126cea8
skala: tools/regress.py 264 baris, app.py 712/703
tags: [sesi, regresi, bug]
---

# 2026-08-26 — Jaring pengaman lahir

Commit `126cea8`. Menutup [[Tahap 1 — Jaring pengaman]] dan sekaligus
membuktikan gunanya di larian pertama.

## Yang dibangun

`tools/regress.py` — boot tiap scene, buktikan ia dirender, periksa hal-hal
yang memang **pernah** rusak. Tiap pemeriksaan terikat kegagalan nyata:

| Cek | Kegagalan yang melatarinya |
|---|---|
| `geom_nol` | [[Mesh NodePath dipakai bersama]] — terjadi dua kali |
| `frame_kosong` | "rumah ga muncul" |
| `pemain_valid` | [[Terjepit permanen]] |
| `motif_waras` | mesin [[Motif]] baru |
| `save_bolak` | format save berubah, save lama tidak boleh rusak |
| `ms_frame` | 4–29 FPS, belum pernah diprofil |

Rinciannya di [[Regresi]].

## Alasannya bukan kerapian

Verifikasi manual gagal dua kali di sesi sebelumnya: WASD dinyatakan beres
padahal belum, dan dua kali sebuah metode disisipkan di tengah fungsi sehingga
fungsi induknya mati total. Keduanya ketahuan **cuma karena kebetulan** diuji
ulang.

## Bug pertama yang ditemukannya

Masuk `house`/`shop` mendaratkan pemain di (19,5) padahal `house` cuma 15 kolom
→ [[Pendaratan scene di luar peta]]. Ini akar dari gejala yang sebelumnya cuma
ditambal di sisi pemain.

## Bukti

**5/5 scene lulus.** Pendaratan sesudah perbaikan: `house` (13,4),
`shop` (12,3), `lake` (13,3).

`docs/TAHAPAN.md` (124 baris) lahir di commit ini — urutan kerja dari sini
sampai selesai, yang sekarang dicerminkan di `10-Tahapan/`.

## Tautan

Berikutnya: [[2026-08-26 — Tahap 2 sambungkan modul yatim]]
