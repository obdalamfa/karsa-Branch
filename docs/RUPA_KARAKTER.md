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
- Ekspresi masih satu: tidak ada perubahan wajah saat senang, lelah, atau
  sakit. Mata dan mulut sudah entity terpisah, jadi menggantinya murah.
