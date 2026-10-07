# Inspirasi dari Repo Open-Source — Temuan & Adaptasi untuk Lembah Karsa 3D

Dipelajari langsung dari kode (clone di `tools/refs/`). **Pola, bukan salinan.**

---

## 🎨 GRAPHIC/ATMOSFER — `mandaw2014/Forest` ⭐ paling berharga
**Temuan:**
- `scene.fog_density = 0.008` + `scene.fog_color = color.hex(...)` → kabut atmosferik 1 baris.
- **Sun pencetak bayangan yang MENGIKUTI player** (`sun.py`): `DirectionalLight.setShadowCaster(True, res, res)`, `lens.setFilmSize((200,200))`, tiap frame `dlnp.setPos(player.world_position)`. Bayangan tajam hanya di sekitar player → dramatis + hemat.
- **Distance culling**: `if distance(player, tree) < 400: tree.enabled=True else False` → matikan prop jauh.
- Threaded asset loading (`direct.stdpy.thread`).
- 400 pohon → rimba padat (vibe Shaman Quest).

**Adaptasi Lembah Karsa:**
- [ ] Tune fog: outdoor density ~0.012–0.02, warna abu/earthy (mist Shaman Quest).
- [ ] Tambah sun shadow-caster mengikuti player (sekarang `shadows=False`) → bayangan dramatis DE.
- [ ] Distance-culling untuk `_obj_ents` (props banyak) → FPS naik.

## 🕹️ GAMEPLAY/COMBAT — `mandaw2014/sword_combat`
**Temuan:**
- Enemy AI: lerp ke player (`x += (target.x-x)*3*dt`) + raycast bawah utk gravitasi + `disable()` saat health≤0.
- Pedang/busur = child entity; collision/hit dicek saat ayun.
- Movement: boxcast per-sumbu (X/Z terpisah) + slope handling.

**Adaptasi:** combat kita sudah setara. Ambil: **crosshair** (`Entity quad parent=camera`) + feedback hit yang lebih jelas.

## 🖥️ HUD/HOTBAR — `kairess/minecraft-clone`
**Temuan:**
- **Hotbar**: `hand = Entity(parent=camera.ui, model=..., texture=..., scale=0.2, position=Vec2(0.6,-0.6))`.
- **Animasi pakai**: saat klik, `hand.position` digeser (efek "pukul"), lalu balik.
- Pilih item via angka: `if key.isdigit(): block_id=int(key)`.

**Adaptasi:** tampilkan **alat aktif** di `camera.ui` pojok bawah + animasi saat dipakai. Dasar inventory/hotbar Harvest Moon.

## ⚙️ SYSTEM/PERFORMANCE — `cpbeto/PyAO` (Argentum Online)
**Temuan:**
- `Texture.default_filtering = None` → **pixel art tajam** (cocok dgn pixelation Shaman Quest kita).
- **Sprite/entity pooling**: reuse entity, `enable()/disable()` — jangan recreate.
- **`need_to_render` flag**: render ulang HANYA saat ada perubahan (bukan tiap frame).
- Tile data simpan **exit/portal** langsung (`tile['exit']`) — seperti kita.
- Tile berlapis (z-layers).

**Adaptasi:**
- [ ] `Texture.default_filtering = None` global → pixel art lebih tajam.
- [ ] Pooling untuk wild entities / mob (sudah sebagian).

## 👹 DOOM HUD — `hamedsheygh/DoomMaker`
**Temuan:**
- **Senjata HUD**: `Entity(model='quad', texture='DOOMGUN.png', parent=camera.ui, position=(0,-0.4))` + swap texture saat nembak.
- **Enemy billboard** (`billboard=True`) → sprite 2D selalu hadap kamera (gaya Doom).
- Map dari grid (0=ground,1=wall,2=enemy).

**Adaptasi (GUI Doom yang kamu minta):**
- [ ] **Bottom HUD bar** ala Doom: panel di bawah layar berisi wajah karakter + HP/Energi/Emas + alat aktif (ikon, bukan teks bertumpuk).
- [ ] Sprite alat/senjata di `camera.ui` bawah-tengah.

---

## RINGKASAN PRIORITAS ADAPTASI (gabungan, sesuai keinginanmu)
1. **HUD Doom** (DoomMaker + minecraft hotbar): bottom-bar wajah+stats+alat, sprite alat di camera.ui.
2. **Inventory Harvest Moon** (minecraft hotbar + grid): slot bergambar, navigasi.
3. **Atmosfer** (Forest): fog mist + bayangan player-following + vegetasi padat.
4. **Pixel tajam + performa** (PyAO): `default_filtering=None` + distance culling.
5. **Combat polish** (sword_combat): crosshair + feedback hit.

> Semua bisa diverifikasi lewat workflow capture offscreen (`tools/capture_scene.py`).
