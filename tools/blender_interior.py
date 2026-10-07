"""blender_interior.py — Bangun set perabot interior di Blender, ekspor ke game.

Dijalankan headless, ATOMIK dalam satu proses (scene Blender lewat MCP sering
ter-reset di antara panggilan, jadi build lintas-panggilan tidak bisa
dipercaya):

    E:/blender/blender.exe -b --factory-startup --python tools/blender_interior.py
    ... -- --render        sekalian render lembar pratinjau

Hasil:
    assets/models/interior/<nama>.obj     satu berkas per perabot
    assets/models/interior/palette.png    satu tekstur palet bersama
    assets/blender/interior_furniture.blend   sumber, untuk disunting manual

## Kenapa palet, bukan material

Shader game (`game/smooth_shader.py`) hanya membaca `p3d_ColorScale` dan satu
tekstur -- ia tidak membaca Kd dari .mtl maupun warna vertex. Model multi-warna
yang diekspor dengan material biasa akan tampil PUTIH polos. Jadi setiap muka
diberi UV yang menunjuk ke tengah satu kotak warna di `palette.png`; game cukup
memasang tekstur itu. Pola yang sama dengan pagar (`meshes.fence_palette_texture`).

## Konvensi

- Satuan meter (1 ubin = 2 m). Jejak tiap perabot muat di dalam satu ubin
  kecuali yang memang dirancang menyambung (konter, meja panjang).
- Lantai di z=0, pusat jejak di x=y=0.
- MUKA DEPAN menghadap -Y Blender. Diekspor dengan up=Y, forward=-Z, sehingga
  di berkas OBJ muka depan menghadap +Z -- arah +ty di game (menjauhi dinding
  utara). Game memutar sesuai dinding tempat perabot bersandar.
"""
import math
import sys
from pathlib import Path

import bpy
import bmesh

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / 'assets' / 'models' / 'interior'
BLEND_OUT = ROOT / 'assets' / 'blender' / 'interior_furniture.blend'
OUT_DIR.mkdir(parents=True, exist_ok=True)
BLEND_OUT.parent.mkdir(parents=True, exist_ok=True)

# ─── PALET ───────────────────────────────────────────────────────────────────
# Muted ala Disco Elysium x Project Zomboid (lihat DESIGN_STANDARD): saturasi
# ditahan, kayu hangat, kain berdebu. Cahaya game masih menambah terang, jadi
# nilai di sini sengaja sedikit di bawah warna "aslinya".
PALETTE = {
    'kayu_gelap':   (86, 58, 40),
    'kayu':         (128, 88, 58),
    'kayu_muda':    (168, 128, 88),
    'kayu_merah':   (112, 56, 40),
    'kayu_lantai':  (150, 112, 74),
    'krem':         (214, 200, 172),
    'seprai':       (222, 218, 204),
    'kain_merah':   (148, 62, 52),
    'kain_teal':    (60, 104, 100),
    'kain_mustard': (188, 146, 66),
    'kain_biru':    (68, 86, 118),
    'kain_hijau':   (86, 112, 70),
    'besi_gelap':   (54, 56, 60),
    'besi':         (124, 128, 132),
    'kuningan':     (170, 136, 68),
    'kaca_tv':      (38, 54, 58),
    'layar':        (110, 150, 140),
    'bata':         (146, 80, 60),
    'bata_gelap':   (104, 58, 46),
    'batu':         (124, 118, 108),
    'batu_gelap':   (82, 78, 74),
    'bara':         (236, 118, 40),
    'api':          (252, 196, 92),
    'arang':        (34, 30, 30),
    'daun':         (76, 118, 60),
    'daun_gelap':   (50, 88, 48),
    'daun_muda':    (112, 148, 74),
    'gerabah':      (166, 90, 62),
    'keramik_biru': (80, 106, 136),
    'kertas':       (230, 224, 204),
    'cermin':       (148, 178, 186),
    'hitam':        (26, 24, 24),
    'merah_salib':  (176, 50, 44),
    'putih':        (232, 230, 222),
    'kanvas':       (228, 220, 196),
    'cat_kuning':   (220, 176, 60),
    'cat_biru':     (70, 110, 168),
    'cat_merah':    (184, 70, 56),
    'tanah':        (76, 56, 40),
    'kaca':         (164, 196, 200),
    'gorden':       (138, 70, 58),
    'karung':       (170, 146, 106),
    'buah_merah':   (178, 64, 48),
    'buah_kuning':  (214, 170, 64),
    'buah_hijau':   (118, 150, 64),
    'buku_1':       (128, 52, 44),
    'buku_2':       (56, 84, 110),
    'buku_3':       (156, 128, 60),
    'buku_4':       (74, 100, 70),
    'buku_5':       (110, 76, 100),
    'lampu':        (250, 222, 160),
}
SWATCH = 8                     # piksel per kotak warna
PAL_COLS = 16                  # 16 x 16 kotak = 128 px
PAL_SIZE = SWATCH * PAL_COLS
_KEYS = list(PALETTE)
assert len(_KEYS) <= PAL_COLS * PAL_COLS


def swatch_uv(key):
    """UV di TENGAH kotak warna -- aman dari luberan filtering/pembulatan."""
    i = _KEYS.index(key)
    cx, cy = i % PAL_COLS, i // PAL_COLS
    u = (cx * SWATCH + SWATCH / 2) / PAL_SIZE
    # Baris gambar 0 ada di ATAS; UV v=1 juga di atas.
    v = 1.0 - (cy * SWATCH + SWATCH / 2) / PAL_SIZE
    return u, v


def write_palette():
    img = bpy.data.images.new('interior_palette', PAL_SIZE, PAL_SIZE, alpha=False)
    px = [0.0] * (PAL_SIZE * PAL_SIZE * 4)
    for i, key in enumerate(_KEYS):
        r, g, b = (c / 255.0 for c in PALETTE[key])
        cx, cy = i % PAL_COLS, i // PAL_COLS
        for yy in range(SWATCH):
            # Blender menyimpan piksel dari BAWAH; balik supaya cocok swatch_uv.
            row = PAL_SIZE - 1 - (cy * SWATCH + yy)
            for xx in range(SWATCH):
                o = (row * PAL_SIZE + cx * SWATCH + xx) * 4
                px[o:o + 4] = (r, g, b, 1.0)
    img.pixels = px
    img.filepath_raw = str(OUT_DIR / 'palette.png')
    img.file_format = 'PNG'
    img.save()
    return img


# ─── MATERIAL (untuk pratinjau Blender & penanda warna) ──────────────────────
def mat(key):
    m = bpy.data.materials.get(key)
    if m is None:
        m = bpy.data.materials.new(key)
        r, g, b = (c / 255.0 for c in PALETTE[key])
        # Warna palet itu sRGB; Blender bekerja linear.
        lin = tuple(((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92
                    for c in (r, g, b))
        m.diffuse_color = (*lin, 1.0)
        m.use_nodes = True
        bsdf = m.node_tree.nodes.get('Principled BSDF')
        if bsdf:
            bsdf.inputs['Base Color'].default_value = (*lin, 1.0)
            bsdf.inputs['Roughness'].default_value = 0.8
            if key in ('api', 'bara', 'lampu', 'layar'):
                bsdf.inputs['Emission Color'].default_value = (*lin, 1.0)
                bsdf.inputs['Emission Strength'].default_value = 1.5
    return m


# ─── PRIMITIF ────────────────────────────────────────────────────────────────
_PARTS = []          # objek bagian dari perabot yang sedang dibangun


def _finish(obj, key, bevel):
    obj.data.materials.append(mat(key))
    if bevel > 0:
        md = obj.modifiers.new('bevel', 'BEVEL')
        md.width = bevel
        md.segments = 1
        md.limit_method = 'ANGLE'
    _PARTS.append(obj)
    return obj


def box(key, size, loc, rot=(0, 0, 0), bevel=0.012):
    """Balok. `loc` = pusat alas (z = dasar balok), bukan pusat volume."""
    sx, sy, sz = size
    x, y, z = loc
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z + sz / 2),
                                    rotation=rot)
    o = bpy.context.active_object
    o.scale = (sx, sy, sz)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return _finish(o, key, min(bevel, min(size) * 0.3))


def cyl(key, r, h, loc, verts=12, rot=(0, 0, 0), r2=None, bevel=0.0):
    """Silinder / kerucut terpancung. `loc` = pusat alas."""
    x, y, z = loc
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h,
                                            location=(0, 0, 0))
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2,
                                        depth=h, location=(0, 0, 0))
    o = bpy.context.active_object
    # Geser supaya alasnya di z=0 lokal, baru diputar dan dipindah.
    for v in o.data.vertices:
        v.co.z += h / 2
    o.rotation_euler = rot
    o.location = (x, y, z)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return _finish(o, key, bevel)


def ball(key, r, loc, seg=10, ring=6, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=ring, radius=r,
                                         location=loc)
    o = bpy.context.active_object
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return _finish(o, key, 0)


def leaf(key, length, width, loc, yaw, pitch):
    """Daun pipih berbentuk belah ketupat, ditanam di pangkalnya."""
    bm = bmesh.new()
    pts = [(0, 0, 0), (width / 2, length * 0.45, 0.02), (0, length, 0),
           (-width / 2, length * 0.45, 0.02)]
    # Dua sisi = dua set vertex (bmesh menolak muka kembar pada vertex yang
    # sama). Tanpa sisi belakang, daun hilang saat dilihat dari bawah.
    bm.faces.new([bm.verts.new(p) for p in pts])
    bm.faces.new([bm.verts.new((x, y, z - 0.004)) for x, y, z in reversed(pts)])
    me = bpy.data.meshes.new('leaf')
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new('leaf', me)
    bpy.context.collection.objects.link(o)
    o.rotation_euler = (pitch, 0, yaw)
    o.location = loc
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    o.select_set(False)
    return _finish(o, key, 0)


# ─── PERABOT ─────────────────────────────────────────────────────────────────
# Tiap fungsi membangun SATU perabot di origin, muka depan ke -Y.

def kasur():
    """Kasur ganda kayu jati: sandaran kepala di belakang (+Y)."""
    W, L = 1.62, 1.96
    y0 = -L / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            box('kayu_gelap', (0.09, 0.09, 0.28), (sx * (W / 2 - 0.05), sy * (L / 2 - 0.05), 0))
    box('kayu', (W, L, 0.12), (0, 0, 0.2))                       # rangka
    box('kayu', (W + 0.04, 0.08, 1.05), (0, L / 2 - 0.02, 0))    # sandaran kepala
    box('kayu_gelap', (W + 0.1, 0.12, 0.06), (0, L / 2 - 0.02, 1.05))
    for i in range(4):                                           # ukiran bilah
        box('kayu_gelap', (0.05, 0.02, 0.5),
            (-0.45 + i * 0.3, L / 2 - 0.07, 0.42))
    box('kayu', (W + 0.04, 0.07, 0.48), (0, y0 + 0.02, 0))       # papan kaki
    box('seprai', (W - 0.08, L - 0.14, 0.2), (0, 0.02, 0.32), bevel=0.05)
    # selimut terlipat menutupi dua pertiga kasur
    box('kain_teal', (W - 0.02, L * 0.6, 0.06), (0, y0 + L * 0.3 + 0.07, 0.5), bevel=0.03)
    box('kain_mustard', (W, 0.12, 0.08), (0, y0 + L * 0.6 + 0.04, 0.5), bevel=0.03)
    for sx in (-0.38, 0.38):                                      # bantal
        box('putih', (0.62, 0.38, 0.14), (sx, L / 2 - 0.32, 0.52), bevel=0.06)


def kasur_klinik():
    """Ranjang pasien besi, tirai pemisah di sisi kanan."""
    W, L = 1.0, 1.95
    for sx in (-1, 1):
        for sy in (-1, 1):
            cyl('besi', 0.025, 0.5, (sx * (W / 2 - 0.04), sy * (L / 2 - 0.04), 0), verts=8)
            cyl('besi_gelap', 0.04, 0.04, (sx * (W / 2 - 0.04), sy * (L / 2 - 0.04), 0), verts=8)
    box('besi', (W, L, 0.06), (0, 0, 0.45))
    box('besi', (W, 0.05, 0.55), (0, L / 2 - 0.03, 0.45))        # kepala
    box('besi', (W, 0.05, 0.3), (0, -L / 2 + 0.03, 0.45))        # kaki
    box('seprai', (W - 0.06, L - 0.1, 0.16), (0, 0, 0.51), bevel=0.04)
    box('kain_biru', (W - 0.02, L * 0.5, 0.05), (0, -L * 0.2, 0.66), bevel=0.02)
    box('putih', (0.6, 0.32, 0.12), (0, L / 2 - 0.28, 0.67), bevel=0.05)
    # tiang infus
    cyl('besi', 0.015, 1.7, (W / 2 + 0.25, L / 2 - 0.3, 0), verts=6)
    box('besi', (0.3, 0.02, 0.02), (W / 2 + 0.25, L / 2 - 0.3, 1.68))
    box('kaca', (0.1, 0.05, 0.18), (W / 2 + 0.36, L / 2 - 0.3, 1.45))


def kompor():
    """Kompor dapur: lemari bata berplester, tungku dua lubang, panci & wajan."""
    W, D = 1.7, 0.75
    box('krem', (W, D, 0.82), (0, 0, 0), bevel=0.02)
    box('bata', (W, 0.04, 0.82), (0, -D / 2 - 0.01, 0))
    for i in range(3):
        box('bata_gelap', (W, 0.045, 0.02), (0, -D / 2 - 0.012, 0.18 + i * 0.25))
    box('batu', (W + 0.06, D + 0.06, 0.08), (0, 0, 0.82))
    for sx in (-0.42, 0.42):
        cyl('arang', 0.2, 0.03, (sx, 0, 0.9), verts=12)
        cyl('bara', 0.13, 0.031, (sx, 0, 0.9), verts=10)
        box('hitam', (0.18, 0.05, 0.16), (sx, -D / 2 - 0.02, 0.4))      # lubang api
        box('bara', (0.12, 0.03, 0.08), (sx, -D / 2 - 0.03, 0.42))
    cyl('besi_gelap', 0.19, 0.24, (-0.42, 0, 0.93), verts=14)           # panci
    cyl('besi', 0.2, 0.03, (-0.42, 0, 1.17), verts=14)
    cyl('hitam', 0.03, 0.04, (-0.42, 0, 1.2), verts=6)
    cyl('besi_gelap', 0.26, 0.09, (0.42, 0, 0.93), verts=14, r2=0.16)  # wajan
    box('kayu_gelap', (0.04, 0.3, 0.03), (0.42, 0.38, 1.0))
    # rak bumbu kecil di dinding belakang
    box('kayu', (1.2, 0.18, 0.04), (0, D / 2 - 0.05, 1.45))
    for i, k in enumerate(('gerabah', 'keramik_biru', 'kuningan', 'gerabah', 'putih')):
        cyl(k, 0.06, 0.16, (-0.48 + i * 0.24, D / 2 - 0.05, 1.49), verts=8)


def meja(L=1.5):
    """Meja makan kayu dengan taplak dan mangkuk buah."""
    D, H = 1.05, 0.76
    for sx in (-1, 1):
        for sy in (-1, 1):
            box('kayu_gelap', (0.08, 0.08, H - 0.05), (sx * (L / 2 - 0.1), sy * (D / 2 - 0.1), 0))
    box('kayu', (L - 0.1, D - 0.1, 0.1), (0, 0, H - 0.15))       # apron
    box('kayu', (L, D, 0.05), (0, 0, H - 0.05), bevel=0.015)
    box('krem', (L * 0.7, 0.42, 0.006), (0, 0, H), bevel=0)      # taplak tengah
    box('kain_merah', (L * 0.7, 0.05, 0.007), (0, 0.19, H), bevel=0)
    box('kain_merah', (L * 0.7, 0.05, 0.007), (0, -0.19, H), bevel=0)
    cyl('keramik_biru', 0.17, 0.08, (0, 0, H), verts=12, r2=0.2)
    for i, k in enumerate(('buah_merah', 'buah_kuning', 'buah_hijau', 'buah_merah')):
        a = i * math.pi / 2
        ball(k, 0.06, (math.cos(a) * 0.07, math.sin(a) * 0.07, H + 0.11))
    if L > 2:
        for sx in (-L * 0.32, L * 0.32):
            cyl('putih', 0.12, 0.02, (sx, -0.2, H), verts=12)       # piring
            cyl('putih', 0.12, 0.02, (sx, 0.2, H), verts=12)
            cyl('kaca', 0.035, 0.11, (sx + 0.18, -0.2, H), verts=8)


def meja_panjang():
    meja(3.7)


def kursi():
    """Kursi kayu bersandaran rotan. Penduduk menghadap -Y (depan)."""
    S, H = 0.48, 0.46
    for sx in (-1, 1):
        for sy in (-1, 1):
            box('kayu_gelap', (0.05, 0.05, H), (sx * (S / 2 - 0.04), sy * (S / 2 - 0.04), 0))
    box('kayu', (S, S, 0.05), (0, 0, H), bevel=0.01)
    box('kain_mustard', (S - 0.06, S - 0.06, 0.04), (0, -0.01, H + 0.05), bevel=0.02)
    for sx in (-1, 1):
        box('kayu_gelap', (0.05, 0.05, 0.5), (sx * (S / 2 - 0.04), S / 2 - 0.04, H + 0.05))
    box('kayu', (S, 0.04, 0.12), (0, S / 2 - 0.04, H + 0.42))
    for i in range(3):
        box('kayu_muda', (0.04, 0.025, 0.32), (-0.12 + i * 0.12, S / 2 - 0.04, H + 0.1))
    box('kayu_gelap', (S - 0.08, 0.03, 0.03), (0, 0, 0.12))     # palang kaki


def tv():
    """TV tabung di atas bufet rendah, antena kelinci."""
    W = 1.4
    box('kayu', (W, 0.5, 0.5), (0, 0.05, 0), bevel=0.015)
    for sx in (-0.34, 0.34):
        box('kayu_gelap', (0.6, 0.02, 0.36), (sx, -0.21, 0.07))
        box('kuningan', (0.06, 0.02, 0.03), (sx + (0.22 if sx < 0 else -0.22), -0.225, 0.26))
    box('besi_gelap', (0.78, 0.55, 0.56), (0, 0.06, 0.5), bevel=0.05)
    box('kayu_gelap', (0.8, 0.04, 0.58), (0, -0.21, 0.49), bevel=0.02)
    box('kaca_tv', (0.56, 0.02, 0.42), (-0.06, -0.235, 0.57), bevel=0.04)
    box('layar', (0.48, 0.01, 0.34), (-0.06, -0.245, 0.61), bevel=0.03)
    for i in range(2):
        cyl('kuningan', 0.035, 0.03, (0.3, -0.24, 0.62 + i * 0.13), rot=(math.pi / 2, 0, 0), verts=8)
    cyl('besi_gelap', 0.05, 0.03, (0, 0.06, 1.06), verts=8)
    for a in (-0.45, 0.45):
        cyl('besi', 0.008, 0.45, (0, 0.06, 1.08), verts=5, rot=(0, a, 0))
    # vas bunga kecil di samping TV
    cyl('gerabah', 0.06, 0.18, (0.55, 0.05, 0.5), verts=8)
    for i in range(3):
        leaf('daun', 0.16, 0.06, (0.55, 0.05, 0.66), i * 2.1, -0.6)
        ball('buah_merah', 0.035, (0.55 + math.cos(i * 2.1) * 0.05, 0.05 + math.sin(i * 2.1) * 0.05, 0.8))


def rak_buku():
    """Rak buku tinggi, isi buku warna-warni berselang-seling."""
    W, D, H = 1.6, 0.42, 2.0
    box('kayu_gelap', (0.05, D, H), (-W / 2 + 0.025, 0, 0))
    box('kayu_gelap', (0.05, D, H), (W / 2 - 0.025, 0, 0))
    box('kayu_gelap', (W, 0.03, H), (0, D / 2 - 0.015, 0))
    box('kayu_gelap', (W + 0.06, D + 0.04, 0.05), (0, 0, H))
    keys = ['buku_1', 'buku_2', 'buku_3', 'buku_4', 'buku_5', 'kertas']
    n = 0
    for s in range(5):
        z = 0.05 + s * 0.4
        box('kayu', (W - 0.1, D - 0.03, 0.03), (0, -0.015, z))
        if s == 4:
            # rak teratas: guci dan bingkai foto, bukan buku
            cyl('gerabah', 0.08, 0.22, (-0.45, 0, z + 0.03), verts=10)
            box('kayu_merah', (0.22, 0.03, 0.28), (0.3, 0.08, z + 0.03), rot=(0.15, 0, 0))
            box('kertas', (0.16, 0.01, 0.2), (0.3, 0.06, z + 0.07), rot=(0.15, 0, 0))
            continue
        x = -W / 2 + 0.1
        while x < W / 2 - 0.16:
            w = 0.05 + ((n * 37) % 5) * 0.012
            h = 0.24 + ((n * 53) % 4) * 0.025
            tilt = 0.18 if n % 9 == 4 else 0.0
            box(keys[n % len(keys)], (w, 0.26, h), (x + w / 2, -0.03, z + 0.03),
                rot=(0, tilt, 0), bevel=0.006)
            x += w + 0.008
            n += 1
            if n % 7 == 6:
                x += 0.12            # celah: rak yang terisi penuh terlihat palsu


def lemari_cermin():
    """Lemari pakaian dua pintu, pintu kiri bercermin."""
    W, D, H = 1.3, 0.6, 2.05
    box('kayu', (W, D, H), (0, 0, 0.08), bevel=0.02)
    for sx in (-1, 1):
        box('kayu_gelap', (0.08, 0.08, 0.08), (sx * (W / 2 - 0.06), -D / 2 + 0.06, 0))
        box('kayu_gelap', (0.08, 0.08, 0.08), (sx * (W / 2 - 0.06), D / 2 - 0.06, 0))
    box('kayu_gelap', (W + 0.08, D + 0.06, 0.08), (0, 0, H + 0.08))
    box('kayu_muda', (W / 2 - 0.06, 0.03, H - 0.25), (-W / 4, -D / 2 - 0.005, 0.2))
    box('kayu_muda', (W / 2 - 0.06, 0.03, H - 0.25), (W / 4, -D / 2 - 0.005, 0.2))
    box('cermin', (W / 2 - 0.2, 0.01, H - 0.55), (-W / 4, -D / 2 - 0.02, 0.35), bevel=0.01)
    box('kayu_gelap', (0.03, 0.01, H - 0.55), (-W / 4 + 0.06, -D / 2 - 0.026, 0.35), bevel=0)
    for sx in (-0.05, 0.05):
        cyl('kuningan', 0.022, 0.05, (sx, -D / 2 - 0.02, 1.1), rot=(math.pi / 2, 0, 0), verts=8)
    # kotak topi di atas lemari
    box('kain_merah', (0.4, 0.35, 0.18), (0.25, 0, H + 0.16), bevel=0.02)


def tungku():
    """Perapian bata dengan cerobong sampai langit-langit dan api menyala."""
    W, D = 1.6, 0.7
    box('bata', (W, D, 1.0), (0, 0.05, 0), bevel=0.01)
    for i in range(5):
        box('bata_gelap', (W + 0.005, D + 0.005, 0.015), (0, 0.05, 0.18 + i * 0.18), bevel=0)
    box('hitam', (0.86, 0.1, 0.64), (0, -D / 2 + 0.06, 0.12))          # mulut
    box('batu', (W + 0.16, D + 0.12, 0.1), (0, 0.02, 1.0))             # rak atas
    box('bata', (1.1, 0.5, 1.7), (0, 0.15, 1.1))                       # cerobong
    for i in range(6):
        box('bata_gelap', (1.105, 0.505, 0.015), (0, 0.15, 1.3 + i * 0.25), bevel=0)
    box('batu_gelap', (W + 0.3, 0.6, 0.08), (0, -D / 2 - 0.12, 0))      # alas depan
    for i, a in enumerate((0.3, -0.3)):
        cyl('kayu_gelap', 0.07, 0.6, (-0.3, -0.12 + i * 0.12, 0.2), rot=(0, math.pi / 2, a))
    cyl('bara', 0.22, 0.05, (0, -0.1, 0.12), verts=10)
    for i, (dx, h) in enumerate(((0, 0.42), (-0.15, 0.3), (0.16, 0.32))):
        cyl('api' if i == 0 else 'bara', 0.12 - i * 0.02, h, (dx, -0.1, 0.17), verts=7, r2=0.0)
    # perkakas & jam kecil di atas
    box('kayu_merah', (0.3, 0.12, 0.22), (-0.5, 0.0, 1.1), bevel=0.02)
    cyl('kertas', 0.08, 0.02, (-0.5, -0.065, 1.21), rot=(math.pi / 2, 0, 0), verts=12)
    cyl('kuningan', 0.05, 0.25, (0.5, 0.0, 1.1), verts=8)
    cyl('kuningan', 0.05, 0.25, (0.25, 0.0, 1.1), verts=8)


def tungku_tempa():
    """Tungku tempa pandai besi: batu, bara menyala, tudung asap, puputan."""
    W, D = 1.75, 1.2
    box('batu_gelap', (W, D, 0.85), (0, 0.15, 0), bevel=0.02)
    for i in range(3):
        box('batu', (W + 0.01, D + 0.01, 0.03), (0, 0.15, 0.2 + i * 0.25), bevel=0)
    box('arang', (W - 0.4, D - 0.4, 0.06), (0, 0.15, 0.85))
    for i in range(9):
        x = -0.5 + (i % 3) * 0.5 + (0.08 if i % 2 else -0.06)
        y = -0.1 + (i // 3) * 0.25
        ball('bara' if i % 3 else 'api', 0.09, (x, y + 0.15, 0.92), seg=6, ring=4)
    # tudung asap & cerobong
    cyl('besi_gelap', 0.9, 0.6, (0, 0.15, 1.75), verts=4, r2=0.3,
        rot=(0, 0, math.pi / 4))
    box('besi_gelap', (0.42, 0.42, 1.2), (0, 0.15, 2.3))
    for sx in (-1, 1):
        box('besi_gelap', (0.05, 0.05, 0.95), (sx * 0.62, -0.3, 0.85))
    # puputan kulit di samping
    box('kayu', (0.5, 0.35, 0.08), (W / 2 + 0.02, -0.1, 0.55), rot=(0, 0.3, 0))
    box('karung', (0.42, 0.3, 0.14), (W / 2 + 0.0, -0.1, 0.62), rot=(0, 0.3, 0), bevel=0.05)
    # penjepit & palu tergeletak di tepi
    box('besi', (0.5, 0.03, 0.03), (-0.4, -0.35, 0.86))
    box('kayu_gelap', (0.3, 0.035, 0.035), (0.3, -0.38, 0.86))
    box('besi_gelap', (0.08, 0.12, 0.08), (0.45, -0.38, 0.86))


def jam():
    """Jam lonceng kayu berdiri dengan bandul kuningan."""
    W, D, H = 0.52, 0.36, 2.05
    box('kayu_merah', (W + 0.06, D + 0.04, 0.12), (0, 0, 0))
    box('kayu_merah', (W - 0.08, D - 0.06, 1.2), (0, 0, 0.12))
    box('kaca', (0.24, 0.01, 0.8), (0, -D / 2 + 0.02, 0.32), bevel=0.01)
    cyl('kuningan', 0.008, 0.6, (0, -D / 2 + 0.05, 0.5), verts=5)
    cyl('kuningan', 0.07, 0.02, (0, -D / 2 + 0.04, 0.48), rot=(math.pi / 2, 0, 0), verts=12)
    box('kayu_merah', (W, D, 0.62), (0, 0, 1.32), bevel=0.02)
    cyl('kertas', 0.19, 0.02, (0, -D / 2 - 0.01, 1.63), rot=(math.pi / 2, 0, 0), verts=16)
    cyl('kuningan', 0.21, 0.015, (0, -D / 2 - 0.0, 1.63), rot=(math.pi / 2, 0, 0), verts=16)
    box('hitam', (0.015, 0.01, 0.14), (0, -D / 2 - 0.035, 1.63), rot=(0, 0.6, 0), bevel=0)
    box('hitam', (0.015, 0.01, 0.1), (0, -D / 2 - 0.035, 1.63), rot=(0, -1.2, 0), bevel=0)
    cyl('kayu_gelap', 0.34, 0.12, (0, 0, 1.94), verts=3, rot=(math.pi / 2, 0, 0))


def pot():
    """Pot gerabah besar berisi tanaman berdaun lebar."""
    cyl('gerabah', 0.26, 0.48, (0, 0, 0), verts=14, r2=0.32, bevel=0.01)
    cyl('kayu_merah', 0.33, 0.06, (0, 0, 0.46), verts=14)
    cyl('tanah', 0.29, 0.02, (0, 0, 0.49), verts=14)
    for i in range(3):
        cyl('daun_gelap', 0.02, 0.5 + i * 0.12, (math.cos(i * 2.1) * 0.06, math.sin(i * 2.1) * 0.06, 0.5),
            verts=5, rot=(0.25 * math.cos(i * 2.1), 0.25 * math.sin(i * 2.1), 0))
    n = 11
    for i in range(n):
        yaw = i * (2 * math.pi / n) + (i % 3) * 0.3
        k = ('daun', 'daun_gelap', 'daun_muda')[i % 3]
        z = 0.75 + (i % 4) * 0.13
        leaf(k, 0.5 + (i % 3) * 0.08, 0.28, (0, 0, z), yaw, -0.7 - (i % 2) * 0.35)


def peti():
    """Peti kayu berpelat besi."""
    W, D, H = 1.1, 0.62, 0.55
    box('kayu', (W, D, H), (0, 0, 0), bevel=0.015)
    cyl('kayu', D / 2, W, (-W / 2, 0, H - 0.0), rot=(0, math.pi / 2, 0), verts=12)
    for sx in (-0.38, 0.38):
        box('besi_gelap', (0.07, D + 0.02, H + 0.01), (sx, 0, 0), bevel=0.005)
        cyl('besi_gelap', D / 2 + 0.01, 0.07, (sx - 0.035, 0, H), rot=(0, math.pi / 2, 0), verts=12)
    box('kuningan', (0.12, 0.03, 0.14), (0, -D / 2 - 0.01, H - 0.12))
    for i in range(3):
        box('kayu_gelap', (W - 0.02, 0.005, 0.012), (0, -D / 2 - 0.002, 0.12 + i * 0.15), bevel=0)


def tong():
    """Dua tong kayu (variasi peti untuk bengkel)."""
    for (x, y, r, h) in ((-0.3, 0.05, 0.3, 0.8), (0.35, -0.1, 0.26, 0.66)):
        cyl('kayu', r, h, (x, y, 0), verts=14, bevel=0.01)
        for z in (0.1, h - 0.14):
            cyl('besi_gelap', r + 0.012, 0.05, (x, y, z), verts=14)
        cyl('kayu_gelap', r - 0.03, 0.02, (x, y, h), verts=14)


def konter():
    """Satu segmen konter selebar ubin penuh -- segmen bersebelahan menyambung."""
    W, D, H = 2.0, 0.72, 0.95
    box('kayu_gelap', (W, D - 0.06, H - 0.05), (0, 0.03, 0), bevel=0.0)
    for i in range(5):
        box('kayu', (0.34, 0.03, H - 0.25), (-0.8 + i * 0.4, -D / 2 + 0.03, 0.12), bevel=0.008)
    box('kayu_muda', (W, D, 0.05), (0, 0, H - 0.05), bevel=0.0)
    box('kayu_gelap', (W, 0.08, 0.1), (0, -D / 2 + 0.04, 0))           # plint


def konter_warung():
    """Konter warung: segmen konter + toples kerupuk dan timbangan."""
    konter()
    H = 0.95
    for i, x in enumerate((-0.65, -0.3)):
        cyl('kaca', 0.13, 0.32, (x, 0.05, H), verts=10)
        cyl('kain_merah' if i else 'keramik_biru', 0.135, 0.06, (x, 0.05, H + 0.32), verts=10)
        cyl('buah_kuning', 0.1, 0.2, (x, 0.05, H + 0.04), verts=8)
    box('besi', (0.32, 0.22, 0.06), (0.45, 0.0, H))
    cyl('kuningan', 0.12, 0.03, (0.45, 0.0, H + 0.2), verts=12)
    box('besi', (0.04, 0.04, 0.14), (0.45, 0.0, H + 0.06))


def meja_kerja():
    """Meja kerja pandai besi: konter + catok + perkakas."""
    konter()
    H = 0.95
    box('besi_gelap', (0.16, 0.24, 0.12), (-0.6, -0.15, H))
    box('besi_gelap', (0.22, 0.04, 0.14), (-0.6, -0.29, H + 0.04))
    box('kayu', (1.2, 0.04, 0.6), (0.2, 0.33, H + 0.3))                 # papan gantung
    for i, k in enumerate(('besi', 'besi_gelap', 'besi', 'besi_gelap')):
        box(k, (0.05, 0.03, 0.34 - (i % 2) * 0.08), (-0.2 + i * 0.25, 0.3, H + 0.38))
    box('kayu_gelap', (0.35, 0.05, 0.05), (0.35, -0.1, H))
    box('besi', (0.1, 0.1, 0.07), (0.55, -0.1, H))


def rak():
    """Rak dagangan: toples, karung, kaleng."""
    W, D, H = 1.9, 0.5, 1.9
    for sx in (-1, 1):
        box('kayu_gelap', (0.05, D, H), (sx * (W / 2 - 0.025), 0, 0))
    box('kayu_gelap', (W, 0.03, H), (0, D / 2 - 0.015, 0))
    items = [('kaca', 'buah_merah'), ('kaca', 'buah_kuning'), ('karung', None),
             ('keramik_biru', None), ('kaca', 'buah_hijau'), ('gerabah', None)]
    for s in range(4):
        z = 0.08 + s * 0.46
        box('kayu', (W - 0.1, D - 0.03, 0.03), (0, -0.015, z))
        for i in range(5):
            x = -0.7 + i * 0.35
            a, b = items[(i + s * 2) % len(items)]
            if a == 'karung':
                box('karung', (0.26, 0.26, 0.3), (x, -0.02, z + 0.03), bevel=0.07)
            elif b:
                cyl(a, 0.08, 0.24, (x, -0.02, z + 0.03), verts=10)
                cyl(b, 0.065, 0.16, (x, -0.02, z + 0.04), verts=8)
                cyl('kayu_gelap', 0.085, 0.03, (x, -0.02, z + 0.27), verts=10)
            else:
                cyl(a, 0.09, 0.2 + (i % 2) * 0.08, (x, -0.02, z + 0.03), verts=10)
    box('kayu_gelap', (W + 0.04, D + 0.02, 0.05), (0, 0, H))


def rak_obat():
    """Lemari obat klinik: kaca depan, botol-botol, tanda palang."""
    W, D, H = 1.9, 0.48, 1.95
    box('putih', (W, D, H), (0, 0, 0), bevel=0.015)
    for s in range(4):
        z = 0.1 + s * 0.45
        box('kayu_muda', (W - 0.1, D - 0.06, 0.025), (0, 0, z))
        for i in range(7):
            k = ('kaca', 'keramik_biru', 'putih', 'gerabah')[(i + s) % 4]
            cyl(k, 0.05, 0.14 + (i % 3) * 0.04, (-0.75 + i * 0.25, -0.03, z + 0.025), verts=8)
    box('kaca', (W - 0.08, 0.01, H - 0.12), (0, -D / 2 - 0.006, 0.06), bevel=0)
    box('putih', (0.04, 0.02, H - 0.1), (0, -D / 2 - 0.01, 0.05), bevel=0)
    box('merah_salib', (0.3, 0.02, 0.08), (0, -D / 2 - 0.015, H + 0.12), bevel=0)
    box('merah_salib', (0.08, 0.02, 0.3), (0, -D / 2 - 0.015, H + 0.01), bevel=0)
    box('putih', (0.42, 0.03, 0.42), (0, -D / 2 + 0.02, H - 0.04), bevel=0.01)


def rak_senjata():
    """Rak senjata & perkakas tempa di dinding."""
    W, H = 1.8, 1.9
    box('kayu_gelap', (W, 0.08, H), (0, 0.15, 0))
    for z in (0.5, 1.2):
        box('kayu', (W - 0.1, 0.12, 0.06), (0, 0.06, z))
    for i in range(5):
        x = -0.7 + i * 0.35
        box('besi', (0.06, 0.02, 0.85), (x, 0.03, 0.62))                  # bilah pedang
        box('kuningan', (0.2, 0.04, 0.04), (x, 0.03, 1.45))
        box('kayu_gelap', (0.04, 0.04, 0.22), (x, 0.03, 1.47))
    for i in range(4):
        x = -0.6 + i * 0.4
        box('kayu', (0.04, 0.04, 0.45), (x, -0.02, 0.0))
        box('besi_gelap', (0.16, 0.06, 0.08), (x, -0.02, 0.42))         # palu di bawah


def rak_bibit():
    """Rak bertingkat rumah kaca berisi pot semai."""
    W, D, H = 1.8, 0.55, 1.5
    for sx in (-1, 1):
        for sy in (-1, 1):
            box('kayu', (0.05, 0.05, H), (sx * (W / 2 - 0.03), sy * (D / 2 - 0.03), 0))
    for s in range(3):
        z = 0.25 + s * 0.5
        box('kayu_muda', (W, D, 0.03), (0, 0, z))
        for i in range(5):
            x = -0.7 + i * 0.35
            cyl('gerabah', 0.08, 0.13, (x, 0, z + 0.03), verts=8, r2=0.1)
            cyl('tanah', 0.085, 0.01, (x, 0, z + 0.16), verts=8)
            for j in range(3):
                leaf(('daun_muda', 'daun')[j % 2], 0.12 + s * 0.03, 0.06,
                     (x, 0, z + 0.16), j * 2.1 + i, -0.5)


def meja_pot():
    """Meja kerja rumah kaca: sekop, karung tanah, kaleng siram."""
    L, D, H = 1.7, 0.8, 0.85
    for sx in (-1, 1):
        for sy in (-1, 1):
            box('kayu', (0.07, 0.07, H), (sx * (L / 2 - 0.06), sy * (D / 2 - 0.06), 0))
    box('kayu_muda', (L, D, 0.05), (0, 0, H))
    box('kayu', (L - 0.1, D - 0.1, 0.03), (0, 0, 0.2))
    box('karung', (0.45, 0.32, 0.26), (-0.45, 0.05, H + 0.05), bevel=0.08)
    box('tanah', (0.36, 0.25, 0.04), (-0.45, 0.05, H + 0.3), bevel=0.02)
    cyl('besi', 0.1, 0.2, (0.15, 0.0, H + 0.05), verts=10)
    cyl('besi', 0.02, 0.28, (0.27, 0.0, H + 0.12), verts=6, rot=(0, 1.0, 0))
    box('besi', (0.08, 0.14, 0.02), (0.55, -0.1, H + 0.05))
    box('kayu_gelap', (0.03, 0.22, 0.03), (0.55, 0.08, H + 0.05))
    for i in range(3):
        cyl('gerabah', 0.07, 0.11, (-0.1 + i * 0.2, -0.28, 0.23), verts=8, r2=0.09)
    cyl('karung', 0.25, 0.3, (0.3, 0.05, 0.23), verts=10, bevel=0.03)


def landasan():
    """Landasan tempa di atas tunggul kayu, palu bersandar."""
    cyl('kayu', 0.33, 0.55, (0, 0, 0), verts=14, bevel=0.02)
    cyl('kayu_muda', 0.31, 0.01, (0, 0, 0.55), verts=14)
    box('besi_gelap', (0.32, 0.22, 0.16), (0, 0, 0.55))
    box('besi_gelap', (0.6, 0.24, 0.13), (0, 0, 0.71))
    cyl('besi_gelap', 0.11, 0.3, (0.3, 0, 0.775), verts=8, r2=0.01, rot=(0, math.pi / 2, 0))
    box('besi', (0.1, 0.08, 0.02), (-0.2, 0, 0.84))
    box('kayu_gelap', (0.04, 0.04, 0.55), (0.32, -0.3, 0.0), rot=(0.25, 0, 0))
    box('besi_gelap', (0.16, 0.08, 0.08), (0.32, -0.2, 0.52))


def kuda_kuda():
    """Kuda-kuda lukis dengan kanvas setengah jadi + meja palet di samping."""
    for sx in (-0.28, 0.28):
        box('kayu_muda', (0.05, 0.04, 1.75), (sx, 0.0, 0.0), rot=(0.12, sx * -0.18, 0))
    box('kayu_muda', (0.05, 0.04, 1.6), (0, 0.38, 0.0), rot=(-0.28, 0, 0))
    box('kayu', (0.7, 0.08, 0.04), (0, -0.04, 0.72))
    box('kanvas', (0.86, 0.04, 0.68), (0, -0.07, 0.76), rot=(0.12, 0, 0), bevel=0.005)
    for (x, z, k, w, h) in ((-0.2, 0.95, 'cat_biru', 0.4, 0.22), (0.12, 1.08, 'cat_kuning', 0.18, 0.18),
                            (0.05, 0.86, 'daun', 0.5, 0.12), (-0.15, 1.18, 'cat_merah', 0.12, 0.1)):
        box(k, (w, 0.01, h), (x, -0.105 + (z - 0.76) * 0.12, z), rot=(0.12, 0, 0), bevel=0)
    # meja palet kecil
    cyl('kayu', 0.2, 0.02, (0.68, -0.15, 0.7), verts=12)
    cyl('kayu_gelap', 0.02, 0.7, (0.68, -0.15, 0.0), verts=6)
    for i, k in enumerate(('cat_merah', 'cat_biru', 'cat_kuning', 'putih')):
        cyl(k, 0.035, 0.02, (0.6 + (i % 2) * 0.13, -0.22 + (i // 2) * 0.13, 0.72), verts=8)
    cyl('kaca', 0.05, 0.14, (0.75, -0.05, 0.72), verts=8)
    for i in range(3):
        cyl('kayu_gelap', 0.007, 0.25, (0.74 + i * 0.015, -0.05, 0.8), verts=4, rot=(0, 0.1 * (i - 1), 0))


def meja_tulis():
    """Meja tulis (ubin KALENDER): kalender gantung di dinding, lampu meja."""
    L, D, H = 1.3, 0.62, 0.75
    for sx in (-1, 1):
        box('kayu', (0.06, D, H), (sx * (L / 2 - 0.03), 0, 0))
    box('kayu', (L, D, 0.04), (0, 0, H), bevel=0.01)
    box('kayu_gelap', (0.42, D - 0.06, 0.4), (L / 2 - 0.27, 0, 0.32))
    for i in range(2):
        box('kayu_muda', (0.38, 0.02, 0.16), (L / 2 - 0.27, -D / 2 + 0.02, 0.36 + i * 0.19))
        cyl('kuningan', 0.015, 0.02, (L / 2 - 0.27, -D / 2, 0.44 + i * 0.19), rot=(math.pi / 2, 0, 0), verts=6)
    # kalender di dinding (dinding ada di +Y, sejauh 1 m dari pusat ubin)
    yw = 0.98
    box('kertas', (0.5, 0.02, 0.64), (0, yw - 0.01, 1.35), bevel=0.004)
    box('merah_salib', (0.5, 0.025, 0.12), (0, yw - 0.012, 1.87), bevel=0.004)
    for r in range(4):
        for c in range(5):
            box('kertas' if (r + c) % 6 else 'merah_salib', (0.07, 0.005, 0.07),
                (-0.18 + c * 0.09, yw - 0.025, 1.45 + r * 0.09), bevel=0)
            box('hitam', (0.05, 0.004, 0.006), (-0.18 + c * 0.09, yw - 0.03, 1.47 + r * 0.09), bevel=0)
    # lampu meja + buku + cangkir
    cyl('kuningan', 0.08, 0.02, (-0.4, 0.12, H + 0.04), verts=10)
    cyl('kuningan', 0.012, 0.32, (-0.4, 0.12, H + 0.06), verts=6, rot=(-0.2, 0, 0))
    cyl('kain_hijau', 0.13, 0.12, (-0.4, 0.06, H + 0.34), verts=10, r2=0.05)
    cyl('lampu', 0.07, 0.01, (-0.4, 0.06, H + 0.34), verts=10)
    box('buku_2', (0.26, 0.2, 0.04), (-0.05, -0.05, H + 0.04), rot=(0, 0, 0.2))
    box('kertas', (0.24, 0.18, 0.01), (-0.04, -0.05, H + 0.08), rot=(0, 0, 0.2), bevel=0)
    cyl('putih', 0.045, 0.09, (0.25, -0.12, H + 0.04), verts=10)
    # bangku kecil
    box('kayu_gelap', (0.4, 0.36, 0.04), (0, -0.62, 0.44))
    for sx in (-0.15, 0.15):
        for sy in (-0.14, 0.14):
            box('kayu_gelap', (0.04, 0.04, 0.44), (sx, -0.62 + sy, 0))


def pintu():
    """Kusen pintu interior + daun pintu terbuka + keset. Pusat = ubin pintu.

    Ubin pintu ADA di baris dinding, jadi rangka ini sendiri yang menutup celah
    di dinding: dua tiang, ambang atas, dan dinding di atas ambang.
    """
    WALL_H = 2.8
    box('kayu_gelap', (0.16, 0.36, 2.25), (-0.86, 0, 0))
    box('kayu_gelap', (0.16, 0.36, 2.25), (0.86, 0, 0))
    box('kayu_gelap', (1.9, 0.36, 0.16), (0, 0, 2.2))
    box('krem', (2.0, 0.3, WALL_H - 2.36), (0, 0, 2.36), bevel=0)        # dinding atas
    box('kayu_gelap', (2.0, 0.34, 0.06), (0, 0, 2.36), bevel=0)
    # celah gelap di ambang: "luar" yang terlihat dari dalam
    box('hitam', (1.56, 0.04, 2.2), (0, 0.16, 0), bevel=0)
    # daun pintu terbuka ke dalam, berengsel di kiri
    box('kayu', (0.06, 1.0, 2.1), (-0.76, -0.62, 0.02), rot=(0, 0, 0.35))
    for z in (0.35, 1.05, 1.7):
        box('kayu_gelap', (0.07, 0.86, 0.05), (-0.76, -0.62, z), rot=(0, 0, 0.35), bevel=0)
    box('kuningan', (0.09, 0.05, 0.05), (-0.98, -1.05, 1.0), rot=(0, 0, 0.35))
    # keset di dalam
    box('karung', (1.1, 0.6, 0.02), (0, -0.62, 0), bevel=0.01)
    box('kain_merah', (0.9, 0.42, 0.022), (0, -0.62, 0), bevel=0)


def jendela():
    """Jendela dinding: kusen, kaca bersekat, ambang, gorden. Pusat = muka dinding.

    Dibuat menghadap -Y dengan punggung di y=0: game menempelkannya ke muka
    dalam dinding.
    """
    W, H, Z0 = 1.2, 1.1, 0.95
    box('kayu_gelap', (W + 0.16, 0.08, H + 0.16), (0, -0.03, Z0 - 0.08))
    box('kaca', (W, 0.03, H), (0, -0.06, Z0), bevel=0)
    box('kayu_gelap', (0.05, 0.05, H), (0, -0.08, Z0), bevel=0)
    box('kayu_gelap', (W, 0.05, 0.05), (0, -0.08, Z0 + H / 2 - 0.025), bevel=0)
    box('kayu', (W + 0.3, 0.2, 0.05), (0, -0.1, Z0 - 0.1))               # ambang
    cyl('kuningan', 0.015, W + 0.6, (-(W + 0.6) / 2, -0.12, Z0 + H + 0.18), rot=(0, math.pi / 2, 0), verts=6)
    for sx in (-1, 1):
        box('gorden', (0.3, 0.06, H + 0.35), (sx * (W / 2 + 0.12), -0.14, Z0 - 0.2), bevel=0.02)
        box('kuningan', (0.3, 0.07, 0.04), (sx * (W / 2 + 0.12), -0.14, Z0 + 0.25), bevel=0)
    cyl('gerabah', 0.07, 0.12, (0.35, -0.1, Z0 - 0.05), verts=8)
    for i in range(3):
        leaf('daun', 0.14, 0.06, (0.35, -0.1, Z0 + 0.07), i * 2.1, -0.5)


def kulkas():
    """Kulkas dua pintu bergaya 60-an, sudut membulat, gagang krom."""
    W, D, H = 0.78, 0.7, 1.75
    box('krem', (W, D, H), (0, 0, 0.06), bevel=0.06)
    for sx in (-1, 1):
        box('besi_gelap', (0.06, 0.06, 0.06), (sx * (W / 2 - 0.08), -D / 2 + 0.08, 0))
        box('besi_gelap', (0.06, 0.06, 0.06), (sx * (W / 2 - 0.08), D / 2 - 0.08, 0))
    box('besi', (W - 0.04, 0.02, 0.02), (0, -D / 2 - 0.005, 1.2), bevel=0)   # sela pintu
    box('besi', (0.04, 0.05, 0.3), (W / 2 - 0.1, -D / 2 - 0.03, 1.32))
    box('besi', (0.04, 0.05, 0.42), (W / 2 - 0.1, -D / 2 - 0.03, 0.62))
    box('kain_merah', (0.16, 0.01, 0.05), (-0.18, -D / 2 - 0.005, 1.58), bevel=0)  # emblem
    # magnet & kertas tempel
    box('kertas', (0.16, 0.01, 0.2), (-0.15, -D / 2 - 0.006, 0.85), rot=(0, 0.08, 0), bevel=0)
    ball('buah_kuning', 0.025, (-0.15, -D / 2 - 0.02, 1.04))
    # toples & keranjang di atas
    box('karung', (0.36, 0.3, 0.14), (-0.12, 0, H + 0.06), bevel=0.04)
    cyl('kaca', 0.07, 0.18, (0.22, 0, H + 0.06), verts=8)


def toilet():
    """Kloset duduk + tangki, sikat, gulungan tisu, alas lantai."""
    box('keramik_biru', (1.3, 1.3, 0.012), (0, -0.05, 0), bevel=0)
    cyl('putih', 0.17, 0.32, (0, -0.06, 0), verts=14, r2=0.21)
    cyl('putih', 0.23, 0.07, (0, -0.1, 0.32), verts=16)
    cyl('kayu', 0.235, 0.025, (0, -0.1, 0.39), verts=16)             # dudukan
    box('putih', (0.46, 0.2, 0.42), (0, 0.24, 0.3), bevel=0.03)        # tangki
    box('putih', (0.5, 0.23, 0.04), (0, 0.24, 0.72), bevel=0.015)
    box('besi', (0.06, 0.02, 0.02), (-0.14, 0.13, 0.62), bevel=0)
    cyl('besi', 0.012, 0.6, (0.45, 0.25, 0.0), verts=6)                 # tiang tisu
    cyl('putih', 0.06, 0.11, (0.39, 0.25, 0.52), rot=(0, math.pi / 2, 0), verts=10)
    cyl('kain_teal', 0.05, 0.08, (-0.42, 0.2, 0.0), verts=8)            # wadah sikat
    cyl('kayu_gelap', 0.01, 0.32, (-0.42, 0.2, 0.08), verts=5)
    box('kain_hijau', (0.5, 0.36, 0.015), (0, -0.48, 0.012), bevel=0.01)


def pancuran():
    """Bilik pancuran: bak keramik, tirai, kepala pancuran, gayung."""
    W, D = 1.3, 1.3
    box('keramik_biru', (W, D, 0.12), (0, 0, 0), bevel=0.02)
    box('putih', (W - 0.14, D - 0.14, 0.01), (0, 0, 0.12), bevel=0)
    box('besi_gelap', (0.1, 0.1, 0.012), (0.3, 0.3, 0.125), bevel=0)    # saluran
    # dinding keramik belakang setinggi kepala
    box('putih', (W, 0.06, 1.9), (0, D / 2 - 0.03, 0.12), bevel=0)
    for r in range(6):
        box('keramik_biru', (W + 0.002, 0.062, 0.012), (0, D / 2 - 0.03, 0.4 + r * 0.28), bevel=0)
    cyl('besi', 0.015, 0.75, (0, D / 2 - 0.08, 1.2), verts=6)
    cyl('besi', 0.015, 0.3, (0, D / 2 - 0.08, 1.95), rot=(math.pi / 2, 0, 0), verts=6)
    cyl('besi', 0.09, 0.04, (0, D / 2 - 0.36, 1.92), verts=12, r2=0.05)
    box('besi', (0.1, 0.04, 0.06), (0.18, D / 2 - 0.07, 1.1))
    # rel & tirai di sisi depan
    box('besi', (W, 0.025, 0.025), (0, -D / 2 + 0.05, 2.05), bevel=0)
    for i in range(5):
        box('kain_teal' if i % 2 else 'putih', (0.13, 0.04, 1.75),
            (-W / 2 + 0.1 + i * 0.12, -D / 2 + 0.06 + (i % 2) * 0.04, 0.3), bevel=0)
    # ember & gayung khas kamar mandi Indonesia
    cyl('keramik_biru', 0.16, 0.3, (0.38, -0.2, 0.12), verts=12, r2=0.18)
    cyl('kuningan', 0.06, 0.08, (0.38, -0.2, 0.44), verts=8)
    box('kuningan', (0.03, 0.2, 0.025), (0.38, -0.05, 0.47), bevel=0)


def gapura_swarga():
    """Candi bentar (gapura terbelah) batu andesit berhias emas, 2 ubin lebar.

    Celah tengah 2,4 m -- jalur dua ubin lewat di antaranya. Pusat = tengah celah.
    """
    for sx in (-1, 1):
        x = sx * 2.1
        box('batu_gelap', (1.6, 1.6, 0.5), (x, 0, 0), bevel=0.03)
        for i, (w, h) in enumerate(((1.4, 1.2), (1.2, 1.0), (1.0, 0.9), (0.8, 0.8), (0.6, 0.7), (0.4, 0.6))):
            z = 0.5 + sum(hh for _, hh in ((1.4, 1.2), (1.2, 1.0), (1.0, 0.9), (0.8, 0.8), (0.6, 0.7), (0.4, 0.6))[:i])
            # Sisi dalam gapura TEGAK lurus (ciri candi bentar), sisi luar bertingkat.
            off = sx * (1.4 - w) / 2
            box('batu' if i % 2 else 'batu_gelap', (w, w, h), (x + off, 0, z), bevel=0.03)
            box('kuningan', (w + 0.04, w + 0.04, 0.06), (x + off, 0, z + h - 0.06), bevel=0)
        box('kuningan', (0.2, 0.2, 0.5), (x + sx * 0.5, 0, 5.7))
        ball('kuningan', 0.14, (x + sx * 0.5, 0, 6.3))
        # relief daun di muka depan
        for j in range(3):
            leaf('kuningan', 0.5, 0.3, (x, -0.72, 1.3 + j * 1.0), sx * 0.4, 1.2)
    # anak tangga di bawah celah
    for i in range(3):
        box('batu', (2.4, 0.5, 0.12), (0, -0.4 - i * 0.5, 0.24 - i * 0.12), bevel=0.02)
    # pot sesajen + payung tedung di kiri-kanan
    for sx in (-1, 1):
        cyl('gerabah', 0.18, 0.3, (sx * 3.3, -1.0, 0), verts=10)
        for k in range(3):
            leaf(('daun', 'kain_mustard', 'kain_merah')[k], 0.2, 0.1, (sx * 3.3, -1.0, 0.3), k * 2.1, -0.4)
        cyl('kayu_gelap', 0.03, 2.6, (sx * 3.0, 0.6, 0), verts=6)
        cyl('kain_mustard', 0.55, 0.3, (sx * 3.0, 0.6, 2.4), verts=12, r2=0.05)
        cyl('putih', 0.56, 0.12, (sx * 3.0, 0.6, 2.3), verts=12)


def mulut_gua():
    """Mulut gua di kaki jalur: lengkung batu kasar dengan kegelapan di dalam.

    Pusat = ubin ambang (dua ubin lebar). Muka menghadap -Y (ke jalur).
    """
    box('hitam', (2.6, 0.3, 2.6), (0, 0.6, 0), bevel=0)
    for i in range(9):
        a = math.pi * i / 8
        x = math.cos(a) * 1.75
        z = math.sin(a) * 2.2
        ball('batu_gelap' if i % 2 else 'batu', 0.55 + 0.1 * (i % 3), (x, 0.3, z + 0.2), seg=7, ring=5,
             scale=(1.0, 0.9, 1.15))
    for sx in (-1, 1):
        box('batu_gelap', (0.9, 1.4, 1.8), (sx * 1.9, 0.5, 0), rot=(0, 0, sx * 0.08), bevel=0.08)
    box('batu', (4.6, 1.4, 1.0), (0, 0.5, 2.4), bevel=0.15)
    for i in range(5):
        leaf(('daun', 'daun_gelap')[i % 2], 0.6, 0.25, (-1.4 + i * 0.7, -0.1, 3.1), i * 0.9, 2.4)  # sulur
    # obor di kedua sisi
    for sx in (-1, 1):
        cyl('kayu_gelap', 0.04, 1.3, (sx * 2.4, -0.4, 0), verts=6)
        cyl('besi_gelap', 0.09, 0.15, (sx * 2.4, -0.4, 1.3), verts=8, r2=0.12)
        cyl('api', 0.08, 0.25, (sx * 2.4, -0.4, 1.42), verts=6, r2=0.0)


def lubang_dungeon():
    """Lubang ke gua bertingkat: bibir batu, kegelapan, tangga kayu, tali, obor.

    Pusat = ubin TANGGA_TURUN. Muka menghadap -Y.
    """
    box('hitam', (1.5, 1.5, 0.02), (0, 0, 0.005), bevel=0)
    for i in range(12):
        a = 2 * math.pi * i / 12
        ball('batu' if i % 3 else 'batu_gelap', 0.26 + 0.05 * (i % 2),
             (math.cos(a) * 0.86, math.sin(a) * 0.86, 0.05), seg=7, ring=5, scale=(1.2, 1.0, 0.6))
    # dua tiang tangga mencuat dari lubang + anak tangga
    for sx in (-0.22, 0.22):
        box('kayu', (0.07, 0.07, 1.6), (sx, 0.42, -0.6), rot=(-0.35, 0, 0))
    for i in range(4):
        box('kayu_gelap', (0.5, 0.06, 0.05), (0, 0.42 - i * 0.12 + 0.3, -0.25 + i * 0.3), rot=(-0.35, 0, 0))
    # kerangka kerekan kayu dan tali
    for sx in (-0.8, 0.8):
        box('kayu_gelap', (0.1, 0.1, 1.9), (sx, -0.75, 0), bevel=0.01)
    box('kayu_gelap', (1.8, 0.1, 0.1), (0, -0.75, 1.85))
    cyl('karung', 0.012, 1.9, (0.1, -0.75, 0.0), verts=5)
    cyl('kayu', 0.09, 0.14, (0.1, -0.75, 1.68), rot=(0, math.pi / 2, 0), verts=10)
    # obor & tanda peringatan
    cyl('kayu_gelap', 0.035, 1.2, (0.95, 0.6, 0), verts=6)
    cyl('api', 0.08, 0.22, (0.95, 0.6, 1.2), verts=6, r2=0.0)
    box('kayu', (0.45, 0.04, 0.3), (-0.9, 0.55, 0.75), rot=(0, 0, 0.1))
    box('merah_salib', (0.3, 0.045, 0.05), (-0.9, 0.548, 0.85), rot=(0, 0, 0.1), bevel=0)
    cyl('kayu_gelap', 0.03, 0.8, (-0.9, 0.58, 0), verts=5)


FURNITURE = {
    'kasur': kasur, 'kasur_klinik': kasur_klinik, 'kompor': kompor,
    'meja': meja, 'meja_panjang': meja_panjang, 'kursi': kursi, 'tv': tv,
    'rak_buku': rak_buku, 'lemari_cermin': lemari_cermin, 'tungku': tungku,
    'tungku_tempa': tungku_tempa, 'jam': jam, 'pot': pot, 'peti': peti,
    'tong': tong, 'konter': konter, 'konter_warung': konter_warung,
    'meja_kerja': meja_kerja, 'rak': rak, 'rak_obat': rak_obat,
    'rak_senjata': rak_senjata, 'rak_bibit': rak_bibit, 'meja_pot': meja_pot,
    'landasan': landasan, 'kuda_kuda': kuda_kuda, 'meja_tulis': meja_tulis,
    'pintu': pintu, 'jendela': jendela,
    'kulkas': kulkas, 'toilet': toilet, 'pancuran': pancuran,
    'gapura_swarga': gapura_swarga, 'mulut_gua': mulut_gua, 'lubang_dungeon': lubang_dungeon,
}


# ─── PERAKITAN & EKSPOR ──────────────────────────────────────────────────────
def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for coll in (bpy.data.meshes, bpy.data.materials):
        for d in list(coll):
            if d.users == 0:
                coll.remove(d)


def assign_palette_uv(obj):
    """Setiap loop UV menunjuk ke kotak warna material mukanya."""
    me = obj.data
    if not me.uv_layers:
        me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data
    for poly in me.polygons:
        key = me.materials[poly.material_index].name
        u, v = swatch_uv(key)
        for li in poly.loop_indices:
            uv[li].uv = (u, v)


def build(name, fn, coll):
    _PARTS.clear()
    fn()
    bpy.ops.object.select_all(action='DESELECT')
    for o in _PARTS:
        o.select_set(True)
    bpy.context.view_layer.objects.active = _PARTS[0]
    for o in _PARTS:
        bpy.context.view_layer.objects.active = o
        for md in list(o.modifiers):
            bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.context.view_layer.objects.active = _PARTS[0]
    bpy.ops.object.join()
    obj = bpy.context.active_object
    obj.name = name
    # Normal rata: cel-shader game butuh bidang tegas, bukan gradasi halus.
    for p in obj.data.polygons:
        p.use_smooth = False
    assign_palette_uv(obj)
    for c in obj.users_collection:
        c.objects.unlink(obj)
    coll.objects.link(obj)
    return obj


def export(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    loc = obj.location.copy()
    obj.location = (0, 0, 0)
    bpy.ops.wm.obj_export(
        filepath=str(OUT_DIR / f'{obj.name}.obj'),
        export_selected_objects=True,
        up_axis='Y', forward_axis='NEGATIVE_Z',
        export_uv=True, export_normals=True,
        export_materials=False, apply_modifiers=True,
        export_triangulated_mesh=True)
    obj.location = loc


def render_sheet(objs):
    """Lembar pratinjau: semua perabot berjajar, kamera 3/4 dari depan."""
    cols = 7
    for i, o in enumerate(objs):
        o.location = ((i % cols) * 2.6, -(i // cols) * 2.8, 0)
    scn = bpy.context.scene
    scn.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [
        e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
    scn.render.resolution_x, scn.render.resolution_y = 1800, 1100
    scn.render.film_transparent = False
    w = bpy.data.worlds.new('w') if not scn.world else scn.world
    scn.world = w
    w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (0.08, 0.075, 0.07, 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.6
    bpy.ops.mesh.primitive_plane_add(size=60, location=(7.8, -3, 0))
    fl = bpy.context.active_object
    fl.data.materials.append(mat('kayu_lantai'))
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    sun = bpy.context.active_object
    sun.data.energy = 3.5
    sun.rotation_euler = (0.75, 0.2, -0.6)
    from mathutils import Vector
    target = Vector((7.8, -4.2, 0.6))
    bpy.ops.object.camera_add(location=(7.8, -21, 13))
    cam = bpy.context.active_object
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 20
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scn.camera = cam
    scn.render.filepath = str(ROOT / '_bench' / 'interior_sheet.png')
    (ROOT / '_bench').mkdir(exist_ok=True)
    bpy.ops.render.render(write_still=True)


def main():
    clear_scene()
    write_palette()
    coll = bpy.data.collections.new('Interior')
    bpy.context.scene.collection.children.link(coll)
    objs = []
    for name, fn in FURNITURE.items():
        o = build(name, fn, coll)
        export(o)
        tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
        print(f'INTERIOR {name:14s} tris={tris}')
        objs.append(o)
    if '--render' in sys.argv:
        render_sheet(objs)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_OUT))
    print('INTERIOR_DONE', len(objs))


main()
