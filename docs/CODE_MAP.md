# CODE_MAP.md — Peta jujur kode Lembah Karsa 3D

**Dibuat:** 2026-08-21 · **Cakupan:** seluruh `game/` (12.6k baris), `main.py`,
`make_assets.py`, `tools/` · **Metode:** dibaca baris-per-baris, lalu diverifikasi
dengan menjalankan game sungguhan (`tools/capture.py`) dan harness runtime.

Dokumen ini adalah *audit*, bukan brosur. Setiap klaim "rusak" di bawah ini
punya bukti `file:baris` dan sebagian besar sudah dipicu secara runtime.

---

## 0. Ringkasan satu paragraf

Ini adalah **farming-RPG Rune-Factory-esque** dengan third-person follow camera,
bukan life-sim. Yang benar-benar hidup dan berkualitas: **pipeline avatar Vitaboy
TSO** (33.332 entri FAR3 asli ter-index: 5.504 animasi, 2.250 mesh, 5.453
appearance, `adult.skel`) — ini aset kelas berat yang sudah bekerja. Yang lain
sebagian besar berupa *scaffolding*: `behavior_vm.py` adalah VM SimAntics
lengkap yang **tidak pernah menyentuh dunia**; needs/motives ada di `state.py`
tapi **tidak punya UI sama sekali**; "Pie Menu" adalah **list vertikal keyboard**;
"Action Queue" adalah **daftar tile untuk satu tool**. Empat jalur kode
melempar `AttributeError` setiap kali dijalankan (dialog, quest, jam, lore
dungeon). Rendering menabrak target Sims 1 dari arah berlawanan: kamera
near-horizontal, dinding solid tanpa cutaway, dan pass dekorasi "surreal
digital" yang menaburkan silinder magenta + kubus cyan neon ke 30% tile rumput.

---

## 1. Peta modul: apa yang dimiliki, permukaan publik, kualitas nyata

Notasi kualitas: **SOLID** (bisa dibangun di atasnya) · **OK** (berfungsi, kasar)
· **RAPUH** (jalan tapi salah/tidak sesuai maksud) · **STUB** (bentuknya ada,
isinya tidak) · **MATI** (tidak pernah diimpor / tidak pernah dipanggil).

### 1.1 Entry & orkestrasi

| File | Baris | Memiliki | Permukaan publik | Kualitas |
|---|---:|---|---|---|
| `main.py` | 34 | Bootstrap, paksa pipeline OpenGL | `main()` | **OK** |
| `game/app.py` | 676 | `Game3D` — game loop, kamera, cuaca, siang-malam, input router | `Game3D`, `run()`, `GameHandler` | **RAPUH** |
| `game/__init__.py` | 0 | — | — | kosong |

**`main.py`** — `loadPrcFileData('', 'load-display pandagl')` sebelum import
Ursina (main.py:9) adalah keputusan bagus; semua shader GLSL bergantung padanya.
Tapi main.py:22-25: kalau folder `assets/` tidak ada, ia menjalankan
`make_assets.main()` — yang menulis PNG **flat ke `assets/`**
(`make_assets.py:684`), sedangkan seluruh game membaca dari `assets/textures/`
(`world.py:32`, `player.py:63`, `panels.py:29`). Jadi jalur "self-heal" itu
menghasilkan game tanpa tekstur sama sekali. `tools/reorganize_assets.py` adalah
migrasi satu-kali yang memperbaikinya — dan path-nya di-hardcode ke
`c:\Users\User\lembah-karsa\3d` (`tools/reorganize_assets.py:5`).

**`game/app.py`** — kelas `Game3D` melakukan terlalu banyak: init engine, partikel
hujan/salju/awan, transisi scene, kamera, palet cahaya per-jam, dan seluruh
routing input. Fungsi `update()` sepanjang ~220 baris dengan lima level nesting.
Catatan penting:

- **Kamera bukan isometrik.** `app.py:187-191`: `camera.orthographic = False`,
  `fov=60`, `camera_pitch = 12.0`, `camera_dist = 13.0`. Ini third-person follow
  perspektif nyaris sejajar tanah. Sims 1 = ortografis dimetrik 2:1 dengan empat
  langkah rotasi. Tidak ada satupun dari itu di sini.
- **Snap kamera duplikat.** Blok yang sama (hitung `dx/dy/dz` dari yaw/pitch,
  set `camera.position`, `look_at`) muncul dua kali: `app.py:281-289` dan
  `app.py:333-342`.
- **Safety walkable snap** disalin tiga kali nyaris identik: `app.py:150-162`,
  `app.py:260-273`, `app.py:546-557`.
- `_check_needs_warning()` (`app.py:591-599`) adalah **satu-satunya** cara pemain
  tahu needs-nya jatuh — sebuah flash text. Tidak ada bar.
- `app.py:479-499`: klik kiri hanya membuka pie menu NPC atau menampilkan nama
  tile. **Tidak** memanggil `player.move_to_world()`. Klik-untuk-jalan mati
  (lihat §1.4).

### 1.2 State & konfigurasi

| File | Baris | Kualitas |
|---|---:|---|
| `game/config.py` | 103 | **SOLID** |
| `game/state.py` | 135 | **OK** |

**`config.py`** — 51 tile ID sebagai konstanta tuple-unpack (`config.py:56-61`),
daftar `WALKABLE`/`BLOCKING`/`MINEABLE`, dan blok needs (`config.py:90-103`).
Bersih. Tapi `QUEUE_USER_DRIVEN=50 / QUEUE_AUTONOMOUS=2 / QUEUE_IDLE=0`
(`config.py:101-103`) hanya dipakai di satu tempat: `QUEUE_USER_DRIVEN` sebagai
prioritas konstan di `interaction_controller.py:574`. `QUEUE_AUTONOMOUS` dan
`QUEUE_IDLE` tidak pernah dibaca oleh siapapun.

**`state.py`** — `GameState` dataclass + JSON save/load. Save menulis
`self.__dict__` mentah (`state.py:115`) — tidak ada versioning, tidak ada
migrasi. Load hanya menerima field yang sudah ada (`state.py:130-131`), jadi
save lama diam-diam kehilangan field baru. Method yang ada:
`get_season`, `get_season_name`, `get_time_str`, `get_hour`, `is_night`,
`get_player_tile`, `get_mood`, `mood_energy_multiplier`.

**Method yang TIDAK ada tapi dipanggil kode lain** (semua diverifikasi runtime):

| Dipanggil di | Nama | Yang benar |
|---|---|---|
| `interaction_controller.py:222` | `state.time_hm()` | `get_time_str()` |
| `interaction_controller.py:226` | `state.season_name()` | `get_season_name()` |
| `quest_controller.py:22` | `state.npc_relations` | `npc_hearts` |
| `quest_controller.py:43,46,49` | `state.lore_found` | `lore_collected` (list, bukan dict) |

### 1.3 Rendering

| File | Baris | Memiliki | Kualitas |
|---|---:|---|---|
| `game/world.py` | 606 | Tile → Entity 3D, soil/crop, air | **RAPUH** |
| `game/meshes.py` | 296 | Superellipsoid soft-cube & capsule ter-cache | **SOLID** |
| `game/smooth_shader.py` | 198 | Cel-shading GLSL 3-tier + fake AO + outline | **SOLID** |
| `game/grass_shader.py` | 115 | Vertex sway rumput (port GrassShader.fx) | **SOLID** |
| `game/sky.py` | 196 | SkyDome sphere terbalik, gradien zenith/horizon | **SOLID** |
| `game/shaders/vhs_bloom.py` | 88 | Post-process CRT/bloom/chromatic aberration | **OK** |
| `game/scenes/props.py` | 187 | Builder prop kompleks (pohon, rumah, kubur, TV) | **OK** |

Detail di §6.

### 1.4 Player & interaksi

| File | Baris | Kualitas |
|---|---:|---|
| `game/player.py` | 1036 | **RAPUH** |
| `game/controllers/interaction_controller.py` | 632 | **RAPUH** |
| `game/controllers/time_controller.py` | 112 | **OK** |
| `game/controllers/quest_controller.py` | 86 | **MATI + rusak** |
| `game/pathfinder.py` | 494 | **SOLID (setengah terpakai)** |

**`player.py`** — `Player3D(Entity)`. Dua jalur model yang saling eksklusif:

1. **Vitaboy** (`player.py:231-238`): merakit `VitaboyAvatar` dari daftar `.apr`.
   Berhasil di mesin ini (terbukti di screenshot — mesh + tekstur TSO asli).
2. **Fallback voxel** (`player.py:241-318`): boneka kotak lengkap dengan pivot
   bahu/siku/lutut. Termasuk **halo cincin magenta + kubus cyan berputar**
   (`player.py:268-269`) yang menempel di kepala pemain. Ini bukan placeholder
   yang lupa dihapus; ada `apply_smooth()` dan animasi bob khusus untuknya
   (`player.py:553-558`).

Permukaan publik: `tick()`, `handle_input()`, `apply_appearance()`,
`set_tile_pos()`, `get_tile_pos()`, `move_to_world()`, `rebuild_pathgrid()`,
`queue_toggle()`, `queue_execute()`, `execute_pie_action()`, `_build_pie_options()`.

Masalah struktural:

- **1036 baris untuk apa yang seharusnya jadi 3 file.** Baris 383-767 adalah satu
  method `tick()` berisi input WASD, kolisi per-axis, dua sistem animasi berbeda,
  regen HP, tick buff, gravitasi, partikel sapu terbang, dan cek portal.
- `move_to_world()` (`player.py:192-198`) **tidak pernah dipanggil**. `PathMover`
  hanya dipakai sebagai fallback pasif. Jadi A* yang bagus di `pathfinder.py`
  tidak menggerakkan pemain sama sekali.
- **Setiap frame** `self.body.color` di-set ulang dengan alpha 0.4 hardcoded
  (`player.py:722-724`) — inilah kenapa badan pemain tembus pandang.
- Baris 1014-1036 adalah **sembilan method yang hanya mem-forward** ke controller.
  Refactor setengah jalan: logika sudah pindah, shim-nya tidak pernah dibersihkan.
- Fitur yang tidak ada di dokumen manapun: `b` = terbang pakai sapu
  (`player.py:790`), `y` = slide/dash (`player.py:794`), `left alt` = lompat.
  Sapu terbang menempelkan **kubus magenta murni** sebagai bulu sapu
  (`interaction_controller.py:600-602`) dan menyemburkan partikel neon
  cyan/magenta/kuning (`player.py:763`).

**`interaction_controller.py`** — inti gameplay: `use_tool_at()`, `interact()`,
`attack()`, `capture()`, `consume_item()`, `try_fishing()`, `try_healing()`,
`try_repair_lighthouse()`, `build_pie_options()`, `execute_pie_action()`,
`queue_toggle()`, `queue_execute()`. Sembilan tool (cangkul/siram/tanam/panen/
kapak/hadiah/pickaxe/pedang/pancing) diimplementasikan sebagai satu rantai
`if/elif` sepanjang 145 baris (`:36-171`). Bug:

- `check_quests()` (`:396-400`) mencari `player.quest_manager` (tidak ada) lalu
  `player._check_quest_progress` (tidak ada) → **no-op senyap**. Dipanggil
  setelah panen, menebang, menambang, memancing, menangkap. Artinya
  **progresi quest utama tidak pernah berjalan dari gameplay.**
- `interact()` pada tile jam (`:222`) dan kalender (`:226`) → `AttributeError`.
- `interact()` pada tile TV/kompor/kursi memberi bonus needs — ini satu-satunya
  interaksi objek bergaya Sims yang ada, tapi hardcoded ke 5 tile ID.
- `queue_execute()` (`:578-588`) menjalankan **seluruh antrian sekaligus dalam
  satu frame**, semuanya dengan `tool_index` yang aktif *sekarang*, bukan yang
  aktif saat tile ditambahkan. Prioritas di-sort (`:582`) lalu diabaikan.

**`quest_controller.py`** — 86 baris, dan `check_quest_progress()` **tidak pernah
dipanggil dari manapun** (satu-satunya pemanggil ada di `interaction_controller.py:398`
dan `time_controller.py:89`, keduanya menargetkan nama yang tidak ada). Kalau
dipanggil, ia crash di `s.npc_relations` (`:22`). `_notify_quest_up()` (`:31`)
memanggil `QUEST_STAGES.get(...)` padahal `QUEST_STAGES` adalah **list**
(`data.py:411`). `check_dungeon_lore()` (`:40`) *memang* dipanggil
(`player.py:931`) dan **crash saat masuk dungeon level 3, 7, atau 12** karena
`s.lore_found`. Lore ID yang dipakainya (`'dungeon_3'`) juga tidak ada di
`LORE_ITEMS`. Modul ini efektif nol-nilai dalam kondisi sekarang.

**`time_controller.py`** — bagian yang benar-benar bekerja: `tick()` memajukan
jam + decay tiga needs (`:14-25`), `advance_day()` menumbuhkan tanaman, memutar
cuaca dengan bobot, reset energi/HP, dan menambah `lapar`/`senang` saat tidur
(`:42-46`). Bersih. Hanya ekor quest-nya yang mati (`:88-91`).

**`pathfinder.py`** — A* 8-arah dengan tie-break, `_nearest_walkable` fallback,
`smooth_path()` line-of-sight, plus `PathMover` dengan callback `on_step`/
`on_arrive`. Ini kode bagus. Dipakai NPC (via `npc_brain.plan_path`) dan
di-instansiasi untuk pemain tapi tidak pernah dikemudikan.

### 1.5 Entities & aktor

| File | Baris | Kualitas |
|---|---:|---|
| `game/entities.py` | 507 | **RAPUH** |
| `game/base_actor.py` | 72 | **OK** |
| `game/npc.py` | 69 | **OK** |
| `game/animal.py` | 55 | **OK** |
| `game/mob.py` | 98 | **OK** |

**`entities.py`** — `EntitiesManager`: spawn/despawn per scene, jadwal NPC,
wild entity, mob dungeon. Permukaan: `load_scene()`, `update()`,
`get_nearest_npc()`, `attack_mobs()`, `try_capture_wild()`, `spawn_mobs()`.

- `NPC_APPEARANCES` (`:52-63`) memetakan **10 dari 14** NPC manusia ke `.apr` TSO
  asli. Empat sisanya (`joko`, `ningsih`, `pak_guru`, `kru_kuro`) plus semua
  makhluk halus dan **semua hewan ternak** jatuh ke `get_npc_model_name()`
  (`:65-70`) yang mengembalikan `'humanoid'`. **Sapi, ayam, kambing, bebek,
  domba, kuda, kucing, rubah, kelinci semuanya di-render sebagai mesh manusia.**
  Terbukti di sensus entity: `6 FarmAnimal|model=humanoid.obj`.
- Label nama NPC dibuat dengan `scale=5, billboard=True, background=True`
  (`:242-245`). Di screenshot mereka jadi papan reklame raksasa yang menutupi
  cakrawala.
- `get_nearest_npc()` (`:438-448`) mengabaikan `max_dist_tiles` sepenuhnya —
  `best_d` diinisialisasi ke `max_dist_tiles + 1` lalu setiap NPC dengan `d <
  best_d` diterima, jadi NPC di seberang peta tetap lolos selama tidak ada yang
  lebih dekat. Karena `interact()` memanggilnya dengan radius 3.0, pemain bisa
  membuka pie menu NPC yang jauh.
- `attack_mobs()` (`:450-475`) memutasi `s.mobs` sementara `update()` juga
  memutasi list yang sama lewat `actor.mob_spec` — dua sumber kebenaran untuk HP
  mob yang disinkronkan manual (`:330-332`).
- `PLAY.md:129` menyuruh mengedit `game/entities.py:736` untuk `_USE_VITABOY_HUMANS`.
  File-nya 507 baris dan flag itu tidak ada lagi. Dokumentasi basi.

**`base_actor.py` / `npc.py` / `animal.py` / `mob.py`** — hierarki OOP yang rapi
dan kecil. `BaseActor` memegang posisi logis vs visual dan lerp
(`base_actor.py:43-68`). `Monster` punya FSM PATROL/ALERT/CHASE/ATTACK
(`mob.py:56-98`) — satu-satunya AI yang benar-benar mengubah dunia. Perhatikan
`mob.py:57-61`: transisi state-nya terbalik (`dist <= alert_r` → CHASE,
`dist <= chase_r` → ALERT) dan ALERT bergerak **1,6× lebih cepat** dari CHASE
(`mob.py:83`). `base_actor.load_model()` (`:34-37`) dan `update_ai()` (`:39-41`)
adalah `pass` — **STUB**.

### 1.6 AI & perilaku

| File | Baris | Kualitas |
|---|---:|---|
| `game/behavior_vm.py` | 459 | **SOLID tapi terputus dari dunia** |
| `game/npc_brain.py` | 125 | **RAPUH** |
| `game/animator.py` | 678 | **MATI (orphan total)** |

Detail di §3.

### 1.7 UI

| File | Baris | Kualitas |
|---|---:|---|
| `game/panels.py` | 867 | **RAPUH** |
| `game/chargen.py` | 330 | **OK** |

**`panels.py`** — `UIManager` dengan empat mode (`hud`/`dialog`/`panel`/`pie`,
plus `chargen` yang di-set dari luar di `app.py:574`). Memiliki HUD, kotak
dialog bercabang, 8 panel teks, pie menu, dan flash message.

- **Thermometer needs tidak ada.** `_need_lbl_ents`, `_need_bg_ents`,
  `_need_fill_ents` diinisialisasi sebagai **list kosong** di `panels.py:139-141`
  dan tidak pernah diisi. `_NBAR_W`/`_NBAR_X` = 0. `_refresh_hud()`
  (`:156-216`) tidak menyentuhnya. Tekstur `up_thermo_slice` dimuat dari
  `assets/ui/` (`panels.py:29`) — **folder itu tidak ada**; file-nya sebenarnya
  di `assets/textures/`. Runtime: `_THERMO_BG_TEX is None`, `_need_fill_ents == []`.
- `_prev_hunger/_prev_social/_prev_fun/_prev_energy` (`:86-89`) di-set `None` dan
  tidak pernah dibaca — sisa rencana indikator panah naik/turun.
- `NEED_LOW` dan `NEED_CRITICAL` diimpor (`:21`) dan tidak pernah dipakai.
- `_end_dialog()` (`:409-420`) memanggil `self.player._check_quest_progress(self)`
  → **`AttributeError` setiap kali percakapan selesai** (diverifikasi runtime).
  Dialog tetap tertutup karena `mode='hud'` di-set di baris 418 sebelum crash,
  tapi traceback tercetak dan progresi quest tidak pernah jalan.
- Semua panel adalah **satu `Text` monospace** yang di-render ulang penuh
  (`_render_panel`, `:518-701`). Tidak ada ikon, tidak ada grid, tidak ada
  interaksi mouse. Panel `map` adalah ASCII art (`:579-597`).
- HUD di-layout untuk 1920×1080; pada 1280×720 teks kanan-atas terpotong keluar
  layar (terlihat di screenshot).

**`chargen.py`** — layar pembuatan karakter keyboard-driven: nama + 5 slot
preset (kulit/rambut/baju/celana/topi). `_to_state()` (`:236-247`) membuat
proxy object anonim, dan `_refresh()` memanggil `player.apply_appearance()`
setiap keypress — yang untuk jalur Vitaboy berarti **destroy + rebuild seluruh
avatar TSO** (`player.py:337-342`) per tekan tombol. Preset warna hanya berdampak
pada jalur voxel fallback; Vitaboy hanya bereaksi pada `char_shirt == 0` vs
selainnya dan `char_hair > 0` (`player.py:332-334`). Jadi 5 kulit × 5 rambut ×
… sebagian besar tidak terlihat.

### 1.8 Konten & data

| File | Baris | Kualitas |
|---|---:|---|
| `game/data.py` | 681 | **SOLID (data)** |
| `game/dungeon.py` | 185 | **OK** |
| `game/scenes/*` | ~570 | **OK** |
| `game/sound.py` | 493 | **OK** |

Detail di §7.

### 1.9 Vitaboy

| File | Baris | Kualitas |
|---|---:|---|
| `game/vitaboy/bcf_reader.py` | 81 | **SOLID** |
| `game/vitaboy/far3.py` | 241 | **SOLID** |
| `game/vitaboy/mesh.py` | 165 | **SOLID** |
| `game/vitaboy/skeleton.py` | 223 | **SOLID** |
| `game/vitaboy/animation.py` | 226 | **SOLID** |
| `game/vitaboy/appearance.py` | 129 | **SOLID** |
| `game/vitaboy/registry.py` | 284 | **SOLID (path hardcoded)** |
| `game/vitaboy/avatar.py` | 296 | **OK (lambat)** |
| `game/vitaboy/actor.py` | 212 | **OK (tidak dipakai game)** |
| `game/vitaboy/loader.py` | 122 | sebagian besar tergantikan `avatar.py` |
| `game/vitaboy/default_skeleton.py` | 76 | **MATI** (registry menemukan `adult.skel` asli) |
| `game/vitaboy/tso_paths.py` | 137 | **RAPUH** (path absolut mesin ini) |
| `game/vitaboy_baked.py` | 167 | **MATI** (orphan) |
| `game/vitaboy_npc.py` | 64 | **MATI** (orphan) |

Detail di §5.

### 1.10 Modul mati / orphan (tidak diimpor siapapun)

| File | Baris | Catatan |
|---|---:|---|
| `game/animator.py` | 678 | Sistem skeleton+blending+head-seek lengkap. Nol pemanggil. |
| `game/blender_bridge.py` | 125 | Generator sapi & hantu via Blender. `BLENDER_PATH = r"E:\blender\blender.exe"` hardcoded (`:5`). Nol pemanggil. |
| `game/vitaboy_baked.py` | 167 | Loader Panda3D `Actor` untuk GLB hasil bake — **24 GLB `au-*_idle/walk.glb` benar-benar ada di `assets/models/`**. Ini jalur skinning GPU yang sudah jadi dan tidak dipakai. |
| `game/vitaboy_npc.py` | 64 | Tabel outfit per-NPC yang lebih lengkap dari yang dipakai `entities.py`. Nol pemanggil. |
| `game/vitaboy/default_skeleton.py` | 76 | Tidak pernah dipanggil sejak registry punya `adult.skel`. |
| `scratch.py`, `scratch_test.py`, `refactor_entities.py`, `refactor_player_script.py`, `refactor_scene_logic.py`, `extract_scenes.py`, `standardize_assets.py`, `test_init.py` | ~250 | Skrip refactor sekali-jalan. Semua mereferensikan `game/scenes.py` yang **sudah tidak ada**. |

Total baris mati/orphan: **± 1.550** (12% dari basis kode).

### 1.11 `tools/`

| File | Baris | Kualitas |
|---|---:|---|
| `tools/capture.py` | 104 | **OK (dua flag rusak)** |
| `tools/progress_page.py` | 448 | **SOLID** |
| `tools/gen_textures.py` | 280 | **OK** |
| `tools/bake_vitaboy.py` | 319 | **OK (butuh Blender)** |
| `tools/blender_gen_models.py` | 308 | **OK (butuh Blender)** |
| `tools/gen_humanoid_obj.py` | 179 | **OK** |
| `tools/reorganize_assets.py` | 50 | **RAPUH** (path hardcoded, sekali-jalan) |

`capture.py` bekerja (`CAPTURE_OK` terverifikasi). Dua flag bohong:
- `--at` (`capture.py:78`) memakai `g.player.entity.position`; `Player3D` **adalah**
  Entity dan tidak punya `.entity` → exception ditelan `traceback.print_exc()`.
- `--hour` (`capture.py:83`) menulis `g.state.hour`, field yang tidak ada;
  jam sebenarnya `time_minutes`. Tidak ada efek, tidak ada error.
- Default `--width/--height` 1280×720 (`:36-37`) padahal BRIEF menuntut 1920×1080
  karena HUD terpotong di bawah itu.

`requirements.txt` hanya berisi `ursina>=5.0.0`. Game butuh **pygame** (sound),
**Pillow** (semua tekstur), dan `make_assets.py` butuh **numpy**.

---

## 2. Needs / Motives vs The Sims 1

### Apa yang ada

**Data** (`config.py:90-98`, `state.py:63-65`): tiga need — `lapar` (Hunger),
`sosial` (Social), `senang` (Fun) — float 0..100 dengan laju decay berbeda.

**Decay** (`time_controller.py:22-25`): dikalikan `INGAME_MINUTES_PER_REAL_SECOND`,
jadi berbasis waktu in-game, bukan real-time. Benar secara desain.

**Mood** (`state.py:100-101`): rata-rata aritmetik tiga need.
**Konsekuensi mood** (`state.py:103-110` + `player.py:1001-1003`): satu-satunya
efek adalah pengali biaya energi tool — 0.8× kalau mood ≥ 70, 1.4× kalau < 20.

**Pengisian ulang** — tersebar dan tidak konsisten:

| Aksi | Need | Lokasi |
|---|---|---|
| Panen tanaman | `senang` +8 | `interaction_controller.py:96` |
| Tangkap makhluk liar | `senang` +20 | `interaction_controller.py:272` |
| Makan (V) | `lapar` + max(hp,en)×0.4 | `interaction_controller.py:291` |
| Nonton TV | `senang` +10 | `interaction_controller.py:230` |
| Sapa NPC | `sosial` +5 | `interaction_controller.py:501` |
| Ngobrol | `sosial` +15 | `interaction_controller.py:505` |
| Beri hadiah | `sosial` +20 | `interaction_controller.py:522` |
| Tanya kabar | `sosial` +8 | `interaction_controller.py:524` |
| Tidur (hari baru) | `lapar` +25, `senang` +20 | `time_controller.py:44-45` |
| Pilihan dialog | `sosial` +N | `panels.py:469-470` |

**Peringatan** (`app.py:591-599`): flash text merah saat need ≤ 20, dengan
hysteresis di 30.

### Apa yang tidak ada

| Sims 1 | Di sini |
|---|---|
| 8 motif: Hunger, Comfort, Hygiene, Bladder, Energy, Fun, Social, Room | 3 (Hunger, Social, Fun). `energy` ada tapi terpisah sebagai stat RPG (`state.py:25`), bukan motif. Comfort/Hygiene/Bladder/Room **tidak ada**. |
| Termometer motif di control panel | **Tidak ada UI apapun.** `panels.py:139-141` list kosong. |
| Mood bar hijau/merah | Tidak ada. `get_mood()` hanya dipakai untuk multiplier energi. |
| Motif menentukan autonomi | Tidak. Autonomi tidak ada (§3). |
| Kematian/kolaps dari motif | Tidak. Hanya HP ≤ 0 → pingsan (`app.py:238-242`). |
| Kurva decay non-linear + advertising | Linear konstan. |
| Motif per-Sim (banyak Sim) | Hanya pemain. NPC punya motif terpisah yang tidak terhubung (§3). |

### Vonis

Kerangka datanya **lebih baik dari yang terlihat** — decay berbasis waktu
in-game itu benar, dan `NEED_*` konstanta sudah menyediakan threshold. Tapi
sebagai sistem yang dialami pemain, ini **± 20% dari Sims 1**: 3 dari 8 motif,
tanpa UI, satu konsekuensi mekanis, dan pengisian ulang yang ditempel ad-hoc di
sepuluh tempat berbeda alih-alih dideklarasikan oleh objek.

Kesenjangan terbesar bukan jumlah motif — melainkan bahwa **di Sims 1 motif
adalah mesin penggerak seluruh permainan** (objek mengiklankan, Sim memilih,
antrian terisi). Di sini motif adalah **angka pasif yang menempel di sudut save
file** dan hanya berbisik lewat multiplier energi.

---

## 3. `behavior_vm.py` + `npc_brain.py` — autonomi atau stub?

### `behavior_vm.py` (459 baris) — VM yang bagus, dunia yang absen

Ini port SimAntics FreeSO yang **serius dan benar secara arsitektur**:

- `NodeResult` SUCCESS/FAILURE/RUNNING = `VMPrimitiveExitCode` (`:40-43`)
- `BehaviorNode` dengan cabang `on_success`/`on_failure` (`:49-66`)
- `BehaviorFrame` dengan 20 register temp = `VMStackFrame` (`:72-77`)
- `QueuedAction` dengan `priority`, `caller`, `motive_changes` = `VMQueuedAction` (`:83-90`)
- `BehaviorThread` dengan stack, queue tersortir prioritas, blocking timer,
  dan guard `MAX_TICKS_PER_FRAME = 200` (`:96-177`)
- Registry aksi global via decorator `@action` / `@condition` (`:242-284`)
- `BehaviorVM.tick()` scheduler (`:321-325`)
- Lima aksi bawaan (`idle`, `tidur`, `makan`, `bicara`, `bertani`) dan tiga
  kondisi (`butuh_makan`, `butuh_tidur`, `malam_hari`) (`:335-381`)
- `AutoNPC` yang memilih motif terendah lalu antri aksi (`:387-418`)
- Demo `__main__` lengkap (`:424-459`)

**Yang tidak ada: satupun sambungan ke dunia.** Setiap aksi bawaan memanggil
`entity.set_animation("eat")` lalu `entity.block_for(3.0)` — dan `set_animation`
hanya menyimpan string dan memanggil callback (`:207-210`). Tidak ada aksi yang
memindahkan NPC, membuka objek, mengubah tile, atau memicu apapun yang terlihat.
Tidak ada konsep **objek yang mengiklankan** (`MotiveAdChanges` di Sims 1) —
`motive_changes` ditempel ke aksi, bukan ke objek. Tidak ada routing, tidak ada
slot, tidak ada interaksi dua-Sim (field `caller` ada, tidak pernah diisi).

**`AutoNPC` sendiri tidak pernah diinstansiasi di luar demo.**

### `npc_brain.py` (125 baris) — jembatan yang cuma separuh dibangun

`NPCBrains` dibuat sekali di `entities.py:100-101` dan **memang di-tick tiap
frame** (`entities.py:305-306`). Ia:

1. Membuat satu `BehaviorEntity` per **14 NPC manusia** dengan 5 motif (`:49-56`)
2. Meluruhkan motif tiap detik (`:63-66`)
3. Auto-antri `makan`/`tidur`/`bicara`/`idle` saat motif jatuh (`:72-83`)
4. Menyediakan `plan_path()` A* (`:116-125`) dan `rebuild_grid()` (`:98-114`)

Dari empat kemampuan itu, **hanya nomor 4 yang mempengaruhi permainan.**
`entities.py:150` dan `npc.py:47` memakai `plan_path`. `get_motives()` (`:85`)
dan `get_anim_hint()` (`:89`) dan `queue()` (`:92`) **tidak pernah dipanggil oleh
siapapun** (diverifikasi dengan grep menyeluruh).

Jadi: setiap frame, 14 NPC menjalankan simulasi motif penuh, memilih aksi,
mengeksekusi behavior tree, dan mengubah animasi — **dan hasilnya dibuang.**
Yang benar-benar menggerakkan NPC adalah tabel jadwal statis `SCHEDULES`
(`data.py:348-409`) yang di-refresh tiap 30 detik (`entities.py:308-311`), plus
wander acak 1,2% per frame (`npc.py:39`).

### Vonis

**Autonomi nyata: 0%.** Yang ada adalah **mesin autonomi yang lengkap dan tidak
tersambung**, berjalan sebagai simulasi bayangan di samping sistem jadwal
hardcoded yang sebenarnya mengendalikan NPC.

Kabar baiknya: `behavior_vm.py` adalah aset. Bentuk API-nya (queue berprioritas,
stack, RUNNING/blocking, registry) sudah cukup dekat dengan SimAntics untuk
dijadikan fondasi. Yang perlu dibangun bukan VM-nya — melainkan **lapisan objek
yang mengiklankan motif** dan **primitif yang benar-benar mengubah dunia**
(GoTo, PlayAnim-blocking, SetMotive, Grab/Drop).

---

## 4. Sistem interaksi: "Pie Menu" + Action Queue vs Sims 1

### "Pie Menu"

Yang disebut pie menu (`PLAY.md:32`, `panels.py:780`) adalah **panel kotak
vertikal di kiri-bawah layar** dengan maksimal 6 baris teks
(`panels.py:781-798`). Navigasi keyboard: kiri/kanan atau angka 1-6
(`app.py:455-467`). Tidak ada busur, tidak ada wedge, tidak ada mouse hover,
tidak ada nested submenu.

**Yang benar dan patut dipertahankan:**
- Opsi dibangun secara **kondisional dari state** (`interaction_controller.py:447-491`):
  `('ngobrol','Ngobrol', hearts >= 1, '+15 Sosial +1❤')` — opsi terkunci tetap
  ditampilkan dengan label `[terkunci]` dan warna redup (`panels.py:853-856`).
  Ini persis pola Sims 1.
- Kolom keempat adalah **preview efek motif** (`panels.py:864-867`) — sadar
  betul akan `MotiveAdChanges` FreeSO.
- Ada tiga famili opsi berbeda (manusia / makhluk halus / hewan) plus opsi
  khusus per-NPC (`arya_tanya`, `sari_gossip`, `budi_riddle`, `maya_quest`,
  `naga_riddle`).

**Yang hilang dibanding Sims 1:**

| Sims 1 | Di sini |
|---|---|
| Klik objek apapun → pie menu | Hanya NPC. Objek dunia punya `interact()` hardcoded 5 tile ID (`interaction_controller.py:198-233`), tanpa menu. |
| Menu radial di posisi kursor | Panel statis di `(-0.60, -0.10)` |
| Interaksi didefinisikan **oleh objek** | Didefinisikan oleh `if npc_id in HUMAN_NPCS` (`interaction_controller.py:454`) |
| Submenu bertingkat (Talk → Gossip → …) | Datar, maks 6 item |
| Hover mouse memilih | Keyboard saja |
| Batal dengan gerakkan kursor keluar | ESC |

### Action Queue

`player.action_queue` adalah `list[((tx,ty), priority)]` (`player.py:140`).
`X` menambah/menghapus tile di depan pemain (`interaction_controller.py:565-576`),
`C` mengeksekusi semuanya (`:578-588`). Indikator HUD: satu teks `[ANT:n]`
(`panels.py:777-778`).

Ini **bukan action queue Sims 1**. Perbandingan:

| Sims 1 | Di sini |
|---|---|
| Antrian **aksi** (Eat, Sleep, Talk to Bob) | Antrian **koordinat tile** |
| Dieksekusi **satu per satu sepanjang waktu**, tiap aksi butuh detik/menit | Semua dieksekusi dalam **satu frame** (`:586-587`) |
| Ikon per-aksi di control panel, bisa diklik untuk batal | Satu angka |
| Drag untuk reorder | Tidak |
| Aksi otonom disisipkan pada prioritas rendah | Prioritas selalu konstan `QUEUE_USER_DRIVEN` (`:574`) |
| Aksi bisa di-interupsi/gagal dan mundur | Tidak ada konsep gagal |
| Sim berjalan ke objek dulu | Tidak ada routing; tool diterapkan dari jauh |
| Tool per-aksi tersimpan di aksi | Semua pakai `tool_index` saat `C` ditekan (`:585`) |

### Vonis

Pie menu: **± 35% dari Sims 1** — filosofinya benar (kondisional + preview efek),
bentuk dan cakupannya salah (bukan radial, hanya NPC, bukan objek).
Action queue: **± 10%** — namanya sama, konsepnya berbeda total. Ironisnya,
`behavior_vm.BehaviorThread` (§3) **sudah punya** action queue Sims-1 yang benar
— berprioritas, RUNNING, blocking — dan tidak dipakai oleh pemain.

---

## 5. `vitaboy/` — apakah benar-benar memuat aset TSO?

**Ya. Ini bagian terkuat dari seluruh basis kode.**

### Diverifikasi runtime di mesin ini

```
scan time 1.2s
{'archives': 75, 'total_entries': 33332, 'anims': 5504,
 'meshes': 2250, 'skels': 3, 'outfits': 1484, 'appearances': 5453}
find mabd000_leathers.apr -> mabd000_leathers.apr
find a2o-walking-loop     -> a2o-walking-loop.anim
find adult                -> adult.skel
```

Dan avatar-nya **benar-benar tampil** — screenshot `farm` menunjukkan pemain dan
NPC dengan mesh + tekstur TSO asli (rambut biru, jaket, sepatu).

### Rantai lengkapnya

1. `tso_paths.py` menemukan install TSO/FreeSO (`:34-48`)
2. `far3.py` membaca arsip `.dat` FAR3 + dekompresi QFS/RefPack (`:54`)
3. `registry.py` meng-index 33k entri by filename **dan** by `(type_id, file_id)`
   (`:110-137`), dengan cache pickle ber-versi (`:64-107`)
4. `appearance.py` mem-parse `.apr` → daftar ref `.bnd`, lalu `.bnd` → mesh id +
   texture id (`:55-118`)
5. `mesh.py` mem-parse `.mesh` termasuk quirk endian FreeSO (int big-endian,
   float little-endian — `bcf_reader.py:51-55`), X-negate, dan bone binding
   per-rentang-vertex (`:161-165`)
6. `skeleton.py` mem-parse `.skel` + FK rekursif (`:205-223`)
7. `animation.py` mem-parse `.anim` keyframe + heuristik ms-vs-detik (`:189-196`)
8. `avatar.py` merakit body+head+hair dari beberapa `.apr` ke satu skeleton
   bersama, lalu re-bake vertex tiap frame (`:223-283`)

Ini **bukan** eksperimen setengah jadi. Ini port yang berfungsi dari FreeSO.

### Tapi

**a) Path-nya hardcoded ke mesin ini.** `tso_paths.py:18-28`:
```
E:/Documents/Panda demo/panda_atb_demo/FreeSO/.../TSOClient
E:/Download/The Sims Online/TSOClient
C:/Program Files (x86)/Maxis/The Sims Online/TSOClient
```
Di mesin lain tanpa TSO, `VitaboyAvatar.__init__` melempar
`RuntimeError("adult.skel tidak ada di registry")` (`avatar.py:87`), pemain jatuh
ke boneka voxel bertopi halo magenta, dan **semua NPC ber-`.apr` kehilangan
model sepenuhnya** — `entities.py:219-221` **tidak punya try/except**, jadi
`load_scene()` akan crash. Ini bom waktu portabilitas.

**b) Skinning dilakukan di Python, per-vertex, per-frame.** `avatar.py:177-203`
mentransform setiap vertex dengan `Mat4.transform_point()` — matriks 4×4 murni
Python dengan loop `sum()` bersarang (`skeleton.py:79-87`). Mitigasinya:
throttle 10 Hz + stagger (`avatar.py:76-80`). Untuk satu lot Sims dengan 8 Sim
ini akan menjadi bottleneck. Skinning-nya juga **rigid** — satu bone per vertex;
`BlendData` di-parse (`mesh.py:132-135`) tapi tidak pernah dipakai.

**c) Jalur cepat sudah ada dan tidak dipakai.** `vitaboy_baked.py` memuat GLB via
`direct.actor.Actor` (skinning GPU Panda3D), dan **24 file `au-*_idle.glb` /
`au-*_walk.glb` sudah ada di `assets/models/`**. Nol pemanggil.

**d) `vitaboy_npc.py` punya tabel outfit yang lebih lengkap** (12 NPC dengan
body+head+hair) daripada `NPC_APPEARANCES` di `entities.py` (10 NPC). Nol pemanggil.

**e) `VitaboyActor` (`actor.py`, 212 baris)** hanya dipakai oleh `test_vitaboy.py`
di root. Duplikasi ~80% dengan `avatar.py`.

**f) `README.md` di dalam `vitaboy/` sudah basi** — mendaftar `.anim`, `.apr/.bnd`,
FAR3, dan texture binding sebagai "TODO / Belum diport". Keempatnya **sudah
selesai**.

### Vonis

**WORKING**, dan merupakan satu-satunya sistem di repo yang setara dengan
ambisi proyek. Utang teknisnya: portabilitas, kecepatan, dan tiga jalur paralel
yang tidak dikonsolidasi.

---

## 6. Jalur rendering

### Kamera (`app.py:186-191`, `304-342`)

```python
camera.orthographic = False
camera.fov          = 60
self.camera_yaw     = 0.0
self.camera_pitch   = 12.0     # <- nyaris sejajar tanah
self.camera_dist    = 13.0
```

Follow-lerp dengan focus point yang tertinggal (`:331`), rotasi bebas via klik
kanan + mouse (`:308-318`), pitch di-clamp 5°–80° (`:324`). **Ini kebalikan dari
Sims 1**: perspektif vs ortografis, sudut bebas vs empat langkah tetap, mengikuti
karakter vs terpaku pada lot. Tidak ada cutaway dinding, tidak ada zoom level,
tidak ada rotasi 90°.

### `world.py` — tile → geometri

`load_scene()` (`:265-272`) → `_clear()` → `_build_tiles()` → `_build_all_crops()`
→ `scene.builder(world)`.

Setiap tile membuat **1-3 Entity terpisah**. Sensus entity nyata pada scene
`farm` (25×18 tile):

```
781  Entity|model=cube        157  Entity|model=mesh
151  Entity|model=cube (off)   80  Entity|model=quad (off)
 34  Entity|model=sphere
--- total scene.children=1227 ---
```

**1.227 node untuk satu ladang kecil.** Tidak ada batching, tidak ada instancing,
tidak ada culling. Sebuah lot Sims dengan furnitur akan meledak.

Masalah visual konkret (semua terlihat di screenshot):

1. **Pass "surreal digital"** — `_add_outdoor_deco()` (`:491-510`) menaburkan ke
   ~30% tile rumput: kubus **cyan murni** `_c(0,255,255)` berputar 45°, silinder
   **magenta murni** `_c(255,0,255)`, dan bola bertekstur `lamp_glow` putih.
   Docstring-nya jujur: *"Surreal digital deco: floating cubes, wireframe
   pyramids"*. Ini bertabrakan langsung dengan palet BRIEF dan dengan Sims 1.
2. **PointLight indoor magenta neon** — `:387-389`,
   `pl.color = color.rgb(255, 40, 200)  # Neon magenta indoor`.
3. **Bug horizon indoor.** `:378`: `if getattr(sc, 'has_horizon', not sc.indoor and not is_dungeon)`.
   Tapi `Scene.__init__` **selalu** menyetel `self.has_horizon = has_horizon`
   dengan default `True` (`scenes/scene_base.py:2,15`), dan `_build_indoor_room()`
   (`:17-37`) tidak pernah mengopernya. Jadi `getattr` selalu menemukan `True`
   dan setiap ruangan interior mendapat quad putih **1000×1000**. Hasilnya:
   **scene `house` di-render sebagai ruang putih kosong total** — terverifikasi
   dengan capture. `scenes/dungeon.py:11` dan `naga_cave.py` sudah lolos karena
   mengoper `has_horizon=False` secara eksplisit; `_build_indoor_room` tidak.
4. **Tile jalan hitam pekat.** `:456-458` me-render `terrain/road##.png` — yang
   isinya alpha-only overlay (mayoritas piksel `(0,0,0,0)`) — sebagai kubus
   **tanpa `transparent=True`**. Komentar di `:73-75` secara sengaja menolak
   auto-transparansi. Jalur setapak jadi lempengan hitam.
5. **Semua prop dibulatkan.** `_e()` default `soft=True` (`:57`), yang menukar
   `cube` → `soft_cube_mesh()` superellipsoid. Karena `_create_entity()`
   (`:258-263`) tidak pernah mengoper `soft=False`, **seluruh furnitur, atap,
   pagar, batu nisan menjadi kentang membulat**. Sims 1 justru objek bersudut
   tajam dengan specular keras.
6. `_tile_heights` selalu `0.0` (`:428`) — terrain following ada API-nya
   (`get_surface_height`, `:280-282`) tapi selalu datar.

### Shader

- **`smooth_shader.py`** — cel-shading 3-tier (`:85-91`), outline gelap di tepi
  via `N·V` (`:97-98`), fake AO berbasis world-Y (`:101-102`), lift saturasi.
  Kualitas bagus, deteksi pipeline OpenGL dengan fallback `setLightOff()` yang
  benar (`:170-183`). **Tapi `update_globals()` (`:186-198`) tidak pernah
  dipanggil** — `app.py:655-668` menyetel uniform lewat `scene.set_shader_input`
  agar terpropagasi otomatis. `update_globals` adalah dead code.
- **`grass_shader.py`** — dua gelombang sinus dengan tinggi-terbobot. Diterapkan
  ke `world._grass_ents` dan di-update tiap frame (`app.py:349-353`). Bekerja.
- **`sky.py`** — sphere skala negatif dengan depth-write mati (`:157-166`),
  gradien zenith→horizon + sun glow pangkat 52. Bekerja, punya fallback tanpa
  shader yang sehat (`:151-156`).
- **`vhs_bloom.py`** — post-process CRT: barrel distortion, chromatic aberration,
  bloom threshold, scanline, vignette. Dipasang tanpa syarat ke `camera.shader`
  saat OpenGL (`app.py:202-208`). Loop bloom 7×7 per piksel (`:29-41`) — mahal,
  dan estetikanya (glitch/VHS) tidak berhubungan dengan Sims 1 maupun BRIEF.

### `meshes.py`

Superellipsoid ter-cache dengan eksponen 0.20 (`:27`), dibangun sekali dan
dipakai ulang. Kode bersih, mesh reuse benar. Masalahnya bukan implementasi
melainkan **kapan** dipakai (lihat poin 5 di atas).

### `props.py`

20 varian tekstur atap (`:8-29`) dipilih deterministik dari posisi (`:137`),
rumah multi-tile digabung otomatis dengan flood-scan (`:118-135`), atap kerucut
4-sisi diputar 45° (`:158-159`), plus cerobong, teras, pilar. **Ini bagian
rendering terbaik.** Sayangnya seluruh output-nya lewat `_create_entity` →
`soft=True` → membulat.

---

## 7. `data.py` — model konten

681 baris data murni tanpa dependensi rendering. Isi terverifikasi:

| Struktur | Jumlah | Bentuk |
|---|---:|---|
| `CROPS` | 8 | `{name, days, sell, cost, seasons[]}` |
| `CONSUMABLES` | 11 | `{heal_hp, heal_energy, buff?, buff_ms?, desc}` |
| `WILD_ITEMS` | 7 | `{name, sell, description, dangerous?}` |
| `HUMAN_NPCS` | 14 | `{name, type, gift, talks{}, gift_r}` |
| `SUPERNATURAL_NPCS` | 13 | idem |
| `ANIMAL_NPCS` | 9 | `{name, type, talks[], product}` |
| `SCHEDULES` | 36 | `[(jam, x, y, scene, activity), …]` |
| `QUEST_STAGES` | 12 | **list** `{s, t, d}` |
| `MINERALS` | 5 | `{name, sell, min_level, tier}` |
| `PICKAXE_RECIPES` | 5 | `{tier, name, cost_gold, needs{}}` |
| `SWORD_RECIPES` | 4 | `{id, name, cost_gold, damage, needs{}}` |
| `MOB_TEMPLATES` | 7 | `{name, hp, damage, min_lvl, max_lvl, speed, drops{}, xp}` |
| `LORE_ITEMS` | 6 | `{name, found_at, text}` |
| `SEASONAL_EVENTS` | 4 | `{name, day, scene, desc}` |
| `SHOP_ITEMS` | 9 | `{id, name, price, season}` |
| `BRANCHING_DIALOGUES` | 22 | `{text, choices[{text, next, effect, condition}]}` |
| `SIDE_QUESTS` | 1 | `{name, desc}` |

**Yang bagus:**

- **Dialog berjenjang.** `talks` bisa berupa dict dengan kunci `default`,
  `hearts_3/5/7/10`, `quest_5/10/11` dan dipilih dengan prioritas eksplisit
  (`panels.py:293-308`). 14 NPC manusia semua sudah punya lapisan lengkap.
  Ini fondasi relasi yang nyata.
- **Dialog bercabang** dengan `condition` (`min_hearts`, `has_item`,
  `side_quest_active`) dan `effect` (`hearts`, `gold`, `energy`, `sosial`,
  `give_item`, `take_item`, `start_side_quest`, `complete_side_quest`,
  `naga_defeated`) — interpreter di `panels.py:330-350` dan `:457-493`. Ini
  **mesin dialog data-driven yang bekerja**.
- `SCHEDULES` lengkap: 36/36 NPC punya jadwal, 0 jadwal yatim. Konvensi
  `(0, -1, -1, 'hidden', …)` untuk makhluk halus yang hanya keluar malam adalah
  trik yang rapi.

**Yang lemah / patut disebut:**

- `QUEST_STAGES` adalah **list**, tapi `quest_controller.py:31` memperlakukannya
  sebagai dict (`.get()`). Crash kalau jalurnya pernah tercapai.
- `LORE_ITEMS` punya 6 entri; hanya 2 yang bisa didapat (`buku_paman_arsa`,
  `peta_mimpi_maya` via `check_npc_lore_gift`, `quest_controller.py:316-319`).
  Tiga `fragmen_prasasti_*` **tidak pernah direferensikan kode manapun**; jalur
  dungeon justru memakai ID lain (`'dungeon_3'`) yang tidak ada di `LORE_ITEMS`.
- `SEASONAL_EVENTS` **tidak pernah diimpor**. Field `_pending_seasonal_event`
  di `player.py:144` diset nol kali dan hanya dibaca di `time_controller.py:228`.
- `SIDE_QUESTS` hanya 1 entri padahal UI panel siap menampilkan banyak
  (`panels.py:562-572`).
- Tidak ada model **objek** sama sekali. Tidak ada tabel `OBJECTS` dengan harga,
  kategori, motif yang diiklankan, atau footprint. Untuk Sims 1 ini adalah
  struktur data yang paling penting, dan `data.py` tidak memilikinya.
- `MOB_TEMPLATES` punya `xp` untuk ketujuh mob; **tidak ada sistem XP di
  seluruh repo**.

**Vonis:** `data.py` adalah aset. Model konten untuk *farming-RPG* di sini
lengkap dan konsisten. Model konten untuk *life-sim* (objek, interaksi objek,
pekerjaan, tagihan, sifat) belum dimulai.

---

## 8. 15 hambatan struktural terbesar menuju The Sims 1

Diurut dari yang paling menghalangi. "Biaya" = perkiraan kasar upaya.

| # | Hambatan | Bukti | Kenapa fatal | Biaya |
|---:|---|---|---|---|
| **1** | **Tidak ada model objek.** Dunia adalah 51 tile-ID enum, bukan katalog objek dengan state, harga, footprint, dan motif yang diiklankan. | `config.py:56-83`, `data.py` (tidak ada `OBJECTS`) | Sims 1 **adalah** simulasi objek. Pie menu, autonomi, buy mode, dan needs semuanya bersumber dari objek. Tanpa ini tak satupun dari empat sistem itu bisa dibangun dengan benar. | Besar |
| **2** | **Kamera perspektif follow-character.** | `app.py:187-191` | Seluruh bahasa visual Sims 1 (dimetrik 2:1, 4 rotasi, cutaway dinding, footprint grid diagonal) mustahil tanpa mengganti fondasi kamera. Juga mengubah cara semua HUD ditempatkan. | Sedang |
| **3** | **Tidak ada cutaway dinding.** Dinding adalah kubus solid `WALL_H=2.8`. | `world.py:518-545`, `config.py:12` | Tanpa ini interior tidak terbaca dan build mode tidak berguna. Butuh sistem tinggi-dinding per-arah-kamera. | Sedang |
| **4** | **Autonomi terputus.** VM lengkap ada, dunia tidak tersambung. | `behavior_vm.py:335-381`, `npc_brain.py:85-95` (nol pemanggil) | Sims tanpa autonomi bukan Sims. Butuh primitif dunia (GoTo, UseObject, SetMotive) dan lapisan advertising. | Sedang |
| **5** | **Tidak ada UI needs sama sekali.** | `panels.py:139-141` (list kosong), `panels.py:29` (folder `assets/ui/` tidak ada) | Control panel biru adalah wajah Sims 1. Termometer + mood bar adalah syarat mutlak untuk lulus perbandingan visual. Untungnya datanya sudah ada. | Kecil |
| **6** | **Empat `AttributeError` di jalur panas.** Dialog selesai, progres quest, jam/kalender, lore dungeon. | `panels.py:420`, `quest_controller.py:22,43`, `interaction_controller.py:222` | Kerusakan yang sudah ada akan menyamarkan kerusakan baru. Harus dibersihkan sebelum apapun dibangun di atasnya. | Sepele |
| **7** | **Progresi quest mati total.** `check_quests()` no-op senyap di 6 tempat. | `interaction_controller.py:396-400`, `time_controller.py:88-91` | Seluruh 12 tahap `QUEST_STAGES` tidak dapat maju dari gameplay. Untuk misteri StrangerVille yang butuh eskalasi bertahap, ini fondasi yang hilang. | Kecil |
| **8** | **Action queue bukan action queue.** Antrian koordinat, dieksekusi satu frame. | `interaction_controller.py:565-588` | Queue adalah antarmuka utama Sims 1. Harus dibangun ulang di atas `BehaviorThread` yang sudah benar. | Sedang |
| **9** | **1.227 Entity untuk satu ladang.** Tanpa batching/instancing/culling. | sensus `capture.py --dump`; `world.py:392-489` | Lot Sims yang berperabot akan jauh lebih padat. Batas performa akan tertabrak sebelum build/buy mode berguna. | Sedang |
| **10** | **Interior indoor di-render sebagai void putih.** Bug `has_horizon`. | `world.py:378` vs `scenes/scene_base.py:2,15` | Sims 1 berlangsung **di dalam ruangan**. Saat ini scene `house` benar-benar kosong putih. | Sepele |
| **11** | **Estetika "surreal digital" bertabrakan dengan target.** Kubus cyan/silinder magenta neon di 30% tile rumput, PointLight magenta indoor, halo magenta di kepala pemain, sapu terbang magenta, post-process VHS. | `world.py:497-505`, `world.py:388`, `player.py:268-269`, `interaction_controller.py:600-602`, `app.py:202-208` | Setiap frame yang diambil akan kalah dari referensi Sims 1 karena alasan ini saja, terlepas dari geometri. | Kecil |
| **12** | **Vitaboy terkunci ke path absolut satu mesin, dan `entities.py` tidak punya guard.** | `vitaboy/tso_paths.py:18-28`, `entities.py:219-221` | Aset terkuat proyek ini akan hilang total — dan `load_scene()` crash — di mesin manapun tanpa TSO. Juga skinning Python 10 Hz tidak akan menskala ke 8 Sim. Jalur GLB cepat sudah ada dan menganggur (`vitaboy_baked.py`). | Sedang |
| **13** | **Tidak ada build mode dan tidak ada buy mode, dan peta bersifat kode.** Setiap scene adalah fungsi Python yang membangun array tile. | `scenes/farm.py:6-35`, `scenes/town.py:6-31` | Build/buy menuntut peta sebagai **data yang bisa dimutasi dan diserialisasi**. Saat ini `state.save()` tidak menyimpan tile apapun kecuali `dungeon_tiles`. Perubahan tile runtime memicu `world.load_scene()` penuh (`interaction_controller.py:123`) — rebuild 1.227 entity. | Besar |
| **14** | **Tidak ada ekonomi rumah tangga, pekerjaan, atau tagihan.** Gold hanya dari jual panen/ikan. Tidak ada `job`, `salary`, `bills`, `career`, `skill` di `state.py`. | `state.py` keseluruhan | Loop harian Sims 1 (kerja → gaji → beli objek → objek isi motif) tidak punya satupun bagiannya. `npc_hearts` (0-10) adalah relasi satu-dimensi, bukan matriks daily/lifetime dua-arah. | Sedang |
| **15** | **Tidak ada thought balloon dan tidak ada Simlish.** Audio = beep prosedural pygame + loop akor ambient. | `sound.py:80-104`, `sound.py:197-395` | Dua penanda identitas Sims 1 yang paling langsung dikenali. Balloon butuh billboard + atlas ikon objek (yang butuh hambatan #1). Simlish butuh sintesis suku kata — tidak ada apapun ke arah itu. | Kecil–Sedang |

**Catatan lintas-hambatan:** #1 adalah akar dari #4, #8, #13, dan #15. Membangun
katalog objek dengan motif-advertising membuka empat hambatan lain sekaligus.
Sebaliknya, memperbaiki #5, #6, #7, #10, #11 semuanya murah dan langsung terlihat
di screenshot.

---

## 9. Status per-pilar Sims 1

Satu kata per pilar, dengan bukti.

| # | Pilar Sims 1 | Status | Bukti |
|---:|---|---|---|
| 1 | **Needs / motives** | **PARTIAL** | 3 dari 8 motif dengan decay berbasis waktu in-game: `config.py:96-98`, `state.py:63-65`, `time_controller.py:22-25`. Satu konsekuensi mekanis: `state.py:103-110`. Tanpa Comfort/Hygiene/Bladder/Room/Energy-sebagai-motif. |
| 2 | **Autonomy** | **STUB** | VM SimAntics lengkap: `behavior_vm.py:96-177`, `:335-418`. Di-tick tiap frame: `entities.py:305-306`. Nol efek pada dunia — `npc_brain.py:85-95` tidak punya pemanggil; gerakan NPC sebenarnya dari tabel statis `data.py:348-409` + wander acak `npc.py:39`. |
| 3 | **Object interactions** | **STUB** | Lima tile ID hardcoded dengan efek tetap: `interaction_controller.py:198-233` (kompor +20 energi, TV +10 senang, kursi +5 energi, ranjang→tidur, kotak pos→dialog). Tidak ada katalog objek, tidak ada state objek, tidak ada advertising. Tile jam & kalender `AttributeError` (`:222`, `:226`). |
| 4 | **Pie menu** | **PARTIAL** | Ada: opsi kondisional + preview efek motif + status terkunci — `interaction_controller.py:447-491`, `panels.py:843-867`. Tidak ada: bentuk radial, target objek, submenu, mouse hover. Panel kotak keyboard di `panels.py:781-798`. |
| 5 | **Action queue** | **STUB** | `player.action_queue` = list koordinat tile (`player.py:140`), semua dieksekusi dalam satu frame dengan tool saat ini (`interaction_controller.py:578-588`). Indikator = satu angka (`panels.py:777-778`). Queue Sims-1 yang benar ada di `behavior_vm.py:109-119` dan tidak dipakai pemain. |
| 6 | **Build mode** | **MISSING** | Tidak ada. Peta didefinisikan sebagai kode Python (`scenes/farm.py:6-35`), tidak diserialisasi ke save (`state.py:42-56` — hanya `dungeon_tiles`), dan mutasi tile memicu `world.load_scene()` penuh (`interaction_controller.py:123`). |
| 7 | **Buy mode** | **MISSING** | Yang terdekat: panel toko benih teks (`panels.py:609-616`, `data.py:538-548`, 9 item). Tidak ada katalog furnitur, tidak ada penempatan, tidak ada inventaris objek. |
| 8 | **Relationships** | **PARTIAL** | `npc_hearts` 0–10 satu-dimensi (`state.py:44`), naik dari hadiah (`interaction_controller.py:439`), dialog (`panels.py:416`), dan aksi pie. Dialog berjenjang per-hearts yang lengkap untuk 14 NPC (`data.py:52-61`, `panels.py:293-308`). Tidak ada: relasi dua-arah, daily vs lifetime, relasi NPC↔NPC, keluarga, romance, dampak sosial. |
| 9 | **Jobs / bills** | **MISSING** | Tidak ada field `job`/`career`/`salary`/`bills`/`skill` di `state.py`. Gold hanya dari jual hasil (`interaction_controller.py:90`, `:330`). Kotak pos hanya mengirim satu surat cerita (`panels.py:270-282`). |
| 10 | **Mood** | **PARTIAL** | `get_mood()` = rata-rata 3 need (`state.py:100-101`), dipakai untuk satu multiplier energi (`state.py:103-110` → `player.py:1001-1003`). Tidak ada mood bar, tidak ada dampak pada sosial/kerja/autonomi. |
| 11 | **Lot rendering + wall cutaway** | **MISSING** | Kamera perspektif follow (`app.py:187-191`), dinding kubus solid setinggi 2,8 (`world.py:518-522`, `config.py:12`), tidak ada level dinding / cutaway / rotasi lot. Scene indoor saat ini di-render sebagai void putih akibat bug `has_horizon` (`world.py:378` vs `scenes/scene_base.py:15`). |
| 12 | **Control panel UI** | **STUB** | HUD sudut yang tersebar: jam/tanggal/cuaca/gold kanan-atas, tool + HP/EN kiri-atas (`panels.py:108-154`). Tidak ada panel biru, tidak ada tombol Live/Buy/Build, tidak ada kontrol kecepatan, tidak ada termometer, tidak ada mood bar. Slot termometer ada tapi kosong (`panels.py:139-143`). |
| 13 | **Thought balloons** | **MISSING** | Nol referensi. Yang ada: flash text tengah layar (`panels.py:146-148`, `:219-225`) dan label nama billboard raksasa (`entities.py:242-245`). |
| 14 | **Simlish audio** | **MISSING** | Nol sintesis suara. Semua audio adalah gelombang prosedural pygame: 23 SFX (`sound.py:80-104`) + 6 loop akor ambient (`sound.py:197-395`). Tidak ada suku kata, tidak ada voice, tidak ada emosi vokal. |

**Rekapitulasi:** 0 WORKING · 5 PARTIAL · 4 STUB · 5 MISSING.

Satu pilar yang tidak ada di daftar tapi layak dicatat: **karakter Sims itu
sendiri** — mesh, tekstur, dan animasi TSO asli — sudah **WORKING**
(`vitaboy/avatar.py`, terverifikasi 33.332 aset ter-index dan tampil di layar).
Itu adalah bagian tersulit dari daftar ini, dan sudah selesai.

---

## 10. Lampiran: bukti runtime

Harness diverifikasi pada 2026-08-21 dengan game sungguhan yang diboot lewat
`tools/capture.py` / `game.app.Game3D`.

```
TEST 1: dialog end path
  -> RAISED: AttributeError 'Player3D' object has no attribute '_check_quest_progress'
TEST 2: interaction_controller.check_quests
  -> silent no-op (quest progression never runs)
TEST 3: QuestController.check_quest_progress direct
  -> RAISED: AttributeError 'GameState' object has no attribute 'npc_relations'
TEST 4: state.time_hm() (dipanggil saat interact tile jam)
  -> RAISED: AttributeError 'GameState' object has no attribute 'time_hm'
TEST 5: needs bars present in HUD?
  need_fill_ents: []   thermo tex: None
```

```
Vitaboy asset registry (scan 1,2 detik):
  archives 75 · total_entries 33332 · anims 5504 · meshes 2250
  skels 3 · outfits 1484 · appearances 5453
  mabd000_leathers.apr  -> ditemukan
  a2o-walking-loop.anim -> ditemukan
  adult.skel            -> ditemukan
```

```
Sensus entity scene 'farm' (25x18 tile):
  781 cube · 157 mesh · 151 cube(off) · 80 quad(off) · 34 sphere
  6 FarmAnimal|model=humanoid.obj   <- semua hewan ternak = mesh manusia
  total scene.children = 1227
```

Screenshot bukti disimpan di scratchpad sesi ini: `farm` 1280×720 dan 1920×1080
(kamera near-horizontal, kisi magenta, void putih di cakrawala, papan nama NPC
raksasa, HUD terpotong) dan `house` (interior putih kosong total).
