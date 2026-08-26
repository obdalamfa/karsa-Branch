"""
tool_models.py — Alat yang benar-benar dipegang karakter, dibangun prosedural.

Kenapa modul ini ada: sebelumnya HUD cuma menulis kata "Cangkul" di pojok kiri
atas sementara tangan karakter kosong. Label bukan benda — pemain tidak melihat
apa yang sedang dipegang, dan animasi "memakai alat" tidak punya objek untuk
diayunkan sehingga gerakannya tidak terbaca. Di sini tiap alat jadi geometri
nyata dalam satuan METER terhadap karakter setinggi ~1,76 m, chunky supaya tetap
terbaca dari jarak kamera isometrik ala FreeSO.

PENTING — bug NodePath ganda (sudah menggigit proyek ini dua kali):
    Mesh Ursina adalah NodePath Panda3D dan sebuah NodePath cuma boleh punya SATU
    parent. Karena itu modul ini sengaja TIDAK men-cache satu pun Mesh: `_prism()`
    membangun Mesh baru setiap dipanggil, jadi dua alat yang hidup bersamaan
    (mis. alat di tangan pemain dan alat di tangan NPC) tidak saling mencuri
    geometri. Kalau nanti ada yang menambahkan cache di sini, WAJIB kembalikan
    salinan lewat `meshes._instance()` — bukan objek cache-nya langsung.

Konvensi orientasi lokal tiap alat (dipakai oleh player._tool_pivot):
    origin (0,0,0) = titik genggam, tepat di dalam kepalan tangan
    -Y             = arah ujung kerja (mata cangkul, kepala kapak, ujung joran)
    +Y             = pangkal/ujung gagang di belakang tangan
    +Z             = arah muka alat menghadap (searah depan karakter)
"""
from __future__ import annotations
import math

from ursina import Entity, Mesh, Vec3, color

from .smooth_shader import apply_smooth

# ─── PALET (muted earth ala DESIGN_STANDARD, bukan warna neon) ───────────────
KAYU       = color.rgb(150, 112,  72)   # gagang jati/asam
KAYU_TUA   = color.rgb(104,  76,  48)
BAMBU      = color.rgb(198, 176, 118)
BAMBU_TUA  = color.rgb(150, 128,  78)
BESI       = color.rgb(104, 110, 118)
BESI_TUA   = color.rgb( 68,  72,  80)
BESI_KILAP = color.rgb(178, 186, 194)
SENG       = color.rgb(148, 156, 154)   # gembor galvanis
SENG_TUA   = color.rgb(108, 118, 118)
TALI       = color.rgb(196, 172, 124)
ANYAM      = color.rgb(196, 162, 104)   # bakul bambu
ANYAM_TUA  = color.rgb(148, 116,  68)
KAIN       = color.rgb(142, 108,  84)
DAUN       = color.rgb( 96, 134,  70)
BUAH       = color.rgb(204, 132,  58)
KADO       = color.rgb(168,  82,  80)
PITA       = color.rgb(226, 198, 124)
PELAMPUNG  = color.rgb(206,  78,  62)
SENAR      = color.rgb(232, 230, 214)


# ─── GEOMETRI DASAR ─────────────────────────────────────────────────────────
def _prism(sides: int = 8, r_bot: float = 0.5, r_top: float | None = None,
           height: float = 1.0, cap_bottom: bool = True, cap_top: bool = True):
    """Prisma n-sisi sepanjang sumbu Y, terpusat di origin, satuan meter.

    Satu generator ini melayani gagang (silinder), corong (taper), dan ujung
    runcing (r_top=0) sekaligus. Normal dibuat per-muka (flat), bukan dihaluskan
    — faset yang kelihatan justru yang bikin alat terbaca chunky ala FreeSO.

    Urutan segitiga mengikuti konvensi menang-hadap Ursina (lihat
    ursina/models/procedural/cone.py): ring berjalan mundur relatif terhadap
    sudut yang menaik.
    """
    if r_top is None:
        r_top = r_bot
    hy = height * 0.5
    ring = [(math.cos(2.0 * math.pi * i / sides),
             math.sin(2.0 * math.pi * i / sides)) for i in range(sides)]

    verts: list = []
    norms: list = []
    tris: list = []

    # Kemiringan normal akibat taper: makin mengecil ke atas, normal makin ke atas
    ny = (r_bot - r_top) / max(height, 1e-6)

    for i in range(sides):
        cx, cz = ring[i]
        nx, nz = ring[(i + 1) % sides]
        b0 = Vec3(cx * r_bot, -hy, cz * r_bot)
        b1 = Vec3(nx * r_bot, -hy, nz * r_bot)
        t0 = Vec3(cx * r_top,  hy, cz * r_top)
        t1 = Vec3(nx * r_top,  hy, nz * r_top)
        mx, mz = (cx + nx) * 0.5, (cz + nz) * 0.5
        ln = math.sqrt(mx * mx + ny * ny + mz * mz) or 1.0
        n = Vec3(mx / ln, ny / ln, mz / ln)
        b = len(verts)
        verts += [b1, b0, t0, t1]
        norms += [n, n, n, n]
        tris += [b, b + 1, b + 2, b, b + 2, b + 3]

    if cap_bottom and r_bot > 1e-6:
        cb = len(verts)
        verts.append(Vec3(0, -hy, 0))
        norms.append(Vec3(0, -1, 0))
        for i in range(sides):
            cx, cz = ring[i]
            nx, nz = ring[(i + 1) % sides]
            b = len(verts)
            verts += [Vec3(nx * r_bot, -hy, nz * r_bot),
                      Vec3(cx * r_bot, -hy, cz * r_bot)]
            norms += [Vec3(0, -1, 0), Vec3(0, -1, 0)]
            tris += [b, cb, b + 1]

    if cap_top and r_top > 1e-6:
        ct = len(verts)
        verts.append(Vec3(0, hy, 0))
        norms.append(Vec3(0, 1, 0))
        for i in range(sides):
            cx, cz = ring[i]
            nx, nz = ring[(i + 1) % sides]
            b = len(verts)
            verts += [Vec3(cx * r_top, hy, cz * r_top),
                      Vec3(nx * r_top, hy, nz * r_top)]
            norms += [Vec3(0, 1, 0), Vec3(0, 1, 0)]
            tris += [b, ct, b + 1]

    return Mesh(vertices=verts, triangles=tris, normals=norms,
                uvs=[Vec3(0, 0, 0).xy for _ in verts], mode='triangle')


def _box(parent, pos, scale, col, rot=(0, 0, 0)):
    """Balok chunky. 'cube' adalah nama model bawaan Ursina — load_model()
    mengembalikan salinan tiap kali, jadi aman dipakai banyak Entity."""
    e = Entity(parent=parent, model='cube', position=Vec3(*pos),
               scale=Vec3(*scale), rotation=rot, color=col)
    apply_smooth(e, has_texture=False)
    return e


def _rod(parent, pos, col, sides=8, r_bot=0.02, r_top=None, height=1.0,
         rot=(0, 0, 0)):
    """Batang/prisma. Mesh dibuat baru — jangan pernah di-cache (lihat header)."""
    e = Entity(parent=parent,
               model=_prism(sides, r_bot, r_top, height),
               position=Vec3(*pos), rotation=rot, color=col)
    apply_smooth(e, has_texture=False)
    return e


# ─── ALAT ───────────────────────────────────────────────────────────────────
def _build_cangkul(r):
    """Cangkul Jawa: gagang lurus 1,15 m, mata besi lebar dipasang ~70°."""
    _rod(r, (0, -0.275, 0), KAYU, 8, 0.023, 0.020, 1.15)     # gagang
    _rod(r, (0,  0.000, 0), KAYU_TUA, 8, 0.028, 0.028, 0.15)  # lilitan genggam
    _rod(r, (0, -0.845, 0), KAYU_TUA, 8, 0.026, 0.026, 0.06)  # baji pangkal
    # Kelopak/sok besi tempat mata ditancapkan
    _box(r, (0, -0.885, 0.020), (0.070, 0.085, 0.075), BESI_TUA, rot=(20, 0, 0))
    # Mata cangkul: pelat lebar miring ke depan-bawah
    _box(r, (0, -0.962, 0.088), (0.235, 0.205, 0.028), BESI, rot=(72, 0, 0))
    # Bibir mata yang mengkilap — ini yang bikin siluetnya kebaca dari jauh
    _box(r, (0, -0.994, 0.182), (0.238, 0.055, 0.016), BESI_KILAP, rot=(72, 0, 0))


def _build_penyiram(r):
    """Gembor seng: badan silinder, corong panjang, kepala percik bundar."""
    _rod(r, (0, -0.205, 0), SENG, 12, 0.118, 0.108, 0.255)    # badan
    _rod(r, (0, -0.338, 0), SENG_TUA, 12, 0.122, 0.122, 0.030)  # kaki
    _rod(r, (0, -0.068, 0), SENG_TUA, 12, 0.110, 0.096, 0.030)  # tutup
    _rod(r, (0, -0.040, 0), SENG_TUA, 8, 0.030, 0.024, 0.040)   # leher isi
    # Busur pegangan atas — inilah yang digenggam, jadi tepat di y=0
    _box(r, (-0.072, -0.030, 0), (0.020, 0.075, 0.024), SENG_TUA)
    _box(r, ( 0.072, -0.030, 0), (0.020, 0.075, 0.024), SENG_TUA)
    _box(r, ( 0.000,  0.008, 0), (0.180, 0.022, 0.026), SENG)
    # Pegangan belakang untuk memiringkan
    _box(r, (0, -0.150, -0.135), (0.024, 0.150, 0.022), SENG_TUA, rot=(14, 0, 0))
    # Corong naik ke depan, lalu kepala percik
    _rod(r, (0, -0.175, 0.185), SENG, 8, 0.036, 0.024, 0.300, rot=(64, 0, 0))
    _rod(r, (0, -0.075, 0.318), SENG_TUA, 10, 0.058, 0.050, 0.028, rot=(64, 0, 0))


def _build_kapak(r):
    """Kapak kayu bakar: gagang 0,70 m, kepala baji dengan bibir terang."""
    _rod(r, (0, -0.170, 0), KAYU, 8, 0.024, 0.020, 0.700)
    _rod(r, (0,  0.000, 0), KAYU_TUA, 8, 0.029, 0.029, 0.130)   # genggam
    _rod(r, (0,  0.172, 0), KAYU_TUA, 8, 0.028, 0.032, 0.030)   # knop pangkal
    _box(r, (0, -0.508, -0.012), (0.064, 0.130, 0.090), BESI_TUA)   # mata/poll
    _box(r, (0, -0.508,  0.092), (0.054, 0.165, 0.140), BESI)       # badan baji
    _box(r, (0, -0.508,  0.182), (0.026, 0.205, 0.042), BESI_KILAP) # bibir tajam


def _build_beliung(r):
    """Beliung/pickaxe: satu ujung runcing, satu ujung pahat."""
    _rod(r, (0, -0.200, 0), KAYU, 8, 0.024, 0.020, 0.800)
    _rod(r, (0,  0.000, 0), KAYU_TUA, 8, 0.029, 0.029, 0.140)
    _box(r, (0, -0.596, 0), (0.080, 0.120, 0.082), BESI_TUA)
    # Lengan runcing ke depan (+Z) — melengkung lewat dua ruas
    _rod(r, (0, -0.586, 0.118), BESI, 6, 0.038, 0.026, 0.200, rot=(90, 0, 0))
    _rod(r, (0, -0.548, 0.268), BESI, 6, 0.026, 0.003, 0.170, rot=(104, 0, 0))
    # Lengan pahat ke belakang (-Z)
    _rod(r, (0, -0.586, -0.112), BESI, 6, 0.038, 0.028, 0.190, rot=(90, 0, 0))
    _box(r, (0, -0.578, -0.232), (0.062, 0.038, 0.070), BESI_KILAP, rot=(-10, 0, 0))


def _build_pedang(r):
    """Golok/pedang desa: bilah 0,62 m dengan alur tengah yang menangkap cahaya."""
    _rod(r, (0, 0.000, 0), KAYU_TUA, 6, 0.023, 0.021, 0.135)    # gagang
    _box(r, (0, 0.086, 0), (0.048, 0.038, 0.048), BESI_TUA)     # bonggol
    _box(r, (0, -0.080, 0), (0.150, 0.026, 0.048), BESI)        # pelindung
    _box(r, (0, -0.395, 0), (0.056, 0.600, 0.017), BESI_KILAP)  # bilah
    _box(r, (0, -0.395, 0), (0.020, 0.560, 0.024), BESI)        # alur/fuller
    _rod(r, (0, -0.735, 0), BESI_KILAP, 4, 0.030, 0.002, 0.090, rot=(0, 45, 0))


def _build_pancing(r):
    """Joran bambu 1,45 m yang meruncing, plus senar dan pelampung."""
    _rod(r, (0,  0.000, 0), TALI,      8, 0.026, 0.024, 0.170)  # lilitan rotan
    _rod(r, (0, -0.330, 0), BAMBU,     8, 0.022, 0.016, 0.520)
    _rod(r, (0, -0.595, 0), BAMBU_TUA, 8, 0.017, 0.017, 0.026)  # ruas
    _rod(r, (0, -0.850, 0), BAMBU,     8, 0.016, 0.010, 0.500)
    _rod(r, (0, -1.105, 0), BAMBU_TUA, 8, 0.011, 0.011, 0.022)  # ruas
    _rod(r, (0, -1.290, 0), BAMBU,     6, 0.010, 0.004, 0.360)
    # Senar menjuntai dari ujung + pelampung merah supaya niat "memancing" jelas
    _box(r, (0, -1.530, 0.115), (0.006, 0.300, 0.006), SENAR, rot=(-22, 0, 0))
    _rod(r, (0, -1.672, 0.172), PELAMPUNG, 8, 0.026, 0.026, 0.070)
    _rod(r, (0, -1.720, 0.172), SENAR,     8, 0.020, 0.004, 0.040)


def _build_benih(r):
    """Kantong benih kain, digantung dari tangan."""
    _rod(r, (0, -0.115, 0), KAIN,     8, 0.070, 0.082, 0.150)
    _rod(r, (0, -0.032, 0), KAYU_TUA, 8, 0.046, 0.038, 0.034)   # ikatan leher
    _rod(r, (0, -0.196, 0), KAIN,     8, 0.066, 0.030, 0.040)   # dasar membulat
    _box(r, (0.030, -0.012, 0.020), (0.030, 0.020, 0.026), DAUN, rot=(0, 0, 22))
    _box(r, (-0.026, -0.008, -0.014), (0.026, 0.018, 0.024), DAUN, rot=(0, 0, -18))


def _build_bakul(r):
    """Bakul anyaman: melebar ke atas, dengan hasil panen menyembul."""
    _rod(r, (0, -0.180, 0), ANYAM,     12, 0.100, 0.140, 0.190)
    _rod(r, (0, -0.086, 0), ANYAM_TUA, 12, 0.146, 0.146, 0.024)  # bibir
    _rod(r, (0, -0.180, 0), ANYAM_TUA, 12, 0.128, 0.128, 0.020)  # sabuk anyam
    _rod(r, (0, -0.272, 0), ANYAM_TUA, 12, 0.104, 0.100, 0.020)  # alas
    # Busur pegangan — digenggam di y=0
    _box(r, (-0.118, -0.045, 0), (0.020, 0.090, 0.020), ANYAM_TUA, rot=(0, 0, 12))
    _box(r, ( 0.118, -0.045, 0), (0.020, 0.090, 0.020), ANYAM_TUA, rot=(0, 0, -12))
    _box(r, ( 0.000, -0.002, 0), (0.260, 0.020, 0.022), ANYAM_TUA)
    # Isi bakul
    _rod(r, (-0.048, -0.082, 0.026), BUAH, 8, 0.044, 0.036, 0.058)
    _rod(r, ( 0.052, -0.086, -0.020), BUAH, 8, 0.040, 0.032, 0.050)
    _box(r, ( 0.010, -0.070, 0.062), (0.070, 0.030, 0.050), DAUN, rot=(18, 24, 0))


def _build_kado(r):
    """Kado berpita — dipeluk di depan dada, bukan diayun."""
    _box(r, (0, -0.130, 0), (0.220, 0.180, 0.220), KADO)
    _box(r, (0, -0.130, 0), (0.236, 0.190, 0.046), PITA)
    _box(r, (0, -0.130, 0), (0.046, 0.190, 0.236), PITA)
    _box(r, (-0.052, -0.030, 0), (0.090, 0.040, 0.040), PITA, rot=(0, 0, 26))
    _box(r, ( 0.052, -0.030, 0), (0.090, 0.040, 0.040), PITA, rot=(0, 0, -26))
    _box(r, ( 0.000, -0.028, 0), (0.044, 0.044, 0.044), PITA, rot=(0, 45, 0))


def _build_bawaan(r):
    """Barang bawaan generik (hasil panen/benih curah) — peti kayu kecil."""
    _box(r, (0, -0.120, 0), (0.200, 0.160, 0.160), KAYU)
    _box(r, (0, -0.120, 0), (0.208, 0.030, 0.168), KAYU_TUA)
    _box(r, (0, -0.046, 0), (0.208, 0.024, 0.168), KAYU_TUA)
    _rod(r, (-0.042, -0.028, 0.024), DAUN, 6, 0.032, 0.026, 0.044)
    _rod(r, ( 0.046, -0.030, -0.020), BUAH, 6, 0.030, 0.024, 0.040)


_BUILDERS = {
    'cangkul':  _build_cangkul,
    'penyiram': _build_penyiram,
    'benih':    _build_benih,
    'bakul':    _build_bakul,
    'kapak':    _build_kapak,
    'kado':     _build_kado,
    'beliung':  _build_beliung,
    'pedang':   _build_pedang,
    'pancing':  _build_pancing,
    'bawaan':   _build_bawaan,
}

# Urutan persis config.TOOLS:
# ['Cangkul','Siram','Tanam','Panen','Kapak','Hadiah','Pickaxe','Pedang','Pancing']
KIND_BY_TOOL_INDEX = ('cangkul', 'penyiram', 'benih', 'bakul', 'kapak',
                      'kado', 'beliung', 'pedang', 'pancing')

# Ikon teks pendek untuk HUD kecil (pengganti label besar "Cangkul")
TOOL_GLYPH = {
    'cangkul': '\\', 'penyiram': 'U', 'benih': 'o', 'bakul': 'W',
    'kapak': 'F', 'kado': '#', 'beliung': 'Y', 'pedang': '|', 'pancing': '/',
    'bawaan': '=',
}

# Pose diam (derajat, relatif frame tulang tangan). Nilai ini yang menentukan
# apakah alat "tergenggam" atau menembus lengan — lihat _bench/shots/toolhand_*.
CARRY_POSE = {
    'cangkul':  (-18.0,  0.0,  10.0),
    'penyiram': (  0.0,  0.0,   0.0),
    'benih':    (  0.0,  0.0,   0.0),
    'bakul':    (  0.0,  0.0,   0.0),
    'kapak':    (-14.0,  0.0,   8.0),
    'kado':     ( -8.0,  0.0,   0.0),
    'beliung':  (-16.0,  0.0,   8.0),
    'pedang':   ( -6.0,  0.0,  -6.0),
    'pancing':  (-152.0, 0.0,  10.0),
    'bawaan':   (  0.0,  0.0,   0.0),
}

# Geseran kecil supaya gagang duduk di tengah kepalan, bukan di titik tulang.
GRIP_OFFSET = {
    'cangkul':  (0.0, 0.0, 0.0),
    'penyiram': (0.0, -0.03, 0.0),
    'benih':    (0.0, -0.02, 0.0),
    'bakul':    (0.0, -0.03, 0.0),
    'kapak':    (0.0, 0.0, 0.0),
    'kado':     (0.0, -0.02, 0.06),
    'beliung':  (0.0, 0.0, 0.0),
    'pedang':   (0.0, 0.0, 0.0),
    'pancing':  (0.0, 0.0, 0.0),
    'bawaan':   (0.0, -0.02, 0.0),
}


def kind_for_tool_index(idx: int) -> str:
    if 0 <= idx < len(KIND_BY_TOOL_INDEX):
        return KIND_BY_TOOL_INDEX[idx]
    return 'bawaan'


def build_tool(kind: str, parent=None):
    """Bangun satu alat baru. Selalu Entity + Mesh segar — tidak ada cache."""
    fn = _BUILDERS.get(kind)
    if fn is None:
        return None
    root = Entity(parent=parent) if parent is not None else Entity()
    root.name = f'tool_{kind}'
    fn(root)
    return root
