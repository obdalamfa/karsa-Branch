"""gen_humanoid_obj.py — Generator OBJ humanoid Sims-style tanpa Blender.

Bikin satu humanoid sebagai mesh tunggal dengan topology lathe (silhouette
karakter diputar mengelilingi sumbu Y) plus limb capsules sebagai sub-mesh.

Output: 3d/assets/models/humanoid.obj — lengkap dengan normal & UV.

Cara pakai (sekali jalan, sebelum game start):
    python tools/gen_humanoid_obj.py

Hasil bisa di-load di Ursina via Entity(model='assets/models/humanoid.obj').
"""
from __future__ import annotations
import math
from pathlib import Path


# ─── HUMANOID SILHOUETTE PROFILE (radial sweep di sumbu Y) ──────────────────
# Setiap titik: (y, radius_xz, jenis_part).
# Tinggi total ~3 unit (Sims adult).
_PROFILE = [
    # y    , radius, label
    (0.00,  0.00, 'foot_apex'),
    (0.05,  0.18, 'foot_top'),
    (0.10,  0.16, 'ankle'),
    (0.45,  0.13, 'shin'),
    (0.80,  0.17, 'knee'),
    (1.20,  0.20, 'thigh'),
    (1.50,  0.24, 'hip'),
    (1.60,  0.26, 'pelvis_top'),
    (1.75,  0.24, 'waist'),
    (1.95,  0.30, 'chest'),
    (2.10,  0.34, 'shoulder'),
    (2.20,  0.32, 'shoulder_top'),
    (2.28,  0.16, 'neck_bot'),
    (2.36,  0.13, 'neck_top'),
    (2.46,  0.22, 'jaw'),
    (2.60,  0.28, 'cheek'),
    (2.74,  0.28, 'temple'),
    (2.86,  0.24, 'forehead'),
    (2.94,  0.16, 'crown'),
    (3.00,  0.00, 'apex'),
]


def _gen_lathe(profile, n_radial: int = 24):
    """Lathe sweep — rotate 2D profile around Y axis to get 3D mesh."""
    verts = []   # (x, y, z)
    normals = [] # (nx, ny, nz)
    uvs = []     # (u, v)
    n_rings = len(profile)
    for j, (y, r, _label) in enumerate(profile):
        v = j / max(n_rings - 1, 1)
        for i in range(n_radial + 1):
            u = i / n_radial
            theta = u * 2 * math.pi
            x = r * math.cos(theta)
            z = r * math.sin(theta)
            verts.append((x, y, z))
            # Normal: approximate dari posisi radial (akan dirapikan saat join)
            if r < 0.001:
                ny = 1.0 if y > 1.5 else -1.0
                normals.append((0, ny, 0))
            else:
                normals.append((math.cos(theta), 0, math.sin(theta)))
            uvs.append((u, v))

    # Triangulasi quad per pasangan ring
    tris = []  # (i0, i1, i2)
    ring = n_radial + 1
    for j in range(n_rings - 1):
        for i in range(n_radial):
            a = j * ring + i
            b = a + 1
            c = a + ring
            d = c + 1
            tris.append((a, b, c))
            tris.append((b, d, c))

    return verts, normals, uvs, tris


def _gen_arm(side: float, n_radial: int = 12):
    """Capsule lengan menyamping dari bahu. side = +1 (kanan) atau -1 (kiri).
    Bahu di sekitar Y=2.10, arm panjang turun ke Y=1.05."""
    profile = [
        (2.18, 0.00),    # apex bahu
        (2.18, 0.12),    # bahu
        (2.10, 0.13),    # upper deltoid
        (1.85, 0.11),    # bicep
        (1.55, 0.10),    # elbow
        (1.25, 0.09),    # forearm
        (1.05, 0.10),    # wrist
        (0.95, 0.13),    # hand
        (0.90, 0.00),    # apex hand
    ]
    verts, normals, uvs, tris = [], [], [], []
    n_rings = len(profile)
    # Geser arm ke samping (shoulder offset 0.34 dari center)
    arm_offset = 0.42 * side
    for j, (y, r) in enumerate(profile):
        for i in range(n_radial + 1):
            u = i / n_radial
            theta = u * 2 * math.pi
            x = arm_offset + r * math.cos(theta)
            z = r * math.sin(theta)
            verts.append((x, y, z))
            normals.append((math.cos(theta) * side, 0, math.sin(theta)))
            uvs.append((u, j / max(n_rings - 1, 1)))
    ring = n_radial + 1
    for j in range(n_rings - 1):
        for i in range(n_radial):
            a = j * ring + i
            b = a + 1
            c = a + ring
            d = c + 1
            tris.append((a, b, c))
            tris.append((b, d, c))
    return verts, normals, uvs, tris


def write_obj(path: Path, parts: list):
    """Gabung beberapa part jadi satu OBJ. Setiap part = (verts, normals, uvs, tris)."""
    lines = ['# Lembah Karsa humanoid mesh — gen_humanoid_obj.py']
    v_offset = 0
    n_offset = 0
    t_offset = 0
    for idx, (verts, normals, uvs, tris) in enumerate(parts):
        lines.append(f'o part_{idx}')
        for x, y, z in verts:
            lines.append(f'v {x:.4f} {y:.4f} {z:.4f}')
        for u, vv in uvs:
            lines.append(f'vt {u:.4f} {vv:.4f}')
        for nx, ny, nz in normals:
            lines.append(f'vn {nx:.4f} {ny:.4f} {nz:.4f}')
        for i0, i1, i2 in tris:
            # OBJ index = 1-based, format v/vt/vn
            a = v_offset + i0 + 1
            b = v_offset + i1 + 1
            c = v_offset + i2 + 1
            ua = t_offset + i0 + 1
            ub = t_offset + i1 + 1
            uc = t_offset + i2 + 1
            na = n_offset + i0 + 1
            nb = n_offset + i1 + 1
            nc = n_offset + i2 + 1
            lines.append(f'f {a}/{ua}/{na} {b}/{ub}/{nb} {c}/{uc}/{nc}')
        v_offset += len(verts)
        n_offset += len(normals)
        t_offset += len(uvs)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines), encoding='utf-8')
    print(f'Wrote {path} ({v_offset} verts, {sum(len(p[3]) for p in parts)} tris)')


def main():
    here = Path(__file__).resolve().parent.parent
    out_dir = here / 'assets' / 'models'

    # Body utama (lathe silhouette)
    body = _gen_lathe(_PROFILE, n_radial=24)
    # Lengan kiri & kanan (capsule terpisah, tidak welded — disengaja supaya
    # bisa dianimasikan dengan rotation_y per-arm jika nanti dipisah)
    arm_l = _gen_arm(side=-1, n_radial=12)
    arm_r = _gen_arm(side=+1, n_radial=12)

    write_obj(out_dir / 'humanoid.obj', [body, arm_l, arm_r])

    # Variant: humanoid_torso_only (untuk bisa di-attach limb per-entity Ursina)
    write_obj(out_dir / 'humanoid_body.obj', [body])
    write_obj(out_dir / 'humanoid_arm_l.obj', [arm_l])
    write_obj(out_dir / 'humanoid_arm_r.obj', [arm_r])

    print('Done. Files: humanoid.obj, humanoid_body.obj, humanoid_arm_l.obj, humanoid_arm_r.obj')


if __name__ == '__main__':
    main()
