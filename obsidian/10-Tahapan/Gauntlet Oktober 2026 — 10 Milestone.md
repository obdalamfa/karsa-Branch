---
judul: Gauntlet Oktober 2026 — 10 Milestone
tipe: tahapan
dibuat: 2026-10-13
jadwal: Selasa 13 – Jumat 16 Okt 2026, tiap 07.00 & 15.00 WIB
bar: A Short Hike (screenshot/footage rilis), plus regresi 14/14
tags: [tahapan, gauntlet]
---

# Gauntlet Oktober 2026 — 10 Milestone

> [!warning] 14 Okt — bar diganti sementara
> *A Short Hike* tidak bisa diambil dari sesi cloud: kebijakan jaringan menolak
> `store.steampowered.com`, `*.steamstatic.com`, Wikipedia, dan `ashorthike.com`.
> Mulai M4, gauntlet memakai patokan **Story of Seasons: A Wonderful Life**
> yang sudah ada di `_bench/refs/` (9 frame gameplay, gerbang `bar_gate.py`).
> Kalau akses Steam dibuka, `tools/ambil_patokan.py` bisa mengambil frame ASH.

**Bar awal:** *A Short Hike* (adamgryu, 2019). Dibandingkan langsung dari
screenshot/footage rilis, bukan dari deskripsi. Syarat terukurnya:
`python tools/regress.py` 14/14 lulus.

**Cara kerja per milestone:** builder dan kritikus dijalankan sebagai subagen
terpisah dengan konteks segar. Kritikus menaruh capture kita di samping bar
secara buta (label dibuang), memilih mana yang lebih baik, lalu menyebut satu
celah terbesar. Ulangi sampai kita menang. Milestone non-visual tidak diadu
lewat gambar; kritikusnya memvonis dari bukti uji.

**Aturan CLAUDE.md tetap berlaku:** milestone tanpa bukti (larian regresi,
probe `_bench/`, atau angka) tidak dicentang.

| # | Milestone | Definition of done (harus ada bukti) | Status |
|---|---|---|---|
| M1 | Regresi hijau lagi | swarga `cahaya_global` lulus; `hud_terbaca` lulus 3 larian penuh berturut-turut | ✅ 13 Okt — 3 larian penuh 14/14 ([[Ubin dilebur membekukan cahaya siang-malam]], [[Cek HUD membaca keadaan setelah motif meluruh]]) |
| M2 | Penjaga arah WASD memvonis | cek `arah_maju` jadi pemeriksaan gagal/lulus tanpa menuduh scene sehat; terbukti gagal bila bug dipasang kembali | ✅ 13 Okt — 42/42 ukuran 0°, 2 larian penuh 14/14; rumus lama dipasang → farm/town/house GAGAL 180° |
| M3 | Alat capture gauntlet | skrip mengambil capture tiap scene dari jalur asli `app.py` (aturan #2) ke `_bench/gauntlet/`; galeri bar *A Short Hike* tersimpan | ✅ 14 Okt — `tools/gauntlet_capture.py`, 9/9 slug → lembar A/B buta. ⛔ *A Short Hike* diblokir jaringan (403 Steam/Wikipedia/situs resmi); bar diganti patokan AWL yang sudah ada (9/9, `bar_gate.py check` terbuka) |
| M4 | Farm mengalahkan bar | kritikus buta memilih capture farm kita atas *A Short Hike* | 🟥 5 ronde, 0 menang (bar AWL) — ditutup tanpa menang 15 Okt. Lahir: fixture ladang hari-10, petak garapan hangat bergundukan, **zoom kamera roda mouse** (8–24). Celah tersisa: cahaya matahari terarah/bayangan, rumput & bunga di tepi ladang, model tanaman, penanda air → pekerjaan seni besar, lihat nota sesi |
| M5 | Suasana batch 1 setara farm | town, beach, house dan studio menang blind | ⏭️ tidak dikerjakan — ditunda setelah M4 kalah 0/5; tanpa cahaya dunia yang diperbaiki, scene lain hampir pasti kalah dengan alasan sama |
| M6 | Suasana batch 2 setara farm | mountain, lake, cemetery dan swarga menang blind; sisa scene dicatat | ⏭️ tidak dikerjakan — alasan sama dengan M5 |
| M7 | Tahap 4 Wishes — mesin | wish lahir dari motif/hubungan, terpenuhi, dan berakibat; probe menempuh jalur asli | ✅ 15 Okt — mesinnya ternyata sudah ada (e72577b) dan tersambung; yang kurang bukti. `probe_wishes.py` diperbaiki (macet di sinema, 5/11 → 12/12) dan ditambah uji janji→panen `space`→dibayar loop update: 17/17; pembayaran dimatikan → GAGAL. Catatan jujur: wish lahir dari konteks & hubungan (hati NPC), **bukan** dari motif |
| M8 | Wishes terlihat pemain | wish muncul di dialog berpotret/HUD dan lulus cek `hud_terbaca` | ✅ 15 Okt — baris "Keinginan: … 0/5 +N" di pelacak HUD (`wishes.baris_hud`), muncul setelah janji, ikut menghilang saat panel/chargen terbuka, hilang setelah dibayar; probe 20/20, di dalam layar, regresi 14/14. Catatan jujur: tidak lewat dialog berpotret; `hud_terbaca` hanya memeriksa bar, jadi baris ini dijaga probe, bukan regresi |
| M9 | Animasi memakai alat | cangkul, siram dan kapak punya pose yang bisa dibedakan di capture; menang blind atas klip *A Short Hike* | ⏭️ tidak dikerjakan — slot dipakai M7/M8/M10 yang bisa dibuktikan |
| M10 | Pohon & gua Blender + 5 menit pertama | aset pohon/gua terpasang dan punya pemanggil (aturan #4); probe main 5 menit dari layar judul sampai panen pertama | ✅ 16 Okt — `mulut_gua`, `gapura_swarga`, `lubang_dungeon` (0 pemanggil) kini dipasang di portal/tangga oleh `world._pasang_penanda_pintu`, arah & pusat diperiksa di tangkapan. `tools/probe_lima_menit.py` 8/8 dari game baru sampai panen — setelah memperbaiki **3 bug nyata** ([[Tutorial menyuruh R, cangkul pertama crash]]). Regresi 14/14. Catatan: pohon Blender (`pohon_tropis`, kenney) belum dipasang; mulai dari Buat Karakter, bukan layar judul |

## Jadwal

Satu slot = satu milestone. Delapan slot untuk sepuluh milestone, jadi slot
yang selesai lebih awal langsung lanjut ke milestone berikutnya.

| Slot | Target |
|---|---|
| Sel 07.00 | M1 |
| Sel 15.00 | M2 |
| Rab 07.00 | M3 |
| Rab 15.00 | M4 |
| Kam 07.00 | M5 |
| Kam 15.00 | M6 + M7 |
| Jum 07.00 | M8 + M9 |
| Jum 15.00 | M10 + penutupan |

## Penutupan (16 Okt 2026, slot terakhir)

**Hasil: 6 ✅ (M1, M2, M3, M7, M8, M10) · 1 🟥 (M4, 0/5 ronde) · 3 ⏭️ (M5, M6, M9).**

Yang paling berharga ternyata bukan seni, tapi bug yang ditemukan alat ukur
baru:

- tanah tidak ikut siang-malam (ubin dilebur membekukan uniform) — M1
- `capture.py` memotret panel Buat Karakter, bukan dunia — M3
- tutorial menyuruh [R], [E] ditelan menu peti, cangkul pertama crash — M10

Slot penutupan menambahkan `probe_lima_menit.py` ke `tools/regress.py`
(baris "lima menit"), jadi ketiga bug M10 kini dijaga CI.

Pelajaran gauntlet: bar visual (AWL) terlalu jauh untuk diadu sebelum
cahaya dunia diperbaiki. Lima ronde M4 menunjukkan celah yang sama berulang:
cahaya matahari terarah/bayangan, tepi rumput, model tanaman. Itu proyek
sendiri, bukan satu slot.

> [!warning] Terbuka saat penutupan — farm `arah_maju` gagal di mesin sesi
> Empat dari lima larian penuh 16 Okt di mesin sesi: farm termuat **689**
> entity (biasanya 1179) dan `arah_maju` memvonis "yaw270: W menyimpang 157
> deg". Ini terjadi juga dengan `regress.py` versi HEAD (tanpa baris lima
> menit), jadi **bukan** akibat perubahan penutupan. `regress.py farm`
> sendirian lulus (1179). Mesin sesi hari itu ~2× lebih lambat (farm 111–123
> ms/frame, Selasa 63). Sebabnya **belum terverifikasi**. CI GitHub pada commit
> M10 hijau. Langkah berikut: bandingkan isi `scene.children` farm di
> larian penuh vs sendirian.
>
> **Pembaruan 16 Okt 09.04 UTC:** CI GitHub pada commit penutupan (9fab45b,
> sudah termasuk baris "lima menit") **hijau, dua larian**. Kegagalan farm
> hanya muncul di mesin sesi cloud yang lambat. Dugaan kuat: lingkungan,
> tapi sebabnya tetap belum diukur.
>
> **Ditutup 18 Okt — sebab TERUKUR, bug alat ukur:** di ~115 ms/frame, W 40
> frame dengan tabrakan mati membawa pemain farm ~11 u, menembus portal
> greenhouse (25,5) yang berjarak 11,0 u; sisa pemeriksaan farm mengukur
> greenhouse (689 entity; 26,00 u / 157° = lompatan ke tujuan portal).
> Direproduksi dengan `_bench/probes/probe_regress_lambat.py --lambat=50`,
> diperbaiki di 294f869 (berhenti di 3 u + jaring `scene_tetap`). Lihat
> [[arah_maju terlempar portal di mesin lambat]].
