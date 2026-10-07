---
judul: Status Sekarang
tipe: peta
diperbarui: 2026-10-07
commit_acuan: 342facf (merge base + kerja sesi 2026-09-22)
regresi: 14/14 lulus — lokal DAN di CI GitHub (2026-09-22)
tags: [moc, status]
---

# Status Sekarang

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
