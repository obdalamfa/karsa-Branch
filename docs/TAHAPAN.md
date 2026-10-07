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

## Tahap 4 — Wishes ✅ SELESAI

**Ini yang membuat game punya alasan untuk dipedulikan.** Sekarang sudah ada
kebutuhan, objek, aksi, antrian — tapi pemain bisa main lima menit lalu
bertanya "terus?".

Jawaban The Sims 3 adalah Wishes: sim memunculkan keinginan kontekstual,
pemain menjanjikan beberapa, memenuhinya membayar Lifetime Happiness. Itu
memberi arah **tanpa** mencabut kebebasan — dan "kebebasannya seru" adalah
kata-kata pemilik sendiri.

Prioritas tertinggi setelah fondasi bersih. Di atas seni apa pun.

### Kenapa bukan quest

Quest sudah ada di proyek ini — `quest_controller.py`, sebelas tahap berurutan
— dan ia **tidak** menjawab "terus?", karena quest memberi satu jalan yang sama
untuk semua pemain. Wishes bekerja dengan arah berlawanan:

    quest     : game yang memutuskan, pemain mengikuti
    keinginan : pemain yang memutuskan, game membayar

### Mekanismenya, empat langkah — dan yang keempat tidak boleh ditunda

```
1. muncul   keinginan kontekstual — hanya yang masuk akal SEKARANG
2. janji    pemain memilih sendiri empat yang mau dikejar
3. bayar    memenuhinya membayar Kebahagiaan
4. belanja  Kebahagiaan ditukar jadi kemampuan permanen
```

Tanpa langkah 4, Kebahagiaan cuma angka yang naik, dan angka yang tidak bisa
dibelanjakan tidak memberi arah apa pun. Jadi hadiahnya ikut dibangun sekarang,
bukan dijanjikan untuk nanti.

### Tiga keputusan yang menentukan apakah ini jujur

**1. Garis dasar dicatat saat DIJANJIKAN.** Ini intinya. Kalau "hasilkan 600G"
diukur dari `stats['earned']` apa adanya, pemain yang sudah pernah menjual
10.000G menyelesaikannya seketika tanpa melakukan apa pun — sistemnya membayar
pemain untuk masa lalunya. Jadi tiap janji menyimpan angka awalnya sendiri, dan
kemajuan selalu selisih terhadap angka itu. Diuji langsung:
`earned = 10.000`, janji "600G" → **0/600**, dan baru selesai pada 600 yang
benar-benar baru.

**2. Tawaran tetap sepanjang satu hari-game.** Diundi dari benih
`(tahun, hari)`. Tawaran yang berubah tiap kali panel dibuka mengajarkan pemain
membuka-tutup panel sampai dapat yang enak — itu mesin judi, bukan pilihan.

**3. Empat slot, bukan delapan.** Kalau semua keinginan bisa dijanjikan
sekaligus, tidak ada yang ditolak — dan kalau tidak ada yang ditolak, tidak ada
keputusan.

Dua jenis keinginan, karena memang ada dua bentuk: **tambah** dihitung dari
selisih ("panen 5 tomat"), **ambang** dari nilai mutlak ("capai 4 hati dengan
Sari"). Keinginan ambang tidak pernah ditawarkan kalau pemain sudah
melewatinya — kalau tidak, ia selesai di detik yang sama ia dijanjikan.

### Isinya

Dua belas jenis keinginan di lima kategori (Tani, Ekonomi, Sosial, Ternak,
Petualangan), semuanya bergerbang relevansi: "Panen 5 Tomat" tidak muncul tanpa
benih tomat, keinginan tambang tidak muncul tanpa pickaxe, keinginan bertarung
tidak muncul tanpa pedang.

Tiga hadiah, dan tiap satu menunjuk field yang **terbukti dibaca** kode
permainan:

| hadiah | efek | field |
|---|---|---|
| Napas Panjang | +10 energi maksimum, maks 5× | `max_energy` |
| Badan Kuat | +15 HP maksimum, maks 4× | `max_hp` |
| Pulih Cepat | +0,4 HP/detik saat diam, maks 3× | `hp_regen_rate` |

Syarat "terbukti dibaca" itu diperiksa otomatis, dan alasannya ada di repo ini:
`state.upgrades` (hoe/water/bag/axe) duduk di save sejak lama dan **tidak
dibaca di mana pun**. Menjual "upgrade cangkul" sebagai hadiah akan mengambil
Kebahagiaan pemain dan memberi nol. `max_energy` dipilih sebagai hadiah utama
karena doktrin `economy.py` sendiri: *"Energi, bukan waktu, adalah sumber daya
langka."*

### Dua alat, karena ada dua hal berbeda yang bisa gagal

| alat | yang dibuktikan |
|---|---|
| `tools/uji_wishes.py` | **mesinnya benar** — 41 pemeriksaan, murni logika, tanpa jendela |
| `tools/probe_wishes.py` | **pemain bisa mencapainya** — 12 pemeriksaan lewat jalur tombol sungguhan di permainan yang berjalan |

Yang kedua ada karena kegagalan jenis itu sudah terjadi di proyek ini dan tidak
terlihat sebagai error apa pun: `husbandry.py` lengkap dan benar, tapi tidak
ada yang memanggilnya. Jadi probe menekan tombol sungguhan — `[l]` membuka,
`[1]` berjanji, `[6]` melupakan, `[a]` membeli, `ESC` menutup — lalu memeriksa
seluruh teks panel ada **di dalam** layar lewat `getTightBounds`, dan bahwa
panelnya benar-benar mengubah piksel (97,1%). Keduanya masuk `regress.py`.

### Yang ketangkap saat mengujinya

Keinginan sosial **tidak pernah muncul**: `wishes.py` mengimpor `NPCS` dari
`data.py`, dan dict itu tidak ada — namanya `HUMAN_NPCS`. Tidak terlihat
sebagai error karena `tawaran()` sengaja menangkap exception per-keinginan
supaya satu templat rusak tidak mengosongkan seluruh papan. Ketahuan dari uji,
bukan dari memainkannya.

Dan satu lulus palsu lagi di alatnya sendiri, arah sebaliknya: pemeriksa
"hadiah menunjuk field hidup" memakai pola `\.max_energy`, padahal
tokenizer-nya menyambung token dengan spasi sehingga `s.max_energy` menjadi
`s . max_energy`. Ketiga hadiah dinyatakan menunjuk field mati padahal
ketiganya dibaca.

### Temuan di luar Tahap 4: alur cerita utama tidak pernah maju

Ditemukan saat menyurvei quest agar Wishes tidak menduplikasinya. `player.py`
membuat `self.quest_controller`, tapi semua pengirimnya mencari
`quest_manager` atau `_check_quest_progress` — dua nama yang **tidak ada** pada
Player. Keduanya dijaga `hasattr`, jadi `check_quests()` diam: tidak ada error,
tidak ada log, `quest_stage` cuma tidak pernah naik.

**Tidak diperbaiki, dan sengaja.** Menyambungkan pengirimnya saja mengubah diam
jadi crash: `QUEST_STAGES` bertipe `list` tapi dibaca `QUEST_STAGES.get(...)`
(terbukti: `AttributeError: 'list' object has no attribute 'get'`), dan tahap
2→3 membaca `s.npc_relations` yang tidak ada — ambangnya 15 sementara
`npc_hearts` berskala 0–10, jadi angkanya harus diputuskan ulang. Memperbaiki
separuhnya mengulang persis kesalahan husbandry. Sekarang tercatat sebagai
RUSAK di `verifikasi.py`, lengkap dengan buktinya.

Karena temuan itu, **`tools/verifikasi.py` sekarang keluar dengan kode 1** — itu
satu cacat nyata yang menunggu keputusan pemilik, bukan alat yang rusak.

**Status:** `uji_wishes.py` 41/41 · `probe_wishes.py` 12/12 ·
`regress.py` 14/14 scene, 0 pemeriksaan gagal.

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

---

## Keputusan pemilik — 2026-10-07

Empat hal yang sengaja ditandai "bukan wewenang alat" akhirnya diputuskan.
Dicatat di sini lengkap dengan **alasan** masing-masing, karena keputusan tanpa
alasan akan dibongkar lagi oleh orang berikutnya yang melihat angkanya aneh.

### 1. Pita G/EN — hanya `ubi_kayu` yang diturunkan

`150G → 84G` (10,77 → **5,69 G/EN**, tepat di langit-langit pita 3,0–5,7).
`cabai` (7,50) dan `ubi_jalar` (6,67) **dibiarkan** sebagai tanaman premium.

Yang membuat singkong timpang bukan hasilnya melainkan **energinya**: 14 hari
singkong = 13 EN untuk 140G bersih, sementara tujuh siklus lobak di petak yang
sama = 49 EN untuk 147G. Per petak-hari praktis sama; per **energi** singkong
menuntut seperempatnya — dan doktrin `economy.py` sendiri berbunyi *"energi,
bukan waktu, adalah sumber daya langka"*. Jadi ia strategi dominan.

### 2. Ternak — `husbandry.py` menang, `economy.animals` pensiun

Dua modul mengurus lima hewan yang sama dengan jawaban berbeda (bebek
telur/1h lawan telur_bebek/2h, domba wol/2h lawan wol/5h, kambing wol/2h lawan
susu_kambing/2h). Dua sistem atas benda yang sama tidak pernah bisa sepakat,
jadi salah satu harus menang. Yang menang husbandry karena ia punya tiga
takaran, jadwal produksi, jalur sakit, **dan** teks keadaan — dan aturan yang
tidak bisa dilihat pemain bukan aturan.

Konsekuensinya dikerjakan sampai habis, bukan separuh:

- **Empat pekerjaan kandang masuk pie menu**: Beri Makan, Beri Minum,
  Bersihkan, Ambil Hasil (`beri_minum` dan `bersihkan` aksi yang benar-benar
  baru). Label tiap aksi menyebut **angka keadaannya** — `air 10%`,
  `kenyang 10% → 70%` — supaya pemain tahu apa yang kurang tanpa menebak.
- **`husbandry.daily_tick` dihidupkan kembali.** Ia pernah dimatikan dengan
  syarat tertulis: keempat aksinya harus terjangkau lebih dulu. Syarat itu kini
  terpenuhi, jadi peluruhannya punya lawan.
- **`economy.tick_animals_daily` tidak lagi dipanggil.** Fungsinya dibiarkan
  ada supaya save lama tetap terbaca.
- **Pakan hantu diperbaiki.** `rumput` dan `dedak` tidak pernah ada sebagai
  barang, dan `rumput` bahkan pilihan pertama untuk lima spesies — jadi
  `feed_item()` melewatinya tiap kali. Selama modulnya dorman cacatnya laten;
  begitu disambungkan ia jadi nyata. `rumput → jerami`, `dedak → pakan`.

### 3. Alur cerita — diperbaiki, ambang hati **7 dari 10**

Tiga cacat sekaligus, dan ketiganya harus beres bersamaan karena memperbaiki
satu saja mengubah diam jadi crash:

| cacat | akibatnya |
|---|---|
| pengirim mencari `quest_manager` / `_check_quest_progress` | dua nama yang tidak ada pada Player, dijaga `hasattr` → alur **diam** |
| `QUEST_STAGES` bertipe `list` tapi dibaca `.get()` | crash di langkah pertama alur |
| `s.npc_relations` tidak ada, ambangnya 15 | `npc_hearts` berskala 0–10, jadi mustahil |

Sekarang: pengirim memakai `quest_controller`, judul tahap dicari lewat
`q['s']`, dan syarat tahap 2→3 jadi `npc_hearts['arya'] >= 7`. Terbukti maju
0 → 1 → 2 → 3 → 4, dan hati 6 memang **ditolak** sementara 7 lolos.

### 4. Benih baru — dipasang, karena penghalangnya sudah tidak ada

16 benih kini ada di toko (26 baris, 3 halaman). Alasan `crops.py` tidak pernah
memasangnya — *"panel toko memilih dengan tombol 1-9"* — sudah **kedaluwarsa**:
`panels.py` punya `ROWS_PER_PAGE = 9`, tombol Q/R, dan `_page_slice` yang
memotong daftar sepanjang apa pun. Jadi ini bukan keputusan desain, melainkan
catatan yang lupa diperbarui.

### Jaring pengamannya ikut tumbuh

`tools/probe_ternak.py` menguji loop perawatan dari **dua sisi**, karena satu
sisi saja tidak membuktikan apa-apa: yang dirawat 14 hari harus selamat *dan*
benar-benar memanen (0 sakit, 40 hasil), yang ditelantarkan 14 hari harus
menanggung (8 dari 8 sakit). Tanpa sisi kedua, sistem tanpa konsekuensi apa pun
akan lulus. Aksinya dijalankan lewat `execute_pie_action` — jalur tombol yang
sama dengan pemain.

### Tiga lulus palsu di alatnya sendiri, semuanya dari sebab yang sama

`tokenize` menyambung token dengan spasi dan mengganti string. Akibatnya:

1. `from ..husbandry import x` menjadi `from . . husbandry import x`, jadi pola
   yang menuntut titik menempel tidak pernah cocok → `daily_tick` terbaca
   "tanpa pemanggil" padahal dipanggil.
2. Alias modul (`import husbandry as hb` → `hb.feed(...)`) tidak dikenali sama
   sekali → perawatan ternak terbaca tidak terjangkau padahal sudah tersambung.
3. `getattr(player, 'quest_controller')` menyembunyikan namanya di dalam
   string → pemeriksaan quest lulus secara **hampa**: tidak menemukan pengirim
   apa pun lalu menyatakan "semua nama ada".

Ketiganya diperbaiki. Pola yang sama sudah muncul di Tahap 2 dan Tahap 4, dan
pelajarannya tidak berubah: **alat yang memberi vonis salah lebih berbahaya
daripada tidak ada alat.**

**Status:** `verifikasi.py` **0 RUSAK, 0 RAPUH, 1 KEPUTUSAN** (cabai dan
ubi_jalar yang sengaja dibiarkan) · `regress.py` 14/14 scene, 0 gagal, termasuk
`rawat_ternak` 13/13 · `uji_wishes.py` 41/41.

---

## Yang TIDAK akan dikejar

**Open world Sims 3.** Lima belas scene terpisah dengan frame rate segini
membuat itu lubang tanpa dasar. Yang dikejar cukup menghilangkan *rasa*
loading: transisi instan, kamera mempertahankan sudut, mendarat di tempat
yang masuk akal. Ini penyimpangan yang disengaja, bukan kesetaraan dengan TS3,
dan tidak akan diakui sebagai kesetaraan.
