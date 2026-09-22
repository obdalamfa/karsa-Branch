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
