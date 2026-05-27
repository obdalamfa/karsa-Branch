"""
world.py — 3D world renderer untuk Ursina Engine.
Mengkonversi tile map 2D (dari scenes.py) menjadi entitas 3D.

Koordinat mapping:
  Tile (tx, ty)  →  World Vec3(tx * TS, 0, ty * TS)
  TS = TILE_SIZE = 2.0 world-units per tile

Struktur Y (vertikal):
  y = 0          → bawah ground
  y = GROUND_H/2 → center ground tile (top face = GROUND_H)
  y > GROUND_H   → objek berdiri di atas tanah
"""
import math, os
from pathlib import Path
from PIL import Image
from ursina import Entity, Vec3, color, destroy, Texture
from ursina.models.procedural.cylinder import Cylinder

from .config import (TILE_SIZE, GROUND_H, WALL_H, TREE_H, HOUSE_H, OBJ_H, SMALL_OBJ_H,
                     WALKABLE, BLOCKING, MINEABLE, TILLABLE,
                     G, D, P, W, FL, WL, TR, H, MB, DR, FN, GT, BD, ST, TB, BS,
                     MR, FP, CL, PP, CH, CT, SH, GR, LN, DT, CV_W, CV_F, PEN, STR_T,
                     DCK, BOT, LLY, CRYS, ORE_TBG, ORE_BSI, ORE_EMS, ORE_KRS, ORE_MTH,
                     STAIRS_DOWN, STAIRS_UP, MINED, SD, LGH_B, LGH_F, CLOUD, GOLD_W, PALM, TV, CHR, CAL)
from .scenes import SCENES
from .data import CROPS

TS = TILE_SIZE

# ─── TEXTURE HELPERS ─────────────────────────────────────
_ASSET_DIR = Path(__file__).resolve().parent.parent / 'assets' / 'textures'
_TEX_CACHE: dict = {}

def _tex(name: str):
    """Load & cache tekstur via Path (bypass Ursina string-search)."""
    if not name:
        return None
    if name in _TEX_CACHE:
        return _TEX_CACHE[name]
    p = _ASSET_DIR / f'{name}.png'
    if p.exists():
        try:
            img = Image.open(p)
            t = Texture(img)
            # Enable high-quality bilinear filtering for high-resolution ground textures
            if name in ('grass_tso', 'rock_ground', 'sand_ground', 'snow_ground'):
                t.filtering = True
            else:
                t.filtering = False
            _TEX_CACHE[name] = t
            return t
        except Exception:
            pass
    return None

def _e(model, pos, scale, tex_name, tint=color.white, smooth=True, soft=True, **kw):
    """Buat Entity dengan tekstur + tint opsional.
    `soft=True`: cube → soft cube (rounded). Set soft=False untuk tile ground / detail tajam."""
    if soft:
        if model == 'cube':
            from .meshes import soft_cube_mesh
            model = soft_cube_mesh()
        elif model == 'cylinder':
            from .meshes import soft_capsule_mesh
            model = soft_capsule_mesh()
    elif model == 'cylinder':
        model = Cylinder()
    t = _tex(tex_name)
    if t:
        e = Entity(model=model, position=pos, scale=scale,
                   texture=t, color=tint, **kw)
        # NOTE: jangan auto-enable transparent — tekstur procedural punya alpha
        # parsial yang BUKAN dimaksud transparan (efek shading). Caller boleh
        # set kw['transparent']=True eksplisit kalau perlu (mis. glass).
    else:
        e = Entity(model=model, position=pos, scale=scale,
                   color=tint, **kw)
    if smooth:
        from .smooth_shader import apply_smooth
        apply_smooth(e, has_texture=bool(t))
    return e


def _c(r, g_, b):
    return color.rgb(r, g_, b)


# Roof texture variants moved to props.py

# Checkerboard outdoor — hijau hangat Sims 1 (tidak terlalu neon)
_CB_LIGHT = color.rgb(148, 205, 105)
_CB_DARK  = color.rgb(125, 182, 85)

# Checkerboard indoor — warm honey wood
_FL_LIGHT = color.rgb(228, 200, 148)
_FL_DARK  = color.rgb(200, 170, 115)

# Cave floor — cool purple-grey
_CV_LIGHT = color.rgb(132, 118, 152)
_CV_DARK  = color.rgb(108, 95, 128)

def _cb(tx, ty):
    return _CB_DARK if (tx + ty) % 2 == 1 else _CB_LIGHT

def _cb_floor(tx, ty):
    return _FL_DARK if (tx + ty) % 2 == 1 else _FL_LIGHT

def _cb_cave(tx, ty):
    return _CV_DARK if (tx + ty) % 2 == 1 else _CV_LIGHT


# ─── TERRAIN NOISE (dari filosofi Panda3D Terrain + Ursina minecraft_clone) ──
# Multi-frequency smooth noise (mirip Perlin stacking dari StephenLujan repo)
def _noise_val(tx, ty):
    """Smooth deterministic noise [0..1] dari posisi tile.
    Menggabungkan 3 frekuensi sin seperti stacked Perlin noise di terrain repos."""
    s = (math.sin(tx * 1.7  + ty * 3.1 ) * 0.50 +
         math.sin(tx * 2.9  + ty * 1.3 ) * 0.30 +
         math.sin(tx * 0.7  + ty * 4.1 ) * 0.20)
    return (s + 1.0) * 0.5   # → [0.0, 1.0]

def _noise2(tx, ty):
    """Noise sekunder untuk dekorasi (frekuensi berbeda)."""
    s = (math.sin(tx * 5.3  + ty * 2.7 ) * 0.60 +
         math.sin(tx * 11.1 + ty * 7.9 ) * 0.40)
    return (s + 1.0) * 0.5

# Terrain step height per level (dari Craig-Macomber: tile height caching)
_STEP_H = 0.09   # tinggi satu "step" voxel — lebih pendek agar border tidak dominan


# ─── PETA TEKSTUR TILE ───────────────────────────────────
TILE_TEX = {
    G:          'grass',
    D:          'dirt',
    P:          'path_stone',
    W:          'water',
    FL:         'floor_wood',
    CV_F:       'cave_floor',
    STR_T:      'straw',
    DCK:        'dock',
    LLY:        'lily',
    MINED:      'mined',
    STAIRS_DOWN:'stairs_down',
    STAIRS_UP:  'stairs_up',
    SD:         'sand_ground',
    CLOUD:      'snow_ground',
}

# Tekstur untuk objek/dinding
OBJ_TEX = {
    WL:      'wall_stone',
    CV_W:    'wall_cave',
    H:       'house_wall',
    TR:      'tree_leaf',
    DT:      'tree_trunk',
    FP:      'fire_orange',
    LN:      'lamp_glow',
    CRYS:    'crystal',
    ORE_TBG: 'ore_copper',
    ORE_BSI: 'ore_iron',
    ORE_EMS: 'ore_gold',
    ORE_KRS: 'ore_crystal',
    ORE_MTH: 'ore_mithril',
    CH:      'chest_wood',
    BOT:     'boat_wood',
    BD:      'wood_plank',
    TB:      'wood_plank',
    BS:      'wood_plank',
    CT:      'wood_plank',
    SH:      'wood_plank',
    ST:      'metal_grey',
    MR:      'mirror_blue',
    GR:      'grave_stone',
    FN:      'wood_plank',
    GT:      'wood_plank',
    PEN:     'wood_plank',
    DR:      'house_wall',
    PP:      'cloth_green',
    MB:      'cloth_blue',
    CL:      'metal_grey',
    LGH_B:   'wall_stone',
    LGH_F:   'house_wall',
    GOLD_W:  'ore_gold',
}

# Fallback warna untuk objek tanpa tekstur
OBJ_COLORS = {
    WL:  _c(118, 105, 138),
    TR:  _c(95, 200, 65),    # vivid green
    H:   _c(248, 235, 200),  # cream warm
    MB:  _c(88, 128, 228),   # bright blue mailbox
    LGH_B: _c(150, 150, 150),
    LGH_F: _c(245, 245, 220),
    CLOUD: _c(235, 245, 255),
    GOLD_W: _c(255, 223, 0),
    DR:  _c(168, 112, 62),
    FN:  _c(178, 148, 95),   # warmer fence
    GT:  _c(168, 130, 72),
    BD:  _c(238, 205, 162),  # warm bed
    ST:  _c(145, 115, 95),
    TB:  _c(205, 168, 112),  # warm table
    BS:  _c(162, 118, 72),
    MR:  _c(165, 225, 255),  # brighter mirror
    FP:  _c(255, 148, 55),   # vivid fireplace
    CL:  _c(105, 85, 68),
    PP:  _c(88, 215, 88),    # vivid plant
    CH:  _c(185, 138, 82),
    CT:  _c(198, 158, 105),
    SH:  _c(185, 145, 95),
    GR:  _c(148, 132, 165),  # softer grave
    LN:  _c(255, 248, 120),  # bright lantern
    DT:  _c(112, 85, 55),
    CV_W:_c(88, 75, 108),
    PEN: _c(155, 115, 65),
    BOT: _c(215, 165, 102),
    CRYS:_c(208, 168, 255),  # soft purple crystal
    ORE_TBG:_c(215, 138, 72),
    ORE_BSI:_c(165, 168, 195),
    ORE_EMS:_c(255, 238, 95),
    ORE_KRS:_c(198, 158, 255),
    ORE_MTH:_c(165, 245, 255),
}

CROP_TEX = {
    'lobak':    'crop_lobak',
    'wortel':   'crop_wortel',
    'stroberi': 'crop_stroberi',
    'jagung':   'crop_jagung',
    'tomat':    'crop_tomat',
    'labu':     'crop_labu',
    'bayam':    'crop_bayam',
    'jamur':    'crop_jamur',
}


class World3D:
    """Mengelola semua 3D entity untuk scene yang sedang aktif."""

    def __init__(self, state):
        self.state              = state
        self.scene_name         = None
        self.scene_obj          = None
        self.dungeon_level      = state.dungeon_level
        self._tile_ents: list   = []   # ground tiles
        self._obj_ents:  list   = []   # blocking objects
        self._soil_ents: dict   = {}   # key → Entity
        self._crop_ents: dict   = {}   # key → Entity
        self._water_ents: list  = []   # untuk animasi warna
        self._grass_ents: list  = []   # untuk grass shader (FreeSO GrassShader.fx)
        self._water_t    = 0.0
        self.ground_collider = None
        # Craig-Macomber pattern: cache tinggi surface per tile (tx,ty) → float
        self._tile_heights: dict = {}

    # ─── PUBLIC API ──────────────────────────────────────
    def _create_entity(self, model, pos, scale, tex_name, tint=None, **kw):
        from ursina import color
        if tint is None:
            tint = color.white
        from .world import _e
        return _e(model, pos, scale, tex_name, tint, **kw)

    def load_scene(self, name: str):
        self._clear()
        self.scene_name = name
        self.scene_obj  = SCENES[name]
        self._build_tiles()
        self._build_all_crops()
        if hasattr(self.scene_obj, 'builder') and self.scene_obj.builder:
            self.scene_obj.builder(self)

    def tile_to_world(self, tx: int, ty: int) -> Vec3:
        return Vec3(tx * TS, 0, ty * TS)

    def world_to_tile(self, wx: float, wz: float):
        return int(round(wx / TS)), int(round(wz / TS))

    def get_surface_height(self, tx: int, ty: int) -> float:
        """Return Y offset permukaan tile (tx,ty) — digunakan player untuk terrain following."""
        return self._tile_heights.get((tx, ty), 0.0)

    def _is_outdoor(self) -> bool:
        return (self.scene_name not in ('dungeon',) and
                not getattr(self.scene_obj, 'indoor', False))

    def _road_bitmask(self, tx: int, ty: int) -> int:
        """4-bit bitmask N/E/S/W → index road00-15 (FreeSO terrain tileset pattern)."""
        n = int(self.get_tile(tx,     ty - 1) == P)
        e = int(self.get_tile(tx + 1, ty    ) == P)
        s = int(self.get_tile(tx,     ty + 1) == P)
        w = int(self.get_tile(tx - 1, ty    ) == P)
        return n | (e << 1) | (s << 2) | (w << 3)

    def get_tile(self, tx: int, ty: int) -> int:
        sc = self.scene_obj
        if sc:
            if self.scene_name == 'dungeon' and self.state.dungeon_tiles:
                if 0 <= ty < len(self.state.dungeon_tiles) and 0 <= tx < len(self.state.dungeon_tiles[0]):
                    return self.state.dungeon_tiles[ty][tx]
            if 0 <= tx < sc.w and 0 <= ty < sc.h:
                return sc.tiles[ty][tx]
        return WL  # out-of-bounds = blocking

    def is_walkable(self, tx: int, ty: int) -> bool:
        return self.get_tile(tx, ty) in WALKABLE

    def refresh_tile(self, tx: int, ty: int, soil_key: str):
        """Update visual tanah/tanaman di satu tile."""
        soil = self.state.soil.get(soil_key, {})
        self._update_soil(soil_key, tx, ty, soil)
        if soil.get('crop'):
            self._update_crop(soil_key, tx, ty, soil)
        else:
            self._destroy_crop(soil_key)

    def update(self, dt: float):
        """Animasi air — tint shimmer perlahan di atas tekstur water."""
        if not self._water_ents:
            return
        self._water_t += dt
        # Tint terang agar tekstur water tetap terlihat (nilai 200-255)
        r  = 195 + int(abs(math.sin(self._water_t * 1.5)) * 30)
        g_ = 220 + int(abs(math.sin(self._water_t * 1.0)) * 20)
        b  = 245 + int(abs(math.sin(self._water_t * 2.0)) * 10)
        col = color.rgb(min(255, r), min(255, g_), min(255, b))
        for e in self._water_ents:
            e.color = col

    # ─── INTERNAL: CLEAR ─────────────────────────────────
    def _clear(self):
        for e in self._tile_ents + self._obj_ents:
            destroy(e)
        for e in self._soil_ents.values():
            destroy(e)
        for e in self._crop_ents.values():
            destroy(e)
        self._tile_ents.clear()
        self._obj_ents.clear()
        self._soil_ents.clear()
        self._crop_ents.clear()
        self._water_ents.clear()
        self._grass_ents.clear()
        self._tile_heights.clear()
        
        if self.ground_collider:
            destroy(self.ground_collider)
            self.ground_collider = None

    # ─── INTERNAL: BUILD TILES ───────────────────────────
    def _build_tiles(self):
        sc = self.scene_obj
        is_dungeon = (self.scene_name == 'dungeon' and self.state.dungeon_tiles)
        default_tex = 'cave_floor' if is_dungeon else ('floor_wood' if sc.indoor else 'grass')

        tiles_to_build = self.state.dungeon_tiles if is_dungeon else sc.tiles
        h = len(tiles_to_build)
        w = len(tiles_to_build[0]) if h > 0 else 0

        for ty in range(h):
            for tx in range(w):
                tid = tiles_to_build[ty][tx]
                wx, wz = tx * TS, ty * TS
                self._make_tile(tid, wx, wz, default_tex, tx, ty)

        # Tambahkan invisible ground collider untuk menangkap klik mouse
        self.ground_collider = Entity(
            model='quad',
            rotation_x=90,
            scale=(w * TS, h * TS),
            position=(w * TS / 2.0 - TS / 2.0, GROUND_H, h * TS / 2.0 - TS / 2.0),
            collider='box',
            visible=False
        )

        # ── Horizon Lingkungan Luas (Menutupi efek "Piring di tengah bola") ──
        if getattr(sc, 'has_horizon', not sc.indoor and not is_dungeon):
            # Digital Alice style: bright neon sky reflection / white void
            horizon = _e('quad', (w * TS / 2.0, -0.05, h * TS / 2.0),
                         (1000, 1000, 1), None, color.rgb(255, 255, 255), soft=False, rotation=(90, 0, 0))
            self._tile_ents.append(horizon)
        
        # ── Pencahayaan Indoor (PointLight) ──
        if sc.indoor:
            from ursina import PointLight, scene
            pl = PointLight(parent=scene, position=(w * TS / 2.0, 5, h * TS / 2.0))
            pl.color = color.rgb(255, 40, 200) # Neon magenta indoor
            pl.shadows = True
            self._obj_ents.append(pl)

    def _make_tile(self, tid, wx, wz, default_tex, tx=0, ty=0):
        # Pick tint based on tile type so indoor rooms aren't all white
        if tid == FL or (tid in BLOCKING and default_tex == 'floor_wood'):
            tint = _cb_floor(tx, ty)
        elif tid == CV_F or (tid in BLOCKING and default_tex == 'cave_floor'):
            tint = _cb_cave(tx, ty)
        else:
            tint = _cb(tx, ty)

        if tid in BLOCKING or tid == MB:
            ge = _e('cube', (wx, GROUND_H/2, wz), (TS, GROUND_H, TS), default_tex, tint, soft=False)
            self._tile_ents.append(ge)
            self._make_blocking_obj(tid, wx, wz)

        elif tid == G:
            # Resolve FreeSO/TSO high-fidelity textures
            is_winter = (self.state.season_index == 3)
            grass_tex = 'snow_ground' if is_winter else 'grass_tso'
            dirt_tex = 'sand_ground'

            # ── Terrain Halus (Bukan Minecraft) ──
            # Hanya buat satu bidang datar, tanpa efek voxel bertingkat
            nv = _noise_val(tx, ty) if self._is_outdoor() else 0.0
            
            # Base dirt cube
            base = _e('cube', (wx, GROUND_H / 2, wz), (TS, GROUND_H, TS), dirt_tex, tint, soft=False)
            self._tile_ents.append(base)

            # Grass cap di atas rata
            cap_y = GROUND_H + 0.02
            cap   = _e('cube', (wx, cap_y, wz), (TS * 1.005, 0.04, TS * 1.005), grass_tex,
                       tint, soft=False)
            self._tile_ents.append(cap)
            self._grass_ents.append(cap)   # kumpulkan untuk grass shader

            # Cache tinggi surface untuk player terrain-following (selalu rata)
            self._tile_heights[(tx, ty)] = 0.0

            # Dekorasi organik: batu kecil / rumput tinggi / bunga liar (30% tile)
            if nv < 0.30:
                self._add_outdoor_deco(wx, wz, GROUND_H + 0.04, tx, ty, nv)

        elif tid == W:
            we = _e('cube', (wx, 0.05, wz), (TS, 0.10, TS), 'water',
                    color.rgb(88, 210, 218), soft=False)  # teal turquoise
            self._tile_ents.append(we)
            self._water_ents.append(we)

        elif tid == STAIRS_DOWN:
            base = _e('cube', (wx, GROUND_H/2, wz), (TS, GROUND_H, TS), 'stairs_down', tint, soft=False)
            self._tile_ents.append(base)

        elif tid == STAIRS_UP:
            base = _e('cube', (wx, GROUND_H/2, wz), (TS, GROUND_H, TS), 'stairs_up', tint, soft=False)
            self._tile_ents.append(base)

        elif tid == P and self._is_outdoor():
            # Road tile: bitmask dari 4 tetangga P → pilih road00-15.png (FreeSO terrain pattern)
            bm   = self._road_bitmask(tx, ty)
            
            # Add solid dirt base so transparent road doesn't show sky
            base_dirt = _e('cube', (wx, GROUND_H/2, wz), (TS, GROUND_H, TS), 'sand_ground', tint, soft=False)
            self._tile_ents.append(base_dirt)
            
            base = _e('cube', (wx, GROUND_H/2 + 0.01, wz), (TS, GROUND_H, TS),
                      f'terrain/road{bm:02d}', tint, soft=False)
            self._tile_ents.append(base)
            nv2 = _noise2(tx, ty)
            if nv2 > 0.55:
                ox = math.sin(tx * 53.7 + ty * 89.1) * 0.38
                oz = math.cos(tx * 73.2 + ty * 47.5) * 0.38
                pebble = _e('cube', (wx + ox, GROUND_H + 0.04, wz + oz),
                            (0.18, 0.09, 0.16), 'rock_ground', _c(140, 128, 112))
                self._tile_ents.append(pebble)

        elif tid == CV_F:
            base = _e('cube', (wx, GROUND_H/2, wz), (TS, GROUND_H, TS), 'cave_floor', _cb_cave(tx, ty), soft=False)
            self._tile_ents.append(base)
            nv2 = _noise2(tx, ty)
            if nv2 > 0.70:
                ox = math.sin(tx * 41.3 + ty * 97.7) * 0.28
                oz = math.cos(tx * 63.9 + ty * 31.1) * 0.28
                h_stala = 0.22 + nv2 * 0.18
                stala = _e('cube', (wx + ox, WALL_H + GROUND_H - h_stala * 0.5, wz + oz),
                           (0.10, h_stala, 0.10), 'wall_cave', _c(65, 55, 75))
                self._tile_ents.append(stala)

        else:
            tex = TILE_TEX.get(tid, default_tex)
            if tex == 'grass':
                tex = 'snow_ground' if self.state.season_index == 3 else 'grass_tso'
            elif tex == 'dirt':
                tex = 'sand_ground'
            elif tex == 'path_stone':
                tex = 'rock_ground'
            ge = _e('cube', (wx, GROUND_H/2, wz), (TS, GROUND_H, TS), tex, tint, soft=False)
            self._tile_ents.append(ge)

    # ─── INTERNAL: OUTDOOR DECORATION ───────────────────────
    def _add_outdoor_deco(self, wx, wz, surface_y, tx, ty, nv):
        """Surreal digital deco: floating cubes, wireframe pyramids"""
        ox = math.sin(tx * 53.7 + ty * 89.1) * 0.42
        oz = math.cos(tx * 73.2 + ty * 47.5) * 0.42
        dtype = int(abs(math.sin(tx * 200.3 + ty * 150.7)) * 3)

        if dtype == 0:   # Floating abstract cube
            c1 = _e('cube', (wx + ox, surface_y + 0.8, wz + oz),
                      (0.2, 0.2, 0.2), None, _c(0, 255, 255), rotation=(45, 45, 0))
            self._tile_ents.append(c1)

        elif dtype == 1:  # Wireframe pillar
            c2 = _e('cylinder', (wx + ox, surface_y + 0.4, wz + oz),
                      (0.05, 0.8, 0.05), None, _c(255, 0, 255))
            self._tile_ents.append(c2)

        else:             # Glowing orb
            flower = _e('sphere', (wx + ox, surface_y + 0.6, wz + oz),
                        (0.2, 0.2, 0.2), 'lamp_glow', _c(255, 255, 255))
            self._tile_ents.append(flower)

    def _make_blocking_obj(self, tid, wx, wz):
        if tid in (TR, PALM, DT, LN, ORE_TBG, ORE_BSI, ORE_EMS, ORE_KRS, ORE_MTH, CRYS, H, FP, GR, TV, CHR, CAL):
            # Handled by Scene builder/props.py
            return

        else:
            oh = {WL: WALL_H, CV_W: WALL_H, FN: OBJ_H * 0.75, GT: OBJ_H, PEN: OBJ_H * 0.95,
                  BD: 0.62, TB: 0.82, BS: OBJ_H * 1.4, MR: OBJ_H * 1.2,
                  CL: OBJ_H * 1.35, PP: 0.70, CH: 0.80, CT: 0.90, SH: OBJ_H * 1.5,
                  GR: OBJ_H * 0.90, BOT: 0.60, MB: 0.85, ST: 0.95,
                  DR: WALL_H}.get(tid, OBJ_H)
            tex = OBJ_TEX.get(tid, None)
            
            # Default OBJ_COLORS if exists, else fallback
            col = OBJ_COLORS.get(tid, _c(130, 130, 130))
            
            sc = 0.88
            if tid == WL:
                sc = 1.0
                if getattr(self.scene_obj, 'indoor', False):
                    tex = 'wood_plank'
                    col = _c(235, 215, 185) # Warm indoor wallpaper
            elif tid == CV_W:
                sc = 0.98
            elif tid == DR:
                sc = 1.0

            if tex:
                e = _e('cube', (wx, oh / 2 + GROUND_H, wz),
                       (TS * sc, oh, TS * sc), tex, col)
            else:
                e = _e('cube', (wx, oh / 2 + GROUND_H, wz),
                       (TS * sc, oh, TS * sc), None, col)
            self._obj_ents.append(e)

    # ─── INTERNAL: SOIL / CROP ───────────────────────────
    def _build_all_crops(self):
        sc_name = self.scene_name
        for key, soil in self.state.soil.items():
            parts = key.split(',')
            if len(parts) != 3 or parts[2] != sc_name:
                continue
            tx, ty = int(parts[0]), int(parts[1])
            if soil.get('tilled'):
                self._update_soil(key, tx, ty, soil)
            if soil.get('crop'):
                self._update_crop(key, tx, ty, soil)

    def _update_soil(self, key, tx, ty, soil):
        if key in self._soil_ents:
            destroy(self._soil_ents.pop(key))
        if not soil.get('tilled'):
            return
        wx, wz = tx * TS, ty * TS
        soil_tex = 'soil_wet' if soil.get('watered') else 'soil_dry'
        e = _e('cube', (wx, GROUND_H + 0.06, wz),
               (TS * 0.92, 0.10, TS * 0.92), soil_tex)
        self._soil_ents[key] = e

    def _update_crop(self, key, tx, ty, soil):
        self._destroy_crop(key)
        crop_id = soil.get('crop')
        if not crop_id:
            return
        crop_data = CROPS.get(crop_id, {})
        days  = crop_data.get('days', 4)
        age   = soil.get('age', 0)
        stage = min(3, int(age / max(days, 1) * 4))

        wx, wz = tx * TS, ty * TS
        scale_y = 0.30 + stage * 0.25
        cy = GROUND_H + 0.16 + scale_y / 2

        if stage == 0:
            crop_tex = 'crop_seed'
        elif stage == 1:
            crop_tex = 'crop_sprout'
        else:
            crop_tex = CROP_TEX.get(crop_id, 'crop_lobak')

        e = _e('sphere', (wx, cy, wz),
               (TS * 0.40, scale_y, TS * 0.40), crop_tex)
        stem_h = scale_y * 0.55
        stem = _e('cylinder',
                  (wx, GROUND_H + 0.12 + stem_h / 2, wz),
                  (TS * 0.08, stem_h, TS * 0.08),
                  'cloth_green')
        self._crop_ents[key] = e
        self._crop_ents[key + '_stem'] = stem

    def _destroy_crop(self, key):
        for k in (key, key + '_stem'):
            if k in self._crop_ents:
                destroy(self._crop_ents.pop(k))

