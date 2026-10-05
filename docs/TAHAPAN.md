# TAHAPAN — dari tambal-menambal ke penyempurnaan

Urutannya bukan selera. Tiap tahap membuka tahap berikutnya, dan tahap yang
dilompati akan menagih ongkosnya belakangan.

---

## Tahap 0 — Amankan kerja ✅ SELESAI

Commit `09ef02f`, 96 file, 12.296 baris. Sebelum ini seluruh sesi ada di
working tree tanpa jaring apa pun, dan satu agen sudah pernah menjalankan
`git stash` di tengah kerja agen lain.

---

## Tahap 1 — Jaring pengaman ✅ SELESAI

**`tools/regress.py`** — boot tiap scene, buktikan ia dirender, dan periksa
hal-hal yang memang PERNAH rusak di proyek ini.

Kenapa ini duluan, bukan fitur: verifikasi manual sudah gagal **dua kali**
sesi ini. WASD dinyatakan beres padahal belum, dan dua kali sebuah metode
disisipkan di tengah fungsi sehingga fungsi induknya mati total. Keduanya
ketahuan karena kebetulan diuji ulang. Yang ketiga tidak akan ketahuan.

Yang diperiksa, tiap satu terikat kegagalan nyata:

| Cek | Kegagalan nyata yang melatarinya |
|---|---|
| entity bergeometri nol | bug NodePath-bersama, terjadi **dua kali** |
| frame kosong / hampir semua langit | "rumah ga muncul" |
| pemain di tile bisa-jalan | terjepit permanen |
| motif dalam rentang, mood terhingga | mesin motif baru |
| save bolak-balik utuh | format save berubah, save lama tidak boleh rusak |
| ms per frame | 4–29 FPS, belum pernah diprofil |

**Selesai kalau:** perintahnya jalan, mengeluarkan tabel LULUS/GAGAL, dan
melaporkan kondisi SEKARANG apa adanya — termasuk yang gagal.

**Catatan penyelesaian.** Syarat itu baru benar-benar terpenuhi setelah TIGA
cacat di alatnya sendiri diperbaiki, dan ketiganya menghasilkan kegagalan PALSU
yang sempat dipercaya:

1. `frame_kosong` menuduh enam scene (shop, house, lake, cemetery, beach,
   clinic) tidak terender. Ternyata `taskMgr.step()` tidak menjamin buffer
   selesai digambar sebelum `getScreenshot()` membacanya;
   `tools/capture.py` merender scene yang sama dengan puluhan ribu warna.
   Efek sampingnya lebih buruk lagi: `ms/frame` ikut membengkak ke 122–149 ms
   untuk scene yang sebenarnya 22 ms. Setelah `renderFrame()` eksplisit,
   **14/14 lulus** dan rentangnya **21,8–58,8 ms**, yaitu **17–46 FPS** —
   bukan 4–29 FPS seperti yang tercatat di tabel ini.

2. `motif_waras` menuduh `swarga` gagal secara acak. Pemeriksaan itu memakai
   mesin motif milik state yang sama untuk tiap scene dan memajukan 240 menit
   tiap kali; setelah belasan scene, `lapar` menempel di dasar -100 dan laju
   peluruhannya menjadi nol, sehingga syarat "harus turun" mustahil dipenuhi.
   Kegagalannya bergantung urutan scene, bukan kesehatan motif.

3. Seluruh 14 scene pernah dilaporkan GAGAL sekaligus, dengan seragam
   `frame_kosong`. Itu bukan cacat scene: `regress.py` membuka jendela
   sungguhan, dan saat Windows menolak `SetForegroundWindow()` isinya tidak
   pernah digambar sehingga `getScreenshot()` membaca buffer kosong. Cacatnya
   bukan bahwa hal itu bisa terjadi — melainkan bahwa alatnya **memberi vonis**
   atas keadaan yang bukan milik scene. Sekarang kegagalan seragam semacam itu
   dilaporkan sebagai LINGKUNGAN BERMASALAH dan keluar dengan kode **2**,
   dibedakan dari kode 1 yang berarti ada scene yang benar-benar rusak. Ada juga
   `--offscreen` untuk melepas ketergantungan pada jendela sama sekali.

Alat yang melaporkan kegagalan palsu lebih berbahaya daripada tidak ada alat:
ia mengajarkan untuk mengabaikan alarmnya. Kegagalan nomor 3 tertangkap ulang
saat memperbaikinya — dan kali ini alatnya menolak memberi vonis.

---

## Tahap 2 — Verifikasi yang sudah terlanjur ada ✅ SELESAI (diverifikasi)

`economy.py`, `husbandry.py`, `crops.py`, `tool_models.py` mendarat di disk
saat agennya mati. **Belum ada yang membuktikan isinya berfungsi.** Sekarang
ada belasan sistem berstatus tidak jelas.

Aturannya: tidak ada fitur baru sampai yang ada terbukti jalan atau ditandai
rusak dengan jujur. Sistem setengah jadi yang diklaim selesai lebih berbahaya
daripada sistem yang belum dibuat.

### Caranya: tagih klaim yang ditulis modulnya sendiri

`tools/verifikasi.py`. Yang diuji **bukan** "apakah modulnya impor" — itu
membuktikan tidak ada apa-apa. Modul-modul ini menulis angka di docstring-nya
sendiri, dan angka yang ditulis sendiri boleh ditagih: pita 3,0–5,7 G/EN,
uplift olahan ~40%, "selalu ada selisih beli-jual", Peti Kirim 85%.

Temuannya dipisah tiga, karena ketiganya memang beda dan memvonis sama membuat
laporannya tidak bisa dipercaya:

| kelas | arti |
|---|---|
| **RUSAK** | ada akibatnya di permainan SEKARANG. Diperbaiki. |
| **RAPUH** | benar hari ini karena kebetulan. Satu perubahan kecil membatalkannya, tanpa error. |
| **KEPUTUSAN** | menyimpang dari yang ditulis, tapi mana yang benar keputusan pemilik. |

### Yang LULUS, dengan angkanya

| klaim modul | hasil |
|---|---|
| olahan menambah ~40% | 12 resep, semuanya **+38..41%** (pakan +50%, memang nilai pakai) |
| selalu ada selisih beli-jual | 10 barang toko, **tidak satu pun** bisa dijual ≥ harga belinya |
| Peti Kirim 85% | 80 barang, semuanya tepat 85% (minimal 1) |
| tanam→siram→tumbuh→panen | **17 tanaman**, semuanya menyelesaikan siklus penuh |
| model alat 8 slot | **8 jenis**, semuanya bergeometri nyata (kotak batas > 0) |

### Yang RUSAK dan sudah diperbaiki

**1. Separuh sistem ternak terpasang: peluruhannya, bukan perawatannya.**
Ini yang terburuk, dan paling tidak kelihatan. `husbandry.daily_tick` dipanggil
tiap pagi dari `TimeController`, tapi `husbandry.feed`, `water` dan `clean`
**tidak punya pemanggil di seluruh `game/`.** Takaran turun 45–55 tiap malam
dan tidak ada apa pun yang bisa mengisinya. Disimulasikan delapan ternak
dengan satu-satunya permainan yang mungkin — tanpa aksi, karena aksinya tidak
terjangkau:

```
hari 3   kenyang semua ternak menyentuh 0
hari 4   KEDELAPAN ternak sakit permanen
hari 6   hati SEMUA hewan menyentuh 0
```

Dan `_ternak_pagi` — satu-satunya hasil berguna dari tick itu — ditulis lalu
**tidak pernah dibaca siapa pun**. Jadi yang mendarat di permainan cuma efek
sampingnya: hewan sakit permanen dan hubungan yang hancur, tanpa satu pun pintu
untuk mencegahnya. Baris pemanggilnya ditambahkan dengan alasan yang benar
("tanpa baris ini, merawat hewan tidak berakibat apa pun"); yang terlewat
adalah bahwa hanya separuh sistemnya yang tersambung.

Dihentikan — **bukan dihapus.** Modulnya utuh; komentar di `time_controller.py`
menuliskan empat sambungan yang dibutuhkan supaya bisa dihidupkan kembali.

**2. Harga 23 barang bergantung urutan impor.** `economy.ITEM_VALUES` dibangun
sekali saat impor dari `data.CROPS`; `crops.py` *menambahkan* 16 palawija + 7
pohon ke `data.CROPS` saat ia diimpor. Terukur: `padi` = **45G** kalau crops
lebih dulu, **0G** kalau economy lebih dulu — tanpa error, tanpa log, cuma
panen yang tidak laku. Permainan kebetulan aman karena `world.py` mengimpor
crops di tingkat modul; satu impor yang dipindah membatalkannya. Sekarang
`sell_price`/`item_name` mencari ulang ke CROPS yang hidup, jadi kedua urutan
memberi 45G.

**3. Dua hasil ternak tanpa harga.** `husbandry` menghasilkan `telur_bebek` dan
`susu_kambing`; keduanya 0G di `economy`, jadi `collect()` menaruh barang tanpa
harga di tas. Diberi harga **38** dan **45** — bukan angka karangan baru:
`husbandry.SPECIES_CARE` sudah mencatat `harga` per spesies, dan angka itu
memang melacak harga produknya (sapi 40/susu 42, ayam 30/telur 32, domba
55/wol 58).

### Yang ditandai, bukan diperbaiki — keputusan pemilik

1. **Tiga tanaman di luar pita G/EN.** `cabai` 7,50 · `ubi_jalar` 6,67 ·
   `ubi_kayu` **10,77** G/EN, lawan pita 3,0–5,7 yang ditulis economy.py
   sendiri. Pitanya disetel untuk delapan tanaman `data.py`; `crops.py`
   menambah sembilan lagi tanpa ikut ditagih. ubi_kayu 1,9× langit-langit: kalau
   angkanya benar ia strategi dominan, kalau pitanya benar harga ubi_kayu yang
   harus turun.
2. **economy.py dan husbandry.py tidak sepakat soal ternak.** bebek
   (telur/1h vs telur_bebek/2h), kambing (wol/2h vs susu_kambing/2h), domba
   (wol/2h vs wol/5h). Memilih salah satu berarti memensiunkan yang lain —
   itu keputusan desain, bukan efek samping perbaikan bug.
3. **16 benih tanaman baru tidak bisa dibeli.** `crops.seed_shop_rows()`
   menyiapkan 16 baris; **nol** yang ada di `data.SHOP_ITEMS`. crops.py sendiri
   menjelaskan sebabnya: panel toko memilih dengan tombol 1–9. Jadi tanamannya
   tumbuh, berharga, punya model — tapi pemain tidak punya jalan memulainya.
   Memperbaikinya berarti mengubah panel toko (gulir/halaman).

### Dua lulus palsu di alatnya sendiri, dan keduanya tertangkap

Pola Tahap 1 berulang, jadi dicatat: **alat yang memberi lulus palsu lebih
berbahaya daripada tidak ada alat.**

1. Pemeriksa "siapa memanggil husbandry" membaca sumber mentah — termasuk
   komentar. Komentar perbaikan yang baru ditulis di `time_controller.py`
   memuat contoh `husbandry.feed(s, animal_id)`, dan pemindainya menganggap
   contoh itu pemanggilan sungguhan, lalu menyatakan perawatan ternak
   "tersambung" padahal nol pemanggil. **Dokumentasi perbaikannya mengalahkan
   alat yang memeriksanya.** Sekarang komentar dan isi string dibuang lewat
   `tokenize` sebelum dicocokkan.
2. Pemeriksa model alat tidak membuat `Ursina()` lebih dulu. Tanpa aplikasi,
   Ursina cuma mencetak peringatan lalu mengembalikan objek setengah jadi —
   sehingga alat yang sama sekali tidak dibangun tetap terbaca "bergeometri".
   Sekarang aplikasinya dibuat sungguhan dan yang ditanya `getTightBounds()`.

Versi pertama pemeriksa pakan juga pernah menyatakan `water` hidup karena
mencocokkan kata telanjang `water` dengan `sound_play('water')`.

**Status akhir:** `python tools/verifikasi.py` → **0 RUSAK**, 2 RAPUH,
3 KEPUTUSAN. `tools/regress.py` → 14/14 scene lulus, 0 pemeriksaan gagal.

---

## Tahap 3 — Performa 🔄 SUDAH DIPROFIL, empat perbaikan mendarat

4–29 FPS, belum pernah diprofil, jumlah entity terus naik (1126 di kandang).
Setiap perbaikan visual dinikmati lewat slideshow.

Dua jalan: optimasi bertahap (batching, culling, kurangi entity) yang aman,
atau perombakan renderer yang berisiko. Mulai dari yang pertama **sambil
mengukur**. Kalau mentok di bawah 30 FPS, itu keputusan besar tentang seberapa
jauh Ursina sanggup dibawa — dan itu keputusan pemilik, bukan keputusanku.

### Alat ukurnya dulu: `tools/profil.py`

Satu hal harus dibereskan sebelum satu baris pun dioptimalkan — **angka mana
yang sah di kontainer tanpa GPU.** Alat ini memisahkan tiga, bukan satu:

| kolom | isinya | sah di mesin pemilik? |
|---|---|---|
| LOGIKA | Python di dalam `Game3D.update` | ya |
| URSINA | Python di luar update: loop per-entity Ursina | ya |
| GAMBAR | di dalam `GraphicsEngine.renderFrame()` | **tidak** — llvmpipe |

Versi pertama alat ini cuma punya LOGIKA dan "SISANYA", dan itu **menyesatkan
diri sendiri**: SISANYA ikut menampung ~14 ms Python milik Ursina di bawah
label "abaikan, itu llvmpipe". Padahal itu CPU murni dan berlaku di mesin mana
pun. Kesalahan itu ketemu dari tabel panggilannya sendiri —
`has_disabled_ancestor` 777 panggilan/frame tidak mungkin pekerjaan GPU.

### Yang ditemukan, dan harganya

Keempatnya satu pola yang sama: **nilai yang tidak berubah ditulis ulang tiap
frame.** Tidak ada satu pun yang ditemukan dengan menebak; semuanya dari tabel
panggilan.

| temuan | harga (scene mountain) | perbaikannya |
|---|---|---|
| `grs_time`/`grs_wind` didorong ke 461 entity rumput satu-satu | 3,12 ms/frame, 922 panggilan `set_shader_input` | didorong **sekali** ke `scene`; Panda3D mewariskannya ke anak |
| `.text` HUD di-set tiap frame walau jamnya sama | 1,32 ms/frame, 841 `text` + 1.442 `create_text_section` per 60 frame | set hanya kalau isinya berubah |
| penghitung debug bawaan Ursina memindai seluruh `scene.entities` | 1,28 ms/frame + `enabled_getter` 5.669 panggilan/frame | dimatikan (`KARSA_DEBUG_COUNTER=1` untuk menghidupkan) |
| `.enabled` 230 partikel cuaca ditulis ulang tiap frame walau cerah | 1,13 ms/frame, `stash()` 232 panggilan/frame | hanya saat cuacanya berganti |

Yang ketiga bukan kode proyek ini melainkan **cacat di Ursina 7**
(`window.py:180/190`): penjaganya menulis `self.entity_counter.i = 0` padahal
yang diperiksa `self.entity_counter.t > 1`. Karena `t` tidak pernah direset,
lewat satu detik pemindaiannya berjalan di **setiap** frame selamanya, bukan
sekali sedetik seperti yang jelas dimaksud.

### Hasilnya, diukur

CPU (LOGIKA + URSINA, kolom yang sah di mana pun), scene mountain:
**18,62 ms → 12,88 ms**, dan LOGIKA sendiri **7,78 ms → 1,91 ms**.

`tools/regress.py`, ms/frame ujung-ke-ujung tanpa profiler menempel:

| scene | sebelum | sesudah |
|---|---|---|
| farm | 70,3 | **42,0** |
| town | 87,7 | **67,8** |
| mountain | 72,5 | **48,0** |
| beach | 96,3 | **60,9** |
| house | 86,7 | **54,2** |
| lake | 63,7 | **48,8** |

14/14 scene masih lulus, 0 pemeriksaan gagal.

**Angka ms/frame itu tetap didominasi llvmpipe** dan BUKAN ramalan FPS di mesin
pemilik. Yang boleh dipercaya penuh cuma kolom CPU di atas.

### Jaring pengamannya ikut tumbuh

Optimasi rumput bisa gagal **tanpa error**: input shader per-entity menindih
input induk, jadi satu panggilan `set_shader_input` yang kembali ke entity akan
membekukan rumputnya diam-diam. Itu tidak boleh dijaga dengan niat baik, jadi
`tools/probe_rumput.py` mengukurnya — menghitung piksel yang bergerak antara
`grs_time` 0 dan 3,7, dan membandingkan kedua jalur berdampingan:

```
per-entity  0,590 ms/frame, 65.870 piksel berubah (maks kanal 147)
scene       0,004 ms/frame, 66.008 piksel berubah (maks kanal 147)
```

Angka piksel yang praktis sama itu sekaligus **bukti uniform-nya memang sampai
ke shader** — bukan diam-diam hilang. Sekarang jadi baris `rumput_hidup` di
regress.

### Yang masih tersisa

Sisa CPU terbesar sekarang **loop per-entity Ursina sendiri** (`main.py:_update`
plus `has_disabled_ancestor`/`enabled_getter` yang diseretnya): ±11 ms/frame di
mountain, dan itu sebanding lurus dengan jumlah entity — 2.210 di mountain.
Menurunkannya berarti benar-benar **mengurangi entity** (menggabung tile tanah
jadi satu mesh), bukan lagi membuang panggilan yang terbuang. Itu perubahan
struktural pada `world.py`, bukan tambalan, jadi berhenti di sini dulu.

---

## Tahap 4 — Wishes

**Ini yang membuat game punya alasan untuk dipedulikan.** Sekarang sudah ada
kebutuhan, objek, aksi, antrian — tapi pemain bisa main lima menit lalu
bertanya "terus?".

Jawaban The Sims 3 adalah Wishes: sim memunculkan keinginan kontekstual,
pemain menjanjikan beberapa, memenuhinya membayar Lifetime Happiness. Itu
memberi arah **tanpa** mencabut kebebasan — dan "kebebasannya seru" adalah
kata-kata pemilik sendiri.

Prioritas tertinggi setelah fondasi bersih. Di atas seni apa pun.

---

## Tahap 5 — Autonomi

Termurah, dampak paling besar. `choose_action()` dan `autonomy_candidates()`
**sudah dibangun dan teruji**; belum ada yang memanggilnya. Begitu tersambung
ke NPC, desa mulai hidup sendiri.

---

## Tahap 6 — Traits dan moodlets

Lima sifat per sim yang benar-benar mengubah perilaku dan wish yang muncul.
Mood jadi jumlah moodlet bernama dengan ikon dan timer, bukan rata-rata —
moodlet menjelaskan dengan kata-kata kenapa sim merasa begitu. Sekalian
delapan motif dipangkas jadi enam (Sims 3): Nyaman dan Ruangan jadi moodlet.

---

## Tahap 7 — Misteri dan entitas

Mesin tahapan ala StrangerVille, ekonomi petunjuk, dan mob yang benar-benar
memanipulasi cerita. Bahasa rupa dari logo: halo gerigi, mata dalam daun,
sulur, dan **akar yang berupa jalur sirkuit siku-siku**.

Sengaja di sini, bukan karena tidak penting, tapi karena StrangerVille bekerja
justru karena kehidupan biasa terus berjalan normal di sekelilingnya. Kalau
kehidupan biasanya belum ada, horornya tidak punya latar untuk mengganggu.

---

## Tahap 8 — Audio

Musik masih terasa seram; agennya gagal empat kali kena limit sesi. Materi
seramnya tidak dibuang — dipindah ke kuburan, gua, dan dungeon. Kontras itu
justru yang membuat lapisan horor bekerja.

---

## Yang TIDAK akan dikejar

**Open world Sims 3.** Lima belas scene terpisah dengan frame rate segini
membuat itu lubang tanpa dasar. Yang dikejar cukup menghilangkan *rasa*
loading: transisi instan, kamera mempertahankan sudut, mendarat di tempat
yang masuk akal. Ini penyimpangan yang disengaja, bukan kesetaraan dengan TS3,
dan tidak akan diakui sebagai kesetaraan.
