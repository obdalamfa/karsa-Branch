"""
bake_vitaboy.py — Bake Vitaboy mesh + skeleton + animation → GLTF via Blender.

Tujuan: ganti Python skinning runtime yang lambat dengan GLTF Actor di Panda3D
yang skinning di GPU. Ini script offline — dipanggil sekali per avatar untuk
generate file .gltf yang nantinya di-load real-time oleh game.

PEMAKAIAN (Windows cmd, asumsi blender di PATH):
    blender --background --python tools/bake_vitaboy.py -- \
        --mesh au-blue \
        --skel adult \
        --anim a2a-talk-idle-loop \
        --out assets/vitaboy/sari_idle.gltf

Atau via Python directly (kalau Blender tidak di PATH):
    "C:\\Program Files\\Blender Foundation\\Blender 5.1\\blender.exe" \
        --background --python tools/bake_vitaboy.py -- ...

INPUT yang diperlukan:
- game/vitaboy/ harus sudah ada (parsers .mesh/.skel/.anim)
- TSO install di-discover otomatis lewat tso_paths.py

OUTPUT:
- File .gltf single-file (text JSON + base64-embedded geometry & anim)
- Bisa load di Panda3D: loader.loadModel('sari_idle.gltf')
- Pakai Actor() untuk play animasi

Catatan teknis:
- Skeleton TSO: X-axis di-negate. Translation/rotation sudah ter-negate di parser.
- Mesh vertex: bone_index → bone_name via bone_bindings.
- Animation: keyframe per bone (translation + rotation quaternion).
"""
import sys
import os
import argparse
from pathlib import Path

# Tambah project root ke sys.path supaya bisa import game.vitaboy
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent          # 3d/
sys.path.insert(0, str(_PROJECT_ROOT))

import bpy
import mathutils


def parse_args():
    """Ambil arg setelah `--` (Blender memisah arg pakai `--`)."""
    if '--' in sys.argv:
        argv = sys.argv[sys.argv.index('--') + 1:]
    else:
        argv = []
    p = argparse.ArgumentParser(description="Bake Vitaboy → GLTF")
    p.add_argument('--mesh', required=True, help='Mesh name (e.g. au-blue)')
    p.add_argument('--skel', default='adult', help='Skeleton name (default adult)')
    p.add_argument('--anim', default=None, help='Animation name (optional)')
    p.add_argument('--out', required=True, help='Output .gltf path (relative ke 3d/)')
    return p.parse_args(argv)


# ─── BLENDER SCENE CLEAR ─────────────────────────────────────────────────────
def clear_scene():
    """Hapus semua objek di scene Blender default."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    # Buang collection orphan
    for c in bpy.data.collections:
        if not c.objects:
            bpy.data.collections.remove(c)


# ─── ARMATURE FROM SKELETON ──────────────────────────────────────────────────
def build_armature(skel):
    """Build Blender Armature dari Vitaboy Skeleton (X-up convention).

    TSO skeleton: Y-up, X-left (sudah di-negate parsernya). Blender Z-up, jadi
    kita harus tukar Y↔Z saat translate (vertex juga akan di-tukar).
    """
    # Buat armature data + object
    arm_data = bpy.data.armatures.new("VitaboySkel")
    arm_obj = bpy.data.objects.new("Armature", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj

    # Masuk EDIT mode untuk add bones
    bpy.ops.object.mode_set(mode='EDIT')

    # Buat semua edit_bones — TSO position pakai absolute_position (world)
    # Default: head = position bone, tail = position + (0, 0.1, 0) untuk visual
    eb_by_name = {}
    for bone in skel.bones:
        eb = arm_data.edit_bones.new(bone.name)
        ap = bone.absolute_position
        # Convert Y-up → Z-up: (x, y, z) Vitaboy → (x, z, y) Blender? Atau (x, y, z)?
        # Sebenarnya kita simpan apa adanya, lalu apply rotasi 90° X di parent armature.
        # Lebih simpel: tetap (x, y, z) — saat export pakai axis Y_FORWARD Z_UP.
        eb.head = mathutils.Vector((ap.x, ap.z, ap.y))   # Y-up → Z-up
        # Tail sedikit di atas (sumbu Y Blender = vertical sesudah swap)
        eb.tail = eb.head + mathutils.Vector((0, 0, 0.1))
        eb_by_name[bone.name] = eb

    # Set parent
    for bone in skel.bones:
        if bone.parent_name != "NULL" and bone.parent_name in eb_by_name:
            eb_by_name[bone.name].parent = eb_by_name[bone.parent_name]

    bpy.ops.object.mode_set(mode='OBJECT')
    return arm_obj


# ─── MESH FROM VITABOY ───────────────────────────────────────────────────────
def build_mesh(vmesh, arm_obj, name='Body'):
    """Build Blender Mesh dari VitaboyMesh + attach ke Armature dengan vertex groups."""
    mesh_data = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh_data)
    bpy.context.scene.collection.objects.link(obj)

    # Vertices — convert Y-up → Z-up: (x, y, z) → (x, z, y)
    verts = [(v.position.x, v.position.z, v.position.y) for v in vmesh.vertices]
    # Triangles — reversed winding karena X-negation di parser
    faces = []
    ib = vmesh.index_buffer
    for f in range(vmesh.num_primitives):
        a, b, c = ib[f*3], ib[f*3+1], ib[f*3+2]
        faces.append((a, c, b))

    mesh_data.from_pydata(verts, [], faces)
    mesh_data.update()

    # UVs
    if not mesh_data.uv_layers:
        mesh_data.uv_layers.new(name='UVMap')
    uv_layer = mesh_data.uv_layers[0].data
    # Per face-corner UV
    for poly in mesh_data.polygons:
        for li in poly.loop_indices:
            vert_idx = mesh_data.loops[li].vertex_index
            uv = vmesh.vertices[vert_idx].uv
            # GLTF expects V flipped relative to Vitaboy
            uv_layer[li].uv = (uv.x, 1.0 - uv.y)

    # Normals (split per loop)
    try:
        mesh_data.use_auto_smooth = True
    except Exception:
        pass
    normals = [(v.normal.x, v.normal.z, v.normal.y) for v in vmesh.vertices]
    try:
        mesh_data.normals_split_custom_set_from_vertices(normals)
    except Exception:
        # Blender 5.x mungkin punya API beda — biarkan default
        pass

    # Vertex groups untuk skinning (1 bone per vertex — rigid)
    group_by_bone_idx = {}
    for binding in vmesh.bone_bindings:
        if binding.bone_name not in obj.vertex_groups:
            vg = obj.vertex_groups.new(name=binding.bone_name)
        else:
            vg = obj.vertex_groups[binding.bone_name]
        group_by_bone_idx[binding.bone_index] = vg

        # Tambahkan real vertices ke group
        for i in range(binding.first_real_vertex,
                       binding.first_real_vertex + binding.real_vertex_count):
            vg.add([i], 1.0, 'REPLACE')
        # Blend vertices: untuk MVP ikut bone yang sama (skip 2-bone blend dulu)
        for i in range(binding.first_blend_vertex,
                       binding.first_blend_vertex + binding.blend_vertex_count):
            # Note: blend vertex index ≥ real_count, jadi pakai offset di mesh.vertices
            blend_real_idx = len(vmesh.vertices) - len(vmesh.blend_verts) + (
                i - binding.first_blend_vertex
            )
            if 0 <= blend_real_idx < len(vmesh.vertices):
                vg.add([blend_real_idx], 1.0, 'REPLACE')

    # Add Armature modifier
    arm_mod = obj.modifiers.new(name='Skeleton', type='ARMATURE')
    arm_mod.object = arm_obj

    # Parent mesh ke armature
    obj.parent = arm_obj

    return obj


# ─── ANIMATION ───────────────────────────────────────────────────────────────
def build_action(arm_obj, anim, skel):
    """Build Blender Action dari Vitaboy Animation, attach ke armature."""
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='POSE')

    action = bpy.data.actions.new(name=anim.name or 'Anim')
    arm_obj.animation_data_create()
    arm_obj.animation_data.action = action

    # Set scene FPS
    bpy.context.scene.render.fps = anim.fps if anim.fps > 0 else 30

    fps = max(1, anim.fps if anim.fps > 0 else 30)
    n_frames = max(1, anim.num_frames)

    # Restore bind pose first — store bind translation/rotation
    bind_pose = {}
    for b in skel.bones:
        bind_pose[b.name] = (
            (b.translation.x, b.translation.y, b.translation.z),
            (b.rotation.x, b.rotation.y, b.rotation.z, b.rotation.w),
        )

    # Animate each motion per bone
    for motion in anim.motions:
        bone = arm_obj.pose.bones.get(motion.bone_name)
        if bone is None:
            continue
        bind_t, bind_r = bind_pose[motion.bone_name]

        for f in range(min(motion.frame_count, n_frames)):
            if motion.has_translation:
                idx = motion.first_translation_index + f
                if 0 <= idx < len(anim.translations):
                    t = anim.translations[idx]
                    # Local translation relative to bind: TSO sudah world translation
                    # Sederhana: set langsung (Blender pose offset).
                    bone.location = mathutils.Vector((t.x, t.z, t.y))
                    bone.keyframe_insert('location', frame=f+1)

            if motion.has_rotation:
                idx = motion.first_rotation_index + f
                if 0 <= idx < len(anim.rotations):
                    r = anim.rotations[idx]
                    # Blender quaternion: (w, x, y, z) order
                    bone.rotation_mode = 'QUATERNION'
                    bone.rotation_quaternion = mathutils.Quaternion(
                        (r.w, r.x, r.z, r.y)   # swap Y↔Z untuk Z-up
                    )
                    bone.keyframe_insert('rotation_quaternion', frame=f+1)

    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = n_frames

    bpy.ops.object.mode_set(mode='OBJECT')
    return action


# ─── MAIN ────────────────────────────────────────────────────────────────────
def main():
    args = parse_args()

    # Import parser sekarang (setelah sys.path siap)
    from game.vitaboy import asset_registry

    reg = asset_registry()
    print(f"[bake] Registry stats: {reg.stats()}")

    print(f"[bake] Load skeleton: {args.skel}")
    skel = reg.load_skel(args.skel)
    if skel is None:
        print(f"[bake] FATAL: skeleton '{args.skel}' tidak ditemukan")
        sys.exit(1)
    print(f"[bake]   {len(skel.bones)} bones, root={skel.root.name if skel.root else None}")

    print(f"[bake] Load mesh: {args.mesh}")
    vmesh = reg.load_mesh(args.mesh)
    if vmesh is None:
        print(f"[bake] FATAL: mesh '{args.mesh}' tidak ditemukan")
        sys.exit(1)
    print(f"[bake]   {len(vmesh.vertices)} verts, {vmesh.num_primitives} tris, {len(vmesh.bone_bindings)} bindings")

    anim = None
    if args.anim:
        print(f"[bake] Load anim: {args.anim}")
        anim = reg.load_anim(args.anim)
        if anim is None:
            print(f"[bake] WARNING: anim '{args.anim}' tidak ditemukan, lanjut tanpa anim")
        else:
            print(f"[bake]   {anim.num_frames} frames @ {anim.fps}fps, {len(anim.motions)} motion tracks")

    # ── Build di Blender ─────────────────────────────────
    clear_scene()
    arm_obj = build_armature(skel)
    print(f"[bake] Armature built: {len(arm_obj.data.bones)} bones")

    mesh_obj = build_mesh(vmesh, arm_obj, name=args.mesh)
    print(f"[bake] Mesh built: {len(mesh_obj.data.vertices)} verts, {len(mesh_obj.data.polygons)} faces")

    if anim:
        action = build_action(arm_obj, anim, skel)
        # Blender 5.x menggunakan action.layers/strips, bukan action.fcurves langsung
        n_curves = sum(1 for _ in action.fcurves) if hasattr(action, 'fcurves') else 0
        print(f"[bake] Action built: {action.name} ({n_curves} fcurves)")

    # ── Export GLTF ─────────────────────────────────────
    out_path = args.out
    if not os.path.isabs(out_path):
        out_path = os.path.join(str(_PROJECT_ROOT), out_path)
    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)

    print(f"[bake] Export GLTF: {out_path}")
    # Blender 5.x: hanya GLB (binary, single file) atau GLTF_SEPARATE
    if out_path.lower().endswith('.glb'):
        export_format = 'GLB'
    else:
        # Konversi .gltf → .glb untuk single-file convenience
        out_path = out_path[:-5] + '.glb' if out_path.lower().endswith('.gltf') else out_path + '.glb'
        export_format = 'GLB'
    bpy.ops.export_scene.gltf(
        filepath=out_path,
        export_format=export_format,
        export_apply=False,
        export_animations=True,
        export_skins=True,
        export_yup=True,
    )
    print(f"[bake] DONE → {out_path}")


if __name__ == '__main__':
    main()
