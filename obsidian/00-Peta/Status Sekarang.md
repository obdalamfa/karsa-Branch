---
judul: Status Sekarang
tipe: peta
diperbarui: 2026-10-07
commit_acuan: 8f5da30 (merge base 250 commit, 2026-10-07)
regresi: 10/14 lulus — diukur di pohon hasil merge 8f5da30 (2026-10-07)
tags: [moc, status]
---

# Status Sekarang

> [!caution] Regresi 10/14 — diukur 2026-10-07 di pohon hasil merge `8f5da30`
> **10/14 scene lulus, 4 pemeriksaan gagal, exit 1.** Dua jenis, dan bedanya penting:
>
> - **Nyata**: `cahaya_global` gagal di `beach` dan `swarga` — deterministik,
>   gagal juga saat keempat scene diuji sendiri. Base menandai swarga "belum
>   diselidiki"; **`beach` tidak disebut nota base sama sekali**.
> - **Tuduhan palsu**: `hud_terbaca` gagal di `house` dan `naga_cave` di larian
>   14 scene, lalu **lulus** di larian 4 scene →
>   [[Pemeriksaan HUD membandingkan tangkapan lama]].
>
> Keempatnya **bukan** bawaan merge: CI base branch sendiri sudah merah di
> `3877418` pada 20:03:20 UTC, sembilan menit sebelum commit merge ini ada.
> Ditulis di [komentar PR #13](https://github.com/obdalamfa/karsa-Branch/pull/13#issuecomment-6046083991).
>
> Yang tetap berdiri setelah merge: `arah_maju` **LULUS** di kedua larian
> (W=atas, S=bawah, A=kiri, D=kanan), termasuk terhadap basis arah baru yang
> base tulis di `player.py:890`. `otonomi_hidup` LULUS, `sims_tersambung` LULUS.

> [!info] Riwayat: pernah 14/14
> Klaim "14/14 lulus, dua kali, lokal dan di CI" benar untuk commit `342facf`
> (2026-09-22) dengan 6 pemeriksaan → [[2026-09-22 — Regresi jalan sungguhan, CI dipasang]].
> Base sejak itu menambah 12 pemeriksaan baru, dan empat di antaranya berbunyi.
> Angka lama tidak dihapus, tapi ia **bukan** status hari ini.

## Yang berdiri, dan buktinya

| Hal | Bukti |
|---|---|
| 14 scene boot, dirender, pemain mendarat di tile sah | larian regresi 2026-09-22 |
| `entity_mesh.py` terbukti berfungsi (16 pemeriksaan) | `_bench/probes/probe_entity_mesh.py` |
| ESC selalu bisa keluar dari mode panel apa pun | cek `bisa_keluar`, lulus di 14 scene |
| Motif waras + benar-benar meluruh | cek `motif_waras`, lulus bebas urutan |
| Save bolak-balik utuh | cek `save_bolak`, lulus di 14 scene |
| **Arah WASD benar di semua yaw** | [[Arah WASD basis sumbu salah]] — diukur di 8 yaw, dijaga cek `arah_maju` yang terbukti berbunyi saat bug dipasang |
| Tidak ada entity bergeometri nol | cek `geom_nol`, lulus di 14 scene |
| Game bisa boot di mesin bersih | [[Font HUD tidak ketemu di mesin bersih]] — diperbaiki |
| Jaring regresi jalan otomatis | `.github/workflows/regresi.yml` |
| Mesin motif TS1 (8 motif, decay, advertising) | [[Motif]] · 9 modul memanggilnya |
| Ternak berakibat: lapar → sakit kalau dilalaikan | [[Ternak]] |
| Alat terlihat di tangan pemain | [[2026-08-26 — Tahap 2 sambungkan modul yatim]] |
| Avatar Vitaboy jalur native C++ (0,288 ms/avatar) | [[Avatar Vitaboy]] |
| **Otonomi NPC hidup** — NPC berjalan ke perabot, motif pulih saat memakai | [[Tahap 5 — Autonomi]] · pemanggil di `game/npc.py:92` |
| CI terbukti hijau di GitHub, bukan cuma di mesin lokal | 4 larian `success` |
| 15 scene sebagai DATA, dan datanya tidak menyimpang dari kode | `tools/scene_export.py --check` 15/15 + `tools/scene_roundtrip.py` 15/15, dijalankan 2026-10-07 → [[Peta Sistem Konten]] |
| 36 NPC semuanya punya jadwal, 36 portal semuanya dua arah | pembacaan data 2026-10-07 → [[Peta Sistem Konten]] |

## Angka terbaru

```
10/14 scene lulus · 4 pemeriksaan gagal · boot 15,0 detik   (2026-10-07, 8f5da30)
ms/frame  28,9 (house)  →   71,5 (beach)         [dirender CPU, bukan GPU]
entity     424 (smith)  →   2097 (mountain)
```

Boot melonjak 3,6 → 15,0 detik sesudah merge: 497 model baru di `assets/`.
Belum diselidiki, dan belum tentu masalah — ia diukur sekali, di runner tanpa
GPU.

Angka ms/frame berasal dari runner tanpa GPU (Mesa software). Ia berguna untuk
**tren antar-commit**, bukan sebagai FPS sebenarnya → [[Tahap 3 — Performa]].

## Yang masih terbuka

| Hal | Berat | Catatan |
|---|---|---|
| 4–29 FPS di mesin pemilik, belum pernah diprofil di GPU | 🔴 | [[Tahap 3 — Performa]] |
| `PLAY.md` menunjuk baris & flag yang sudah tidak ada | 🟡 | [[Utang Teknis]] |
| `cahaya_global` gagal di `beach` dan `swarga` — cahaya scene tidak sampai ke dunia | 🔴 | deterministik, lolos urutan; base menandainya belum diselidiki dan tidak menyebut `beach` |
| `hud_terbaca` menuduh palsu tergantung urutan scene | 🟠 | [[Pemeriksaan HUD membandingkan tangkapan lama]] — tambalan sudah diusulkan, belum dipasang |
| 16 dari 24 benih tidak bisa dibeli — baris tokonya siap tapi tidak dipasang | 🟠 | [[Peta Sistem Konten]] — syaratnya (panel toko berhalaman) sudah ada sejak `panels.py:861` |
| `SEASONAL_EVENTS`, 25 model, `random_stairs_chance()` — konten tanpa pemakai | 🟡 | [[Peta Sistem Konten]] |
| `scene_export.py --check` tidak dijalankan CI maupun `regress.py` | 🟡 | detektor penyimpangan kode↔data digantung tapi tidak dipasang → [[Regresi]] |

## Yang baru saja lunas

- **Arah WASD** 🔴 → selesai, kodenya **dan** penjaganya: cek `arah_maju` memvonis lagi sejak 2026-10-06, diuji dua arah → [[2026-10-06 — Penjaga arah jadi penjaga sungguhan]]. Basisnya membaca komponen `(.x,.y)` padahal bidang mendatar Ursina `(x,z)`; menyimpang sampai 180° dan di yaw 90/270 vektor "kanan" runtuh jadi nol. Diukur di 8 yaw, diperbaiki, dan dijaga pemeriksaan `arah_maju` yang **terbukti gagal** saat bug dipasang kembali → [[2026-10-04 — Arah WASD akhirnya terukur dan diperbaiki]].

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
5. Pasang `SEED_SHOP_ROWS` ke panel toko yang kini berhalaman — 16 tanaman sudah bermekanika lengkap tapi benihnya tidak bisa dibeli → [[Peta Sistem Konten]].
6. Jalankan `scene_export.py --check` di CI, supaya kode dan data scene tidak bisa menyimpang diam-diam.

Dengan Tahap 5 lunas, [[Tahap 4 — Wishes]] jadi kandidat berikutnya yang paling
mengubah rasa bermain: bahan-bahannya (motif, kandidat objek, antrian) kini
semuanya terbukti hidup.
