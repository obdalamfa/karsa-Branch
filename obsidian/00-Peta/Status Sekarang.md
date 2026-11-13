---
judul: Status Sekarang
tipe: peta
diperbarui: 2026-11-13
commit_acuan: 096bb31 (branch ccr-ae8cd761-mj4kbu, PR #15)
regresi: 15/15 scene lulus + semua baris global, gauntlet 20/20, dua desa 154/154, tampilan 74/74, animasi gerak 23/23 (lima menit, majelis batin, buy/sinema, kamera Q/E, lore gua, dua desa, ...)
tags: [moc, status]
---

# Status Sekarang

> [!success] Pembaruan 2026-11-13 (sore) — gauntlet hijau 20/20
> `gauntlet/check.py` gagal di tiga titik yang tidak ada hubungannya dengan
> kode yang sedang dikerjakan: ketiganya assertion yang memaku angka/rumus
> lama sementara kodenya berubah sah. Diperbaiki dengan mengukur invarian
> aslinya, bukan melonggarkan batas: warna kristal diperiksa sebagai hasil
> kali entity × vertex terpanggang (palet lama memuncak 1,0493 → terpotong;
> palet baru 0,9936), palet editor menuntut satu warna per jenis ubin
> (15 properti `props.py` dulu jatuh ke abu-abu anonim), dan daftar scene
> dibandingkan dengan `SCENE_BUILDERS` + tiap scene harus benar-benar bisa
> dimuat. Uji suntik membuktikan assertion palet menggigit. Gauntlet
> **20/20**, regresi **15/15 scene, 0 gagal**, boot 5,4 detik
> → [[2026-11-13 — Gauntlet- tiga assertion basi dibalikkan ke invarian aslinya]].

> [!success] Pembaruan 2026-11-13 — baris regresi "dua desa"
> Logika Cerita Dua Desa tidak pernah menyentuh layar, jadi tidak ada scene
> yang bisa menangkapnya kalau rusak. Kini ada `tools/probe_dua_desa.py`
> (154 pemeriksaan) dan baris `dua desa` di `tools/regress.py`. Yang diuji
> nilai, bukan angka salinan: imbalan 1,25–1,35× harga Warung untuk 19
> titipan, nilai lawan di dalam rentang + naik ketat tiap tahun, emas
> sebagai selisih. Strings yang dilihat pemain (`baris_lomba`,
> `pesan_pagi`, pesan kilat) justru dipatok. Regresi penuh 15/15 scene,
> 0 gagal → [[2026-11-12 — Regresi- baris -dua desa- lewat probe_dua_desa.py]].

> [!success] Pembaruan 2026-11-03 (malam) — kuburan berpenghuni, mob terbaca
> Kuburan Tua punya kemamang (malam) dan tuyul untuk tahap Misteri Kuburan.
> [F8] mengatur dua penunjuk. Mob penyerang kini punya papan nama dan HP
> billboard, aura, cincin ancaman seukuran jangkauan pukulan, angka
> kerusakan, dan gaya serang per jenis (termasuk terjangan). Regresi 15/15,
> "tampilan" 74/74, "animasi gerak" 23/23.

> [!success] Pembaruan 2026-11-03 (sore) — penunjuk lengkap
> Penunjuk emas kini juga menunjuk Pak Budi di Bengkel, bijih yang kurang,
> lawan terdekat, dan bos di dungeon, serta makhluk liar yang sungguh bisa
> ditangkap. Penunjuk kedua biru-hijau menuntun Cerita Dua Desa (Kades,
> Mbah Rukmi, papan titipan, longsor). Temuan desain: Kuburan Tua tidak
> punya makhluk untuk tahap "Misteri Kuburan". Regresi 15/15, "tampilan"
> 69/69.

> [!success] Pembaruan 2026-11-03 (siang) — penunjuk ke tugas utama
> Sesudah tutorial, penunjuk emas mengikuti tugas utama: Bengkel, tangga Gua
> Sang Hyang dan tangga tiap lantai dungeon, Kuburan Tua, sarang Naga. Dari
> dungeon ke luar ia menunjuk tangga naik. Regresi 15/15, "tampilan" 62/62.

> [!success] Pembaruan 2026-11-03 — tebing tembus pandang
> Keputusan pemilik: tebing lereng gunung (dan mulut gua) memudar tembus
> pandang saat menghalangi kamera, lalu kembali pejal. Pemain kini terlihat
> dari 12/12 posisi × sudut yang dulu tertutup sampai ~85%. Regresi 15/15,
> "tampilan" 56/56.

> [!success] Pembaruan 2026-11-02 — penunjuk tujuan tutorial
> Tiap langkah tutorial kini punya penanda emas di dunia (kotak pos, ladang,
> pintu rumah lalu kasur, Peti Kirim) dan panah di tepi layar saat target di
> luar pandangan atau di scene lain. Regresi 15/15, baris "tampilan" 55/55.

> [!success] Pembaruan 2026-10-30 (malam) — Cerita Dua Desa babak 1-2 masuk PR #15
> Atas permintaan pemilik ("kembalikan semua perkembangan ke karsa-brench di
> github"), babak 1-2 dipindah dari checkout lokal lama ke branch ini:
> - Dukuh Lawang di ujung timur lereng, dengan tiga warga baru: Kades Hardjo,
>   Mbah Rukmi, dan Sekar.
> - Pilihan desa mitra, Papan Titipan, dan Kerukunan.
> - Gotong royong yang membuka jalan lama ke Gua Sang Hyang.
> - Lomba Antar-Desa (Panas 21).
>
> Kartu J punya blok Cerita Dua Desa, dan peta M punya simpul Dukuh Lawang.
> "Ya, berikan." kini benar-benar menyerahkan hadiah
> → [[Ya, berikan tidak menyerahkan hadiah]]. Regresi 15/15, 0 gagal.
> Terbuka: Dua Desa belum punya baris regresi, dan warga baru belum
> bermodel Blender.

> [!success] Pembaruan 2026-10-30 — panel Warung dan kawan-kawan berbaris
> Warung, Dapur, Bengkel, Papan, Keinginan, dan Ekosistem kini digambar per
> baris: nomor berkeping, ikon, kolom lurus, dan pil SIAP/KURANG. Bengkel
> bertab, sehingga Perahu Kayu (dulu nomor [10], tak terjangkau) akhirnya
> bisa dibuat → [[Perkakas bengkel bernomor 10-14 tak bisa dibuat]].
> Regresi 14/14, baris "tampilan" 49/49.

> [!success] Pembaruan 2026-10-29 — catatan gua terbaca, dasar gua bisa ditinggali
> Atas permintaan pemilik ("masukan ke game terbaru yang ada di github"):
> - Catatan lantai 3/7/12 kini entri LORE_ITEMS. Dulu panel [N] menampilkan
>   `[dungeon_3]` tanpa isi. Fragmen prasasti III pindah dari lantai 14 yang
>   tidak ada ke lantai 13.
> - Catatan gua tampil saat tiba, bukan sesudah tidur. Panel [N] berhalaman
>   (Q/R) dan dibuka di catatan terbaru
>   → [[Catatan gua tanpa isi dan fragmen III di lantai 14]].
> - Pemain yang diam di lantai 13 tidak lagi terlempar balik ke 12
>   → [[Pemain terpantul dari dasar gua]].
>
> Regresi 14/14 + baris baru "lore gua". ~~Terbuka: `gauntlet/check.py` gagal
> di tint kristal gua (1,5 > 1,0), sama persis di 630c805 sebelum perubahan ini.~~
> (lunas 13 Nov: warna yang tampil diukur sebagai hasil kali, palet diturunkan)

> [!success] Pembaruan 2026-10-26 — HUD, menu, menu jeda, kotak putih
> Panel I/J/M/H/P/N/F1 kini kartu bergaya layar judul:
> - Jurnal punya daftar tahap dan kartu "sedang dikerjakan".
> - Peta dibaca dari portal; peta ASCII lama salah sambung.
> - Hubungan memakai potret dan hati.
> - Inventori bergrid dan bisa dinavigasi.
>
> ESC membuka menu jeda. HUD memakai bilah kapsul HP koral dan energi emas,
> ikon cuaca dan koin, serta kartu tujuan beraksen emas. Dialog maju dengan
> [F]. Kotak putih melayang di kebun ternyata makhluk liar tanpa model →
> [[Makhluk liar tampil sebagai kotak putih]]. Regresi 14/14, baris
> "tampilan" 36/36.

> [!success] Pembaruan 2026-10-23 (malam) — animasi kerja dan mob
> Klip kerja pemain kini dibaur, bukan dibanting. Ada lapisan ancang-ancang,
> hentakan dan ikut-gerak dari pinggang, termasuk untuk panen (bend) yang
> dulu diam. Mob dungeon bernapas, melangkah sesuai wataknya, memerah saat
> ancang-ancang, berkilat saat dipukul, dan mati bertahap 0,6 dtk
> → [[Kilat kena pukul mob tidak pernah terlihat]]. Regresi 14/14 dengan
> baris "animasi gerak" 15/15. Mutasi a–d tertangkap. Pemain kini tersentak
> dan berkedip saat dipukul mob, dan kebal 600 ms tidak lagi hilang dalam
> satu frame → [[Kebal sesudah dipukul mob hilang dalam satu frame]].

> [!success] Pembaruan 2026-10-23 (sore) — layar judul, cerita, menu radial
> `python main.py` kini dibuka layar judul (Lanjutkan / Permainan Baru /
> Panduan / Keluar) dengan kamera mengorbit kebun. Sesudah Buat Karakter
> ada adegan pembuka sinematik. Tiap interaksi pertama punya adegan cerita
> pendek yang ditutup tujuan tutorial berikutnya: surat, cangkul, tanam,
> siram, pagi kedua, peti kirim, warga, ternak, dan tiba di desa, pantai,
> danau, gunung, kuburan. Menu interaksi warga dan barang kini radial ala
> Sims. Regresi 14/14 + baris "sinema/judul" 36/36, CI hijau.

> [!success] Pembaruan 2026-10-23 — empat jalur kerja masuk PR #15
> - **Majelis Batin** pulih (F7), F5/F9 tidak lagi dibajak HotReloader, ESC
>   melewati sinema, Bangun/Beli tidak yatim → [[Majelis Batin hilang di merge 5683e79]].
> - **Gua naga dan hutan lebat** dari `integrasi/satu` (permintaan pemilik).
> - **[Q]/[E] putar kamera 45°**, interaksi [F], tangkap [Shift]+[F]
>   (permintaan pemilik) → [[Interaksi di lapangan terbuka melempar TypeError]].
> - **Pohon Blender** (kelapa, tropis, mati) di beach, town, cemetery; mountain
>   memakai hutan pinus; farm & lake tetap prosedural. Palung farm kembali.
> - **Cahaya**: matahari hangat lawan ambient sejuk, ambient hemisfer, bayangan
>   kontak berbulu, arah matahari per jam. Shadow map ada tapi MATI bawaan
>   (`KARSA_SHADOW=1`; ongkos +22..84% ms/frame).
> Tiap jalur lulus verifikator adversarial (atau temuannya ditutup dengan
> mutasi). Regresi penuh gabungan: 14/14, lima menit 8/8.
> ~~Terbuka: tebing mulut gua menutupi ~85% layar saat tiba di mountain~~ (lunas 3 Nov: tembus pandang)
> (keputusan rupa pemilik); gauntlet buta cahaya baru belum dijalankan.

> [!success] Pembaruan 2026-10-18 — kegagalan farm di mesin lambat terjelaskan
> Bug alat ukur, bukan bug game: `arah_maju` menahan W 40 frame, dan di
> ~115 ms/frame pemain farm menembus portal greenhouse. Sisa cek farm lalu
> mengukur greenhouse (689 entity). Kini cek berhenti di 3 u dan ada jaring
> `scene_tetap` → [[arah_maju terlempar portal di mesin lambat]].
> Sedang dikerjakan paralel (worktree terpisah, tiap hasil diverifikasi
> adversarial): Majelis Batin, pohon Blender, cahaya hangat/sejuk + bayangan.

> [!success] Pembaruan 2026-10-16 — gauntlet Okt selesai
> Regresi 14/14 + baris baru **"lima menit"** (tutorial dimainkan dari game
> baru sampai panen). Diperbaiki minggu ini: cahaya siang-malam di tanah,
> `arah_maju` kini memvonis, `capture.py` memotret dunia, keinginan
> terlihat di HUD, zoom kamera, penanda gua/gapura/dungeon Blender, dan tiga
> bug lima menit pertama ([[Tutorial menyuruh R, cangkul pertama crash]]).
> Belum: suasana visual kalah 0/5 melawan AWL (cahaya terarah, tepi rumput,
> model tanaman); sisa Majelis Batin hilang; pohon Blender belum dipasang.
> Rincian: [[Gauntlet Oktober 2026 — 10 Milestone]].

> [!success] Pembaruan 2026-10-13 — gauntlet M1
> Regresi **kembali 14/14**, tiga larian penuh berturut-turut. Ada dua sebab.
> Pertama, ubin yang dilebur membekukan uniform siang-malam
> ([[Ubin dilebur membekukan cahaya siang-malam]]). Kedua, cek HUD membaca
> keadaan setelah motif meluruh ([[Cek HUD membaca keadaan setelah motif meluruh]]).
> Rencana empat hari ada di [[Gauntlet Oktober 2026 — 10 Milestone]].

> [!warning] Pembaruan 2026-10-05 (branch `integrasi/satu`, commit 17d570b)
> Regresi **tidak lagi 14/14**: swarga gagal `cahaya_global` (sudah gagal sebelum
> 17d570b, belum diselidiki); `hud_terbaca` gagal acak di larian penuh tapi
> lulus per scene. Yang baru berdiri: karakter beragam suku, wajah chibi per
> gender, topi model Blender yang pas ([[Topi diukur dari kepala sebelum diperbesar]]),
> kotak dialog berpotret, jadwal warga lintas scene, layar Buat Karakter.
> Belum: suasana semua scene setara farm, animasi pakai alat, pohon/gua Blender.

> [!success] Regresi sudah dijalankan sungguhan
> **14/14 scene lulus, 0 pemeriksaan gagal** — dua kali: di mesin sesi ini, dan
> di **GitHub Actions** (4 larian, semuanya `success`, artifact bukti 3,28 MB).
> Catatan sebelumnya harus menulis "belum diuji ulang"; sekarang tidak perlu
> lagi, dan jaringnya terpasang sendiri di tiap push.
> Rincian: [[2026-09-22 — Regresi jalan sungguhan, CI dipasang]] ·
> [[2026-09-22 — Merge base, CI terbukti hijau]].

## Yang berdiri, dan buktinya

| Hal | Bukti |
|---|---|
| 14 scene boot, dirender, pemain mendarat di tile sah | larian regresi 2026-09-22 |
| `entity_mesh.py` terbukti berfungsi (16 pemeriksaan) | `_bench/probes/probe_entity_mesh.py` |
| ESC selalu bisa keluar dari mode panel apa pun | cek `bisa_keluar`, lulus di 14 scene |
| Motif waras + benar-benar meluruh | cek `motif_waras`, lulus bebas urutan |
| Save bolak-balik utuh | cek `save_bolak`, lulus di 14 scene |
| **Arah WASD benar di semua yaw** | [[Arah WASD basis sumbu salah]] — diukur di 8 yaw oleh dua probe ter-commit |
| Tidak ada entity bergeometri nol | cek `geom_nol`, lulus di 14 scene |
| Game bisa boot di mesin bersih | [[Font HUD tidak ketemu di mesin bersih]] — diperbaiki |
| Jaring regresi jalan otomatis | `.github/workflows/regresi.yml` |
| Mesin motif TS1 (8 motif, decay, advertising) | [[Motif]] · 9 modul memanggilnya |
| Ternak berakibat: lapar → sakit kalau dilalaikan | [[Ternak]] |
| Alat terlihat di tangan pemain | [[2026-08-26 — Tahap 2 sambungkan modul yatim]] |
| Avatar Vitaboy jalur native C++ (0,288 ms/avatar) | [[Avatar Vitaboy]] |
| **Otonomi NPC hidup** — NPC berjalan ke perabot, motif pulih saat memakai | [[Tahap 5 — Autonomi]] · pemanggil di `game/npc.py:92` |
| CI terbukti hijau di GitHub, bukan cuma di mesin lokal | 4 larian `success` |
| `gauntlet/check.py` 20/20 — dijalankan di mesin sungguhan | larian 2026-11-13, exit 0 |

## Angka terbaru

```
15/15 scene lulus · gauntlet 20/20 · 0 pemeriksaan gagal · boot 5,4 detik
ms/frame  16,2 (house)  →  47,2 (mountain)      [dirender CPU, bukan GPU]
entity     555 (smith)  →  3035 (mountain)
```

Angka ms/frame berasal dari runner tanpa GPU (Mesa software). Ia berguna untuk
**tren antar-commit**, bukan sebagai FPS sebenarnya → [[Tahap 3 — Performa]].

## Yang masih terbuka

| Hal | Berat | Catatan |
|---|---|---|
| 4–29 FPS di mesin pemilik, belum pernah diprofil di GPU | 🔴 | [[Tahap 3 — Performa]] |
| `PLAY.md` menunjuk baris & flag yang sudah tidak ada | 🟡 | [[Utang Teknis]] |

## Yang baru saja lunas

- **Gauntlet 20/20, tiga assertion basi** (13 Nov). Kristal gua diperiksa sebagai warna yang benar-benar tampil (entity × vertex terpanggang), bukan `max(ent.color)*1.5`; palet editor menuntut satu warna per jenis ubin setelah 15 properti `props.py` ternyata jatuh ke abu-abu anonim yang sama; daftar scene editor dibandingkan dengan `SCENE_BUILDERS` dan tiap scene harus bisa dimuat, bukan dipaku 15. Tata letak palet yang dulu `51 // 4` = 12 baris untuk 67 ubin juga bug sungguhan: 5 baris tombol menimpa panel objek → [[2026-11-13 — Gauntlet- tiga assertion basi dibalikkan ke invarian aslinya]].

- **Cerita Dua Desa punya baris regresi** (12 Nov). Harness-nya di luar repo dan tidak punya penjaga, jadi probe berdiri sendiri mengikuti pola `probe_lore_gua.py`. 154 pemeriksaan, nilai bukan angka salinan; regresi penuh 15/15 scene → [[2026-11-12 — Regresi- baris -dua desa- lewat probe_dua_desa.py]].

- **`arah_maju` memvonis** (13 Okt, gauntlet M2). "Kontaminasi antar-scene" ternyata cacat di alat ukurnya sendiri: tabrakan peta membelokkan lintasan, dan arah acuan dibaca dari kamera yang tertinggal. Setelah diperbaiki, 42/42 pengukuran menunjukkan 0°. Rumus lama dipasang kembali → farm/town/house GAGAL 180°.

- **Arah WASD** 🔴 → selesai (kodenya; penjaganya belum). Basisnya membaca komponen `(.x,.y)` padahal bidang mendatar Ursina `(x,z)`; menyimpang sampai 180° dan di yaw 90/270 vektor "kanan" runtuh jadi nol. Diukur di 8 yaw, diperbaiki, dan dijaga pemeriksaan `arah_maju` yang **terbukti gagal** saat bug dipasang kembali → [[2026-10-04 — Arah WASD akhirnya terukur dan diperbaiki]].

- **Tahap 2 — Verifikasi modul yatim**: yatim terakhir `entity_mesh.py` dibuktikan jalan (16 pemeriksaan) dan ditandai jujur di kepala modulnya; tidak disambungkan supaya tidak melompati urutan tahap → [[2026-10-03 — Tahap 2 ditutup, entity_mesh terbukti]].
- **92 `.pyc`**: nol yang masih dilacak — base branch sudah melepasnya.
- **Tahap 5 — Autonomi**: `choose_action()` dan `autonomy_candidates()` akhirnya punya pemanggil di kode game yang hidup. Kerja branch `claude/nice-shamir-93f5de`, masuk lewat merge `342facf` → [[Tahap 5 — Autonomi]].
- **Workflow CI terbukti jalan di GitHub** — tebakan nama paket apt untuk `ubuntu-latest` ternyata benar.

- `requirements.txt` hanya menyebut `ursina`; `pygame` dan `pillow` yang wajib tidak tercantum. Tanpa keduanya game **tidak bisa di-import**, apalagi boot. Sudah dilengkapi.
- Pemeriksaan `motif_waras` mengotori keadaan yang diperiksanya → [[Pemeriksaan motif mengotori keadaan]].
- Font HUD tidak ketemu di mesin bersih → [[Font HUD tidak ketemu di mesin bersih]].

## Langkah berikutnya yang masuk akal

1. Profil di mesin ber-GPU, mulai optimasi aman → [[Tahap 3 — Performa]]. Ini satu-satunya 🔴 yang tersisa, dan ia **butuh mesin pemilik** — tidak bisa dari sini.
2. [[Tahap 4 — Wishes]] — bahan-bahannya kini semuanya terbukti hidup: motif, kandidat objek, antrian, dan autonomi.
3. Perbaiki instruksi Vitaboy di `PLAY.md` yang menyuruh mengedit flag tidak ada → [[Utang Teknis]].
4. Tulis ulang probe yang masih dibutuhkan dari 14 yang hilang → [[2026-10-03 — Probe pertama yang bisa diperiksa]].

Dengan Tahap 5 lunas, [[Tahap 4 — Wishes]] jadi kandidat berikutnya yang paling
mengubah rasa bermain: bahan-bahannya (motif, kandidat objek, antrian) kini
semuanya terbukti hidup.
