"""
Generate OBJ models for 4 missing dungeon mobs:
  mob_banaspati  - roh api melayang (will-o-wisp / fireball spirit)
  mob_tikus_gua  - tikus gua berkaki empat
  mob_leak       - kepala setan Bali melayang (Leyak)
  mob_kuntilanak - hantu wanita berambut panjang
"""

import math
import os

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'models')


# ─── Geometry helpers ────────────────────────────────────────────────

def _normalize(v):
    x, y, z = v
    d = math.sqrt(x*x + y*y + z*z)
    if d == 0:
        return (0.0, 1.0, 0.0)
    return (x/d, y/d, z/d)


def _face_normal(verts, f):
    """Per-face normal for a tri/quad using first 3 verts."""
    a, b, c = [verts[i] for i in f[:3]]
    ab = (b[0]-a[0], b[1]-a[1], b[2]-a[2])
    ac = (c[0]-a[0], c[1]-a[1], c[2]-a[2])
    nx = ab[1]*ac[2] - ab[2]*ac[1]
    ny = ab[2]*ac[0] - ab[0]*ac[2]
    nz = ab[0]*ac[1] - ab[1]*ac[0]
    return _normalize((nx, ny, nz))


class OBJBuilder:
    def __init__(self, name):
        self.name = name
        self.verts = []   # (x, y, z)
        self.faces = []   # list of vertex index lists (0-based)

    def add_vert(self, x, y, z):
        self.verts.append((x, y, z))
        return len(self.verts) - 1

    def add_face(self, *indices):
        self.faces.append(list(indices))

    # ── Primitive builders ──────────────────────────────────────────

    def add_sphere(self, cx, cy, cz, r, lat=10, lon=16):
        """UV-sphere. Returns base vertex index."""
        base = len(self.verts)
        for i in range(lat + 1):
            phi = math.pi * i / lat - math.pi / 2
            for j in range(lon):
                theta = 2 * math.pi * j / lon
                x = cx + r * math.cos(phi) * math.cos(theta)
                y = cy + r * math.sin(phi)
                z = cz + r * math.cos(phi) * math.sin(theta)
                self.verts.append((x, y, z))
        # Quads
        for i in range(lat):
            for j in range(lon):
                v0 = base + i * lon + j
                v1 = base + i * lon + (j + 1) % lon
                v2 = base + (i + 1) * lon + (j + 1) % lon
                v3 = base + (i + 1) * lon + j
                self.faces.append([v0, v1, v2, v3])
        return base

    def add_ellipsoid(self, cx, cy, cz, rx, ry, rz, lat=8, lon=14):
        base = len(self.verts)
        for i in range(lat + 1):
            phi = math.pi * i / lat - math.pi / 2
            for j in range(lon):
                theta = 2 * math.pi * j / lon
                x = cx + rx * math.cos(phi) * math.cos(theta)
                y = cy + ry * math.sin(phi)
                z = cz + rz * math.cos(phi) * math.sin(theta)
                self.verts.append((x, y, z))
        for i in range(lat):
            for j in range(lon):
                v0 = base + i * lon + j
                v1 = base + i * lon + (j + 1) % lon
                v2 = base + (i + 1) * lon + (j + 1) % lon
                v3 = base + (i + 1) * lon + j
                self.faces.append([v0, v1, v2, v3])
        return base

    def add_cone(self, cx, cy_base, cz, r, height, segs=10):
        """Cone pointing upward."""
        base = len(self.verts)
        tip_idx = base
        self.verts.append((cx, cy_base + height, cz))
        ring_start = len(self.verts)
        for j in range(segs):
            theta = 2 * math.pi * j / segs
            self.verts.append((cx + r * math.cos(theta), cy_base, cz + r * math.sin(theta)))
        # Side tris
        for j in range(segs):
            v0 = ring_start + j
            v1 = ring_start + (j + 1) % segs
            self.faces.append([tip_idx, v1, v0])
        # Base cap (fan)
        cap_center = len(self.verts)
        self.verts.append((cx, cy_base, cz))
        for j in range(segs):
            v0 = ring_start + j
            v1 = ring_start + (j + 1) % segs
            self.faces.append([cap_center, v0, v1])
        return base

    def add_cylinder(self, cx, cy_bot, cz, r, height, segs=8):
        """Cylinder with caps."""
        base = len(self.verts)
        bot_start = base
        for j in range(segs):
            theta = 2 * math.pi * j / segs
            self.verts.append((cx + r * math.cos(theta), cy_bot, cz + r * math.sin(theta)))
        top_start = len(self.verts)
        for j in range(segs):
            theta = 2 * math.pi * j / segs
            self.verts.append((cx + r * math.cos(theta), cy_bot + height, cz + r * math.sin(theta)))
        # Side quads
        for j in range(segs):
            v0 = bot_start + j
            v1 = bot_start + (j + 1) % segs
            v2 = top_start + (j + 1) % segs
            v3 = top_start + j
            self.faces.append([v0, v1, v2, v3])
        # Bottom cap
        bc = len(self.verts)
        self.verts.append((cx, cy_bot, cz))
        for j in range(segs):
            self.faces.append([bc, bot_start + (j+1) % segs, bot_start + j])
        # Top cap
        tc = len(self.verts)
        self.verts.append((cx, cy_bot + height, cz))
        for j in range(segs):
            self.faces.append([tc, top_start + j, top_start + (j+1) % segs])
        return base

    def add_tapered_cylinder(self, cx, cy_bot, cz, r_bot, r_top, height, segs=12):
        """Cylinder with different top/bottom radii (frustum / bell shape)."""
        base = len(self.verts)
        bot_start = base
        for j in range(segs):
            theta = 2 * math.pi * j / segs
            self.verts.append((cx + r_bot * math.cos(theta), cy_bot, cz + r_bot * math.sin(theta)))
        top_start = len(self.verts)
        for j in range(segs):
            theta = 2 * math.pi * j / segs
            self.verts.append((cx + r_top * math.cos(theta), cy_bot + height, cz + r_top * math.sin(theta)))
        for j in range(segs):
            v0 = bot_start + j
            v1 = bot_start + (j + 1) % segs
            v2 = top_start + (j + 1) % segs
            v3 = top_start + j
            self.faces.append([v0, v1, v2, v3])
        bc = len(self.verts)
        self.verts.append((cx, cy_bot, cz))
        for j in range(segs):
            self.faces.append([bc, bot_start + (j+1) % segs, bot_start + j])
        tc = len(self.verts)
        self.verts.append((cx, cy_bot + height, cz))
        for j in range(segs):
            self.faces.append([tc, top_start + j, top_start + (j+1) % segs])
        return base

    def add_flat_plane(self, points):
        """Flat quad from 4 (x,y,z) tuples."""
        base = len(self.verts)
        for p in points:
            self.verts.append(p)
        self.faces.append([base, base+1, base+2, base+3])
        return base

    # ── Write ──────────────────────────────────────────────────────

    def write(self, path):
        lines = [
            '# Lembah Karsa 3D — procedural mob model',
            f'o {self.name}',
            '',
        ]
        for x, y, z in self.verts:
            lines.append(f'v {x:.6f} {y:.6f} {z:.6f}')
        lines.append('')

        # Per-face smooth normals: compute vertex normals by averaging adjacent faces
        vn_accum = [(0.0, 0.0, 0.0)] * len(self.verts)
        face_norms = []
        for f in self.faces:
            n = _face_normal(self.verts, f)
            face_norms.append(n)
            for vi in f:
                nx, ny, nz = vn_accum[vi]
                vn_accum[vi] = (nx + n[0], ny + n[1], nz + n[2])

        vn_list = [_normalize(v) for v in vn_accum]
        for nx, ny, nz in vn_list:
            lines.append(f'vn {nx:.4f} {ny:.4f} {nz:.4f}')
        lines.append('')
        lines.append('s 1')

        for f in self.faces:
            parts = ' '.join(f'{vi+1}//{vi+1}' for vi in f)
            lines.append(f'f {parts}')

        with open(path, 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(lines) + '\n')
        print(f'  Wrote {path}  ({len(self.verts)} verts, {len(self.faces)} faces)')


# ─── MOB BUILDERS ───────────────────────────────────────────────────

def build_banaspati():
    """
    Banaspati — roh api/bola api melayang.
    Bentuk: bola utama + 7 lidah api mengarah ke atas + 2 mata oval.
    Skala: tinggi ~1.1 unit, melayang (pivot di bawah).
    """
    b = OBJBuilder('Banaspati')

    # Bola utama (badan)
    b.add_sphere(0, 0.45, 0, r=0.32, lat=10, lon=16)

    # 7 lidah api di bagian atas
    flame_r = [0.0, 0.14, 0.10, 0.18, 0.08, 0.16, 0.12]
    flame_h = [0.55, 0.38, 0.42, 0.30, 0.48, 0.34, 0.45]
    flame_off_a = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    angles = [0, 51, 103, 154, 206, 257, 308]
    for i, ang_deg in enumerate(angles):
        ang = math.radians(ang_deg)
        ox = flame_r[i] * math.cos(ang)
        oz = flame_r[i] * math.sin(ang)
        b.add_cone(ox, 0.65 + flame_off_a[i], oz,
                   r=0.06 + 0.01 * i, height=flame_h[i], segs=6)

    # Mata — dua oval kecil di depan bola
    for side in (-1, 1):
        b.add_ellipsoid(side * 0.12, 0.52, -0.28, rx=0.04, ry=0.055, rz=0.03, lat=4, lon=8)

    return b


def build_tikus_gua():
    """
    Tikus Gua — tikus besar berkaki empat.
    Bentuk: badan lonjong, kepala bulat, 4 kaki, ekor panjang.
    Skala: tinggi ~0.35, panjang ~0.85.
    """
    b = OBJBuilder('TikusGua')

    # Badan — ellipsoid memanjang ke Z
    b.add_ellipsoid(0, 0.18, 0.05, rx=0.18, ry=0.14, rz=0.35, lat=8, lon=12)

    # Kepala — bola agak lebih kecil, maju ke depan
    b.add_sphere(0, 0.22, -0.42, r=0.16, lat=8, lon=12)

    # Moncong — kerucut pendek ke depan
    b.add_cone(0, 0.18, -0.58, r=0.065, height=0.09, segs=8)

    # Telinga kiri & kanan — setengah bola pipih
    for side in (-1, 1):
        b.add_ellipsoid(side * 0.11, 0.36, -0.41, rx=0.05, ry=0.08, rz=0.03, lat=4, lon=8)

    # 4 kaki — silinder pendek
    leg_positions = [
        (-0.14, 0.0, -0.18),
        ( 0.14, 0.0, -0.18),
        (-0.14, 0.0,  0.22),
        ( 0.14, 0.0,  0.22),
    ]
    for lx, ly, lz in leg_positions:
        b.add_cylinder(lx, ly, lz, r=0.045, height=0.14, segs=6)

    # Ekor — rantai silinder kecil melengkung ke belakang
    tail_segs = 7
    for i in range(tail_segs):
        t = i / tail_segs
        tx = math.sin(t * 0.6) * 0.08
        ty = 0.17 - t * 0.12
        tz = 0.38 + t * 0.35
        r = 0.025 * (1 - t * 0.5)
        b.add_cylinder(tx, ty, tz, r=r, height=0.06, segs=5)

    return b


def build_leak():
    """
    Leak (Leyak) — kepala setan Bali melayang tanpa tubuh.
    Bentuk: kepala besar, dua tanduk, taring panjang, mata besar, jeroan menggantung.
    Skala: pusat ~y=0.6, total tinggi ~1.1.
    """
    b = OBJBuilder('Leak')

    # Kepala utama
    b.add_sphere(0, 0.62, 0, r=0.45, lat=12, lon=18)

    # Dua tanduk melengkung (dibuat dari cone bertumpuk)
    for side in (-1, 1):
        for seg in range(4):
            t = seg / 4
            hx = side * (0.22 + t * 0.18)
            hy = 0.95 + t * 0.35 + seg * 0.07
            hz = -0.05 + t * 0.08
            b.add_cone(hx, hy, hz, r=0.045 - t * 0.025, height=0.14, segs=6)

    # Mata besar (bola menonjol)
    for side in (-1, 1):
        b.add_sphere(side * 0.20, 0.70, -0.38, r=0.10, lat=6, lon=10)
        # Pupil
        b.add_sphere(side * 0.20, 0.70, -0.48, r=0.045, lat=4, lon=8)

    # Mulut terbuka — dua taring panjang
    for ox in (-0.10, 0.10):
        b.add_cone(ox, 0.22, -0.38, r=0.04, height=-0.26, segs=6)  # height negatif = ke bawah

    # Lidah menjulur keluar
    b.add_ellipsoid(0, 0.18, -0.42, rx=0.06, ry=0.04, rz=0.14, lat=4, lon=8)

    # Jeroan menggantung ke bawah (5 untaian)
    entail_xs = [0.0, -0.15, 0.15, -0.25, 0.25]
    entail_h  = [0.40, 0.30, 0.28, 0.22, 0.18]
    for ex, eh in zip(entail_xs, entail_h):
        # Silinder utama
        b.add_cylinder(ex, 0.18 - eh, 0.05, r=0.035, height=eh, segs=6)
        # Ujung bulat
        b.add_sphere(ex, 0.18 - eh, 0.05, r=0.055, lat=4, lon=8)

    return b


def build_kuntilanak():
    """
    Kuntilanak — hantu wanita berambut panjang berdiri melayang.
    Bentuk: gaun lebar ke bawah, torso ramping, kepala bulat, rambut panjang,
            lengan terentang ke samping.
    Skala: tinggi ~1.85 unit.
    """
    b = OBJBuilder('Kuntilanak')

    # Gaun bawah — kerucut terpotong melebar ke bawah
    b.add_tapered_cylinder(0, 0.0, 0, r_bot=0.55, r_top=0.22, height=0.75, segs=16)

    # Torso — silinder ramping
    b.add_tapered_cylinder(0, 0.75, 0, r_bot=0.18, r_top=0.14, height=0.45, segs=12)

    # Leher
    b.add_cylinder(0, 1.20, 0, r=0.07, height=0.10, segs=8)

    # Kepala
    b.add_sphere(0, 1.50, 0, r=0.22, lat=10, lon=14)

    # Mata kosong (lekukan gelap) — bola kecil tertanam
    for side in (-1, 1):
        b.add_sphere(side * 0.09, 1.52, -0.19, r=0.05, lat=4, lon=8)

    # Rambut panjang — 8 untaian menggantung dari kepala ke bawah
    hair_count = 8
    for i in range(hair_count):
        ang = 2 * math.pi * i / hair_count
        hx0 = 0.15 * math.cos(ang)
        hz0 = 0.15 * math.sin(ang)
        # Rambut bergerak sedikit ke samping dan ke belakang
        drift_x = hx0 * 0.8 + (0.1 if math.cos(ang) > 0 else -0.1)
        drift_z = hz0 * 0.5 + 0.15  # sedikit ke belakang
        seg_count = 6
        for s in range(seg_count):
            t0 = s / seg_count
            t1 = (s + 1) / seg_count
            sx = hx0 + drift_x * t0
            sz = hz0 + drift_z * t0
            sy = 1.38 - t0 * 1.30
            b.add_cylinder(sx, sy - 0.11, sz, r=0.025, height=0.24, segs=4)

    # Lengan kiri & kanan — terentang, sedikit turun
    for side in (-1, 1):
        arm_segs = 4
        for s in range(arm_segs):
            t = s / arm_segs
            ax = side * (0.18 + t * 0.35)
            ay = 1.05 - t * 0.10
            az = 0.0
            b.add_cylinder(ax, ay - 0.04, az, r=0.048 - t * 0.010, height=0.12, segs=6)
        # Tangan
        b.add_sphere(side * 0.60, 0.96, 0, r=0.055, lat=4, lon=8)

    # Cakar jari tangan (3 per tangan)
    for side in (-1, 1):
        for fi in range(3):
            fang = math.radians(-20 + fi * 20)
            fx = side * 0.63 + math.cos(fang) * 0.06 * side
            fy = 0.96 - 0.02
            fz = math.sin(fang) * 0.05
            b.add_cone(fx, fy, fz, r=0.015, height=0.08 * side * (-1), segs=4)

    return b


# ─── MAIN ─────────────────────────────────────────────────────────

def main():
    builders = [
        ('mob_banaspati',  build_banaspati),
        ('mob_tikus_gua',  build_tikus_gua),
        ('mob_leak',       build_leak),
        ('mob_kuntilanak', build_kuntilanak),
    ]
    for filename, builder_fn in builders:
        obj = builder_fn()
        out_path = os.path.join(OUT_DIR, f'{filename}.obj')
        obj.write(out_path)
    print('Done.')


if __name__ == '__main__':
    main()
