"""
entities.py — Refactored OOP EntitiesManager for Ursina Engine.
"""
import math, os, random
from pathlib import Path

from ursina import Entity, Vec3, color, destroy, Text, Texture
from .config import TILE_SIZE, GROUND_H, INVULN_AFTER_HIT_MS, WALKABLE
from .data import HUMAN_NPCS, SUPERNATURAL_NPCS, ANIMAL_NPCS, SCHEDULES, WILD_ITEMS, all_npcs
from .scenes import SCENES

from .npc import NPC
from .mob import Monster
from .animal import FarmAnimal

TS = TILE_SIZE
GH = GROUND_H

_MODELS_DIR = Path(__file__).resolve().parent.parent / 'assets' / 'models'
_ASSET_DIR = Path(__file__).resolve().parent.parent / 'assets' / 'textures'

_MODEL_CACHE: dict = {}
_TEX_CACHE: dict = {}

def _model_instance(cached):
    """Salinan lepas dari model cache — WAJIB, sama alasannya dengan
    meshes._instance() (BRIEF §8.1).

    Model hasil `loader.loadModel()` adalah NodePath Panda3D, dan sebuah
    NodePath hanya boleh punya SATU parent. `Entity.model = <NodePath>`
    me-reparent node itu, jadi actor kedua yang memakai nama model yang sama
    MENCURI geometri dari actor pertama. Diukur di scene farm sebelum perbaikan:
    dari 6 hewan yang semuanya memakai 'humanoid.obj', hanya SATU (yang dibuat
    terakhir) punya tight-bounds bervolume; lima sisanya kosong dan hanya
    menyisakan nameplate melayang.
    """
    if cached is None:
        return None
    from panda3d.core import NodePath
    holder = NodePath('_model_instance')
    copy = cached.copy_to(holder)
    copy.detach_node()
    return copy


def load_model_file(name: str):
    """Load model from assets/models/."""
    if not name: return None
    if name in _MODEL_CACHE:
        return _model_instance(_MODEL_CACHE[name])

    path_obj = _MODELS_DIR / f'{name}.obj'
    path_glb = _MODELS_DIR / f'{name}.glb'
    
    path = path_obj if path_obj.exists() else (path_glb if path_glb.exists() else None)
    if not path:
        _MODEL_CACHE[name] = None
        return None
        
    try:
        from panda3d.core import Filename
        from direct.showbase.ShowBaseGlobal import base
        fn = Filename.fromOsSpecific(str(path))
        m = base.loader.loadModel(fn)
        _MODEL_CACHE[name] = m
        return _model_instance(m)
    except Exception as e:
        import logging
        logging.warning(f"Failed to load model '{name}': {e}")
        _MODEL_CACHE[name] = None
        return None

# Tabel outfit sekarang dimiliki `vitaboy_npc.py` — di sana ia digabung dengan
# tabel kedua yang dulu tercecer dan tidak pernah diadu dengan yang ini, sehingga
# tiga orang lagi (ningsih, joko, pak_guru) punya wajah sendiri. Alias ini
# dipertahankan supaya kode lama yang mengimpor nama ini tidak putus.
from .vitaboy_npc import NPC_OUTFIT as NPC_APPEARANCES, resolve_outfit

# Radius warga mulai menoleh ke pemain (unit dunia), dikuadratkan supaya tidak
# perlu akar kuadrat di dalam loop NPC. 9 unit kira-kira sejauh mata memang
# masuk akal memperhatikan seseorang, dan cukup dekat sehingga hanya beberapa
# orang aktif sekaligus.
_R_TOLEH_KUADRAT = 9.0 * 9.0

# Player3D dibangun SETELAH EntitiesManager, jadi manager tidak bisa menerima
# referensinya lewat konstruktor. Satu slot modul, diisi Player3D saat lahir —
# jauh lebih jujur daripada menyusuri scene graph mencari pemain tiap frame.
_PEMAIN_AKTIF = [None]


def daftarkan_pemain(pl):
    """Dipanggil Player3D.__init__ supaya head-seek tahu harus melihat siapa."""
    _PEMAIN_AKTIF[0] = pl


def get_npc_model_name(npc_id):
    if npc_id == 'naga_bijak':
        return 'naga'
    if npc_id in ['genderuwo', 'kelelawar', 'pocong']:
        return f"mob_{npc_id}"
    return 'humanoid' # Fallback

def _can_walk(tx, ty, scene_name, dungeon_tiles=None):
    tx, ty = int(round(tx)), int(round(ty))
    if scene_name == 'dungeon' and dungeon_tiles:
        if ty < 0 or ty >= len(dungeon_tiles): return False
        if tx < 0 or tx >= len(dungeon_tiles[0]): return False
        return dungeon_tiles[ty][tx] in WALKABLE
    sc = SCENES.get(scene_name)
    if not sc: return False
    if tx < 0 or tx >= sc.w or ty < 0 or ty >= sc.h: return False
    return sc.tiles[ty][tx] in WALKABLE


class EntitiesManager:
    """Mengelola semua NPC, wild entity, dan mob 3D dengan pendekatan OOP."""

    def __init__(self, state):
        self.state = state
        self.scene_name = None
        self.actors = {}       # id -> BaseActor (NPC, FarmAnimal, Monster)
        self.wild_ents = {}    # idx -> Entity
        self._npc_sched_t = 0.0
        self._wild_update_t = 0.0
        self.brains = None

        self._init_data()
        self._spawn_wild_state()

        try:
            from .npc_brain import NPCBrains
            self.brains = NPCBrains(self.state)
        except Exception as e:
            import logging
            logging.warning(f"NPCBrains gagal init: {e}")
            self.brains = None

    def _init_data(self):
        s = self.state
        for npc_id in all_npcs():
            if npc_id not in s.npc_hearts:       s.npc_hearts[npc_id] = 0
            if npc_id not in s.npc_dialog_index: s.npc_dialog_index[npc_id] = 0
        self._update_npc_schedules()

    def _update_npc_schedules(self):
        s = self.state
        hour = s.get_hour()
        for npc_id in all_npcs():
            sched = SCHEDULES.get(npc_id, [])
            if not sched: continue
            current = sched[0]
            for entry in sched:
                if entry[0] <= hour: current = entry
                else: break
            target_scene = current[3]
            tx, ty = float(current[1]), float(current[2])

            if npc_id not in s.npc_positions:
                s.npc_positions[npc_id] = {
                    'scene': target_scene, 'x': tx, 'y': ty,
                    'target_x': tx, 'target_y': ty,
                    'sched_x': tx, 'sched_y': ty,
                    'activity': current[4], 'facing': 'down',
                }
            else:
                pos = s.npc_positions[npc_id]
                old_target_x = pos.get('target_x', pos['x'])
                old_target_y = pos.get('target_y', pos['y'])

                if pos['scene'] != target_scene:
                    pos['scene'] = target_scene
                    pos['x'] = tx
                    pos['y'] = ty
                    pos['target_x'] = tx
                    pos['target_y'] = ty
                    if 'path' in pos: pos.pop('path')
                else:
                    if abs(old_target_x - tx) > 0.1 or abs(old_target_y - ty) > 0.1:
                        path = None
                        if self.brains is not None:
                            path = self.brains.plan_path(pos['x'], pos['y'], tx, ty)
                        if path:
                            pos['path'] = path
                            nxt = pos['path'].pop(0)
                            pos['target_x'], pos['target_y'] = float(nxt[0]), float(nxt[1])
                        else:
                            pos['target_x'] = tx
                            pos['target_y'] = ty
                pos['sched_x'] = tx
                pos['sched_y'] = ty
                pos['activity'] = current[4]

    def _spawn_wild_state(self):
        s = self.state
        if s.wild_entities: return
        rng = random.Random(s.day * 7)
        for _ in range(3):
            x, y = rng.randint(2, 28), rng.randint(5, 22)
            s.wild_entities.append({'kind':'mandrake','x':x,'y':y,'scene':'mountain','moving':False})
        for scene in ['farm','mountain']:
            for _ in range(3):
                x, y = rng.randint(5, 20), rng.randint(5, 15)
                s.wild_entities.append({'kind':'running_mushroom','x':x,'y':y,'scene':scene,'moving':True})
        for scene in ['farm','town','lake']:
            for _ in range(5):
                x, y = rng.randint(3, 15), rng.randint(3, 12)
                s.wild_entities.append({'kind':'firefly','x':x,'y':y,'scene':scene,'moving':True,'night_only':True})
        for _ in range(15):
            x, y = rng.randint(2, 28), rng.randint(5, 22)
            s.wild_entities.append({
                'kind': rng.choice(['wild_herb','wild_berry']),
                'x':x,'y':y,'scene':'mountain','moving':False,
            })

    def load_scene(self, scene_name: str):
        self._clear_all()
        self.scene_name = scene_name
        if self.brains is not None:
            self.brains.rebuild_grid(scene_name, self.state.dungeon_tiles)
        
        # Spawn NPCs and Animals
        s = self.state
        from .data import LIVESTOCK_FOR_SALE
        for actor_id, pos in s.npc_positions.items():
            if pos.get('scene') != self.scene_name: continue
            if pos.get('x', -1) < 0: continue

            # Ternak penghasil hanya muncul kalau sudah dibeli. Tanpa baris ini
            # kandang penuh sejak hari pertama dan transaksi di Warung tidak
            # mengubah apa pun yang terlihat. Hewan bukan-ternak tidak lewat
            # sini sama sekali — mereka penghuni, bukan barang dagangan.
            if actor_id in LIVESTOCK_FOR_SALE and \
                    actor_id not in getattr(s, 'owned_animals', []):
                continue

            # Determine class
            if actor_id in ANIMAL_NPCS:
                actor = FarmAnimal(s, actor_id)
            else:
                actor = NPC(s, actor_id)
                
            actor.logical_x = pos['x']
            actor.logical_y = pos['y']
            actor.target_x = pos.get('target_x', pos['x'])
            actor.target_y = pos.get('target_y', pos['y'])
            if hasattr(actor, 'path') and 'path' in pos:
                actor.path = list(pos['path'])
            if hasattr(actor, 'sched_x'):
                actor.sched_x = pos.get('sched_x', pos['x'])
                actor.sched_y = pos.get('sched_y', pos['y'])
                actor.activity = pos.get('activity', '')
            
            # Position visually
            actor.position = (actor.logical_x * TS, 0, actor.logical_y * TS)
            
            # Setup Model
            lbl_y, lbl_scale = GH + 3.1, 5
            is_animal = actor_id in ANIMAL_NPCS
            if is_animal:
                # Hewan memakai rig prosedural berskala meter. Sebelum ini
                # get_npc_model_name() mengembalikan 'humanoid' untuk SEMUA
                # hewan — sapi, ayam dan kucing memakai mesh manusia yang sama.
                from .animal_models import build_animal
                h = build_animal(actor, ANIMAL_NPCS[actor_id].get('type', ''))
                # Hewan dibangun menghadap +Z (konvensi base_actor.sync_visuals),
                # dan kamera default juga memandang ke +Z — jadi pada rotation_y
                # 0 pemain selalu melihat PUNGGUNG hewan, sementara kepala,
                # tanduk, paruh dan moncong (satu-satunya yang membedakan
                # spesies) menghadap menjauh. Putar ke arah kamera, dengan
                # variasi deterministik supaya sekandang tidak seragam.
                # (sum(ord) — bukan hash(), yang di-randomisasi per proses)
                actor.rotation_y = 180 + (sum(map(ord, actor_id)) % 5 - 2) * 22
                # Nameplate duduk tepat di atas hewan. Di ketinggian manusia
                # (3,1 m) label ayam melayang lepas dari badannya sehingga
                # pemain tidak bisa memasangkan nama dengan bentuk.
                lbl_y, lbl_scale = h + 0.45, 2.6
            apr_list = None if is_animal else resolve_outfit(actor_id, default=False)
            # Vitaboy memuat aset TSO asli dari path absolut mesin tertentu
            # (vitaboy/tso_paths.py). Tanpa try/except, satu mesin tanpa TSO
            # membuat load_scene() crash total dan game tidak bisa dibuka sama
            # sekali. Pembungkus gagal-lunak ini WAJIB dipertahankan.
            if apr_list:
                try:
                    from .vitaboy_npc import build_vitaboy_human_npc
                    from .wajah import tinggi_varian
                    # Tinggi badan ikut jadi ciri orang. Di patokan Story of
                    # Seasons, Takakura yang pendek bungkuk di samping pemuda
                    # yang tegak sudah bisa dibedakan dari siluetnya saja,
                    # sebelum wajahnya kelihatan. Pengalinya 0,90-1,12 —
                    # cukup untuk terbaca, tidak cukup untuk membuat pintu,
                    # papan nama atau tinggi kamera meleset.
                    sc = 0.19 if actor_id in ('cici', 'bowo') else 0.32
                    sc *= tinggi_varian(actor_id)
                    # Pabrik memilih backend sendiri: Character Panda3D (skinning
                    # C++, 0,288 ms/avatar) kalau bisa, jatuh ke skinning Python
                    # (6,387 ms/avatar) kalau tidak. Lihat vitaboy_npc.py.
                    actor._va = build_vitaboy_human_npc(actor, actor_id, scale=sc,
                                                       apr_list=apr_list)
                    if actor._va is None:
                        raise RuntimeError('kedua backend avatar gagal')
                    actor.model = 'cube'  # dummy parent
                    actor.color = color.clear # hide dummy
                except Exception as e:
                    import logging
                    logging.warning(
                        f"Vitaboy gagal untuk '{actor_id}' ({e}); pakai model biasa.")
                    actor._va = None
                    apr_list = None
            if not apr_list and not is_animal:
                model_name = get_npc_model_name(actor_id)
                panda_model = load_model_file(model_name)
                if not panda_model:
                    model_name = 'humanoid'
                    panda_model = load_model_file(model_name)
                if panda_model:
                    # Mesh humanoid tidak punya warna sama sekali, dan satu
                    # mesh cuma punya satu entity.color. Tanpa ini setiap
                    # warga desa sampai ke layar sebagai gumpalan PUTIH POLOS
                    # di mesin tanpa instalasi TSO — bukan karena avatarnya
                    # hilang, tapi karena tidak ada yang pernah memberitahu
                    # warnanya. Diwarnai per-vertex, jadi kulit, baju, celana
                    # dan rambut muat dalam SATU entity. Lihat human_paint.py
                    # untuk kenapa bukan lima entity.
                    warnai = (model_name == 'humanoid')
                    if warnai:
                        try:
                            from .human_paint import paint_humanoid, palet_untuk
                            warnai = paint_humanoid(panda_model, palet_untuk(actor_id))
                        except Exception as e:
                            import logging
                            logging.warning(f"human_paint gagal untuk '{actor_id}': {e}")
                            warnai = False
                        # Proporsi chibi juga di jalur cadangan. Di mesin tanpa
                        # instalasi TSO SEMUA warga lewat sini, dan kalau hanya
                        # avatar TSO yang dibuat chibi maka mesin itu diam-diam
                        # menampilkan desa berproporsi dewasa. Lihat wajah.py.
                        try:
                            from .wajah import chibikan_humanoid
                            chibikan_humanoid(panda_model)
                        except Exception as e:
                            import logging
                            logging.warning(f"chibikan_humanoid gagal '{actor_id}': {e}")
                    actor.model = panda_model
                    actor.scale = 1.0
                    if warnai:
                        # WAJIB, dan bukan sekadar hiasan. Lampu di scene ini
                        # memicu setShaderAuto() Panda3D (lihat app.py:74), dan
                        # shader hasil generator itu MENGABAIKAN kolom warna
                        # vertex — diuji: mesh yang sudah diwarnai tetap keluar
                        # putih pucat sampai smooth_shader dipasang. Yang membaca
                        # p3d_Color cuma smooth_shader, jadi tanpa baris ini
                        # seluruh kerja pewarnaan tidak sampai ke layar.
                        try:
                            from .smooth_shader import apply_smooth
                            apply_smooth(actor, has_texture=False)
                        except Exception:
                            pass
                else:
                    actor.model = 'cube'
                    
            # Setup Label
            all_d = {**HUMAN_NPCS, **SUPERNATURAL_NPCS, **ANIMAL_NPCS}
            name = all_d.get(actor_id, {}).get('name', actor_id)
            actor._lbl = Text(name, parent=actor, billboard=True,
                             position=(0, lbl_y, 0),
                             scale=lbl_scale, color=color.rgb(255, 240, 160),
                             background=True)
                             
            self.actors[actor_id] = actor

        # Spawn Wild
        for i, w in enumerate(s.wild_entities):
            if w['scene'] != self.scene_name: continue
            if w.get('night_only') and not s.is_night(): continue
            px, py = w['x'] * TS, w['y'] * TS
            # Simple fallback for wild entities, no complex procedural shapes
            e = Entity(model='quad', position=(px, GH + 0.25, py), scale=0.5, billboard=True)
            self.wild_ents[i] = e
            
        # Spawn Mobs
        self._spawn_mobs_for_scene()

    def spawn_mobs(self, mob_specs: list):
        self.state.mobs = mob_specs
        # Remove old mobs
        for k in list(self.actors.keys()):
            if isinstance(self.actors[k], Monster):
                destroy(self.actors[k])
                del self.actors[k]
        self._spawn_mobs_for_scene()

    def _spawn_mobs_for_scene(self):
        s = self.state
        if self.scene_name != 'dungeon': return
        for i, mob in enumerate(s.mobs):
            actor_id = f"mob_{i}"
            actor = Monster(s, actor_id, mob)
            actor.position = (actor.logical_x * TS, 0, actor.logical_y * TS)
            
            kind = mob['kind']
            is_boss = mob.get('is_boss', False)
            sc = 1.4 if is_boss else 1.0
            
            model_name = 'naga' if is_boss else f"mob_{kind}"
            panda_model = load_model_file(model_name)
            if panda_model:
                actor.model = panda_model
                actor.scale = sc
            else:
                # Empat dari tujuh mob (`tikus_gua`, `banaspati`, `kuntilanak`,
                # `leak`) tidak punya mesh sendiri dan jatuh ke humanoid.obj.
                # Mereka HUMANOID, jadi mereka ikut aturan proporsi yang sama
                # dengan warga desa; kalau tidak, satu dungeon berisi mob
                # berkepala dewasa yang dipukul oleh pemain berkepala chibi.
                panda_fallback = load_model_file('humanoid')
                if panda_fallback:
                    try:
                        from .wajah import chibikan_humanoid
                        chibikan_humanoid(panda_fallback)
                    except Exception as e:
                        import logging
                        logging.warning(f"chibikan_humanoid gagal '{actor_id}': {e}")
                    actor.model = panda_fallback
                else:
                    actor.model = 'cube'
                actor.scale = sc
                
            # HP Bar
            hp_y = GH + (3.5 if is_boss else 2.4) * sc
            actor._bg_bar = Entity(parent=actor, model='cube', position=(0, hp_y, 0), scale=(0.9*sc, 0.10, 0.10), color=color.rgb(45, 45, 45))
            actor._hp_bar = Entity(parent=actor, model='cube', position=(0, hp_y, -0.02), scale=(0.9*sc, 0.08, 0.08), color=color.rgb(225, 48, 48))
            
            self.actors[actor_id] = actor

    def update(self, dt: float):
        s = self.state

        # Posisi pemain untuk head-seek, dihitung SEKALI per frame. Kalau
        # dihitung di dalam loop NPC, ongkosnya ikut naik seiring jumlah warga
        # — persis pola yang membuat frame proyek ini berat sejak awal
        # (lihat _bench/reports/profil-logika.md).
        _lihat_pemain = None
        pl = _PEMAIN_AKTIF[0]
        if pl is not None:
            try:
                _lihat_pemain = (pl.world_x, pl.world_y + 1.6, pl.world_z)
            except Exception:
                _lihat_pemain = None
        
        if self.brains is not None:
            self.brains.tick(dt)

        self._npc_sched_t += dt
        if self._npc_sched_t >= 30:
            self._npc_sched_t = 0
            self._update_npc_schedules()

        # Build local walk function for actors
        def can_walk_fn(nx, ny):
            return _can_walk(nx, ny, self.scene_name, s.dungeon_tiles)

        # Update all OOP actors
        for actor_id, actor in list(self.actors.items()):
            if isinstance(actor, Monster):
                if actor.hp <= 0:
                    if actor.is_boss: s.naga_defeated = True
                    if actor.mob_spec in s.mobs:
                        s.mobs.remove(actor.mob_spec)
                    destroy(actor)
                    del self.actors[actor_id]
                    continue
                actor.update_ai(dt, s.player_x, s.player_y, can_walk_fn)
                
                # Sync state back to dict so game can read it
                actor.mob_spec['x'] = actor.logical_x
                actor.mob_spec['y'] = actor.logical_y
                actor.mob_spec['hp'] = actor.hp
                
                # Update visual HP bar
                ratio = max(0, actor.hp / max(actor.mob_spec.get('max_hp', 1), 1))
                sc = 1.4 if actor.is_boss else 1.0
                actor._hp_bar.scale_x = 0.9 * sc * ratio

                if actor.dmg_flash_ms > 0:
                    actor.color = color.white
                else:
                    actor.color = color.white # Revert to normal
                
            elif isinstance(actor, NPC):
                actor.update_ai(dt, self.brains, can_walk_fn)
                if actor_id in s.npc_positions:
                    s.npc_positions[actor_id]['x'] = actor.logical_x
                    s.npc_positions[actor_id]['y'] = actor.logical_y
                    s.npc_positions[actor_id]['target_x'] = actor.target_x
                    s.npc_positions[actor_id]['target_y'] = actor.target_y
                    s.npc_positions[actor_id]['path'] = list(actor.path)
                
                is_sleeping = getattr(actor, 'activity', '') == 'sleeping'
                if is_sleeping:
                    if ' (Tidur)' not in actor._lbl.text:
                        actor._lbl.text = f"{actor._lbl.text.split(' (Tidur)')[0]} (Tidur)"
                    actor._lbl.position = (0, 0, 2.4)
                    actor.rotation_x = -90
                    actor.y = GH + 0.15
                else:
                    actor._lbl.text = actor._lbl.text.split(' (Tidur)')[0]
                    actor._lbl.position = (0, GH + 3.1, 0)
                actor._lbl.position = (0, GH + 3.1, 0)
                
                is_moving_now = abs(actor.logical_x - actor.target_x) > 0.02 or abs(actor.logical_y - actor.target_y) > 0.02
                if is_moving_now:
                    actor.rotation_y = math.degrees(math.atan2(actor.target_x - actor.logical_x, actor.target_y - actor.logical_y))
                
                if hasattr(actor, '_va') and actor._va:
                    if is_sleeping:
                        actor._va.set_animation("a2o-slide-normal")
                    elif is_moving_now:
                        actor._va.set_animation("a2o-walking-loop")
                    else:
                        actor._va.set_animation("a2a-talk-idle-loop")
                    # Head-seek: warga menoleh ke pemain kalau ia cukup dekat.
                    # Ini tanda khas Sims/FreeSO — desa terasa memperhatikan,
                    # bukan cuma berjalan melewati kita. Ongkosnya SATU joint
                    # per orang (lihat HeadSeekController di animator.py):
                    # `look_at_world` baru membangun apa pun saat pertama kali
                    # ada yang benar-benar dipandang, dan `update()` keluar di
                    # baris pertama untuk kepala yang sudah lurus kembali.
                    if _lihat_pemain is not None and not is_sleeping:
                        dxp = _lihat_pemain[0] - actor.world_x
                        dzp = _lihat_pemain[2] - actor.world_z
                        dekat = (dxp * dxp + dzp * dzp) <= _R_TOLEH_KUADRAT
                        try:
                            actor._va.look_at_world(_lihat_pemain if dekat else None)
                        except AttributeError:
                            # Jalur VitaboyAvatar (skinning Python) belum punya
                            # head-seek. Bukan error — orangnya cuma tidak menoleh.
                            pass
                    actor._va.update(dt)
                else:
                    if not is_moving_now:
                        actor.rotation_x = 0
                    actor.y = 0
                    
            elif isinstance(actor, FarmAnimal):
                actor.update_ai(dt, can_walk_fn)
                if actor_id in s.npc_positions:
                    s.npc_positions[actor_id]['x'] = actor.logical_x
                    s.npc_positions[actor_id]['y'] = actor.logical_y
                    s.npc_positions[actor_id]['target_x'] = actor.target_x
                    s.npc_positions[actor_id]['target_y'] = actor.target_y

            # Let the actor smoothly move visually
            actor.sync_visuals(dt, TS, GH)

        # Wild update tiap 0.8s
        self._wild_update_t += dt
        if self._wild_update_t >= 0.8:
            self._wild_update_t = 0
            self._update_wild_ai()
        self._sync_wild_visuals()

    def _update_wild_ai(self):
        s = self.state
        rng = random.Random()
        px, py = s.player_x, s.player_y
        for w in s.wild_entities:
            if w['scene'] != self.scene_name: continue
            if w.get('night_only') and not s.is_night(): continue
            if not w.get('moving'): continue
            dist = math.hypot(w['x']-px, w['y']-py)
            if w['kind'] == 'running_mushroom' and dist <= 3:
                dx_ = 1 if w['x']>px else (-1 if w['x']<px else rng.choice([-1,1]))
                dy_ = 1 if w['y']>py else 0
                nx_, ny_ = w['x']+dx_, w['y']+dy_
                if _can_walk(nx_, ny_, self.scene_name, s.dungeon_tiles):
                    w['x'], w['y'] = nx_, ny_
            elif w['kind'] == 'firefly':
                dx_, dy_ = rng.choice([-1,0,1]), rng.choice([-1,0,1])
                nx_, ny_ = w['x']+dx_, w['y']+dy_
                if _can_walk(nx_, ny_, self.scene_name, s.dungeon_tiles):
                    w['x'], w['y'] = nx_, ny_

    def _sync_wild_visuals(self):
        s = self.state
        for i, w in enumerate(s.wild_entities):
            if i not in self.wild_ents: continue
            e = self.wild_ents[i]
            e.x = w['x']*TS; e.z = w['y']*TS
            if w.get('night_only'):
                e.enabled = s.is_night()

    def _clear_all(self):
        for actor in self.actors.values():
            destroy(actor)
        self.actors.clear()
        for e in self.wild_ents.values():
            destroy(e)
        self.wild_ents.clear()

    def get_nearest_npc(self, tx: int, ty: int, max_dist_tiles: float = 3.0):
        s = self.state
        best_d, best_id = max_dist_tiles + 1, None
        for npc_id, pos in s.npc_positions.items():
            if pos.get('scene') != s.scene_name: continue
            if pos.get('x', -1) < 0: continue
            d = math.hypot(pos['x'] - tx, pos['y'] - ty)
            if d < best_d:
                best_d, best_id = d, npc_id
        if best_id is None: return None
        return {'id': best_id}

    def attack_mobs(self, tx: int, ty: int, attack_range: float, damage: int) -> int:
        s = self.state
        if s.scene_name != 'dungeon': return 0
        killed = 0
        wx, wz = tx * TS, ty * TS
        for mob in list(s.mobs):
            mx, mz = mob['x'] * TS, mob['y'] * TS
            dist = math.sqrt((wx-mx)**2 + (wz-mz)**2)
            if dist <= attack_range:
                mob['hp'] -= damage
                mob['dmg_flash_ms'] = 200
                
                # Forward to actor so it flashes
                for a in self.actors.values():
                    if getattr(a, 'mob_spec', None) == mob:
                        a.hp -= damage
                        a.dmg_flash_ms = 200
                        
                if mob['hp'] <= 0:
                    for item, n in mob.get('drops', {}).items():
                        s.inventory[item] = s.inventory.get(item, 0) + n
                    if mob.get('is_boss'):
                        s.naga_defeated = True
                    killed += 1
                    s.mobs.remove(mob)
        return killed

    def try_capture_wild(self, tx: int, ty: int, state) -> tuple | None:
        import random as rng_mod
        sc = state.scene_name
        px, pz = tx * TS, ty * TS
        for w in list(state.wild_entities):
            if w['scene'] != sc: continue
            wx, wz = w['x'] * TS, w['y'] * TS
            if math.sqrt((px-wx)**2 + (pz-wz)**2) > 3.0: continue
            kind = w['kind']
            rates = {'running_mushroom': 0.60, 'firefly': 0.70,
                     'mandrake': 0.30, 'wild_herb': 0.90, 'wild_berry': 0.90}
            if rng_mod.random() < rates.get(kind, 0.5):
                state.wild_entities.remove(w)
                # Cleanup visually
                for i, we in list(self.wild_ents.items()):
                    if we.x == wx and we.z == wz:
                        destroy(we)
                        del self.wild_ents[i]
                item = WILD_ITEMS.get(kind, {})
                return kind, item.get('sell', 10)
        return None

def respawn_wild_at_morning(state):
    rng = random.Random()
    for scene in ['farm', 'mountain']:
        for _ in range(rng.randint(2, 4)):
            x, y = rng.randint(2, 20), rng.randint(5, 15)
            state.wild_entities.append({
                'kind': rng.choice(['wild_herb', 'wild_berry']),
                'x': x, 'y': y, 'scene': scene, 'moving': False,
            })
