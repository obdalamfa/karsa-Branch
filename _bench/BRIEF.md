# Briefing bersama — Ternak & Animasi, Lembah Karsa 3D

Dibaca oleh SEMUA pembangun dan kritikus. Konteksmu segar; ini semua yang
kamu butuh untuk mulai.

## Proyek

`/home/user/karsa-Branch` — farming RPG 3D Python + Ursina/Panda3D.
Branch kerja: `claude/lembah-karsa-livestock-interactions-5s1z13`.
Bahasa komentar/dokumen/teks dalam game: **Indonesia**. Ikuti gaya yang ada:
komentar menjelaskan SEBAB, bukan mengulang kode.

Patokan rasa: **Story of Seasons: A Wonderful Life (remake 2023)**.

## Jalankan apa pun lewat xvfb

Tidak ada layar. Selalu `xvfb-run -a python ...`.
Kalau `panda3d`/`pygame`/`ursina` hilang: `pip install ursina pygame pillow imageio-ffmpeg`.

## Gerbang wajib — tidak bisa ditawar

```
xvfb-run -a python tools/regress.py
```

Harus **14/14 scene lulus, 0 pemeriksaan gagal**, SEBELUM kamu menyentuh apa
pun dan SESUDAH kamu selesai. Potongan yang membuatnya merah **tidak dihitung
selesai**. Jangan pernah melonggarkan atau melewati satu pemeriksaan supaya
hijau — kalau pemeriksaannya sendiri yang salah, katakan, jangan diam-diam
diubah.

## Merekam gameplay sungguhan

```
xvfb-run -a python tools/record.py --out _bench/clips/<nama>.mp4 \
    --scene farm --fps 30 --strip 10 \
    --script "warp:19,5|cam:4.2,14,55|lift:1.5|face:sapi_betsy|wait:20|mark:aksi|pie:sapi_betsy:<aksi>|wait:120"
```

Keluar tiga hal: `.mp4`, `_strip.png` (filmstrip berlabel ms — ini yang bisa
kamu LIHAT dengan Read), dan `_trace.json` (jejak sudut sendi per frame).

Bahasa skrip: `wait:N`, `key:K`, `warp:X,Y`, `face:NPC`, `pie:NPC:AKSI`,
`hour:H`, `cam:DIST,PITCH,YAW`, `lift:H`, `mark:NAMA`, `care:ID|*:TAKARAN:NILAI`,
`pos:NPC:X,Y`, `sepi:ID,ID`.

**Penyiapan keadaan itu wajib.** Aksi perawatan MENOLAK jalan kalau tidak ada
yang perlu dikerjakan, jadi tanpa `care:` rekamanmu berisi penolakan, bukan
aksi:

| aksi | penyiapan |
|---|---|
| `beri_minum` | `care:*:air:8` |
| `gosok` | `care:*:bersih:12` |
| `ambil_hasil` | `care:*:siap:9` (ini menulis ke economy.animal_record, bukan husbandry) |

**Kandang itu sempit.** Enam ekor di petak 9x5, jadi pada kamera sedekat yang
dibutuhkan untuk MELIHAT animasi selalu ada satu ekor yang menutupi pemain.
`sepi:<id>` menyembunyikan hewan lain; `pos:` memindahkan satu hewan. Ini
menata panggung pengambilan gambar, bukan mengubah permainan.

**Jangan merekam jam 7 pagi.** Matahari terbit membakar bingkai jadi putih di
beberapa arah kamera. Pakai `hour:13`. Sudut kamera yang terbukti terbaca:
`cam:5.0,15,95` dan `cam:3.4,7,110`; hindari yaw 170-210 (menghadap matahari).

Kamera baku untuk menilai animasi: `cam:4.2,14,55|lift:1.5`.
Klok dipaksa tetap 1/fps, jadi rekaman bisa diulang persis.

## Mengukur animasi

```
xvfb-run -a python tools/anim_trace.py _bench/clips/<nama>_trace.json
```

Mencetak per sendi: rentang, durasi, **antisipasi** (derajat/ms gerakan
berlawanan sebelum ayunan), **tahanan** (ms pose puncak bertahan), **ikutan**
(overshoot), **ease** (kecepatan puncak / rata-rata; 1,00 = segitiga linier
mati), **stroke** (jumlah sapuan), dan **jeda sekunder** (ms keterlambatan
sendi pengikut terhadap penggerak).

`TIDAK ADA SENDI YANG BERGERAK` berarti aksi itu tidak dianimasikan sama sekali.

Alat ini punya swauji sendiri:

```
python tools/anim_trace.py --swauji
```

Ia mengukur jeda pada sinyal buatan yang jawabannya sudah diketahui, termasuk
sendi yang bergerak BERLAWANAN arah penggeraknya dan sapuan berulang yang
bikin korelasi silang ambigu. Kalau ia tidak `SEMUA LULUS`, jangan percayai
kolom `jeda` sampai itu beres.

### Ambang yang dipakai kritikus

Aksi perawatan ternak yang layak disebut dianimasikan harus, pada sendi
penggeraknya:

| sifat | ambang | kenapa |
|---|---|---|
| rentang | ≥ 25° | di bawah itu tidak terbaca di kamera main |
| durasi | ≥ 900 ms | aksi 350 ms terbaca sebagai kedutan, bukan pekerjaan |
| antisipasi | ≥ 2° dan ≥ 60 ms | tanpa gerak balik, aksi mulai dari nol = kaku |
| tahanan | ≥ 80 ms | pose puncak harus sempat dibaca mata |
| ikutan | ≥ 1,5° | berhenti mati di titik akhir hanya terjadi pada mesin |
| ease | ≥ 1,35 | 1,00 berarti lerp linier; manusia 1,4–2,2 |
| jeda sekunder | ≥ 40 ms pada minimal satu sendi lain | badan/kepala harus telat mengikuti tangan |

Untuk aksi berulang (gosok, perah): `stroke ≥ 4` dan `irama_sd_ms > 8`
(irama 0 = metronom = mesin).

## Perbandingan buta

```
python tools/ab_sheet.py --slice <id> --round <n> \
    --ours _bench/clips/<nama>.mp4 --bar _bench/bar/<patokan>.mp4
```

Menyusun lembar dua baris berlabel cuma A/B dengan urutan diacak; kuncinya
ditulis ke berkas tersembunyi terpisah. **Kritikus tidak boleh membuka kunci.**

Kalau `_bench/bar/` kosong alat ini berhenti dengan kode 3 — itu memang
disengaja. Baca `_bench/bar/STATUS.md` untuk keadaan terkini. Selama klip
patokan belum ada, penilaian jatuh ke ambang angka di atas plus pembacaan
filmstrip; katakan terus terang bahwa itu BUKAN perbandingan buta.

## Mencatat ke halaman progres

Tambahkan satu baris JSON ke `_bench/progress.jsonl`:

```
{"slice":"gosok","round":1,"role":"build","note":"apa yang dibangun"}
{"slice":"gosok","round":1,"role":"judge","verdict":"bar","gap":"celah terbesar"}
```

`role` = `build` | `judge` | `note`. `verdict` = `ours` | `bar`.
Lalu `python tools/progress_page.py`.

## Peta kode yang relevan

| berkas | isi |
|---|---|
| `game/controllers/interaction_controller.py` | `build_pie_options()` menyusun menu; `execute_pie_action()` menjalankannya |
| `game/player.py` | rig voxel (`_pivot_shoulder_l/r`, `_pivot_elbow_l/r`, `_pivot_hip_*`, `_pivot_knee_*`, `_pivot_neck`, `body`), `_play_tool_anim()`, dan blok animasi di `tick()` |
| `game/husbandry.py` | aturan perawatan lengkap (kenyang/air/bersih, sakit, produksi) — **sudah ada tapi belum tersambung ke menu** |
| `game/economy.py` | jalur lama yang DIPAKAI menu sekarang (`animal_record`, `animal_status`, `produce_for`) |
| `game/entities.py` | `EntitiesManager.actors`, NPC/hewan yang dirender |
| `game/animal.py` | AI hewan ternak (`FarmAnimal.update_ai`) |
| `game/panels.py` | HUD, dialog, pie menu |
| `game/data.py` | `ANIMAL_NPCS` — `sapi_betsy` (18,5), `ayam_kuning` (16,5), `kambing_jenggot` (19,6), `domba_woolly` (17,7), `kuda_pegasus` (20,5) di scene `farm` |

Pemain lahir di tile (19,5) di `farm`. Avatar Vitaboy gagal dimuat di
lingkungan ini, jadi rig voxel fallback yang dipakai — dan rig itu yang punya
semua pivot. Animasi harus terlihat di rig itu.

## Keadaan awal yang sudah diukur

`Belai` (aksi ternak yang sudah ada) menghasilkan
`TIDAK ADA SENDI YANG BERGERAK`: ia cuma memunculkan pesan. Itu titik nol.
