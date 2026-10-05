"""blender_mob_gua.py — Desain ulang tujuh monster gua/dungeon di Blender.

Dijalankan ATOMIK di dalam Blender (scene Blender bisa ter-reset antar
panggilan socket, jadi satu exec = bersihkan -> bangun -> export -> render):

    python tools/blender_rpc.py "exec(open(r'<path>/tools/blender_mob_gua.py').read())"

Atau dari luar: python tools/blender_mob_gua.py  (mengirim dirinya lewat socket).

Tiap monster dibangun dari primitif low-poly dengan material Principled
BERWARNA -- .mtl hasil export membawa Kd per bagian, dan game memuat OBJ lewat
Assimp yang membaca .mtl (game/__init__.py). Ukuran dalam meter, kaki di z=0,
menghadap -Y (sama dengan model mob lama), export Y-atas.
"""
import math

try:
    import bpy
    import mathutils
except ImportError:          # dijalankan dari luar Blender: kirim diri sendiri
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from blender_rpc import run
    print(run(f"exec(open(r'{os.path.abspath(__file__)}', encoding='utf-8').read())"))
    raise SystemExit

import os

WT = os.environ.get('LK_WORKTREE') or r'E:/Game Research/Lembah Karsa 3D/.claude/worktrees/coba-play-game-d5f058'
MDIR = WT + '/assets/models'
PREV = WT + '/tools/icon3d'
os.makedirs(PREV, exist_ok=True)


# ─── util ────────────────────────────────────────────────────────────────
def lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


_MATS = {}


def mat(nama, rgb, emit=0.0, rough=0.8):
    key = (nama, rgb, emit)
    if key in _MATS:
        return _MATS[key]
    m = bpy.data.materials.new(nama)
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    col = (lin(rgb[0]), lin(rgb[1]), lin(rgb[2]), 1.0)
    b.inputs['Base Color'].default_value = col
    b.inputs['Roughness'].default_value = rough
    if emit:
        b.inputs['Emission Color'].default_value = col
        b.inputs['Emission Strength'].default_value = emit
    m.diffuse_color = col
    _MATS[key] = m
    return m


def _fin(o, m, smooth=False):
    o.data.materials.clear()
    o.data.materials.append(m)
    if smooth:
        for p in o.data.polygons:
            p.use_smooth = True
    return o


def sph(loc, r, m, sc=(1, 1, 1), seg=12, ring=8, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=ring, radius=r, location=loc)
    o = bpy.context.active_object
    o.scale = sc
    o.rotation_euler = rot
    return _fin(o, m, smooth=True)


def ico(loc, r, m, sc=(1, 1, 1), sub=1, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc)
    o = bpy.context.active_object
    o.scale = sc
    o.rotation_euler = rot
    return _fin(o, m)


def cone(loc, r1, r2, d, m, rot=(0, 0, 0), v=8, sc=(1, 1, 1)):
    bpy.ops.mesh.primitive_cone_add(vertices=v, radius1=r1, radius2=r2, depth=d, location=loc)
    o = bpy.context.active_object
    o.rotation_euler = rot
    o.scale = sc
    return _fin(o, m)


def cyl(loc, r, d, m, rot=(0, 0, 0), v=10, sc=(1, 1, 1)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=v, radius=r, depth=d, location=loc)
    o = bpy.context.active_object
    o.rotation_euler = rot
    o.scale = sc
    return _fin(o, m, smooth=True)


def box(loc, s, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.scale = s
    o.rotation_euler = rot
    return _fin(o, m)


def tabung(titik, r, m, v=8):
    """Silinder dari titik a ke b (untuk lengan, jari, usus, ekor)."""
    out = []
    for a, b in zip(titik, titik[1:]):
        a, b = mathutils.Vector(a), mathutils.Vector(b)
        d = b - a
        bpy.ops.mesh.primitive_cylinder_add(vertices=v, radius=r, depth=d.length,
                                            location=(a + b) / 2)
        o = bpy.context.active_object
        o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
        out.append(_fin(o, m, smooth=True))
        sph(tuple(b), r, m, seg=8, ring=6)
    return out


def sayap(akar, ujung_jari, m_kulit, m_tulang):
    """Membran sayap: segitiga-segitiga dari akar ke tiap ujung jari."""
    verts = [akar] + list(ujung_jari)
    faces = [(0, i, i + 1) for i in range(1, len(verts) - 1)]
    me = bpy.data.meshes.new('membran')
    me.from_pydata(verts, [], faces)
    me.update()
    o = bpy.data.objects.new('membran', me)
    bpy.context.collection.objects.link(o)
    sol = o.modifiers.new('tebal', 'SOLIDIFY')
    sol.thickness = 0.02
    _fin(o, m_kulit)
    for j in ujung_jari:
        tabung([akar, j], 0.012, m_tulang, v=6)


def bersihkan():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for d in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for x in list(d):
            if x.users == 0:
                d.remove(x)
    _MATS.clear()


# ─── palet (sRGB) ──────────────────────────────────────────────────────────
MATA_MERAH = (232, 64, 40)
TARING = (236, 226, 204)


# ─── 1. KELELAWAR ──────────────────────────────────────────────────────────
def kelelawar():
    kulit = mat('KB_Kulit', (70, 56, 66))
    bulu = mat('KB_Bulu', (92, 74, 70))
    membran = mat('KB_Membran', (112, 80, 92))
    tulang = mat('KB_Tulang', (60, 46, 54))
    mata = mat('KB_Mata', MATA_MERAH, emit=2.0)
    gigi = mat('KB_Taring', TARING)
    # badan menggantung, sedikit membungkuk
    sph((0, 0, 0.0), 0.16, bulu, sc=(1.0, 0.9, 1.25))
    sph((0, -0.02, 0.24), 0.13, bulu, sc=(1.05, 1.0, 0.95))          # kepala
    for sx in (-1, 1):
        cone((sx * 0.08, 0.0, 0.40), 0.065, 0.0, 0.2, kulit,
             rot=(0, sx * math.radians(18), 0))                        # telinga
        sph((sx * 0.05, -0.115, 0.27), 0.024, mata, seg=8, ring=6)
        cone((sx * 0.025, -0.125, 0.19), 0.012, 0.0, 0.05, gigi,
             rot=(math.radians(180), 0, 0), v=5)                       # taring
        # sayap: akar di bahu, empat jari menyebar
        akar = (sx * 0.12, 0.0, 0.08)
        jari = [(sx * 0.42, 0.04, 0.34), (sx * 0.66, 0.06, 0.20),
                (sx * 0.70, 0.06, -0.04), (sx * 0.52, 0.04, -0.22),
                (sx * 0.20, 0.02, -0.20)]
        sayap(akar, jari, membran, tulang)
        tabung([(sx * 0.06, 0, -0.16), (sx * 0.07, -0.02, -0.28)], 0.018, kulit, v=6)  # kaki
    sph((0, -0.12, 0.22), 0.04, kulit, sc=(1.2, 0.8, 0.8))             # moncong
    return 1.4


# ─── 2. TIKUS GUA ─────────────────────────────────────────────────────────
def tikus_gua():
    bulu = mat('TG_Bulu', (104, 94, 86))
    perut = mat('TG_Perut', (150, 136, 122))
    pink = mat('TG_Kulit', (198, 140, 140))
    mata = mat('TG_Mata', MATA_MERAH, emit=1.5)
    gigi = mat('TG_Gigi', (232, 210, 150))
    gelap = mat('TG_Kumis', (40, 34, 32))
    sph((0, 0.05, 0.30), 0.30, bulu, sc=(0.95, 1.35, 0.9))             # badan gemuk
    sph((0, -0.08, 0.26), 0.2, perut, sc=(0.9, 1.0, 0.8))
    sph((0, -0.38, 0.40), 0.18, bulu, sc=(0.9, 1.2, 0.9))              # kepala
    cone((0, -0.58, 0.37), 0.11, 0.02, 0.2, bulu, rot=(math.radians(90), 0, 0))  # moncong
    sph((0, -0.68, 0.37), 0.035, pink, seg=8, ring=6)                  # hidung
    for sx in (-1, 1):
        sph((sx * 0.13, -0.32, 0.58), 0.09, pink, sc=(1, 0.35, 1.1))   # telinga
        sph((sx * 0.08, -0.52, 0.46), 0.03, mata, seg=8, ring=6)
        for k in (-1, 0, 1):
            tabung([(sx * 0.05, -0.62, 0.36), (sx * 0.24, -0.66, 0.36 + k * 0.05)], 0.004, gelap, v=4)
        for y in (-0.22, 0.25):                                        # kaki
            tabung([(sx * 0.17, y, 0.14), (sx * 0.19, y - 0.04, 0.02)], 0.04, pink, v=6)
    box((0, -0.66, 0.30), (0.05, 0.02, 0.06), gigi)                    # gigi seri
    tabung([(0, 0.42, 0.24), (0, 0.72, 0.12), (0.12, 0.98, 0.06), (0.30, 1.12, 0.05)], 0.03, pink, v=6)
    return 0.8


# ─── 3. GENDERUWO ─────────────────────────────────────────────────────────
def genderuwo():
    bulu = mat('GW_Bulu', (58, 48, 42))
    bulu2 = mat('GW_BuluUjung', (82, 68, 56))
    kulit = mat('GW_Kulit', (96, 72, 62))
    mata = mat('GW_Mata', MATA_MERAH, emit=3.0)
    gigi = mat('GW_Taring', TARING)
    cakar = mat('GW_Cakar', (40, 34, 30))
    # badan raksasa membungkuk ke depan
    sph((0, 0.02, 1.35), 0.62, bulu, sc=(1.0, 0.8, 1.05))              # dada
    sph((0, 0.08, 0.86), 0.5, bulu, sc=(0.95, 0.8, 0.8))               # perut
    sph((0, -0.18, 2.02), 0.34, bulu, sc=(1.0, 0.95, 0.95))            # kepala menjorok
    sph((0, -0.40, 1.92), 0.2, kulit, sc=(1.1, 0.7, 0.8))              # muka
    for sx in (-1, 1):
        sph((sx * 0.11, -0.50, 2.02), 0.05, mata, seg=8, ring=6)
        cone((sx * 0.07, -0.55, 1.80), 0.03, 0.0, 0.12, gigi, rot=(0, 0, 0), v=5)  # taring naik
        cone((sx * 0.22, -0.05, 2.32), 0.08, 0.0, 0.22, bulu2, rot=(math.radians(-15), sx * math.radians(25), 0))
        # bahu, lengan panjang sampai lutut
        sph((sx * 0.6, 0, 1.62), 0.26, bulu)
        tabung([(sx * 0.66, -0.02, 1.55), (sx * 0.86, -0.12, 0.95), (sx * 0.82, -0.25, 0.45)], 0.16, bulu)
        sph((sx * 0.82, -0.28, 0.36), 0.15, kulit, sc=(1, 1, 0.8))      # kepalan
        for k in (-1, 0, 1):
            cone((sx * (0.82 + k * 0.06), -0.40, 0.30), 0.025, 0.0, 0.1, cakar,
                 rot=(math.radians(110), 0, 0), v=5)
        # kaki pendek kekar
        tabung([(sx * 0.28, 0.08, 0.62), (sx * 0.34, 0.0, 0.18)], 0.2, bulu)
        sph((sx * 0.36, -0.08, 0.08), 0.18, kulit, sc=(1, 1.4, 0.55))
    # gumpalan bulu acak di punggung dan bahu (siluet kasar)
    import random
    rnd = random.Random(7)
    for _ in range(26):
        a = rnd.uniform(0, math.tau)
        z = rnd.uniform(0.8, 2.0)
        r = 0.55 - abs(z - 1.4) * 0.25
        cone((math.cos(a) * r, 0.2 + abs(math.sin(a)) * r * 0.6, z), 0.09, 0.0,
             rnd.uniform(0.18, 0.32), bulu2,
             rot=(math.radians(rnd.uniform(-60, 60)), math.radians(rnd.uniform(-60, 60)), a), v=5)
    return 2.6


# ─── 4. BANASPATI ─────────────────────────────────────────────────────────
def banaspati():
    inti = mat('BP_Inti', (255, 236, 170), emit=4.0)
    api1 = mat('BP_Api', (255, 168, 60), emit=3.0)
    api2 = mat('BP_ApiLuar', (230, 92, 40), emit=2.0)
    tengkorak = mat('BP_Tengkorak', (70, 40, 30))
    mata = mat('BP_Mata', (40, 20, 16))
    tangan = mat('BP_Tangan', (120, 60, 40))
    ico((0, 0, 0.95), 0.42, inti, sub=2)
    # lidah api berlapis, condong ke atas-belakang
    import random
    rnd = random.Random(3)
    for lapis, (m, r0, n) in enumerate(((api1, 0.46, 12), (api2, 0.55, 14))):
        for i in range(n):
            a = i * math.tau / n + lapis * 0.2
            h = rnd.uniform(0.5, 0.95) + lapis * 0.15
            cone((math.cos(a) * r0 * 0.7, math.sin(a) * r0 * 0.7 + 0.08, 1.05 + h * 0.3),
                 0.16 - lapis * 0.02, 0.0, h, m,
                 rot=(math.radians(-10 + math.sin(a) * 18), math.radians(math.cos(a) * 22), 0), v=6)
    # wajah tengkorak di depan bola api
    sph((0, -0.36, 0.98), 0.2, tengkorak, sc=(1.0, 0.45, 1.05))
    for sx in (-1, 1):
        sph((sx * 0.08, -0.45, 1.03), 0.055, mata, seg=8, ring=6)
        # tangan yang dipakai berjalan (legenda: banaspati berjalan dengan tangan)
        tabung([(sx * 0.3, -0.15, 0.62), (sx * 0.42, -0.25, 0.25), (sx * 0.45, -0.32, 0.04)], 0.06, tangan)
        for k in (-1, 0, 1):
            tabung([(sx * 0.45, -0.32, 0.04), (sx * (0.45 + k * 0.06), -0.46, 0.02)], 0.022, tangan, v=6)
    box((0, -0.47, 0.88), (0.14, 0.02, 0.05), mata)                    # mulut
    return 2.0


# ─── 5. KUNTILANAK ────────────────────────────────────────────────────────
def kuntilanak():
    gaun = mat('KN_Gaun', (226, 220, 204))
    gaun2 = mat('KN_GaunBayang', (190, 184, 170))
    rambut = mat('KN_Rambut', (22, 20, 24))
    kulit = mat('KN_Kulit', (214, 206, 196))
    kuku = mat('KN_Kuku', (60, 50, 46))
    mata = mat('KN_Mata', (240, 70, 50), emit=2.0)
    # gaun panjang melebar, ujungnya robek (kerucut-kerucut)
    cone((0, 0, 0.9), 0.55, 0.2, 1.3, gaun, v=12)
    cyl((0, 0, 1.68), 0.2, 0.36, gaun)                                 # badan atas
    for i in range(12):
        a = i * math.tau / 12
        cone((math.cos(a) * 0.5, math.sin(a) * 0.5, 0.18), 0.09, 0.0, 0.28, gaun2,
             rot=(math.radians(180), 0, 0), v=5)
    sph((0, 0, 2.02), 0.17, kulit, sc=(0.92, 0.95, 1.1))              # kepala
    # rambut panjang menutup muka dan punggung sampai pinggang
    sph((0, 0.02, 2.08), 0.2, rambut, sc=(1.0, 1.0, 1.0))
    box((0, -0.06, 1.6), (0.32, 0.12, 0.85), rambut)
    box((0, 0.10, 1.45), (0.4, 0.1, 1.1), rambut)
    sph((0.04, -0.14, 2.0), 0.022, mata, seg=8, ring=6)                # satu mata mengintip
    for sx in (-1, 1):
        # lengan terjulur ke depan, jari panjang berkuku
        tabung([(sx * 0.22, 0, 1.78), (sx * 0.28, -0.3, 1.58), (sx * 0.24, -0.62, 1.5)], 0.05, gaun)
        sph((sx * 0.24, -0.66, 1.5), 0.055, kulit, seg=8, ring=6)
        for k in (-1, 0, 1):
            tabung([(sx * 0.24, -0.68, 1.5), (sx * (0.24 + k * 0.035), -0.84, 1.44)], 0.012, kulit, v=5)
            cone((sx * (0.24 + k * 0.035), -0.88, 1.43), 0.012, 0.0, 0.06, kuku,
                 rot=(math.radians(90), 0, 0), v=4)
    return 2.2


# ─── 6. LEAK ──────────────────────────────────────────────────────────────
def leak():
    kulit = mat('LK_Kulit', (176, 120, 96))
    rambut = mat('LK_Rambut', (36, 30, 30))
    mata_p = mat('LK_MataPutih', (240, 232, 214))
    mata = mat('LK_Pupil', (200, 40, 30), emit=2.5)
    lidah = mat('LK_Lidah', (196, 60, 70))
    usus = mat('LK_Usus', (176, 84, 92))
    jantung = mat('LK_Jantung', (150, 40, 50))
    gigi = mat('LK_Taring', TARING)
    sph((0, 0, 1.55), 0.3, kulit, sc=(1.0, 0.95, 1.05))               # kepala melayang
    # rambut liar mengembang
    import random
    rnd = random.Random(11)
    for _ in range(22):
        a = rnd.uniform(0, math.tau)
        el = rnd.uniform(-0.2, 1.2)
        d = mathutils.Vector((math.cos(a) * math.cos(el), math.sin(a) * math.cos(el) + 0.15, math.sin(el)))
        p = mathutils.Vector((0, 0, 1.6)) + d * 0.26
        cone(tuple(p + d * 0.16), 0.07, 0.0, 0.38, rambut,
             rot=d.to_track_quat('Z', 'Y').to_euler(), v=5)
    for sx in (-1, 1):
        sph((sx * 0.11, -0.25, 1.62), 0.075, mata_p, seg=10, ring=8)   # mata melotot
        sph((sx * 0.11, -0.32, 1.62), 0.035, mata, seg=8, ring=6)
        cone((sx * 0.1, -0.28, 1.4), 0.03, 0.0, 0.14, gigi,
             rot=(math.radians(180), 0, 0), v=5)                       # taring turun
    # lidah panjang menjulur
    tabung([(0, -0.26, 1.42), (0, -0.34, 1.2), (0.03, -0.32, 0.98)], 0.045, lidah)
    # isi perut terjuntai di bawah kepala
    sph((0.0, 0.02, 1.18), 0.1, jantung, sc=(1, 0.9, 1.2))
    for k, sx in enumerate((-0.12, 0.0, 0.12)):
        tabung([(sx, 0.02, 1.25), (sx * 1.4, 0.06, 0.95), (sx * 0.7, -0.02, 0.7),
                (sx * 1.6, 0.05, 0.45 - k * 0.05)], 0.035, usus)
    return 1.9


# ─── 7. POCONG ────────────────────────────────────────────────────────────
def pocong():
    kafan = mat('PC_Kafan', (222, 216, 200))
    bayang = mat('PC_Lipatan', (184, 176, 160))
    tali = mat('PC_Tali', (150, 136, 110))
    muka = mat('PC_Muka', (120, 128, 112))
    mata = mat('PC_Mata', (20, 18, 18))
    # tubuh terbungkus: kapsul memanjang, menyempit di kaki
    sph((0, 0, 1.05), 0.34, kafan, sc=(1.0, 0.85, 2.6), seg=14, ring=10)
    sph((0, 0, 1.92), 0.24, kafan, sc=(1.0, 1.0, 1.15))               # kepala
    # lipatan kain melingkar
    for z in (0.5, 0.85, 1.25, 1.55):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.33 - abs(z - 1.05) * 0.18,
                                         minor_radius=0.018, location=(0, 0, z))
        _fin(bpy.context.active_object, bayang)
    # ikatan di leher, ubun-ubun (dua "telinga" kain), dan pergelangan kaki
    for z, r in ((1.68, 0.2), (0.22, 0.17)):
        bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.03, location=(0, 0, z))
        _fin(bpy.context.active_object, tali)
    cone((0, 0, 2.2), 0.08, 0.03, 0.14, tali)
    for sx in (-1, 1):
        cone((sx * 0.07, 0, 2.34), 0.06, 0.0, 0.2, kafan, rot=(0, sx * math.radians(35), 0), v=6)
        sph((sx * 0.07, -0.205, 1.94), 0.03, mata, seg=8, ring=6)
    sph((0, -0.17, 1.9), 0.13, muka, sc=(0.9, 0.4, 1.1))               # muka kelabu mengintip
    cone((0, 0, 0.06), 0.16, 0.12, 0.12, tali)                          # ujung kaki terikat
    return 2.4


MOBS = {
    'kelelawar': kelelawar, 'tikus_gua': tikus_gua, 'genderuwo': genderuwo,
    'banaspati': banaspati, 'kuntilanak': kuntilanak, 'leak': leak, 'pocong': pocong,
}


def export(nama):
    bpy.ops.object.select_all(action='DESELECT')
    for o in bpy.context.scene.objects:
        if o.type == 'MESH':
            o.select_set(True)
            bpy.context.view_layer.objects.active = o
    for o in bpy.context.selected_objects:
        for md in list(o.modifiers):
            bpy.context.view_layer.objects.active = o
            bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.ops.object.join()
    o = bpy.context.active_object
    o.name = f'mob_{nama}'
    # Transform DITERAPKAN dulu: objek hasil join mewarisi rotasi bagian
    # terakhir yang dibuat (kerucut lidah, ekor), dan menimpanya mengacak
    # orientasi tiap model berbeda-beda.
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    # Lalu diputar 180 derajat terhadap sumbu tegak: dengan sumbu export ini
    # model menghadap +Z game, dan kamera default memandang ke +Z -- terukur,
    # yang terlihat punggungnya.
    o.rotation_euler = (0, 0, math.pi)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    path = f'{MDIR}/mob_{nama}.obj'
    bpy.ops.wm.obj_export(filepath=path, export_selected_objects=True,
                          up_axis='Y', forward_axis='NEGATIVE_Z',
                          export_materials=True, export_uv=True, export_normals=True)
    return path, len(o.data.polygons)


def preview_semua(path):
    """Jajarkan semua monster dan render satu lembar berwarna."""
    bersihkan()
    x = 0.0
    tinggi = {}
    for nama, fn in MOBS.items():
        sebelum = set(bpy.context.scene.objects)
        h = fn()
        baru = [o for o in bpy.context.scene.objects if o not in sebelum]
        lebar = 1.2 if nama in ('tikus_gua',) else (1.8 if nama in ('kelelawar', 'genderuwo') else 1.3)
        for o in baru:
            o.location.x += x + lebar / 2
            if nama == 'kelelawar':
                o.location.z += 1.4
        tinggi[nama] = h
        x += lebar + 0.3
    sc = bpy.context.scene
    bpy.ops.mesh.primitive_plane_add(size=60, location=(x / 2, 0, 0))
    _fin(bpy.context.active_object, mat('lantai', (54, 50, 52)))
    cam_d = bpy.data.cameras.new('cam')
    cam = bpy.data.objects.new('cam', cam_d)
    sc.collection.objects.link(cam)
    cam_d.lens = 35
    target = mathutils.Vector((x / 2, 0, 1.15))
    cam.location = target + mathutils.Vector((0, -x * 0.95, 1.6))
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    for e, rot, en in (((4, -6, 8), (0.9, 0.2, 0.4), 3.2), ((-6, 4, 5), (1.1, -0.6, 2.4), 1.0)):
        ld = bpy.data.lights.new('sun', 'SUN')
        ld.energy = en
        lo = bpy.data.objects.new('sun', ld)
        lo.rotation_euler = rot
        sc.collection.objects.link(lo)
    if sc.world is None:
        sc.world = bpy.data.worlds.new('w')
    sc.world.use_nodes = True
    bg = sc.world.node_tree.nodes.get('Background')
    bg.inputs[0].default_value = (0.05, 0.05, 0.06, 1)
    bg.inputs[1].default_value = 0.6
    sc.render.engine = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE_NEXT'
    sc.render.resolution_x, sc.render.resolution_y = 2000, 640
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return tinggi


hasil = {}
for nama, fn in MOBS.items():
    bersihkan()
    fn()
    hasil[nama] = export(nama)
hasil['_preview'] = preview_semua(PREV + '/mob_gua_baru.png')
print('HASIL', hasil)
