# 🌾 Lembah Karsa 3D

Farming RPG Nusantara dalam **3D** menggunakan Python + Ursina Engine.
Terinspirasi gameplay **Rune Factory 4** — kamera fixed isometric, combat action, farming harian.

---

## 🚀 Cara Menjalankan

```bash
# 1. Install Ursina Engine
pip install ursina

# 2. Masuk ke folder
cd lembah_karsa_3d

# 3. Jalankan
python main.py
```

> **Catatan:** Ursina membutuhkan Python 3.8+ dan Panda3D (otomatis terinstall bersama ursina).

---

## 🎮 Kontrol

### Gerakan
| Tombol | Aksi |
|--------|------|
| **WASD** / **Arrow** | Bergerak |
| **SHIFT** (tahan) | Lari (1.7×) |

### Aksi
| Tombol | Aksi |
|--------|------|
| **SPACE** | Pakai alat aktif |
| **E** | Bicara / Interaksi |
| **Z** | Serang (butuh pedang) |
| **F** | Tangkap makhluk liar |
| **T** | Tidur — hanya di rumah |
| **1–8** | Pilih alat |
| **Q / R** | Ganti benih (maju/mundur) |

### Panel
| Tombol | Panel |
|--------|-------|
| **I** | Inventori |
| **J** | Quest Log |
| **M** | Peta Dunia |
| **H** | Hubungan NPC |
| **ESC** | Tutup panel |

### System
| Tombol | Aksi |
|--------|------|
| **F5** | Simpan game |
| **F9** | Muat game |
| **F1** | Bantuan kontrol |

---

## 🎨 Perbedaan dari Versi 2D

| Fitur | 2D (v17) | 3D (ini) |
|-------|----------|----------|
| Rendering | Pygame sprite | Ursina 3D entities |
| Kamera | Top-down 2D | Fixed isometric (RF4 style) |
| Player | Pixel art 16×16 | Blocky humanoid 3D |
| NPC | Sprite 4-dir | Blocky 3D + nama floating |
| Tanaman | Sprite 2D | Sphere 3D growing |
| Lighting | Flat 2D | Ambient + Directional |
| Cave | 2D tiles | 3D cave walls + ore crystals |

---

## 🗺️ Dunia

12 scene yang bisa dikunjungi:
- **Kebun Paman Arsa** — lahan pertanian, kandang ternak, rumah
- **Desa Karsa** — warung, klinik, studio, bengkel, rumah kaca
- **Lereng Gunung** — hutan, entrance ke gua naga
- **Danau Karsa** — dermaga, perahu, eceng gondok
- **Kuburan Tua** — nisan, pohon mati, makhluk halus
- **Gua Sang Hyang** — tempat naga tidur, entrance dungeon
- **Gua Bertingkat** — 15 level roguelike dengan ore & mob

---

## 🌿 Sistem Farming

1. Pilih alat **Cangkul** → tekan SPACE di depan tanah (G/D)
2. Pilih **Siram** → siram tanah yang sudah dicangkul
3. Pilih **Tanam** + benih → tanam benih
4. Tunggu beberapa hari (tidur T) → panen dengan **Panen**

**8 tanaman**: Lobak, Wortel, Stroberi, Jagung, Tomat, Labu, Bayam, Jamur

---

## ⚔️ Sistem Combat (Rune Factory style)

- Crafting pedang di **Bengkel Budi** (butuh mineral)
- **Z** = ayun pedang (radius 1.5 tile)
- Mob di dungeon chase player dalam range 6-8 tile
- 7 jenis mob + Boss Naga di level 15
- KO → respawn di rumah dengan penalti energi

---

## 📦 Struktur Kode

```
lembah_karsa_3d/
├── main.py              ← Entry point (2 baris)
├── requirements.txt     ← ursina
└── game/
    ├── config.py        ← Konstanta 3D + tile IDs
    ├── data.py          ← NPC, crop, quest, mob data
    ├── state.py         ← GameState + save/load JSON
    ├── scenes.py        ← Tile map 2D → dirender 3D
    ├── world.py         ← 3D tile renderer (World3D)
    ├── player.py        ← Player controller 3D
    ├── entities.py      ← NPC/mob/wild AI + visuals
    ├── panels.py        ← HUD + dialog + panel UI
    ├── dungeon.py       ← Procedural dungeon generator
    └── app.py           ← Main Ursina app + game loop
```

---

Selamat bertani di Lembah Karsa! 🌾✨
