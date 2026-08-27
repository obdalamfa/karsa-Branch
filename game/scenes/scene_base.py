class Scene:
    def __init__(self, name, display, tiles, portals=None, indoor=False, builder=None,
                 has_horizon=None, paint=None):
        if builder is None:
            from .props import default_prop_builder
            self.builder = lambda world: default_prop_builder(world, self)
        else:
            self.builder = builder
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
