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
| `arah_maju` | [[Arah WASD basis sumbu salah]] — basis membaca komponen sumbu yang salah; diukur di jendela 10 frame, tiga yaw |
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

| 4 | **menuduh enam scene sehat** | 14 scene → 6 GAGAL (dua "180°"); `town` sendirian **LULUS** |
| 5 | **ditolak CI** | hijau di mesin lokal, exit 1 di runner GitHub — jendela berpatok frame padahal gerak berpatok jam dinding |
| 6 | **lolos** | dua larian bersih berturut-turut 14/14; 7/7 GAGAL (179°) dengan bug dipasang; jendela ditutup oleh jarak, dan hanya jendela penuh yang memvonis |

Versi 4 sudah menyapu tiga yaw dan memulihkan keadaan pemain, tapi menuduh
enam scene sehat. Dugaan waktu itu — kontaminasi antar-scene — **ternyata
salah**: `probe_kontaminasi.py` mengukur selisih posisi lokal lawan dunia
**0,000 di keempat belas scene**, dan instrumentasi di dalam pemeriksaannya
menunjukkan posisi masuk = posisi keluar.

Sebab sebenarnya dua lapis, keduanya di alat ukur:

1. **Acuan diambil sesudah berjalan.** Vektor "atas layar" dihitung dari
   kamera→fokus setelah 40 frame, saat kamera sudah ikut bergeser dan
   disesuaikan pemotong dinding. Itu sumber tuduhan **180°** yang hanya muncul
   di scene berbangunan. Sekarang acuan diambil **sebelum** tombol ditekan.
2. **Jendela terlalu panjang.** Penyimpangan karena menggeser rintangan
   menumpuk bersama jarak — diukur berdampingan di scene yang sama:

   | scene | 10 frame | 40 frame |
   |---|---:|---:|
   | lake | 11,0° | 36,0° |
   | cemetery | 10,8° | 36,1° |
   | mountain | 11,4° | 34,4° |
   | town | 2,8° | 30,3° |

Vonis sekarang memakai jendela **10 frame** dengan ambang **45°** — empat kali
lipat ruang di atas sisa 11° (tikungan saat berakselerasi dari diam), sementara
bug sungguhan mengukur 179°.

Diuji dua arah, dan itu syarat kelayakannya:

```
dengan perbaikan      14/14 lulus, 0 gagal                       exit 0
dengan bug dipasang    0/6  lulus, 6 gagal (177-179 deg)         exit 1
```

Versi 5 masih jatuh dua kali lagi, dan CI yang menemukannya:

- **Jendela berpatok frame.** `player.tick(dt)` memakai jam dinding, jadi 10 frame di mesin lambat ≠ 10 frame di mesin cepat. Sekarang jendela ditutup oleh **jarak 0,40 satuan**, batas aman 60 frame.
- **Jendela setengah jalan tetap memvonis.** Pemain yang tertahan lalu terdorong mundur 0,2–0,4 satuan lolos gerbang lama dan divonis 180°. `probe_acuan.py` membuktikan game dan acuannya benar di kasus itu — ketiga acuan sepakat 0,0°. Sekarang hanya jendela yang **mencapai** 0,40 satuan yang boleh memvonis.

**Penjaga yang belum pernah dilihat gagal bukan penjaga** — penjaga yang salah
menuduh juga bukan penjaga — dan penjaga yang hanya terbukti di satu mesin
belum terbukti. Rinciannya di
[[2026-10-06 — CI menolak penjaga yang saya nyatakan lolos]].

## Laporan CI sekarang bisa dibaca

Log dan artifact GitHub disajikan dari host penyimpanan yang tidak bisa
dihubungi klien API sesi ini, jadi larian merah dulu hanya terlihat sebagai
"exit code 1". Workflow sekarang menempelkan `_bench/regress/report.md` ke
ringkasan job (`if: always()`), jadi tabel LULUS/GAGAL terbaca langsung.

## Cacat alat ukur yang ditemukan pada dirinya sendiri

`motif_waras` dulu memajukan keadaan motif nyata di setiap scene tanpa
memulihkannya, sehingga scene ke-14 apa pun akan gagal palsu →
[[Pemeriksaan motif mengotori keadaan]]. Sekarang bebas urutan.

## Tautan

[[Tahap 1 — Jaring pengaman]] · [[Utang Teknis]]
