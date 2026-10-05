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
    """peta: {nilai_topeng|'kulit'|'rambut': rgb}. Mengembalikan gambar baru.

    Vektor numpy: loop per piksel Python memakan ~0,3 s per tekstur 256 px,
    terlalu mahal kalau tiap warga di scene ikut diwarnai saat scene dimuat.
    """
    import numpy as np
    from PIL import Image
    a = np.asarray(img.convert('RGBA'), dtype=np.float32) / 255.0
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    l = 0.299 * r + 0.587 * g + 0.114 * b
    out = a.copy()
    sudah = np.zeros(l.shape, bool)

    def isi(mask, rgb, f):
        t = np.array(rgb, np.float32) / 255.0
        m = mask & ~sudah
        for k in range(3):
            out[..., k][m] = np.clip(t[k] * f[m], 0, 1)
        return sudah | m

    if 'kulit' in peta:
        kulit = (r > g * 1.06) & (g > b * 1.02) & (r > 0.06) & (b >= r * 0.26) & ((r - b) > 0.025)
        acuan = peta.get('_acuan')
        t = np.array(peta['kulit'], np.float32) / 255.0
        if acuan is not None:
            # Bobot LEMBUT menurut jarak kroma ke kulit asli warga ini: batas
            # tegas membuat kulit belang-belang (sebagian piksel tercelup,
            # tetangganya tidak), sedangkan uji generik saja ikut mencelup
            # kain cokelat/jingga (mantel Kapten, baju Maya).
            jum = r + g + b + 1e-5
            ar, ag, ab_, al = acuan
            aj = ar + ag + ab_ + 1e-5
            jarak = np.abs(r / jum - ar / aj) + np.abs(g / jum - ag / aj)
            kulit_longgar = (r > g * 0.98) & (g > b * 0.95) & (b >= r * 0.2)
            w = np.clip(1.0 - (jarak - 0.06) / 0.14, 0, 1)
            w *= np.clip((l - al * 0.15) / (al * 0.2), 0, 1)
            w *= kulit_longgar
            # diburamkan: bayangan dan noda di kulit TSO punya kroma sedikit
            # lain, dan tanpa ini mereka tertinggal sebagai bintik gelap.
            from PIL import Image as _I, ImageFilter as _F
            wi = _I.fromarray((w * 255).astype(np.uint8), 'L').filter(_F.GaussianBlur(1.6))
            w = np.minimum(1.0, np.asarray(wi, np.float32) / 255.0 * 1.25)
            f = np.minimum(1.25, l / max(al, 1e-3))   # di atas ini kulit terang jadi putih kapur
        else:
            m = l[kulit]
            f = np.minimum(1.7, l / (float(np.median(m)) if m.size else 0.42))
            w = kulit.astype(np.float32)
        for k in range(3):
            baru = np.clip(t[k] * f, 0, 1)
            out[..., k] = out[..., k] * (1 - w) + baru * w
        sudah = sudah | (w > 0.5)
    if 'rambut' in peta:
        sat = a[..., :3].max(-1) - a[..., :3].min(-1)
        rambut = ((l < 0.24) & (sat < 0.045)) | (b > r * 1.15)
        sudah = isi(rambut, peta['rambut'], 0.6 + l * 1.6)
    if topeng is not None:
        tp = np.asarray(topeng)
        for nilai, rgb in peta.items():
            if isinstance(nilai, int) and not isinstance(nilai, bool):
                sudah = isi(tp == nilai, rgb, 0.45 + l * 1.1)
    return Image.fromarray((out * 255).astype(np.uint8), 'RGBA')


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
            img = wajah_chibi(img, 'pemain', rambut, kulit=kulit)
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
    besarkan_kepala(char_actor)
    pasang_aksesori(char_actor, AKSESORI[getattr(state, 'char_hat', 0) % len(AKSESORI)][1])


# ─── aksesori kepala ──────────────────────────────────────────────────────
def _kepala_bounds(a):
    """(pusat_x, puncak_y, pusat_z, lebar) kepala dalam ruang aktor."""
    # Kepala = node 'head' TERTINGGI yang tampil. Node pertama bisa saja
    # kacamata TSO (5 cm) -- peci Pak Hadi lalu terpasang setinggi mata.
    calon = []
    for gnp in a.findAllMatches('**/+GeomNode'):
        if 'head' in gnp.getName() and not gnp.isHidden():
            lo, hi = gnp.getTightBounds(a)
            calon.append((hi.y - lo.y, lo, hi))
    if calon:
        _t, lo, hi = max(calon, key=lambda c: c[0])
        return ((lo.x + hi.x) / 2, hi.y, (lo.z + hi.z) / 2, hi.x - lo.x, hi.y - lo.y)
    lo, hi = a.getTightBounds()
    return (0, hi.y, 0, 0.2, 0.25)


def _sembunyikan_topi_panggang(a, kepala_tengah):
    """Penutup kepala hasil Blender (Cone/Torus/Cylinder/... di atas kepala)
    disembunyikan: posisinya dihitung dari pose istirahat dan sering melayang
    beberapa senti di atas rambut. Kerudung dan aksesori badan dibiarkan."""
    for gnp in a.findAllMatches('**/+GeomNode'):
        nm = gnp.getName()
        if any(k in nm for k in ('head', 'hair', 'body', 'kerudung', 'Mesh', 'mesh_geom')):
            continue
        if gnp.findAllTextures():
            continue
        try:
            lo, hi = gnp.getTightBounds(a)
        except Exception:
            continue
        if (lo.y + hi.y) / 2 > kepala_tengah:
            gnp.hide()


def pasang_aksesori(char_actor, jenis, warna=None, skala=1.0):
    import math
    from ursina import Entity, color
    from ursina.models.procedural.cone import Cone
    from ursina.models.procedural.cylinder import Cylinder
    a = char_actor.actor
    lama = getattr(char_actor, '_aksesori', None)
    if lama is not None:
        lama.removeNode()
    char_actor._aksesori = None
    cx, top, cz, lebar, tinggi = _kepala_bounds(a)
    # Topi panggang selalu disembunyikan pada pemain (pilihan chargen yang
    # menang) dan pada warga yang diberi topi runtime.
    # batas seperempat bawah kepala: peci Blender Pak Hadi jatuh setinggi mata
    _sembunyikan_topi_panggang(a, top - tinggi * 0.75)
    if jenis is None:
        return
    kar = a.find('**/+Character')
    sendi = a.exposeJoint(kar.attachNewNode('kepala_aks'), 'modelRoot', 'HEAD')
    akar = NodePath('aksesori')
    akar.reparentTo(a)
    # Ruang aktor: Y atas. Dasar topi duduk di bawah puncak kepala supaya
    # mahkotanya MENUTUP ubun-ubun, bukan bertengger di atasnya.
    r = lebar * 0.5 * skala
    # 0,3: rambut TSO yang jabrik/bersanggul menonjol di atas mesh kepala;
    # topi harus sedikit menekannya, bukan bertengger di ujungnya.
    dasar = top - tinggi * 0.3

    def bagian(model, pos, sk, rgb, rot=(0, 0, 0)):
        e = Entity(model=model, color=color.rgb(*rgb))
        e.reparentTo(akar)
        e.setPos(pos[0], pos[1], pos[2])
        e.setScale(*sk)
        e.setHpr(*rot)
        return e

    def W(bawaan):
        return warna or bawaan

    if jenis == 'caping':
        # kerucut anyaman + pita tepi tipis
        bagian(Cone(20, height=1, radius=1), (cx, top - tinggi * 0.2, cz), (r * 2.7, tinggi * 0.55 * skala, r * 2.7), W((200, 172, 110)))
        bagian(Cylinder(20, start=0, height=1, radius=1), (cx, top - tinggi * 0.21, cz), (r * 2.72, tinggi * 0.02, r * 2.72), (150, 120, 70))
    elif jenis == 'bucket':
        bagian(Cylinder(16, start=0, height=1, radius=1), (cx, dasar, cz), (r * 1.12, tinggi * 0.3, r * 1.12), W((98, 104, 70)))
        bagian(Cone(16, height=1, radius=1), (cx, dasar - tinggi * 0.04, cz), (r * 1.9, tinggi * 0.18, r * 1.9), W((98, 104, 70)))
    elif jenis == 'peci':
        bagian(Cylinder(18, start=0, height=1, radius=1), (cx, dasar + tinggi * 0.02, cz), (r * 1.06, tinggi * 0.28, r * 0.92), W((30, 30, 34)))
        bagian(Cylinder(18, start=0, height=1, radius=1), (cx, dasar + tinggi * 0.02, cz), (r * 1.075, tinggi * 0.025, r * 0.935), (64, 56, 46))
    elif jenis == 'ikat':
        bagian(Cylinder(16, start=0, height=1, radius=1), (cx, top - tinggi * 0.38, cz), (r * 1.08, tinggi * 0.12, r * 1.08), W((150, 70, 52)))
    elif jenis == 'koboi':
        # tepi lebar, mahkota rendah berlekuk, pita kulit gelap
        bagian(Cylinder(20, start=0, height=1, radius=1), (cx, dasar, cz), (r * 2.05, tinggi * 0.035, r * 1.7), W((110, 76, 50)))
        bagian(Cylinder(16, start=0, height=1, radius=1), (cx, dasar, cz), (r * 0.98, tinggi * 0.34, r * 0.84), W((110, 76, 50)))
        bagian('sphere', (cx, dasar + tinggi * 0.34, cz), (r * 1.9, tinggi * 0.14, r * 1.6), W((110, 76, 50)))
        bagian(Cylinder(16, start=0, height=1, radius=1), (cx, dasar + tinggi * 0.03, cz), (r * 1.0, tinggi * 0.07, r * 0.86), (46, 32, 24))
    elif jenis == 'baret':
        bagian('sphere', (cx + r * 0.15, top - tinggi * 0.06, cz), (r * 2.3, tinggi * 0.3, r * 2.2), W((150, 52, 60)))
    elif jenis == 'bandana':
        bagian('sphere', (cx, top - tinggi * 0.2, cz), (r * 2.12, tinggi * 0.62, r * 2.15), W((170, 44, 40)))
    elif jenis == 'tricorn':
        # Topi bajak laut: mahkota hitam yang MENUTUP seluruh ubun-ubun (tricorn
        # pipih lama membiarkan kubah kepala putih menyembul, kepala dan topi
        # terbaca terpisah), tepi lebar dilipat naik, pita emas, tengkorak.
        hitam = W((26, 24, 28))
        bagian(Cylinder(18, start=0, height=1, radius=1), (cx, dasar - tinggi * 0.04, cz), (r * 1.14, tinggi * 0.5, r * 1.1), hitam)
        bagian('sphere', (cx, dasar + tinggi * 0.44, cz), (r * 2.25, tinggi * 0.3, r * 2.15), hitam)
        bagian(Cylinder(24, start=0, height=1, radius=1), (cx, dasar - tinggi * 0.04, cz), (r * 2.0, tinggi * 0.035, r * 1.85), hitam)
        for sx in (-1, 1):
            bagian(Cylinder(12, start=0, height=1, radius=1), (cx + sx * r * 1.45, dasar + tinggi * 0.1, cz),
                   (r * 0.62, tinggi * 0.035, r * 1.55), hitam, rot=(0, 0, sx * -55))
        bagian(Cylinder(18, start=0, height=1, radius=1), (cx, dasar + tinggi * 0.02, cz), (r * 1.16, tinggi * 0.06, r * 1.12), (196, 160, 70))
        # tengkorak di depan (glTF menghadap -Z ruang aktor)
        bagian('sphere', (cx, dasar + tinggi * 0.28, cz - r * 1.12), (r * 0.36, r * 0.32, r * 0.08), (236, 232, 220))
        for sx in (-1, 1):
            bagian('sphere', (cx + sx * r * 0.11, dasar + tinggi * 0.29, cz - r * 1.18), (r * 0.08, r * 0.08, r * 0.04), (26, 24, 28))
    elif jenis == 'pita':
        for sx in (-1, 1):
            bagian('sphere', (cx + sx * r * 0.45, top - tinggi * 0.02, cz + r * 0.5), (r * 0.55, tinggi * 0.18, r * 0.25), W((222, 92, 120)))
    elif jenis == 'mahkota':
        for k, (rr, hh) in enumerate(((1.08, 0.2), (0.85, 0.2), (0.55, 0.22))):
            bagian(Cylinder(10, start=0, height=1, radius=1), (cx, dasar + tinggi * (0.02 + 0.18 * k), cz), (r * rr, tinggi * hh, r * rr), W((214, 172, 72)))
    elif jenis == 'mahkota_bunga':
        for k in range(8):
            t = k / 8 * math.tau
            bagian('sphere', (cx + math.cos(t) * r * 1.0, top - tinggi * 0.12, cz + math.sin(t) * r * 1.0),
                   (r * 0.38, r * 0.38, r * 0.38), W((240, 214, 120)) if k % 2 else (226, 140, 170))
    akar.wrtReparentTo(sendi)
    char_actor._aksesori = akar


# --- warga desa ---------------------------------------------------------------
# Semua tekstur kepala TSO berkulit cokelat sampai gelap, jadi seluruh desa
# terbaca satu suku. Warna kulit tiap warga mengikuti keragaman Nusantara.
KULIT_NPC = {
    'raka': (226, 188, 156),        # Tionghoa-Indonesia
    'kapten_kuro': (220, 184, 150), # Jepang
    'sari': (214, 170, 130),        # Sunda
    'cici': (220, 176, 138),        # Sunda
    'maya': (196, 142, 102),        # Bali
    'pak_guru': (192, 138, 100),    # Minang
    'kru_kuro': (184, 140, 98),     # Arab-Indonesia
    'joko': (170, 118, 82),         # Bugis
    'bowo': (164, 112, 78),         # Jawa
    'arya': (158, 106, 74),         # Batak
    'budi': (136, 90, 62),          # Jawa
    'mbok_jum': (142, 98, 70),      # Jawa
    'jaka_ronda': (110, 72, 50),    # Ambon
    'ningsih': (92, 60, 42),        # Papua
    'bidadari': (236, 214, 196),
    'dewa_angin': (206, 170, 136),
}
# (jenis, warna atau None, skala)
TOPI_NPC = {
    'ningsih': ('caping', None, 1.0), 'bowo': ('caping', None, 0.85),
    'budi': ('koboi', None, 1.0), 'joko': ('bucket', None, 1.0),
    'arya': ('bucket', (120, 84, 50), 1.0), 'maya': ('baret', None, 1.0),
    'pak_guru': ('peci', None, 1.0), 'jaka_ronda': ('peci', None, 1.0),
    'kapten_kuro': ('tricorn', None, 1.0), 'kru_kuro': ('bandana', None, 1.0),
    'cici': ('pita', None, 1.0), 'dewa_angin': ('mahkota', None, 1.0),
    'bidadari': ('mahkota_bunga', None, 1.0),
}

_CACHE_TEKSTUR = {}

# Kepala sedikit diperbesar lewat sendi HEAD. Versi chibi lama memakai 2,90x
# dan terbaca kebesaran; ini cukup untuk proporsi ramah tanpa jadi boneka.
SKALA_KEPALA = 1.16


# Iris cokelat tua yang wajar untuk warga Nusantara; satu dua yang lebih terang.
_IRIS_NUSANTARA = ((58, 38, 28), (72, 46, 30), (46, 32, 26), (88, 60, 38), (40, 30, 30))


def wajah_chibi(src, kunci, rambut=None, kulit=None):
    """Lukis wajah chibi (game/wajah.py) ke tekstur kepala TSO.

    Struktur muka dari versi kepala chibi -- mata besar berkilau, hidung
    titik, mulut kecil, alis berkarakter, variasi per orang -- tapi mata
    diperkecil dan dipipihkan sedikit supaya tidak melotot pada kepala yang
    tidak lagi 2,9x.
    """
    from .wajah import lukis_wajah_chibi, varian_wajah
    v = dict(varian_wajah(kunci))
    v['mata_global'] = 0.68
    v['mata_pipih'] = 0.84
    v['iris'] = _IRIS_NUSANTARA[sum(map(ord, kunci)) % len(_IRIS_NUSANTARA)]
    if kulit is not None:
        v['kulit_tetap'] = kulit
    v['lewati_rambut'] = True
    if rambut is not None:
        v['rambut'] = rambut
    return lukis_wajah_chibi(src.convert('RGB'), v).convert('RGBA')


def besarkan_kepala(char_actor, skala=SKALA_KEPALA):
    a = char_actor.actor
    if getattr(char_actor, '_kepala_dikendali', None) is not None:
        return
    try:
        j = a.controlJoint(None, 'modelRoot', 'HEAD')
        j.setScale(skala)
        char_actor._kepala_dikendali = j
    except Exception:
        char_actor._kepala_dikendali = None
# Warga yang pakaiannya SEWARNA kulit aslinya (mantel cokelat Kapten): tekstur
# badannya tidak dicelup, cukup wajah dan tangan -- lengannya tertutup kain.
_KULIT_WAJAH_SAJA = {'kapten_kuro'}


def _acuan_kulit(a):
    """(r, g, b, luma) median kulit dari tekstur KEPALA warga ini."""
    import numpy as np
    for gnp in a.findAllMatches('**/+GeomNode'):
        if 'head' not in gnp.getName():
            continue
        texs = gnp.findAllTextures()
        if not texs:
            continue
        img = _ke_pil(texs[0])
        if img is None:
            continue
        x = np.asarray(img.convert('RGB'), np.float32) / 255.0
        r, g, b = x[..., 0], x[..., 1], x[..., 2]
        m = (r > g * 1.06) & (g > b * 1.02) & (r > 0.06) & (b >= r * 0.26)
        if m.sum() < 30:
            continue
        rr, gg, bb = float(np.median(r[m])), float(np.median(g[m])), float(np.median(b[m]))
        return (rr, gg, bb, 0.299 * rr + 0.587 * gg + 0.114 * bb)
    return None


def terapkan_npc(char_actor, npc_id):
    """Warna kulit sesuai suku + topi yang diukur dari kepala sungguhan."""
    if char_actor is None:
        return
    a = char_actor.actor
    kulit = KULIT_NPC.get(npc_id)
    if npc_id == 'pak_guru':
        # kepala TSO-nya membawa kacamata las sebagai mesh '_head' yang pendek
        kepala = [g for g in a.findAllMatches('**/+GeomNode') if 'head' in g.getName()]
        if len(kepala) > 1:
            def _t(g):
                lo, hi = g.getTightBounds(a)
                return hi.y - lo.y
            min(kepala, key=_t).hide()
    acuan = _acuan_kulit(a) if kulit is not None else None
    if kulit is not None:
        for gnp in a.findAllMatches('**/+GeomNode'):
            texs = gnp.findAllTextures()
            nama = gnp.getName()
            if not texs:
                if nama == 'Mesh':
                    gnp.setColor(kulit[0] / 255.0, kulit[1] / 255.0, kulit[2] / 255.0, 1, 1)
                continue
            if 'body' in nama and npc_id in _KULIT_WAJAH_SAJA:
                continue
            kunci = (npc_id, nama)
            tex = _CACHE_TEKSTUR.get(kunci)
            if tex is None:
                src = _ke_pil(texs[0])
                if src is None:
                    continue
                # Kulit dicelup DULU, wajah chibi dilukis di atasnya: urutan
                # sebaliknya membuat celup (berbobot kabur) melunturkan mata.
                img = _warnai(src, None, {'kulit': kulit, '_acuan': acuan})
                # Mesh '_hair' TSO adalah cangkang kepala utuh yang teksturnya ikut
                # memuat lukisan wajah lama -- tanpa ini Maya dkk. tetap berwajah TSO.
                if ('head' in nama or 'hair' in nama) and not gnp.isHidden():
                    img = wajah_chibi(img, npc_id, kulit=kulit)
                tex = _dari_pil(img, f'{npc_id}_{nama}_kulit')
                _CACHE_TEKSTUR[kunci] = tex
            stages = gnp.findAllTextureStages()
            if stages:
                gnp.setTexture(stages[0], tex, 1)
    besarkan_kepala(char_actor)
    topi = TOPI_NPC.get(npc_id)
    if topi is not None:
        pasang_aksesori(char_actor, topi[0], topi[1], topi[2])
