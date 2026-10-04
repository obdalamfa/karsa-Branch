---
judul: Regresi
tipe: sistem
modul: tools/regress.py
baris: 291
status: jalan
hasil_terakhir: 14/14 scene lulus — lokal dan di CI GitHub (2026-09-22)
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
| `arah_maju` ⚠️ | [[Arah WASD basis sumbu salah]] — basis membaca komponen sumbu yang salah. **Lapor-saja**, belum memvonis: instrumennya masih terkontaminasi antar-scene |
| `ms_frame` | 4–29 FPS, belum pernah diprofil → [[Tahap 3 — Performa]] |

`ms_frame` dan jumlah entity dicatat sebagai **angka**, bukan lulus/gagal —
supaya regresi performa **terlihat**, bukan cuma terasa.

## Larian terakhir — 2026-09-22, sungguhan

```
scene            hasil  ms/frame  entity
------------------------------------------------------------------------------
mountain         LULUS     119.6    2177
town             LULUS     102.6    1884
farm             LULUS      96.8    1257
beach            LULUS      84.2    1728
naga_cave        LULUS      82.2     530
lake             LULUS      72.3     686
swarga           LULUS      71.9    1379
cemetery         LULUS      70.5     983
greenhouse       LULUS      53.9     488
shop             LULUS      49.5     405
studio           LULUS      47.3     384
smith            LULUS      47.2     385
clinic           LULUS      46.6     385
house            LULUS      46.4     418
------------------------------------------------------------------------------
14/14 scene lulus, 0 pemeriksaan gagal, boot 3.6s
```

**14 scene, bukan 5.** Angka "5/5" yang beredar di dokumen lama hanya
mencakup sebagian; sepuluh scene lain tidak pernah ikut terhitung.

Angka ms/frame di atas dirender **CPU** (Mesa software di Xvfb), jadi bukan
FPS sebenarnya — pakai untuk tren, bukan untuk klaim performa.

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

## Sekarang jalan otomatis

`.github/workflows/regresi.yml` menjalankan seluruh 14 scene di tiap push dan
PR — Xvfb + Mesa software, lalu tangkapan layar dan laporan diunggah sebagai
artifact. Sebelum itu jaring ini cuma bekerja kalau ada yang **ingat**
mengetiknya.

**Terbukti jalan:** 4 larian di GitHub Actions, semuanya `success`, artifact
bukti 3,28 MB. Karena `regress.py` keluar dengan kode 1 begitu satu pemeriksaan
gagal, langkah CI yang hijau itu sendiri adalah bukti 14/14.

Dua hal harus beres lebih dulu sebelum CI mungkin sama sekali:
[[Font HUD tidak ketemu di mesin bersih]] dan `requirements.txt` yang tidak
menyebut `pygame`/`pillow`.

## `arah_maju`: penjaga yang harus diperbaiki tiga kali

Pemeriksaan termuda di sini, dan tiga kali gagal sebagai penjaga sebelum
berguna. Tiap kegagalan terukur, bukan dinalar:

| Versi | Cacat | Buktinya |
|---|---|---|
| 1 | hanya menguji yaw yang sedang aktif | bug lama dipasang kembali → `farm` dan `town` **LULUS** |
| 2 | meninggalkan bekas (pemain tergeser, kamera masih bergerak) | `beach` **LULUS** kalau pertama, **GAGAL** kalau keenam |
| 3 | menghukum pemain yang **terhalang dinding** | `house` (ruang kecil) dilaporkan menyimpang 102° padahal cuma menabrak |

| 4 | **masih terkontaminasi di larian panjang** | 14 scene → 6 GAGAL (dua "180°"); `town` sendirian **LULUS**, sesudah `farm` **LULUS** |

Versi 4 menyapu tiga yaw, menyalin-dan-memulihkan posisi + kecepatan pemain,
menyentak kamera alih-alih menunggu lerp, dan melaporkan `terhalang` alih-alih
GAGAL kalau jarak jalan di bawah 1,5 satuan. Ia **menangkap bug sungguhan**:

```
dengan bug lama dipasang   farm GAGAL yaw135: W menyimpang 179 deg   exit 1
dengan perbaikan, 3 scene  farm house beach LULUS                     exit 0
```

…tapi di larian 14 scene ia menuduh enam scene yang sehat. Karena kegagalannya
bergantung panjang larian, bukan pada kode yang diperiksa, ia **diturunkan jadi
lapor-saja**: angka penyimpangan tetap tercetak di kolom catatan, tapi tidak
memvonis.

**Penjaga yang belum pernah dilihat gagal bukan penjaga** — dan penjaga yang
salah menuduh juga bukan penjaga: yang berikutnya akan mematikannya, lalu bug
sungguhan lewat tanpa suara. Status terbukanya ada di [[Utang Teknis]].

Yang membuktikan arah sekarang: `_bench/probes/probe_arah_wasd.py` dan
`probe_basis_kamera.py`, keduanya ter-commit.

## Cacat alat ukur yang ditemukan pada dirinya sendiri

`motif_waras` dulu memajukan keadaan motif nyata di setiap scene tanpa
memulihkannya, sehingga scene ke-14 apa pun akan gagal palsu →
[[Pemeriksaan motif mengotori keadaan]]. Sekarang bebas urutan.

## Tautan

[[Tahap 1 — Jaring pengaman]] · [[Utang Teknis]]
