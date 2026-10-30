---
judul: "Cerita Dua Desa babak 1-2: Dukuh Lawang, Papan Titipan, jalan lama, Lomba"
tipe: sesi
tanggal: 2026-10-30
commit: e90d729
skala: 25 file sumber, +1855 / −44 baris
tags: [sesi]
---

# 2026-10-30 — Cerita Dua Desa babak 1-2: Dukuh Lawang, Papan Titipan, jalan lama, Lomba

## Pesan commit

- Dipindah dari checkout lokal lama (6765f22 babak 1, babak 2 belum
  di-commit) ke PR #15 atas permintaan pemilik. Teks, nama tokoh dan
  tempat ditulis baru
- game/scenes/lawang.py + lawang.json: Dukuh Lawang di ujung timur lereng
  (mountain 29,12-13), kandang kerbau dan kambing, longsor jalan lama
- Tiga warga baru: Kades Hardjo, Mbah Rukmi, Sekar, masing-masing dengan
  dialog hearts_3/5/7/10 dan satu barang favorit
- game/dua_desa.py: titipan harian, Kerukunan, Lomba, dan jadwal khusus
  warga lewat jadwal_npc (dipakai _update_npc_schedules dan
  _aktivitas_jadwal)
- Babak 1: tamu yang dicurigai dua desa, pilih mitra untuk bonus awal.
  Babak 2: Juru Titip, Akar Perselisihan, Satu Tikar, lalu Gotong Royong
  membuka jalan lama Lawang <-> Gua Sang Hyang (dua arah: save lama
  menutupnya lagi)
- Lomba Antar-Desa di SEASONAL_EVENTS (Panas 21): panel lomba masak dan
  panen terbesar
- Ubin PPN = 66 di ujung TILE_IDS: Papan Titipan di town (20,8) dan
  lawang (3,11), terpisah dari Papan Permintaan Warga
- Kartu J: daftar tugas utama tanpa entri ber-'alur', blok Cerita Dua
  Desa di kolom kanan. Peta M punya simpul Dukuh Lawang. Pelacak HUD
  sesudah tutorial hanya membaca tugas utama
- Bugfix: "Ya, berikan." tidak pernah menyerahkan hadiah
  (complete_gift_gifting tanpa pemanggil) -> efek serahkan_hadiah
- Penyesuaian PR #15: titik jadwal Kades di peta town baru, mulut gua di
  (14,3)/(14,4), opsi cerita didahulukan di pie (_PIE_MAKS 8), cache
  perjalanan.rute dibersihkan saat portal jalan lama berubah
- Uji: regress 15/15 scene, 0 pemeriksaan gagal (tampilan 49/49);
  harness Dua Desa 37/37 dan 79/79; scene_export --check 15/16 (swarga
  sudah beda sebelum port ini)

## Berkas yang berubah

| Berkas | + | − |
|---|---:|---:|
| `docs/CERITA_DUA_DESA.md` | +108 | −0 |
| `game/animal_models.py` | +32 | −0 |
| `game/config.py` | +10 | −4 |
| `game/controllers/interaction_controller.py` | +96 | −14 |
| `game/controllers/quest_controller.py` | +215 | −0 |
| `game/controllers/time_controller.py` | +24 | −3 |
| `game/data.py` | +460 | −1 |
| `game/dua_desa.py` | +195 | −0 |
| `game/entities.py` | +9 | −2 |
| `game/panel_kartu.py` | +59 | −4 |
| `game/panels.py` | +165 | −1 |
| `game/scenes/__init__.py` | +30 | −0 |
| `game/scenes/lawang.json` | +67 | −0 |
| `game/scenes/lawang.py` | +201 | −0 |
| `game/scenes/mountain.json` | +9 | −6 |
| `game/scenes/mountain.py` | +15 | −1 |
| `game/scenes/naga_cave.py` | +21 | −0 |
| `game/scenes/props.py` | +29 | −0 |
| `game/scenes/scene_base.py` | +7 | −1 |
| `game/scenes/town.json` | +3 | −2 |
| `game/scenes/town.py` | +5 | −0 |
| `game/state.py` | +19 | −0 |
| `game/tutorial.py` | +6 | −2 |
| `game/world.py` | +7 | −3 |
| `obsidian/40-Bug/Ya, berikan tidak menyerahkan hadiah.md` | +63 | −0 |

## Bukti

<!-- ISI MANUAL. Angka, larian regresi, atau probe — skrip sengaja tidak
     menebak bagian ini. Lihat [[Aturan Pencatatan]]. -->

- Permintaan pemilik: "kenapa kamu edit disini, tolong kembalikan semua
  perkembangan ke karsa-brench di github". Ia lalu memilih memindahkan
  babak 1 dan 2 ke PR #15 di salinan kerja terpisah, menjalankan cek
  wajibnya, dan push langsung ke branch itu.
- Regresi penuh lokal (`PYTHONUTF8=1 python tools/regress.py --offscreen`):
  15/15 scene termasuk lawang, 0 pemeriksaan gagal. Semua baris global
  lulus: tampilan 49/49, lima menit 8/8, sinema/judul 36/36, lore gua 19/19.
- Larian regresi pertama sesudah port: tampilan 48/49. Kartu J menggambar
  ketujuh tahap Dua Desa di daftar tugas utama (0/19), dan barisnya meluber
  keluar kartu. Sesudah daftar disaring dan Dua Desa diberi blok sendiri:
  49/49.
- Harness Dua Desa di luar repo (folder catatan sesi). Tombol dikirim lewat
  EventQueue, dan portal diuji dengan berdiri di ubinnya. Babak 1 37/37,
  babak 2 79/79, dua larian berturut-turut.
- Cek statis babak 1 dan 2 lulus. `tools/scene_export.py --check` 15/16:
  swarga beda dari JSON-nya, dan berkas itu tidak disentuh port ini.
- Hadiah lewat tombol sungguhan: favorit +3 (ikan 1 → 0, hati 0 → 3,1),
  kesukaan biasa +1 → [[Ya, berikan tidak menyerahkan hadiah]].
- Warga berjalan ke Lawang lewat portal (`perjalanan.py`) dan tiba dengan
  kegiatan jadwal Dua Desa ("menggali longsor", "menjadi juri lomba").
  Sebelum `entities.py` memakai `jadwal_npc`, mereka tetap di jadwal biasa.
- Cache `perjalanan.rute` mengikuti graf. Lawang → gua lewat (4,1) saat
  jalan terbuka, lewat lereng sesudah save lama menutupnya, tanpa
  `cache_clear` manual.
- Kartu J dipotret di tiga keadaan (babak 1 awal, babak 2 tahap 4, babak 2
  selesai) dan peta M di dua keadaan, lalu dilihat langsung.

## Yang belum beres

<!-- ISI MANUAL. Ditulis apa adanya, termasuk yang alat ukurnya belum bisa
     dipercaya. -->

- Belum ada baris regresi untuk Cerita Dua Desa. Harness-nya di luar repo,
  jadi [[Ya, berikan tidak menyerahkan hadiah]] belum punya penjaga di
  [[Regresi]].
- Tiga warga baru belum punya model Blender (`npc_<id>.obj`), jadi tampil
  dengan manekin cadangan.
- Ada dua papan berdampingan: Papan Permintaan Warga (PR #15) dan Papan
  Titipan (Dua Desa). Belum diputuskan pemilik apakah digabung.
- Di hari Lomba, pie Kades tepat 8/8 opsi. Satu opsi cerita tambahan akan
  memotong "gombal" diam-diam (`_PIE_MAKS`).
- Di Windows, `tools/regress.py` tanpa `PYTHONUTF8=1` crash sesudah baris
  "sistem sims". Probe anak mencetak cp1252, induk membacanya sebagai
  UTF-8, `r.stdout` jadi None, lalu AttributeError.
- Empat larian di mesin ini berhenti mendadak tanpa traceback:
  - satu harness babak 2 (kode 0);
  - tiga larian regresi (kode 127 sekali, kode 0 dua kali).

  Yang dua terlacak: Panda menerima window-event "jendela tertutup" untuk
  buffer offscreen, lalu `ShowBase.userExit()`. Penyebabnya belum terbukti.
  RAM bebas saat itu 280-440 MB dari 7,9 GB. Larian ulang yang sama lulus
  penuh.
- Rasa dialog dan tata letak Lawang belum dinilai pemilik di layarnya
  sendiri.
- Checkout lokal lama (`karsa-Branch`) masih memegang 6765f22 dan babak 2
  yang belum di-commit. Tidak disentuh.

## Tautan

[[Status Sekarang]] · [[Peta Progres]]
