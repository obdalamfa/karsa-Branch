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
# Impor ini BUKAN sekadar dekorasi: game/crops.py mendaftarkan katalog palawija,
# padi dan pohon ke data.CROPS saat diimpor (tanpa menimpa entri yang sudah
# ada). Semua kode lama yang membaca CROPS — pemilih benih Q/R di player.py,
# HUD, panel toko — langsung ikut melihat tanaman baru tanpa diubah.
from . import crops as _crops_registry  # noqa: F401

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

def _e(model, pos, scale, tex_name, tint=color.white, smooth=True, soft=True,
       tex_obj=None, **kw):
    """Buat Entity dengan tekstur + tint opsional.
    `soft=True`: cube → soft cube (rounded). Set soft=False untuk tile ground / detail tajam.
    `tex_obj`: Texture yang sudah jadi (mis. palet pagar yang dibuat runtime,
    bukan file di assets/textures) — melewati _tex() sepenuhnya."""
    if soft:
        if model == 'cube':
            from .meshes import soft_cube_mesh
            model = soft_cube_mesh()
        elif model == 'cylinder':
            from .meshes import soft_capsule_mesh
            model = soft_capsule_mesh()
    elif model == 'cylinder':
        model = Cylinder()
    t = tex_obj if tex_obj is not None else _tex(tex_name)
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

# Checkerboard indoor — kayu jati gelap.
# Nilai (value) sengaja jauh di bawah dinding: mata membaca ruangan lewat beda
# terang-gelap, bukan beda warna. Sebelumnya lantai (228,200,148) dan dinding
# (235,215,185) hampir identik, jadi ruangan terlihat seperti satu gumpalan.
_FL_LIGHT = color.rgb(150, 112, 74)
_FL_DARK  = color.rgb(131, 96, 62)

# Cave floor — cool purple-grey
_CV_LIGHT = color.rgb(132, 118, 152)
_CV_DARK  = color.rgb(108, 95, 128)

def _tile_hash(tx, ty):
    """Acak per-ubin yang deterministik, [0..1]. Tetangga tidak berkorelasi."""
    h = (int(tx) * 374761393 + int(ty) * 668265263) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def tint_mix(tx, ty):
    """Seberapa terang ubin (tx, ty) seharusnya, [0..1].

    Ini pengganti papan catur. Yang lama benar-benar papan catur: (tx+ty) % 2
    memilih antara dua warna, dan periode DUA adalah pola paling teratur yang
    bisa dibuat. Mata mengunci grid semacam itu sebelum sempat membaca apa pun
    sebagai tanah — di screenshot ladangnya terbaca sebagai papan catur, bukan
    rumput. Maksud aslinya (variasi halus ala Sims 1) tidak salah; yang salah
    periodenya.

    Dua lapis, dan keduanya perlu:

      bercak  tiga sinus berfrekuensi rendah (periode ~7, ~9, dan ~20 ubin)
              memberi bercak selebar beberapa ubin — terang di satu tempat,
              lebih tua di tempat lain, seperti tanah yang tidak rata sinarnya.
      bintik  hash per-ubin memecah bercaknya. Tanpa ini jumlah sinus tetap
              periodik dan matanya menemukan pita, cuma pita yang lebih besar.
              Dengan ini tepian bercaknya berbutir, bukan bergaris.

    Deterministik dari koordinat ubin: scene yang sama selalu terlihat sama,
    jadi tangkapan layar regresi tidak berkedip antar-jalan.
    """
    s = (math.sin(tx * 0.31 + ty * 0.47) * 0.45 +
         math.sin(tx * 0.73 - ty * 0.19 + 2.1) * 0.30 +
         math.sin(tx * 0.17 + ty * 0.91 + 4.3) * 0.25)
    bercak = (s + 1.0) * 0.5
    return max(0.0, min(1.0, bercak * 0.70 + _tile_hash(tx, ty) * 0.30))


def _campur(gelap, terang, t):
    return color.rgb(*[int(round(a + (b - a) * t))
                       for a, b in (( gelap[0] * 255, terang[0] * 255),
                                    ( gelap[1] * 255, terang[1] * 255),
                                    ( gelap[2] * 255, terang[2] * 255))])


def _cb(tx, ty):
    return _campur(_CB_DARK, _CB_LIGHT, tint_mix(tx, ty))

def _cb_floor(tx, ty):
    # Di dalam ruangan papan catur justru BENAR: lantai papan/ubin memang
    # dipasang berselang, dan ruangannya kecil sehingga polanya terbaca
    # sebagai lantai, bukan sebagai grid yang menutupi dunia.
    return _FL_DARK if (tx + ty) % 2 == 1 else _FL_LIGHT

def _cb_cave(tx, ty):
    return _campur(_CV_DARK, _CV_LIGHT, tint_mix(tx, ty))


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
    BD:  _c(196, 92, 88),  # warm bed
    ST:  _c(198, 200, 204),
    TB:  _c(96, 130, 122),  # warm table
    BS:  _c(72, 96, 140),
    MR:  _c(165, 225, 255),  # brighter mirror
    FP:  _c(255, 148, 55),   # vivid fireplace
    CL:  _c(105, 85, 68),
    PP:  _c(88, 215, 88),    # vivid plant
    CH:  _c(120, 92, 158),
    CT:  _c(206, 208, 212),
    SH:  _c(86, 112, 96),
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

# Tile yang dianggap satu keluarga pagar. Sebuah tile pagar hanya bisa memilih
# bentuknya kalau ia tahu sisi mana yang diteruskan tetangga — dan gerbang harus
# ikut dihitung, kalau tidak palang berhenti satu tile sebelum tiang gerbang.
_FENCE_LIKE = (FN, GT, PEN)

# CROP_TEX DIHAPUS. Delapan tekstur bola tanaman (crop_lobak.png dkk) dipakai
# oleh renderer lama yang menggambar semua tanaman sebagai satu bola bertekstur.
# Renderer sekarang membangun siluet dari bentuk tumbuh dan mewarnainya dari
# CROP_CATALOG, jadi tabel ini tidak dibaca siapa pun lagi. File PNG-nya SENGAJA
# dibiarkan di assets/textures — tidak ada yang dihapus dari disk.


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
        self._grass_tiles: list = []   # (tx, ty) sejajar _grass_ents, untuk cek regresi
        self._water_t    = 0.0
        # Dinding dilacak terpisah supaya bisa dipotong (wall cutaway ala Sims 1):
        # (entity, tinggi_penuh, y_penuh, tx, ty)
        self._wall_ents: list   = []
        self._cutaway_state     = None   # cache arah kamera terakhir
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

    def _fence_bitmask(self, tx: int, ty: int) -> int:
        """4-bit N/E/S/W untuk pagar — pola persis sama dengan _road_bitmask.

        Pagar didefinisikan oleh sambungannya: tanpa ini, tile sudut memasang
        palang ke arah yang kosong dan ujung larik menggantung di udara.
        """
        n = int(self.get_tile(tx,     ty - 1) in _FENCE_LIKE)
        e = int(self.get_tile(tx + 1, ty    ) in _FENCE_LIKE)
        s = int(self.get_tile(tx,     ty + 1) in _FENCE_LIKE)
        w = int(self.get_tile(tx - 1, ty    ) in _FENCE_LIKE)
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
        if not self.get_tile(tx, ty) in WALKABLE:
            return False
        # Pohon yang DITANAM pemain menempati tilenya secara permanen — itu
        # ongkos utama menanam pohon dibanding tanaman semusim, dan ongkos itu
        # hanya nyata kalau tilenya benar-benar tidak bisa dilewati lagi.
        return not self.has_planted_tree(tx, ty)

    def has_planted_tree(self, tx: int, ty: int) -> bool:
        soil = self.state.soil.get(f"{tx},{ty},{self.scene_name}")
        if not soil:
            return False
        cid = soil.get('crop')
        if not cid:
            return False
        from . import crops
        return crops.is_tree(cid)

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
    # ─── WALL CUTAWAY (pelajaran inti dari The Sims 1) ───
    # Ruangan hanya terbaca kalau dinding yang berdiri antara kamera dan isi
    # ruangan dipangkas jadi tembok setinggi lutut. Sims 1 memangkas dinding
    # sisi-dekat; kita lakukan hal yang sama, tapi dihitung dari arah kamera
    # supaya tetap benar saat kamera diputar.
    CUTAWAY_STUB = 0.42          # tinggi sisa dinding yang dipangkas (world units)

    def update_wall_cutaway(self, cam_pos, focus_pos):
        """Pangkas dinding yang menghalangi pandangan ke titik fokus.

        Sebuah dinding dipangkas kalau ia berada di sisi kamera relatif terhadap
        fokus, diukur sepanjang sumbu pandang mendatar. Murah: hanya beberapa
        puluh dinding per scene, dan kita lewati seluruhnya kalau arah pandang
        belum berubah cukup jauh sejak frame sebelumnya.
        """
        if not self._wall_ents:
            return

        vx, vz = focus_pos[0] - cam_pos[0], focus_pos[2] - cam_pos[2]
        mag = math.hypot(vx, vz)
        if mag < 1e-4:
            return
        vx /= mag; vz /= mag

        # Proyeksi fokus ke sumbu pandang — dinding dengan proyeksi lebih kecil
        # berada di depan fokus (lebih dekat ke kamera) dan karenanya menghalangi.
        f_proj = focus_pos[0] * vx + focus_pos[2] * vz

        state = (round(vx, 2), round(vz, 2), round(f_proj, 1))
        if state == self._cutaway_state:
            return
        self._cutaway_state = state

        stub = self.CUTAWAY_STUB
        for rec in self._wall_ents:
            e, full_h, full_y = rec[0], rec[1], rec[2]
            if not e:
                continue
            proj = e.x * vx + e.z * vz
            # Ambang setengah tile: dinding tepat sejajar fokus dibiarkan berdiri
            # supaya ruangan tetap punya batas yang terbaca.
            cut = proj < f_proj - TS * 0.5
            want_h = stub if cut else full_h
            if abs(e.scale_y - want_h) > 1e-3:
                e.scale_y = want_h
                e.y = want_h / 2 + GROUND_H if cut else full_y

    def _clear(self):
        for e in self._tile_ents + self._obj_ents:
            destroy(e)
        for e in self._soil_ents.values():
            destroy(e)
        # Satu petak sekarang berisi BANYAK entity (batang, daun, buah,
        # penanda), jadi nilainya list — bukan satu Entity seperti dulu.
        for ents in self._crop_ents.values():
            for e in ents:
                destroy(e)
        self._tile_ents.clear()
        self._obj_ents.clear()
        self._soil_ents.clear()
        self._crop_ents.clear()
        self._water_ents.clear()
        self._grass_ents.clear()
        self._grass_tiles.clear()
        self._wall_ents.clear()
        self._cutaway_state = None
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
        # `default_tex` untuk scene luar ruang bernilai 'grass', dan grass.png
        # di repo ini rata-ratanya (44,13,46) — nyaris hitam, dan UNGU karena
        # R dan B jauh di atas G. Cabang normal di bawah sudah memetakannya ke
        # 'grass_tso' (78,158,50) yang benar, tapi cabang penghalang tidak:
        # ia meneruskan `default_tex` apa adanya. Akibatnya tiap ubin di bawah
        # benda penghalang jadi kotak hitam-ungu, dan di sinar matahari tepinya
        # menyala jadi kisi merah-muda.
        #
        # Untuk pohon dan lentera itu tertutup massanya sendiri. Untuk RUMAH
        # tidak: `build_house_block` memberi badan rumah lebar TS * n * 0.94,
        # jadi 6% sisa di tiap sisi membiarkan ubinnya mengintip — itulah pita
        # hitam berkisi merah-muda yang melingkari tiap bangunan di `town`.
        # props.py punya daftar tambalan `_TILE_TAMBALAN` yang mengecat ulang
        # sebagian ubin ini satu per satu; komentarnya sendiri menyebut diri
        # "tambalan sementara, bukan perbaikan", dan ia sengaja TIDAK memuat
        # bangunan dengan alasan "massanya menutupi ubinnya sendiri" — alasan
        # yang tidak berlaku justru karena angka 0,94 itu.
        #
        # Dinormalkan sekali di sini supaya semua cabang dapat tekstur yang
        # benar, bukan ditambal per jenis benda. `luar` disimpan supaya
        # perbandingan `== 'grass'` di bawah tetap berarti "ini scene luar
        # ruang" setelah nilainya diganti.
        luar = (default_tex == 'grass')
        if luar:
            default_tex = ('snow_ground' if self.state.season_index == 3
                           else 'grass_tso')

        # Pick tint based on tile type so indoor rooms aren't all white
        if tid == FL or (tid in BLOCKING and default_tex == 'floor_wood'):
            tint = _cb_floor(tx, ty)
        elif tid == CV_F or (tid in BLOCKING and default_tex == 'cave_floor'):
            tint = _cb_cave(tx, ty)
        else:
            tint = _cb(tx, ty)

        if tid in BLOCKING or tid == MB:
            if tid in _FENCE_LIKE and luar:
                # Pagar sekarang berlubang, jadi tanah di bawahnya ikut terlihat.
                # Dulu tersembunyi di balik kubus pagar; kalau dibiarkan setinggi
                # GROUND_H saja, jalur pagar terbaca sebagai pita gelap yang
                # melesak di antara rumput. Samakan tinggi dengan tutup rumput
                # tetangga (GROUND_H + 0.04) dan pakai tekstur yang sama.
                # Tambahan 2 mm bukan hiasan: tutup rumput tetangga dibuat
                # selebar TS * 1.005, jadi tepinya menjorok ~1 cm ke tile ini.
                # Kalau tingginya PERSIS sama, dua bidang jadi sebidang dan
                # z-fighting bikin garis belang di kaki tiang.
                gh = GROUND_H + 0.042
                ge = _e('cube', (wx, gh / 2, wz), (TS, gh, TS),
                        'snow_ground' if self.state.season_index == 3 else 'grass_tso',
                        tint, soft=False)
            else:
                ge = _e('cube', (wx, GROUND_H/2, wz), (TS, GROUND_H, TS), default_tex, tint, soft=False)
            self._tile_ents.append(ge)
            self._make_blocking_obj(tid, wx, wz)

        elif tid == GT:
            # Ambang gerbang: tanah padat terinjak, bukan rumput. Bukaan harus
            # terbaca sebagai jalur masuk dari satu frame diam, tanpa kursor.
            gh = GROUND_H + 0.042
            ge = _e('cube', (wx, gh / 2, wz), (TS, gh, TS), 'sand_ground',
                    _c(176, 150, 112), soft=False)
            self._tile_ents.append(ge)
            self._tile_heights[(tx, ty)] = 0.0
            self._make_gate(wx, wz)

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
            self._grass_tiles.append((tx, ty))

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
            # Jalan desa: SATU ubin tanah, bukan aspal.
            #
            # Sebelumnya di sini ada dua entitas — dasar pasir plus slab tipis
            # bertekstur `terrain/road{00..15}`, dipilih lewat bitmask 4 tetangga
            # supaya tepi jalan menyambung. Masalahnya bukan cara memasangnya,
            # tapi asetnya: road*.png itu tileset JALAN KOTA dari FreeSO/The Sims
            # Online — badan hitam aspal dengan MARKA KUNING PUTUS-PUTUS di tepi
            # ubin (diperiksa: road01 punya 246 piksel (255,255,1) di x=125..127).
            #
            # Di layar hasilnya jalur gelap berkisi dengan garis putus-putus
            # membelah petak ladang. Komentar lama di sini mengejar gejalanya
            # — "hitam pekat plus garis kuning" — dan menambal dengan
            # transparent=True supaya sebagian tembus ke dasar pasir. Yang
            # tersisa tetap aspal, cuma lebih tipis.
            #
            # `dirt_path.png` sudah ada, dibuat `tools/gen_textures.py`
            # (`gen_dirt_path`, komentarnya sendiri menyebutnya "alternatif road
            # tile"), coklat tanah (152,125,89) — dan tidak pernah dipakai satu
            # kali pun. TILE_TEX bahkan sudah memetakan P ke jalur, tapi cabang
            # ini membajaknya sebelum sampai ke sana.
            #
            # Satu ubin menggantikan dua: marka jalannya hilang, dan z-fighting
            # antara dasar dan slab yang dulu ditambal dengan slab tipis tidak
            # bisa terjadi lagi karena tidak ada lagi dua permukaan yang
            # bertumpuk. Tint dibuat nyaris putih supaya warna tekstur yang
            # tampil, bukan hasil kali dua coklat.
            base = _e('cube', (wx, GROUND_H/2, wz), (TS, GROUND_H, TS),
                      'dirt_path', _c(240, 232, 220), soft=False)
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
        """Batu kecil, rumput tinggi, dan bunga liar — 30% ubin luar ruangan.

        Isi fungsi ini dulu tidak ada hubungannya dengan namanya maupun dengan
        komentar di situs pemanggilnya. Docstring-nya berbunyi "Surreal digital
        deco: floating cubes, wireframe pyramids" dan yang ditaburkannya kubus
        CYAN melayang berputar 45° plus tiang MAGENTA neon `_c(255, 0, 255)`.
        Sementara pemanggilnya, satu-satunya, menulis "Dekorasi organik: batu
        kecil / rumput tinggi / bunga liar".

        Di layar itu tampak seperti gizmo debug yang lupa dimatikan: batang
        magenta berdiri di tengah ladang dan pecahan cyan melayang di atas
        rumput. Membandingkannya dengan frame patokan mana pun tidak ada
        gunanya selama benda-benda itu masih ada — mata membaca frame-nya
        sebagai level editor, bukan sebagai desa.

        Ketiga cabangnya dipertahankan apa adanya: jumlah, posisi, dan
        pemilihannya lewat hash ubin tidak berubah, jadi kepadatan dan
        sebarannya persis sama. Yang berganti hanya benda apa yang berdiri di
        titik itu.
        """
        ox = math.sin(tx * 53.7 + ty * 89.1) * 0.42
        oz = math.cos(tx * 73.2 + ty * 47.5) * 0.42
        dtype = int(abs(math.sin(tx * 200.3 + ty * 150.7)) * 3)

        if dtype == 0:    # Batu kecil
            batu = _e('cube', (wx + ox, surface_y + 0.05, wz + oz),
                      (0.22, 0.14, 0.20), 'rock_ground', _c(150, 142, 130))
            self._tile_ents.append(batu)

        elif dtype == 1:  # Rumput tinggi — dua bilah tipis, bukan satu tiang
            for sx, sz, tinggi in ((0.0, 0.0, 0.42), (0.07, 0.05, 0.30)):
                bilah = _e('cube',
                           (wx + ox + sx, surface_y + tinggi / 2, wz + oz + sz),
                           (0.05, tinggi, 0.05), 'grass_tso', _c(104, 150, 66))
                self._tile_ents.append(bilah)

        else:             # Bunga liar — tangkai hijau, kelopak warna dari hash
            tangkai = _e('cube', (wx + ox, surface_y + 0.15, wz + oz),
                         (0.035, 0.30, 0.035), 'grass_tso', _c(96, 138, 62))
            self._tile_ents.append(tangkai)
            # Warna dipilih dari hash ubin, bukan acak: ladang yang sama harus
            # terlihat sama tiap kali dimuat, kalau tidak tangkapan regresi
            # berkedip antar-jalan.
            palet = (_c(232, 196, 84), _c(226, 122, 138), _c(198, 158, 226))
            kelopak = palet[min(int(_tile_hash(tx * 7 + 3, ty * 11 + 5)
                                    * len(palet)), len(palet) - 1)]
            bunga = _e('sphere', (wx + ox, surface_y + 0.33, wz + oz),
                       (0.13, 0.10, 0.13), None, kelopak)
            self._tile_ents.append(bunga)

    # ─── INTERNAL: PAGAR & GERBANG ──────────────────────────
    # Sebuah pagar dikenali dari CELAH-nya, bukan dari massanya. Satu kubus utuh
    # per tile — yang dipakai sebelumnya — tidak bisa terbaca sebagai pagar dari
    # sudut kamera mana pun; ia hanya bisa terbaca sebagai kardus. Geometri
    # sebenarnya (tiang + palang + bilah) ada di meshes.fence_mesh().

    def _make_fence(self, tid, wx, wz):
        from .meshes import fence_mesh, fence_palette_texture
        tx, ty = self.world_to_tile(wx, wz)
        bm = self._fence_bitmask(tx, ty)
        # Kandang ternak sengaja beda gaya dari pagar keliling: pemain harus
        # bisa membedakan "batas kebun" dari "tempat hewan" sekali lihat.
        style = 'kandang' if tid == PEN else 'bambu'
        var = (tx * 7 + ty * 13) % 3
        # scale WAJIB (1,1,1) — mesh sudah dibangun dalam meter.
        e = _e(fence_mesh(bm, style, var), (wx, GROUND_H + 0.02, wz), (1, 1, 1),
               None, color.white, soft=False, tex_obj=fence_palette_texture())
        self._obj_ents.append(e)

    def _make_gate(self, wx, wz):
        from .meshes import gate_mesh, fence_palette_texture
        tx, ty = self.world_to_tile(wx, wz)
        bm = self._fence_bitmask(tx, ty)
        ew = ((bm >> 1) & 1) + ((bm >> 3) & 1)
        ns = (bm & 1) + ((bm >> 2) & 1)
        axis = 'x' if ew >= ns else 'z'
        # Tiang dilewati kalau tetangga di sisi itu juga gerbang: gerbang dua
        # tile (kuburan) harus jadi SATU bukaan lebar, bukan empat tiang rapat.
        if axis == 'x':
            lo = self.get_tile(tx - 1, ty) != GT
            hi = self.get_tile(tx + 1, ty) != GT
        else:
            lo = self.get_tile(tx, ty - 1) != GT
            hi = self.get_tile(tx, ty + 1) != GT
        var = (tx * 7 + ty * 13) % 3
        e = _e(gate_mesh(axis, lo, hi, var), (wx, GROUND_H + 0.02, wz), (1, 1, 1),
               None, color.white, soft=False, tex_obj=fence_palette_texture())
        self._obj_ents.append(e)

    def _make_blocking_obj(self, tid, wx, wz):
        if tid in (TR, PALM, DT, LN, ORE_TBG, ORE_BSI, ORE_EMS, ORE_KRS, ORE_MTH, CRYS, H, FP, GR, TV, CHR, CAL):
            # Handled by Scene builder/props.py
            return

        elif tid in (FN, PEN):
            self._make_fence(tid, wx, wz)
            return

        else:
            oh = {WL: WALL_H, CV_W: WALL_H,
                  BD: 0.62, TB: 0.82, BS: OBJ_H * 1.4, MR: OBJ_H * 1.2,
                  CL: OBJ_H * 1.35, PP: 0.70, CH: 0.80, CT: 0.90, SH: OBJ_H * 1.5,
                  GR: OBJ_H * 0.90, BOT: 0.60, MB: 0.85, ST: 0.95,
                  DR: WALL_H}.get(tid, OBJ_H)
            tex = OBJ_TEX.get(tid, None)
            
            # Default OBJ_COLORS if exists, else fallback
            col = OBJ_COLORS.get(tid, _c(130, 130, 130))
            
            sc = 0.88
            # Dinding dan batu gua dirender sebagai balok TAJAM (soft=False).
            # Soft cube membulatkan sudut sampai dinding terbaca seperti bongkahan
            # batu/bantal, bukan bidang tegak — sudut siku justru yang bikin
            # ruangan terbaca sebagai ruangan.
            sharp = False
            if tid == WL:
                sc = 1.0
                sharp = True
                if getattr(self.scene_obj, 'indoor', False):
                    # Tanpa tekstur: 'wood_plank' berwarna oranye kuat sehingga
                    # tint apa pun tetap terbaca oranye dan dinding lebur dengan
                    # lantai kayu. Plester polos memberi bidang tenang yang
                    # membuat perabot dan karakter menonjol.
                    tex = None
                    # Nilai ditahan di ~0,67: smooth_shader menambah cahaya di
                    # atas warna dasar, jadi plester putih langsung clipping ke
                    # putih rata dan detail dinding hilang.
                    col = _c(170, 164, 150)
            elif tid == CV_W:
                sc = 0.98
                sharp = True
            elif tid == DR:
                sc = 1.0

            pos_y = oh / 2 + GROUND_H
            e = _e('cube', (wx, pos_y, wz), (TS * sc, oh, TS * sc),
                   tex, col, soft=not sharp)
            self._obj_ents.append(e)
            if tid in (WL, CV_W):
                tx, ty = self.world_to_tile(wx, wz)
                self._wall_ents.append([e, oh, pos_y, tx, ty])

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
        # Tanah punya TIGA keadaan, bukan dua. Basah dan kering sudah ada;
        # yang ketiga adalah tanah yang sudah berhari-hari kering — warnanya
        # dipucatkan supaya petak yang terlupakan terbaca sebagai satu blok
        # pucat dari kejauhan, sebelum pemain sempat memeriksa satu per satu.
        basah = soil.get('watered')
        soil_tex = 'soil_wet' if basah else 'soil_dry'
        if basah:
            tint = color.rgb(255, 255, 255)
        elif soil.get('kering', 0) >= 2:
            tint = color.rgb(214, 198, 172)
        else:
            tint = color.rgb(236, 226, 210)
        e = _e('cube', (wx, GROUND_H + 0.06, wz),
               (TS * 0.92, 0.10, TS * 0.92), soil_tex, tint)
        self._soil_ents[key] = e

    # ─── INTERNAL: TANAMAN & POHON ───────────────────────
    # Kenapa bagian ini ditulis ulang: renderer lama menggambar SEMUA tanaman
    # sebagai satu bola + satu batang, hanya berganti tekstur di tahap akhir.
    # Dari kamera lot, delapan tanaman berbeda tampil sebagai delapan bola
    # identik, dan "baru tumbuh" tidak bisa dibedakan dari "siap panen".
    # Tanaman yang keadaannya tidak bisa dibaca adalah tanaman yang akan
    # dilupakan pemain — lalu pemain menyalahkan game, bukan dirinya.
    #
    # Sekarang SILUET ditentukan oleh bentuk tumbuh (umbi/daun/rumpun/tegak/
    # rambat/padi/jamur) dan UKURAN oleh tahap. Jagung tidak akan tertukar
    # dengan bayam. Dua penanda melayang memisahkan dua pertanyaan yang paling
    # sering ditanyakan pemain: butuh air (kerucut BIRU menghadap bawah)
    # versus siap panen (berlian EMAS). Warnanya sengaja berjauhan di roda
    # warna — bukan dua nuansa hijau yang harus dibandingkan berdampingan.
    #
    # JEBAKAN MESH BERBAGI (BRIEF §8.1): tiap Entity di sini memanggil getter
    # mesh-nya sendiri (low_cone_mesh() / soft_cube_mesh() lewat _e), yang
    # sudah mengembalikan _instance(). Tidak ada satu Mesh pun yang disimpan
    # ke variabel lalu dipakai ulang oleh dua Entity.

    @staticmethod
    def _plant_tint(rgb, soil):
        """Warna daun digeser oleh KEADAAN, bukan cuma oleh jenis tanaman.

        Kering → menguning. Layu → coklat. Mati → abu kecoklatan tanpa hijau.
        Ini lapisan keterbacaan kedua: penanda melayang bekerja dari jauh,
        warna daun bekerja saat pemain berdiri tepat di petaknya.
        """
        r, g_, b = rgb
        if soil.get('mati'):
            return color.rgb(92, 80, 68)
        if soil.get('layu'):
            return color.rgb(min(235, int(r * 0.72 + 60)), int(g_ * 0.55 + 34),
                             int(b * 0.45 + 22))
        if soil.get('kering', 0) > 0 and not soil.get('watered'):
            return color.rgb(min(235, int(r * 0.85 + 52)), int(g_ * 0.88 + 26),
                             int(b * 0.70))
        return color.rgb(r, g_, b)

    def _p(self, key, model, pos, scale, tex=None, tint=color.white, **kw):
        """Buat satu bagian tanaman dan daftarkan ke petak `key`."""
        e = _e(model, pos, scale, tex, tint, **kw)
        self._crop_ents.setdefault(key, []).append(e)
        return e

    def _plant_markers(self, key, cid, soil, wx, wz, top_y):
        """Penanda melayang: tetes biru = butuh air, berlian emas = siap panen."""
        from . import crops
        from .meshes import low_cone_mesh
        if soil.get('mati'):
            self._p(key, 'cube', (wx, top_y + 0.26, wz), (0.16, 0.16, 0.16),
                    None, color.rgb(74, 62, 54), smooth=False, rotation=(0, 45, 45))
            return
        if crops.is_ready(cid, soil):
            # Berlian emas — satu-satunya benda emas di petak, jadi mata
            # menemukannya dari seberang kebun tanpa harus dicari.
            self._p(key, 'cube', (wx, top_y + 0.30, wz), (0.20, 0.20, 0.20),
                    None, color.rgb(248, 206, 72), smooth=False, rotation=(0, 45, 45))
        elif crops.needs_water(cid, soil):
            # Kerucut menghadap BAWAH = bentuk tetes air, bukan sekadar kubus
            # berwarna lain. Bentuk terbaca lebih cepat daripada warna.
            self._p(key, low_cone_mesh(), (wx, top_y + 0.26, wz),
                    (0.20, 0.26, 0.20), None, color.rgb(88, 168, 236),
                    smooth=False, rotation=(180, 0, 0))

    def _update_crop(self, key, tx, ty, soil):
        """Gambar satu petak — dipakai untuk tanaman semusim MAUPUN pohon."""
        from . import crops
        self._destroy_crop(key)
        cid = soil.get('crop')
        if not cid:
            return
        wx, wz = tx * TS, ty * TS
        if crops.is_tree(cid):
            self._build_tree_plant(key, cid, soil, wx, wz)
        else:
            self._build_crop_plant(key, cid, soil, wx, wz)

    # ── TANAMAN SEMUSIM ──────────────────────────────────
    def _build_crop_plant(self, key, cid, soil, wx, wz):
        from . import crops
        sp     = crops.spec(cid)
        stage  = crops.crop_stage(cid, soil)
        daun   = self._plant_tint(sp.get('warna', (96, 140, 70)), soil)
        buah   = color.rgb(*sp.get('buah', (200, 160, 60)))
        base   = GROUND_H + 0.12
        bentuk = sp.get('bentuk', 'rumpun')

        # ── Tahap 0: benih. Gundukan pipih + dua keping biji. Sengaja nyaris
        # rata tanah: pemain harus bisa melihat "belum ada apa-apa di sini".
        if stage == 0:
            self._p(key, 'cube', (wx, base + 0.03, wz), (0.42, 0.07, 0.42),
                    'soil_dry', color.rgb(122, 96, 70))
            for sx in (-0.09, 0.09):
                self._p(key, 'cube', (wx + sx, base + 0.09, wz), (0.09, 0.03, 0.13),
                        None, color.rgb(186, 196, 148))
            self._plant_markers(key, cid, soil, wx, wz, base + 0.10)
            return

        # ── Tahap 1: tunas. Satu batang tipis + dua daun keping. Sama untuk
        # semua jenis — tunas memang belum punya ciri, dan berpura-pura punya
        # akan membuat tahap 2 kehilangan kejutannya.
        if stage == 1:
            self._p(key, 'cylinder', (wx, base + 0.11, wz), (0.045, 0.22, 0.045),
                    None, color.rgb(118, 156, 84))
            for sgn in (-1, 1):
                self._p(key, 'cube', (wx + 0.11 * sgn, base + 0.20, wz),
                        (0.20, 0.03, 0.11), None, daun, rotation=(0, 0, -18 * sgn))
            self._plant_markers(key, cid, soil, wx, wz, base + 0.26)
            return

        siap = (stage == 4)
        f    = 0.62 if stage == 2 else (0.84 if stage == 3 else 1.0)

        if bentuk == 'umbi':
            # Umbi: roset daun memancar dari satu titik + BAHU UMBI yang
            # menyembul saat siap. Umbi menyembul memang tanda panen di kebun
            # sungguhan, jadi dipakai apa adanya.
            h = 0.46 * f
            for i in range(5):
                a = math.radians(i * 72)
                self._p(key, 'cube',
                        (wx + math.cos(a) * 0.13 * f, base + h * 0.55,
                         wz + math.sin(a) * 0.13 * f),
                        (0.09, h, 0.05), None, daun,
                        rotation=(math.sin(a) * 26, i * 72, -math.cos(a) * 26))
            if siap:
                self._p(key, 'sphere', (wx, base + 0.05, wz),
                        (0.34, 0.26, 0.34), None, buah)
            self._plant_markers(key, cid, soil, wx, wz, base + h + 0.06)

        elif bentuk == 'daun':
            # Daun: roset rendah dan lebar, hampir menutup petak saat siap.
            h = 0.30 * f
            for i in range(6):
                a = math.radians(i * 60 + 12)
                self._p(key, 'cube',
                        (wx + math.cos(a) * 0.17 * f, base + h * 0.5,
                         wz + math.sin(a) * 0.17 * f),
                        (0.30 * f, 0.045, 0.17 * f), None, daun,
                        rotation=(0, i * 60, 22))
            self._plant_markers(key, cid, soil, wx, wz, base + h + 0.14)

        elif bentuk == 'tegak':
            # Tegak (jagung/sorgum): satu batang TINGGI dengan daun panjang
            # melengkung. Siluet paling menonjol di kebun — memang harus,
            # karena jagung di kebun sungguhan juga menjulang begitu.
            h = 1.50 * f
            self._p(key, 'cylinder', (wx, base + h * 0.5, wz), (0.075, h, 0.075),
                    None, daun)
            for i in range(5):
                a  = math.radians(i * 72 + 20)
                ly = base + h * (0.32 + 0.13 * i)
                self._p(key, 'cube',
                        (wx + math.cos(a) * 0.24, ly, wz + math.sin(a) * 0.24),
                        (0.50, 0.035, 0.10), None, daun,
                        rotation=(0, i * 72 + 20, 34))
            if siap:
                # Tongkol menempel miring di batang — bukan bola melayang.
                for sgn in (-1, 1):
                    self._p(key, 'cylinder',
                            (wx + 0.11 * sgn, base + h * 0.60, wz),
                            (0.15, 0.34, 0.15), None, buah,
                            rotation=(0, 0, 16 * sgn))
            self._plant_markers(key, cid, soil, wx, wz, base + h + 0.06)

        elif bentuk == 'rambat':
            # Rambat (labu/ubi jalar/kacang panjang): hamparan daun menutup
            # tanah + sulur. Rendah dan LEBAR — kebalikan siluet 'tegak'.
            for i in range(7):
                a = math.radians(i * 51 + 8)
                r = 0.34 * f
                self._p(key, 'cube',
                        (wx + math.cos(a) * r, base + 0.07, wz + math.sin(a) * r),
                        (0.26 * f, 0.04, 0.22 * f), None, daun,
                        rotation=(0, i * 51, 6))
            self._p(key, 'cylinder', (wx, base + 0.16 * f, wz),
                    (0.05, 0.32 * f, 0.05), None, daun, rotation=(9, 0, 14))
            if siap:
                if sp.get('hasil', 1) <= 1:
                    # Satu buah besar bertumpu di hamparan (labu).
                    self._p(key, 'sphere', (wx + 0.13, base + 0.19, wz - 0.09),
                            (0.42, 0.34, 0.42), None, buah)
                else:
                    # Polong menggantung (kacang panjang / ubi jalar).
                    for i in range(3):
                        a = math.radians(i * 120 + 30)
                        self._p(key, 'cylinder',
                                (wx + math.cos(a) * 0.18, base + 0.18,
                                 wz + math.sin(a) * 0.18),
                                (0.05, 0.30, 0.05), None, buah,
                                rotation=(24, i * 120, 18))
            self._plant_markers(key, cid, soil, wx, wz, base + 0.34)

        elif bentuk == 'padi':
            # Padi: rumpun rapat berisi banyak helai halus. Saat masak helainya
            # MERUNDUK dan menguning — tanda padi siap panen yang dikenal semua
            # orang, dan tidak butuh satu kata pun untuk dijelaskan.
            h = 0.72 * f
            n = 9
            for i in range(n):
                a = math.radians(i * (360 / n) + 11)
                r = 0.10 + (i % 3) * 0.035
                lean = 44 if siap else 13
                self._p(key, 'cube',
                        (wx + math.cos(a) * r, base + h * 0.5, wz + math.sin(a) * r),
                        (0.05, h, 0.035), None, buah if siap else daun,
                        rotation=(math.sin(a) * lean, i * 41, -math.cos(a) * lean))
            self._plant_markers(key, cid, soil, wx, wz, base + h * 0.9)

        elif bentuk == 'jamur':
            # Jamur: batang pendek + tudung pipih. Tidak punya daun sama sekali,
            # jadi tidak mungkin tertukar dengan apa pun di kebun.
            n = 3 if siap else 2
            for i in range(n):
                a  = math.radians(i * 120 + 25)
                ox, oz = math.cos(a) * 0.14, math.sin(a) * 0.14
                hh = (0.16 + 0.05 * i) * f
                self._p(key, 'cylinder', (wx + ox, base + hh * 0.5, wz + oz),
                        (0.07, hh, 0.07), None, color.rgb(206, 196, 176))
                self._p(key, 'sphere', (wx + ox, base + hh + 0.03, wz + oz),
                        (0.26 * f, 0.13 * f, 0.26 * f), None, daun)
            self._plant_markers(key, cid, soil, wx, wz, base + 0.34)

        else:   # 'rumpun' — tomat, cabai, kacang tanah, kedelai, stroberi
            # Rumpun: batang tengah + tiga cabang bergerombol daun. Buah
            # menggantung di cabang saat siap, bukan melayang di tengah.
            h = 0.72 * f
            self._p(key, 'cylinder', (wx, base + h * 0.42, wz),
                    (0.06, h * 0.84, 0.06), None, daun)
            for i in range(3):
                a  = math.radians(i * 120 + 18)
                ox, oz = math.cos(a) * 0.17 * f, math.sin(a) * 0.17 * f
                self._p(key, 'sphere', (wx + ox, base + h * 0.66, wz + oz),
                        (0.34 * f, 0.26 * f, 0.34 * f), None, daun)
                if siap:
                    self._p(key, 'sphere',
                            (wx + ox * 1.25, base + h * 0.46, wz + oz * 1.25),
                            (0.16, 0.16, 0.16), None, buah)
            self._plant_markers(key, cid, soil, wx, wz, base + h + 0.06)

    # ── POHON ────────────────────────────────────────────
    def _build_tree_plant(self, key, cid, soil, wx, wz):
        """Pohon yang ditanam pemain.

        Bedanya dari tanaman semusim harus TERLIHAT, bukan cuma tertulis di
        tabel: batang berkayu, tinggi bertambah tiap tahap, dan tajuknya tetap
        berdiri setelah dipanen. Bibit sengaja diberi AJIR bambu supaya sekali
        lihat pemain tahu "ini pohon yang sedang tumbuh", bukan tunas sayur.
        """
        from . import crops
        sp     = crops.spec(cid)
        st     = crops.tree_stage(cid, soil)
        daun   = self._plant_tint(sp.get('warna', (78, 126, 62)), soil)
        buah   = color.rgb(*sp.get('buah', (196, 162, 62)))
        kayu   = color.rgb(88, 78, 70) if soil.get('mati') else color.rgb(104, 80, 56)
        tinggi_penuh = sp.get('tinggi', 4.0)
        bentuk = sp.get('bentuk', 'rindang')
        base   = GROUND_H

        # Tinggi per tahap: bibit 18%, muda 52%, dewasa/berbuah 100%.
        h = tinggi_penuh * (0.18, 0.52, 1.0, 1.0)[st]

        if st == 0:
            self._p(key, 'cylinder', (wx, base + h * 0.5, wz), (0.06, h, 0.06),
                    None, kayu)
            for i in range(3):
                a = math.radians(i * 120 + 30)
                self._p(key, 'cube',
                        (wx + math.cos(a) * 0.13, base + h * 0.86,
                         wz + math.sin(a) * 0.13),
                        (0.24, 0.035, 0.13), None, daun, rotation=(0, i * 120, 18))
            self._p(key, 'cylinder', (wx + 0.16, base + h * 0.62, wz + 0.10),
                    (0.035, h * 1.24, 0.035), None, color.rgb(176, 156, 108),
                    rotation=(0, 0, 5))
            self._plant_markers(key, cid, soil, wx, wz, base + h * 1.3)
            return

        # Batang berkayu — makin tua makin gemuk.
        tebal = 0.11 + 0.13 * (h / max(tinggi_penuh, 0.01))
        self._p(key, 'cylinder', (wx, base + h * 0.44, wz),
                (tebal, h * 0.88, tebal), None, kayu)

        if bentuk == 'kelapa':
            # Kelapa: batang polos tinggi, pelepah memancar hanya di puncak.
            for i in range(6):
                a = math.radians(i * 60)
                self._p(key, 'cube',
                        (wx + math.cos(a) * 0.62, base + h * 0.90,
                         wz + math.sin(a) * 0.62),
                        (1.35, 0.05, 0.30), None, daun, rotation=(0, i * 60 + 90, 18))
            if st == 3:
                for i in range(3):
                    a = math.radians(i * 120 + 40)
                    self._p(key, 'sphere',
                            (wx + math.cos(a) * 0.22, base + h * 0.80,
                             wz + math.sin(a) * 0.22),
                            (0.26, 0.28, 0.26), None, buah)
        elif bentuk == 'pisang':
            # Pisang: daun panjang tegak melengkung, tandan menggantung.
            for i in range(5):
                a = math.radians(i * 72 + 15)
                self._p(key, 'cube',
                        (wx + math.cos(a) * 0.40, base + h * 0.86,
                         wz + math.sin(a) * 0.40),
                        (1.05, 0.05, 0.42), None, daun, rotation=(0, i * 72 + 90, 30))
            if st == 3:
                self._p(key, 'cylinder', (wx + 0.26, base + h * 0.66, wz),
                        (0.30, 0.42, 0.30), None, buah, rotation=(0, 0, 18))
        elif bentuk == 'pepaya':
            # Pepaya: batang tunggal tak bercabang, daun berjari di puncak,
            # buah menempel LANGSUNG di batang — cirinya yang paling khas.
            for i in range(5):
                a = math.radians(i * 72 + 30)
                self._p(key, 'cube',
                        (wx + math.cos(a) * 0.34, base + h * 0.92,
                         wz + math.sin(a) * 0.34),
                        (0.72, 0.05, 0.44), None, daun, rotation=(0, i * 72, 24))
            if st == 3:
                for i in range(3):
                    a = math.radians(i * 120)
                    self._p(key, 'sphere',
                            (wx + math.cos(a) * 0.17,
                             base + h * (0.66 + 0.06 * i),
                             wz + math.sin(a) * 0.17),
                            (0.24, 0.30, 0.24), None, buah)
        else:
            # Rindang (mangga / rambutan / nangka / jambu): tajuk bertumpuk.
            lebar = tinggi_penuh * 0.52 * (0.72 if st == 1 else 1.0)
            self._p(key, 'sphere', (wx, base + h * 0.92, wz),
                    (lebar, lebar * 0.80, lebar), 'tree_leaf', daun)
            self._p(key, 'sphere',
                    (wx + lebar * 0.16, base + h * 1.14, wz - lebar * 0.14),
                    (lebar * 0.74, lebar * 0.62, lebar * 0.74), 'tree_leaf', daun)
            if st == 3:
                for i in range(4):
                    a = math.radians(i * 90 + 25)
                    self._p(key, 'sphere',
                            (wx + math.cos(a) * lebar * 0.42, base + h * 0.86,
                             wz + math.sin(a) * lebar * 0.42),
                            (0.24, 0.24, 0.24), None, buah)

        self._plant_markers(key, cid, soil, wx, wz, base + h * 1.28)

    def _destroy_crop(self, key):
        ents = self._crop_ents.pop(key, None)
        if not ents:
            return
        for e in ents:
            destroy(e)

