# Animasi Perawatan — apa yang membuat gerakan terbaca hidup

Dokumen ini menjelaskan `game/care_anim.py` dan alat penilainya. Ditulis
sesudah pekerjaannya selesai, dari catatan pengukuran yang sebenarnya — bukan
dari rencana yang dibayangkan sebelum mulai. Yang paling berguna di sini bukan
daftar fiturnya, tapi **daftar kesalahan yang benar-benar terjadi** dan cara
masing-masing ketahuan.

---

## 1. Titik nol

Sebelum apa pun dibangun, dua aksi ternak yang sudah ada diukur:

```
── before_belai_trace.json · 89 frame · 2.97s @ 30fps
   TIDAK ADA SENDI YANG BERGERAK. Aksi ini tidak dianimasikan.
```

`Belai` dan `Ambil Hasil` sama-sama cuma memunculkan pesan. Satu-satunya
animasi aksi yang ada di game adalah `_play_tool_anim()`: 350 ms, satu sendi,
amplop segitiga linier (`st = 1 - |2t - 1|`).

Diukur, gerakan seperti itu **selalu** keluar dengan angka yang sama:

```
antisipasi 0    tahanan 0    ikutan 0    ease 1,00    jeda sekunder 0
```

Keempat nol itu bukan detail halus. Itu daftar persis dari hal-hal yang
membedakan gerakan yang DIANIMASIKAN dari gerakan yang cuma di-lerp. Mata
tidak menghitungnya, tapi mata melihat akibatnya: aksi 350 ms terbaca sebagai
kedutan, bukan sebagai pekerjaan yang dilakukan seseorang.

---

## 2. Mesinnya

`care_anim.py` menyusun satu aksi dari tiga hal.

### Fase

Satu pekerjaan bukan satu ayunan. Menuang air = ancang-ancang, turun, tuang,
tegak kembali, redam. Tiap fase punya durasi sendiri, jadi bagian yang harus
lambat boleh lambat tanpa memperlambat seluruh aksi. Nama fase ikut ke jejak
rekaman, jadi ia **kontrak** — mengganti namanya berarti mengganti perekamnya.

### Jalur

Satu kanal animasi: satu sendi, satu sifat, satu deret kunci. `jeda_ms`
menggeser seluruh jalur ke belakang — **inilah gerak sekunder**: badan dan
kepala membaca kurva yang sama beberapa frame lebih lambat daripada tangan.

`dasar='awal'` untuk kanal `.y`, yang pose diamnya bukan nol dan berbeda tiap
rig; `dasar='nol'` untuk rotasi.

### Kurva

Enam: `linier`, `masuk`, `keluar`, `halus`, `balik`, `redam`. Segitiga linier
berarti kecepatan konstan lalu berbalik arah seketika — tidak ada benda
bermassa yang bergerak begitu.

### Jalur sekanal DIJUMLAHKAN, tidak menimpa

`AksiRawat.terapkan()` mengelompokkan jalur menurut (sendi, sifat) lalu
menjumlahkan simpangannya terhadap pose dasar. Ini yang membuat kedalaman
jongkok bisa ditambahkan sebagai **lapisan** di atas resep apa pun tanpa
menulis ulang resepnya — dan tanpa lapisan terakhir diam-diam menghapus yang
sebelumnya.

### Dijalankan TERAKHIR di player.tick()

Blok animasi lama melerp tiap sendi kembali ke nol setiap frame saat pemain
diam. Kalau aksi perawatan menulis posenya lebih dulu, lerp itu menghapusnya
di frame yang sama dan tidak ada yang pernah terlihat bergerak. **Menulis
terakhir = menang.**

---

## 3. Ambang

Aksi perawatan yang layak disebut dianimasikan harus, pada sendi penggeraknya:

| sifat | ambang | kenapa |
|---|---|---|
| rentang | ≥ 25° | di bawah itu tidak terbaca di kamera main |
| durasi | ≥ 900 ms | 350 ms terbaca sebagai kedutan, bukan pekerjaan |
| antisipasi | ≥ 2° dan ≥ 60 ms | tanpa gerak balik, aksi mulai dari nol = kaku |
| tahanan | ≥ 80 ms | pose puncak harus sempat dibaca mata |
| ikutan | ≥ 1,5° | berhenti mati di titik akhir hanya terjadi pada mesin |
| ease | ≥ 1,35 | 1,00 = lerp linier; manusia 1,4–2,2 |
| jeda sekunder | ≥ 40 ms di satu sendi lain | badan telat mengikuti tangan |

Untuk aksi berulang: `stroke ≥ 4` dan `irama_sd_ms > 8`. **Irama nol =
metronom = mesin.** Jarak antar sapuan menyikat sengaja tidak sama
(300/300/340/290/360/310 ms); tangan manusia selalu meleset sedikit.

---

## 4. Yang ada sekarang

| resep | durasi | ciri |
|---|---|---|
| `belai` | 1400 ms | satu tangan, dua usapan, gratis — sengaja separuh bobot `gosok` |
| `gosok` | 2700 ms | sikat, enam sapuan beririgama, amplitudo mengecil ke belakang |
| `minum` | 1933 ms | ember dimiringkan, kolom air, palung terisi bertahap |
| `perah` | 2300 ms | jongkok dalam, tarikan BERGANTIAN kiri-kanan |
| `telur` | 2100 ms | jongkok sedang, satu tangan masuk sarang, tahanan 900 ms (meraba) |
| `cukur` | 2533 ms | membungkuk, sapuan panjang, badan ikut berputar |
| `bicara` | berulang | tiga ketukan tangan berjarak tidak sama + anggukan di akhir frasa |
| `dengar` | berulang | jauh lebih kecil, tapi bukan nol |

Resep panen dipilih dari **produk**, bukan spesies — spesies baru otomatis
memakai postur yang benar.

---

## 5. Alat penilai

```
tools/record.py     jalankan game sungguhan lewat skrip langkah; keluarkan
                    .mp4, filmstrip berlabel ms, dan jejak sudut sendi per
                    frame. Klok dipaksa non-real-time: tiap frame persis
                    1/fps detik, jadi dua rekaman dari kode yang sama
                    menghasilkan jejak yang sama.
tools/anim_trace.py ubah jejak jadi angka yang bisa dibantah.
tools/ab_sheet.py   lembar banding dua baris berlabel cuma A/B, urutan
                    diacak, kunci ditulis terpisah. Berhenti dengan kode 3
                    kalau klip patokan tidak ada — banding buta melawan
                    ingatan bukan banding buta.
```

### Tiga buta yang sudah terbukti menyesatkan

Alat ini bukan wasit yang netral. Ketiganya sudah pernah membuang waktu:

**`ease` membengkak karena tahanan.** Definisinya kecepatan sudut puncak
dibagi rata-rata. Aksi dengan tahanan panjang punya rata-rata rendah, jadi
`ease`-nya naik tanpa gerakannya membaik. Nilai ~5 pada aksi bertahanan 533 ms
adalah artefak, bukan prestasi.

**`jeda` pernah mengunci ke siklus salah — SUDAH DIPERBAIKI, lihat §6e.**
Korelasi silang mengeluarkan −667 ms pada sendi yang jelas-jelas mengikuti.
Ternyata bukan satu cacat tapi dua: puncak yang seri diselesaikan ke lag paling
negatif, dan sendi yang bergerak berlawanan arah tidak pernah ketemu karena
puncaknya dicari pada korelasi bertanda. Sekarang ada swauji tertanam
(`python tools/anim_trace.py --swauji`). Dicatat di sini karena angka −667 ms
sempat masuk ke beberapa tabel di dokumen ini sebelum ketahuan; tabel-tabel itu
sudah diukur ulang.

**Mengukur satu sumbu punya buta arah.** Condongan hewan yang disikat dibagi
antara `rotation_x` dan `rotation_z` menurut arah datangnya sikat. Probe yang
cuma membaca `rz` pernah melaporkan "ayam tidak bereaksi sama sekali" —
padahal diukur sebagai besar gabungan `sqrt(rx²+rz²)`, ayam justru bereaksi
paling besar dari semua hewan. **Metrik dengan buta arah menuduh kode yang
benar.**

---

## 6. Yang tidak bisa dilihat alat sendi

Ini bagian terpenting dokumen ini.

Sebuah aksi bisa **lulus setiap ambang di tabel** sambil menyapu udara satu
meter dari hewannya. Jejak sudut sendi tidak tahu apa-apa soal ruang.

Diukur dengan menempel penanda di ujung bulu sikat lalu mencatat jaraknya ke
kotak badan hewan tiap frame:

| | sebelum (min · frame menyentuh) | sesudah |
|---|---|---|
| gosok sapi | 0,04 m · 60/90 | 0,00 m · 64/90 |
| gosok kambing | 0,35 m · **0**/90 | 0,00 m · 81/90 |
| gosok ayam | 0,73 m · **0**/90 | 0,00 m · 61/90 |
| cukur domba | 0,14 m · 26/91 | 0,00 m · 76/91 |
| telur ayam | 0,68 m · **0**/68 | 0,00 m · 47/68 |

Empat dari enam aksi tidak pernah menyentuh hewannya. Semuanya lulus seluruh
ambang animasi.

Sebabnya jarak berdiri **tetap** 1,15 m dari titik tengah hewan, sementara
semua resep ditulis untuk tangan yang bekerja di ketinggian punggung sapi.
Sapi setengah-lebarnya 0,36 m dan punggungnya 1,37 m, jadi 1,15 m dari
pusatnya menaruh tangan tepat di lambungnya — **sapi kebetulan satu-satunya
yang benar, dan sapi satu-satunya hewan yang ada di filmstrip yang dilihat.**
Ayam setengah-lebarnya 0,11 m dan punggungnya 0,44 m: jarak yang sama
meninggalkan satu meter udara, dan tangannya melayang 70 cm di atas kepalanya.

Perbaikannya dua lapis:

- `animal_models.UKURAN` menyimpan (setengah-lebar, setengah-panjang, tinggi
  punggung) tiap spesies, dibaca dari kotak `badan` rig masing-masing.
  `jari_jari_arah()` memperlakukan badan berkaki empat sebagai **elips**:
  mendekat dari samping dan dari depan bukan jarak yang sama.
- `care_anim._lapisan_turun()` menambahkan kedalaman jongkok sebagai lapisan
  di atas resep apa pun, bentuk waktunya dipinjam dari kanal `.y` yang sudah
  ada. Alternatifnya sembilan resep per spesies yang harus dijaga tetap
  sinkron selamanya.

**Pelajarannya**: kritikus harus mengukur hal LAIN dari yang diukur
pembangunnya. Ambang animasi dan kebenaran ruang adalah dua pertanyaan
terpisah, dan yang kedua tidak akan pernah ketahuan dari yang pertama.

### 6a. Tiga sebab lagi, ditemukan setelah yang pertama ditutup

Menutup sebab pertama tidak menutup pertanyaannya. Probe yang sama, dijalankan
ulang dengan RNG berbenih dan hewan dikembalikan ke posisi jadwalnya supaya
angkanya bisa dibandingkan antar-jalan, menemukan tiga sebab berikutnya —
masing-masing lolos dari seluruh tabel ambang animasi.

**Hewannya berjalan pergi.** Menyikat kebetulan menahan hewannya, lewat pemicu
yang dipasang tiap sapuan. Memanen tidak menahan apa pun. Terukur: gunting
MENYENTUH domba di frame awal (0,00 m) lalu jaraknya naik ke median 2,06 m —
dombanya berjalan pergi di tengah pencukuran, dan sisa animasinya mencukur
udara. `FarmAnimal.tahan_diam(detik)` menahannya; hewan yang ditahan tetap
bernapas dan tetap bereaksi terhadap sentuhan, jadi ini bukan patung baru.
Median 2,06 → 0,04 m, frame menyentuh 15/91 → 56/91.

**Jangkauan dipilih per pemanggil, dan satu di antaranya salah.** Sikat
menambah panjang tangan; telapak telanjang tidak. Angkanya ditulis tangan di
tiap pemanggil, jadi mengambil telur — bertangan kosong — memakai jangkauan
bertangkai dan berhenti 14 cm terlalu jauh. Sekarang `_jangkau()` membacanya
dari `alat` di RESEP, dan nilai bawaan `_geometri_hewan()` dihapus supaya
tidak ada pemanggil yang bisa diam-diam dapat angka yang salah lagi.

**Yang diselaraskan dengan hewan adalah pusar pemain, bukan tangannya.** Semua
alat menggantung di lengan kanan, jadi ujung kerjanya selalu ~0,30 m ke
samping. Pada sapi sepanjang 2 m selisih itu ditelan badan; pada ayam
setengah-panjang 0,22 m ia adalah SELURUH celahnya — terukur, tangan berhenti
tepat 0,30 − 0,22 = 0,08 m dari kotak badan sepanjang aksi. `_langkah_masuk()`
sekarang menggeser titik berdiri sebanyak pergeseran bahu kanan, dibaca dari
rig, bukan ditulis sebagai angka tetap.

**Dan sudut yang besar tidak berarti jangkauan yang jauh.** Resep telur menahan
bahu di −84° karena angka besar terbaca seperti "menjulur jauh". Yang
sebenarnya terjadi: lengan menggantung dari bahu, jadi −84° mengangkatnya ke
MENDATAR setinggi bahu. Sepanjang 900 ms merabanya tangan itu melayang
0,38–0,46 m **di atas** ayamnya, dan baru menyentuh sarang 330 ms saat ditarik
keluar — pemainnya diberi telur di detik 1,76 sementara tangannya masih di
udara. Jarak ke kotak badan nol di rentang −52°..−20°; seluruh rabaan
dipindahkan ke dalam rentang itu dan badan ditahan rendah sampai tangannya
benar-benar keluar. Kontak beruntun 0 → 1,13 detik; median 0,42 → 0,02 m.

Pelajaran yang sama, dalam bentuk yang lebih tajam: **angka sudut adalah niat,
bukan hasil.** Satu-satunya cara tahu ke mana tangan benar-benar pergi adalah
menempelkan penanda di ujungnya dan mengukurnya.

### 6b. Sebab kelima: sapuan seukuran sapi pada hewan seukuran ayam

Sesudah empat sebab di atas ditutup, tiap aksi sudah MENYENTUH hewannya —
tapi pada hewan pendek ia menyentuh lalu lepas, dua kali tiap sapuan.

Sapuan menyikat ditulis untuk lambung sapi: permukaan tegak setinggi 0,37 m,
jadi sapuan tegak sepanjang itu benar. Punggung ayam tingginya 0,44 m dan
MENDATAR. Terukur, ujung sikat berayun antara 0,49 m (menyentuh) dan 0,86 m
(0,28 m di atas ayamnya) — separuh tiap sapuan menyapu udara.

Menunduk lebih dalam tidak bisa menutupnya: 0,70 m pada karakter 1,76 m sudah
jongkok penuh, dan lebih dari itu badannya masuk tanah.

`_lapisan_skala()` menarik tiap kunci ke arah garis diamnya sebanyak
`1 - skala`, dengan skala = tinggi punggung / tinggi sapi (dibatasi 0,50).
Ujung-ujungnya tidak ikut ditarik, jadi aksinya tetap mulai dan berakhir di
pose diam yang sama. Sudut bahu yang lebih kecil berarti lengan lebih
menggantung, dan lengan yang menggantung berarti tangan lebih RENDAH — arah
yang memang dibutuhkan hewan pendek.

Satu jebakan yang cuma ketahuan karena diukur ulang: memperkecil ayunan saja
membuatnya LEBIH BURUK di sumbu lain. Lengan yang berayun lebih pendek juga
menjulur lebih pendek, jadi sikatnya turun ke ketinggian yang benar tapi
tertarik 0,07-0,27 m ke belakang dan lewat DI ATAS ayam alih-alih
menyentuhnya. Jangkauan berdiri harus ikut diskalakan: `r + jangkau * skala`.

Hasilnya, dan perhatikan bahwa baris sapi tidak bergerak sama sekali (skala
1,00 — resep aslinya memang ditulis untuk sapi):

| | sebelum skala | sesudah |
|---|---|---|
| belai kambing | 0,13 m · 25/46 | 0,00 m · 37/46 |
| belai ayam | 0,22 m · 24/46 | 0,00 m · 26/46 |
| gosok kambing | 0,04 m · 60/90 | 0,00 m · 81/90 |
| gosok ayam | 0,25 m · 45/90 | 0,00 m · 61/90 |
| cukur domba | 0,04 m · 56/91 | 0,00 m · 76/91 |
| telur ayam | 0,02 m · 40/68 | 0,00 m · 47/68 |
| gosok/belai sapi | 0,05 / 0,03 m | **sama persis** |

Ambangnya tetap lulus sesudah dikecilkan — diukur pada rekaman menyikat ayam,
sendi penggerak sikat `bahu_r.rotation_x`: rentang 36,5° (ambang 25),
durasi 2700 ms (900), antisipasi 6,5°/267 ms (2°/60), tahanan 533 ms (80),
ikutan 4,5° (1,5), ease 5,31 (1,35), 9 sapuan (4).

Catatan alat: sesudah lapisan jongkok dipakai, `anim_trace` menyebut
`lutut_r` sebagai penggerak karena rentangnya 107,8° — lutut jongkok
mengalahkan sendi yang benar-benar mengerjakan aksinya. Pembacaan ambang
harus dilakukan pada sendi kerjanya, bukan pada yang dipilih otomatis.



---

## 6c. Apa yang ditemukan kritikus berkonteks segar

Bagian ini ditulis dari laporan kritikus yang tidak pernah melihat kode ini
sebelumnya dan diminta mengukur hal LAIN dari yang sudah diukur pembangunnya.
Ia menemukan tiga hal yang tidak terlihat oleh kedua alat yang sudah ada, dan
satu di antaranya adalah akar dari sesuatu yang sudah dikejar dari arah lain
tanpa ketemu.

### Tidak ada yang memilih SISI hewan

`_langkah_masuk()` menaruh pemain di sinar dari pusat hewan **ke tempat pemain
kebetulan berdiri**. Tidak ada yang memutar hewannya, dan tidak ada yang
memilih rusuknya. Diukur pada 8 arah datang x 4 arah hadap x 5 aksi, sudut
sisinya tersebar rata 0-180 derajat: seperempat pemerahan terjadi dalam 45
derajat dari moncong sapi, dan mencukur domba mendarat tepat di depan
kepalanya. Tidak ada peternak yang memerah sapi dari depan mukanya.

Akar keduanya, dari sumber yang sama: **`jari_jari_arah()` menghitung elips
badan selaras sumbu DUNIA dan tidak pernah menerima `rotation_y` hewan.**
Begitu hewannya menoleh, sumbu panjang dan sumbu lebarnya tertukar. Pada sapi
(0,36 x 0,68 m) galatnya 0,32 m — separuh jangkauan alatnya sendiri:

| arah hadap sapi | jarak berdiri dipakai | kulit sebenarnya | selisih |
|---|---|---|---|
| 0°, datang 0° | 0,67 m | 0,64 m | +0,03 m |
| 45°, datang 0° | 0,67 m | 0,40 m | +0,26 m di udara |
| 45°, datang 90° | 0,51 m | 0,54 m | −0,03 m **menembus** |
| 90°, datang 0° | 0,67 m | 0,37 m | +0,30 m di udara |
| 90°, datang 90° | 0,51 m | 0,62 m | −0,10 m **menembus** |

Perbaikannya `titik_rusuk()`: titik berdiri dipilih di RUANG LOKAL hewan —
lurus di samping badan, setengah badan ke arah pemain — lalu diputar balik ke
dunia. Hewan boleh menghadap ke mana saja; pemain selalu berakhir di rusuknya.
Sesudahnya, pada uji yang sama:

| aksi | di depan moncong (<45°) | di rusuk (60-120°) |
|---|---|---|
| perah | 8/32 → **0/32** | 32/32 |
| telur | 6/32 → **0/32** | (49°/131°, lihat catatan) |
| cukur | 5/32 → **0/32** | 32/32 |
| gosok | 4/32 → **0/32** | 32/32 |
| belai | 8/32 → **0/32** | 32/32 |

Catatan `telur`: ayam setengah-lebarnya cuma 0,11 m, jadi pergeseran tangan
0,30 m adalah sudut yang besar pada jari-jari sekecil itu. Pemainnya memang
di samping ayam; yang melar adalah sudutnya, bukan posisinya.

### Biaya mendarat, hasilnya kadang-kadang

`AksiRawat.update()` berhenti memanggil pemicu begitu aksi dibatalkan — itu
memang benar. Yang salah: `_spend_energy()` dan `flash_msg()` dibayar **di
muka**, sebelum `care_anim.mulai()`. Tekan W setengah detik sesudah menyikat
dan HUD menulis "Bersih 12% -> 100%, +1 hati" sementara kandangnya tetap
kotor, hatinya tetap nol, dan energi hilang 2.

Sekarang biaya dan pesan hasilnya ikut masuk ke pemicu, bersama efeknya.
Pesan pembuka tinggal "Menyikat Betsy..." — janji yang tidak dibuat tidak
bisa diingkari. Terukur sesudahnya, dibatalkan pada 500 ms:

| aksi | energi | keadaan | pesan |
|---|---|---|---|
| gosok | 0,0 | bersih 12 → 12 | "Menyikat Betsy..." |
| perah | 0,0 | siap 9 → 9, tas kosong | "Memerah Betsy..." |
| beri minum | 0,0 | air 8 → 8 | "Mengisi palung..." |
| gosok, batal pada 2400 ms | 2,0 | bersih 12 → **100**, +1,5 hati | hasil lengkap |

Yang terakhir itu yang membuktikan perbaikannya bukan sekadar mematikan
efeknya: batal SESUDAH titik efek tetap memberi hasil dan tetap menagih.

### Ganti scene memaku pemain di koordinat peta lama

Tidak ada `care_anim.bereskan()` di jalur portal. `_saat_frame` terus
memanggil `_maju()`, yang menulis `player.x/z` tanpa syarat — jadi selama
sisa aksi pemain berdiri di peta baru, tidak bisa pergi dari satu titik,
memegang ember, alat HUD-nya hilang, dan memerah sapi yang ada di peta lain.
Sekarang portal dan pingsan sama-sama memanggil `bereskan()`. Terukur: aksi
dibersihkan, ember dilepas, alat HUD kembali, pemain bergerak 8,0 m dalam 45
frame (dulu 0,0), dan susunya tidak masuk tas.

### Alat ukurnya sendiri menyembunyikan satu ambang

`tools/anim_trace.py` MENGHITUNG `irama_sd_ms` sejak awal tapi `cetak()` tidak
pernah mencetak kolomnya, jadi satu ambang di BRIEF tidak bisa dibaca dari
keluaran alatnya sendiri. Sekarang dicetak. Menyikat ayam: `bahu_r` irama
33,3 ms (ambang > 8).

### Dan satu artefak di probe kritikusnya sendiri

Probe sudut sisi menjalankan 32 aksi berturut-turut tanpa mengembalikan
energi pemain. Aksi pertama (`perah`) habis-habisan memakainya, jadi tiga
aksi berikutnya DITOLAK — pemainnya tidak melangkah ke mana pun dan sudut
sisinya jadi sekadar arah datang tadi. Itu yang membuat `cukur`, `gosok` dan
`telur` tetap terlihat tersebar 0-180 derajat sesudah diperbaiki. Dengan
`s.energy = 100` dikembalikan tiap iterasi, ketiganya ikut lulus.

Ini kesalahan pengukuran kesebelas yang tercatat di pekerjaan ini, dan yang
kesatu yang datang dari kritikus, bukan dari pembangun. Pelajarannya tidak
berubah: **alat ukur yang belum pernah salah biasanya belum pernah diperiksa.**

---

## 6d. Sudut yang ketiga kalinya terbalik, dan alat ukur yang akhirnya jujur

Sesudah semua di atas, satu-satunya alat ukur yang tersisa masih berbohong
dalam tiga cara sekaligus, dan ketiganya membuat angkanya terlalu bagus:

1. **Kotak badannya ditulis tangan** di probe, dan lebih besar daripada torso
   yang benar (kambing setengah-panjang 0,62 lawan 0,36 yang sebenarnya).
   Diverifikasi lewat `getTightBounds()` tiap anak rig: `UKURAN` di game
   ternyata BENAR — cocok persis dengan kotak torso yang dirender untuk
   kelima spesies. Yang salah probe-nya. (Satu kekecualian nyata: tinggi
   domba tercatat 0,85 m sementara torsonya berhenti di 0,77 m.)
2. **Rotasi hewan diabaikan.** Sapi berdiri pada `rotation_y = -90`, jadi
   sumbu panjangnya (0,68) ada di X dunia sementara probe memakainya di Z.
   Kotaknya tertukar sisinya.
3. **Jaraknya tak bertanda.** Menyerempet permukaan dan terbenam 30 cm di
   dalam daging sama-sama tercatat 0,00.

Probe penggantinya membaca `UKURAN` dari game, memutar titik ujung alat ke
ruang lokal hewan (swauji: pusat torso sapi harus jatuh di lokal 0,0 — hasilnya
0,004), dan mengembalikan jarak BERTANDA. Ia langsung menemukan dua hal yang
tidak pernah terlihat sebelumnya.

### Memerah dilakukan di atas punggung sapi

Diukur di ruang lokal sapi, selama seluruh fase menarik: ember ada di
`lx` 0,05-0,14 (torso setengah-lebar 0,36 — jadi di GARIS TENGAH) dan
`ly` 1,29-1,59 (punggung 1,37 — jadi DI ATASNYA). Yang dianimasikan bukan
memerah, melainkan menjulurkan tangan melewati sapi sambil menenteng ember
di atas tulang belakangnya.

Sebabnya sama persis seperti pada resep telur, ketiga kalinya: bahu ditahan
di -70..-87 derajat karena angka besar terbaca seperti "menjulur ke bawah",
padahal lengan menggantung dari bahu sehingga sudut sebesar itu MENGANGKATNYA.

Kali ini petanya dibuat dulu, bukan ditebak: resep ditambal jadi tanjakan
lambat 0 → -90 derajat di dalam mesin sungguhan, lalu tiap frame mencatat
posisi ujung ember di ruang lokal sapi.

| bahu | lx | ly | | bahu | lx | ly |
|---|---|---|---|---|---|---|
| −10 | 0,74 | 0,33 | | −50 | 0,13 | 0,83 |
| −28 | 0,40 | 0,49 | | −71 | 0,06 | 1,26 |
| −32 | 0,33 | 0,55 | | −86 | 0,12 | 2,05 |

Ambing ada di lx 0,33-0,40 / ly 0,49-0,55, yaitu bahu **−28..−34**. Seluruh
tarikan dipindah ke pita itu. Sesudahnya ember bertahan di lx 0,33-0,55 dan
ly 0,45-0,55 sepanjang fase menarik, dengan jarak bertanda −0,03 s.d. +0,09.

### Kelonggaran berdiri per resep

Mencukur menyapu panjang lewat `rotation_z`, jadi ujung bilahnya menjulur
lebih jauh ke dalam daripada aksi lain dengan jangkauan yang sama: terukur,
ia terbenam 9-22 cm ke dalam torso domba di 49 dari 91 frame. `RESEP` sekarang
menerima `renggang` — meter tambahan jarak berdiri, ditambahkan SESUDAH
penskalaan, karena galatnya bukan proporsi melainkan panjang tetap alatnya.

Hasil akhir seluruh tabel, diukur dengan alat yang sudah jujur:

| aksi | min | frame menyentuh (≤12 cm) | frame menembus > 8 cm |
|---|---|---|---|
| belai sapi | −0,03 | 25/46 | 0 |
| belai ayam | 0,00 | 22/46 | 0 |
| belai kambing | −0,04 | 24/46 | 0 |
| gosok sapi | −0,04 | 54/90 | 0 |
| gosok kambing | −0,12 | 59/90 | **10** |
| gosok ayam | −0,09 | 57/90 | 1 |
| perah sapi | −0,26 → **−0,03** | 24 → 38/90 | 11 → **0** |
| cukur domba | −0,23 → **−0,08** | 25 → 54/91 | 49 → **2** |
| telur ayam | −0,11 → **−0,03** | 39 → 35/68 | 17 → **0** |

Ambang animasi `perah` tetap lulus sesudah pitanya dipindah, diukur pada
`bahu_r.rotation_x`: rentang 46,0° (dari 87), durasi 2300 ms, antisipasi
11,0°/433 ms, tahanan 600 ms, ikutan 8,0°, ease 4,29, 7 sapuan, irama 146,1 ms,
jeda sekunder 67 ms pada leher (diukur ulang dengan pengukur yang sudah
diperbaiki, §6e).

### Satu baris yang sengaja dibiarkan merah

`gosok kambing` masih menembus 0,12 m di 10 dari 90 frame. Kelonggaran 0,05 m
pada `gosok` diuji: tembusan kambing turun ke 5/90, **tapi sentuhan pada SAPI
jatuh dari 54 ke 40 dari 90**. Sapi hewan yang paling sering disikat, jadi
tukar itu rugi. Sisanya dibiarkan dan dicatat, bukan ditukar dengan kemunduran
pada kasus yang paling sering terjadi.

---

## 6e. Pertanyaan terbuka kritikus, dijawab: pengukurnya yang salah

Kritikus meninggalkan satu hal tanpa vonis: kolom `jeda` melaporkan **−667 ms**
untuk kepala, badan dan kedua lutut saat menggosok — sendi-sendi itu
MENDAHULUI lengan penggerak dua pertiga detik. Ia menulis: "salah satu dari
dua hal ini keliru dan belum ada yang menengahi: gerak sekundernya, atau
pengukur jedanya."

Diadili dengan sinyal yang jawabannya sudah diketahui. Dua cacat, keduanya di
pengukurnya, dan keduanya membuat angkanya tidak sekadar meleset tapi terbalik
maknanya.

**Satu: puncak yang seri diselesaikan ke lag paling negatif.** Gerakan berulang
membuat korelasi silang ambigu — sapuan berperiode 300 ms punya puncak sama
tinggi di lag 0, ±1 periode, ±2 periode. Kode lama memakai `c > best`, jadi di
antara puncak yang seri ia menyimpan yang pertama ditemukan, dan loopnya mulai
dari `-max_lag`. Diuji: dua deret berperiode 9 frame dengan jeda **nol**
dilaporkan **−600 ms**.

**Dua: sendi yang bergerak berlawanan arah tidak pernah ketemu.** Puncaknya
dicari pada korelasi BERTANDA. Empat kanal di resep menggosok ditulis sebagai
kelipatan NEGATIF penggeraknya — badan mencondong ke belakang saat lengan
mengayun ke depan, yang justru gerak sekunder yang benar. Korelasinya negatif
di lag sebenarnya, jadi pencarian puncak mendarat di batas pencarian: −667 ms
bukan sebuah pengukuran, itu angka `max_lag`.

Perbaikannya: cari puncak |korelasi| (yang diukur selisih WAKTU, bukan
tandanya), dan di antara puncak yang praktis seri pilih |lag| terkecil.

Diperiksa terhadap dua kebenaran dasar yang saling bebas. Sinyal buatan:

| kasus | jeda 0 | 67 ms | 133 ms | 267 ms |
|---|---|---|---|---|
| punuk sekali jalan | 0 | 67 | 133 | 267 |
| punuk berlawanan arah | 0 | 67 | 133 | 267 |
| sapuan berulang 300 ms | 0 | 67 | 133 | 267 |
| sapuan berulang berlawanan | 0 | 67 | 133 | 267 |

Dan `jeda_ms` yang tertulis di resep menggosok, dibandingkan dengan yang
diukur dari rekaman sungguhan:

| kanal | tertulis | terukur | selisih |
|---|---|---|---|
| siku_r.rotation_x | 70 | 67 | −3 |
| badan.rotation_x | 130 | 100 | −30 |
| leher.rotation_x | 150 | 133 | −17 |
| lutut_r.rotation_x | 140 | 133 | −7 |
| badan.rotation_z | 175 | 167 | −8 |
| lutut_l.rotation_x | 185 | 167 | −18 |
| leher.rotation_y | 195 | 167 | −28 |

Semua di dalam satu frame (33,3 ms). Jawaban atas pertanyaan kritikus:
**gerak sekundernya benar sejak awal; yang bohong pengukurnya.**

Swauji itu sekarang tertanam di alatnya: `python tools/anim_trace.py --swauji`,
keluar dengan kode 1 kalau ada yang gagal. Alat ukur yang belum pernah
diperiksa biasanya belum pernah salah hanya karena tidak ada yang melihat.

---

## 6f. Berbicara: lawan bicaranya mematah, dan fasenya tidak bisa diulang

Dari tiga animasi yang diminta di brief — panen, menggosok, berbicara — yang
ketiga paling sedikit diperiksa. Diukur sekarang.

**Yang sudah benar.** Keduanya saling menatap (selisih 0,00° di kedua arah).
Sisi pemain lulus seluruh ambang pada `bahu_r.rotation_x`: rentang 53,0°,
durasi 4333 ms, antisipasi 7,0°/233 ms, tahanan 733 ms, ease 6,71, 13 ketukan,
irama 61,6 ms. Lawan bicaranya bergerak, bukan patung: angguk 6,1°, goyang
4,8°, dan napas yang tidak pernah berhenti.

**Batas yang tidak bisa dilewati.** NPC manusia di sini satu mesh
`humanoid.obj` TANPA pivot sendi — jalur Vitaboy gagal di lingkungan ini, dan
`entities.py` sengaja menangkap kegagalannya supaya game tetap bisa dibuka.
Jadi lawan bicara cuma punya rotasi badan utuh dan posisi. Tidak ada isyarat
tangan yang mungkin dibuat tanpa rig itu. Ini batas struktural, bukan sesuatu
yang bisa diperbaiki di dalam potongan ini.

**Cacat satu: berpaling tidak butuh waktu.** `mulai_percakapan()` menulis
`rotation_y` sekali di frame pembuka, jadi lawan bicara mematah menghadap
pemain dalam SATU frame. Terukur, rentang `rotation_y` selama seluruh
percakapan 0,0° — bukan karena ia tidak berputar, tapi karena seluruh
putarannya sudah selesai sebelum frame pertama tercatat.

Sekarang ia berpaling 320 ms dengan ease-out kubik lewat jalur sudut
terpendek. Terukur: 8 frame (266 ms) dari 0° ke 90°, berangkat 25° di frame
pertama dan mendarat 0,02° di frame terakhir — leher yang berhenti sendiri,
bukan motor yang dimatikan.

**Cacat dua: berpaling balik tidak pernah terjadi.** `_bicara_rot0` disimpan
sejak awal dan tidak pernah dipakai satu kali pun. Lawan bicara tetap
menghadap ke tempat pemain berdiri, selamanya, bahkan sesudah pemain pergi.
Sekarang ia kembali dalam 420 ms — lebih lambat daripada saat menoleh, karena
tidak ada yang menariknya. Terukur: 10 frame (333 ms) dari 53,6° ke 0,0°.

**Cacat tiga, dan ini yang merusak seluruh proyek ini: `hash()`.** Fase
anggukan NPC dan fase napas hewan sama-sama diambil dari `hash(actor_id)`.
Python **mengacak ulang hash string tiap proses**. Artinya dua rekaman dari
kode yang sama persis punya fase berbeda, dan tidak bisa dibandingkan —
padahal seluruh metode kerja di dokumen ini bersandar pada rekaman yang bisa
diulang. Jebakan yang sama sudah tercatat di `entities.py:262` sejak lama,
dengan perbaikannya sekaligus: `sum(map(ord, ...))`.

Diperiksa: dua proses terpisah sekarang memberi `_bicara_t` awal 2,3415 yang
sama persis.

Pelajaran yang mahal: **catatan tentang sebuah jebakan tidak mencegah jebakan
itu.** Peringatannya sudah ditulis di berkas lain di repo yang sama, dan dua
tempat tetap jatuh ke dalamnya.

---

## 7. Patung

Tiga kali, dengan bentuk berbeda, sesuatu berhenti bergerak sama sekali:

| di mana | berapa lama | sebab |
|---|---|---|
| pendengar dialog | 2,7 detik tiap siklus | `max(0, sin(t))` memotong separuh gelombang |
| ternak sesudah disikat | 1,30 detik | `FarmAnimal` diam tidak menganimasikan apa pun |
| dunia selama dialog | selamanya | `app.py` menggerbangi semuanya di balik `mode == 'hud'` |

Yang ketiga itu yang paling dalam: waktu permainan, gerak, dan input memang
HARUS berhenti saat modal terbuka — itu gunanya modal. Tapi **animasi tidak**.
`_tick_percakapan()` menjalankan pose saja: tidak memanggil `player.tick()`
atau `entities.update()`, jadi jam tidak maju dan WASD tidak diterima
(terukur: delta 0,0000 menit, pergeseran 0,00000).

Obatnya sama untuk ketiganya: **jangan pernah meluruh ke nol, luruhlah ke
napas.** Tiap ternak dan tiap NPC punya denyut kecil yang selalu jalan, fase
digeser dari hash id-nya — kawanan yang bernapas serempak terbaca sebagai satu
benda, bukan sebagai beberapa hewan.

---

## 8. Aturan yang tidak bisa dipatuhi bukan aturan

Sesudah air dipakai menggerbangi produksi, dua kali ditemukan hewan yang
dihukum tanpa jalan keluar: airnya meluruh 55% tiap pagi sampai nol, tiga hari
lalai jadi SAKIT dan hati turun tiap hari — sementara palung hanya ada di
kandang kebun, jadi pemain tidak punya satu pun cara mencegahnya.

Pertama bebek di danau. Ditambal. Lalu **penyapuan ulang seluruh daftar hewan**
menemukan kucing dan kelinci di jebakan yang sama.

> Memperbaiki satu contoh dari sebuah cacat bukan memperbaiki cacatnya.
> Setelah menambal yang pertama, daftar lengkapnya harus disapu lagi.

`husbandry.air_mandiri()` sekarang gerbangnya: hewan yang mencari minumnya
sendiri adalah yang di air terbuka ATAU yang tidak dikandangkan. Takaran air
hanya berlaku untuk hewan yang dikurung, karena hanya merekalah yang
benar-benar bergantung pada pemain untuk air.

---

## 9. Alat pertanian: dipindah dari mesin lama

Enam aksi alat — cangkul, siram, tanam, panen tanaman, kapak, beliung —
sekarang memakai `care_anim`. Yang tertinggal cuma **bertarung** (`Pedang`,
dan `attack()`), sengaja: irama serangan adalah angka keseimbangan permainan,
bukan angka animasi, dan memanjangkannya dari 350 ms ke 1,2 detik mengubah
pertarungan, bukan memperbaikinya. Itu potongan tersendiri dengan patokan
tersendiri.

Diukur dengan alat yang sama, pada sendi dengan rentang terbesar:

| aksi | rentang | durasi | antisipasi | tahanan | ikutan | ease | jeda |
|---|---|---|---|---|---|---|---|
| cangkul | 146,0° | 1000 ms | 6,2°/200 ms | 200 ms | 7,0° | 5,10 | 133 ms |
| siram | 78,9° | 1267 ms | 4,2°/200 ms | 667 ms | 5,8° | 7,57 | 133 ms |
| tanam | 90,0° | 1133 ms | 4,0°/233 ms | 567 ms | 3,7° | 8,87 | 100 ms |
| petik | 86,0° | 1167 ms | 4,0°/233 ms | 500 ms | 2,4° | 4,51 | 133 ms |
| tebang | 174,0° | 1233 ms | 9,3°/233 ms | 200 ms | 8,9° | 4,26 | 167 ms |
| tambang | 190,0° | 1133 ms | 9,9°/233 ms | 200 ms | 7,6° | 5,20 | 167 ms |
| **ambang** | **25°** | **900 ms** | **2°/60 ms** | **80 ms** | **1,5°** | **1,35** | **40 ms** |

Dan mesin lama, diukur langsung lewat `_play_tool_anim()` supaya
perbandingannya bukan dari ingatan:

| mode | rentang | durasi | antisipasi | tahanan | ikutan | ease | jeda |
|---|---|---|---|---|---|---|---|
| down | 128,6° | 433 ms | **0** | 33 ms | **0** | 1,50 | **0** |
| water | 63,3° | 367 ms | **0** | 100 ms | **0** | **1,19** | **0** |
| bend | 81,0° | 400 ms | **0** | 33 ms | **0** | 1,38 | **0** |
| swing | 95,2° | 400 ms | **0** | 33 ms | **0** | 1,38 | **0** |
| mine | 152,4° | 433 ms | **0** | 33 ms | **0** | 1,50 | **0** |

Kolom `jeda` di kedua tabel di atas DIUKUR ULANG sesudah pengukurnya sendiri
diperbaiki (§6e). Angka pertama yang tercatat — 433-667 ms untuk resep baru,
dan 667 ms untuk mode `mine` yang lama — adalah artefak batas pencarian, bukan
pengukuran. Yang benar: resep baru 100-167 ms, mesin lama **nol di kelima
modenya**. Perbaikannya membuat mesin lama terlihat lebih buruk, bukan lebih
baik, karena satu-satunya angka yang dulu terlihat mendukungnya ternyata palsu.

Perhatikan bahwa RENTANG-nya tidak pernah jadi masalah — mesin lama mengayun
sejauh yang baru. Yang tidak ada padanya adalah semua yang lain: tidak ada
gerak balik sebelum ayunan, tidak ada pose puncak yang sempat dibaca, tidak
ada berhenti yang melewati lalu kembali, dan seluruh badan bergerak di frame
yang sama persis.

### Yang berbeda dari resep ternak

**Durasinya setengahnya** (1,15-1,35 detik lawan 2,3-2,7). Mengurus seekor
sapi terjadi sekali sehari; mencangkul terjadi dua puluh kali berturut-turut,
dan aksi 2,5 detik akan mengubah bertani jadi menunggu.

**Alatnya tidak diganti properti.** Aksi ternak menyembunyikan alat HUD lalu
memasang ember/sikat sendiri. Alat pertanian sudah memegang benda yang benar,
jadi `alat_hud: True` membiarkannya terlihat — dan resep `siram` menganimasikan
alat itu langsung lewat kanal `alat_hud`, supaya penyiramnya benar-benar
miring saat menuang alih-alih menyemburkan air dari alat yang tetap tegak.

Satu jebakan di situ: pose diam penyiram di tangan bukan nol (`rotation_x`
−12°), jadi kanalnya harus `dasar='awal'`. Dengan `dasar='nol'`, `usai()` akan
menulis 0 dan MELURUSKAN alat itu permanen begitu aksi selesai.

## 10. Ranjau: rig Vitaboy

`assets/vitaboy/` tidak ada di repo, jadi jalur avatar Vitaboy gagal di semua
mesin dan semua orang mendapat rig voxel — yang memang rig yang diukur di
seluruh dokumen ini.

Tapi kalau aset Vitaboy suatu saat di-bake (`tools/bake_all.sh`), `_pivot_*`
menjadi **Entity kosong** yang cuma dipakai untuk menempelkan benda di tangan.
Menulis rotasi ke sana tidak menggerakkan badan sama sekali: yang terlihat cuma
ember dan sikat melayang di udara. Seluruh animasi perawatan harus disambungkan
ulang ke `VitaboyAvatar` sebelum jalur itu dinyalakan.
