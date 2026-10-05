"""blender_swarga.py — Makhluk swarga sebagai karakter Vitaboy ter-rig.

Tiga warga swarga sebelumnya jatuh ke manekin voxel kotak tanpa wajah karena
tidak punya .glb di assets/models/actors/. Di sini masing-masing dibuat dari
rig Vitaboy yang sudah ada (29 tulang, tekstur kepala/badan asli TSO), lalu
dimodifikasi:

  petapa_srimana  dari pak_guru — DUDUK BERSILA di atas teratai, tangan di
                  lutut, jubah dicelup kunyit. Pose sila menjadi aksi 'idle'.
  bidadari        dari ningsih  — sayap peri di punggung (ikut tulang SPINE2),
                  pakaian dicelup lembayung. Kecil dan melayang diatur di
                  game/char_actor.py (_GAYA), bukan dipanggang ke rig.
  dewa_angin      dari raka     — mahkota emas (ikut tulang HEAD), selendang,
                  pakaian dicelup biru langit.

Jalankan (Blender terbuka dengan add-on MCP di port 9876):
    python tools/blender_swarga.py
"""
import math
import os

try:
    import bpy
    import mathutils
except ImportError:
    import sys
    BLEND_LUAR = r'E:/Game Research/Lembah Karsa 3D/.claude/worktrees/coba-play-game-d5f058/assets/blend/characters_vitaboy.blend'
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from blender_rpc import run
    # Dua panggilan: open_mainfile meninggalkan konteks tanpa objek aktif
    # sampai panggilan berikutnya, dan bpy.ops primitif membutuhkannya.
    run("import bpy; bpy.ops.wm.open_mainfile(filepath=r'%s')" % BLEND_LUAR)
    print(run(f"exec(open(r'{os.path.abspath(__file__)}', encoding='utf-8').read())"))
    raise SystemExit

WT = r'E:/Game Research/Lembah Karsa 3D/.claude/worktrees/coba-play-game-d5f058'
BLEND = WT + '/assets/blend/characters_vitaboy.blend'
TEX_DIR = WT + '/assets/blend/tex'
OUT_DIR = WT + '/assets/models/actors'
PREV = WT + '/tools/icon3d/swarga_baru.png'

assert 'npc_ningsih_rig' in bpy.data.objects, 'buka characters_vitaboy.blend dulu'

for img in bpy.data.images:
    p = os.path.join(TEX_DIR, os.path.basename(img.filepath))
    if os.path.exists(p):
        img.filepath = p
        img.reload()


def lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def mat_polos(nama, rgb, emit=0.0):
    m = bpy.data.materials.new(nama)
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    col = (lin(rgb[0]), lin(rgb[1]), lin(rgb[2]), 1.0)
    b.inputs['Base Color'].default_value = col
    b.inputs['Roughness'].default_value = 0.6
    if emit:
        b.inputs['Emission Color'].default_value = col
        b.inputs['Emission Strength'].default_value = emit
    return m


def gandakan(sumber, baru):
    """Salin rig + semua mesh anaknya, data mesh ikut disalin (bukan linked)."""
    rig = bpy.data.objects[sumber + '_rig']
    bagian = [o for o in bpy.data.objects if o.parent == rig]
    peta = {}
    for o in [rig] + bagian:
        c = o.copy()
        if o.data is not None:
            c.data = o.data.copy()
        c.animation_data_clear()
        bpy.context.scene.collection.objects.link(c)
        peta[o] = c
    rig2 = peta[rig]
    rig2.name = baru + '_rig'
    rig2.data.name = baru + '_rig'
    rig2.location = (0, 0, 0)          # posisi jajaran tidak boleh ikut terekspor
    for o, c in peta.items():
        if o is rig:
            continue
        c.parent = rig2
        c.name = o.name.replace(sumber, baru)
        for md in c.modifiers:
            if md.type == 'ARMATURE':
                md.object = rig2
    # salin aksi milik sumber dengan nama baru
    for a in list(bpy.data.actions):
        if a.name.startswith(sumber + '_rig_'):
            a2 = a.copy()
            a2.name = a.name.replace(sumber, baru)
    return rig2, [c for o, c in peta.items() if o is not rig]


def celup(parts, kata_kunci, warna, nama_baru):
    """Kalikan tekstur pakaian dengan satu warna dan simpan sebagai PNG baru.

    Warna dipanggang ke pikselnya (bukan faktor material) karena shader game
    hanya membaca tekstur x warna vertex, dan faktor glTF tidak sampai ke sana.
    """
    for o in parts:
        if kata_kunci not in o.name:
            continue
        for slot in o.material_slots:
            m = slot.material.copy()
            slot.material = m
            for n in m.node_tree.nodes:
                if n.type == 'TEX_IMAGE' and n.image is not None:
                    src = n.image
                    # Dibaca dari SUMBER: salinan gambar yang belum pernah
                    # dimuat tidak punya piksel, dan celupnya diam-diam tidak
                    # mengubah apa pun (jubah petapa tetap baju pak_guru).
                    px = list(src.pixels)
                    img = src.copy()
                    img.name = nama_baru
                    w = [c / 255.0 for c in warna]     # piksel sRGB: jangan dilinearkan
                    for i in range(0, len(px), 4):
                        r, g, b = px[i], px[i + 1], px[i + 2]
                        if r > g * 1.15 and g > b * 1.05 and r - b > 0.06:
                            continue                      # kulit dibiarkan
                        # luma mempertahankan lipatan kain, warna menggantikan hue
                        l = 0.299 * r + 0.587 * g + 0.114 * b
                        k = min(1.0, 0.55 + l * 0.9)
                        px[i], px[i + 1], px[i + 2] = w[0] * k, w[1] * k, w[2] * k
                    img.pixels = px
                    img.filepath_raw = os.path.join(TEX_DIR, nama_baru + '.png')
                    img.file_format = 'PNG'
                    img.save()
                    n.image = img


def tempel_tulang(obj, rig, tulang):
    """Aksesori ikut satu tulang lewat SKINNING, bukan parent tulang.

    Objek ber-parent tulang diekspor glTF sebagai simpul anak sendi, dan
    loader Actor Panda tidak menggerakkannya: sayap jatuh ke kaki sebagai
    piringan datar, mahkota hilang. Dibuat jadi mesh ber-skin dengan bobot 1
    ke satu tulang -- jalur yang sama dengan badan, jadi pasti ikut.
    """
    # Transform dipanggang ke verteks: glTF mengabaikan transform objek untuk
    # mesh ber-skin, jadi sayap yang diputar dan diangkat ke punggung jatuh
    # kembali ke titik asal sebagai piringan datar di kaki.
    bpy.context.view_layer.update()        # matrix_world basi sesudah .location diubah
    obj.data.transform(obj.matrix_world)
    obj.parent = rig
    obj.parent_type = 'OBJECT'
    obj.matrix_world = mathutils.Matrix.Identity(4)
    vg = obj.vertex_groups.new(name=tulang)
    vg.add(list(range(len(obj.data.vertices))), 1.0, 'REPLACE')
    md = obj.modifiers.new('rig', 'ARMATURE')
    md.object = rig


def mesh_dari(verts, faces, nama, m, tebal=0.0):
    me = bpy.data.meshes.new(nama)
    me.from_pydata(verts, [], faces)
    me.update()
    o = bpy.data.objects.new(nama, me)
    bpy.context.scene.collection.objects.link(o)
    me.materials.append(m)
    if tebal:
        md = o.modifiers.new('tebal', 'SOLIDIFY')
        md.thickness = tebal
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier=md.name)
    return o


# ─── PETAPA SRIMANA: duduk bersila di atas teratai ──────────────────────────
def petapa():
    rig, parts = gandakan('npc_pak_guru', 'npc_petapa_srimana')
    # kepala TSO pak_guru membawa kacamata sebagai mesh kedua; pertapa tidak
    # Kacamata pak_guru adalah mesh '_head' yang PENDEK (5,7 cm, 520 verteks);
    # kepalanya justru '_head.001'. Dipilih dari tinggi, bukan dari nama.
    def _tinggi(o):
        zs = [v.co.z for v in o.data.vertices]
        return max(zs) - min(zs)
    kepala_kepala = [o for o in parts if '_head' in o.name]
    kacamata = [min(kepala_kepala, key=_tinggi)] if len(kepala_kepala) > 1 else []
    parts = [o for o in parts if o not in kacamata]
    for o in kacamata:
        bpy.data.objects.remove(o, do_unlink=True)
    celup(parts, '_body', (232, 168, 60), 'petapa_jubah')
    # teratai: kelopak dua lapis + alas
    kelopak = mat_polos('teratai_kelopak', (232, 168, 186))
    kelopak2 = mat_polos('teratai_dalam', (246, 214, 222))
    daun = mat_polos('teratai_daun', (86, 128, 92))
    objs = []
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.55, depth=0.06, location=(0, 0, 0.03))
    o = bpy.context.active_object; o.data.materials.append(daun); objs.append(o)
    for lap, (n, r, tinggi, m) in enumerate(((10, 0.46, 0.22, kelopak), (8, 0.30, 0.26, kelopak2))):
        for i in range(n):
            a = i * math.tau / n + lap * 0.3
            bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6, radius=0.16,
                                                 location=(math.cos(a) * r, math.sin(a) * r, 0.1 + tinggi * 0.4))
            k = bpy.context.active_object
            k.scale = (0.55, 1.0, 0.35)
            k.rotation_euler = (math.radians(-35), 0, a + math.pi / 2)
            k.data.materials.append(m)
            objs.append(k)
    for o in objs:
        o.parent = rig
    # pose bersila sebagai aksi idle
    # Salinan aksi idle milik pak_guru sudah memakai nama ini; kalau dibiarkan
    # aksi sila dapat akhiran .001 dan yang terekspor tetap pose berdiri.
    lama = bpy.data.actions.get('npc_petapa_srimana_rig_idle')
    if lama is not None:
        bpy.data.actions.remove(lama)
    for jenis in ('walk', 'hoe', 'swing', 'water'):
        a = bpy.data.actions.get(f'npc_petapa_srimana_rig_{jenis}')
        if a is not None:
            bpy.data.actions.remove(a)       # petapa tidak berjalan atau bertani
    act = bpy.data.actions.new('npc_petapa_srimana_rig_idle')
    rig.animation_data_create()
    rig.animation_data.action = act
    pb = rig.pose.bones
    for b in pb:
        b.rotation_mode = 'XYZ'
        b.rotation_euler = (0, 0, 0)
        b.location = (0, 0, 0)
    tinggi_duduk = 0.30                          # pantat di atas kelopak
    # turunkan ROOT dari 0,93 ke tinggi duduk (sumbu lokal tulang = Y dunia-atas)
    # matrix_local ROOT ~ identitas: sumbu lokal Z = atas armatur.
    pb['ROOT'].location = (0, 0, -(0.93 - tinggi_duduk))
    for s, kaki in ((1, 'L'), (-1, 'R')):
        pb[f'{kaki}_LEG'].rotation_euler = (math.radians(-88), 0, math.radians(s * 38))
        pb[f'{kaki}_LEG1'].rotation_euler = (math.radians(150), 0, 0)
        pb[f'{kaki}_FOOT'].rotation_euler = (math.radians(-30), 0, 0)
        pb[f'{kaki}_ARM1'].rotation_euler = (math.radians(-10), 0, math.radians(s * -25))
        pb[f'{kaki}_ARM2'].rotation_euler = (math.radians(-55), 0, 0)
    pb['HEAD'].rotation_euler = (math.radians(6), 0, 0)
    for f, napas in ((1, 0.0), (40, 0.012), (80, 0.0)):
        pb['SPINE1'].rotation_euler = (math.radians(-napas * 80), 0, 0)
        for b in pb:
            b.keyframe_insert('rotation_euler', frame=f)
            b.keyframe_insert('location', frame=f)
    rig.animation_data.action = None
    return rig


# ─── BIDADARI: peri bersayap ────────────────────────────────────────────────
def bidadari():
    rig, parts = gandakan('npc_ningsih', 'npc_bidadari')
    celup(parts, '_body', (190, 156, 214), 'bidadari_kain')
    sayap_m = mat_polos('sayap_peri', (206, 232, 236), emit=0.4)
    urat = mat_polos('sayap_urat', (150, 196, 206))
    for s in (1, -1):
        # dua cuping per sisi: atas besar, bawah kecil, pipih di bidang X-Z
        for (panjang, lebar, naik, sudut) in ((0.62, 0.30, 0.14, 35), (0.42, 0.20, -0.12, -25)):
            n = 14
            verts = [(0, 0, 0)]
            for i in range(n + 1):
                t = i / n * math.pi
                x = math.sin(t) * panjang
                z = math.cos(t) * lebar + naik
                verts.append((s * x, 0, z))
            faces = [(0, i, i + 1) for i in range(1, n + 1)]
            w = mesh_dari(verts, faces, 'sayap', sayap_m, tebal=0.012)
            w.location = (s * 0.05, 0.12, 1.30)
            w.rotation_euler = (0, s * math.radians(-sudut * 0.4), s * math.radians(28))
            tempel_tulang(w, rig, 'SPINE2')
    # mahkota bunga kecil
    bpy.ops.mesh.primitive_torus_add(major_radius=0.12, minor_radius=0.025, location=(0, 0.01, 1.70))
    t = bpy.context.active_object
    t.data.materials.append(mat_polos('mahkota_bunga', (240, 214, 120)))
    tempel_tulang(t, rig, 'HEAD')
    return rig


# ─── DEWA ANGIN: mahkota dan selendang ──────────────────────────────────────
def dewa_angin():
    rig, parts = gandakan('npc_raka', 'npc_dewa_angin')
    celup(parts, '_body', (96, 150, 196), 'dewa_angin_kain')
    emas = mat_polos('emas_dewa', (214, 172, 72), emit=0.2)
    selendang = mat_polos('selendang_angin', (228, 236, 240))
    # mahkota bertingkat
    for i, (r, z, h) in enumerate(((0.13, 1.78, 0.08), (0.10, 1.86, 0.08), (0.06, 1.94, 0.1))):
        bpy.ops.mesh.primitive_cone_add(vertices=10, radius1=r, radius2=r * 0.7, depth=h, location=(0, 0.01, z))
        c = bpy.context.active_object
        c.data.materials.append(emas)
        tempel_tulang(c, rig, 'HEAD')
    # selendang melingkar di bahu, dua ujungnya terjuntai di punggung dan
    # tertiup ke samping -- penanda "angin" tanpa satu pun efek partikel
    bpy.ops.mesh.primitive_torus_add(major_radius=0.2, minor_radius=0.035, location=(0, 0.02, 1.42),
                                     major_segments=24, minor_segments=8)
    t = bpy.context.view_layer.objects.active
    t.scale = (1.0, 0.8, 0.55)
    t.data.materials.append(selendang)
    tempel_tulang(t, rig, 'SPINE2')
    for sx in (-1, 1):
        verts, faces = [], []
        titik = [(sx * 0.12, 0.14, 1.38), (sx * 0.2, 0.22, 1.18), (sx * 0.34, 0.3, 0.98), (sx * 0.5, 0.36, 0.84)]
        for i, (x, y, z) in enumerate(titik):
            verts += [(x - 0.05, y, z), (x + 0.05, y, z)]
            if i:
                a = 2 * (i - 1)
                faces.append((a, a + 1, a + 3, a + 2))
        e = mesh_dari(verts, faces, 'selendang_juntai', selendang, tebal=0.01)
        tempel_tulang(e, rig, 'SPINE2')
    return rig


def ekspor(rig, nama):
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
    anak = [o for o in bpy.data.objects if o.parent == rig]
    for o in [rig] + anak:
        o.hide_set(False)
        o.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.export_scene.gltf(
        filepath=os.path.join(OUT_DIR, nama + '.glb'), export_format='GLB',
        use_selection=True, export_apply=True, export_animations=True,
        export_animation_mode='NLA_TRACKS', export_force_sampling=True,
        export_skins=True, export_yup=True)
    return [t.name for t in ad.nla_tracks]


hasil = {}
_HANYA = os.environ.get('LK_SWARGA', '')
for fn, nama in ((petapa, 'npc_petapa_srimana'), (bidadari, 'npc_bidadari'),
                 (dewa_angin, 'npc_dewa_angin')):
    if _HANYA and _HANYA not in nama:
        continue
    r = fn()
    hasil[nama] = ekspor(r, nama)
print('HASIL', hasil)
