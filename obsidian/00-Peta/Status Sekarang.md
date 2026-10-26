---
judul: Status Sekarang
tipe: peta
diperbarui: 2026-10-23
commit_acuan: f7e5650 (branch ccr-ae8cd761-mj4kbu, PR #15)
regresi: 14/14 lulus + 10 baris global (tampilan baru) (lima menit, majelis batin, buy/sinema, kamera Q/E, ...)
tags: [moc, status]
---

# Status Sekarang

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
> Terbuka: tebing mulut gua menutupi ~85% layar saat tiba di mountain
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

## Angka terbaru

```
14/14 scene lulus · 0 pemeriksaan gagal · boot 3,6 detik
ms/frame  46,4 (house)  →  119,6 (mountain)      [dirender CPU, bukan GPU]
entity     384 (studio) →   2177 (mountain)
```

Angka ms/frame berasal dari runner tanpa GPU (Mesa software). Ia berguna untuk
**tren antar-commit**, bukan sebagai FPS sebenarnya → [[Tahap 3 — Performa]].

## Yang masih terbuka

| Hal | Berat | Catatan |
|---|---|---|
| 4–29 FPS di mesin pemilik, belum pernah diprofil di GPU | 🔴 | [[Tahap 3 — Performa]] |
| `PLAY.md` menunjuk baris & flag yang sudah tidak ada | 🟡 | [[Utang Teknis]] |

## Yang baru saja lunas

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
