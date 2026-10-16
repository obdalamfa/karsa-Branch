---
judul: "Tutorial menyuruh R, cangkul pertama crash"
tipe: bug
status: selesai
ditemukan: "2026-10-16"
commit_perbaikan: (gauntlet M10, 2026-10-16)
dijaga_oleh: tools/probe_lima_menit.py
tags: [bug, status/selesai, lima-menit-pertama]
---

# 🐞 Tutorial menyuruh R, cangkul pertama crash

Tiga bug bertumpuk di lima menit pertama. Tidak satu pun tertangkap regresi,
karena tidak ada alat yang pernah memainkan tutorial dari awal.

## Gejala

Pemain baru tidak bisa melewati langkah 1 tutorial, dan kalaupun lewat, ayunan
cangkul pertama melempar exception.

## Sebab (diukur dengan probe_lima_menit.py)

1. **Petunjuk menyebut [R].** Tutorial dan 11 prompt kontekstual menulis "[R]"
   untuk interaksi, padahal `r` mengganti benih dan interaksi ada di `e`
   (petunjuk tombol HUD sendiri sudah benar: "E Aksi"). Dengan `r`:
   `mail_read=False`.
2. **[E] pun tidak membaca surat.** `open_object_menu()` (perabot radius 1)
   dicek sebelum ubin yang dihadap, dan peti di sebelah kotak pos membuka menu
   pie, walau prompt menjanjikan "[E] Baca surat".
3. **`say_batin_once` tidak ada.** Metode itu (beserta `say_batin`) hilang
   bersama merge yang menelan `_build_batin`, sementara enam pemanggilnya
   tetap ada. Cangkul pertama → `AttributeError`.

Ditambah: petunjuk tidur "berdiri di kasur, tekan [E]" membuka menu kasur,
bukan tidur.

## Perbaikan

`[R]` → `[E]` (15 tempat). Kotak pos yang dihadap menang atas menu perabot
(`_baca_surat`). `say_batin`/`say_batin_once` dipulihkan minimal (lewat
`flash_msg`). Petunjuk tidur → "[T]".

## Yang menjaganya sekarang

`tools/probe_lima_menit.py` 8/8. Probe ini belum masuk `regress.py`.

## Yang belum

Sisa Majelis Batin masih hilang: `Batin` tidak pernah dibuat, dan
`open_batin_check` tidak ada (pemanggilnya keluar lebih awal karena
`panels.batin` kosong).
