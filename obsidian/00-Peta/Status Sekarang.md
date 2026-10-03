---
judul: Status Sekarang
tipe: peta
diperbarui: 2026-09-22
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
| Arah WASD belum terverifikasi benar | 🔴 | [[Arah WASD belum terverifikasi]] — regresi tidak menguji arah |
| 4–29 FPS di mesin pemilik, belum pernah diprofil di GPU | 🔴 | [[Tahap 3 — Performa]] |
| `entity_mesh.py` (458 baris) nol pemanggil | 🟠 | [[Utang Teknis]] |
| 92 file `.pyc` ter-commit | 🟡 | [[Utang Teknis]] |
| `PLAY.md` menunjuk baris & flag yang sudah tidak ada | 🟡 | [[Utang Teknis]] |

## Yang baru saja lunas

- **Tahap 5 — Autonomi**: `choose_action()` dan `autonomy_candidates()` akhirnya punya pemanggil di kode game yang hidup. Kerja branch `claude/nice-shamir-93f5de`, masuk lewat merge `342facf` → [[Tahap 5 — Autonomi]].
- **Workflow CI terbukti jalan di GitHub** — tebakan nama paket apt untuk `ubuntu-latest` ternyata benar.

- `requirements.txt` hanya menyebut `ursina`; `pygame` dan `pillow` yang wajib tidak tercantum. Tanpa keduanya game **tidak bisa di-import**, apalagi boot. Sudah dilengkapi.
- Pemeriksaan `motif_waras` mengotori keadaan yang diperiksanya → [[Pemeriksaan motif mengotori keadaan]].
- Font HUD tidak ketemu di mesin bersih → [[Font HUD tidak ketemu di mesin bersih]].

## Langkah berikutnya yang masuk akal

1. Sambungkan atau tandai `entity_mesh.py` → menutup [[Tahap 2 — Verifikasi modul yatim]]. Ini satu-satunya yang menahan tahap itu.
2. Bangun probe arah yang kokoh, baru sentuh tanda WASD → [[Arah WASD belum terverifikasi]].
3. Profil di mesin ber-GPU, mulai optimasi aman → [[Tahap 3 — Performa]].
4. Lepas 92 `.pyc` dari pelacakan git — commit tersendiri → [[Utang Teknis]].

Dengan Tahap 5 lunas, [[Tahap 4 — Wishes]] jadi kandidat berikutnya yang paling
mengubah rasa bermain: bahan-bahannya (motif, kandidat objek, antrian) kini
semuanya terbukti hidup.
