---
judul: Status Sekarang
tipe: peta
diperbarui: 2026-09-22
commit_acuan: 7ed8d59 + kerja sesi 2026-09-22
regresi: 14/14 lulus (dijalankan 2026-09-22)
tags: [moc, status]
---

# Status Sekarang

> [!success] Regresi sudah dijalankan sungguhan
> **14/14 scene lulus, 0 pemeriksaan gagal, boot 3,6 detik** — larian nyata di
> sesi 2026-09-22, bukan angka warisan. Catatan sebelumnya harus menulis
> "belum diuji ulang"; sekarang tidak perlu lagi.
> Rinciannya: [[2026-09-22 — Regresi jalan sungguhan, CI dipasang]].

## Yang berdiri, dan buktinya

| Hal | Bukti |
|---|---|
| 14 scene boot, dirender, pemain mendarat di tile sah | larian regresi 2026-09-22 |
| ESC selalu bisa keluar dari mode panel apa pun | cek `bisa_keluar`, lulus di 14 scene |
| Motif waras + benar-benar meluruh | cek `motif_waras`, lulus bebas urutan |
| Save bolak-balik utuh | cek `save_bolak`, lulus di 14 scene |
| Tidak ada entity bergeometri nol | cek `geom_nol`, lulus di 14 scene |
| Game bisa boot di mesin bersih | [[Font HUD tidak ketemu di mesin bersih]] — diperbaiki |
| Jaring regresi jalan otomatis | `.github/workflows/regresi.yml` |
| Mesin motif TS1 (8 motif, decay, advertising) | [[Motif]] · 9 modul memanggilnya |
| Ternak berakibat: lapar → sakit kalau dilalaikan | [[Ternak]] |
| Alat terlihat di tangan pemain | [[2026-08-26 — Tahap 2 sambungkan modul yatim]] |
| Avatar Vitaboy jalur native C++ (0,288 ms/avatar) | [[Avatar Vitaboy]] |

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
| Arah WASD belum terverifikasi benar | 🔴 | [[Arah WASD belum terverifikasi]] — regresi tidak menguji arah |
| 4–29 FPS di mesin pemilik, belum pernah diprofil di GPU | 🔴 | [[Tahap 3 — Performa]] |
| `entity_mesh.py` (458 baris) nol pemanggil | 🟠 | [[Utang Teknis]] |
| `choose_action()` / `autonomy_candidates()` nol pemanggil | 🟠 | [[Tahap 5 — Autonomi]] |
| Workflow CI belum pernah jalan di GitHub | 🟡 | terbukti lewat perintah identik di mesin lokal; larian pertamanya di PR |
| 92 file `.pyc` ter-commit | 🟡 | [[Utang Teknis]] |
| `PLAY.md` menunjuk baris & flag yang sudah tidak ada | 🟡 | [[Utang Teknis]] |

## Yang baru saja lunas

- `requirements.txt` hanya menyebut `ursina`; `pygame` dan `pillow` yang wajib tidak tercantum. Tanpa keduanya game **tidak bisa di-import**, apalagi boot. Sudah dilengkapi.
- Pemeriksaan `motif_waras` mengotori keadaan yang diperiksanya → [[Pemeriksaan motif mengotori keadaan]].
- Font HUD tidak ketemu di mesin bersih → [[Font HUD tidak ketemu di mesin bersih]].

## Langkah berikutnya yang masuk akal

1. Tunggu larian CI pertama di PR — kalau merah, itu pekerjaan berikutnya.
2. Sambungkan atau tandai `entity_mesh.py` → menutup [[Tahap 2 — Verifikasi modul yatim]].
3. Bangun probe arah yang kokoh, baru sentuh tanda WASD → [[Arah WASD belum terverifikasi]].
4. Profil di mesin ber-GPU, mulai optimasi aman → [[Tahap 3 — Performa]].
