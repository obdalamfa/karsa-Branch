# Lembah Karsa 3D — Standar Desain Aset (Jun 2026)

Target visual: **Disco Elysium × Project Zomboid** — dunia lusuh, palet pudar,
material kusam. Gameplay: farming & life-sim. Standar ini berlaku untuk semua
aset baru dan pass restandarisasi.

## Skala (1 Blender unit = 1 meter; spawn scale=1.0)
Patokan game: `TILE_SIZE=2.0`, `WALL_H=2.8`, `HOUSE_H=3.2`, manusia `1.75`.

| Aset | Tinggi (m) | Aset | Tinggi (m) |
|---|---|---|---|
| ayam 0.50 / jago 0.60 | | tuyul 0.95 (roh anak) | |
| bebek 0.50 / kucing 0.60 | | demit 1.60 / leak 1.90 | |
| kelinci 0.40 / rubah 0.65 | | pocong 1.90 / banaspati 2.00 | |
| kambing 1.00 / domba 1.05 | | kuntilanak 2.20 / wewe 2.30 | |
| sapi 1.50 / kuda 1.85 | | jin 2.50 / bidadari 2.10 | |
| kelelawar 0.50 / tikus_gua 0.80 | | genderuwo 2.60 / dewa 2.60 | |
| NPC manusia 1.70–1.80, anak 1.15 | | naga 4.50 (deity) / srimana galak 3.6 | |

## Palet & Material (muted decay)
- **Saturasi dibatasi**: bake/tekstur di-desaturasi ~40% (S×0.60), highlight
  diturunkan, bayangan diangkat tipis — tidak ada warna permen.
- Kulit manusia: sawo matang pudar `(0.55,0.42,0.32)` ±variasi, JANGAN pink.
- Kain: olive `(0.35,0.36,0.24)`, rust `(0.48,0.28,0.18)`, teal pudar
  `(0.24,0.34,0.34)`, abu-krem `(0.55,0.52,0.44)`, coklat tanah.
- Roughness 0.75–0.95 untuk kain/kulit/kayu; metallic 0 kecuali emas
  dewa (≤0.6) dan logam alat (≤0.35).
- Emissive hanya untuk: mata mob horor, api, artefak sakral.
- Aksen grime: noise scale 14–20, dark=base×0.5, bright=base×1.3 (bake).

## Bentuk & Pose
- Proporsi manusia sedikit memanjang, bahu turun lelah (Disco mood);
  kepala ≈ 1/6.5 tinggi. Hindari chibi.
- Pose siluet jelas dari sudut kamera ¾ atas (gaya Zomboid).
- Setiap karakter bergerak punya `_idle/_walk1/_walk2` (mesh-swap 2 frame).

## Pipeline (lihat memory blender-mcp-workflow)
build → join → export multi-mat → save .blend → UV smart_project →
inject pattern → bake DIFFUSE 1024/2048 → re-export (`path_mode='STRIP'`) →
PNG sedir dengan OBJ → mute pass. Export SELALU ke main repo
`assets/models/` + worktree. `forward_axis='NEGATIVE_Y', up_axis='Z'`
untuk export DAN import.
