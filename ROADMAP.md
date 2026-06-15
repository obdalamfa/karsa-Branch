# PROYEK LEMBAH KARSA 1.0 — "Legendaris"

> Target: game **utuh** — tampilan, HUD, dan gameplay yang langsung dimengerti
> dalam 5 menit pertama. Engine: **Ursina/Panda3D** (keputusan final).
> Identitas: farming & sim-life folklore Indonesia, rasa Disco Elysium × Zomboid,
> NPC ala The Sims. Eksekusi: Claude Fable 5, sesi demi sesi, milestone demi milestone.

## Prinsip kerja
1. **Legibility dulu, kedalaman kemudian** — pemain baru harus paham tanpa dijelaskan.
2. Tiap milestone punya *definition of done* yang bisa diverifikasi (capture/checklist).
3. Aset = script idempoten (regenerable); kode = compile + capture sebelum lanjut.
4. Jebakan terdokumentasi di memory (axis Y-up, cache .bam, scene-reset Blender).

## STATUS (per 13 Jun 2026) — ringkas
| Milestone | Progres | Catatan |
|---|---|---|
| **M1** Lima Menit Pertama | **~90%** | judul/intro/tutorial/tracker/prompt/signpost ADA & lulus smoke_boot |
| **M2** Tampilan | **~60%** | skybox+lighting+cuaca ADA; sisa: dress props→tile, tekstur interior |
| **M3** HUD & UX | **~55%** | HUD Disco + needs + **Majelis Batin** ADA; sisa: ikon item, pause/settings, save-slot UI |
| **M4** Gameplay core | **~55%** | crafting+laut, upgrade alat, **tani Sakuna mendalam** ADA; sisa: shipping bin, ternak produktif, balance, audit quest |
| **M5** Animasi & kehidupan | **~40%** | walk mesh-swap 2-frame + pose aksi ADA; sisa: 4-frame, schedule penuh, telegraph mob, ambient satwa |
| **M6** Audio | **~30%** | sound.py + ambient scene ADA; sisa: SFX/musik lengkap, game-feel |
| **M7** Rilis | **0%** | belum |

**BONUS lintas-milestone yang sudah jadi (di luar rencana awal):**
- **Majelis Batin** — 4 suara batin (BARA/AKAR/SUKMA/LAPAR) + skill-check 2d6 white/red (TAB) — DNA Disco, di-port dari prototipe three.js
- **Tani Sakuna mendalam** — jadwal air muda-basah/menua-kering, nutrisi, gulma → mutu ★1-5 → hasil & harga
- **Kamera third-person** diperbaiki (lebih dekat, sudut lebih baik, smoothing stabil)
- **Petapa Srimana 2 wujud** (kalem → galak saat interaksi), **Kapal Kurofune + Mercusuar**, **crafting + pelayaran**
- **Prototipe web three.js** terpisah (`lembah karsa html/lembah_karsa_3d.html`) — cel-shade, terverifikasi jalan

> Pola nyata: kita kerja per-FITUR (sesuai mood/permintaan), bukan M1→M7 berurutan.
> Itu OK — tapi untuk "game utuh" perlu menutup celah *legibility* (M1 selesai) lalu
> *kelengkapan loop* (M4: shipping bin + ternak) supaya ada alasan main berhari-hari.

## Sumber daya FreeSO/TSO (sudah ter-port: `game/vitaboy/`, GPL v3)
- Lokasi: `E:/Documents/Panda demo/panda_atb_demo/FreeSO/` + `E:/Download/The Sims Online/TSOClient`
- **Yang sudah dipakai:** avatar Vitaboy, animator (blending/head-seek), snowflake,
  SkyDome pattern, grass shader, tekstur `grass_tso`/roof.
- **Yang akan digali:** (M5) timing curves dari `.anim` untuk gait/pose autentik;
  (M3) UI chrome `uigraphics` untuk skin HUD; (M2) tekstur lantai/dinding interior;
  (M6) eksplorasi audio (XA/UTK — perlu decoder, fallback: sound design sendiri).

---

## M1 — LIMA MENIT PERTAMA (onboarding & legibility)  ⭐ prioritas
**Masalah yang diserang:** pemain baru bingung harus apa.
- [x] Layar judul: logo, Mulai Baru / Lanjutkan / Kontrol
- [x] Intro: surat Paman Arsa di mailbox → tujuan game dinyatakan eksplisit
- [x] Rantai quest tutorial ber-objective (tutorial.py, 6 langkah)
- [x] **Objective tracker** di HUD (kiri-atas, tracker_lines)
- [x] Prompt kontekstual (context_prompt: "[SPACE] Cangkul tanah …")
- [x] Papan petunjuk (signpost) antar-scene (build_signpost)
**DoD:** orang baru bisa panen pertama tanpa bertanya. → **sebagian besar TERCAPAI**
(perlu playtest manusia nyata untuk pastikan).

## M2 — TAMPILAN (identitas visual terkunci)
- [x] Skybox gradient (SkyDome) + transisi warna siang-malam
- [x] Lighting rig siang/malam (ambient+sun lerp; tint per fase)
- [ ] Scene dressing: wire props farming ke tile system (kandang, gerobak,
      scarecrow, jerami, peti — tile baru di config + builder di props.py) ← SISA UTAMA
- [ ] Interior: lantai/dinding bertekstur (kandidat: aset TSO housedata)
- [x] Polish cuaca: hujan/salju/angin/kabut konsisten
**DoD:** screenshot 6 scene utama layak jadi material itch.io.

## M3 — HUD & UX 2.0
- [ ] Skin HUD: panel chrome TSO (9-slice) ATAU pixel-art custom — pilih satu
- [ ] **Ikon item bergambar**: auto-render 64px dari model 3D via Blender (batch)
- [ ] Inventory grid pakai ikon + tooltip; kategori tab jelas
- [ ] Pie menu NPC dengan ikon aksi
- [x] Pause menu (Esc → Lanjut/Simpan/Kontrol) — Settings volume/fullscreen masih sisa
- [ ] Save/Load slot UI (3 slot + autosave harian)
- [x] Sistem notifikasi terpadu (flash/emote/toast/subtitle batin)
**DoD:** semua sistem bisa dioperasikan tanpa membaca README.

## M4 — GAMEPLAY CORE LENGKAP
- [x] Shipping bin / Peti Kirim (model A Stardew: panen→kirim→tidur→emas)
- [x] Ternak produktif: [R] hewan → susu/telur/wol harian → Peti Kirim
- [~] Set crop per musim + benih di toko Bu Sari (CROPS ada, perlu dilengkapi)
- [x] Upgrade alat (pickaxe/pedang via Bengkel Budi)
- [~] Balance ekonomi pass 1 (harga/energi/durasi) — paling baik sambil playtest manusia
- [x] Audit quest 11-stage end-to-end — dulu MACET di tahap 4, kini tamat (smoke-tested)
- [x] Crafting diperluas (perahu, jala, obor, peti, pagar + pelayaran laut)
- [x] **Tani Sakuna mendalam** (jadwal air, nutrisi, gulma → mutu ★) — BONUS
**DoD:** loop harian punya 3+ keputusan bermakna; tamat quest bisa dicapai.

## M5 — ANIMASI & KEHIDUPAN
- [ ] Walk cycle 4-frame (dari 2) — timing dicuplik dari `.anim` TSO
- [ ] Pose aksi per konteks: mencangkul, menyiram, duduk, tidur, memancing
- [ ] NPC schedule terlihat: warung buka/tutup, Jaka ronda malam, anak sekolah
- [ ] Mob dungeon: telegraph serangan + death anim (mesh-swap)
- [x] Kupu-kupu ambient siang (pool 8, flutter) + kunang-kunang malam (sudah ada)
**DoD:** dunia terasa hidup saat diam ditonton 60 detik. → kupu-kupu/kunang ✓; sisa: jadwal NPC, telegraph mob.

## M6 — AUDIO & GAME FEEL
- [ ] SFX per aksi (cangkul, siram, panen, pintu, kasir, ombak, api)
- [ ] Ambience per scene (jangkrik malam, ombak pantai, gamelan pasar samar)
- [ ] Musik: 2-3 loop (pagi/malam/dungeon) — komposisi prosedural atau CC0
- [ ] Transisi scene fade; screen-shake halus; hit-feedback combat
**DoD:** main dengan mata tertutup tetap tahu apa yang terjadi.

## M7 — RILIS
- [ ] Performance pass (profiling; target 60fps di scene terpadat)
- [ ] Packaging PyInstaller → folder distribusi + ikon
- [ ] README pemain + 6 screenshot + GIF
- [ ] Playtest checklist penuh + bugfix sweep
- [ ] Tag v1.0
**DoD:** satu zip yang bisa dikirim ke teman dan langsung jalan.

---

## Estimasi
M1+M2 ≈ 2 sesi · M3 ≈ 1 · M4 ≈ 2 · M5 ≈ 1 · M6 ≈ 1 · M7 ≈ 1 → **±8 sesi kerja**.
Mulai dari M1; tiap sesi diakhiri commit + update dokumen ini (centang checkbox).
