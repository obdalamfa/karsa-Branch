---
judul: "Ubin dilebur membekukan cahaya siang-malam"
tipe: bug
status: selesai
ditemukan: "2026-10-13"
commit_perbaikan: (sesi gauntlet M1, 2026-10-13)
dijaga_oleh: cahaya_global
tags: [bug, status/selesai]
---

# 🐞 Ubin dilebur membekukan cahaya siang-malam

## Gejala

`cahaya_global` gagal di swarga (05 Okt) lalu di beach (13 Okt). Ambient
dipaksa ke 0,02, tapi rerata layar cuma turun ~11 dari 309. Tanah tetap
seterang tengah hari.

## Sebab

Optimasi `_lebur_ubin_statis` (086fe0c, FPS 19→48) memasang
`gnp.getNetState()` ubin pertama di node `ubin_statis` yang tergantung
langsung di bawah `scene`. ShaderAttrib di net state itu membawa salinan
`sm_ambient`/`sm_sun_color`/`sm_sun_dir` yang dipasang Ursina per entity.
Akibatnya nilai beku itu menimpa uniform `scene` untuk seluruh tanah.
Penyakitnya sama dengan yang pernah dijaga `cahaya_global`, hanya jalur
masuknya baru.

## Perbaikan

`game/world.py`: ketiga uniform global dicabut (`clearShaderInput`) dari
ShaderAttrib `bersama` sebelum `akar.setState`.

Bukti: rerata layar beach sebelum (114,115,80)→(111,110,79), turun 11.
Setelah diperbaiki, `_cahaya_b.png` gelap merata dan beach lulus.

## Yang menjaganya sekarang

`cahaya_global` di `tools/regress.py` yang dulu menangkapnya. Penjaga itu
sudah terbukti merah saat bug ada.
