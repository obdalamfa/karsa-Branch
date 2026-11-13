---
judul: "Regresi: baris 'dua desa' lewat probe_dua_desa.py"
tipe: sesi
tanggal: 2026-11-12
commit: fbadbfd
skala: 3 file sumber, +702 / −0 baris
tags: [sesi]
---

# 2026-11-12 — Regresi: baris "dua desa" lewat probe_dua_desa.py

## Pesan commit

Logika Dua Desa (game/dua_desa.py + tahap di QuestController) tidak
pernah menyentuh layar, jadi tidak ada scene yang bisa menangkapnya
kalau rusak. Probe berdiri sendiri mengikuti pola probe_lore_gua.py:

- fungsi murni: titipan harian per papan, imbalan, nama peminta, bar,
  nilai lawan, baris dan pilihan lomba, tahap_babak, jadwal NPC,
  pesan pagi
- QuestController langsung: maju_dua_desa, pilih_mitra, kerukunan,
  serahkan_titipan, ikut_lomba, buka_jalan_lama, jadwalkan_gotong

154/154 lulus, exit 0. Yang diuji nilai, bukan angka salinan: imbalan
1,25-1,35x harga Warung untuk semua 19 titipan; nilai lawan di dalam
dasar..dasar+naik+acak dan naik ketat tiap tahun. Imbalan dan hadiah
diperiksa sebagai selisih dari emas awal karena GameState mulai 100G.

regress.py: baris "dua desa" (lebar 14), subproses 600 detik, hanya
saat tidak memfilter scene. Regresi penuh: 15/15 scene, 0 gagal.

## Berkas yang berubah

| Berkas | + | − |
|---|---:|---:|
| `_bench/progress.jsonl` | +1 | −0 |
| `tools/probe_dua_desa.py` | +673 | −0 |
| `tools/regress.py` | +28 | −0 |

## Bukti

<!-- ISI MANUAL. Angka, larian regresi, atau probe — skrip sengaja tidak
     menebak bagian ini. Lihat [[Aturan Pencatatan]]. -->

- `python tools/probe_dua_desa.py` → **154/154 lulus, exit 0**. Probe
  mengimpor `QuestController` (menarik `ursina`, ±1 detik) tetapi tidak
  membuka jendela; `game.sound.play` no-op tanpa perangkat.
- Regresi penuh `python tools/regress.py --offscreen` → **15/15 scene,
  0 pemeriksaan gagal**, baris `dua desa` melaporkan `LULUS 154/154 lulus`,
  exit 0. Tanpa `PYTHONUTF8=1` larian mati sesudah "sistem sims"; itu
  lingkungan, bukan regresi.
- Cakupan: 17 bagian — titipan, imbalan, nama, bar, nilai lawan, baris
  lomba, pilihan lomba, tahap, syarat opsi, jadwal NPC, pesan pagi, maju,
  pilih mitra, kerukunan, serahkan titipan, ikut lomba, buka jalan.
- Yang diuji **nilai, bukan angka salinan**:
  - imbalan setiap titipan 1,25–1,35× harga Warung (19 entri, rasio
    terukur 1,2778–1,3333) — jadi bila tabel harga bergeser, probe ikut
    benar tanpa disunting.
  - nilai lawan di dalam `dasar..dasar+naik+acak`; tahun naik ketat untuk
    masak (`naik` 35 > `acak` 30) dan hanya tidak-turun untuk panen
    (`naik` 60 == `acak` 60), karena di sana undian bisa menutupi kenaikan.
  - emas diperiksa sebagai **selisih** dari `state.gold`, bukan nilai
    mutlak, sebab `GameState` mulai dari 100G.
  - `titipan_hari_ini` diperiksa secara struktural: id yang keluar harus
    himpunan bagian dari kandidat yang dihitung ulang + cocok dengan
    `CROPS[...]['seasons']`. Id hasil `random.sample` tidak dipatok.
  - keragaman roster dilonggarkan (`>=4` id berbeda pada grid beberapa
    hari) supaya tidak bergantung pada perilaku internal `random.sample`.
- Yang **dipatok** justru yang dilihat pemain: `baris_lomba`,
  `pesan_pagi`, dan pesan kilat (`flash_msg`) — supaya perubahan tampilan
  teks tertangkap, bukan cuma perubahan angka.
- Catatan desain: harness Dua Desa hidup di luar repo dan tidak punya
  penjaga, jadi probe ini berdiri sendiri mengikuti pola
  `probe_lore_gua.py` → baris `lore gua`. Rendering panel Dua Desa tidak
  diuji di sini; itu milik probe `tampilan`.

## Yang belum beres

<!-- ISI MANUAL. Ditulis apa adanya, termasuk yang alat ukurnya belum bisa
     dipercaya. -->

- Tiga warga belum punya model Blender: Kades Hardjo, Mbah Rukmi, Sekar.
  Cerita Dua Desa sudah bisa dimainkan, tetapi tiga tokoh utamanya masih
  siluet.
- `gauntlet/check.py` merah pada rona kristal gua: 1,5 > 1,0, merah sejak
  `630c805`. Belum diperbaiki maupun diputuskan ambangnya.
- Dua papan permintaan berdampingan dan belum diputuskan mana yang
  dipertahankan: Papan Permintaan Warga vs Papan Titipan.
- Empat larian regresi lebih awal mati mendadak tanpa traceback (Panda
  offscreen "window closed" → `userExit`); larian ulang yang identik lulus.
  Penyebabnya belum terbukti, jadi hasil regresi masih perlu dicurigai
  saat ia gagal sendiri tanpa jejak.
- `regress.py` menjalankan probe ini hanya saat tidak memfilter scene
  (`if not minta:`), jadi `--scene` tertentu tidak ikut memeriksa Dua Desa.

## Tautan

[[Status Sekarang]] · [[Peta Progres]]
