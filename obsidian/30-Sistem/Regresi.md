---
judul: Regresi
tipe: sistem
modul: tools/regress.py
baris: 291
status: jalan
hasil_terakhir: 5/5 scene lulus (commit 7ed8d59)
tags: [sistem, uji, status/jalan]
---

# Regresi — jaring pengaman proyek

`tools/regress.py`. Boot tiap scene, buktikan ia **benar dirender**, lalu
periksa hal-hal yang memang **pernah** rusak di sini.

```bash
python tools/regress.py                 # semua scene (dungeon dikecualikan)
python tools/regress.py farm house      # scene tertentu
```

Keluar dengan kode `1` kalau ada yang gagal, supaya bisa dipakai di skrip.

## Tujuh pemeriksaan, tiap satu terikat kegagalan nyata

| Cek | Kegagalan yang melatarinya |
|---|---|
| `geom_nol` | [[Mesh NodePath dipakai bersama]] — terjadi **dua kali** (`meshes.py`, `entities.py`) |
| `frame_kosong` | "rumah ga muncul" — scene jadi langit polos |
| `pemain_valid` | [[Terjepit permanen]] |
| `bisa_keluar` | [[Pemain beku saat panel terbuka]] — ESC dari mode dialog/panel/pie |
| `motif_waras` | mesin [[Motif]] baru; nilai harus tetap di −100..+100 |
| `save_bolak` | format save berubah; save lama tidak boleh merusak loader |
| `ms_frame` | 4–29 FPS, belum pernah diprofil → [[Tahap 3 — Performa]] |

`ms_frame` dan jumlah entity dicatat sebagai **angka**, bukan lulus/gagal —
supaya regresi performa **terlihat**, bukan cuma terasa.

## Bentuk laporannya

```
scene            hasil  ms/frame  entity  catatan
------------------------------------------------------------------------------
farm             LULUS      33.4     412  (13,4)
...
------------------------------------------------------------------------------
5/5 scene lulus, 0 pemeriksaan gagal, boot 4.2s
```

Tiap scene: 30 frame pemanasan, 12 frame diukur, tangkapan layar ke
`_bench/regress/<scene>.png`.

## Kenapa ini ada sebelum fitur apa pun

Verifikasi manual sudah gagal **dua kali**: WASD dinyatakan beres padahal
belum, dan dua kali sebuah metode disisipkan di tengah fungsi sehingga fungsi
induknya mati total. Keduanya ketahuan cuma karena **kebetulan** diuji ulang.
Yang ketiga tidak akan ketahuan.

## Pelajaran yang mahal: probe harus menempuh jalur asli

Tiga probe gagal menemukan [[Pemain beku saat panel terbuka]] karena ketiganya
memanggil `player.tick()` **langsung**, melewati gerbang mode di `app.py`.
Alat ukur yang salah, bukan kode. Aturan yang lahir dari situ ada di
[[Aturan Pencatatan]].

> [!caution] Belum dijalankan ulang sejak 2026-08-27
> Lihat [[Status Sekarang]] — mesin sesi 2026-09-22 tidak punya
> `ursina`/`panda3d`.

## Tautan

[[Tahap 1 — Jaring pengaman]] · [[Utang Teknis]]
