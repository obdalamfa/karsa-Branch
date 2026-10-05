"""blender_topi.py — Topi dan hiasan kepala sebagai mesh sungguhan.

Topi primitif runtime (tumpukan silinder/kerucut/bola) terbaca kasar. Di sini
tiap topi dimodel dari profil yang diputar (spin) dan dideformasi: caping
beranyam, koboi bertepi melengkung dan bermahkota berlekuk, topi bajak laut
dengan tepi terlipat ke tiga sisi, dan seterusnya.

KONVENSI (dipakai game/rupa_pemain.pasang_aksesori):
  - satuan: JARI-JARI KEPALA = 1.0
  - alas topi (tempat ia bertemu kepala) di z = 0, mahkota ke +Z
  - depan = -Y Blender (setelah export: -Z), sama dengan wajah rig
Export OBJ+MTL Y-atas ke assets/models/topi/<jenis>.obj.

    python tools/blender_topi.py
"""
import math
import os

try:
    import bpy
    import bmesh
except ImportError:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from blender_rpc import run
    print(run(f"exec(open(r'{os.path.abspath(__file__)}', encoding='utf-8').read())"))
    raise SystemExit

WT = r'E:/Game Research/Lembah Karsa 3D/.claude/worktrees/coba-play-game-d5f058'
OUT = WT + '/assets/models/topi'
PREV = WT + '/tools/icon3d/topi_baru.png'
os.makedirs(OUT, exist_ok=True)


def lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


_M = {}


def mat(nama, rgb):
    if nama in _M:
        return _M[nama]
    m = bpy.data.materials.new(nama)
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (lin(rgb[0]), lin(rgb[1]), lin(rgb[2]), 1)
    b.inputs['Roughness'].default_value = 0.8
    m.diffuse_color = (lin(rgb[0]), lin(rgb[1]), lin(rgb[2]), 1)
    _M[nama] = m
    return m


def bersihkan():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for d in (bpy.data.meshes, bpy.data.materials):
        for x in list(d):
            if x.users == 0:
                d.remove(x)
    _M.clear()


def objek(nama, bm, mats):
    me = bpy.data.meshes.new(nama)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    for p in me.polygons:
        p.use_smooth = True
    o = bpy.data.objects.new(nama, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def putar(profil, seg=40, mat_baris=None, deform=None):
    """Mesh dari profil (r, z) yang diputar 360 derajat.

    mat_baris(i) -> indeks material untuk pita ke-i (anyaman bergaris).
    deform(x, y, z, a, r) -> (x, y, z) untuk melengkungkan tepi dll.
    """
    bm = bmesh.new()
    cincin = []
    for (r, z) in profil:
        baris = []
        for k in range(seg):
            a = k / seg * math.tau
            x, y = math.cos(a) * r, math.sin(a) * r
            zz = z
            if deform is not None:
                x, y, zz = deform(x, y, z, a, r)
            baris.append(bm.verts.new((x, y, zz)))
        cincin.append(baris)
    for i in range(len(cincin) - 1):
        for k in range(seg):
            f = bm.faces.new((cincin[i][k], cincin[i][(k + 1) % seg],
                              cincin[i + 1][(k + 1) % seg], cincin[i + 1][k]))
            if mat_baris is not None:
                f.material_index = mat_baris(i)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def bola(nama, pusat, skala, m, seg=16):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=1.0)
    for v in bm.verts:
        v.co.x = v.co.x * skala[0] + pusat[0]
        v.co.y = v.co.y * skala[1] + pusat[1]
        v.co.z = v.co.z * skala[2] + pusat[2]
    return objek(nama, bm, [m])


def tabung(nama, a, b, r, m, seg=10):
    import mathutils
    a, b = mathutils.Vector(a), mathutils.Vector(b)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=(b - a).length)
    rot = (b - a).to_track_quat('Z', 'Y').to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=mathutils.Matrix.Translation((a + b) / 2) @ rot, verts=bm.verts)
    return objek(nama, bm, [m])


# ─── topi ──────────────────────────────────────────────────────────────────
def caping():
    anyam1, anyam2 = mat('anyam_terang', (206, 176, 112)), mat('anyam_gelap', (176, 146, 88))
    tepi = mat('caping_tepi', (132, 100, 60))
    # profil sedikit cekung: caping asli melandai lalu melengkung di tepinya
    prof = [(0.0, 0.92), (0.18, 0.86), (0.5, 0.7), (0.9, 0.5), (1.3, 0.32),
            (1.7, 0.18), (2.1, 0.08), (2.45, 0.02), (2.7, -0.02)]
    objek('caping', putar(prof, 48, lambda i: i % 2), [anyam1, anyam2])
    objek('caping_tepi', putar([(2.66, -0.0), (2.74, -0.05), (2.7, -0.08), (2.62, -0.03)], 48), [tepi])
    # pucuk
    bola('caping_pucuk', (0, 0, 0.92), (0.12, 0.12, 0.08), tepi)


def koboi():
    kulit, pita = mat('koboi', (112, 78, 52)), mat('koboi_pita', (46, 32, 24))

    def lengkung(x, y, z, a, r):
        # tepi naik di kiri-kanan, sedikit turun di depan-belakang
        if r > 1.05:
            t = (r - 1.05) / 1.0
            z += 0.38 * (t ** 2) * abs(math.cos(a)) ** 1.5 - 0.06 * t * abs(math.sin(a))
        return x, y * 0.9, z
    objek('koboi_tepi', putar([(1.0, 0.0), (1.4, 0.0), (1.8, 0.01), (2.05, 0.03), (2.1, 0.05),
                               (2.05, 0.06), (1.4, 0.04), (1.0, 0.04)], 48, deform=lengkung), [kulit])

    def lekuk(x, y, z, a, r):
        # mahkota berlekuk di atas (pinch depan) + lonjong
        if z > 0.8:
            z -= 0.16 * (1 - r) * 1.2
        if z > 0.7 and y < 0:
            x *= 0.82
        return x, y * 0.86, z
    objek('koboi_mahkota', putar([(1.0, 0.0), (1.0, 0.45), (0.95, 0.85), (0.8, 0.98), (0.5, 0.96),
                                  (0.0, 0.88)], 32, deform=lekuk), [kulit])
    objek('koboi_pita', putar([(1.02, 0.04), (1.02, 0.22)], 32,
                              deform=lambda x, y, z, a, r: (x, y * 0.86, z)), [pita])


def bucket(rgb=(98, 104, 70), nama='bucket'):
    kain = mat(nama, rgb)
    jahit = mat(nama + '_jahit', tuple(int(c * 0.7) for c in rgb))
    objek(nama, putar([(1.04, 0.0), (1.02, 0.5), (0.85, 0.7), (0.4, 0.78), (0.0, 0.79)], 32), [kain])
    objek(nama + '_tepi', putar([(1.04, 0.02), (1.35, -0.12), (1.65, -0.28), (1.7, -0.31),
                                 (1.66, -0.28), (1.04, -0.02)], 32), [kain])
    for z in (0.12, 0.24, 0.36):
        objek(nama + '_garis', putar([(1.035, z), (1.035, z + 0.02)], 32), [jahit])


def peci():
    beludru = mat('peci', (30, 30, 34))
    jahit = mat('peci_jahit', (70, 60, 48))
    def lonjong(x, y, z, a, r):
        return x, y * 0.88, z
    objek('peci', putar([(1.06, 0.0), (1.05, 0.12), (1.0, 0.5), (0.97, 0.6), (0.85, 0.66),
                         (0.0, 0.66)], 36, deform=lonjong), [beludru])
    objek('peci_jahit', putar([(1.065, 0.0), (1.065, 0.035)], 36, deform=lonjong), [jahit])


def bajak_laut():
    hitam = mat('bajak_hitam', (26, 24, 28))
    emas = mat('bajak_emas', (196, 160, 70))
    putih = mat('bajak_tulang', (236, 232, 220))
    objek('bajak_mahkota', putar([(1.08, 0.0), (1.06, 0.4), (0.95, 0.68), (0.6, 0.8), (0.0, 0.82)], 32), [hitam])

    def lipat(x, y, z, a, r):
        # tepi terlipat naik ke tiga sisi: tiga sudut runcing (depan & dua
        # belakang-samping) tetap rendah, di antaranya naik setinggi mahkota.
        if r > 1.08:
            t = min(1.0, (r - 1.08) / 0.85)
            naik = 0.5 + 0.5 * math.cos(3 * (a + math.pi / 2))
            z += 0.72 * t * (1 - naik) ** 0.8
        return x, y, z
    objek('bajak_tepi', putar([(1.08, 0.0), (1.4, 0.0), (1.75, 0.0), (1.95, 0.0), (1.95, 0.04),
                               (1.75, 0.04), (1.4, 0.04), (1.08, 0.04)], 72, deform=lipat), [hitam])
    objek('bajak_pita', putar([(1.09, 0.05), (1.09, 0.13)], 32), [emas])
    # tengkorak + tulang bersilang di depan mahkota
    bola('bajak_tengkorak', (0, -1.07, 0.42), (0.17, 0.05, 0.15), putih)
    bola('bajak_rahang', (0, -1.06, 0.3), (0.1, 0.04, 0.06), putih)
    for s in (-1, 1):
        tabung('bajak_tulang', (-0.24 * s, -1.06, 0.2), (0.24 * s, -1.06, 0.48), 0.025, putih, 8)
        bola('bajak_mata', (s * 0.06, -1.115, 0.43), (0.04, 0.02, 0.04), hitam)


def baret():
    kain = mat('baret', (150, 52, 60))
    def miring(x, y, z, a, r):
        return x + z * 0.25, y, z
    objek('baret', putar([(1.0, 0.0), (1.12, 0.06), (1.3, 0.16), (1.28, 0.26), (1.0, 0.33),
                          (0.5, 0.36), (0.0, 0.37)], 36, deform=miring), [kain])
    tabung('baret_tangkai', (0.08, 0, 0.36), (0.1, 0, 0.46), 0.04, kain, 8)


def bandana(rgb=(170, 44, 40)):
    kain = mat('bandana', rgb)
    titik = mat('bandana_titik', (236, 226, 210))
    objek('bandana', putar([(1.05, -0.05), (1.06, 0.2), (0.95, 0.5), (0.65, 0.72), (0.0, 0.8)], 32), [kain])
    # simpul dan dua ekor di belakang
    bola('bandana_simpul', (0, 1.02, 0.12), (0.16, 0.1, 0.12), kain)
    for s in (-1, 1):
        tabung('bandana_ekor', (s * 0.05, 1.05, 0.1), (s * 0.22, 1.25, -0.35), 0.07, kain, 6)
    for k in range(8):
        a = k / 8 * math.tau
        bola('bandana_motif', (math.cos(a) * 0.98, math.sin(a) * 0.98, 0.32), (0.05, 0.05, 0.05), titik, 8)


def mahkota():
    emas = mat('mahkota_emas', (214, 172, 72))
    permata = mat('mahkota_permata', (60, 150, 140))
    objek('mahkota_pita', putar([(1.06, 0.0), (1.06, 0.28), (1.0, 0.28), (1.0, 0.0)], 40), [emas])
    for k in range(10):
        a = k / 10 * math.tau
        x, y = math.cos(a) * 1.03, math.sin(a) * 1.03
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.15, radius2=0.0, depth=0.42)
        bmesh.ops.translate(bm, vec=(x, y, 0.28 + 0.21), verts=bm.verts)
        objek('mahkota_runcing', bm, [emas])
        bola('mahkota_permata', (x * 1.02, y * 1.02, 0.14), (0.06, 0.06, 0.06), permata, 8)


def mahkota_bunga():
    daun = mat('bunga_daun', (96, 140, 84))
    kelopak = [mat('bunga_kuning', (240, 214, 120)), mat('bunga_merah_muda', (226, 140, 170)),
               mat('bunga_putih', (244, 240, 230))]
    objek('rangkai', putar([(1.0, 0.04), (1.07, 0.1), (1.0, 0.16), (0.93, 0.1)], 40), [daun])
    for k in range(9):
        a = k / 9 * math.tau
        x, y = math.cos(a) * 1.0, math.sin(a) * 1.0
        m = kelopak[k % 3]
        for j in range(5):
            b = j / 5 * math.tau
            bola('kelopak', (x + math.cos(b) * 0.07, y + math.sin(b) * 0.07, 0.17), (0.06, 0.06, 0.03), m, 8)
        bola('putik', (x, y, 0.19), (0.035, 0.035, 0.03), mat('putik', (226, 170, 60)), 8)


def pita():
    m = mat('pita', (222, 92, 120))
    for s in (-1, 1):
        bm = bmesh.new()
        v = [bm.verts.new(p) for p in ((0, 0.6, 0.02), (s * 0.55, 0.6, 0.3), (s * 0.55, 0.6, -0.22))]
        bm.faces.new(v)
        objek('pita_sayap', bm, [m]).modifiers.new('t', 'SOLIDIFY').thickness = 0.06
    bola('pita_simpul', (0, 0.6, 0.04), (0.1, 0.08, 0.1), m)


def ikat():
    m = mat('ikat', (150, 70, 52))
    objek('ikat', putar([(1.06, 0.0), (1.07, 0.18), (1.0, 0.18), (0.99, 0.0)], 36), [m])
    bola('ikat_simpul', (0.75, 0.75, 0.09), (0.12, 0.12, 0.1), m)
    for s in (0.1, -0.1):
        tabung('ikat_ekor', (0.8, 0.8, 0.08), (1.05 + s, 1.0, -0.3), 0.05, m, 6)


TOPI = {
    'caping': caping, 'koboi': koboi, 'bucket': bucket, 'peci': peci,
    'bajak_laut': bajak_laut, 'baret': baret, 'bandana': bandana,
    'mahkota': mahkota, 'mahkota_bunga': mahkota_bunga, 'pita': pita, 'ikat': ikat,
}


def ekspor(nama):
    for o in bpy.context.scene.objects:
        for md in list(o.modifiers):
            bpy.context.view_layer.objects.active = o
            bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.ops.object.select_all(action='DESELECT')
    for o in bpy.context.scene.objects:
        if o.type == 'MESH':
            o.select_set(True)
    bpy.ops.wm.obj_export(filepath=f'{OUT}/{nama}.obj', export_selected_objects=True,
                          up_axis='Y', forward_axis='NEGATIVE_Z', export_materials=True,
                          export_uv=False, export_normals=True)


def pratinjau():
    import mathutils
    bersihkan()
    for i, (nama, fn) in enumerate(TOPI.items()):
        sebelum = set(bpy.context.scene.objects)
        fn()
        for o in [o for o in bpy.context.scene.objects if o not in sebelum]:
            o.location.x += (i % 6) * 6.0
            o.location.y += (i // 6) * 6.0
        # kepala acuan (bola jari-jari 1) supaya terlihat cara topi duduk
        bola('kepala', ((i % 6) * 6.0, (i // 6) * 6.0, -0.35), (1, 1, 1.15), mat('kulit', (196, 146, 104)))
    sc = bpy.context.scene
    cam_d = bpy.data.cameras.new('cam'); cam = bpy.data.objects.new('cam', cam_d)
    sc.collection.objects.link(cam); cam_d.lens = 40
    t = mathutils.Vector((15, 3, 0.2))
    cam.location = t + mathutils.Vector((0, -30, 13))
    cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    ld = bpy.data.lights.new('sun', 'SUN'); ld.energy = 3.5
    lo = bpy.data.objects.new('sun', ld); lo.rotation_euler = (0.8, 0.2, 0.5); sc.collection.objects.link(lo)
    if sc.world is None:
        sc.world = bpy.data.worlds.new('w')
    sc.world.use_nodes = True
    bg = sc.world.node_tree.nodes.get('Background')
    bg.inputs[0].default_value = (0.25, 0.24, 0.24, 1); bg.inputs[1].default_value = 0.8
    sc.render.resolution_x, sc.render.resolution_y = 1800, 760
    sc.render.filepath = PREV
    bpy.ops.render.render(write_still=True)


hasil = []
for nama, fn in TOPI.items():
    bersihkan()
    fn()
    ekspor(nama)
    hasil.append(nama)
pratinjau()
print('HASIL', hasil)
