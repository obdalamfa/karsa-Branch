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
- [ ] Layar judul: logo, Mulai Baru / Lanjutkan / Kontrol, latar render kampung
- [ ] Intro: surat Paman Arsa di mailbox → tujuan game dinyatakan eksplisit
- [ ] Rantai quest tutorial ber-objective: cangkul → tanam → siram → tidur →
      panen → jual (tiap langkah dipandu hint HUD + emote)
- [ ] **Objective tracker** di HUD (kiri-atas: quest aktif + langkah berikutnya)
- [ ] Prompt kontekstual di atas target: `[R] Bicara`, `[SPACE] Cangkul`, dll.
- [ ] Papan petunjuk (signpost) di percabangan jalan antar-scene
**DoD:** orang yang belum pernah lihat game ini bisa panen pertama tanpa bertanya.

## M2 — TAMPILAN (identitas visual terkunci)
- [ ] Skybox gradient + siluet gunung di horizon (pengganti void abu-abu)
- [ ] Lighting rig per scene (interior hangat, malam dingin, swarga keemasan)
- [ ] Scene dressing: wire props farming ke tile system (kandang, gerobak,
      scarecrow, jerami, peti — tile baru di config + builder di props.py)
- [ ] Interior: lantai/dinding bertekstur (kandidat: aset TSO housedata)
- [ ] Polish cuaca: hujan/salju/angin konsisten dengan LUT siang-malam
**DoD:** screenshot 6 scene utama layak jadi material itch.io.

## M3 — HUD & UX 2.0
- [ ] Skin HUD: panel chrome TSO (9-slice) ATAU pixel-art custom — pilih satu
- [ ] **Ikon item bergambar**: auto-render 64px dari model 3D via Blender (batch)
- [ ] Inventory grid pakai ikon + tooltip; kategori tab jelas
- [ ] Pie menu NPC dengan ikon aksi
- [ ] Pause menu + Settings (volume, fullscreen, bahasa hint)
- [ ] Save/Load slot UI (3 slot + autosave harian)
- [ ] Sistem notifikasi terpadu (flash/emote/toast — satu bahasa visual)
**DoD:** semua sistem bisa dioperasikan tanpa membaca README.

## M4 — GAMEPLAY CORE LENGKAP
- [ ] Shipping bin (jual di akhir hari ala Stardew) di samping rumah
- [ ] Ternak produktif: beli anak ternak → rawat → susu/telur/wol harian
- [ ] Set crop lengkap per musim + benih di toko Bu Sari
- [ ] Upgrade alat terasa (radius siram, auto-panen 3×3, dst.)
- [ ] Balance ekonomi pass 1 (harga, energi, durasi hari)
- [ ] Audit quest utama 11-stage end-to-end (main sampai tamat tanpa stuck)
- [ ] Crafting diperluas (resep dari hasil dungeon + laut)
**DoD:** loop harian punya 3+ keputusan bermakna; tamat quest utama bisa dicapai.

## M5 — ANIMASI & KEHIDUPAN
- [ ] Walk cycle 4-frame (dari 2) — timing dicuplik dari `.anim` TSO
- [ ] Pose aksi per konteks: mencangkul, menyiram, duduk, tidur, memancing
- [ ] NPC schedule terlihat: warung buka/tutup, Jaka ronda malam, anak sekolah
- [ ] Mob dungeon: telegraph serangan + death anim (mesh-swap)
- [ ] Burung/kupu-kupu ambient di farm (partikel bermodel)
**DoD:** dunia terasa hidup saat diam ditonton 60 detik.

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
