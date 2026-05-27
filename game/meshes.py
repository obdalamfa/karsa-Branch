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
"""
from __future__ import annotations
import math
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


# ─── CACHED MESHES ───────────────────────────────────────────────────────────
_soft_cube_mesh = None
_soft_capsule_mesh = None


def soft_cube_mesh():
    """Return cached unit superellipsoid (vertices roughly in [-1, 1]).
    Tepi/sudut membulat, tengah sisi hampir datar."""
    global _soft_cube_mesh
    if _soft_cube_mesh is not None:
        return _soft_cube_mesh

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
    return _soft_cube_mesh


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
        return _chibi_head_mesh

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
    return _chibi_head_mesh


def chibi_torso_mesh():
    """Torso chibi: barrel berbentuk T halus — bahu lebar, pinggang sempit,
    dasar menyempit halus. 28×20 segmen, eksponen 0.22."""
    global _chibi_torso_mesh
    if _chibi_torso_mesh is not None:
        return _chibi_torso_mesh

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
    return _chibi_torso_mesh


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
        return _creature_body_mesh

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
    return _creature_body_mesh


def creature_head_mesh():
    """Kepala hewan: rounded box (eksponen 0.28) — bentuk antara kotak dan bola.
    Tanpa moncong-push agar dekorasi (telinga/tanduk/paruh) tetap kelihatan."""
    global _creature_head_mesh
    if _creature_head_mesh is not None:
        return _creature_head_mesh

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
    return _creature_head_mesh
