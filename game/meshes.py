"""
meshes.py — Mesh prosedural halus untuk Lembah Karsa 3D.

Tujuan Phase 2: ganti voxel feel dari cube tajam menjadi soft-cube
(superellipsoid) yang menyerupai bentuk "rounded box" di TSO/AC.

Pendekatan: superellipsoid dengan eksponen rendah (~0.3-0.4) memberikan
bentuk yang sebagian besar datar di tengah tiap sisi tapi membulat
di tepi/sudut. Satu unit mesh di-cache lalu di-scale via Entity.scale.

Bentuk yang disediakan:
  - soft_cube_mesh()  → unit cube dengan tepi membulat
  - soft_capsule_mesh() → silinder dengan tutup hemisfer (kaki, lengan)

Pemakaian (dari entities.py / world.py):
    from .meshes import soft_cube_mesh
    e = Entity(model=soft_cube_mesh(), scale=(2, 1, 2), color=col)

PENTING — kenapa setiap getter mengembalikan salinan node:
    Mesh Ursina adalah NodePath Panda3D, dan sebuah NodePath hanya boleh punya
    SATU parent. Kalau satu Mesh cache diberikan ke banyak Entity, Entity kedua
    "mencuri" node itu dari yang pertama, ketiga dari kedua, dan seterusnya —
    hasil akhirnya hanya Entity yang dibuat TERAKHIR yang punya geometri, sisanya
    jadi node kosong yang tidak menggambar apa pun. Itulah sebabnya dinding,
    rumah, dan perabot tidak pernah muncul meski entity-nya ada di scene graph.

    Perbaikannya: `_instance()` mengembalikan salinan sub-pohon lewat `copy_to()`.
    Harus `copy_to`, BUKAN `node().makeCopy()` — Mesh Ursina adalah PandaNode
    kosong yang Geom-nya ada di anaknya, jadi makeCopy() (dangkal, hanya node itu
    sendiri) menghasilkan node kosong yang tidak menggambar apa pun. Diukur di
    `_bench/probes/probe_copymode.py`: makeCopy = 0 GeomNode, copy_to = 1.
    Biaya `_bench/probes/probe_meshcost.py`: 1.500 salinan copy_to = 0,035 s,
    versus 0,399 s kalau Mesh dibangun ulang dari array vertex.
"""
from __future__ import annotations
import math
from panda3d.core import NodePath
from ursina import Mesh, Vec3


# ─── PARAMETER GLOBAL ────────────────────────────────────────────────────────
_CUBE_SEG_U = 12      # longitudinal (dikurangi untuk performa voxel)
_CUBE_SEG_V = 10      # latitudinal (kutub ke kutub)
_CUBE_EXP = 0.20      # eksponen 0.20 menghasilkan kubus modern bersudut melengkung, bukan bola bulat

_CAPSULE_SEG_U = 16
_CAPSULE_SEG_V = 8    # hemisfer atas/bawah, masing-masing


# ─── HELPERS ─────────────────────────────────────────────────────────────────
def _signed_pow(x: float, n: float) -> float:
    """sign(x) * |x|^n — superellipsoid building block."""
    if x == 0.0:
        return 0.0
    return math.copysign(abs(x) ** n, x)


def _superellipsoid_point(u: float, v: float, e1: float, e2: float):
    """u: longitude [-pi, pi], v: latitude [-pi/2, pi/2]."""
    cv = math.cos(v); sv = math.sin(v)
    cu = math.cos(u); su = math.sin(u)
    x = _signed_pow(cv, e1) * _signed_pow(cu, e2)
    y = _signed_pow(sv, e1)
    z = _signed_pow(cv, e1) * _signed_pow(su, e2)
    return x, y, z


def _instance(cached):
    """Salinan lepas dari mesh cache, siap dipasang ke satu Entity.

    Wajib dipakai oleh SEMUA getter mesh di modul ini — lihat catatan di
    docstring modul. Mengembalikan objek cache secara langsung akan membuat
    semua entity kecuali yang terakhir kehilangan geometri.
    """
    if cached is None:
        return None
    holder = NodePath('_mesh_instance')
    copy = cached.copy_to(holder)
    copy.detach_node()      # lepas dari holder supaya Entity bisa jadi parent
    return copy


# ─── CACHED MESHES ───────────────────────────────────────────────────────────
_soft_cube_mesh = None
_soft_capsule_mesh = None


def soft_cube_mesh():
    """Return cached unit superellipsoid (vertices roughly in [-1, 1]).
    Tepi/sudut membulat, tengah sisi hampir datar."""
    global _soft_cube_mesh
    if _soft_cube_mesh is not None:
        return _instance(_soft_cube_mesh)

    nu, nv = _CUBE_SEG_U, _CUBE_SEG_V
    e1 = e2 = _CUBE_EXP

    verts = []
    norms = []
    uvs = []
    # Build vertex grid (nv+1) rings × (nu+1) longitudes
    for j in range(nv + 1):
        v = -math.pi/2 + math.pi * j / nv
        for i in range(nu + 1):
            u = -math.pi + 2 * math.pi * i / nu
            x, y, z = _superellipsoid_point(u, v, e1, e2)
            # Skala dikalikan 0.5 agar sesuai dengan model standard Ursina cube (ukuran 1.0, dari -0.5 ke 0.5)
            verts.append(Vec3(x * 0.5, y * 0.5, z * 0.5))
            # Normal kasar = posisi yang dinormalisasi (cukup baik untuk shading half-Lambert)
            ln = math.sqrt(x*x + y*y + z*z) or 1.0
            norms.append(Vec3(x/ln, y/ln, z/ln))
            uvs.append((i / nu, j / nv))

    tris = []
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i
            b = a + 1
            c = a + (nu + 1)
            d = c + 1
            # Dua segitiga membentuk satu quad (winding order CCW)
            tris.append((a, b, c))
            tris.append((b, d, c))

    _soft_cube_mesh = Mesh(vertices=verts, triangles=tris,
                            normals=norms, uvs=uvs,
                            mode='triangle', static=True)
    return _instance(_soft_cube_mesh)


def soft_capsule_mesh():
    """Dikembalikan ke bentuk voxel kotak (bukan bulat) agar sesuai dengan style chibi voxel."""
    return soft_cube_mesh()


# ─── CHIBI POLY MESHES ───────────────────────────────────────────────────────
# Mesh berdetil sedang untuk kepala & torso ala Tomodachi/Sims/Funko.
# Idenya: superellipsoid dengan non-uniform exponent + taper di sumbu tertentu,
# menghasilkan bentuk berkarakter tanpa harus jadi voxel kotak.

_chibi_head_mesh = None
_chibi_torso_mesh = None


def chibi_head_mesh():
    """Kepala chibi: rounded box sedikit lebih tinggi dari lebar, dagu mengecil
    halus. 32×24 segmen, eksponen 0.22 (sama dengan body — rounded box konsisten)."""
    global _chibi_head_mesh
    if _chibi_head_mesh is not None:
        return _instance(_chibi_head_mesh)

    nu, nv = 22, 16
    e1 = e2 = 0.10   # hampir cube tajam, hanya tepi/sudut yang dibevel halus (Crossy Road feel)

    verts, norms, uvs = [], [], []
    for j in range(nv + 1):
        v = -math.pi/2 + math.pi * j / nv
        for i in range(nu + 1):
            u = -math.pi + 2 * math.pi * i / nu
            x, y, z = _superellipsoid_point(u, v, e1, e2)
            # Taper dagu: kompres X & Z secara progresif di bagian bawah (y < 0)
            if y < 0:
                chin_factor = 1.0 - 0.15 * (abs(y) ** 1.5)
                x *= chin_factor
                z *= chin_factor
            # Sedikit elongate vertical (head lebih tinggi)
            y *= 1.05
            # Sedikit pipih anterior-posterior
            z *= 0.94
            # Skala dikalikan 0.5 agar sesuai dengan model standard Ursina (ukuran 1.0)
            verts.append(Vec3(x * 0.5, y * 0.5, z * 0.5))
            ln = math.sqrt(x*x + y*y + z*z) or 1.0
            norms.append(Vec3(x/ln, y/ln, z/ln))
            uvs.append((i / nu, j / nv))

    tris = []
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i
            b = a + 1
            c = a + (nu + 1)
            d = c + 1
            tris.append((a, b, c))
            tris.append((b, d, c))

    _chibi_head_mesh = Mesh(vertices=verts, triangles=tris,
                             normals=norms, uvs=uvs,
                             mode='triangle', static=True)
    return _instance(_chibi_head_mesh)


def chibi_torso_mesh():
    """Torso chibi: barrel berbentuk T halus — bahu lebar, pinggang sempit,
    dasar menyempit halus. 28×20 segmen, eksponen 0.22."""
    global _chibi_torso_mesh
    if _chibi_torso_mesh is not None:
        return _instance(_chibi_torso_mesh)

    nu, nv = 22, 16
    e1 = e2 = 0.10   # hampir cube tajam, hanya tepi/sudut yang dibevel halus (Crossy Road feel)

    verts, norms, uvs = [], [], []
    for j in range(nv + 1):
        v = -math.pi/2 + math.pi * j / nv
        for i in range(nu + 1):
            u = -math.pi + 2 * math.pi * i / nu
            x, y, z = _superellipsoid_point(u, v, e1, e2)
            # Taper torso: profil naik-turun di sumbu Y → bahu (atas) lebar,
            # pinggang sedikit lebih sempit, panggul sedang.
            # y ∈ [-1, 1]; bentuk profil: 1.0 di atas, 0.85 di pinggang (y≈-0.2), 0.95 di bawah
            t = (y + 1.0) * 0.5    # 0 di bawah, 1 di atas
            # Profil S-curve: bahu (t~0.85) > pinggang (t~0.45) > pinggul (t~0.2)
            if t > 0.7:
                width = 1.00            # bahu
            elif t > 0.35:
                # Interpolasi pinggang
                wt = (t - 0.35) / 0.35
                width = 0.86 + (1.00 - 0.86) * wt
            else:
                # Pinggul agak melebar lalu menyempit di dasar
                wt = t / 0.35
                width = 0.92 + (0.86 - 0.92) * wt
            x *= width
            z *= width * 0.78   # torso lebih pipih anterior-posterior (dada/punggung)
            # Skala dikalikan 0.5 agar sesuai dengan model standard Ursina (ukuran 1.0)
            verts.append(Vec3(x * 0.5, y * 0.5, z * 0.5))
            ln = math.sqrt(x*x + y*y + z*z) or 1.0
            norms.append(Vec3(x/ln, y/ln, z/ln))
            uvs.append((i / nu, j / nv))

    tris = []
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i
            b = a + 1
            c = a + (nu + 1)
            d = c + 1
            tris.append((a, b, c))
            tris.append((b, d, c))

    _chibi_torso_mesh = Mesh(vertices=verts, triangles=tris,
                              normals=norms, uvs=uvs,
                              mode='triangle', static=True)
    return _instance(_chibi_torso_mesh)


# ─── CREATURE / ANIMAL MESHES ────────────────────────────────────────────────
# Untuk badan hewan (sapi, kambing, kelinci, kucing, dll.) dan kepala mob.
# Eksponen lebih tinggi (0.45-0.55) supaya bentuknya ovoid-rounded, bukan kotak.

_creature_body_mesh = None
_creature_head_mesh = None


def creature_body_mesh():
    """Tubuh hewan: rounded box (di antara kotak dan ellipsoid).
    Eksponen 0.30 → face datar tegas, sudut/edge dibevel lebih halus daripada chibi 0.22."""
    global _creature_body_mesh
    if _creature_body_mesh is not None:
        return _instance(_creature_body_mesh)

    nu, nv = 22, 16
    e1 = e2 = 0.10   # hampir cube tajam, hanya tepi/sudut yang dibevel halus (Crossy Road feel)

    verts, norms, uvs = [], [], []
    for j in range(nv + 1):
        v = -math.pi/2 + math.pi * j / nv
        for i in range(nu + 1):
            u = -math.pi + 2*math.pi * i / nu
            x, y, z = _superellipsoid_point(u, v, e1, e2)
            # Skala dikalikan 0.5 agar sesuai dengan model standard Ursina (ukuran 1.0)
            verts.append(Vec3(x * 0.5, y * 0.5, z * 0.5))
            ln = math.sqrt(x*x + y*y + z*z) or 1.0
            norms.append(Vec3(x/ln, y/ln, z/ln))
            uvs.append((i / nu, j / nv))

    tris = []
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i
            b = a + 1
            c = a + (nu + 1)
            d = c + 1
            tris.append((a, b, c))
            tris.append((b, d, c))

    _creature_body_mesh = Mesh(vertices=verts, triangles=tris,
                                normals=norms, uvs=uvs,
                                mode='triangle', static=True)
    return _instance(_creature_body_mesh)


def creature_head_mesh():
    """Kepala hewan: rounded box (eksponen 0.28) — bentuk antara kotak dan bola.
    Tanpa moncong-push agar dekorasi (telinga/tanduk/paruh) tetap kelihatan."""
    global _creature_head_mesh
    if _creature_head_mesh is not None:
        return _instance(_creature_head_mesh)

    nu, nv = 22, 16
    e1 = e2 = 0.10   # hampir cube tajam, hanya tepi/sudut yang dibevel halus (Crossy Road feel)

    verts, norms, uvs = [], [], []
    for j in range(nv + 1):
        v = -math.pi/2 + math.pi * j / nv
        for i in range(nu + 1):
            u = -math.pi + 2*math.pi * i / nu
            x, y, z = _superellipsoid_point(u, v, e1, e2)
            # Skala dikalikan 0.5 agar sesuai dengan model standard Ursina (ukuran 1.0)
            verts.append(Vec3(x * 0.5, y * 0.5, z * 0.5))
            ln = math.sqrt(x*x + y*y + z*z) or 1.0
            norms.append(Vec3(x/ln, y/ln, z/ln))
            uvs.append((i / nu, j / nv))

    tris = []
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i
            b = a + 1
            c = a + (nu + 1)
            d = c + 1
            tris.append((a, b, c))
            tris.append((b, d, c))

    _creature_head_mesh = Mesh(vertices=verts, triangles=tris,
                                normals=norms, uvs=uvs,
                                mode='triangle', static=True)
    return _instance(_creature_head_mesh)


# ─── KERUCUT LOW-POLY ────────────────────────────────────────────────────────
# Dipakai untuk paruh, tanduk, telinga, dan moncong hewan (game/animal_models.py).
# Kubus tidak pernah terbaca sebagai "runcing" pada siluet sekecil itu — satu
# bentuk meruncing sudah cukup membedakan ayam dari kelinci dari kambing.

_low_cone_mesh = None


def low_cone_mesh():
    """Kerucut 8 sisi, unit: alas radius 0.5 di y=-0.5, puncak di y=+0.5.

    Sengaja dibuat sepusat seperti cube standar Ursina supaya `scale` langsung
    berarti ukuran penuh dalam meter, sama seperti creature_body_mesh().
    """
    global _low_cone_mesh
    if _low_cone_mesh is not None:
        return _instance(_low_cone_mesh)

    seg = 8
    verts, norms, uvs, tris = [], [], [], []
    apex = Vec3(0, 0.5, 0)
    for i in range(seg):
        a0 = 2 * math.pi * i / seg
        a1 = 2 * math.pi * (i + 1) / seg
        p0 = Vec3(math.cos(a0) * 0.5, -0.5, math.sin(a0) * 0.5)
        p1 = Vec3(math.cos(a1) * 0.5, -0.5, math.sin(a1) * 0.5)
        # Sisi miring
        base = len(verts)
        verts += [p0, p1, apex]
        nx, nz = math.cos((a0 + a1) * 0.5), math.sin((a0 + a1) * 0.5)
        n = Vec3(nx * 0.89, 0.45, nz * 0.89)
        norms += [n, n, n]
        uvs += [(i / seg, 0), ((i + 1) / seg, 0), ((i + 0.5) / seg, 1)]
        tris.append((base, base + 1, base + 2))
        # Alas
        base = len(verts)
        verts += [Vec3(0, -0.5, 0), p1, p0]
        nd = Vec3(0, -1, 0)
        norms += [nd, nd, nd]
        uvs += [(0.5, 0.5), (0, 0), (1, 0)]
        tris.append((base, base + 1, base + 2))

    _low_cone_mesh = Mesh(vertices=verts, triangles=tris,
                          normals=norms, uvs=uvs,
                          mode='triangle', static=True)
    return _instance(_low_cone_mesh)


# ─── PAGAR & GERBANG DESA ────────────────────────────────────────────────────
# Kenapa satu Mesh utuh per tile, bukan tumpukan Entity kubus:
#   Pagar hanya terbaca sebagai pagar kalau ada UDARA di antara batangnya, jadi
#   satu tile butuh belasan batang. Kalau tiap batang jadi Entity sendiri, pagar
#   keliling kebun (82 tile) langsung menambah ~900 node ke scene graph. Dirakit
#   jadi satu Mesh per pola sambungan, satu tile tetap SATU Entity — sama murah
#   dengan kubus kardus yang digantikan, dan justru lebih ringan segitiganya
#   (~130 tris versus 240 tris milik soft_cube_mesh).
#
# Warna diambil dari tekstur palet 4-pita (fence_palette_texture): UV tiap
# batang menunjuk ke satu pita. Vertex color TIDAK bisa dipakai di sini —
# smooth_shader hanya membaca p3d_ColorScale, yaitu satu warna untuk seluruh
# Entity — jadi palet-lewat-UV satu-satunya cara mendapat tiang gelap dan bilah
# pucat dalam satu draw call.
#
# Semua ukuran di bawah dalam METER dan mesh dibangun pada skala akhir, jadi
# Entity pemakai WAJIB scale=(1,1,1). Menskalakan mesh ini akan menggepengkan
# batang-batangnya.

from .config import TILE_SIZE as _FENCE_TS

# Pita palet
_TONE_POST = 0    # kayu tiang, paling gelap
_TONE_RAIL = 1    # palang bambu
_TONE_SLAT = 2    # bilah bambu belah, paling pucat
_TONE_LASH = 3    # ikatan ijuk / kepala tiang / daun pintu

# Luminance (0-100) dijaga di pita "scenery" docs/READABILITY.md §3.1
# (L 40-62, S <= 35) supaya pagar tidak bersaing dengan objek yang bisa dipakai.
_PALETTE = ((120, 104,  80),   # L 42  S 33
            (150, 136, 102),   # L 53  S 32
            (162, 150, 118),   # L 59  S 27
            (132, 114,  86))   # L 46  S 35
_PAL_W = 8                     # 8x8 px, empat pita selebar 2 px

_fence_palette_tex = None


def fence_palette_texture():
    """Tekstur palet kayu untuk semua mesh pagar/gerbang.

    Dikembalikan APA ADANYA, bukan lewat _instance(): Texture bukan NodePath,
    jadi boleh dipakai bersama ratusan Entity sekaligus. Larangan berbagi di
    docstring modul ini hanya berlaku untuk Mesh.
    """
    global _fence_palette_tex
    if _fence_palette_tex is None:
        from PIL import Image
        from ursina import Texture
        img = Image.new('RGB', (_PAL_W, _PAL_W))
        px = img.load()
        for i, rgb in enumerate(_PALETTE):
            for x in range(i * 2, i * 2 + 2):
                for y in range(_PAL_W):
                    px[x, y] = rgb
        t = Texture(img)
        t.filtering = False      # nearest — pita warna tidak boleh saling luber
        _fence_palette_tex = t
    return _fence_palette_tex


def _tone_uv(tone: int):
    """Titik sampel di tengah pita, aman dari pembulatan texel."""
    return ((tone * 2 + 1) / _PAL_W, 0.5)


# ─── Perakit geometri balok ──────────────────────────────────────────────────
class _Acc:
    """Penampung vertex/normal/uv/segitiga selama satu mesh dirakit."""
    __slots__ = ('v', 'n', 'u', 't')

    def __init__(self):
        self.v = []; self.n = []; self.u = []; self.t = []

    def build(self):
        return Mesh(vertices=self.v, triangles=self.t, normals=self.n,
                    uvs=self.u, mode='triangle', static=True)


def _m3mul(a, b):
    return tuple(tuple(a[i][0]*b[0][j] + a[i][1]*b[1][j] + a[i][2]*b[2][j]
                       for j in range(3)) for i in range(3))


def _m3apply(m, v):
    return (m[0][0]*v[0] + m[0][1]*v[1] + m[0][2]*v[2],
            m[1][0]*v[0] + m[1][1]*v[1] + m[1][2]*v[2],
            m[2][0]*v[0] + m[2][1]*v[1] + m[2][2]*v[2])


def _rot(yaw: float, lean_x: float, lean_z: float):
    """Ry * Rz * Rx. lean_* kecil saja — miring sedikit bikin pagar terbaca
    buatan tangan; miring banyak bikin terbaca rusak."""
    cy, sy = math.cos(yaw), math.sin(yaw)
    cx, sx = math.cos(lean_x), math.sin(lean_x)
    cz, sz = math.cos(lean_z), math.sin(lean_z)
    ry = ((cy, 0.0, sy), (0.0, 1.0, 0.0), (-sy, 0.0, cy))
    rz = ((cz, -sz, 0.0), (sz, cz, 0.0), (0.0, 0.0, 1.0))
    rx = ((1.0, 0.0, 0.0), (0.0, cx, -sx), (0.0, sx, cx))
    return _m3mul(ry, _m3mul(rz, rx))


_BOX_FACES = (
    (( 1.0, 0.0, 0.0), (( 1, -1,  1), ( 1, -1, -1), ( 1,  1, -1), ( 1,  1,  1))),
    ((-1.0, 0.0, 0.0), ((-1, -1, -1), (-1, -1,  1), (-1,  1,  1), (-1,  1, -1))),
    (( 0.0, 1.0, 0.0), ((-1,  1,  1), ( 1,  1,  1), ( 1,  1, -1), (-1,  1, -1))),
    (( 0.0,-1.0, 0.0), ((-1, -1, -1), ( 1, -1, -1), ( 1, -1,  1), (-1, -1,  1))),
    (( 0.0, 0.0, 1.0), ((-1, -1,  1), ( 1, -1,  1), ( 1,  1,  1), (-1,  1,  1))),
    (( 0.0, 0.0,-1.0), (( 1, -1, -1), (-1, -1, -1), (-1,  1, -1), ( 1,  1, -1))),
)


def _emit_quad(acc, pts, nrm, uv):
    p0, p1, p2, p3 = pts
    e1 = (p1[0]-p0[0], p1[1]-p0[1], p1[2]-p0[2])
    e2 = (p2[0]-p1[0], p2[1]-p1[1], p2[2]-p1[2])
    cr = (e1[1]*e2[2] - e1[2]*e2[1],
          e1[2]*e2[0] - e1[0]*e2[2],
          e1[0]*e2[1] - e1[1]*e2[0])
    # Winding dikoreksi sendiri terhadap normal — lebih aman daripada menghafal
    # urutan sudut yang benar untuk enam sisi sekaligus.
    if cr[0]*nrm[0] + cr[1]*nrm[1] + cr[2]*nrm[2] < 0.0:
        p0, p1, p2, p3 = p3, p2, p1, p0
    b = len(acc.v)
    for p in (p0, p1, p2, p3):
        acc.v.append(Vec3(*p))
        acc.n.append(Vec3(*nrm))
        acc.u.append(uv)
    acc.t.append((b, b + 1, b + 2))
    acc.t.append((b, b + 2, b + 3))


def _emit_box(acc, center, half, tone, yaw=0.0, lean_x=0.0, lean_z=0.0):
    """Satu balok = 24 vertex / 12 segitiga, normal per-sisi (cel shader butuh
    sisi datar, bukan normal yang dirata-ratakan antar sisi)."""
    m = _rot(yaw, lean_x, lean_z)
    uv = _tone_uv(tone)
    for n_local, corners in _BOX_FACES:
        nrm = _m3apply(m, n_local)
        pts = []
        for c in corners:
            p = _m3apply(m, (c[0]*half[0], c[1]*half[1], c[2]*half[2]))
            pts.append((p[0]+center[0], p[1]+center[1], p[2]+center[2]))
        _emit_quad(acc, pts, nrm, uv)


# ─── Ukuran pagar (meter) ────────────────────────────────────────────────────
# Tinggi tiang 1,35 sengaja MELEWATI OBJ_H = 1,2: docs/READABILITY.md §3.4
# memesan pita 0,6-1,2 m untuk benda yang bisa dipakai. Pagar harus berdiri di
# atas pita itu supaya tidak pernah tertukar dengan perabot yang bisa diklik.
_F_POST_HW = 0.075
_F_RAIL_HH = 0.056
_F_RAIL_HD = 0.044
_F_SLAT_HW = 0.045     # setengah lebar bilah, searah bentang
_F_SLAT_HD = 0.024     # setengah tebal bilah, melintang bentang
# Dua bilah per setengah bentang, bukan tiga: dengan jarak ~0,25 m deretan
# bilah menjadi rapat dan pagar terbaca sebagai pagar piket pinggiran kota
# Amerika. Jarak ~0,4 m membuat PALANG yang terbaca lebih dulu, dan itulah
# yang membedakan pagar bambu desa dari panel piket.
_F_SLAT_T  = (0.34, 0.74)
# Bilah diikat di SATU muka pagar, tidak di tengah palang. Detail kecil ini yang
# bikin bilah terbaca sebagai bambu yang diikatkan, bukan panel utuh dari pabrik.
_F_SLAT_OFF = 0.046

# style -> (tinggi tiang, ketinggian palang, pakai bilah, pengali tebal palang)
_FENCE_STYLE = {
    # Pagar bambu keliling kebun: dua palang + bilah belah berjarak.
    'bambu':   (1.35, (0.44, 0.92),       True,  1.0),
    # Kandang ternak: tiga palang tanpa bilah — hewan harus terlihat dari luar,
    # dan bedanya dengan pagar keliling jadi informasi, bukan sekadar variasi.
    'kandang': (1.22, (0.34, 0.70, 1.04), False, 1.35),
}

# Miring deterministik per varian: (yaw tiang, lean_x tiang, lean_z tiang,
# lean bilah 1..3). Tiga varian cukup supaya larik panjang tidak terlihat
# di-copy-paste, tapi cache mesh tetap kecil (16 pola x 2 gaya x 3 varian).
_JITTER = (
    ( 0.020,  0.012, -0.018,  0.030, -0.022,  0.014),
    (-0.030, -0.020,  0.010, -0.026,  0.034, -0.012),
    ( 0.010,  0.008,  0.022,  0.018, -0.030,  0.026),
)

# Urutan bit sama persis dengan World3D._road_bitmask: N, E, S, W.
_DIRS = ((0, -1), (1, 0), (0, 1), (-1, 0))

_fence_cache: dict = {}


def _build_fence_mesh(bm: int, style: str, variant: int):
    post_h, rail_ys, use_slat, rail_k = _FENCE_STYLE[style]
    j = _JITTER[variant]
    acc = _Acc()
    half = _FENCE_TS * 0.5

    dirs = [i for i in range(4) if (bm >> i) & 1]
    if not dirs:
        dirs = [1, 3]   # tile pagar terpencil tetap digambar sebagai potongan timur-barat

    # Tiang di pusat tile: jarak antar tiang = satu tile (2 m), persis jarak
    # tiang bambu di pagar desa. Bentang antar tiang bertemu di batas tile.
    _emit_box(acc, (0.0, post_h * 0.5, 0.0),
              (_F_POST_HW, post_h * 0.5, _F_POST_HW), _TONE_POST,
              yaw=j[0], lean_x=j[1], lean_z=j[2])
    _emit_box(acc, (0.0, post_h + 0.035, 0.0),
              (_F_POST_HW * 0.8, 0.035, _F_POST_HW * 0.8), _TONE_LASH, yaw=j[0])

    for d in dirs:
        dx, dz = _DIRS[d]
        ax  = 0 if dx else 2          # sumbu bentang
        sgn = float(dx if dx else dz)
        # Palang dipanjangkan 4% melewati batas tile supaya sambungan dengan
        # tile sebelah tidak menyisakan celah setipis rambut.
        hl  = half * 0.52
        mid = sgn * half * 0.5

        for ry in rail_ys:
            c = [0.0, ry, 0.0]
            c[ax] = mid
            h = [_F_RAIL_HD, _F_RAIL_HH * rail_k, _F_RAIL_HD]
            h[ax] = hl
            _emit_box(acc, tuple(c), tuple(h), _TONE_RAIL)

        if not use_slat:
            continue
        top0 = rail_ys[-1] + 0.18
        cross = 2 if ax == 0 else 0
        for k, t in enumerate(_F_SLAT_T):
            top = top0 + (0.07 if k % 2 else -0.05)   # ujung bilah dipotong tidak rata
            # Bilah menyentuh tanah. Digantung 8 cm di atas rumput, ujung
            # bawahnya terbaca sebagai benda melayang — pelanggaran nomor 5 di
            # checklist docs/READABILITY.md §6.
            bot = 0.01
            c = [0.0, (bot + top) * 0.5, 0.0]
            c[ax] = sgn * half * t
            c[cross] = _F_SLAT_OFF
            h = [_F_SLAT_HD, (top - bot) * 0.5, _F_SLAT_HD]
            h[ax] = _F_SLAT_HW
            lean = j[3 + k]
            _emit_box(acc, tuple(c), tuple(h), _TONE_SLAT,
                      lean_z=lean if ax == 0 else 0.0,
                      lean_x=lean if ax == 2 else 0.0)

    return acc.build()


def fence_mesh(bitmask: int, style: str = 'bambu', variant: int = 0):
    """Satu tile pagar. `bitmask` N|E<<1|S<<2|W<<3 = sisi mana yang diteruskan
    pagar lain, jadi sudut dan ujung larik tidak pernah menggantung."""
    key = ('f', bitmask & 15, style, variant % 3)
    m = _fence_cache.get(key)
    if m is None:
        m = _build_fence_mesh(key[1], key[2], key[3])
        _fence_cache[key] = m
    return _instance(m)          # WAJIB — lihat catatan _instance() di kepala modul


# ─── Gerbang ─────────────────────────────────────────────────────────────────
_G_POST_H  = 1.85
_G_POST_HW = 0.105


def _emit_gate_leaf(acc, ax: int, sgn: float):
    """Daun pintu bambu yang menganga ~75 derajat ke dalam tile."""
    half = _FENCE_TS * 0.5
    hx = sgn * half if ax == 0 else 0.0
    hz = sgn * half if ax == 2 else 0.0
    # Arah dasar = masuk ke tengah tile, lalu diputar supaya daun berdiri
    # menyamping dan siluetnya terbaca sebagai pintu, bukan sebagai palang.
    ux, uz = (-sgn, 0.0) if ax == 0 else (0.0, -sgn)
    a = math.radians(75.0)
    ca, sa = math.cos(a), math.sin(a)
    dx, dz = ux * ca - uz * sa, ux * sa + uz * ca
    yaw = math.atan2(-dz, dx)          # Ry memetakan +X lokal ke (cos yaw, -sin yaw)

    ln = 0.82
    for ry in (0.34, 0.92):
        _emit_box(acc, (hx + dx * ln * 0.5, ry, hz + dz * ln * 0.5),
                  (ln * 0.5, _F_RAIL_HH, _F_RAIL_HD), _TONE_RAIL, yaw=yaw)
    for t in (0.18, 0.42, 0.66):
        _emit_box(acc, (hx + dx * ln * t, 0.60, hz + dz * ln * t),
                  (_F_SLAT_HW, 0.54, _F_SLAT_HD), _TONE_SLAT, yaw=yaw)
    # Tiang tepi daun — memberi ujung tegas, jadi daun tidak terlihat patah.
    _emit_box(acc, (hx + dx * ln, 0.62, hz + dz * ln),
              (_F_SLAT_HD * 1.6, 0.62, _F_SLAT_HD * 1.6), _TONE_LASH, yaw=yaw)


def _build_gate_mesh(axis: str, post_lo: bool, post_hi: bool, variant: int):
    """Gerbang harus terbaca sebagai LUBANG, bukan sebagai kotak berwarna lain:
    dua tiang tinggi menandai bukaan, tidak ada satu pun palang yang menyeberang
    di ketinggian badan, dan daun pintunya digambar dalam keadaan TERBUKA."""
    acc = _Acc()
    half = _FENCE_TS * 0.5
    ax = 0 if axis == 'x' else 2
    hinge_sgn = None

    for sgn, present in ((-1.0, post_lo), (1.0, post_hi)):
        if not present:
            continue
        if hinge_sgn is None:
            hinge_sgn = sgn
        c = [0.0, _G_POST_H * 0.5, 0.0]
        c[ax] = sgn * half
        _emit_box(acc, tuple(c), (_G_POST_HW, _G_POST_H * 0.5, _G_POST_HW), _TONE_POST)
        cap = [0.0, _G_POST_H + 0.055, 0.0]
        cap[ax] = sgn * half
        h = [_G_POST_HW * 1.9, 0.055, _G_POST_HW * 1.9]
        _emit_box(acc, tuple(cap), tuple(h), _TONE_LASH)

    # Palang lintang hanya kalau kedua tiang ada di tile yang sama. Bukaan dua
    # tile (gerbang kuburan) dibiarkan lapang, bukan diberi dua potong palang
    # yang menggantung di udara.
    if post_lo and post_hi:
        c = [0.0, _G_POST_H - 0.16, 0.0]
        h = [_F_RAIL_HD * 1.5, 0.06, _F_RAIL_HD * 1.5]
        h[ax] = half * 1.04
        _emit_box(acc, tuple(c), tuple(h), _TONE_RAIL)

    if hinge_sgn is not None:
        _emit_gate_leaf(acc, ax, hinge_sgn)
    return acc.build()


def gate_mesh(axis: str = 'x', post_lo: bool = True, post_hi: bool = True,
              variant: int = 0):
    """Satu tile gerbang. `post_lo`/`post_hi` = pasang tiang di batas tile sisi
    negatif / positif sumbu. Sisi yang bersebelahan dengan tile gerbang lain
    dilewati, supaya gerbang dua tile jadi satu bukaan lebar, bukan tiang dobel."""
    key = ('g', axis, bool(post_lo), bool(post_hi), variant % 3)
    m = _fence_cache.get(key)
    if m is None:
        m = _build_gate_mesh(key[1], key[2], key[3], key[4])
        _fence_cache[key] = m
    return _instance(m)
