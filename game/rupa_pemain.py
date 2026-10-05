"""rupa_pemain.py — Pilihan layar Buat Karakter diterapkan ke model pemain.

Sejak pemain memakai rig ter-ekspor (assets/models/actors/player.glb), seluruh
pilihan chargen -- kulit, rambut, baju, celana, topi -- tidak berpengaruh
apa pun: kode penerapnya ditulis untuk model voxel dan Vitaboy lama. Di sini
pilihan itu diterapkan ke GLB-nya langsung, saat permainan berjalan:

  - BAJU dan CELANA: tiap segitiga badan digolongkan dari tinggi verteksnya
    (di atas pinggul = baju, di bawah = celana), lalu segitiga itu dilukis ke
    topeng di ruang UV. Piksel di dalam topeng diwarnai ulang dengan
    mempertahankan terang-gelapnya, jadi lipatan kain tetap ada.
  - KULIT: piksel yang lolos uji kulit di tekstur badan dan kepala.
  - RAMBUT: piksel gelap tak berwarna di tekstur kepala.
  - AKSESORI KEPALA: dibangun dari primitif dan ditempel ke sendi HEAD.
    Posisinya DIUKUR dari kotak batas geometri kepala yang sebenarnya, bukan
    angka tebakan -- topi yang melayang di atas rambut terbaca sebagai benda
    yang tidak dipakai.
"""
from __future__ import annotations

from panda3d.core import GeomVertexReader, Texture as PTexture, NodePath

# Palet: kalem, mengikuti DESIGN_STANDARD (muted Disco/Zomboid).
KULIT = [
    ('Kuning Langsat', (226, 186, 150)),
    ('Sawo Cerah',     (198, 146, 104)),
    ('Sawo Matang',    (164, 112, 76)),
    ('Cokelat Tua',    (124, 82, 56)),
    ('Gelap',          (92, 60, 42)),
    ('Terang',         (238, 208, 182)),
]
RAMBUT = [
    ('Hitam',      (28, 24, 22)),
    ('Cokelat',    (74, 50, 32)),
    ('Uban',       (176, 172, 168)),
    ('Pirang Kusam', (176, 146, 92)),
    ('Merah Bata', (128, 58, 38)),
]
BAJU = [
    ('Lurik Kunyit', (196, 150, 64)),
    ('Biru Nila',    (64, 82, 128)),
    ('Hijau Daun',   (86, 120, 74)),
    ('Merah Bata',   (150, 70, 52)),
    ('Krem',         (214, 200, 170)),
    ('Abu Batu',     (112, 112, 108)),
    ('Cokelat Kopi', (102, 72, 50)),
]
CELANA = [
    ('Hitam',      (44, 42, 44)),
    ('Nila Tua',   (50, 60, 92)),
    ('Cokelat',    (96, 70, 48)),
    ('Khaki',      (150, 136, 100)),
    ('Batik Sogan', (120, 84, 52)),
]
AKSESORI = [
    ('Caping',       'caping'),
    ('Topi Bucket',  'bucket'),
    ('Peci',         'peci'),
    ('Ikat Kepala',  'ikat'),
    ('Topi Koboi',   'koboi'),
    ('Tanpa',        None),
]


def _kulit(r, g, b):
    # Kulit punya biru yang cukup (b/r >= ~0.28); kain jingga/kunyit hampir
    # tanpa biru dan dulu lolos sebagai kulit -- seluruh baju tercelup.
    return (r > g * 1.06 and g > b * 1.02 and r > 0.06
            and b >= r * 0.26 and (r - b) > 0.025)


def _segitiga(geom_node):
    """(uv0, uv1, uv2, tinggi_rata) untuk tiap segitiga di GeomNode."""
    out = []
    n = geom_node.node()
    for gi in range(n.getNumGeoms()):
        geom = n.getGeom(gi)
        vd = geom.getVertexData()
        fmt = vd.getFormat()
        # glTF menamai kolom UV 'texcoord.0', bukan 'texcoord'
        kol_uv = next((str(fmt.getColumn(k).getName()) for k in range(fmt.getNumColumns())
                       if str(fmt.getColumn(k).getName()).startswith('texcoord')), None)
        if kol_uv is None:
            continue
        rv = GeomVertexReader(vd, 'vertex')
        rt = GeomVertexReader(vd, kol_uv)
        pos, uv = [], []
        while not rv.isAtEnd():
            pos.append(rv.getData3())
            uv.append(rt.getData2())
        for pi in range(geom.getNumPrimitives()):
            prim = geom.getPrimitive(pi).decompose()
            for k in range(prim.getNumPrimitives()):
                a, b = prim.getPrimitiveStart(k), prim.getPrimitiveEnd(k)
                if b - a != 3:
                    continue
                idx = [prim.getVertex(j) for j in range(a, b)]
                h = sum(pos[i].y for i in idx) / 3.0      # glTF Y-atas
                out.append(([uv[i] for i in idx], h))
    return out


def _gambar_topeng(tris, w, h, batas_pinggul):
    """Topeng 'L' (Image mode L): 1 = baju, 2 = celana, 0 = lain."""
    from PIL import Image, ImageDraw
    tp = Image.new('L', (w, h), 0)
    d = ImageDraw.Draw(tp)
    for uvs, tinggi in tris:
        nilai = 1 if tinggi >= batas_pinggul else 2
        d.polygon([(u * w, (1.0 - v) * h) for (u, v) in uvs], fill=nilai)
    return tp


def _ke_pil(tex: PTexture):
    from PIL import Image
    w, h = tex.getXSize(), tex.getYSize()
    raw = bytes(tex.getRamImageAs('RGBA'))
    if len(raw) != w * h * 4:
        return None
    # Panda menyimpan baris dari bawah ke atas
    return Image.frombytes('RGBA', (w, h), raw).transpose(Image.FLIP_TOP_BOTTOM)


def _dari_pil(img, nama):
    from PIL import Image
    t = PTexture(nama)
    data = img.convert('RGBA').transpose(Image.FLIP_TOP_BOTTOM).tobytes()
    t.setup2dTexture(img.width, img.height, PTexture.T_unsigned_byte, PTexture.F_rgba)
    t.setRamImageAs(data, 'RGBA')
    # Mipmap HARUS dibangkitkan kalau filter mipmap dipakai; tanpa data level
    # itu GPU membaca level kosong dan seluruh baju tampil satu warna rata.
    t.generateRamMipmapImages()
    t.setMinfilter(PTexture.FT_linear_mipmap_linear)
    t.setMagfilter(PTexture.FT_linear)
    return t


def _warnai(img, topeng, peta):
    """peta: {nilai_topeng|'kulit'|'rambut': rgb}. Mengembalikan gambar baru."""
    px = img.load()
    tp = topeng.load() if topeng is not None else None
    W, H = img.size
    cache = {k: tuple(c / 255.0 for c in v) for k, v in peta.items()}
    for y in range(H):
        for x in range(W):
            r, g, b, a = px[x, y]
            r, g, b = r / 255.0, g / 255.0, b / 255.0
            l = 0.299 * r + 0.587 * g + 0.114 * b
            if 'kulit' in cache and _kulit(r, g, b):
                t = cache['kulit']; f = min(1.6, l / 0.42)
            elif 'rambut' in cache and ((l < 0.24 and max(r, g, b) - min(r, g, b) < 0.045)
                                        or b > r * 1.15):
                # kebiruan di tekstur kepala = topi bawaan TSO; ikut warna rambut
                t = cache['rambut']; f = 0.6 + l * 1.6
            elif tp is not None and tp[x, y] in cache:
                t = cache[tp[x, y]]; f = 0.45 + l * 1.1
            else:
                continue
            px[x, y] = (min(255, int(t[0] * f * 255)), min(255, int(t[1] * f * 255)),
                        min(255, int(t[2] * f * 255)), a)
    return img


def terapkan(char_actor, state):
    """Terapkan char_skin/hair/shirt/pants/hat ke CharActor pemain."""
    if char_actor is None:
        return
    a = char_actor.actor
    kulit = KULIT[getattr(state, 'char_skin', 0) % len(KULIT)][1]
    rambut = RAMBUT[getattr(state, 'char_hair', 0) % len(RAMBUT)][1]
    baju = BAJU[getattr(state, 'char_shirt', 0) % len(BAJU)][1]
    celana = CELANA[getattr(state, 'char_pants', 0) % len(CELANA)][1]
    asli = char_actor.__dict__.setdefault('_tekstur_asli', {})
    for gnp in a.findAllMatches('**/+GeomNode'):
        nama = gnp.getName()
        texs = gnp.findAllTextures()
        if not texs:
            continue
        tex = texs[0]
        if nama not in asli:
            asli[nama] = (_ke_pil(tex), tex)
        src, _ = asli[nama]
        if src is None:
            continue
        if 'body' in nama:
            if '_topeng' not in char_actor.__dict__:
                lo, hi = a.getTightBounds()
                pinggul = lo.y + (hi.y - lo.y) * 0.52
                char_actor._topeng = _gambar_topeng(_segitiga(gnp), src.width, src.height, pinggul)
            img = _warnai(src.copy(), char_actor._topeng, {'kulit': kulit, 1: baju, 2: celana})
        elif 'head' in nama:
            img = _warnai(src.copy(), None, {'kulit': kulit, 'rambut': rambut})
        else:
            continue
        # TextureStage ASLI: stage bawaan membaca kolom 'texcoord', padahal UV
        # glTF ada di 'texcoord.0' -- seluruh badan lalu mencuplik satu piksel
        # pojok dan tampil satu warna rata.
        stages = gnp.findAllTextureStages()
        if stages:
            gnp.setTexture(stages[0], _dari_pil(img, nama + '_rupa'), 1)
        else:
            gnp.setTexture(_dari_pil(img, nama + '_rupa'), 1)
    # tangan tanpa tekstur: warna kulit
    from panda3d.core import ColorAttrib
    for gnp in a.findAllMatches('**/+GeomNode'):
        if gnp.getName() == 'Mesh' and not gnp.findAllTextures():
            # prioritas 1: warna material tangan dipanggang di level geom
            gnp.setColor(kulit[0] / 255.0, kulit[1] / 255.0, kulit[2] / 255.0, 1, 1)
    pasang_aksesori(char_actor, AKSESORI[getattr(state, 'char_hat', 0) % len(AKSESORI)][1])


# ─── aksesori kepala ──────────────────────────────────────────────────────
def _kepala_bounds(a):
    """(pusat_x, puncak_y, pusat_z, lebar) kepala dalam ruang aktor."""
    for gnp in a.findAllMatches('**/+GeomNode'):
        if 'head' in gnp.getName():
            lo, hi = gnp.getTightBounds(a)
            return ((lo.x + hi.x) / 2, hi.y, (lo.z + hi.z) / 2, hi.x - lo.x, hi.y - lo.y)
    lo, hi = a.getTightBounds()
    return (0, hi.y, 0, 0.2, 0.25)


def pasang_aksesori(char_actor, jenis):
    from ursina import Entity, color, Mesh
    from ursina.models.procedural.cone import Cone
    from ursina.models.procedural.cylinder import Cylinder
    a = char_actor.actor
    # caping panggaan dari Blender disembunyikan: pilihan pemain yang menang
    for nm in ('Cone', 'Torus'):
        for np in a.findAllMatches(f'**/{nm}'):
            np.hide()
    lama = getattr(char_actor, '_aksesori', None)
    if lama is not None:
        lama.removeNode()
    char_actor._aksesori = None
    if jenis is None:
        return
    cx, top, cz, lebar, tinggi = _kepala_bounds(a)
    kar = a.find('**/+Character')
    sendi = a.exposeJoint(kar.attachNewNode('kepala_aks'), 'modelRoot', 'HEAD')
    akar = NodePath('aksesori')
    akar.reparentTo(a)
    # Ruang aktor: Y atas. Dasar topi duduk sedikit di bawah puncak kepala
    # supaya mahkotanya MENUTUP ubun-ubun, bukan bertengger di atasnya.
    r = lebar * 0.5
    dasar = top - tinggi * 0.22

    def bagian(model, pos, skala, rgb, rot=(0, 0, 0)):
        e = Entity(model=model, color=color.rgb(*rgb))
        e.reparentTo(akar)
        e.setPos(pos[0], pos[1], pos[2])
        e.setScale(*skala)
        e.setHpr(*rot)
        return e

    if jenis == 'caping':
        bagian(Cone(16, height=1, radius=1), (cx, dasar, cz), (r * 2.7, tinggi * 0.55, r * 2.7), (200, 172, 110))
    elif jenis == 'bucket':
        bagian(Cylinder(16, start=0, height=1, radius=1), (cx, dasar, cz), (r * 1.12, tinggi * 0.42, r * 1.12), (98, 104, 70))
        bagian(Cone(16, height=1, radius=1), (cx, dasar - tinggi * 0.04, cz), (r * 1.9, tinggi * 0.18, r * 1.9), (98, 104, 70))
    elif jenis == 'peci':
        bagian(Cylinder(16, start=0, height=1, radius=1), (cx, dasar + tinggi * 0.02, cz), (r * 1.06, tinggi * 0.36, r * 0.92), (30, 30, 34))
    elif jenis == 'ikat':
        bagian(Cylinder(16, start=0, height=1, radius=1), (cx, top - tinggi * 0.38, cz), (r * 1.08, tinggi * 0.12, r * 1.08), (150, 70, 52))
    elif jenis == 'koboi':
        bagian(Cylinder(18, start=0, height=1, radius=1), (cx, dasar, cz), (r * 2.1, tinggi * 0.05, r * 1.8), (110, 76, 50))
        bagian(Cylinder(16, start=0, height=1, radius=1), (cx, dasar, cz), (r * 1.0, tinggi * 0.5, r * 0.85), (110, 76, 50))
    akar.wrtReparentTo(sendi)
    char_actor._aksesori = akar
