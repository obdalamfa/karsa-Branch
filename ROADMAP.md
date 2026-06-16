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
| **M2** Tampilan | **~80%** | skybox+lighting+cuaca + dressing obj (farm/town/beach/greenhouse + **mountain/lake/cemetery via scatter aman**) ADA; sisa: tekstur interior |
| **M3** HUD & UX | **~95%** | HUD Disco + needs + Majelis Batin + menu Jeda berlapis (Simpan/Muat 3 slot + Pengaturan) + ikon item (18 PNG) + **skin panel chrome TSO** ADA; tinggal polish opsional |
| **M4** Gameplay core | **~55%** | crafting+laut, upgrade alat, **tani Sakuna mendalam** ADA; sisa: shipping bin, ternak produktif, balance, audit quest |
| **M5** Animasi & kehidupan | **~90%** | walk mesh-swap + pose aksi + **jadwal NPC per-jam** + ambient kupu/kunang + **telegraph & death anim mob** ADA; sisa: 4-frame walk (Blender batch) |
| **M6** Audio & game-feel | **~95%** | 27 SFX prosedural + 6 BGM ambient per-scene (progresi akor) + musik tempur dinamis (duck HP kritis) + SFX tempur (telegraph/mati/kena) + screen-shake + **fade transisi scene** ADA |
| **M7** Rilis | **~40%** | **scaffold packaging siap** (lembah_karsa.spec + build_release.ps1 + README_PEMAIN + main.py frozen-path); sisa: jalankan build & uji exe (sisi user), perf pass, bug sweep playtest |

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
- [x] Scene dressing: props farming ke tile (kandang/gerobak/scarecrow/jerami/peti via
      farm_builder) + **scatter_obj_props aman** (mountain/lake/cemetery: bambu, pohon mati,
      lentera, pagar — hanya di tile lantai kosong jauh dari portal, deterministik)
- [ ] Interior: lantai/dinding bertekstur (kandidat: aset TSO housedata)
- [x] Polish cuaca: hujan/salju/angin/kabut konsisten
**DoD:** screenshot 6 scene utama layak jadi material itch.io.

## M3 — HUD & UX 2.0
- [x] Skin HUD: panel chrome TSO (opsi A) — tekstur bingkai logam+parchment (`tools/make_ui_chrome.py`)
      dipasang ke Majelis Batin, modal skill-check, & menu Jeda (tahan-stretch, bukan 9-slice penuh)
- [x] **Ikon item bergambar**: 18 ikon 64px prosedural PIL (`tools/make_item_icons.py`) —
      tanpa Blender (crop/material/produk belum punya model 3D); grid auto-muat via _item_icon_tex
- [x] Inventory grid pakai ikon + tooltip; kategori tab jelas (grid sudah ada, kini berikon)
- [ ] Pie menu NPC dengan ikon aksi
- [x] Pause menu berlapis (Esc → Lanjut/Simpan/Muat/Pengaturan/Kontrol) + Settings volume master & fullscreen
- [x] Save/Load slot UI (3 slot, ringkasan nama/hari/emas; slot 0 = save lama kompatibel)
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
- [x] NPC schedule terlihat: jadwal per-jam ADA & terverifikasi (SCHEDULES 25+ NPC —
      Jaka ronda malam, warung sari buka pagi→pulang malam, hantu muncul malam di kuburan/gunung)
- [x] Mob dungeon: telegraph serangan (wind-up merah+membesar, bisa dielak) + death anim (tumbang+menyusut)
- [x] Kupu-kupu ambient siang (pool 8, flutter) + kunang-kunang malam (sudah ada)
**DoD:** dunia terasa hidup saat diam ditonton 60 detik. → kupu-kupu/kunang ✓, jadwal NPC ✓, telegraph+death mob ✓; sisa: 4-frame walk (Blender).

## M6 — AUDIO & GAME FEEL
- [x] SFX per aksi (cangkul, siram, panen, dialog, beli/jual, quest, tidur, dll — 27 SFX prosedural)
- [x] Ambience per scene (outdoor/forest/cave/indoor/water + tempur — sintesis prosedural)
- [x] Musik: 6 loop ambient (per kategori scene) + tempur dinamis (duck saat HP kritis, boost saat terbang)
- [x] Transisi scene fade (layar hitam memudar 0.45s saat pindah scene); screen-shake halus + hit-feedback combat (SFX telegraph/mati/kena + shake kamera)
**DoD:** main dengan mata tertutup tetap tahu apa yang terjadi.

## M7 — RILIS
- [ ] Performance pass (profiling; target 60fps di scene terpadat) — butuh run nyata
- [x] Packaging PyInstaller → spec onedir (`lembah_karsa.spec`) + `build_release.ps1`
      (auto-install PI, smoke-test gate, bundel assets+ursina+panda3d, salin README)
- [x] main.py: set `application.asset_folder` saat frozen (font/aset internal terbaca)
- [x] README pemain (`README_PEMAIN.md`) — kontrol + loop harian; sisa: 6 screenshot + GIF
- [ ] **Jalankan build & uji exe** (sisi user: `pwsh ./build_release.ps1`) — perlu GUI nyata
- [ ] Playtest checklist penuh + bugfix sweep — perlu pemain manusia
- [ ] Tag v1.0
**DoD:** satu zip yang bisa dikirim ke teman dan langsung jalan.
> Catatan: scaffold build tak bisa diverifikasi di lingkungan headless (butuh
> PyInstaller + boot GUI). Langkah build sengaja diserahkan ke user via skrip.

---

## Estimasi
M1+M2 ≈ 2 sesi · M3 ≈ 1 · M4 ≈ 2 · M5 ≈ 1 · M6 ≈ 1 · M7 ≈ 1 → **±8 sesi kerja**.
Mulai dari M1; tiap sesi diakhiri commit + update dokumen ini (centang checkbox).
