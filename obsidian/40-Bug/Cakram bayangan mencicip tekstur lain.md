---
judul: "Cakram bayangan mencicip tekstur lain"
tipe: bug
status: selesai
ditemukan: "2026-10-18"
commit_perbaikan: (workstream D, sesudah ed063dc)
dijaga_oleh: _bench/probes/probe_cakram_capture.py
tags: [bug, status/selesai, cahaya, bayangan]
---

# 🐞 Cakram bayangan mencicip tekstur lain

## Gejala

Di tangkapan `tools/capture.py --scene farm --hour 10` (jalur yang juga
dipakai gauntlet), pemain berdiri di atas **lajur papan kayu** dan pangkal
pohon di kanan duduk di **kotak rumput hijau**. Keduanya tidak ada di peta;
yang seharusnya di sana adalah bayangan kontak yang gelap.

## Sebab

Cakram bayangan kontak (game/bayangan.py, ed063dc) dibuat dengan
`shader=None`. Di Ursina itu berarti tidak ada shader sama sekali, jadi
cakram digambar pipeline fixed-function -- tanpa TextureAttrib. GL lalu
memakai tekstur yang terakhir terikat, dan warna vertex gelap cakram cuma
mewarnainya.

`probe_bayangan_kontak.py` tidak melihatnya: ia menempuh jalur boot
probe_cahaya, yang urutan gambarnya lain, dan di sana cakram kebetulan
gelap. Alat ukur yang benar di satu jalur tidak membuktikan jalur lain
(aturan #2).

## Angka (capture.py, fixture ladang_hari10, 1280x720)

Selisih rerata RGB dengan cakram minus tanpa cakram:

| wilayah | sebelum | sesudah |
|---|---|---|
| kaki pemain | (+14,2, +12,7, +9,9) | (-5,9, -4,2, -2,4) |
| pangkal pohon kanan | (-10,5, +14,8, -4,3) | (-0,8, -0,5, -0,3) |

## Perbaikan

Di pipeline GL cakram memakai `unlit_shader` Ursina (warna vertex x tekstur
putih bawaan Panda); di D3D9 teksturnya dimatikan eksplisit
(`setTextureOff(1)`).

## Penjaga

`_bench/probes/probe_cakram_capture.py` -- dua tangkapan capture.py (dengan
dan tanpa cakram), menuntut wilayah kaki dan pangkal pohon menggelap tanpa
kanal yang naik > 3. MERAH pada kode lama, hijau sesudahnya.
