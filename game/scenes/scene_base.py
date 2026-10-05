"""scene_base.py — Scene: satu peta ubin, dan bentuk serialisasinya.

`Scene` bisa diubah menjadi dict dan dibangun kembali darinya. Itu fondasi bagi
editor yang mengedit peta sebagai DATA, bukan sebagai kode Python — lihat
hambatan #13 di `docs/CODE_MAP.md` ("Build/buy menuntut peta sebagai data yang
bisa dimutasi dan diserialisasi").

Berkas ini juga membawa `_build_indoor_room()` dan `_add_indoor_atmosphere()`
dari cabang visual/3d-mobs: pembangun ruangan indoor bertema (shop, clinic,
smith, greenhouse, studio) yang jauh lebih kaya daripada ruangan WL/FL/DR
polos. Lima scene (klinik, warung, bengkel, studio, rumah) memanggilnya dengan
`w=`, `h=`, dan `theme=` — argumen yang TIDAK ADA di versi lama, jadi fungsi
ini wajib superset, bukan diganti.

## Yang bisa dan tidak bisa diserialisasi

Hampir seluruh `Scene` adalah data: grid ubin, daftar portal, zona cat, ukuran,
bendera indoor/horizon.

Satu-satunya yang TIDAK bisa adalah `Scene.builder` — ia fungsi Python
(`lambda world: build_cavern(world, scene)`), dan JSON tidak punya konsep
closure. Karena itu berkas scene menyimpan NAMA buildernya, dan
`resolve_builder()` memetakan nama itu kembali ke fungsi yang sebenarnya.
Ruangan indoor bertema dibangun lewat `_combined_builder` tertutup
(`_build_indoor_room`), yang juga tidak bisa diserialisasi lewat nama --
builder_name-nya jatuh ke 'default' kalau ruangan itu diekspor ke berkas
scene, dan atmosfer temanya tidak ikut. Itu bukan regresi dari gabungan ini:
`BUILDER_NAMES` di bawah tidak pernah mencakup tema ruangan sejak awal.

## Kenapa ID ubin disimpan sebagai NAMA

Berkas scene menyimpan `"CV_W"`, bukan `28`. Kalau urutan `range(51)` di
`config.py` suatu saat berubah, berkas berbasis angka akan diam-diam menunjuk
ubin yang salah di seluruh 15 scene — kerusakan yang tidak memunculkan satu pun
error. Nama juga yang membuat berkasnya bisa dibaca dan diedit manusia.
"""
import math

from game.config import TILE_IDS

# Versi format berkas scene. Naikkan saat makna sebuah field berubah, lalu
# tangani perbedaannya di `Scene.from_dict`.
SCENE_VERSION = 1

# Nama builder yang sah. Ditulis sebagai nama, bukan referensi fungsi, supaya
# modul ini tidak mengimpor props/rock_sanctuary/beach di level atas -- itu
# akan membuat siklus impor, karena ketiganya mengimpor scene_base.
BUILDER_NAMES = ('default', 'beach', 'mountain', 'cave', 'interior')

_ID_TO_KEY = {value: name for name, value in TILE_IDS.items()}


def tile_key(tid: int) -> str:
    """Nama konstanta untuk sebuah ID ubin."""
    return _ID_TO_KEY.get(tid, f'UNKNOWN_{tid}')


# ─── Objek terpasang bebas ──────────────────────────────────────────────────
# Perabot yang diletakkan di POSISI, bukan di sel grid. Bentuknya sengaja
# sekecil mungkin: `kind` menunjuk ke tile ID yang sudah ada lewat
# `objects.tile_dari_kind`, sehingga tekstur, nama pemain, interaksi, dan sifat
# memblokirnya tidak perlu disimpan di sini -- semuanya sudah ada di tabel yang
# dipakai grid. Yang benar-benar BARU hanyalah posisi bebas dan rotasi; itulah
# satu-satunya hal yang tidak bisa diungkapkan grid.
#
# KONVENSI KOORDINAT, dan ini mengikuti seluruh basis kode:
#   `x`, `y`  koordinat UBIN dalam float -- sama dengan `player_x/player_y`,
#             `portals`, `npc_positions`, dan `wild_entities`. `12.5` berarti
#             "di antara ubin 12 dan 13".
#   `h`       ketinggian di atas tanah, dalam satuan dunia.
#   `rot_y`   putaran mengelilingi sumbu tegak, derajat.
# Versi pertama skema ini memakai `x`/`z` untuk posisi ubin dan `y` untuk
# ketinggian -- persis TERBALIK dari kebiasaan seluruh basis kode, dan karena
# itu menyesatkan setiap pembaca berikutnya.
def _angka(nilai, baku):
    """float yang terhingga, atau `baku` kalau nilainya tidak bisa dipakai.

    `math.isfinite` penting di sini: `float('nan')` adalah float yang sah di
    Python, tapi NaN dan Infinity BUKAN JSON yang sah. Menerimanya berarti
    menulis berkas yang tidak bisa dibaca alat lain.
    """
    try:
        v = float(nilai)
    except (TypeError, ValueError):
        return baku
    return v if math.isfinite(v) else baku


def _objek_sah(o):
    """Validasi satu objek terpasang. None kalau tidak bisa dipakai.

    Objek rusak dibuang SATU, bukan menjatuhkan seluruh scene: satu entri salah
    ketik di berkas peta tidak boleh membuat game tidak bisa dibuka. Pola yang
    sama dengan pemuat scene di `__init__.py`.
    """
    from game.objects import tile_dari_kind
    if not isinstance(o, dict):
        return None
    kind = o.get('kind')
    if not isinstance(kind, str) or tile_dari_kind(kind) is None:
        return None
    x, y = _angka(o.get('x'), None), _angka(o.get('y'), None)
    if x is None or y is None:
        return None
    skala = _angka(o.get('scale'), 1.0)
    return {
        'kind': kind,
        'x': x, 'y': y,
        'h': _angka(o.get('h'), 0.0),
        'rot_y': _angka(o.get('rot_y'), 0.0) % 360.0,
        'scale': skala if skala > 0 else 1.0,
    }


def resolve_builder(name: str, scene):
    """Petakan nama builder dari berkas scene kembali ke fungsinya.

    `Scene.builder` selalu dipanggil dengan SATU argumen (`builder(world)` oleh
    `world.py`), jadi tiap cabang mengembalikan callable satu-argumen. Perhatikan
    `beach_builder` sudah berbentuk begitu, sedangkan `default_prop_builder`,
    `build_cavern`, dan `build_mountain_landscape` menerima `(world, scene)`.
    """
    if name == 'cave':
        from .rock_sanctuary import build_cavern
        return lambda world: build_cavern(world, scene)
    if name == 'mountain':
        from .rock_sanctuary import build_mountain_landscape
        return lambda world: build_mountain_landscape(world, scene)
    if name == 'beach':
        from .beach import beach_builder
        return beach_builder
    if name == 'interior':
        from .interior import build_interior
        return lambda world: build_interior(world, scene)
    from .props import default_prop_builder
    return lambda world: default_prop_builder(world, scene)


class Scene:
    def __init__(self, name, display, tiles, portals=None, indoor=False, builder=None,
                 has_horizon=None, paint=None, builder_name='default', objects=None):
        if builder is None:
            from .props import default_prop_builder
            self.builder = lambda world: default_prop_builder(world, self)
        else:
            self.builder = builder
        # Nama builder disimpan terpisah dari callable-nya karena hanya namanya
        # yang bisa masuk berkas scene. Scene yang memasang builder kustom
        # (beach, mountain, naga_cave) wajib menyetelnya; sisanya 'default'.
        self.builder_name = builder_name
        self.name    = name
        self.display = display
        self.tiles   = tiles
        self.w       = len(tiles[0]) if tiles else 0
        self.h       = len(tiles) if tiles else 0
        self.portals = portals or []
        self.indoor  = indoor
        # Lapisan warna per-ZONA (lihat game/scenes/zone_paint.py). Tiap entri
        # adalah satu Zone: satu persegi ubin yang dicat ulang oleh SATU entity.
        # Dibutuhkan karena world.py mewarnai hampir semua ubin luar ruang
        # dengan papan catur RUMPUT, sehingga ladang tanah terbaca sebagai
        # halaman. Zona dipegang di sini, bukan di dalam builder, supaya
        # default_prop_builder() tahu ubin mana yang SUDAH tertutup dan tidak
        # perlu ditambal satu-satu.
        self.paint   = list(paint or [])
        # Objek terpasang bebas. Validasinya ada di SETTER properti di bawah,
        # bukan di sini, supaya penugasan langsung sesudah konstruksi -- yang
        # justru dilakukan editor -- tidak bisa melewatinya.
        self.objects = objects
        # Horizon = pelat putih raksasa 1000x1000 di world.py. Di dalam ruangan
        # pelat itu menelan seluruh interior jadi void putih ("rumah ga muncul"),
        # jadi defaultnya harus ikut `indoor`, bukan True untuk semua scene.
        self.has_horizon = (not indoor) if has_horizon is None else has_horizon

    # ─── Objek terpasang ────────────────────────────────────────────────────
    @property
    def objects(self):
        return self._objects

    @objects.setter
    def objects(self, nilai):
        """Validasi di SETTER, bukan cuma di `__init__`.

        Versi pertama hanya memvalidasi saat konstruksi, dan itu lubang: editor
        -- dan kode mana pun -- menulis `scene.objects = [...]` langsung, jadi
        daftar mentah bisa masuk dan baru meledak jauh kemudian di `to_dict`.
        Properti membuat invariannya tidak bisa dilanggar lewat penugasan.

        Ketahuan dari uji dengan data kotor, bukan dari membaca ulang.
        """
        self._objects = [o for o in (_objek_sah(x) for x in (nilai or [])) if o]

    # ─── Bentuk data ────────────────────────────────────────────────────────
    def to_dict(self) -> dict:
        """Ubah scene jadi dict yang aman di-JSON-kan.

        Grid ubin disimpan sebagai ANGKA INDEKS ke dalam `legend`, bukan sebagai
        nama di tiap sel. Dengan 15 scene berukuran sampai 35x30, nama di tiap
        sel membengkakkan berkas sekitar sepuluh kali lipat tanpa menambah
        informasi apa pun -- legendanya sudah memuat semua nama yang dipakai.
        """
        legend, index, grid = [], {}, []
        for row in self.tiles:
            out = []
            for tid in row:
                slot = index.get(tid)
                if slot is None:
                    slot = index[tid] = len(legend)
                    legend.append(tid)
                out.append(slot)
            grid.append(out)
        return {
            'scene_version': SCENE_VERSION,
            'name': self.name,
            'display': self.display,
            'size': [self.w, self.h],
            'indoor': bool(self.indoor),
            'has_horizon': bool(self.has_horizon),
            'builder': self.builder_name,
            'legend': [tile_key(t) for t in legend],
            'tiles': grid,
            'portals': [list(p) for p in self.portals],
            'paint': [z.to_dict() for z in self.paint],
            'objects': [dict(o) for o in self.objects],
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Scene':
        """Bangun kembali scene dari dict hasil `to_dict()`."""
        version = data.get('scene_version', SCENE_VERSION)
        if version != SCENE_VERSION:
            # Belum ada format lain yang pernah ditulis, jadi belum ada langkah
            # migrasi nyata. Kaitannya ada di sini supaya perubahan berikutnya
            # tidak lupa menambahkannya.
            raise ValueError(
                f'scene_version {version} tidak dikenal (kode ini: {SCENE_VERSION})')

        legend = data['legend']
        missing = [name for name in legend if name not in TILE_IDS]
        if missing:
            raise ValueError(f'nama ubin tidak dikenal di legend: {missing}')
        lookup = [TILE_IDS[name] for name in legend]

        tiles = [[lookup[slot] for slot in row] for row in data['tiles']]

        from .zone_paint import Zone
        scene = cls(
            name=data['name'],
            display=data['display'],
            tiles=tiles,
            portals=[tuple(p) for p in data.get('portals', [])],
            indoor=bool(data.get('indoor', False)),
            has_horizon=bool(data.get('has_horizon', True)),
            paint=[Zone.from_dict(z) for z in data.get('paint', [])],
            builder_name=data.get('builder', 'default'),
            objects=data.get('objects', []),
        )
        # Builder dipasang SESUDAH konstruksi karena `resolve_builder` butuh
        # scene-nya sendiri untuk membentuk closure-nya.
        scene.builder = resolve_builder(scene.builder_name, scene)
        return scene


def _build_indoor_room(name, display, objects, portal_exit, w=15, h=8,
                       door_x=None, door_y=None, extra_builder=None, theme='default'):
    """
    Bangun ruangan indoor dengan tile WL/FL/DR.
    w, h: ukuran ruangan (default 15×8 — lebih luas dari sebelumnya)
    door_x/y: posisi pintu (default: tengah bawah)
    extra_builder: callable(world) untuk tambah props khusus ruangan
    theme: tema atmosfer interior ('default'|'shop'|'clinic'|'smith'|'greenhouse'|'studio')
    """
    from game.config import WL, FL, DR

    if door_x is None:
        door_x = w // 2
    if door_y is None:
        door_y = h - 1

    tiles = []
    for y in range(h):
        row = []
        for x in range(w):
            if x == 0 or x == w - 1 or y == 0 or y == h - 1:
                row.append(WL)
            else:
                row.append(FL)
        tiles.append(row)

    tiles[door_y][door_x] = DR

    for ox, oy, ot in objects:
        if 0 <= oy < h and 0 <= ox < w:
            tiles[oy][ox] = ot

    portals = [(door_x, door_y, portal_exit[0], portal_exit[1], portal_exit[2])]

    _theme = theme  # capture for closure

    def _combined_builder(world):
        from .props import default_prop_builder
        default_prop_builder(world, scene_obj)
        _add_indoor_atmosphere(world, scene_obj, _theme)
        if extra_builder:
            extra_builder(world)

    scene_obj = Scene(name, display, tiles, portals, indoor=True,
                      builder=_combined_builder)
    return scene_obj


def _add_indoor_atmosphere(world, scene, theme='default'):
    """
    Tambahkan detail atmosfer otomatis ke setiap ruangan indoor.
    theme: 'default' | 'shop' | 'clinic' | 'smith' | 'greenhouse' | 'studio'
    """
    import math
    from game.config import TILE_SIZE, GROUND_H, WALL_H, OBJ_H
    from ursina import color

    TS = TILE_SIZE

    def _h(x, z):
        return abs(math.sin(x * 31.7 + z * 47.3))

    W = scene.w
    H = scene.h
    mid_x = (W // 2) * TS
    mid_z = (H // 2) * TS
    hv2 = _h(mid_x, mid_z)

    if theme == 'default':
        # ── Noda di sudut-sudut dinding ──
        corners = [(1, 1), (W-2, 1), (1, H-2), (W-2, H-2)]
        for cx, cy in corners:
            wx, wz = cx * TS, cy * TS
            hv = _h(wx, wz)
            if hv > 0.4:
                stain = world._create_entity('cube',
                           (wx, GROUND_H + WALL_H*0.18, wz),
                           (TS*0.15, WALL_H*0.35, TS*0.12), None,
                           color.rgb(int(52 + hv*18), int(48 + hv*15), int(45 + hv*12)))
                world._obj_ents.append(stain)

        # ── Kabel/kawat gantung di langit-langit ──
        if hv2 > 0.35:
            wire = world._create_entity('cube',
                      (mid_x, WALL_H + GROUND_H - 0.05, mid_z),
                      (TS * (W*0.4), 0.025, 0.025), None, color.rgb(35, 32, 28))
            bulb_wire = world._create_entity('cylinder',
                           (mid_x + TS*0.2, WALL_H + GROUND_H - 0.22, mid_z),
                           (0.02, 0.38, 0.02), None, color.rgb(35, 32, 28))
            bulb = world._create_entity('sphere',
                      (mid_x + TS*0.2, WALL_H + GROUND_H - 0.42, mid_z),
                      (0.10, 0.10, 0.10), 'lamp_glow', color.rgb(215, 185, 115))
            world._obj_ents.extend([wire, bulb_wire, bulb])

        # ── Retakan dinding ──
        crack_spots = [(2, 2), (W-3, H-3)]
        for cx, cy in crack_spots:
            if cx >= W-1 or cy >= H-1:
                continue
            hv3 = _h(cx * TS, cy * TS)
            if hv3 > 0.55:
                crack = world._create_entity('cube',
                           (cx * TS, GROUND_H + WALL_H*0.55, (cy-1) * TS + 0.05),
                           (TS*0.06, WALL_H*0.42, 0.04), None, color.rgb(42, 38, 35))
                world._obj_ents.append(crack)

        # ── Genangan air ──
        puddle = world._create_entity('cube',
                    (2 * TS, GROUND_H + 0.012, (H - 3) * TS),
                    (TS*0.55, 0.018, TS*0.42), None, color.rgb(42, 48, 45))
        world._obj_ents.append(puddle)

    elif theme == 'shop':
        # Lantai lebih terang — strip highlight
        floor_strip = world._create_entity('cube',
                         (mid_x, GROUND_H + 0.008, mid_z),
                         (TS * (W - 2) * 0.92, 0.012, TS * (H - 2) * 0.92),
                         None, color.rgb(185, 175, 155))
        world._obj_ents.append(floor_strip)

        # Lampu lebih banyak — kuning hangat
        lamp_positions = [
            (mid_x - TS * 2, mid_z), (mid_x + TS * 2, mid_z),
            (mid_x, mid_z - TS), (mid_x, mid_z + TS),
        ]
        for lx, lz in lamp_positions:
            wire = world._create_entity('cylinder',
                      (lx, WALL_H + GROUND_H - 0.18, lz),
                      (0.02, 0.30, 0.02), None, color.rgb(35, 32, 28))
            bulb = world._create_entity('sphere',
                      (lx, WALL_H + GROUND_H - 0.35, lz),
                      (0.10, 0.10, 0.10), 'lamp_glow', color.rgb(235, 205, 135))
            world._obj_ents.extend([wire, bulb])

        # Papan nama (strip dekoratif di dinding belakang)
        sign = world._create_entity('cube',
                  (mid_x, GROUND_H + WALL_H * 0.72, 1 * TS - 0.05),
                  (TS * (W * 0.45), 0.38, 0.06), None, color.rgb(205, 175, 118))
        world._obj_ents.append(sign)

    elif theme == 'clinic':
        # Dinding lebih terang — overlay tipis putih di sisi dalam
        for cx_t, cz_t in [(1, H//2), (W-2, H//2), (W//2, 1), (W//2, H-2)]:
            panel = world._create_entity('cube',
                       (cx_t * TS, GROUND_H + WALL_H * 0.5, cz_t * TS),
                       (TS * 0.04 if cx_t in (1, W-2) else TS * (W-2) * 0.92,
                        WALL_H * 0.85,
                        TS * (H-2) * 0.92 if cx_t in (1, W-2) else TS * 0.04),
                       None, color.rgb(228, 225, 220))
            world._obj_ents.append(panel)

        # Lantai bersih
        floor_clean = world._create_entity('cube',
                         (mid_x, GROUND_H + 0.008, mid_z),
                         (TS * (W - 2) * 0.92, 0.012, TS * (H - 2) * 0.92),
                         None, color.rgb(208, 205, 198))
        world._obj_ents.append(floor_clean)

        # Lampu putih-biru — lebih banyak, lebih terang
        for lx_o, lz_o in [(-2, 0), (2, 0), (0, -1), (0, 1)]:
            lx = mid_x + lx_o * TS
            lz = mid_z + lz_o * TS
            wire = world._create_entity('cylinder',
                      (lx, WALL_H + GROUND_H - 0.12, lz),
                      (0.02, 0.22, 0.02), None, color.rgb(38, 35, 32))
            bulb = world._create_entity('sphere',
                      (lx, WALL_H + GROUND_H - 0.28, lz),
                      (0.12, 0.12, 0.12), 'lamp_glow', color.rgb(200, 215, 225))
            world._obj_ents.extend([wire, bulb])

    elif theme == 'smith':
        # Dinding hangus di sekitar forge — noda hitam tebal
        soot_spots = [(2, 2), (W-3, 2), (2, H-3), (W-3, H-3), (W//2, 2)]
        for cx_s, cy_s in soot_spots:
            if cx_s >= W-1 or cy_s >= H-1:
                continue
            hv_s = _h(cx_s * TS, cy_s * TS)
            soot = world._create_entity('cube',
                      (cx_s * TS, GROUND_H + WALL_H * 0.28, (cy_s - 1) * TS + 0.05),
                      (TS * (0.22 + hv_s * 0.18), WALL_H * 0.55, 0.05),
                      None, color.rgb(28, 24, 20))
            world._obj_ents.append(soot)

        # Lantai gelap & kotor
        floor_dark = world._create_entity('cube',
                        (mid_x, GROUND_H + 0.008, mid_z),
                        (TS * (W - 2) * 0.92, 0.012, TS * (H - 2) * 0.92),
                        None, color.rgb(55, 48, 40))
        world._obj_ents.append(floor_dark)

        # Lampu oranye redup — atmosfer panas bengkel
        for lx_o, lz_o in [(-1, 0), (1, 0)]:
            lx = mid_x + lx_o * TS * 2
            lz = mid_z + lz_o * TS
            wire = world._create_entity('cylinder',
                      (lx, WALL_H + GROUND_H - 0.20, lz),
                      (0.02, 0.32, 0.02), None, color.rgb(35, 30, 25))
            bulb = world._create_entity('sphere',
                      (lx, WALL_H + GROUND_H - 0.40, lz),
                      (0.10, 0.10, 0.10), 'lamp_glow', color.rgb(215, 125, 45))
            world._obj_ents.extend([wire, bulb])

        # Percikan/ember di lantai
        for i in range(3):
            ex = mid_x + (i - 1) * TS * 0.8
            ember = world._create_entity('sphere',
                       (ex, GROUND_H + 0.04, mid_z - TS * 0.5),
                       (0.06, 0.06, 0.06), None, color.rgb(215, 98, 22))
            world._obj_ents.append(ember)

    elif theme == 'greenhouse':
        # Tanah visible sebagai overlay lantai coklat
        soil_strip = world._create_entity('cube',
                        (mid_x, GROUND_H + 0.008, mid_z),
                        (TS * (W - 2) * 0.92, 0.012, TS * (H - 2) * 0.92),
                        None, color.rgb(88, 65, 40))
        world._obj_ents.append(soil_strip)

        # Tanaman interior lebih rimbun
        plant_spots = [(2, 2), (W-3, 2), (2, H-3), (W-3, H-3)]
        plant_cols = [color.rgb(55, 140, 58), color.rgb(38, 115, 45),
                      color.rgb(72, 165, 65), color.rgb(48, 128, 52)]
        for i, (px_t, pz_t) in enumerate(plant_spots):
            pc = plant_cols[i % len(plant_cols)]
            foliage = world._create_entity('sphere',
                         (px_t * TS, GROUND_H + 0.55, pz_t * TS),
                         (TS * 0.55, TS * 0.50, TS * 0.55), 'cloth_green', pc)
            world._obj_ents.append(foliage)

        # Lampu biru-hijau tumbuh — grow light
        for lx_o, lz_o in [(-2, -1), (2, -1), (-2, 1), (2, 1)]:
            lx = mid_x + lx_o * TS
            lz = mid_z + lz_o * TS
            wire = world._create_entity('cylinder',
                      (lx, WALL_H + GROUND_H - 0.15, lz),
                      (0.02, 0.28, 0.02), None, color.rgb(35, 38, 35))
            bulb = world._create_entity('sphere',
                      (lx, WALL_H + GROUND_H - 0.30, lz),
                      (0.11, 0.11, 0.11), 'lamp_glow', color.rgb(115, 195, 145))
            world._obj_ents.extend([wire, bulb])

    elif theme == 'studio':
        # Dinding sedikit lebih gelap/coklat — perpustakaan kusam
        for cx_t in [1, W-2]:
            panel = world._create_entity('cube',
                       (cx_t * TS, GROUND_H + WALL_H * 0.5, mid_z),
                       (TS * 0.04, WALL_H * 0.85, TS * (H-2) * 0.90),
                       None, color.rgb(118, 105, 85))
            world._obj_ents.append(panel)

        # Lantai kayu tua
        floor_wood = world._create_entity('cube',
                        (mid_x, GROUND_H + 0.008, mid_z),
                        (TS * (W - 2) * 0.92, 0.012, TS * (H - 2) * 0.92),
                        None, color.rgb(105, 82, 55))
        world._obj_ents.append(floor_wood)

        # Lampu kuning-pudar — cahaya baca
        for lx_o, lz_o in [(-2, 0), (2, 0), (0, -1)]:
            lx = mid_x + lx_o * TS
            lz = mid_z + lz_o * TS
            wire = world._create_entity('cylinder',
                      (lx, WALL_H + GROUND_H - 0.18, lz),
                      (0.02, 0.30, 0.02), None, color.rgb(35, 32, 28))
            bulb = world._create_entity('sphere',
                      (lx, WALL_H + GROUND_H - 0.38, lz),
                      (0.10, 0.10, 0.10), 'lamp_glow', color.rgb(205, 180, 115))
            world._obj_ents.extend([wire, bulb])

        # Rak buku efek di dinding belakang (strip warna-warni)
        book_strip_cols = [
            color.rgb(140, 65, 50), color.rgb(65, 90, 125),
            color.rgb(140, 130, 65), color.rgb(75, 112, 75),
        ]
        for i, bc in enumerate(book_strip_cols):
            bx = 2 * TS + i * TS * 1.8
            bstrip = world._create_entity('cube',
                        (bx, GROUND_H + WALL_H * 0.48, 1 * TS - 0.04),
                        (TS * 0.32, WALL_H * 0.62, 0.05), None, bc)
            world._obj_ents.append(bstrip)

        # Debu di sudut
        dust_spots = [(1, 1), (W-2, H-2)]
        for dx_t, dz_t in dust_spots:
            dust = world._create_entity('cube',
                      (dx_t * TS, GROUND_H + 0.010, dz_t * TS),
                      (TS * 0.40, 0.015, TS * 0.35), None, color.rgb(115, 108, 95))
            world._obj_ents.append(dust)


# ─── Ruangan dari denah ASCII ───────────────────────────────────────────────
# Huruf denah -> nama ubin. Denah ditulis sebagai GAMBAR supaya tata letak bisa
# dibaca dan diperiksa dengan mata: daftar koordinat (x, y, ubin) yang lama
# menyembunyikan konter yang menutup satu baris penuh dan pintu yang
# mendaratkan pemain di luar peta.
DENAH = {
    '#': 'WL', '.': 'FL', 'D': 'DR', 'B': 'BD', 'S': 'ST', 'T': 'TB',
    'c': 'CHR', 'V': 'TV', 'K': 'BS', 'M': 'MR', 'F': 'FP', 'J': 'CL',
    'P': 'PP', 'C': 'CH', 'N': 'CT', 'R': 'SH', 'L': 'CAL', 'd': 'D',
    'k': 'KLK', 'w': 'WC', 'u': 'SWR',
}


def ruang_denah(name, display, denah, portal_exit):
    """Ruangan dalam dari denah ASCII, dirender oleh builder 'interior'.

    Satu-satunya `D` di denah adalah pintu; portal keluarnya dipasang di sana.
    Ubin tepat di dalam pintu harus lantai kosong -- itu titik mendarat pemain
    yang masuk, dan portal di scene luar harus menunjuk ke situ.
    `tools/interior_check.py` membuktikan semua ini.
    """
    baris = denah.strip().splitlines()
    lebar = len(baris[0])
    assert all(len(r) == lebar for r in baris), f'{name}: denah tidak persegi'
    tiles = [[TILE_IDS[DENAH[ch]] for ch in r] for r in baris]
    pintu = [(x, y) for y, r in enumerate(baris) for x, ch in enumerate(r) if ch == 'D']
    assert len(pintu) == 1, f'{name}: harus tepat satu pintu'
    px, py = pintu[0]
    portals = [(px, py, portal_exit[0], portal_exit[1], portal_exit[2])]
    sc = Scene(name, display, tiles, portals, indoor=True, builder_name='interior')
    sc.builder = resolve_builder('interior', sc)
    return sc
