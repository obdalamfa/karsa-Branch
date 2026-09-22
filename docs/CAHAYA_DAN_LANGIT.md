# Cahaya dan langit — Lembah Karsa 3D

Permintaan pemilik: *"buat grafik yang lebih baik dengan sempurna."*

Dokumen ini mencatat empat cacat yang saling bertaut, ditemukan dengan
mengukur warna piksel yang benar-benar dirender — bukan dengan membaca kode
dan menyimpulkan niatnya. Yang terbesar di antaranya membuat SELURUH kode
siang-malam di `app.py` tidak pernah terlihat sama sekali.

---

## 1. Langitnya merah muda sepanjang siang

Langit digerakkan tabel palet enam waktu di `sky.py`. Dibaca sebagai warna:

```
palet         zenith                 cakrawala              pendar
_SKY_NIGHT     38, 13, 38             26,204,255 sian       255, 51,204 MERAH MUDA
_SKY_DAWN     255,204,230            255, 51,204 MERAH MUDA   0,255,255 sian
_SKY_MORNING  255,230,255             51,255,204 sian       255, 51,204 MERAH MUDA
_SKY_DAY      230,204,255            255,128,204 MERAH MUDA  51,204,255 sian
_SKY_DUSK     255,128,204 MERAH MUDA  51,204,255 sian       255,204,255
_SKY_EVENING  128, 26,128             26,204,255 sian       255, 51,204 MERAH MUDA
```

Tidak ada satu pun warna langit yang masuk akal di seluruh tabel. Magenta
`(1,00 0,20 0,80)` dipakai di **empat slot berbeda** — sebagai pendar malam,
cakrawala fajar, pendar pagi, dan pendar petang sekaligus. Itu bukan palet,
itu warna tempelan yang tidak pernah diganti.

Diukur dari frame yang benar-benar dirender di scene farm:

```
jam     langit atas frame
09:00   158,198,211
12:00   253,131,210  MERAH MUDA
15:00   253,131,210  MERAH MUDA
22:00    26,210,253  sian terang
```

Dua hal yang tidak bisa dibela sebagai gaya: sepanjang siang langitnya merah
muda menyala, dan **pukul 22:00 langitnya lebih terang daripada pukul 09:00.**

Tabel penggantinya tetap bergaya — birunya lebih pekat dan jingganya lebih
hangat daripada langit sungguhan, mengikuti bahasa game kehidupan Jepang yang
sudah dipakai di seluruh rupa karakter — tapi tiga hal fisis dijaga: zenith
selalu lebih gelap daripada cakrawala di siang hari, malam benar-benar gelap,
dan pendar matahari hangat, tidak pernah magenta.

## 2. Fajar dimulai dari tengah malam

`_sky_palette()` memetakan `hour < 5.0` ke `lerp(NIGHT, DAWN, hour / 5.0)`.
Jadi pukul 03:00 langitnya sudah **60% fajar** — terukur kejinggaan di tengah
malam. Malam sekarang ditahan penuh sampai 04:12, dan sesudah 21:00 langit
diam di malam penuh alih-alih memulai peralihan kedua dari nol.

## 3. Cahaya adegan tidak pernah sampai ke satu entitas pun

Ini yang terbesar, dan ia menyembunyikan dirinya di balik kode yang benar.

`app.py` menghitung warna matahari dan ambient per jam dengan benar — malam
`sun=(35,48,92)`, `ambient=(28,28,52)` — lalu `_sync_smooth_lighting()`
menyetelnya di node `scene` tiap frame, mengandalkan Panda3D menurunkannya ke
seluruh anak.

Tapi `smooth_shader` mendaftarkan ketiganya di `default_input`, dan Ursina
menyalin tiap `default_input` **ke node entitas** saat shader dipasang
(`Entity.shader_setter`):

```python
for key, value in value.default_input.items():
    self.set_shader_input(key, value)
```

Di Panda3D nilai pada node mengalahkan warisan dari induk. Jadi setiap entitas
terkunci pada `sm_sun_color=(1,05 1,02 0,92)` dan `sm_ambient=(0,45 0,46 0,50)`
— tengah hari — selamanya, dan `scene.set_shader_input(...)` yang dipanggil
tiap frame tidak pernah mengubah apa pun.

Terukur, warna rata-rata tanah di scene farm:

```
jam     03:00       09:00       12:00       22:00
tanah   131,147,16  131,147,16  131,147,16  131,147,16
```

Sama sampai digit terakhir di keempat jam. Langit biru tua malam di atas
rumput seterang tengah hari.

Perbaikannya satu baris yang dihapus: ketiga kunci cahaya dicabut dari
`default_input` supaya tidak dicap ke node, dan dibiarkan datang dari `scene`.

## 4. Lalu malamnya terlalu gelap

Begitu jalurnya dibuka, angka malam lama ternyata dipilih tanpa pernah
terlihat: rumput jatuh ke `21,29,8` pada 22:00 dan hewannya nyaris tidak
terlihat. Komentar di sebelahnya berbunyi *"bukan hitam total"* — klaim yang
tidak pernah bisa salah selama cahayanya memang tidak pernah dipakai.

Dinaikkan ke `sun=(62,82,140)`, `ambient=(54,58,95)`. Terukur sesudahnya:

```
jam     03:00      09:00       18:00      22:00
tanah   43,58,13   120,131,12  120,86,2   39,54,13
```

Malam sekitar sepertiga terang siang — redup, bukan buta. Senja hangat.

---

## Dua cacat probe yang ikut ketahuan

**Kamera game tidak pernah bisa mendongak.** Ronde pertama memberi label
"zenith" pada pita atas frame. Dengan pitch 6° puncak frame cuma ~14° di atas
horizon, jadi kedua kolom mengukur langit yang sama. Menaikkan pitch ke 62°
tidak menolong — kamera selalu memandang pemain, jadi pitch tinggi justru
menghadapkannya ke **tanah** (terukur: seluruh frame jadi rumput `50,157,16`
di setiap jam). Yang benar diukur memang langit yang dilihat pemain, dan
labelnya dibuat jujur; nilai zenith dicetak terpisah dari paletnya.

**Dugaan pertama soal rumput terang salah.** Cahaya adegan di-lerp per frame,
jadi hipotesis pertamanya "probe cuma `step(3)`, lampunya belum menyusul".
Dinaikkan ke `step(90)` — dan tanahnya tetap `131,147,16` persis. Hipotesis itu
mati di situ, dan yang sebenarnya baru ketemu dengan bertanya langsung ke game
shader apa yang dipakai tiap entitas rumput.

---

## 5. Bayangan kontak: satu terkubur, satu melayang setinggi lutut

Diukur siapa yang punya bayangan kontak sama sekali:

```
farm   hewan 6/6 punya   warga 0/4 punya   pemain punya
town   hewan 6/6 punya   warga 0/4 punya   pemain punya
```

Jadi setiap tetangga di desa ini melayang. Alasan kenapa itu buruk sudah
ditulis proyek ini sendiri, di docstring `animal_models._shadow()`: *"di
proyeksi miring ... terlihat melayang dan mata tidak tahu ia berdiri di tile
mana."* Yang berlaku untuk ayam berlaku untuk manusia.

Tapi menambahkannya membuka cacat yang lebih besar. Permukaan rumput ada di
`GROUND_H + 0,04 = 0,24`, dan:

```
bayangan warga  (y lokal 0,02)  ->  y dunia 0,0137   terkubur 23 cm
bayangan pemain (y lokal 0,02)  ->  y dunia 0,92     MELAYANG 68 cm
```

**Bayangan pemain sudah mengambang setinggi lutut sejak lama.** Dua sebabnya
berbeda dan tidak satu pun terlihat dari kode di tempatnya: node actor warga
berskala (manekin dikecilkan 2,35/3,42 = 0,687), sedangkan pemain punya titik
asal di y 0,90.

### Tiga cara yang tampak benar dan ketiganya salah

- Menulis `position=Vec3(0, GROUND_H + 0.045, 0)` di konstruktor warga
  mendarat di y dunia **0,168**, bukan 0,245 — node-nya berskala.
- `Entity.world_y = ...` milik Ursina menulis ke y **LOKAL**: bayangan pemain
  justru naik ke **1,145**.
- `Entity.set_position(render, Vec3(...))` juga bukan API yang dikira —
  bayangannya mendarat di **0,0407**.

Yang dipakai akhirnya `NodePath.setPos(render, ...)` mentah, yang memang
menghitung skala dan induk. Ia dipanggil tiap frame, karena warga yang tidur
dipindah ke `y = GH + 0,15` dan pemain berpindah scene.

Dan letaknya di dalam `player.tick()` juga sempat salah: dipasang di AWAL, ia
mendarat di **0,2269** — 1,3 cm di bawah tutup rumput, terkubur lagi — karena
kode gerak di bawahnya memindahkan pemain sesudahnya dan menyeret bayangannya
ikut. Sekarang di akhir tick.

### Terukur

Bayangan dimatikan lalu dinyalakan dalam SATU frame, tanpa satu langkah pun di
antaranya:

```
pemain      8.630 piksel berubah   tanah 179,126,59 -> 103,78,44
warga arya  2.371 piksel berubah   tanah 166,118,58 ->  98,76,45
```

Sebelum ketinggiannya diperbaiki, bayangan warga yang sama cuma mengubah
**149 piksel** — serpihan di tempat tanahnya kebetulan cekung. Naik 16 kali
lipat untuk warga dan 58 kali untuk pemain.

### Empat cacat probe, semuanya jenis yang sama

Seluruh angka membingungkan di irisan ini datang dari probe, bukan dari game:

- Membandingkan dua PROSES terpisah: diff-nya 28.164 piksel tersebar di
  x 2..899, karena warga dan hewan lain bergerak di antara kedua run.
- Menyelipkan `step()` di antara dua tembakan isolasi: diff jadi 729.545
  piksel, yaitu seluruh adegan.
- Membaca posisi bayangan langsung sesudah memindahkan warga, tanpa satu frame
  pun lewat — nilai basi.
- Memperbesar bayangan sampai 1,85 m untuk "membuatnya terbaca", padahal yang
  salah ketinggiannya: piksel terlihat cuma naik 149 -> 375, karena quad-nya
  memang ada di bawah tanah sepanjang waktu.

---

## 6. Empat tekstur yang isinya pola uji

Dipindai seluruh 73 berkas di `assets/textures`, empat di antaranya bukan
gambar bahan sama sekali:

```
tekstur      rata-rata RGB        isinya
tree_trunk   (  7,5  71,2  37,5)  hitam bergaris HIJAU NEON tegak
tree_leaf    ( 15,7  23,0  38,7)  hitam dengan wajik CYAN dan MAGENTA
dirt         ( 46,2  42,3  60,7)  hitam, garis cyan/magenta/putih acak
grass        ( 44,1  13,6  46,2)  hitam dengan KISI MAGENTA
```

Empat tekstur kayu lain di repo ini semuanya coklat wajar — `boat_wood`
(183,136,86), `chest_wood` (140,96,56), `floor_wood` (155,109,69),
`wood_plank` (130,90,56) — jadi keempatnya memang ganjil, bukan gaya.

Akibatnya terlihat di **setiap frame**. Batang pohon dikalikan tint
`rgb(100,70,40)` menghasilkan ~(3,20,6): hitam kehijauan. Dan kontras
hitam-pekat lawan rumput terang itulah yang memicu aberasi kromatik di
post-process, sehingga muncul garis magenta dan cyan di sekeliling tiap
batang — mudah disalahartikan sebagai "tekstur hilang", padahal ia gejala,
bukan sebabnya.

Ketiganya dibangun ulang oleh `tools/buat_tekstur.py`: deterministik (derau
dari `sin`, bukan `random()`), dengan alasan tiap angka di sebelahnya, dan
kecerahannya dipilih dari perhitungan — tiap tekstur di sini DIKALIKAN tint
entitasnya, jadi tekstur yang terlalu gelap akan hilang berapa pun cahayanya.

### Dan satu regresi yang saya buat sendiri

Versi pertama generator menyimpan PNG bermode **RGB**; seluruh tekstur lain di
repo bermode RGBA. Akibatnya **batang pohon hilang sama sekali dari layar** —
terukur pada frame yang sama persis: kolom hitam ada dengan tekstur lama,
tidak ada dengan yang baru, dan piksel nyaris-hitam di area pohon turun dari
7.256 ke 4.233 bukan karena membaik melainkan karena batangnya lenyap. Dengan
RGBA: 6.357, dan batangnya coklat.

### `grass.png` sudah didokumentasikan cacat, dan perbaikannya sudah ditulis

Kotak hitam bergaris magenta di bawah tiap pohon bukan bayangan, melainkan
UBIN. `world.py` memberi tiap ubin penghalang di luar ruang
`default_tex = 'grass'` — tekstur kisi magenta itu.

Dua komentar di repo sudah menyebutnya, dan salah satunya menuliskan
perbaikannya kata per kata:

> *"Ini TAMBALAN, bukan perbaikan. Perbaikan sebenarnya satu baris di
> `game/world.py` (pakai 'grass_tso'/'sand_ground' sebagai default_tex luar
> ruang). Begitu itu dikerjakan pemilik world.py, seluruh fungsi ini boleh
> dihapus beserta pemanggilnya di props.py."*

Baris itu sekarang ditulis. Menghapus tambalannya saja tidak cukup: ia
memberi ubin penghalang **tutup rumput setinggi tetangganya**, dan tanpa itu
tiap ubin pohon melesak 4 cm dan terbaca sebagai lubang persegi. Jadi cabang
penghalang di `world.py` — yang tadinya cuma mengurus pagar — sekarang
mengurus semua penghalang luar ruang, dan `zone_paint.patch_tile()` beserta
`_TILE_TAMBALAN` di props.py dihapus: satu entity per pohon, tunggul, lentera
dan peti yang tidak perlu lagi ada.
