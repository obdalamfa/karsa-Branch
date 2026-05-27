# Lembah Karsa 3D — Panduan Bermain

Game RPG cozy bergaya Sims/Stardew Valley dengan setting desa Indonesia.

## Menjalankan

```cmd
cd C:\Users\User\lembah-karsa\3d
python main.py
```

Sistem yang dibutuhkan:
- Python 3.10+
- Windows 10/11 dengan OpenGL driver
- `pip install ursina pygame pillow`

## Kontrol

### Gerakan
| Key | Aksi |
|---|---|
| **W / ↑** | Jalan ke arah utara isometric (atas-layar) |
| **S / ↓** | Jalan ke selatan |
| **A / ←** | Jalan ke barat |
| **D / →** | Jalan ke timur |
| **Shift + WASD** | Lari (menghabiskan energi) |

### Aksi karakter
| Key | Aksi |
|---|---|
| **SPACE** | Pakai alat aktif di tile depan (cangkul, siram, panen, kapak, pickaxe, pedang) |
| **E** | Buka Pie Menu untuk NPC yang menghadap (bicara, beri hadiah, dll.) |
| **Z** | Serang mob (butuh pedang) — auto-attack range 4 unit |
| **F** | Tangkap wild entity (jamur lari, kunang-kunang, dll.) di sekitar |
| **G** | Beri hadiah ke NPC (item aktif di inventori) |
| **V** | Konsumsi item makanan untuk pulihkan HP/Energi |
| **T** | Tidur — hanya di scene `house`, advance ke hari berikutnya |
| **X** | Tandai tile untuk Antrian Aksi |
| **C** | Eksekusi semua Antrian Aksi sekaligus |

### Pilih alat & bibit
| Key | Aksi |
|---|---|
| **1-8** | Slot alat: 1=Cangkul, 2=Siram, 3=Tanam, 4=Panen, 5=Kapak, 6=Hadiah, 7=Pickaxe, 8=Pedang |
| **Q / R** | Cycle bibit untuk ditanam |

### Panel & menu
| Key | Aksi |
|---|---|
| **I** | Inventori — lihat item yang kamu punya |
| **M** | Peta — preview area + lokasi NPC |
| **J** | Quest — tugas yang sedang diambil |
| **H** | Relasi NPC — hearts level + dialog |
| **N** | Catatan Lembah — fragmen cerita dan lore yang ditemukan |
| **K** | Toko (hanya di Warung Bu Sari di `shop`) |
| **U** | Kerajinan (hanya di Bengkel Budi di `smith`) |
| **F1** | Bantuan kontrol |
| **F2** | Chargen — ubah penampilan |
| **F5** | Simpan game |
| **F9** | Muat dari save terakhir |
| **ESC** | Tutup panel aktif |

## Jadwal Hari

- 1 hari nyata ≈ 15 menit real (900 detik)
- Jam 23:00 game memaksa kamu tidur (advance hari)
- 1 musim = 28 hari, 4 musim per tahun

## Scene & NPC

### Desa utama
- **farm** — kebun untuk cangkul/tanam/panen. Sari, Arya berkumpul siang.
- **town** — pusat desa dengan rumah-rumah NPC.
- **shop** — Warung Bu Sari, beli/jual item.
- **smith** — Bengkel Budi, kerajinan alat.
- **clinic** — Pak Guru, klinik desa.
- **studio** — Cici, foto/seni.
- **greenhouse** — Ningsih, kebun kaca.
- **house** — Rumahmu, tempat tidur + chest.

### Luar desa
- **lake** — Danau Karsa. Joko mancing. Bebek + kuntilanak (malam).
- **mountain** — Lereng. Pohon untuk kayu + ore vein.
- **cemetery** — Kuburan. Demit Tua + Pocong (malam).
- **naga_cave** — Gua naga + portal dungeon.
- **dungeon** — Procedurally generated dungeon dengan mob + boss Naga.

## Tips Awal

1. **Mulai pagi di rumah** — jam 6, energi penuh.
2. **Datang ke Warung Bu Sari (K)** — beli bibit jagung/lobak (~30G).
3. **Pergi ke farm** — pakai Cangkul (1+SPACE) untuk tanah, Tanam (3+SPACE), Siram (2+SPACE).
4. **Bicara dengan NPC** (E) untuk naik hearts → buka dialog cerita.
5. **Tidur jam 22** (T di rumah) — tanaman bertumbuh saat hari berikutnya.
6. **Save sering** (F5) — terutama sebelum masuk dungeon.

## Quests Awal

Tugas pertama otomatis terdaftar di **J** (Quest panel):
1. Bicara dengan Sari di farm
2. Tanam 3 bibit jagung
3. Panen + jual ke Warung Bu Sari

## Troubleshooting

### Game stuck di lake
**Fixed** di [player.py:610](game/player.py:610) — portal cooldown 0.8s. Kalau masih stuck, lepas WASD sebelum cross portal.

### Layar hitam saat boot
Cek pipeline OpenGL — jalankan `python main.py` dari command prompt, lihat output `Known pipe types: wglGraphicsPipe`. Kalau `dxgsg9` muncul, GPU driver belum support OpenGL — update driver.

### NPC tidak muncul
Cek `lembah_karsa_3d_save.json` corrupt — hapus file ini, game akan re-init dari awal.

### Performance lambat
- Buka help panel (F1) → lihat scene saat ini
- Coba pindah ke scene lebih kecil (`house`)
- Pastikan tidak ada window background heavy lainnya

## Files Penting

- `lembah_karsa_3d_save.json` — save file
- `assets/` — texture + sound assets
- `assets/vitaboy/` — baked Vitaboy avatar GLB (opsional, off by default)
- `game/` — source code Python

## Mengaktifkan Vitaboy NPC (eksperimen)

Edit [game/entities.py:736](game/entities.py:736):
```python
_USE_VITABOY_HUMANS = True   # ganti dari False
```

Catatan: saat ini bake cuma body (tanpa kepala/tangan). NPC akan tampak aneh. Tunggu Phase 11 (full appearance assembly via .apr/.bnd) untuk hasil utuh.

Untuk bake ulang animasi atau warna:
```cmd
bash tools/bake_all.sh
ANIM=a2o-soc-greet-bow1 SUFFIX=greet bash tools/bake_all.sh
```

## Generate Texture Baru

Mau ubah palette tembok/lantai? Edit `tools/gen_textures.py`, lalu:
```cmd
python tools/gen_textures.py
```

Output otomatis ke `assets/`. Restart game untuk lihat hasilnya.
