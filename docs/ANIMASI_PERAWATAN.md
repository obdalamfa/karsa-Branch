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

**`jeda` bisa mengunci ke siklus salah.** Korelasi silang kadang mengeluarkan
−667 ms pada sendi yang jelas-jelas mengikuti. Angka negatif besar di kolom itu
harus dicurigai, bukan dilaporkan.

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
| gosok kambing | 0,35 m · **0**/90 | 0,00 m · 60/90 |
| gosok ayam | 0,73 m · **0**/90 | 0,00 m · 45/90 |
| cukur domba | 0,14 m · 26/91 | 0,00 m · 56/91 |
| telur ayam | 0,68 m · **0**/68 | 0,00 m · 40/68 |

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

## 9. Yang masih memakai mesin lama

Semua alat pertanian — cangkul, siram, panen tanaman, kapak, pickaxe, pedang —
masih memakai `_play_tool_anim()` 350 ms. Diukur, semuanya masih antisipasi 0,
tahanan 0, ikutan 0, ease 1,00, jeda sekunder 0.

Memindahkannya ke `care_anim` adalah pekerjaan berikutnya yang paling besar
hasilnya per baris kode, karena mesinnya sudah ada dan yang dibutuhkan cuma
resep.

## 10. Ranjau: rig Vitaboy

`assets/vitaboy/` tidak ada di repo, jadi jalur avatar Vitaboy gagal di semua
mesin dan semua orang mendapat rig voxel — yang memang rig yang diukur di
seluruh dokumen ini.

Tapi kalau aset Vitaboy suatu saat di-bake (`tools/bake_all.sh`), `_pivot_*`
menjadi **Entity kosong** yang cuma dipakai untuk menempelkan benda di tangan.
Menulis rotasi ke sana tidak menggerakkan badan sama sekali: yang terlihat cuma
ember dan sikat melayang di udara. Seluruh animasi perawatan harus disambungkan
ulang ke `VitaboyAvatar` sebelum jalur itu dinyalakan.
