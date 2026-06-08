class Scene:
    def __init__(self, name, display, tiles, portals=None, indoor=False, builder=None, has_horizon=True):
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
        self.has_horizon = has_horizon


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
