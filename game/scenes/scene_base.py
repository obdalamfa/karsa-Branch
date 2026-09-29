"""scene_base.py — Scene: satu peta ubin, dan bentuk serialisasinya.

`Scene` bisa diubah menjadi dict dan dibangun kembali darinya. Itu fondasi bagi
editor yang mengedit peta sebagai DATA, bukan sebagai kode Python — lihat
hambatan #13 di `docs/CODE_MAP.md` ("Build/buy menuntut peta sebagai data yang
bisa dimutasi dan diserialisasi").

## Yang bisa dan tidak bisa diserialisasi

Hampir seluruh `Scene` adalah data: grid ubin, daftar portal, zona cat, ukuran,
bendera indoor/horizon.

Satu-satunya yang TIDAK bisa adalah `Scene.builder` — ia fungsi Python
(`lambda world: build_cavern(world, scene)`), dan JSON tidak punya konsep
closure. Karena itu berkas scene menyimpan NAMA buildernya, dan
`resolve_builder()` memetakan nama itu kembali ke fungsi yang sebenarnya.

## Kenapa ID ubin disimpan sebagai NAMA

Berkas scene menyimpan `"CV_W"`, bukan `28`. Kalau urutan `range(51)` di
`config.py` suatu saat berubah, berkas berbasis angka akan diam-diam menunjuk
ubin yang salah di seluruh 15 scene — kerusakan yang tidak memunculkan satu pun
error. Nama juga yang membuat berkasnya bisa dibaca dan diedit manusia.
"""
from game.config import TILE_IDS

# Versi format berkas scene. Naikkan saat makna sebuah field berubah, lalu
# tangani perbedaannya di `Scene.from_dict`.
SCENE_VERSION = 1

# Nama builder yang sah. Ditulis sebagai nama, bukan referensi fungsi, supaya
# modul ini tidak mengimpor props/rock_sanctuary/beach di level atas -- itu
# akan membuat siklus impor, karena ketiganya mengimpor scene_base.
BUILDER_NAMES = ('default', 'beach', 'mountain', 'cave')

_ID_TO_KEY = {value: name for name, value in TILE_IDS.items()}


def tile_key(tid: int) -> str:
    """Nama konstanta untuk sebuah ID ubin."""
    return _ID_TO_KEY.get(tid, f'UNKNOWN_{tid}')


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
    from .props import default_prop_builder
    return lambda world: default_prop_builder(world, scene)


class Scene:
    def __init__(self, name, display, tiles, portals=None, indoor=False, builder=None,
                 has_horizon=None, paint=None, builder_name='default'):
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
        # Horizon = pelat putih raksasa 1000x1000 di world.py. Di dalam ruangan
        # pelat itu menelan seluruh interior jadi void putih ("rumah ga muncul"),
        # jadi defaultnya harus ikut `indoor`, bukan True untuk semua scene.
        self.has_horizon = (not indoor) if has_horizon is None else has_horizon

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
        )
        # Builder dipasang SESUDAH konstruksi karena `resolve_builder` butuh
        # scene-nya sendiri untuk membentuk closure-nya.
        scene.builder = resolve_builder(scene.builder_name, scene)
        return scene


def _build_indoor_room(name, display, objects, portal_exit):
    from game.config import WL, FL, DR
    w, h = 15, 6
    tiles = []
    for y in range(h):
        row = []
        for x in range(w):
            if x == 0 or x == w - 1 or y == 0 or y == h - 1:
                row.append(WL)
            else:
                row.append(FL)
        tiles.append(row)
    
    tiles[5][7] = DR
    
    for ox, oy, ot in objects:
        if 0 <= oy < h and 0 <= ox < w:
            tiles[oy][ox] = ot
        
    portals = [(7, 5, portal_exit[0], portal_exit[1], portal_exit[2])]
    return Scene(name, display, tiles, portals, indoor=True)
