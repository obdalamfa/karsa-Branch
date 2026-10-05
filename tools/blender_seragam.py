"""blender_seragam.py — Seragam profesi untuk 15 karakter ter-rig.

Semua warga memakai pakaian TSO acak sehingga tidak satu pun terbaca dari
pekerjaannya. Di sini tiap rig di characters_vitaboy.blend diberi aksesori
yang langsung menyebut perannya (caping petani, jas dokter + stetoskop, topi
koboi pandai besi, ...), lalu diekspor ulang ke assets/models/actors/.

Aksesori di-skin ke satu tulang dengan bobot 1 (bukan parent tulang: Actor
Panda tidak menggerakkan anak sendi), transformnya dipanggang ke verteks
(glTF mengabaikan transform objek mesh ber-skin), dan rig dikembalikan ke
titik nol sebelum ekspor (posisi jajaran di .blend dulu ikut terekspor dan
menggeser warga sampai 12 m dari tempatnya).

    python tools/blender_seragam.py            # semua
    LK_SERAGAM=npc_raka python tools/blender_seragam.py   # satu (lewat env Blender)
"""
import math
import os

try:
    import bpy
    import mathutils
except ImportError:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from blender_rpc import run
    BLEND_LUAR = r'E:/Game Research/Lembah Karsa 3D/.claude/worktrees/coba-play-game-d5f058/assets/blend/characters_vitaboy.blend'
    nama = sys.argv[1:] or [None]
    for n in nama:
        # Satu karakter per panggilan: ekspor glTF yang panjang memutus socket.
        run("import bpy; bpy.ops.wm.open_mainfile(filepath=r'%s')" % BLEND_LUAR)
        run("import os; os.environ['LK_SERAGAM']=%r" % (n or ''))
        print(run(f"exec(open(r'{os.path.abspath(__file__)}', encoding='utf-8').read())"))
    run("import os; os.environ.pop('LK_SERAGAM', None)")
    raise SystemExit

import sys as _sys
WT = r'E:/Game Research/Lembah Karsa 3D/.claude/worktrees/coba-play-game-d5f058'
_sys.path.insert(0, WT + '/tools')
from blender_walk_cycle import buat_siklus_jalan  # noqa: E402

TEX_DIR = WT + '/assets/blend/tex'
OUT_DIR = WT + '/assets/models/actors'
assert 'npc_ningsih_rig' in bpy.data.objects, 'buka characters_vitaboy.blend dulu'

for img in bpy.data.images:
    p = os.path.join(TEX_DIR, os.path.basename(img.filepath))
    if os.path.exists(p):
        img.filepath = p
        img.reload()


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
    b.inputs['Base Color'].default_value = (lin(rgb[0]), lin(rgb[1]), lin(rgb[2]), 1.0)
    b.inputs['Roughness'].default_value = 0.75
    _M[nama] = m
    return m


def _aktif():
    return bpy.context.view_layer.objects.active


def kerucut(loc, r1, r2, d, m, rot=(0, 0, 0), v=16, sc=(1, 1, 1)):
    bpy.ops.mesh.primitive_cone_add(vertices=v, radius1=r1, radius2=r2, depth=d, location=loc)
    o = _aktif(); o.rotation_euler = rot; o.scale = sc; o.data.materials.append(m)
    return o


def silinder(loc, r, d, m, rot=(0, 0, 0), v=16, sc=(1, 1, 1)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=v, radius=r, depth=d, location=loc)
    o = _aktif(); o.rotation_euler = rot; o.scale = sc; o.data.materials.append(m)
    return o


def bola(loc, r, m, sc=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=14, ring_count=8, radius=r, location=loc)
    o = _aktif(); o.scale = sc; o.data.materials.append(m)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def torus(loc, R, r, m, rot=(0, 0, 0), sc=(1, 1, 1)):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=loc,
                                     major_segments=20, minor_segments=8)
    o = _aktif(); o.rotation_euler = rot; o.scale = sc; o.data.materials.append(m)
    return o


def kotak(loc, s, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = _aktif(); o.scale = s; o.rotation_euler = rot; o.data.materials.append(m)
    return o


def tempel(obj, rig, tulang):
    bpy.context.view_layer.update()
    obj.data.transform(obj.matrix_world)
    obj.parent = rig
    obj.parent_type = 'OBJECT'
    obj.matrix_world = mathutils.Matrix.Identity(4)
    vg = obj.vertex_groups.new(name=tulang)
    vg.add(list(range(len(obj.data.vertices))), 1.0, 'REPLACE')
    md = obj.modifiers.new('rig', 'ARMATURE')
    md.object = rig


def ukur_kepala(rig):
    """Puncak kepala, pusat kepala, dan lebar kepala di ruang rig (rig di 0)."""
    kepala = [o for o in bpy.data.objects if o.parent == rig and o.name.endswith('_head')]
    pts = []
    for o in kepala:
        pts += [o.matrix_world @ v.co for v in o.data.vertices]
    zs = [p.z for p in pts]
    xs = [p.x for p in pts]
    ys = [p.y for p in pts]
    top = max(zs)
    tinggi = top - min(zs)
    pusat = mathutils.Vector(((max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, top - tinggi * 0.45))
    lebar = max(xs) - min(xs)
    return top, pusat, lebar


def badan(rig):
    b = rig.data.bones
    leher = b['NECK'].head_local.z
    dada = b['SPINE2'].head_local.z
    pinggul = b['PELVIS'].head_local.z
    return leher, dada, pinggul


# ─── kosakata aksesori ─────────────────────────────────────────────────────
def caping(rig, skala=1.0):
    top, c, w = ukur_kepala(rig)
    o = kerucut((c.x, c.y, top - 0.02 * skala), 0.34 * skala, 0.02, 0.17 * skala,
                mat('caping', (204, 176, 112)), v=20)
    tempel(o, rig, 'HEAD')
    o = torus((c.x, c.y, top - 0.08 * skala), 0.33 * skala, 0.012, mat('caping_tepi', (150, 120, 70)))
    tempel(o, rig, 'HEAD')


def topi_koboi(rig):
    top, c, w = ukur_kepala(rig)
    coklat = mat('koboi', (110, 76, 50))
    o = silinder((c.x, c.y, top - 0.03), 0.23, 0.02, coklat, sc=(1, 0.85, 1))
    tempel(o, rig, 'HEAD')
    o = silinder((c.x, c.y, top + 0.04), 0.11, 0.13, coklat, sc=(1, 0.8, 1))
    tempel(o, rig, 'HEAD')
    o = torus((c.x, c.y, top - 0.0), 0.125, 0.015, mat('pita_koboi', (40, 30, 26)), sc=(1, 0.8, 1))
    tempel(o, rig, 'HEAD')


def _verts_dunia(o):
    return [(o.matrix_world @ v.co) for v in o.data.vertices]


def celemek(rig, rgb, nama, pinggang=False):
    """Celemek yang MENGIKUTI badan, bukan papan.

    Kotak datar di depan dada terbaca sebagai papan nama. Di sini lembarannya
    dibangun dari profil depan badan sendiri: tiap baris ketinggian mengambil
    titik paling depan badan pada irisan itu, lalu melengkung ke belakang di
    kedua sisi. Di bawah pinggul lembaran jatuh lurus (kain menggantung, tidak
    mengikuti dua kaki). Baris di atas pinggul ikut SPINE1, di bawahnya PELVIS.
    """
    leher, dada, pinggul = badan(rig)
    tubuh = [o for o in bpy.data.objects if o.parent == rig and o.name.endswith('_body')]
    pts = []
    for o in tubuh:
        pts += _verts_dunia(o)
    if pinggang:
        z_atas, z_bawah, hw = pinggul + 0.06, pinggul - 0.52, 0.17
    else:
        z_atas, z_bawah, hw = dada + 0.12, pinggul - 0.42, 0.2
    BARIS, KOLOM = 12, 9
    verts, faces, grup = [], [], []
    y_gantung = None
    for r in range(BARIS + 1):
        z = z_atas + (z_bawah - z_atas) * r / BARIS
        if z >= pinggul - 0.04:
            irisan = [p.y for p in pts if abs(p.z - z) < 0.035 and abs(p.x) < hw + 0.04]
            yf = (min(irisan) if irisan else -0.12) - 0.022
            y_gantung = yf
        else:
            # menggantung: lurus dari pinggul, sedikit mengembang ke bawah
            yf = y_gantung - (pinggul - 0.04 - z) * 0.06
        for c in range(KOLOM):
            t = -1 + 2 * c / (KOLOM - 1)
            x = t * hw
            verts.append((x, yf + 0.07 * t * t, z))
            grup.append('SPINE1' if z >= pinggul else 'PELVIS')
    n = len(verts)
    # tebal: lapis belakang, normal terbalik, supaya terlihat dari dua sisi
    verts += [(x, y + 0.008, z) for x, y, z in verts]
    grup += grup
    for r in range(BARIS):
        for c in range(KOLOM - 1):
            a = r * KOLOM + c
            faces.append((a, a + 1, a + KOLOM + 1, a + KOLOM))
            faces.append((n + a, n + a + KOLOM, n + a + KOLOM + 1, n + a + 1))
    me = bpy.data.meshes.new(nama)
    me.from_pydata(verts, [], faces)
    me.update()
    o = bpy.data.objects.new(nama, me)
    bpy.context.scene.collection.objects.link(o)
    me.materials.append(mat(nama, rgb))
    o.parent = rig
    for tl in set(grup):
        vg = o.vertex_groups.new(name=tl)
        vg.add([k for k, g in enumerate(grup) if g == tl], 1.0, 'REPLACE')
    md = o.modifiers.new('rig', 'ARMATURE')
    md.object = rig
    # tali di leher untuk celemek dada
    if not pinggang:
        t = torus((0, -0.02, leher - 0.04), 0.1, 0.008, mat(nama + '_tali', (60, 42, 30)),
                  rot=(math.radians(60), 0, 0))
        tempel(t, rig, 'SPINE2')


def celup_baju(rig, warna, nama_baru):
    """Baju dicelup satu warna (luma dipertahankan supaya lipatan tetap ada)."""
    for o in [o for o in bpy.data.objects if o.parent == rig and o.name.endswith('_body')]:
        for slot in o.material_slots:
            m = slot.material.copy()
            slot.material = m
            for n in m.node_tree.nodes:
                if n.type == 'TEX_IMAGE' and n.image is not None:
                    src = n.image
                    px = list(src.pixels)
                    # Piksel gambar disimpan sRGB apa adanya: warna celup TIDAK
                    # dilinearkan, kalau tidak hasilnya lebih gelap dan bergeser
                    # merah (kunyit keluar sebagai bata).
                    w = [c / 255.0 for c in warna]
                    for i in range(0, len(px), 4):
                        r, g, b = px[i], px[i + 1], px[i + 2]
                        # piksel kulit (merah > hijau > biru, cukup jenuh) dibiarkan
                        if r > g * 1.15 and g > b * 1.05 and r - b > 0.06:
                            continue
                        l = 0.299 * r + 0.587 * g + 0.114 * b
                        k = min(1.0, 0.55 + l * 0.9)
                        px[i], px[i + 1], px[i + 2] = w[0] * k, w[1] * k, w[2] * k
                    img = src.copy()
                    img.name = nama_baru
                    img.pixels = px
                    img.filepath_raw = os.path.join(TEX_DIR, nama_baru + '.png')
                    img.file_format = 'PNG'
                    img.save()
                    n.image = img


def jas_dokter(rig):
    leher, dada, pinggul = badan(rig)
    # Jas putih = baju sendiri dicelup putih. Kerucut jas yang dibungkuskan
    # ke badan terbaca sebagai papan datar di depan dada.
    celup_baju(rig, (236, 236, 230), 'raka_jas_dokter')
    # stetoskop melingkar di leher, kepala stetoskop di dada
    o = torus((0, -0.03, leher - 0.06), 0.11, 0.011, mat('stetoskop', (40, 44, 52)),
              rot=(math.radians(70), 0, 0))
    tempel(o, rig, 'SPINE2')
    o = silinder((0.06, -0.16, dada - 0.06), 0.03, 0.015, mat('stetoskop_kepala', (190, 194, 200)),
                 rot=(math.radians(90), 0, 0))
    tempel(o, rig, 'SPINE2')


def baret(rig, rgb=(150, 52, 60)):
    top, c, w = ukur_kepala(rig)
    o = bola((c.x + 0.03, c.y, top - 0.02), 0.13, mat('baret', rgb), sc=(1.15, 1.1, 0.42))
    tempel(o, rig, 'HEAD')


def peci(rig):
    top, c, w = ukur_kepala(rig)
    o = silinder((c.x, c.y, top - 0.03), w * 0.52, 0.1, mat('peci', (30, 30, 34)), sc=(1, 0.85, 1))
    tempel(o, rig, 'HEAD')


def kacamata(rig):
    top, c, w = ukur_kepala(rig)
    m = mat('kacamata', (50, 40, 34))
    for s in (-1, 1):
        o = torus((c.x + s * 0.045, c.y - w * 0.5, c.z + 0.02), 0.03, 0.006, m, rot=(math.radians(90), 0, 0))
        tempel(o, rig, 'HEAD')


def kerudung(rig, rgb):
    """Kerudung = salinan mesh kepala, wajah dibuang, didorong sedikit keluar.

    Bola yang dibungkuskan ke kepala terbaca sebagai helm. Salinan kepala
    sendiri pas di bentuk kepala itu, ber-skin ke tulang yang sama, jadi ikut
    tiap gerak kepala. Rambut dihapus: kerudung menutupinya.
    """
    import bmesh
    top, c, w = ukur_kepala(rig)
    for o in [o for o in bpy.data.objects if o.parent == rig and o.name.endswith('_hair')]:
        bpy.data.objects.remove(o, do_unlink=True)
    kepala = max((o for o in bpy.data.objects if o.parent == rig and '_head' in o.name),
                 key=lambda o: len(o.data.vertices))
    k = kepala.copy()
    k.data = kepala.data.copy()
    k.name = 'kerudung'
    bpy.context.scene.collection.objects.link(k)
    bm = bmesh.new()
    bm.from_mesh(k.data)
    mw = kepala.matrix_world
    mwi = mw.inverted()
    pusat_l = mwi @ c
    dagu = min((mw @ v.co).z for v in bm.verts)
    alis = c.z + 0.035
    buang = []
    for v in bm.verts:
        p = mw @ v.co
        arah = (p - c).normalized()
        # Normal mesh kepala TSO menghadap ke DALAM, jadi wajah dan arah dorong
        # dihitung dari pusat kepala, bukan dari normal verteks.
        if arah.y < -0.3 and dagu - 0.01 < p.z < alis:
            buang.append(v)
    bmesh.ops.delete(bm, geom=buang, context='VERTS')
    for v in bm.verts:
        v.co = pusat_l + (v.co - pusat_l) * 1.0 + (v.co - pusat_l).normalized() * 0.024
    bm.to_mesh(k.data)
    bm.free()
    k.data.materials.clear()
    k.data.materials.append(mat('kerudung', rgb))
    # kain jatuh ke bahu: kerucut lebar di bawah kepala
    o = kerucut((c.x, c.y + 0.01, dagu - 0.02), w * 0.95, w * 0.55, 0.12,
                mat('kerudung', rgb), v=18)
    tempel(o, rig, 'NECK')


def topi_rimba(rig, rgb=(98, 104, 70)):
    """Topi bucket: mahkota bulat rendah + tepi melandai ke bawah."""
    top, c, w = ukur_kepala(rig)
    m = mat('topi_rimba', rgb)
    o = kerucut((c.x, c.y, top - 0.02), w * 0.62, w * 0.55, 0.11, m, v=20)
    tempel(o, rig, 'HEAD')
    o = bola((c.x, c.y, top + 0.03), w * 0.55, m, sc=(1, 1, 0.35))
    tempel(o, rig, 'HEAD')
    o = kerucut((c.x, c.y, top - 0.09), w * 1.05, w * 0.6, 0.06, m, v=20)
    tempel(o, rig, 'HEAD')
    o = torus((c.x, c.y, top - 0.055), w * 0.6, 0.012, mat('topi_rimba_pita', (60, 50, 36)))
    tempel(o, rig, 'HEAD')


def topi_pemburu(rig):
    topi_rimba(rig, (120, 84, 50))
    top, c, w = ukur_kepala(rig)
    o = kerucut((c.x + 0.12, c.y + 0.04, top + 0.1), 0.02, 0.0, 0.22, mat('bulu_topi', (180, 50, 40)),
                rot=(0, math.radians(-30), 0), v=6)
    tempel(o, rig, 'HEAD')


def tricorn(rig):
    top, c, w = ukur_kepala(rig)
    hitam = mat('tricorn', (28, 26, 30))
    o = kerucut((c.x, c.y, top - 0.01), 0.22, 0.12, 0.11, hitam, v=3, rot=(0, 0, math.radians(90)))
    tempel(o, rig, 'HEAD')
    o = torus((c.x, c.y, top - 0.055), 0.115, 0.01, mat('tricorn_emas', (196, 160, 70)))
    tempel(o, rig, 'HEAD')
    o = kotak((c.x - 0.05, c.y - w * 0.52, c.z + 0.03), (0.06, 0.01, 0.05), hitam)   # penutup mata
    tempel(o, rig, 'HEAD')


def bandana(rig, rgb=(170, 44, 40)):
    top, c, w = ukur_kepala(rig)
    o = bola((c.x, c.y, c.z + 0.05), w * 0.6, mat('bandana', rgb), sc=(1, 1.05, 0.85))
    tempel(o, rig, 'HEAD')


def ganti_kepala(rig, sumber, uban=None):
    """Pakai kepala (dan rambut) rig lain, disesuaikan ke tulang HEAD rig ini.

    Tekstur kepala npc_mbok_jum ternyata bukan wajah: gambar 64x64 berisi dua
    bentuk putih di latar biru keabu -- di layar ia terbaca sebagai topeng.
    """
    rs = bpy.data.objects[sumber + '_rig']
    for o in [o for o in bpy.data.objects if o.parent == rig and ('_head' in o.name or '_hair' in o.name)]:
        bpy.data.objects.remove(o, do_unlink=True)
    geser = rig.data.bones['HEAD'].head_local - rs.data.bones['HEAD'].head_local
    for o in [o for o in bpy.data.objects if o.parent == rs and ('_head' in o.name or '_hair' in o.name)]:
        k = o.copy()
        k.data = o.data.copy()
        bpy.context.scene.collection.objects.link(k)
        # verteks ke ruang rig sumber, lalu digeser ke tinggi kepala rig ini
        m = rs.matrix_world.inverted() @ o.matrix_world
        k.data.transform(m)
        k.data.transform(mathutils.Matrix.Translation(geser))
        k.parent = rig
        k.matrix_world = rig.matrix_world.copy()
        k.name = o.name.replace(sumber, rig.name[:-4])
        for md in k.modifiers:
            if md.type == 'ARMATURE':
                md.object = rig
        if uban:
            for slot in k.material_slots:
                mm = slot.material.copy()
                slot.material = mm
                for n in mm.node_tree.nodes:
                    if n.type == 'TEX_IMAGE' and n.image is not None:
                        px = list(n.image.pixels)
                        for i in range(0, len(px), 4):
                            r, g, b = px[i], px[i + 1], px[i + 2]
                            l = 0.299 * r + 0.587 * g + 0.114 * b
                            # hanya RAMBUT: gelap dan nyaris tanpa warna. Kulit
                            # (merah > hijau > biru) dibiarkan, kalau tidak
                            # seluruh wajah ikut memutih.
                            if l < 0.3 and max(r, g, b) - min(r, g, b) < 0.07:
                                v = min(1.0, 0.55 + l * 1.2)
                                px[i], px[i + 1], px[i + 2] = v * 0.95, v * 0.94, v * 0.92
                        img = n.image.copy()
                        img.name = uban + '_' + n.image.name.split('.')[0]
                        img.pixels = px
                        img.filepath_raw = os.path.join(TEX_DIR, img.name + '.png')
                        img.file_format = 'PNG'
                        img.save()
                        n.image = img


def sanggul(rig):
    top, c, w = ukur_kepala(rig)
    o = bola((c.x, c.y + w * 0.55, c.z + 0.02), 0.08, mat('sanggul', (34, 30, 30)))
    tempel(o, rig, 'HEAD')
    leher, dada, pinggul = badan(rig)
    # selendang batik melintang dari bahu kanan ke pinggang kiri
    o = torus((0, 0.0, (dada + pinggul) / 2 + 0.08), 0.21, 0.04, mat('selendang_mbok', (140, 82, 52)),
              rot=(0, math.radians(-38), 0), sc=(1, 0.72, 1))
    tempel(o, rig, 'SPINE1')


def sarung_bahu(rig):
    leher, dada, pinggul = badan(rig)
    o = torus((0, 0.0, dada), 0.22, 0.045, mat('sarung_kotak', (70, 92, 120)),
              rot=(0, math.radians(35), 0), sc=(1, 0.75, 1))
    tempel(o, rig, 'SPINE2')


def pita(rig):
    top, c, w = ukur_kepala(rig)
    m = mat('pita', (222, 92, 120))
    for s in (-1, 1):
        o = kerucut((c.x + s * 0.06, c.y + 0.05, top - 0.02), 0.05, 0.0, 0.09, m,
                    rot=(0, s * math.radians(90), 0), v=4)
        tempel(o, rig, 'HEAD')


SERAGAM = {
    'player':          lambda r: caping(r),
    'npc_ningsih':     lambda r: caping(r),
    'npc_bowo':        lambda r: caping(r, 0.75),
    'npc_raka':        jas_dokter,
    'npc_budi':        lambda r: (topi_koboi(r), celemek(r, (96, 62, 40), 'celemek_kulit')),
    'npc_joko':        lambda r: topi_rimba(r),
    'npc_sari':        lambda r: (kerudung(r, (120, 150, 110)), celemek(r, (226, 214, 190), 'celemek_warung', pinggang=True)),
    'npc_maya':        lambda r: baret(r),
    'npc_pak_guru':    lambda r: peci(r),   # kacamata sudah ada di kepala TSO-nya (head.001)
    'npc_mbok_jum':    lambda r: (ganti_kepala(r, 'npc_sari', uban='mbok_jum_uban'), sanggul(r)),
    'npc_jaka_ronda':  lambda r: (peci(r), sarung_bahu(r)),
    'npc_kapten_kuro': tricorn,
    'npc_kru_kuro':    lambda r: bandana(r),
    'npc_arya':        topi_pemburu,
    'npc_cici':        pita,
}


def ekspor(nama):
    rig = bpy.data.objects[nama + '_rig']
    rig.location = (0, 0, 0)
    bpy.context.view_layer.update()
    SERAGAM[nama](rig)
    buat_siklus_jalan(rig)
    ad = rig.animation_data or rig.animation_data_create()
    for t in list(ad.nla_tracks):
        ad.nla_tracks.remove(t)
    for anim in ('idle', 'walk', 'hoe', 'swing', 'water'):
        act = bpy.data.actions.get(f'{nama}_rig_{anim}')
        if act is None:
            continue
        tr = ad.nla_tracks.new()
        tr.name = anim
        strip = tr.strips.new(anim, int(act.frame_range[0]), act)
        if hasattr(strip, 'action_slot') and act.slots:
            strip.action_slot = act.slots[0]
    ad.action = None
    bpy.ops.object.select_all(action='DESELECT')
    for o in [rig] + [o for o in bpy.data.objects if o.parent == rig]:
        o.hide_set(False)
        o.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.export_scene.gltf(
        filepath=os.path.join(OUT_DIR, nama + '.glb'), export_format='GLB',
        use_selection=True, export_apply=True, export_animations=True,
        export_animation_mode='NLA_TRACKS', export_force_sampling=True,
        export_skins=True, export_yup=True)
    return [t.name for t in ad.nla_tracks]


_HANYA = os.environ.get('LK_SERAGAM', '')
hasil = {}
for nama in SERAGAM:
    if _HANYA and _HANYA != nama:
        continue
    hasil[nama] = ekspor(nama)
print('HASIL', hasil)
