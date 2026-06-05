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
                       door_x=None, door_y=None, extra_builder=None):
    """
    Bangun ruangan indoor dengan tile WL/FL/DR.
    w, h: ukuran ruangan (default 15×8 — lebih luas dari sebelumnya)
    door_x/y: posisi pintu (default: tengah bawah)
    extra_builder: callable(world) untuk tambah props khusus ruangan
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

    def _combined_builder(world):
        from .props import default_prop_builder
        default_prop_builder(world, scene_obj)
        _add_indoor_atmosphere(world, scene_obj)
        if extra_builder:
            extra_builder(world)

    scene_obj = Scene(name, display, tiles, portals, indoor=True,
                      builder=_combined_builder)
    return scene_obj


def _add_indoor_atmosphere(world, scene):
    """
    Tambahkan detail atmosfer otomatis ke setiap ruangan indoor:
    noda dinding, debu, retakan, kabel gantung — ala Disco Elysium.
    """
    import math
    from game.config import TILE_SIZE, GROUND_H, WALL_H, OBJ_H
    from ursina import color

    TS = TILE_SIZE

    def _h(x, z):
        return abs(math.sin(x * 31.7 + z * 47.3))

    W = scene.w
    H = scene.h

    # ── Noda di sudut-sudut dinding ──
    corners = [(1, 1), (W-2, 1), (1, H-2), (W-2, H-2)]
    for cx, cy in corners:
        wx, wz = cx * TS, cy * TS
        hv = _h(wx, wz)
        if hv > 0.4:
            # Noda air gelap di pojok bawah dinding
            stain = world._create_entity('cube',
                       (wx, GROUND_H + WALL_H*0.18, wz),
                       (TS*0.15, WALL_H*0.35, TS*0.12), None,
                       color.rgb(int(52 + hv*18), int(48 + hv*15), int(45 + hv*12)))
            world._obj_ents.append(stain)

    # ── Kabel/kawat gantung di langit-langit ──
    mid_x = (W // 2) * TS
    mid_z = (H // 2) * TS
    hv2 = _h(mid_x, mid_z)
    if hv2 > 0.35:
        wire = world._create_entity('cube',
                  (mid_x, WALL_H + GROUND_H - 0.05, mid_z),
                  (TS * (W*0.4), 0.025, 0.025), None,
                  color.rgb(35, 32, 28))
        bulb_wire = world._create_entity('cylinder',
                       (mid_x + TS*0.2, WALL_H + GROUND_H - 0.22, mid_z),
                       (0.02, 0.38, 0.02), None,
                       color.rgb(35, 32, 28))
        bulb = world._create_entity('sphere',
                  (mid_x + TS*0.2, WALL_H + GROUND_H - 0.42, mid_z),
                  (0.10, 0.10, 0.10), 'lamp_glow',
                  color.rgb(215, 185, 115))
        world._obj_ents.extend([wire, bulb_wire, bulb])

    # ── Retakan dinding (1-2 lokasi acak) ──
    crack_spots = [(2, 2), (W-3, H-3)]
    for cx, cy in crack_spots:
        if cx >= W-1 or cy >= H-1:
            continue
        hv3 = _h(cx * TS, cy * TS)
        if hv3 > 0.55:
            crack = world._create_entity('cube',
                       (cx * TS, GROUND_H + WALL_H*0.55, (cy-1) * TS + 0.05),
                       (TS*0.06, WALL_H*0.42, 0.04), None,
                       color.rgb(42, 38, 35))
            world._obj_ents.append(crack)

    # ── Genangan air di lantai (salah satu sudut) ──
    puddle_x = 2 * TS
    puddle_z = (H - 3) * TS
    puddle = world._create_entity('cube',
                (puddle_x, GROUND_H + 0.012, puddle_z),
                (TS*0.55, 0.018, TS*0.42), None,
                color.rgb(42, 48, 45))
    world._obj_ents.append(puddle)
