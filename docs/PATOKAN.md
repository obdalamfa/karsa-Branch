# PATOKAN — kenapa gauntlet loop belum bisa dijalankan di sini

Patokannya **Story of Seasons: A Wonderful Life (remake 2023)**. Yang
dibandingkan tangkapan layar dari game yang benar-benar dijalankan — bukan art
resmi, bukan trailer, bukan gambar promosi, dan **bukan ingatan tentang
game-nya**.

Baris terakhir itu yang jadi masalah.

---

## Yang terukur

Sesi web ini tidak bisa mengambil patokannya sendiri. Diukur, bukan diduga:

```
https://store.steampowered.com -> 000   ditolak
https://en.wikipedia.org       -> 000   ditolak
https://api.github.com         -> 200
```

Dan `_bench/refs/` kosong. `_bench/.gitignore` dulu berisi `*`, jadi patokan
yang sudah pernah diambil **tidak pernah ter-commit** dan hilang bersama
container sesi itu.

Dua hal itu bersama-sama berarti: kritikus yang dijalankan di sini tidak punya
apa pun untuk dibandingkan.

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

**`_bench/.gitignore` sekarang mengizinkan `refs/`.** Patokan yang diambil
akan ikut ter-commit dan tidak bisa hilang lagi bersama container.

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
Simpan sebagai `_bench/refs/<slug>.png`, commit, lalu:

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
