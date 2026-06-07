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
                     STAIRS_DOWN, STAIRS_UP, MINED, SD, LGH_B, LGH_F, CLOUD, GOLD_W, PALM, TV, CHR, CAL,
                     WARUNG, RUMAH_PG, UNION_HL, SHRINE, DEBRIS, LAUNDRY, GRAFFITI_W)
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
            # Pixel-art crisp (point filtering) untuk SEMUA tekstur — konsisten dgn
            # look pixelation Shaman Quest (pola PyAO: Texture.default_filtering=None).
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

# Checkerboard outdoor — hijau-coklat lumpur, sangat desaturated (Disco Elysium)
# Tint ini MENGALIKAN tekstur grass_tso yang terang → tarik jauh ke arah gelap/keruh.
_CB_LIGHT = color.rgb(70,  82,  52)
_CB_DARK  = color.rgb(54,  64,  40)

# Checkerboard indoor — papan kayu (cukup terang agar furniture menonjol)
_FL_LIGHT = color.rgb(122, 100, 72)
_FL_DARK  = color.rgb(104, 84, 60)

# Cave floor — abu-ungu gelap
_CV_LIGHT = color.rgb(108, 95, 125)
_CV_DARK  = color.rgb(88,  78, 102)

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

# Fallback warna — palet decay tropis (Disco Elysium × Indonesia)
OBJ_COLORS = {
    WL:    _c( 95,  88, 105),   # dinding plester tua
    TR:    _c( 52, 105,  38),   # dedaunan hijau tua, tidak neon
    H:     _c(162, 148, 128),   # dinding rumah lapuk
    MB:    _c( 72, 105, 158),   # kotak pos biru pudar
    LGH_B: _c(125, 118, 112),
    LGH_F: _c(205, 195, 175),
    CLOUD: _c(218, 225, 235),
    GOLD_W:_c(188, 162,  55),   # emas pudar, bukan kuning neon
    DR:    _c(105,  75,  45),   # pintu kayu tua
    FN:    _c(138, 112,  72),   # pagar lapuk
    GT:    _c(128, 100,  62),
    # ─── FURNITURE INTERIOR (gelap, lapuk) ─────────────────
    BD:    _c( 75,  62,  48),   # kasur usang, bernoda
    ST:    _c( 88,  82,  75),   # kompor tua, abu kehitaman
    TB:    _c( 92,  75,  55),   # meja kayu tua
    BS:    _c( 78,  60,  42),   # rak buku gelap
    MR:    _c( 72,  82,  95),   # cermin berdebu, biru abu
    FP:    _c(188, 102,  42),   # perapian, oranye gelap
    CL:    _c( 88,  72,  58),   # jam dinding usang
    PP:    _c( 58, 105,  52),   # tanaman pot, setengah layu
    CH:    _c(105,  80,  52),   # peti kayu tua
    CT:    _c( 88,  70,  50),   # counter kayu gelap
    SH:    _c( 82,  65,  45),   # rak gelap
    # ─── ALAM / OUTDOOR ────────────────────────────────────
    GR:    _c(105,  92, 118),   # batu nisan
    LN:    _c(195, 175, 105),   # lampu redup, kuning pudar
    DT:    _c( 88,  65,  40),   # pohon mati
    CV_W:  _c( 75,  62,  92),   # dinding gua
    PEN:   _c(125,  92,  55),   # tiang kandang
    BOT:   _c(158, 118,  72),   # perahu kayu lapuk
    # ─── ORE (tetap bisa dibaca tapi lebih gelap) ──────────
    CRYS:  _c(162, 128, 205),
    ORE_TBG:_c(175, 110,  55),
    ORE_BSI:_c(128, 132, 155),
    ORE_EMS:_c(195, 178,  65),
    ORE_KRS:_c(155, 118, 205),
    ORE_MTH:_c(125, 195, 205),
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
        """Animasi air — warna keruh/kotor, bergerak lambat (sungai Lembah Karsa)."""
        if not self._water_ents:
            return
        self._water_t += dt
        # Air keruh — hijau-abu gelap, bukan biru jernih
        r  = 62  + int(abs(math.sin(self._water_t * 0.8)) * 15)
        g_ = 88  + int(abs(math.sin(self._water_t * 0.5)) * 18)
        b  = 82  + int(abs(math.sin(self._water_t * 1.2)) * 12)
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
        # 'grass.png' adalah placeholder rusak (grid magenta!) → pakai 'grass_tso' yang bersih
        default_tex = 'cave_floor' if is_dungeon else ('floor_wood' if sc.indoor else 'grass_tso')

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
            # Lembah Karsa: kabut abu suram di horizon (bukan void putih)
            horizon = _e('quad', (w * TS / 2.0, -0.05, h * TS / 2.0),
                         (1000, 1000, 1), None, color.rgb(78, 82, 88), soft=False, rotation=(90, 0, 0))
            self._tile_ents.append(horizon)

            # Kabut tanah tipis — mist layer setinggi pinggang, atmosfer rimba
            mist = _e('quad', (w * TS / 2.0, 0.35, h * TS / 2.0),
                      (w * TS + 20, h * TS + 20, 1), None,
                      color.rgba(148, 158, 142, 38), soft=False, rotation=(90, 0, 0))
            self._tile_ents.append(mist)
        
        # ── Pencahayaan Indoor — bohlam redup, amber hangat (Disco Elysium) ──
        if sc.indoor:
            from ursina import PointLight, scene as ursina_scene
            pl = PointLight(parent=ursina_scene,
                            position=(w * TS / 2.0, 4.5, h * TS / 2.0))
            pl.color = color.rgb(215, 172, 98)   # kuning-amber bohlam usang
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
            # TS*1.04 → tile saling tumpang sedikit, menutup celah (cegah "grid" background bocor)
            ge = _e('cube', (wx, GROUND_H/2, wz), (TS*1.04, GROUND_H, TS*1.04), default_tex, tint, soft=False)
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
            
            # Base dirt cube (overlap menutup celah background)
            base = _e('cube', (wx, GROUND_H / 2, wz), (TS*1.04, GROUND_H, TS*1.04), dirt_tex, tint, soft=False)
            self._tile_ents.append(base)

            # Grass cap di atas rata (overlap lebih besar agar tak ada garis pemisah)
            cap_y = GROUND_H + 0.02
            cap   = _e('cube', (wx, cap_y, wz), (TS * 1.04, 0.04, TS * 1.04), grass_tex,
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
                    color.rgb(62, 88, 82), soft=False)    # air sungai keruh
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
            base_dirt = _e('cube', (wx, GROUND_H/2, wz), (TS*1.04, GROUND_H, TS*1.04), 'sand_ground', tint, soft=False)
            self._tile_ents.append(base_dirt)

            base = _e('cube', (wx, GROUND_H/2 + 0.01, wz), (TS*1.04, GROUND_H, TS*1.04),
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
            base = _e('cube', (wx, GROUND_H/2, wz), (TS*1.04, GROUND_H, TS*1.04), 'cave_floor', _cb_cave(tx, ty), soft=False)
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
            ge = _e('cube', (wx, GROUND_H/2, wz), (TS*1.04, GROUND_H, TS*1.04), tex, tint, soft=False)
            self._tile_ents.append(ge)

    # ─── INTERNAL: OUTDOOR DECORATION ───────────────────────
    def _add_outdoor_deco(self, wx, wz, surface_y, tx, ty, nv):
        """Dekorasi organik outdoor — rumput tinggi, batu, genangan lumpur."""
        ox = math.sin(tx * 53.7 + ty * 89.1) * 0.40
        oz = math.cos(tx * 73.2 + ty * 47.5) * 0.40
        dtype = int(abs(math.sin(tx * 200.3 + ty * 150.7)) * 4)

        if dtype == 0:   # Batu kecil lapuk
            stone_col = _c(int(95 + nv*20), int(88 + nv*18), int(82 + nv*15))
            stone = _e('cube', (wx + ox, surface_y + 0.06, wz + oz),
                       (0.22, 0.12, 0.18), 'rock_ground', stone_col,
                       rotation=(0, tx*37.0, 0))
            self._tile_ents.append(stone)

        elif dtype == 1:  # Rumput tinggi (clump)
            grass_col = _c(int(55 + nv*25), int(88 + nv*30), int(42 + nv*18))
            for i in range(2):
                gx = ox + math.sin(i * 2.1) * 0.15
                gz = oz + math.cos(i * 2.1) * 0.15
                grass = _e('cube', (wx + gx, surface_y + 0.18, wz + gz),
                           (0.06, 0.34, 0.06), None, grass_col,
                           rotation=(0, i*45.0, 0))
                self._tile_ents.append(grass)

        elif dtype == 2:  # Genangan lumpur kecil
            puddle = _e('cube', (wx + ox*0.5, surface_y + 0.01, wz + oz*0.5),
                        (0.38, 0.02, 0.30), None, _c(58, 52, 45))
            self._tile_ents.append(puddle)

        else:             # Ranting/dahan kering jatuh
            twig = _e('cube', (wx + ox, surface_y + 0.04, wz + oz),
                      (0.38, 0.05, 0.07), 'tree_trunk', _c(72, 52, 32),
                      rotation=(0, tx*63.0, 0))
            self._tile_ents.append(twig)

    def _make_blocking_obj(self, tid, wx, wz):
        if tid in (TR, PALM, DT, LN, ORE_TBG, ORE_BSI, ORE_EMS, ORE_KRS, ORE_MTH, CRYS, H, FP, GR, TV, CHR, CAL,
                   WARUNG, RUMAH_PG, UNION_HL, SHRINE, DEBRIS, LAUNDRY, GRAFFITI_W,
                   BD, TB, ST, BS, SH, CT, CH, PP, MR, CL):   # furniture → props.py
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
                    tex = 'wall_stone'
                    col = _c(88, 82, 78)   # plester beton tua, gelap kusam
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

