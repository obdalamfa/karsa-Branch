---
judul: "Cek bayangan matahari membaca daun dan bayangan pohon"
tipe: bug
status: selesai
ditemukan: "2026-10-19"
commit_perbaikan: (workstream D, sesudah ca0f4df)
dijaga_oleh: tools/regress.py (cek_bayangan_matahari)
tags: [bug, status/selesai, cahaya, bayangan, regresi]
---

# 🐞 Cek bayangan matahari membaca daun dan bayangan pohon

## Gejala

Regresi penuh dengan `KARSA_SHADOW=1` merah di **lake** saja:
`bayangan kubus tidak sampai ke tanah: luminans 59.0 -> 59.0`. Shadow map
sendiri bekerja (bayangan pohon jelas di air pada tangkapan yang sama).
Regresi bawaan (shadow map mati) tidak menyentuhnya, jadi CI tetap hijau.

## Sebab

Dua salah ukur di `cek_bayangan_matahari` (ca0f4df), keduanya alat ukur
yang mengukur dunia yang tidak ada (aturan #2):

1. Titik uji di +2,4 m samping pemain jatuh di dalam tajuk pohon. Piksel
   yang dibaca sebagai "tanah dalam bayangan kubus" ternyata daun, yang
   tidak berubah saat caster dimatikan.
2. Perbandingan caster hidup lawan mati mencampur bayangan kubus dengan
   bayangan benda lain. Begitu titiknya dipindah ke sisi yang tampak, muka
   atas kubus jatuh ke bayangan pohon dan terbaca sebagai jerawat
   (115,3 -> 93,8). Kebalikannya juga mungkin: tanah yang sudah teduh
   pohon lulus tanpa bayangan kubus sama sekali.

## Perbaikan

- Calon titik (4 di samping, 2 searah sinar) diuji keterlihatannya dengan
  penanda magenta unlit yang digeser 0,35 m ke arah kamera di sepanjang
  sinar pandang (jatuh di piksel yang sama, tidak terkubur ubin).
- Sumbangan kubus diukur A (kubus ikut membayangi) lawan C (kubus
  disembunyikan dari bit kamera bayangan), keduanya caster hidup.
- Frame B (caster mati) menyaring titik yang teduh benda lain (C/B < 0,93).
  Kalau SEMUA titik yang tampak teduh, cek MERAH: itu jerawat yang
  menyebar ke tanah terbuka, bukan alasan untuk melewati.

## Angka (KARSA_SHADOW=1, regress farm town lake)

| mutasi | farm | town | lake |
|---|---|---|---|
| tanpa mutasi, sebelum | lulus | lulus | GAGAL (59,0 -> 59,0) |
| tanpa mutasi, sesudah | lulus -39% | lulus -38% | lulus -38% |
| `s_mat = 1.0` | GAGAL | GAGAL | GAGAL |
| caster dimatikan | GAGAL | GAGAL | GAGAL |
| tanpa normal offset & bias | GAGAL | GAGAL | lulus |

Versi antara (penyaring "teduh" yang melewati, bukan merah) membuat mutasi
jerawat LULUS di ketiga scene -- itulah sebabnya "semua teduh" kini merah.
Jerawat di lake tetap tidak tertangkap: di sudut kamera lake ia tidak jatuh
ke titik uji.
