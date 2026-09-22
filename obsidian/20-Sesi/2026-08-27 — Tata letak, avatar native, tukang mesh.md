---
judul: Tata letak Stardew/HarvestMoon, jalur avatar native, dan tukang mesh entitas
tipe: sesi
tanggal: 2026-08-27
commit: d8da814
skala: +2.267 / −238 baris, 12 file sumber
tags: [sesi, performa, rupa, tata-letak]
---

# 2026-08-27 — Avatar native 22× lebih murah

Commit `d8da814`. Kerja yang sempat mendarat sebelum agennya dihentikan limit
sesi, plus perbaikan lanjutan. Semua file parse; gerakan diuji **4,65
unit/detik** keempat arah tanpa exception.

## Baru

| File | Baris | Isi |
|---|---:|---|
| `game/entity_mesh.py` | 458 | tukang mesh kosakata rupa entitas, dipisah dari `entity_style.py` yang memegang **angka** |
| `game/scenes/layout.py` | 123 | penataan peta ala Stardew / Harvest Moon |
| `game/scenes/zone_paint.py` | 199 | pewarnaan zona supaya area terbaca fungsinya |
| `docs/TATA_LETAK.md` | 201 | prinsip tata letak yang diekstrak dari peta aslinya |

Semua motif rupa dibangun **datar di bidang XY** karena logonya memang seni
vektor datar; `z` cuma nomor lapisan biar tidak z-fighting → [[Tata Letak Scene]].

## Satu pabrik avatar

`vitaboy_npc.py` / `vitaboy_baked.py` / `animator.py` digabung jadi **satu**
pabrik yang memilih `Character` Panda3D (skinning C++) kalau tersedia, dan
jatuh ke skinning Python kalau tidak. Pemain memakai jalur yang sama dengan NPC
supaya tidak ada dua kebenaran. Angkanya:

```
frame kosong (tanpa avatar)      9,34 ms
8 NativeAvatar                  11,64 ms  →  0,288 ms per avatar
8 VitaboyAvatar                 60,43 ms  →  6,387 ms per avatar
```

**22× lebih murah per frame** → [[Avatar Vitaboy]].

## Basis arah gerak dirombak

`player.py` mengambil basis arah dari vektor hadap kamera milik Panda3D
(`getQuat(render).getForward()`), bukan dari selisih posisi kamera–pemain yang
tandanya disetel empiris. Versi lama rapuh: begitu ada yang menyentuh kamera,
keempat arah WASD terbalik lagi — dan itu sudah terjadi dua kali.

## Yang belum beres, jujur dicatat

- **Arah WASD masih belum terverifikasi benar.** Probe proyeksi layar menghasilkan angka yang saling bertentangan (W dan S sama-sama "atas"), jadi **alat ukurnya** yang tidak bisa dipercaya, bukan kodenya → [[Arah WASD belum terverifikasi]].
- Ditemukan tapi belum diperbaiki di sesi ini: `player.tick()` hanya dipanggil kalau `panels.mode == 'hud'` → [[Pemain beku saat panel terbuka]].
- `entity_mesh.py` mendarat **tanpa pemanggil** → [[Utang Teknis]].

## Tautan

Berikutnya: [[2026-08-27 — Dua jebakan pembeku pemain]]
