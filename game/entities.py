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


def load_texture_file(name: str):
    """Load & cache tekstur PNG dari assets/textures/ via PIL (bypass string-search Ursina)."""
    if not name:
        return None
    if name in _TEX_CACHE:
        return _TEX_CACHE[name]
    p = _ASSET_DIR / f'{name}.png'
    tex = None
    if p.exists():
        try:
            from PIL import Image
            tex = Texture(Image.open(p))
        except Exception as e:
            import logging
            logging.warning(f"Gagal load tekstur '{name}': {e}")
    _TEX_CACHE[name] = tex
    return tex


# ─── MATERIAL RELIK ARKEOLOGIS (gaya @archaeologyart) ─────────────────────────
# Makhluk halus & mob = artefak kuno yang hidup. (tekstur, tint warna)
_RELIC_MATERIAL = {
    'mob_pocong':    ('relic_terracotta', color.rgb(205, 195, 178)),  # mumi terakota
    'mob_genderuwo': ('relic_bronze',     color.rgb(190, 200, 180)),  # arca perunggu raksasa
    'mob_kelelawar': ('relic_andesite',   color.rgb(175, 180, 185)),  # kelelawar batu
    'naga':          ('relic_bronze',     color.rgb(185, 195, 175)),  # naga perunggu purba
}
_RELIC_DEFAULT = ('relic_andesite', color.rgb(180, 182, 180))  # arca batu generik

# Roh humanlike = ARCA-HUMANOID RELIK (basis humanoid + permukaan artefak, gaya DE).
# (tekstur, tint warna, skala) — skala basis humanoid 0.62 (~1.86m); disesuaikan peran.
_SPIRIT_RELIC = {
    'kuntilanak':    ('relic_andesite',   color.rgb(180, 185, 190), 0.70),  # arca wanita, tinggi-ramping
    'genderuwo':     ('relic_bronze',     color.rgb(190, 200, 175), 0.92),  # arca perunggu raksasa
    'pocong':        ('relic_terracotta', color.rgb(205, 195, 178), 0.60),  # mumi terakota
    'wewe_gombel':   ('relic_terracotta', color.rgb(198, 188, 170), 0.52),  # terakota anak (kecil)
    'banaspati':     ('relic_bronze',     color.rgb(200, 160, 120), 0.66),  # api → perunggu membara
    'leak_bali':     ('relic_andesite',   color.rgb(185, 180, 175), 0.62),  # topeng batu
    'bidadari':      ('relic_andesite',   color.rgb(205, 205, 198), 0.68),  # arca bidadari pucat
    'dewa_angin':    ('relic_bronze',     color.rgb(195, 200, 185), 0.78),  # arca dewa
    'jin_kebun':     ('relic_andesite',   color.rgb(175, 182, 168), 0.64),
    'demit_tua':     ('relic_andesite',   color.rgb(168, 172, 165), 0.58),
    'tuyul_pencuri': ('relic_terracotta', color.rgb(195, 180, 160), 0.45),  # terakota kecil
}

# Mob/roh NON-manusia yang tetap pakai mesh khusus (bukan humanoid)
_NONHUMAN_RELIC_IDS = {'naga_bijak', 'kelelawar'}

# Dewa-pertapa (ala Siwa Mahayogi) — arca emas-perunggu yang menjulang & beraura
_DEITY_IDS = {'petapa_srimana'}

def _add_deity_aura(actor):
    """Aura ilahi untuk dewa-pertapa (ala Siwa): halo + tetesan cahaya melayang."""
    try:
        # Halo cincin di belakang kepala
        halo = Entity(parent=actor, model='circle', position=(0, 2.2, 0.15),
                      scale=1.6, color=color.rgb(255, 226, 150),
                      double_sided=True, billboard=True)
        try: halo.setLightOff()
        except Exception: pass
        actor._halo = halo
        # Tetesan cahaya (motif air Ganga turun dari rambut) — beberapa titik
        actor._aura_motes = []
        for i in range(5):
            m = Entity(parent=actor, model='sphere',
                       position=(math.sin(i*1.3)*0.5, 1.6 + i*0.18, math.cos(i*1.3)*0.5),
                       scale=0.10, color=color.rgb(150, 210, 255))
            try: m.setLightOff()
            except Exception: pass
            actor._aura_motes.append(m)
    except Exception as e:
        import logging
        logging.warning(f"deity aura gagal: {e}")


# ─── AKSESORI PER-PERAN untuk NPC Vitaboy (model, pos, scale, rgb) ─────────────
# Diposisikan di ruang actor (figur Vitaboy ~1.8 unit tinggi). Front = +z.
_ROLE_ACCESSORIES = {
    'sari': [   # Warung — celemek putih kusam + ikat kepala
        ('cube', (0, 0.80, 0.15), (0.50, 0.66, 0.06), (205, 200, 188)),
        ('cube', (0, 1.14, 0.14), (0.30, 0.28, 0.05), (205, 200, 188)),
        ('cube', (0, 1.60, 0.00), (0.44, 0.20, 0.44), (165, 95, 85)),
    ],
    'budi': [   # Pandai besi — apron kulit + palu
        ('cube',     (0, 0.82, 0.15),    (0.52, 0.70, 0.07), (112, 80, 50)),
        ('cube',     (0, 1.16, 0.14),    (0.32, 0.30, 0.06), (95, 66, 40)),
        ('cylinder', (0.36, 0.95, 0.10), (0.05, 0.40, 0.05), (120, 85, 50)),
        ('cube',     (0.36, 1.18, 0.10), (0.16, 0.12, 0.12), (110, 112, 118)),
    ],
    'raka': [   # Dokter klinik — jas putih + tas
        ('cube', (0, 0.95, 0.14),    (0.48, 0.86, 0.10), (222, 224, 226)),
        ('cube', (0.32, 0.78, 0.10), (0.20, 0.18, 0.12), (90, 70, 55)),
    ],
    'maya': [   # Studio — selempang + buku
        ('cube', (0.0, 0.95, 0.16),  (0.10, 0.70, 0.05), (120, 90, 140)),
        ('cube', (0.30, 0.80, 0.10), (0.18, 0.24, 0.12), (150, 70, 55)),
    ],
    'kapten_kuro': [  # Kapten — topi + lis
        ('cube', (0, 1.62, 0.00), (0.52, 0.16, 0.52), (38, 42, 58)),
        ('cube', (0, 1.60, 0.22), (0.52, 0.06, 0.18), (30, 34, 48)),
    ],
    'pak_guru': [  # Pak Hadi (guru) — kacamata + buku
        ('cube', (0, 1.55, 0.20),    (0.30, 0.05, 0.05), (40, 40, 45)),
        ('cube', (0.30, 0.82, 0.10), (0.16, 0.22, 0.10), (90, 120, 90)),
    ],
    'jaka_ronda': [  # Ronda — selempang merah
        ('cube', (0, 0.98, 0.16), (0.55, 0.12, 0.05), (160, 60, 55)),
    ],
    'mbok_jum': [   # Nenek — selendang
        ('cube', (0, 1.22, 0.00), (0.52, 0.32, 0.30), (150, 110, 130)),
    ],
}

def _add_role_accessories(actor, npc_id):
    """Tempel aksesori sesuai peran NPC (celemek/apron/topi/palu) di atas avatar."""
    specs = _ROLE_ACCESSORIES.get(npc_id)
    if not specs:
        return
    actor._role_acc = []
    for model, pos, scale, col in specs:
        try:
            e = Entity(parent=actor, model=model, position=pos, scale=scale,
                       color=color.rgb(*col))
            try:
                from .smooth_shader import apply_smooth
                apply_smooth(e, has_texture=False)
            except Exception:
                try: e.setLightOff()
                except Exception: pass
            actor._role_acc.append(e)
        except Exception as ex:
            import logging
            logging.warning(f"role accessory gagal ({npc_id}): {ex}")


def _apply_relic_material(actor, model_name, override=None):
    """Pasang tekstur artefak + smooth_shader ke actor (makhluk relik).
    override=(tex_name, tint) untuk per-id (roh humanoid)."""
    if override is not None:
        tex_name, tint = override
    else:
        tex_name, tint = _RELIC_MATERIAL.get(model_name, _RELIC_DEFAULT)
    tex = load_texture_file(tex_name)
    if tex is not None:
        actor.texture = tex
        actor.color = tint
        try:
            from .smooth_shader import apply_smooth
            apply_smooth(actor, has_texture=True)
        except Exception:
            pass

def load_model_file(name: str):
    """Load model from assets/models/."""
    if not name: return None
    if name in _MODEL_CACHE:
        return _MODEL_CACHE[name]
        
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
        return m
    except Exception as e:
        import logging
        logging.warning(f"Failed to load model '{name}': {e}")
        _MODEL_CACHE[name] = None
        return None

NPC_APPEARANCES = {
    'arya': ['mabd000_sw__default.apr', 'mahd001_romeo.apr'],
    'sari': ['fabd002_mom01.apr', 'fahd001_sharon.apr', 'fahl001_sharon.apr'],
    'raka': ['mabd000_sl__teepjs.apr', 'mahd001_ross.apr'],
    'maya': ['fabd001_slacker.apr', 'fahd001_shannon01.apr', 'fahl001_shannon01.apr'],
    'mbok_jum': ['fabd002_gma1.apr', 'fahd001_alt.apr', 'fahl001_alt.apr'],
    'budi': ['mabd000_leathers.apr', 'mahd000_proxy.apr'],
    'jaka_ronda': ['mabd000_robin.apr', 'mahd001_robin.apr'],
    'kapten_kuro': ['mabd000_leathers3.apr', 'mahd002_asian.apr'],
    'cici': ['fabd001_summer01.apr'],
    'bowo': ['mabd000_sl__teepjs2.apr'],
    # Tambahan: semua human NPC pakai Vitaboy (sebelumnya fallback humanoid)
    'joko':     ['mabd000_sl__teepjs.apr', 'mahd001_ross.apr'],
    'ningsih':  ['fabd002_mom01.apr', 'fahd001_sharon.apr', 'fahl001_sharon.apr'],
    'pak_guru': ['mabd000_leathers.apr', 'mahd000_proxy.apr'],   # Pak Hadi
    'kru_kuro': ['mabd000_sl__teepjs2.apr', 'mahd002_asian.apr'],
    # petapa_srimana pakai model prosedural khusus (petapa_model.py), bukan Vitaboy
}

# ─── PALET WARNA NPC (Disco Elysium decay aesthetic) ──────────────────────────
# Untuk NPC yang tidak punya Vitaboy/model khusus — tinted fallback humanoid
_ACTOR_PALETTE = {
    # Manusia — warna kulit/baju lapuk, tone tanah
    'arya':        color.rgb(155, 132, 105),   # pemuda kerja, coklat hangat
    'sari':        color.rgb(148, 125, 100),   # pemilik warung, lelah
    'raka':        color.rgb(138, 118,  92),   # nelayan, terbakar matahari
    'maya':        color.rgb(145, 128, 108),   # dokter, abu pudar
    'mbok_jum':    color.rgb(128, 108,  85),   # nenek, sangat lapuk
    'budi':        color.rgb(142, 120,  95),   # pandai besi, abu gelap
    'jaka_ronda':  color.rgb(118, 108,  92),   # penjaga, grim
    'kapten_kuro': color.rgb(108,  98,  82),   # kapten, paling gelap
    'cici':        color.rgb(158, 138, 115),   # anak, sedikit lebih cerah
    'bowo':        color.rgb(150, 132, 110),
    # Makhluk supernatural — pucat/abu/gelap
    'naga_bijak':  color.rgb( 68,  90, 115),   # biru-abu dalam
    'genderuwo':   color.rgb( 82, 102,  82),   # olive gelap, berat
    'kelelawar':   color.rgb( 55,  52,  72),   # ungu-abu gelap
    'pocong':      color.rgb(185, 178, 168),   # putih kain kafan kusam
}

# ─── VISUAL WILD ENTITIES (size, color) ───────────────────────────────────────
_WILD_VISUALS = {
    'mandrake':         (0.38, color.rgb( 52,  82,  45)),   # tanaman gelap
    'running_mushroom': (0.30, color.rgb(105,  82,  62)),   # jamur coklat
    'firefly':          (0.14, color.rgb(185, 215, 140)),   # kunang-kunang pucat
    'wild_herb':        (0.24, color.rgb( 68, 115,  62)),   # herbal hijau
    'wild_berry':       (0.20, color.rgb(128,  42,  42)),   # beri merah tua
}

# ─── TRANSFORM PER-MODEL (skala, offset Y) — perbaiki proporsi/posisi aneh ─────
# Model .obj punya tinggi/origin berbeda; tanpa ini NPC raksasa & bat tenggelam.
_MODEL_TRANSFORM = {
    # Pasca-restandarisasi Jun 2026 (DESIGN_STANDARD.md): semua mob_*.obj
    # sudah skala meter (1u=1m) — tidak perlu koreksi skala lagi.
    'humanoid':      (0.62, 0.0),   # 3.0 tall → ~1.86 (satu-satunya model non-meter)
    'mob_kelelawar': (1.00, 0.55),  # bat melayang di atas tanah
}

def _setup_pose_swap(actor, base_name):
    """Aktifkan animasi mesh-swap 2-frame bila aset pose tersedia
    (<base>_idle/_walk1/_walk2.obj). Dibaca oleh BaseActor.sync_visuals."""
    try:
        if load_model_file(base_name + '_idle') and load_model_file(base_name + '_walk1'):
            actor._pose_names = (base_name + '_idle',
                                 base_name + '_walk1',
                                 base_name + '_walk2')
            actor._pose_cur = -1
    except Exception:
        pass

def get_npc_model_name(npc_id):
    mapping = {
        'naga_bijak': 'naga',
        'genderuwo': 'mob_genderuwo',
        'pocong': 'mob_pocong',
        'kuntilanak': 'mob_kuntilanak',
        'tuyul_pencuri': 'mob_tuyul',
        'wewe_gombel': 'mob_wewe',
        'banaspati': 'mob_banaspati',
        'leak_bali': 'mob_leak',
        'jin_kebun': 'mob_jin',
        'demit_tua': 'mob_demit',
        'bidadari': 'mob_bidadari',
        'dewa_angin': 'mob_dewa',
        'petapa_srimana': 'mob_petapa',
        'kucing_oren': 'mob_kucing',
        'sapi_betsy': 'mob_sapi',
        'kambing_jenggot': 'mob_kambing',
        'bebek_donald': 'mob_bebek',
        'domba_woolly': 'mob_domba',
        'kuda_pegasus': 'mob_kuda',
        'rubah_hutan': 'mob_rubah',
        'kelinci_putih': 'mob_kelinci',
        'ayam_kuning': 'mob_ayam',
    }
    if npc_id in mapping:
        return mapping[npc_id]
    if npc_id in ['genderuwo', 'kelelawar', 'pocong']:
        return f"mob_{npc_id}"
    return 'humanoid'


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
        self._actor_pool = {}  # Object pooling untuk actors
        self._wild_pool = []   # Object pooling untuk wild entities
        self._npc_sched_t = 0.0
        self._wild_update_t = 0.0
        self._wild_anim_t = 0.0
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
        for actor_id, pos in s.npc_positions.items():
            if pos.get('scene') != self.scene_name: continue
            if pos.get('x', -1) < 0: continue
            
            # Reuse from pool if available
            actor = self._actor_pool.get(actor_id)
            if not actor:
                # Determine class
                if actor_id in ANIMAL_NPCS:
                    actor = FarmAnimal(s, actor_id)
                else:
                    actor = NPC(s, actor_id)
                
                # Setup Model
                apr_list = NPC_APPEARANCES.get(actor_id)
                if apr_list:
                    from .vitaboy import VitaboyAvatar
                    sc = 0.19 if actor_id in ('cici', 'bowo') else 0.32
                    actor._va = VitaboyAvatar(actor, apr_list, scale=sc)
                    actor._va.set_animation("a2a-talk-idle-loop")
                    actor.model = 'cube'  # dummy parent
                    actor.color = color.clear # hide dummy
                else:
                    model_name = get_npc_model_name(actor_id)
                    if model_name == 'naga':
                        from .naga_model import build_naga
                        build_naga(actor)
                        actor.scale = 0.62
                    else:
                        panda_model = load_model_file(model_name)
                        if panda_model:
                            actor.model = panda_model
                            actor.scale = 1.0
                        else:
                            panda_fallback = load_model_file('humanoid')
                            actor.model = panda_fallback if panda_fallback else 'cube'
                # Apply Slum Grunge Tint
                # (Will be applied below to both new and pooled actors)

                # Step 6: Blob shadow
                actor._shadow = Entity(parent=actor, model='quad', position=(0, 0.02, 0), rotation=(90, 0, 0), scale=(1.2, 1.2, 1), color=color.rgba(0, 0, 0, 120))
                        
                # Setup Label
                all_d = {**HUMAN_NPCS, **SUPERNATURAL_NPCS, **ANIMAL_NPCS}
                name = all_d.get(actor_id, {}).get('name', actor_id)
                actor._lbl = Text(name, parent=actor, billboard=True,
                                 position=(0, GH + 3.1, 0),
                                 scale=5, color=color.rgb(255, 240, 160),
                                 background=True)
            else:
                actor.enabled = True
                if hasattr(actor, '_lbl') and actor._lbl:
                    actor._lbl.enabled = True

            # Dynamic Slum Grunge Tint
            if self.scene_name == 'town':
                grunge_tint = color.rgb(160, 150, 140)
                if hasattr(actor, '_va') and actor._va:
                    actor._va.color = grunge_tint
                else:
                    actor.color = grunge_tint
            else:
                if hasattr(actor, '_va') and actor._va:
                    actor._va.color = color.white
                else:
                    actor.color = color.white

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
            # ── HEWAN: cek aset GLB/OBJ dulu (wiring upgrade), else mesh prosedural ──
            if actor_id in ANIMAL_NPCS:
                from .animal_models import build_animal, get_animal_model_file
                animal_type = ANIMAL_NPCS[actor_id].get('type', 'kucing')
                asset = get_animal_model_file(animal_type)
                pm = load_model_file(asset) if asset else None
                if pm is None:
                    # Aset Blender baked (mob_<type>.obj) — standar meter + muted
                    asset = 'mob_' + animal_type
                    pm = load_model_file(asset)
                if pm is not None:
                    actor.model = pm
                    actor.scale = 1.0
                    _setup_pose_swap(actor, asset)
                else:
                    build_animal(actor, animal_type)   # prosedural
                # Label + lanjut (lewati blok model manusia/roh)
                all_d = {**HUMAN_NPCS, **SUPERNATURAL_NPCS, **ANIMAL_NPCS}
                name = all_d.get(actor_id, {}).get('name', actor_id)
                actor._lbl = Text(name, parent=actor, billboard=True,
                                 position=(0, GH + 2.4, 0), scale=4,
                                 color=color.rgb(195, 185, 162), background=True)
                self.actors[actor_id] = actor
                continue

            apr_list = NPC_APPEARANCES.get(actor_id)
            npc_mdl = load_model_file(f'npc_{actor_id}')
            if actor_id == 'petapa_srimana':
                from .petapa_model import build_petapa_srimana
                build_petapa_srimana(actor)              # sets model/color/scale
                if not getattr(actor, '_halo', None):    # guard pool reuse
                    _add_deity_aura(actor)
            elif npc_mdl is not None:
                # Model NPC kustom Blender (npc_<id>.obj) — gaya Disco muted,
                # skala meter, tekstur baked. Menggantikan Vitaboy/humanoid.
                actor.model = npc_mdl
                actor.color = color.white
                actor.scale = 1.0
                _setup_pose_swap(actor, f'npc_{actor_id}')
            elif apr_list:
                from .vitaboy import VitaboyAvatar
                sc = 0.19 if actor_id in ('cici', 'bowo') else 0.32
                if actor_id in _DEITY_IDS:
                    sc *= 1.5   # dewa-pertapa menjulang
                actor._va = VitaboyAvatar(actor, apr_list, scale=sc)
                actor._va.set_animation("a2a-talk-idle-loop")
                actor.model = 'cube'  # dummy parent
                actor.color = color.clear # hide dummy
                if actor_id in _DEITY_IDS:
                    _add_deity_aura(actor)   # halo + tetesan cahaya Ganga
                _add_role_accessories(actor, actor_id)   # celemek/apron/topi per-peran
            else:
                model_name = get_npc_model_name(actor_id)
                panda_model = load_model_file(model_name)
                if panda_model:
                    actor.model = panda_model
                    _setup_pose_swap(actor, model_name)
                else:
                    model_name = 'humanoid'
                    panda_fallback = load_model_file('humanoid')
                    actor.model = panda_fallback if panda_fallback else 'cube'
                # Skala & offset Y sesuai model (perbaiki proporsi raksasa / tenggelam)
                msc, moff = _MODEL_TRANSFORM.get(model_name, (1.0, 0.0))
                actor.scale = msc
                actor._model_y_off = moff
                if actor_id in _DEITY_IDS:
                    # Dewa-pertapa ala Siwa: arca emas-perunggu menjulang + aura
                    _apply_relic_material(actor, 'naga')  # tekstur perunggu verdigris
                    actor.color = color.rgb(212, 188, 120)  # rona emas ilahi
                    actor.scale = msc * 1.55                # menjulang, agung
                    _add_deity_aura(actor)
                elif actor_id in _SPIRIT_RELIC:
                    # Roh humanlike = arca-humanoid relik (basis humanoid + permukaan artefak)
                    tex_name, tint, spirit_sc = _SPIRIT_RELIC[actor_id]
                    _apply_relic_material(actor, model_name, override=(tex_name, tint))
                    actor.scale = spirit_sc
                elif actor_id in _NONHUMAN_RELIC_IDS:
                    # Naga / kelelawar — mesh khusus + relik
                    _apply_relic_material(actor, model_name)
                else:
                    # Human NPC: palet warna decay biasa (bukan arca)
                    actor.color = _ACTOR_PALETTE.get(actor_id, color.rgb(138, 122, 100))

            # Setup Label — gaya Disco Elysium: teks kecil, warna kertas tua
            all_d = {**HUMAN_NPCS, **SUPERNATURAL_NPCS, **ANIMAL_NPCS}
            name = all_d.get(actor_id, {}).get('name', actor_id)
            actor._lbl = Text(name, parent=actor, billboard=True,
                             position=(0, GH + 3.1, 0),
                             scale=4, color=color.rgb(195, 185, 162),
                             background=True)

            self.actors[actor_id] = actor

        # Spawn Wild
        for i, w in enumerate(s.wild_entities):
            if w['scene'] != self.scene_name: continue
            if w.get('night_only') and not s.is_night(): continue
            px, py = w['x'] * TS, w['y'] * TS
            from .animal_models import build_wild_entity
            k = w['kind']
            if self._wild_pool:
                e = self._wild_pool.pop()
                for p in getattr(e, '_wild_parts', []):
                    destroy(p)
                e._wild_parts = []
                e.enabled  = True
                e.position = (px, GH + 0.25, py)
            else:
                e = Entity(model='cube', position=(px, GH + 0.25, py))
                e._wild_parts = []
            e._base_y = GH + 0.25
            build_wild_entity(e, k)
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

            if is_boss:
                from .naga_model import build_naga
                build_naga(actor)
                sc = 1.05
                actor.scale = sc
                model_name = 'naga'
            else:
                model_name = f"mob_{kind}"
                panda_model = load_model_file(model_name)
                if panda_model:
                    actor.model = panda_model
                else:
                    model_name = 'humanoid'
                    panda_fallback = load_model_file('humanoid')
                    actor.model = panda_fallback if panda_fallback else 'cube'
                msc, moff = _MODEL_TRANSFORM.get(model_name, (1.0, 0.0))
                sc = msc * (1.6 if is_boss else 1.0)
                actor.scale = sc
                if moff:
                    actor.y = moff
                # Mob biasa = artefak relik
                _apply_relic_material(actor, model_name)

            # HP Bar — warna suram, gaya Disco Elysium
            hp_y = GH + (3.0 if is_boss else 2.2)
            actor._bg_bar = Entity(parent=actor, model='cube', position=(0, hp_y, 0),
                                   scale=(0.9*sc, 0.09, 0.09), color=color.rgb(28, 25, 22))
            actor._hp_bar = Entity(parent=actor, model='cube', position=(0, hp_y, -0.02),
                                   scale=(0.9*sc, 0.07, 0.07),
                                   color=color.rgb(188, 62, 48) if not is_boss else color.rgb(158, 45, 82))
            
            self.actors[actor_id] = actor

    def update(self, dt: float):
        s = self.state
        
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
                actor.update_anim(dt)

            # Let the actor smoothly move visually
            actor.sync_visuals(dt, TS, GH)

        # Wild update tiap 0.8s
        self._wild_update_t += dt
        self._wild_anim_t   += dt
        if self._wild_update_t >= 0.8:
            self._wild_update_t = 0
            self._update_wild_ai()
        self._sync_wild_visuals(self._wild_anim_t)

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

    def _sync_wild_visuals(self, anim_t: float = 0.0):
        from .animal_models import update_anim_wild
        s = self.state
        for i, w in enumerate(s.wild_entities):
            if i not in self.wild_ents: continue
            e = self.wild_ents[i]
            e.x = w['x']*TS; e.z = w['y']*TS
            if w.get('night_only'):
                e.enabled = s.is_night()
            if e.enabled:
                update_anim_wild(e, w['kind'], anim_t)

    def _clear_all(self):
        for actor_id, actor in self.actors.items():
            actor.enabled = False
            if hasattr(actor, '_lbl') and actor._lbl:
                actor._lbl.enabled = False
            self._actor_pool[actor_id] = actor
        self.actors.clear()
        
        for e in self.wild_ents.values():
            e.enabled = False
            self._wild_pool.append(e)
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

    def try_capture_wild(self, tx: int, ty: int, state, kinds=None) -> tuple | None:
        """Coba tangkap/panen entitas liar di sekitar (tx, ty).
        kinds: set jenis yang diizinkan; None = semua jenis."""
        import random as rng_mod
        sc = state.scene_name
        px, pz = tx * TS, ty * TS
        for w in list(state.wild_entities):
            if w['scene'] != sc: continue
            wx, wz = w['x'] * TS, w['y'] * TS
            if math.sqrt((px-wx)**2 + (pz-wz)**2) > 3.0: continue
            kind = w['kind']
            if kinds is not None and kind not in kinds: continue
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
