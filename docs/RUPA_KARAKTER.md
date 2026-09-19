# Rupa karakter — Lembah Karsa 3D

Catatan pekerjaan yang dimulai dari satu kalimat: *"posisi kepala sepertinya
salah, dan bentuk atau ekspresinya creepy."*

Ternyata bukan satu sebab, melainkan **lima**, dan tiga di antaranya tidak ada
hubungannya dengan model karakternya sama sekali. Dokumen ini mencatat
angkanya, karena separuh dari yang saya kira benar ternyata salah begitu
diukur.

---

## 1. Cara melihatnya

Semua yang di bawah ini baru terlihat setelah **memotret dari dekat**. Seluruh
filmstrip sebelumnya diambil dari jarak main, dan pada jarak itu wajah cuma
beberapa piksel — tidak ada satu pun cacat di bawah yang terbaca.

Probe potret: `scratchpad/potret.py`. Tiga hal yang membuatnya bisa dipercaya,
dan ketiganya baru benar setelah gagal dulu:

- **Pasang kamera SESUDAH langkah terakhir.** Pengendali kamera game menulis
  ulang posisinya tiap tick, jadi kamera yang dipasang sebelum `step()` selalu
  direbut kembali. Gambar pertama saya semuanya dari jarak main tanpa saya
  sadari.
- **Kunci arah hadap.** Muka ada di sisi +Z lokal. Pemain berdiri pada
  `rotation_y = 90`, jadi kamera di +Z memotret pipinya. Bidikan "depan"
  pertama saya adalah sisi kepala.
- **Bidik pusat kepala yang sebenarnya.** Pusat kepala pemain ada di
  `GROUND_H + 1,89 = 2,09`. Bidikan pertama saya di 1,55 memotong ubun-ubunnya
  — dan itu bukan kepala yang salah, itu kamera yang salah.

Untuk apa pun yang ketinggiannya tidak diketahui, **tempel kubus penanda
berwarna** dan lihat mana yang mendarat. Saya dua kali menebak ketinggian dari
foto dan dua kali meleset; penanda tidak pernah meleset.

---

## 2. Kepala pemain melayang

Diukur dari geometrinya, bukan dari kesan:

| bagian | rentang tinggi | lebar |
|---|---|---|
| dada | 1,27 – 1,57 | 0,52 |
| leher | 1,57 – 1,67 | **0,14** |
| kepala | 1,665 – 2,115 | 0,35 |

Secara geometri leher dan kepala BERSENTUHAN — tidak ada celah. Tapi leher
selebar 0,14 yang berdiri di antara dada 0,52 dan kepala 0,35 terbaca sebagai
kepala di atas **tangkai**.

Perbaikannya bukan menutup celah yang tidak ada, tapi menghilangkan lehernya:
leher dilebarkan ke 0,21 dan sengaja **tumpang tindih** dengan keduanya
(1,555–1,675, melewati puncak dada 1,57 dan dasar kepala 1,665), lalu kerah
baju menutup sambungannya. Karakter chibi game pertanian Jepang tidak punya
leher yang terlihat sama sekali.

---

## 3. Ekspresi creepy: wajahnya memang tidak ada

Kepala pemain adalah kotak kulit polos. Tanpa mata, tanpa mulut, tanpa rambut.

Dan kode memasang **"surreal floating geometric halo"** — cincin magenta dan
kubus cyan melayang di atas kepala **setiap** pemain. Itu perancah uji yang
tertinggal, dan ia yang terlihat sebagai berlian cyan di semua tangkapan lama.

### Bahasa rupa yang diikuti

Dari game kehidupan Jepang (Story of Seasons, Rune Factory, Harvest Moon).
Ditulis sekali di `game/wajah.py` dan dipakai pemain DAN NPC, dengan ukuran
sebagai **pecahan dari setengah-lebar kepala** — jadi satu resep pas di kepala
pemain (0,175) maupun kepala NPC (0,366) tanpa dua tabel angka yang harus
dijaga sinkron. Urutannya penting karena tiap langkah menyelesaikan masalah
yang berbeda:

1. **Rambut dulu.** Poni yang menjorok di atas dahi adalah satu hal yang paling
   cepat mengubah kotak jadi kepala, dan ia sekaligus memberi kepala **arah
   depan** yang terbaca dari jauh. Tanpa rambut, kepala dari depan dan dari
   belakang sama saja.
2. **Mata adalah fiturnya**, bukan salah satu fitur. Besar, gelap, bentuk
   sederhana, duduk sedikit **di bawah** garis tengah wajah — mata yang
   diletakkan tepat di tengah membuat wajah terbaca dewasa dan dingin.
   Besarnya sekitar **sepertiga** tinggi wajah yang terlihat. Percobaan pertama
   memakai hampir setengahnya (0,074 × 0,100 pada kepala 0,35 × 0,45) dan
   hasilnya terbaca sebagai **kacamata hitam atau rongga kosong**. Yang membuat
   mata terbaca hidup bukan besarnya, tapi RUANG KOSONG di sekelilingnya.
3. **Kilau.** Mata anime tidak pernah hitam rata. Satu titik putih kecil di
   sudut yang **sama** pada kedua mata (cahaya datang dari satu arah) adalah
   beda antara "melihat" dan "melotot". Kilau simetris cermin terbaca sebagai
   dua bola mata, bukan wajah. Kilau sebesar seperempat mata membuatnya
   seperti jendela.
4. **Mulut sekecil mungkin, warnanya diredam.** Pada bidang sekecil ini, merah
   menyala terbaca sebagai luka.
5. **Rona pipi.** Murah, dan ia yang membuat kulit terbaca hidup.

Alis sempat ada lalu dibuang: poni yang menjorok menutupi dahi sampai ke garis
mata, jadi alis di bawahnya tidak pernah terlihat sekali pun.

`chibi_head_mesh()` — rounded box dengan sudut dibevel halus — sudah ada di
`meshes.py` sejak lama dan **tidak pernah dipanggil sekali pun**; kepalanya
memakai kubus tajam. Begitu juga `chibi_torso_mesh()`. Keduanya sekarang
dipakai.

---

## 4. NPC: manekin putih menyala yang menjulang

Ini yang paling merusak, dan ia bukan pemainnya.

Jalur Vitaboy gagal di lingkungan ini (asetnya tidak ada di repo), jadi SEMUA
NPC manusia jatuh ke `humanoid.obj`. Diukur apa adanya:

```
Color(1,0 1,0 1,0 1,0)   putih murni, tanpa tekstur, tanpa material
tinggi 3,42 unit         pemain cuma ~2,35 — NPC 1,45x lebih tinggi
anak: ['text']           cuma label nama; tanpa wajah, rambut, atau baju
```

Dan `resolve_outfit()` mengembalikan nama aset Vitaboy yang tidak pernah
dipakai jalur fallback, jadi warna baju yang sudah ditentukan per-NPC **tidak
pernah sampai ke layar**. Sama halnya `HAIR_PRESETS`: pemain bisa memilih warna
rambut di chargen, `state.char_hair` tersimpan, dan rig voxel tidak pernah
memakainya karena tidak ada geometri rambut sama sekali.

### Yang diperbaiki, urut menurut besar kerusakannya

**Tinggi.** Diskalakan ke tinggi pemain. Menjulang membuat tiap NPC terbaca
mengancam sebelum ekspresi apa pun sempat terbaca.

**Warna, dan arah yang benar.** Percobaan pertama mewarnai mesh KULIT — dan
karena `humanoid.obj` satu potong, tidak ada cara mewarnai lengan berbeda dari
badan: hasilnya dua lengan telanjang merah muda menyala di sisi badan. Dibalik:
mesh diwarnai **baju**, jadi lengannya otomatis lengan baju panjang, dan yang
perlu kulit tinggal kepala — yang memang ditumpuk terpisah.

**Wajah dan rambut**, resep yang sama dengan pemain.

Ketinggian baju, kaki dan sepatu semuanya **diukur dengan kubus penanda** di
0,15 / 0,55 / 1,00 / 1,45 / 1,90 pada mesh yang belum diskalakan:
rok/pinggul 1,15–1,45, kolom kaki 0,20–1,15, kaki di bawah 0,20. Pusat
kepala 2,80 (penanda hijau 2,70 dan biru 3,00 mengapitnya) — tebakan pertama
dari profil verteks memberi 3,09, dan seluruh rambut serta wajahnya melayang
di ATAS kepala.

> **Profil verteks berbohong dua kali.** Pertama karena sumbu atas mesh ini
> `y`, bukan `z`, dan saya membin pada sumbu yang salah. Kedua karena mesh ini
> berpoli rendah: banyak pita ketinggian yang kosong, dan lebar sebuah pita
> hanya dihitung dari verteks yang kebetulan ada di dalamnya. Penanda visual
> tidak punya kedua masalah itu.

### Kepala bola, dan kenapa akhirnya bukan bola

Kepala manekin awalnya ditutup **bola** kulit. Itu menuntut dua hal khusus:
resep rambut versi bola (batok kotak duduk seperti papan di atas bola, dan dua
tuft kotak di kiri-kanan membentuk **pigura gelap persegi** mengelilingi
wajah), dan perhitungan kedalaman **per fitur** dari persamaan bola.

Yang terakhir itu bukan kosmetik. `bangun_wajah()` menempel semua fitur pada
satu **bidang datar**; di atas bola, fitur yang jauh dari tengah wajah melayang
lepas dari permukaan — rona pipi di `x = 0,71R` keluar dari siluet kepala
sebagai **dua batang merah muda**. Perbaikannya `z = √(R² − x² − y²)` per fitur.

Lalu ternyata bolanya sendiri yang salah: bola Ursina bersegi rendah, dan
cel-shader di sini memotong terang dan gelap pada **ambang keras**, jadi batas
bayangannya mengikuti segi-segi bola satu per satu dan membentuk **tangga** di
pipi. Kepala NPC dipindah ke `chibi_head_mesh()` — bentuk yang sama dengan
pemain — dan seluruh jalur khusus-bola di atas jadi tidak punya pemakai lalu
dibuang.

**Perbaikan yang menghapus kodenya sendiri lebih berharga daripada perbaikan
yang menambahnya.**

---

## 5. Dan wajahnya memang bercahaya — itu dua shader, bukan modelnya

Sesudah semua di atas, wajah masih terbaca menyala dari dekat. Dua sebab
terpisah, dan yang kedua **membatalkan perbaikan yang pertama**.

### 5.1 Pencahayaan tidak pernah dibatasi

`game/smooth_shader.py`:

```glsl
vec3 lit = base.rgb * (sm_ambient + sm_sun_color * diff) * ao;
```

Tidak ada pembatas. Dengan `ambient (0,45 0,46 0,50)` dan
`sun (1,05 1,02 0,92)`, penggandanya **1,50** di pita tersinari:

```
kulit rgb(230,190,148) = (0,902 0,745 0,580)
        x 1,50         = (1,353 1,103 0,824)
        dipotong       -> rgb(255, 255, 210)
```

Kanal yang lewat 1,0 dipotong **satu per satu** oleh perangkat keras, jadi
warna terang tidak menjadi lebih terang — ia **kehilangan warnanya**. Cokelat
hangat berubah kuning-putih menyala.

Perbaikannya bukan menjepit per kanal, tapi **menskalakan bersama-sama**: kanal
tertinggi didudukkan di 1,0 dan sisanya ikut turun dengan rasio yang sama, jadi
ronanya utuh dan yang hilang cuma kelebihan terang yang memang tidak bisa
ditampilkan.

### 5.2 Bloom mengembalikannya

Saya sempat menyebut sisa mekar putihnya "tampak bloom pasca-proses" — itu
tebakan, dan tebakan sudah dua kali salah. Diperiksa: memang ada,
`vhs_bloom_shader` dipasang ke kamera di `app.py:203`.

```glsl
LUM_THRESHOLD = 0,65     kulit tersinari luminans 0,85 -> WAJAH IKUT MEKAR
bloom / count            dibagi seluruh 49 sampel, bukan yang lolos ambang
base + bloom * 0,45      menambah cahaya DI ATAS warna, lalu terpotong lagi
```

Jadi bloom mengembalikan **persis** pemotongan putih yang baru ditutup di 5.1:
kulit hangat dijadikan putih oleh mekarnya sendiri. Dua perbaikan saling
membatalkan, dan itu tidak akan ketahuan tanpa membaca angkanya.

Tiga perbaikan: ambang **0,65 → 0,80** (bloom seharusnya menangkap sumber
cahaya dan sorotan, bukan kulit orang); saklar keras `if (lum > ambang)`
diganti **lutut lunak** kuadrat (sebelumnya satu piksel yang kebetulan melewati
ambang menyumbang sebanyak piksel yang jauh lebih terang); dan penjagaan rona
yang sama seperti di 5.1.

---

## 6. Yang masih terbuka

- Kaki manekin NPC satu kolom tanpa pemisah; ditutup celana dan sepatu, tapi
  tidak akan pernah berjalan dengan dua kaki terpisah tanpa mengganti meshnya.
- Rig Vitaboy tetap ranjau — lihat `ANIMASI_PERAWATAN.md` §10. Kalau asetnya
  suatu saat di-bake, seluruh rupa di dokumen ini tidak terpakai dan yang
  dipakai adalah avatar TSO.
- Ekspresi masih hampir satu. **Kedipan dan mata lelah sudah ada** (§7);
  senang dan sakit belum. Mata dan mulut sudah entity terpisah, jadi
  menambahnya murah.
- Ternak sekarang bermata, berkedip, menggerakkan telinga dan mengibaskan
  ekor (§8, §9). Yang masih statis cuma mulutnya.

---

## 7. Wajah yang tidak pernah berkedip

Ditambahkan setelah semua di atas, karena baru terlihat begitu karakter punya
mata: **tidak ada satu pun dari mereka yang berkedip.** Itu tanda uncanny yang
paling tua dan paling murah dihilangkan, dan mata sudah entity terpisah sejak
awal, jadi kedipan cuma soal menyekakan tingginya.

Tiga hal yang membuat kedipan terbaca sebagai kedipan, bukan kedutan:

- **Cepat.** Mata manusia menutup-membuka dalam 100–150 ms. Terukur di sini
  100 ms (60 menutup + 25 tertutup + 75 membuka, membuka sengaja lebih lambat
  daripada menutup). Lebih lambat dari itu terbaca sebagai mengantuk.
- **Tidak berirama.** Jarak antar-kedip 2,4–5,8 detik.
- **Kilau ikut hilang.** Kilau yang tetap melayang saat mata tertutup terbaca
  sebagai dua titik putih di atas kelopak.

Ditambah: `set_lelah()` menyipitkan mata ke 0,55 tinggi penuh saat energi
habis — memberi tahu pemain keadaannya tanpa satu pun angka di HUD.

### Uji itu menangkap cacat saya sendiri

Percobaan pertama memakai `sin(self._t * 12,9898)` sebagai derau jarak — dan
`self._t` di-nol-kan **tepat sebelum** fungsi itu dipanggil, jadi deraunya
selalu dievaluasi di `sin(0) = 0` dan jaraknya selalu `JEDA_MIN`. Terukur:

```
12 kedipan dalam 30 detik, semuanya berjarak 2,40 detik
simpangan baku 0,00 detik
```

Nol adalah metronom, dan metronom adalah persis cacat yang tabel ambang
proyek ini sendiri sebut mesin (`irama_sd_ms > 8` pada aksi berulang). Umpan
deraunya diganti ke **nomor kedipan**, yang memang berubah tiap kali:

```
8 kedipan dalam 30 detik  (16/menit — rentang normal manusia)
jarak 2,70 / 3,43 / 5,07 / 3,37 / 2,83 / 5,03 / 3,83 detik
simpangan baku 0,89 detik
```

Dan fasenya dari `sum(ord(id))`, **bukan** `hash()` — Python mengacak hash
string tiap proses, jebakan yang sudah dua kali memakan proyek ini. Tanpa fase
per-karakter sekampung akan berkedip serempak seperti pasukan. Diperiksa: dua
proses terpisah memberi deret jarak yang sama persis, dan empat warga memberi
fase awal 4,033 / 5,200 / 1,900 / 5,267.

---

## 8. Ternak yang tidak punya mata sama sekali

Ditemukan tepat setelah §7 selesai, dan ini cacat yang **sama persis** dengan
yang baru ditutup di manusia — pada hewan yang jadi pokok seluruh pekerjaan
perawatan ini. Sembilan spesies di `animal_models.py`, semuanya lengkap dengan
badan, moncong, tanduk, telinga, ambing, ekor dan kuku:

```
$ grep -n "mata" game/animal_models.py
47:    'hidung': color.rgb(46,40,40),   # L 16 — hidung/mata
```

Satu komentar warna. Tidak satu baris geometri. Padahal pemain berdiri **60 cm
dari kepala sapi selama 1,9 detik** tiap kali memerah.

### Empat keputusan, tiga di antaranya datang dari memotret hasilnya

**1. Letak menentukan spesies.** Mangsa (ayam, bebek, kelinci, kambing, domba,
sapi, kuda) bermata di **sisi** kepala — dua mata yang tidak pernah terlihat
bersamaan. Pemangsa (kucing, rubah) bermata di **depan**, berpasangan. Satu
resep melayani keduanya lewat `arah=`.

**2. Bulat — dan ini satu-satunya bentuk bulat di seluruh proyek.** Ronde
pertama memakai `creature_body_mesh()` seperti bagian lain, dan bentuk itu
eksponen 0,10: hampir kubus. Terpotret dari depan, mata kucing keluar sebagai
dua **persegi** putih bertambal kotak hitam — terbaca sebagai kacamata las.
`mata_mesh()` (eksponen 1,0, elipsoid sejati) ada khusus untuk ini.

**3. Pelipit sklera setipis benang pada ternak, lebar pada pemangsa.** Ronde
pertama menaruh pupil jauh lebih menonjol daripada sklera dan dari sudut
tiga-perempat pupil menutupi sklera sepenuhnya: mata sapi terbaca sebagai
**lubang** gelap. Ronde kedua membalikkannya terlalu jauh — mata sapi
terpotret sebagai **bola pingpong yang ditempel di pipi**. Ternak bermata sisi
hampir seluruhnya iris gelap, jadi pupilnya 0,76 d; pemangsa memang
berputih-mata lebar, jadi 0,55 d.

**4. Ukuran mengikuti bahasa game kehidupan Jepang, bukan anatomi.** Mata sapi
asli berdiameter ~3,5 cm — persis di bawah ambang ~3 cm yang docstring
`animal_models.py` sendiri sebut tidak pernah sampai ke layar. Mata sapi di
sini 12 cm, ~32% tinggi kepala. Seperti sapi Story of Seasons, bukan sapi asli.

### Aritmetika yang salah dan potret yang menangkapnya

Offset pupil ronde kedua ditulis `(0,5 - pupil*0,5) * 0,9`. Untuk pupil 0,76
itu `(0,5 - 0,38) * 0,9 = 0,108`, jadi titik terluar pupil ada di
`0,108 + 0,38 = 0,488 d` — **di dalam** bola sklera berjari 0,5 d. Terpotret:
mata domba keluar sebagai bola putih polos tanpa pupil sama sekali. Rumusnya
sekarang `0,5 - 0,40 * pupil`, dan hasilnya diperiksa dengan hitungan, bukan
dengan mata:

```
pupil 0,76 -> pusat 0,196, terluar 0,576 (sklera 0,500), cakram terlihat 68%
pupil 0,55 -> pusat 0,280, terluar 0,555 (sklera 0,500), cakram terlihat 43%
```

### Kenapa sklera dibiarkan melewati batas terang 205

`animal_models.py` memasang batas atas nilai ~205 karena cel shader menjepit
warna di atas itu jadi putih rata dan **bentuk di dalamnya hilang**. Sklera
(L 88) sengaja melanggarnya: ia tidak punya bentuk di dalamnya — pupilnya
entity terpisah di depannya — jadi "putih rata" justru yang dicari. Tanpa
sklera, mata gelap di atas kepala gelap (bebek L 23, muka domba L 23, kambing
L 36, kuda L 35) hilang sama sekali.

### Mata dikaitkan ke kepala, bukan ke akar rig

Kepala kuda miring 26° dan dua kali lebih panjang daripada lebar. Mata yang
dipasang di koordinat akar akan menggantung lepas dari pipinya dan lonjong dua
kali panjangnya. Jadi `_mata()` mengait ke entity kepala lalu **membagi** tiap
ukuran dengan skala kepala.

### Kedipan ikut gratis, dan malam memejamkannya

`build_animal()` mengumpulkan mata jadi satu `Wajah` — pengendali yang sama
persis dengan yang dipakai pemain dan warga — di `parent._wajah`. Loop entitas
sudah men-tick `actor._wajah` untuk setiap actor, jadi tidak ada jalur kode
kedua. Jedanya diperketat ke 1,8–4,6 detik (hewan berkedip lebih rapat
daripada manusia) pada instance-nya, bukan pada kelasnya, supaya wajah manusia
tidak ikut berubah.

Yang **tidak** bisa datang dari loop itu: hewan tidur dibaca dari jam dunia,
bukan dari jadwal actor seperti warga. Jadi `FarmAnimal.update_ai()` memanggil
`set_tidur(self.state.is_night())` sendiri. Tanpa satu baris itu, sapi tidur
membelalak semalaman.

Terukur, 60 detik siang di kandang farm:

```
hewan            kedip  jeda rata2   sd       kedipan pertama
  ayam_kuning       19    3,16 s    0,88 s        1,20 s
  domba_woolly      18    3,32 s    0,81 s        1,40 s
  kambing_jenggot   17    3,38 s    0,77 s        2,20 s
  kucing_oren       18    3,30 s    0,93 s        2,83 s
  kuda_pegasus      19    3,13 s    0,74 s        0,03 s
  sapi_betsy        19    3,12 s    0,81 s        3,83 s
```

Simpangan baku terkecil 0,74 detik — bukan nol, jadi bukan metronom — dan
enam kedipan pertama di enam waktu berbeda, jadi kawanan tidak berkedip
serempak. Pukul 20:00 keenamnya turun ke skala 0,02 (6–7% tinggi penuh):
terpejam, tapi tetap segaris tipis, bukan hilang.

### Dua "cacat" yang ternyata cacat probe-nya

Pengukur kedipan versi pertama melaporkan **kuda tidak pernah berkedip** (0
dari 60 detik) dan **mata 5,000 kali terbuka saat malam**. Keduanya palsu:

- Tinggi acuan tiap mata diambil sesudah `step(40)`, dan kuda kebetulan sedang
  **di tengah kedipan** saat itu — acuannya terekam 0,0575 dan bukan 0,2875,
  jadi rasionya tidak pernah turun ke ambang 0,35 dan puncaknya jadi 5,0.
  Tabel di atas menunjukkan kenapa justru kuda yang kena: kedipan pertamanya
  jatuh di detik 0,03, satu-satunya yang mendarat tepat di saat pengintipan.
- Uji malamnya memasang jam ke 23:00, yaitu `FORCE_SLEEP_HOUR`. Satu `step()`
  memicu tidur paksa dan jam melompat ke 06:01, jadi yang terbaca `_tidur`
  siang hari — benar, hanya bukan yang sedang diuji.

Diperiksa ulang dengan acuan dari `Wajah._tinggi0` (nilai saat dibangun, bukan
saat diintip) dan jam 20:00: keenam ekor berkedip 17–19 kali, dan keenamnya
terpejam saat malam.

### Catatan probe: enam ronde sebelum satu gambar bisa dipercaya

Lima percobaan berturut-turut memindahkan `camera.position` ke depan kepala
hewan, dan semuanya gagal dengan cara yang **sama dan menyesatkan**: kubus
penanda `unlit=True` muncul persis di tengah frame pada jarak yang terukur
benar (5 cm pada 1,04 m = 7,6% lebar frame, cocok sampai desimal dengan fov
35), dan **hewannya tidak muncul sama sekali**. Dua sebab terpisah:

- Rig yang dipasang sendiri lewat `Entity(...)` + `build_animal(...)` tidak
  pernah terlihat di dalam scene — bagian hewan memakai `apply_smooth`, dan
  shader itu butuh input per-frame yang hanya dipasang app untuk actor yang
  dibuat app sendiri.
- `app.update()` menulis ulang kamera dari `_camera_offset()` tiap frame, jadi
  yang terpotret selalu frame hasil tulis-ulangnya.

Yang akhirnya dipakai: **actor `ANIMAL_NPCS` milik game**, difoto lewat kendali
kamera game sendiri (`camera_yaw` / `camera_pitch` / `camera_dist` — kendali
yang sama yang dipakai pemain lewat klik-kanan), dengan titik kepala
**diproyeksikan** ke koordinat layar lewat lensa Panda3D untuk menentukan
potongan. Tidak ada tebakan framing yang tersisa, dan sudut yang terlihat
benar-benar sudut yang bisa dilihat pemain.

Panggung telanjang (Ursina kosong + lampu sendiri) sempat dicoba dan **bohong
soal warna**: pupil L 13 tampil merah muda pucat, karena cel shader mengambil
cahayanya dari app, bukan dari node lampu Panda. Panggung itu hanya dipakai
untuk menilai bentuk, tidak pernah untuk menilai warna.

---

## 9. Telinga dan ekor yang tidak pernah bergerak

Sisa terakhir daftar §6, dan yang paling menyambung ke brief: seluruh proyek
ini tentang **interaksi** perawatan ternak, dan hewan yang disikat selama 2,7
detik tanpa menggerakkan telinga maupun ekor tidak memberi satu pun tanda
bahwa ia merasakan sikatnya. Badannya memang sudah condong ke arah sikat
(`FarmAnimal._tick_sikat`), tapi itu satu gerakan untuk satu benda utuh —
bukan reaksi.

### Simpul putar tanpa satu pun sin/cos yang saya tulis sendiri

Telinga dan ekor dibangun sebagai kotak lepas yang dikaitkan langsung ke akar
rig, jadi tidak ada yang bisa diputar: memutar kotak ekor memutarnya di
TENGAHNYA, bukan di pangkalnya. Tiap bagian itu sekarang dibungkus satu simpul
putar di pangkalnya.

Letak pangkal tidak dihitung tangan. `_sendi()` membuat part-nya DULU di
koordinat akar — angka yang sama persis seperti sebelumnya, jadi masih bisa
dibandingkan dengan gambar — lalu meminta `getRelativePoint()` milik mesin
menghitung di mana ujungnya mendarat sesudah skala dan rotasi. Aritmetika
tangan seperti itu sudah empat kali salah di proyek ini dan tiap kali baru
ketahuan dari gambar.

Simpulnya geseran murni, jadi memindahkan anak ke bawahnya cuma soal mengurangi
posisi; rotasi tiap part tidak berubah. Itu sebabnya reparent di sini **tidak**
memakai `wrtReparentTo` — yang justru berbahaya karena melewati pembukuan
`_parent`/`_children` Ursina dan membuat `destroy()` serta iterasi anak bohong.

Diperiksa: kotak batas SETIAP part sembilan spesies, sebelum dan sesudah.

```
spesies   part  selisih maks (m)
  ayam       18   0.000000    kambing    25   0.000000
  bebek      16   0.000000    kelinci    21   0.000000
  domba      19   0.000000    kucing     24   0.000000
  kuda       24   0.000010    rubah      22   0.000000
  sapi       31   0.000000
```

Sepuluh mikrometer pada kuda, itu pun pembulatan float. Tampilan diamnya sama.

### Tiga hal yang membedakan gerak hidup dari motor, semuanya angka

**Ekor tidak boleh berayun satu sinus.** Satu sinus murni punya jarak
antar-lintasan-nol yang sama persis tiap kali — simpangan baku nol, cacat
"metronom" yang tabel ambang proyek ini sendiri sebut mesin dan yang sudah
sekali memakan kedipan wajah (§7). Ayunannya dua sinus berperiode tidak
sepadan (0,61x, dekat 1/rasio emas): terukur 25 ayunan dalam 120 detik dengan
sd 0,415 detik.

**Telinga berkedut, bukan berayun.** Telinga yang berayun terus terbaca sebagai
kipas. Yang benar: diam lama, lalu satu sentakan cepat — 70 ms keluar, 190 ms
pulang, dengan sedikit lewat saat pulang supaya tidak berhenti seperti tuas.
Terukur 30 kedutan per 180 detik, jeda rata-rata 5,85 detik, sd 1,62 detik,
dan 0 dari 30 bersamaan dengan telinga sebelahnya.

**Menyentuh harus terbaca.** Tiap sapuan memicu sentakan telinga (puncak 24,8°
pada 67 ms) dan melebarkan ayunan ekor. Di uji unit dengan sapuan terus-menerus
10,5° → 34,0° (3,2x); di dalam game, dengan `_sikat_kuat` yang meluruh di
antara sapuan seperti sungguhan, 10,5° → 24,6° (2,3x). Amplitudonya menyusul
pelan, bukan melompat: lompatan frame pertama 1,81°.

Malam hari ekor menyempit ke 2,4° dan telinga berhenti berkedut sama sekali.

### Gerbangnya sendiri diuji dengan merusak kode

`tools/uji_gerak_ternak.py` menjalankan 12 pemeriksaan; dengan `--rig` ia ikut
membangun rig sungguhan dan memeriksa 22 poros. Alat ukur yang belum pernah
gagal biasanya belum pernah diperiksa, jadi empat cacat dipasang dengan sengaja
lalu gerbangnya dijalankan lagi:

```
ekor jadi sinus tunggal (metronom)      TERTANGKAP  sd 0.000 s
sentuhan tidak melebarkan ekor          TERTANGKAP  10.5 -> 11.0 derajat (1.0x)
dua telinga benar-benar diserempakkan   TERTANGKAP  30 dari 30 bareng
poros ekor sapi dipindah ke ujung       TERTANGKAP  pangkal 0.118 m vs ujung 0.000 m
```

Ronde pertama uji mutasi ini **bohong dua kali**, dan keduanya layak dicatat:

- Dua mutasi berturut-turut kebetulan menghasilkan berkas berukuran sama persis
  dalam detik yang sama, jadi Python memakai `.pyc` basi dari mutasi
  sebelumnya. Yang dilaporkan gagal adalah cacat yang sudah dikembalikan.
- Mutasi "dua telinga diberi benih yang sama" lolos, dan itu terbaca seperti
  gerbang bocor. Bukan: kedua telinga dipisahkan **tiga** mekanisme (jam awal,
  nomor awal, benih), jadi mencabut satu saja memang tidak menyerempakkannya.
  Mutasi yang mencabut ketiganya langsung tertangkap.

### Dan pemeriksaan poros versi pertama memang bocor

Versi pertama bertanya "apakah poros lebih dekat ke pusat badan daripada titik
terjauh part". Uji mutasi membuktikannya tidak cukup: memindahkan poros ekor
sapi ke ujung bawah tetap lolos, karena ekor yang menggantung ke belakang punya
dua ujung yang berjarak nyaris sama dari pusat badan — 0,800 m lawan 0,852 m.

Rumusan sekarang memakai definisi yang memang dimaksud: **pangkal adalah ujung
yang menempel pada bagian lain hewannya.** Pangkal ekor menyentuh pantat; ujung
ekor tidak menyentuh apa pun. Dua syarat, keduanya perlu — pangkal memang
menempel (<= 3,5 cm), dan pangkal tidak lebih jauh daripada ujungnya.

Rumusan perantara sempat memakai margin tunggal 2 cm dan itu pun salah: pada
bagian yang lebih pendek daripada marginnya sendiri, pangkal yang menempel
SEMPURNA ikut dijatuhkan — telinga kuda gagal dengan pangkal 0,000 m lawan
ujung 0,015 m. Ekor buntut domba menempel di kedua ujungnya karena terbenam di
bulu; itu memang tidak bisa dibedakan, dan syarat sekarang meloloskannya tanpa
berpura-pura tahu.
