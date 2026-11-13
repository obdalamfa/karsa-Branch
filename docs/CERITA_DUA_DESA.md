# Cerita Dua Desa — bahan rancangan dari struktur Harvest Moon: The Tale of Two Towns

Status: rancangan 2026-10-28. Babak 1 "Datang" dibangun 2026-10-28, babak 2
"Menjembatani" dibangun 2026-10-29 (lihat bagian 4). Babak 3 belum. Sumbernya telaah ROM HM 3D: The Tale of Two Towns (USA) milik sendiri, di `C:\Users\Administrator\Downloads\New folder\hm-tott-re\`.

## Batasan pemakaian

- Yang diambil hanya **struktur dan ide**: premis, konflik, alur, peran tokoh, jenis event. Ide dan struktur tidak dilindungi hak cipta, tetapi **teks dialog, nama tokoh, dan nama tempat HM dilindungi**.
- **Jangan menyalin dialog atau nama dari HM ke repo ini.** Repo ini punya remote GitHub, jadi apa pun yang di-push ikut tersebar. Semua teks Lembah Karsa ditulis baru.
- Dump teks HM asli tetap di `hm-tott-re\analysis\text\` hanya sebagai rujukan pribadi.

## 1. Struktur cerita HM (ringkasan dengan kata-kata sendiri)

- **Premis:** seorang pendatang mencari lahan untuk bertani, pingsan di jalan gunung, lalu ditolong para pemimpin dua desa di kaki gunung itu.
- **Dua desa yang bersaing:** satu desa bergaya Barat yang hidup dari **ternak**, satu lagi bergaya Asia yang hidup dari **tanaman**. Kedua pemimpinnya saling sindir dan sama-sama ingin si pendatang menetap di desa mereka.
- **Pilihan awal:** pemain memilih desa tempat tinggal. Pilihan itu menentukan lahan, tetangga dan gaya bertani di awal permainan.
- **Penghubung yang terputus:** awalnya perjalanan antardesa harus memutar lewat gunung. Belakangan sebuah **terowongan** dibuka; sejak itu warga mulai berdagang dan berkunjung ke desa seberang. Terowongan menjadi tanda rukunnya dua desa.
- **Persaingan antardesa:** festival musiman, terutama **lomba masak**, tempat pemain mewakili desanya.
- **Papan permintaan:** warga kedua desa memasang permintaan kecil. Menyelesaikannya menaikkan keakraban dan membuka event.
- **Relasi:** tiap warga punya selera hadiah (termasuk satu favorit utama), event per tingkat hati, lalu pacaran, menikah dan punya anak.
- **Lapisan mitos:** sosok dewi panen dan seorang peramal.

## 2. Usulan adaptasi untuk Lembah Karsa

Lembah Karsa sudah punya alur utama sendiri: **Perjanjian Pertama** dengan penjaga gunung yang harus dipulihkan, catatan Paman Arsa, fragmen prasasti, Gua Sang Hyang dan Bhutakala. Struktur dua desa cocok dijadikan **alur kehidupan desa** yang menyatu dengan alur utama itu, bukan menggantikannya.

| Unsur HM | Versi Lembah Karsa (usulan, nama bebas diganti) |
|---|---|
| Dua desa: ternak vs tanaman | **Desa Karsa** (kebun dan sawah) dan dusun di balik lereng, mis. **Dukuh Lawang** (peternak kerbau dan kambing) |
| Dua pemimpin yang bersaing | Kades Karsa dan sesepuh Dukuh Lawang berselisih soal air dan jalan. Akar perselisihannya: putusnya Perjanjian Pertama |
| Pemain memilih desa | Pemain tetap mewarisi Kebun Paman Arsa, tetapi memilih **bermitra** dengan salah satu pihak untuk bonus awal (bibit unggul atau seekor ternak) |
| Terowongan dibuka | **Jalur lama lewat Gua Sang Hyang** yang tertutup longsor, dibuka bertahap: lantai dungeon + fragmen prasasti. Setelah terbuka, jadwal NPC berubah dan warga kedua desa saling berkunjung |
| Lomba masak antardesa | **Lomba Antar-Desa** musiman: lomba masak, lomba hias kandang, panen terbesar. Kemenangan menaikkan nilai "kerukunan" yang ikut membuka jalur |
| Papan permintaan | **Papan permintaan di balai desa** berisi permintaan harian dari kedua desa |
| Selera hadiah dan event hati | Pakai sistem hearts yang sudah ada, ditambah satu **favorit utama** per NPC sebagai kejutan |
| Dewi panen dan peramal | **Penjaga gunung (Sang Hyang)** dan **juru kunci kuburan tua** |

### Alur besar dalam tiga babak

1. **Datang.** Pemain tiba untuk mengurus kebun Paman Arsa yang hilang. Kedua desa menyambut dengan curiga karena masing-masing mengira pemain berpihak ke desa lain. Quest awal yang sudah ada (bicara dengan Sari, tanam, panen, jual) tetap dipakai.
2. **Menjembatani.** Lewat permintaan warga, lomba antardesa dan fragmen prasasti, pemain menemukan bahwa perselisihan dimulai sejak perjanjian dengan penjaga gunung putus. Jalur gua dibuka sedikit demi sedikit.
3. **Memulihkan.** Pemain meredakan atau mengalahkan Bhutakala di dasar gua dan memulihkan Perjanjian Pertama. Penutupnya **Sedekah Bumi** yang digelar bersama oleh kedua desa.

## 3. Tempat implementasi di kode

- `game/data.py`:
  - `HUMAN_NPCS`: warga dukuh kedua, dialog `hearts_N` baru, favorit utama.
  - `QUEST_STAGES`: quest per babak.
  - `SEASONAL_EVENTS`: lomba antardesa dan Sedekah Bumi.
  - `LORE_ITEMS`: fragmen prasasti tambahan tentang perselisihan dua desa.
  - `SCHEDULES`: jadwal yang berubah setelah jalur gua terbuka.
- Scene dusun kedua mengikuti pola file di `game/scenes/`.

## 4. Babak 2 "Menjembatani" — yang dibangun (2026-10-29)

Pemain menjadi juru titip di antara dua desa. Nilai **Kerukunan Karsa-Lawang**
(`state.kerukunan`, 0..100) naik dari titipan dan Lomba Antar-Desa. Ambangnya
membuka cerita Watu Tikar, yaitu batu sumpah dua desa yang terkubur longsor.
Puncaknya gotong royong yang membuka jalan lama lewat Gua Sang Hyang.

| Tahap | Judul | Syarat maju |
|---|---|---|
| 3 | Juru Titip | satu titipan selesai di papan Balai Desa **dan** satu di papan Dukuh Lawang |
| 4 | Akar Perselisihan | Kerukunan >= 25, lalu "Tanya Jalan Lama" ke Mbah Rukmi |
| 5 | Satu Tikar | Kerukunan >= 50, lalu "Ajak Menggali Bersama" ke Kades Hardjo |
| 6 | Gotong Royong | pagi berikutnya, 06.00-18.00: kedua sesepuh menunggu di longsor Lawang |
| 7 | babak 2 selesai | jalan lama terbuka, catatan Watu Tikar, Kerukunan +20 |

- **Papan Titipan** (ubin baru `PPN`): town (20,8) di alun-alun, di depan
  gerbang Balai Desa tempat Kades Hardjo berjaga; lawang (3,11) di antara
  gapura dan lapangan. Setiap pagi muncul 2 titipan per
  papan, diundi deterministik dari tanggal (`game/dua_desa.py`), jadi tidak
  ada daftar yang disimpan. Warga Karsa menitip hasil ternak dan olahan,
  warga Lawang menitip sayur Karsa. Titipan tanaman hanya muncul di musimnya.
  Imbalannya sekitar 1,3x harga Warung, +0,5 hati untuk peminta, dan
  Kerukunan +5.
- **Lomba Antar-Desa** (Panas hari 21, 09.00-17.00, lapangan Lawang). Kades
  Hardjo dan Mbah Rukmi menjadi juri; lawan pemain adalah juru masak desa
  seberang (Sekar atau Mbok Jum). Ada dua kategori, masing-masing sekali per
  tahun:
  - Lomba Masak: satu olahan.
  - Panen Terbesar: satu tumpukan hasil kebun, maksimal 10 butir.

  Nilai lawan tetap sepanjang tahun dan naik tiap tahun. Ikut memberi
  Kerukunan +5; menang memberi +10 lagi, emas, dan +1 hati untuk kedua juri.
  Pengumuman muncul sehari sebelumnya dan pada pagi hari H. Pengumuman ini
  mengisi `_pending_seasonal_event`, yang sebelumnya tidak pernah diisi, dan
  juga tampil sesudah tidur paksa jam 23.
- **Jalan lama**: `Scene` punya kait opsional `sesuaikan(scene, state)` yang
  dipanggil `World3D.load_scene()` sebelum ubin dibangun. Kait ini bekerja dua
  arah, jadi memuat save lama tidak mewarisi jalan yang sudah terbuka.
  - Lawang: batu (4..5,2) menjadi jalan, tebing (4..5,1) menjadi mulut gua
    berportal, dan pohon tumbang diganti lentera.
  - Gua Sang Hyang: dinding timur (14,5/6) terbuka ke Lawang.
- **Jadwal khusus** (`data.JADWAL_*`, dipilih `dua_desa.jadwal_npc`), dengan
  prioritas hari Lomba > gotong royong > jalan terbuka > `SCHEDULES`. Sesudah
  jalan terbuka:
  - Sekar mengantar susu ke Desa pada pagi hari.
  - Mbah Rukmi dan Kades Hardjo duduk bersama di balai pukul 13.00-16.00.
  - Maya melukis di Lawang.
- Yang berbeda dari rancangan:
  - Fragmen prasasti di lantai dungeon belum dipakai. Penggantinya lore baru
    `watu_tikar` yang ditemukan saat gotong royong.
  - "Hias kandang" belum menjadi kategori yang bisa diikuti pemain.

Kait babak 3 ada di teks Watu Tikar: janji yang putus hanya bisa disambung "di
dasar gua, di hadapan sang penjaga". Setelah itu Bhutakala dan Sedekah Bumi
bersama.
