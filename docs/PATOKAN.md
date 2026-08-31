# PATOKAN — kenapa gauntlet loop belum bisa dijalankan di sini

Patokannya **Story of Seasons: A Wonderful Life (remake 2023)**. Yang
dibandingkan **screenshot gameplay** — game yang sedang dimainkan, oleh siapa
pun. Halaman Steam-nya sendiri dan frame dari video gameplay sama sahnya
dengan main sendiri; itu tetap game yang merender dirinya.

Yang tidak boleh: art resmi, render, still cutscene, dan frame trailer.
Semuanya lewat pipeline berbeda, sering di-stage, dan biasanya HUD-nya
dicopot — untuk potongan `hud_default` itu membuat frame-nya tidak berguna,
dan untuk `character_closeup`, still cutscene punya kamera dan pencahayaan
yang bukan kamera main.

Dan yang paling tidak boleh: **ingatan tentang game-nya**. Baris itu yang jadi
masalah.

---

## Yang terukur

Sesi web ini tidak bisa mengambil patokannya sendiri. Diukur, bukan diduga:

```
https://store.steampowered.com -> 000   ditolak
https://en.wikipedia.org       -> 000   ditolak
https://api.github.com         -> 200
```

Dan `_bench/refs/` kosong, karena patokan **sengaja tidak di-commit** — lihat
bagian berikutnya.

Dua hal itu bersama-sama berarti: kritikus yang dijalankan di sesi web tidak
punya apa pun untuk dibandingkan, dan tidak akan pernah punya.

---

## Kenapa itu bukan gangguan kecil

Skill gauntlet-loop menyebut satu kegagalan sebagai yang paling sering
terjadi, dan ini persis kegagalan itu:

> *"A vague bar. The critic invents a comparison and approves everything.
> Most common failure by far."*

Kritikus tanpa frame patokan **tidak akan** berkata "aku tidak punya
patokan". Ia akan menulis perbandingan yang terdengar masuk akal dari ingatan
tentang AWL, memilih pemenang, lalu meluluskan potongan itu. Loopnya berhenti
di ronde satu, laporannya penuh, dan tidak ada satu pun kalimat di dalamnya
yang bersandar pada sesuatu yang nyata.

Loop yang meluluskan semuanya lebih buruk daripada tidak ada loop, karena ia
menghasilkan bukti palsu bahwa pekerjaannya sudah selesai.

---

## Yang sudah dipasang supaya itu tidak bisa terjadi

**`_bench/.gitignore` mengabaikan `refs/`, dan itu keputusan sadar.**

Sempat dibuka supaya patokan tidak hilang tiap container ditarik. Itu memang
masalahnya, tapi jalan keluarnya salah: **repo ini publik**. Meng-commit
tangkapan layar Story of Seasons ke repo publik adalah redistribusi karya
orang lain — beda urusan dengan menyimpannya lokal untuk pembandingan
internal, yang justru dituliskan MANIFEST-nya sendiri.

Konsekuensinya diterima dengan sadar dan tidak perlu dikeluhkan lagi:
**patokan hilang tiap container ditarik, jadi gauntlet loop hanya bisa
dijalankan di mesin yang menyimpan berkasnya — bukan di sesi web.**

`MANIFEST.json` tetap ter-commit; ia bukan karya orang lain, ia daftar frame
apa yang dibutuhkan.

`_bench/progress.html` juga tidak di-commit, dan itu bukan kelalaian.
`progress_page.py` meng-embed lembar perbandingan sebagai data URI, jadi
meng-commit halaman itu akan menyelundupkan frame patokan lewat pintu belakang
tanpa satu pun berkas gambar ikut ter-stage. Tidak ada yang hilang: halaman itu
turunan, dan `bash tools/bench.sh` membangunnya ulang dalam ~3,5 menit.

**`bar_gate.py check` menolak jalan kalau patokan bocor ke git.** Komentar yang
meminta orang mengingat bukan jaring pengaman. Sudah diuji dua arah: bersih
lolos, satu berkas yang di-`git add -f` membuat gerbangnya tertutup dengan
sebab yang disebut.

**`tools/bar_gate.py check`** menolak jalan kalau frame yang diminta
`_bench/refs/MANIFEST.json` tidak ada — keluar dengan kode 1, bukan sekadar
memperingatkan. Berkas kosong dan placeholder 1×1 juga ditolak (minimal 20 KiB
dan sisi terpendek 480 px), supaya `touch farm_wide.png` tidak cukup untuk
membuka gerbangnya.

**`tools/bar_gate.py pair`** menyusun lembar A/B dengan label dicopot dan
urutan **diacak**, lalu menulis kuncinya ke berkas terpisah. Kritikus menerima
lembarnya saja. Tanpa ini "buta" cuma janji: agen yang tahu gambar kiri buatan
sendiri akan memilih gambar kiri.

**`tools/bar_gate.py reveal`** dijalankan **setelah** kritikus menjawab, oleh
pemanggilnya. Kode keluar 0 kalau kritikus memilih punya kita, 2 kalau belum —
jadi keputusan "lanjut atau ulang" tidak bergantung pada agen mana pun yang
menilai dirinya sendiri.

---

## Halaman progres

`_bench/progress.html` — **Karsa Bench**. Delapan potongan, tiap satu terikat
pada satu frame patokan di MANIFEST, lengkap dengan pertanyaan jurinya dan
tangkapan layar keadaan kita sekarang.

Perbarui dengan satu perintah, lalu publish ke URL Artifact yang sama:

```
bash tools/bench.sh          # tangkapan + regresi + gerbang + halaman
bash tools/bench.sh --cepat  # lewati regresi
```

Halaman itu sengaja membedakan tiga keadaan yang mudah tertukar:
**menunggu patokan** (frame aslinya belum ada — belum ada yang BISA menilai),
**masih kalah** (sudah dinilai buta dan kalah), dan **menang buta**. Selama
gerbangnya tertutup, kedelapan potongan berstatus yang pertama.

---

## Yang perlu Anda lakukan supaya loopnya bisa jalan

Delapan frame, semuanya tercantum di `_bench/refs/MANIFEST.json` lengkap
dengan situasi yang harus ditangkap:

| slug | yang harus terlihat |
|---|---|
| `farm_wide` | ladang dari jarak main biasa, siang cerah |
| `farm_closeup` | berdiri di antara tanaman, kamera dekat |
| `hud_default` | layar main biasa tanpa menu terbuka |
| `character_closeup` | satu penduduk dari jarak percakapan |
| `character_midshot` | penduduk seluruh badan, jarak main biasa |
| `village_wide` | beberapa bangunan dan penduduk sekaligus |
| `barn_interior` | di dalam kandang bersama ternak |
| `evening_light` | luar ruang saat senja |

PNG resolusi penuh, minimal 1280×720, **tidak di-crop dan tidak disunting** —
yang dinilai termasuk bagaimana permainannya membingkai layarnya sendiri.
Idealnya kedelapan frame dari sumber dan pengaturan grafis yang sama, supaya
perbandingannya tidak tercemar beda setting.

Simpan sebagai `_bench/refs/<slug>.png`. **Jangan di-commit** — gitignore dan
`bar_gate` sudah menjaganya. Lalu:

```
python tools/bar_gate.py check
```

Kalau gerbangnya terbuka, loopnya boleh jalan.

---

## Yang sudah dikerjakan tanpa patokan, dan kenapa itu sah

Sebagian cacat tidak butuh AWL untuk dinilai. HUD yang terpotong di tepi layar
salah tanpa perlu dibandingkan dengan apa pun; panel yang barnya tertimbun
latarnya sendiri juga. Yang seperti itu dikerjakan dan diukur sendiri:

| cacat | diukur sebagai | pemeriksaan |
|---|---|---|
| HUD terpotong | tepi elemen lewat `±aspect/2` | `hud_muat` |
| bar motif tertimbun | piksel layar ≠ warna yang diminta | `hud_terbaca` |
| rumput papan catur | korelasi terang dengan paritas ubin | `rumput_catur` |
| avatar gumpalan putih | jumlah warna vertex + shader pembacanya | `avatar_warna` |

Tiap pemeriksaan diuji **GAGAL dulu pada kode lama** sebelum dipercaya. Cek
yang tidak pernah bisa gagal tidak membuktikan apa pun.

Yang **tidak** dikerjakan tanpa patokan: setiap penilaian yang berbentuk
"punya kita lebih baik". Tidak ada satu pun klaim seperti itu di repo ini
sampai `bar_gate check` terbuka.
