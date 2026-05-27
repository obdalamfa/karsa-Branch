"""blender_gen_models.py — Script Blender untuk generate model 3D Lembah Karsa.

CARA PAKAI:
1. Buka Blender (dengan MCP addon aktif) ATAU jalankan Blender headless:
       blender --background --python tools/blender_gen_models.py
2. Output OBJ akan di-save ke 3d/assets/models/

Model yang di-generate:
  - humanoid.obj         : karakter manusia Sims-style (rig-friendly proportions)
  - naga.obj             : naga Asia panjang berkelok (sungguhan 3D, bukan tumpukan kotak)
  - mob_kelelawar.obj    : kelelawar mob
  - mob_genderuwo.obj    : genderuwo (raksasa berbulu)
  - mob_pocong.obj       : pocong silhouette

Catatan: script ini self-contained — pakai bpy primitives + modifier sederhana.
Tidak butuh asset eksternal.
"""
import bpy
import os
import math
from pathlib import Path

OUT_DIR = Path(bpy.path.abspath('//')).parent / 'assets' / 'models'
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _clear_scene():
    """Hapus semua object di scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def _add_modifier_smooth(obj, levels=2):
    """Tambah subdivision surface untuk smoothing."""
    mod = obj.modifiers.new(name='Subsurf', type='SUBSURF')
    mod.levels = levels
    mod.render_levels = levels


def _join_objects(name: str):
    """Join semua object yang dipilih jadi satu, rename."""
    bpy.ops.object.join()
    bpy.context.object.name = name


def _export_obj(filepath: Path, apply_modifiers=True):
    """Export selected ke OBJ."""
    bpy.ops.wm.obj_export(
        filepath=str(filepath),
        export_selected_objects=True,
        apply_modifiers=apply_modifiers,
        export_normals=True,
        export_uv=True,
        export_materials=False,
        forward_axis='NEGATIVE_Z',
        up_axis='Y',
    )
    print(f'Exported {filepath}')


# ─── HUMANOID (Sims-style) ────────────────────────────────────────────────────
def gen_humanoid():
    _clear_scene()

    # Body parts: head, torso, hip, arms, legs sebagai mesh terpisah lalu dijoin
    parts = []

    # Head: sphere subdivisi
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22, location=(0, 0, 2.65), segments=24, ring_count=16)
    head = bpy.context.object
    head.scale = (1.0, 1.0, 1.1)  # sedikit elongated vertical
    parts.append(head)

    # Neck
    bpy.ops.mesh.primitive_cylinder_add(radius=0.10, depth=0.18, location=(0, 0, 2.42), vertices=16)
    parts.append(bpy.context.object)

    # Torso: cube → subdivide → loop cuts untuk shape
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1.95))
    torso = bpy.context.object
    torso.scale = (0.38, 0.22, 0.45)
    parts.append(torso)

    # Hip (panggul)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1.55))
    hip = bpy.context.object
    hip.scale = (0.32, 0.20, 0.18)
    parts.append(hip)

    # Lengan (×2): capsule
    for side in (-1, 1):
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.10, depth=0.95,
            location=(side * 0.36, 0, 1.65),
            vertices=12
        )
        arm = bpy.context.object
        arm.rotation_euler = (0, 0, 0)  # vertikal
        parts.append(arm)
        # Hand
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=0.10, location=(side * 0.36, 0, 1.10),
            segments=12, ring_count=8
        )
        parts.append(bpy.context.object)

    # Kaki (×2): capsule
    for side in (-1, 1):
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.11, depth=1.35,
            location=(side * 0.14, 0, 0.78),
            vertices=12
        )
        leg = bpy.context.object
        parts.append(leg)
        # Foot
        bpy.ops.mesh.primitive_cube_add(size=1, location=(side * 0.14, 0.10, 0.10))
        foot = bpy.context.object
        foot.scale = (0.11, 0.18, 0.08)
        parts.append(foot)

    # Pilih semua parts & join
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    _join_objects('Humanoid')

    # Apply subdivision smoothing
    _add_modifier_smooth(bpy.context.object, levels=2)
    bpy.ops.object.shade_smooth()

    _export_obj(OUT_DIR / 'humanoid.obj')


# ─── NAGA (dragon panjang berkelok) ───────────────────────────────────────────
def gen_naga():
    _clear_scene()

    parts = []

    # Tubuh: rangkaian 8 sphere yang ditata berkelok
    body_segments = [
        # (x, y, z, scale)
        (0.0,  0.0, 0.50, 0.40),  # ekor ujung
        (0.0,  0.5, 0.50, 0.45),
        (0.0,  1.0, 0.55, 0.55),
        (0.1,  1.6, 0.60, 0.62),
        (0.2,  2.2, 0.65, 0.65),  # body widest
        (0.1,  2.8, 0.70, 0.62),
        (0.0,  3.3, 0.85, 0.55),  # leher mulai naik
        (0.0,  3.7, 1.10, 0.48),  # leher tinggi
        (0.0,  4.0, 1.35, 0.40),  # leher → kepala
    ]
    for x, y, z, s in body_segments:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=s, location=(x, y, z), segments=20, ring_count=12)
        parts.append(bpy.context.object)

    # Kepala
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.45, location=(0, 4.3, 1.50), segments=20, ring_count=12)
    head = bpy.context.object
    head.scale = (1.0, 1.25, 0.9)
    parts.append(head)

    # Moncong
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 4.75, 1.40))
    snout = bpy.context.object
    snout.scale = (0.25, 0.30, 0.20)
    parts.append(snout)

    # Tanduk emas (sepasang melengkung)
    for sx in (-0.18, 0.18):
        bpy.ops.mesh.primitive_cone_add(radius1=0.08, depth=0.45, location=(sx, 4.18, 1.85))
        horn = bpy.context.object
        horn.rotation_euler = (math.radians(-25), math.radians(sx * 60), 0)
        parts.append(horn)

    # Mata
    for sx in (-0.18, 0.18):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.07, location=(sx, 4.45, 1.55), segments=12, ring_count=8)
        parts.append(bpy.context.object)

    # 4 kaki bercakar
    for fx, fy in [(-0.35, 2.0), (0.35, 2.0), (-0.45, 2.7), (0.45, 2.7)]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.16, depth=0.45,
                                             location=(fx, fy, 0.25), vertices=12)
        parts.append(bpy.context.object)
        # Cakar
        bpy.ops.mesh.primitive_cube_add(size=1, location=(fx, fy - 0.15, 0.04))
        claw = bpy.context.object
        claw.scale = (0.20, 0.25, 0.04)
        parts.append(claw)

    # Sirip ekor di belakang
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.4, 0.65))
    fin = bpy.context.object
    fin.scale = (0.45, 0.15, 0.30)
    parts.append(fin)

    bpy.ops.object.select_all(action='DESELECT')
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    _join_objects('Naga')

    _add_modifier_smooth(bpy.context.object, levels=2)
    bpy.ops.object.shade_smooth()

    _export_obj(OUT_DIR / 'naga.obj')


# ─── SUPERNATURAL MOBS ────────────────────────────────────────────────────────
def gen_genderuwo():
    _clear_scene()
    parts = []
    # Tubuh besar
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.85, location=(0, 0, 1.10), segments=24, ring_count=16)
    body = bpy.context.object
    body.scale = (1.0, 0.9, 1.1)
    parts.append(body)
    # Kepala
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.55, location=(0, 0, 2.30), segments=20, ring_count=12)
    parts.append(bpy.context.object)
    # Lengan panjang (×2)
    for side in (-1, 1):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.22, depth=1.40, location=(side * 0.85, 0, 1.30), vertices=12)
        parts.append(bpy.context.object)
    # Kaki (×2)
    for side in (-1, 1):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.22, depth=1.00, location=(side * 0.30, 0, 0.50), vertices=12)
        parts.append(bpy.context.object)
    # Mata merah
    for sx in (-0.20, 0.20):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.08, location=(sx, 0.45, 2.30), segments=10, ring_count=6)
        parts.append(bpy.context.object)
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts: p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    _join_objects('Genderuwo')
    _add_modifier_smooth(bpy.context.object, levels=1)
    bpy.ops.object.shade_smooth()
    _export_obj(OUT_DIR / 'mob_genderuwo.obj')


def gen_pocong():
    _clear_scene()
    parts = []
    # Tubuh terbungkus kain (silinder dengan ujung membulat)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.30, depth=1.80, location=(0, 0, 0.95), vertices=20)
    parts.append(bpy.context.object)
    # Kepala bulat
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.30, location=(0, 0, 1.95), segments=20, ring_count=12)
    parts.append(bpy.context.object)
    # Ikatan tali atas dan bawah
    bpy.ops.mesh.primitive_torus_add(major_radius=0.32, minor_radius=0.04, location=(0, 0, 1.75))
    parts.append(bpy.context.object)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.32, minor_radius=0.04, location=(0, 0, 0.20))
    parts.append(bpy.context.object)
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts: p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    _join_objects('Pocong')
    _add_modifier_smooth(bpy.context.object, levels=1)
    bpy.ops.object.shade_smooth()
    _export_obj(OUT_DIR / 'mob_pocong.obj')


def gen_kelelawar():
    _clear_scene()
    parts = []
    # Tubuh kecil
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.20, location=(0, 0, 0), segments=14, ring_count=10)
    parts.append(bpy.context.object)
    # Kepala
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.18, location=(0, 0.22, 0.05), segments=14, ring_count=10)
    parts.append(bpy.context.object)
    # Telinga lancip (×2)
    for sx in (-0.10, 0.10):
        bpy.ops.mesh.primitive_cone_add(radius1=0.06, depth=0.22, location=(sx, 0.22, 0.20))
        parts.append(bpy.context.object)
    # Sayap (×2) — segitiga datar
    for side in (-1, 1):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(side * 0.45, 0, 0))
        wing = bpy.context.object
        wing.scale = (0.50, 0.02, 0.32)
        wing.rotation_euler = (0, 0, math.radians(side * 15))
        parts.append(wing)
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts: p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    _join_objects('Kelelawar')
    bpy.ops.object.shade_smooth()
    _export_obj(OUT_DIR / 'mob_kelelawar.obj')


# ─── ENTRY ────────────────────────────────────────────────────────────────────
def main():
    print(f'Output dir: {OUT_DIR}')
    gen_humanoid()
    gen_naga()
    gen_genderuwo()
    gen_pocong()
    gen_kelelawar()
    print('Selesai. File OBJ tersimpan.')


if __name__ == '__main__':
    main()
