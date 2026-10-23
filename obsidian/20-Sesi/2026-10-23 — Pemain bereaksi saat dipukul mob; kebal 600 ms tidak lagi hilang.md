---
judul: "Pemain bereaksi saat dipukul mob; kebal 600 ms tidak lagi hilang"
tipe: sesi
tanggal: 2026-10-23
commit: 1e32d74
skala: 4 file sumber, +123 / −1 baris
tags: [sesi]
---

# 2026-10-23 — Pemain bereaksi saat dipukul mob; kebal 600 ms tidak lagi hilang

## Pesan commit

Player.tick menimpa s.invuln_timer_ms (ditulis mob.py) dengan _invuln
yang selalu 0, jadi kebal hilang di frame berikutnya dan kedip merah tak
pernah menyala. Kedipnya pun mewarnai self.body, Entity kosong pada rig.

- kebal diambil dari state dulu; pukulan baru menyalakan jus 'kena'
  (tersentak, gepeng, dorongan kamera)
- kedip merah di CharActor.poros
- probe_gerak: 3 cek baru lewat AI mob sungguhan (15/15); mutasi
  sinkron dimatikan -> 3 GAGAL

## Berkas yang berubah

| Berkas | + | − |
|---|---:|---:|
| `game/jus_gerak.py` | +13 | −1 |
| `game/player.py` | +16 | −0 |
| `obsidian/40-Bug/Kebal sesudah dipukul mob hilang dalam satu frame.md` | +56 | −0 |
| `tools/probe_gerak.py` | +38 | −0 |

## Bukti

<!-- ISI MANUAL. Angka, larian regresi, atau probe — skrip sengaja tidak
     menebak bagian ini. Lihat [[Aturan Pencatatan]]. -->

- Diukur lebih dulu lewat jalur asli: genderuwo dipasang di sebelah pemain
  di dungeon dan AI-nya dibiarkan memukul. Sebelum perbaikan,
  `invuln_timer_ms` 600 → 0 di frame berikutnya dan `player._invuln` tetap 0.
  Sesudahnya kebal turun 544 → 486 → 428 … → 0 dalam 0,6 dtk.
- `tools/probe_gerak.py`: 15/15. Tiga cek baru: kebal bertahan, tersentak
  (P maks 14,6), dan kedip merah.
- Mutasi "sinkron dimatikan": 12/15, ketiga cek "kena" GAGAL.
- Regresi penuh lokal: 14/14 scene, 0 pemeriksaan gagal, semua baris global
  lulus ("animasi gerak" 15/15). CI hijau di 1e32d74.

## Yang belum beres

<!-- ISI MANUAL. Ditulis apa adanya, termasuk yang alat ukurnya belum bisa
     dipercaya. -->

- Belum ada dorongan mundur (knockback) pada posisi pemain. Sengaja ditunda
  karena menggeser posisi bersinggungan dengan tabrakan dan portal.
- `combat_controller.py` (dodge, block, receive_damage) masih tanpa
  pemanggil, jadi belum ada dodge/block di permainan.
- Cabang `return` saat pemain terjepit melewati blok kedip, sehingga pemain
  yang terjepit sambil kebal tidak berkedip selama frame itu.
- Keputusan tebing mulut gua di mountain masih menunggu pemilik.

## Tautan

[[Status Sekarang]] · [[Peta Progres]]
