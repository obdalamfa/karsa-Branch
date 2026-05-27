"""
actor.py — Vitaboy runtime actor: mesh + skeleton + animasi yang dapat di-update tiap frame.

Tiap `VitaboyActor` membungkus:
  - VitaboyMesh (geometri)
  - Skeleton (struktur tulang)
  - Animation (data keyframe — opsional)
  - Ursina Entity (visual)

API:
    actor = VitaboyActor(mesh_path, skel_path=None, anim_path=None)
    actor.entity.position = Vec3(...)
    actor.set_animation('a2o-broom-fly-leftside')  # ganti animasi
    actor.update(dt)   # panggil tiap frame

Implementasi skinning:
  1. Tiap frame, ambil bone pose (translation + rotation) dari animation di frame current.
  2. Tulis ke bone.translation / bone.rotation.
  3. Skeleton.recompute_absolute_matrices() → FK.
  4. Untuk tiap vertex, transform pakai bone.absolute_matrix berdasarkan bone_index.
  5. Update Ursina Mesh.vertices in-place + Mesh.generate().

Catatan: skinning ini "rigid" (1 bone per vertex, tanpa blend weight). Vitaboy
sebenarnya support 2-bone blend via BlendData — itu Phase 6b nanti.
"""
from __future__ import annotations
from typing import Optional, List, Dict
from pathlib import Path

from .mesh import VitaboyMesh, Vec3
from .skeleton import Skeleton, Mat4, Bone, Quat
from .animation import Animation
from .tso_paths import skeleton_path, find_animations


class VitaboyActor:
    def __init__(self, mesh_path: str, skel_path: Optional[str] = None,
                 anim_path: Optional[str] = None,
                 entity_kwargs: Optional[dict] = None):
        # Load assets
        self.mesh = VitaboyMesh.from_file(mesh_path)
        if skel_path is None:
            real = skeleton_path('adult')
            if real:
                skel_path = str(real)
        if skel_path is None:
            raise RuntimeError("VitaboyActor: skel_path required atau adult.skel tidak ditemukan")
        self.skeleton = Skeleton.from_file(skel_path)
        self.animation: Optional[Animation] = None

        # Save bind-pose: kita perlu restore bone.translation/rotation kalau
        # tidak ada motion track untuk bone tersebut di animasi
        self._bind_pose: Dict[str, tuple] = {}
        for b in self.skeleton.bones:
            self._bind_pose[b.name] = (
                Vec3(b.translation.x, b.translation.y, b.translation.z),
                Quat(b.rotation.x, b.rotation.y, b.rotation.z, b.rotation.w),
            )

        # Per-vertex bone matrix lookup: bone_index in mesh.bone_bindings → bone name → skeleton bone
        self._bind_idx_to_bone: Dict[int, Optional[Bone]] = {}
        for binding in self.mesh.bone_bindings:
            self._bind_idx_to_bone[binding.bone_index] = self.skeleton.get_bone(binding.bone_name)

        # Animation playback state
        self._anim_time: float = 0.0
        self.fps: int = 30
        self.loop: bool = True
        self.playing: bool = True
        self.speed: float = 1.0

        # Build Ursina Mesh + Entity
        from ursina import Entity, Mesh as UMesh, Vec3 as UVec3
        # Initial bake (bind pose)
        positions, normals, uvs, tris = self._bake_vertices()
        self._u_verts  = [UVec3(*p) for p in positions]
        self._u_norms  = [UVec3(*n) for n in normals]
        self._u_uvs    = uvs
        self._u_tris   = tris
        self.umesh = UMesh(vertices=self._u_verts, triangles=self._u_tris,
                           normals=self._u_norms, uvs=self._u_uvs,
                           mode='triangle', static=False)
        ekw = dict(model=self.umesh)
        if entity_kwargs:
            ekw.update(entity_kwargs)
        self.entity = Entity(**ekw)

        # Load initial animation kalau diberi
        if anim_path:
            self.set_animation_file(anim_path)

    # ─── ANIMATION CONTROL ──────────────────────────────────────────────────
    def set_animation_file(self, anim_path: str):
        """Load animasi dari .anim file."""
        self.animation = Animation.from_file(anim_path)
        self.fps = self.animation.fps if self.animation.fps > 0 else 30
        self._anim_time = 0.0

    def set_animation(self, name: str) -> bool:
        """Cari animasi by name (substring case-insensitive) di registry.
        Coba registry FAR3 dulu (5000+ anim), fallback ke folder file."""
        from .registry import asset_registry
        anim = asset_registry().load_anim(name)
        if anim:
            self.animation = anim
            self.fps = anim.fps if anim.fps > 0 else 30
            self._anim_time = 0.0
            return True
        # Fallback: folder-based scan
        for ap in find_animations():
            if name.lower() in ap.name.lower():
                self.set_animation_file(str(ap))
                return True
        return False

    def stop_animation(self):
        self.animation = None
        self._restore_bind_pose()
        self._rebake()

    # ─── UPDATE (panggil tiap frame) ────────────────────────────────────────
    def update(self, dt: float):
        if not self.animation or not self.playing:
            return
        a = self.animation
        if a.num_frames <= 0:
            return
        # Advance time
        self._anim_time += dt * self.speed
        total_dur = a.duration if a.duration > 0 else (a.num_frames / max(self.fps, 1))
        if self.loop:
            self._anim_time %= total_dur
        else:
            if self._anim_time >= total_dur:
                self._anim_time = total_dur
                self.playing = False

        frame_f = (self._anim_time / total_dur) * (a.num_frames - 1)
        frame = int(frame_f) % a.num_frames

        # Set bone pose dari frame
        self._restore_bind_pose()
        for motion in a.motions:
            bone = self.skeleton.get_bone(motion.bone_name)
            if bone is None:
                continue
            if motion.has_translation and motion.frame_count > 0:
                idx = motion.first_translation_index + min(frame, motion.frame_count - 1)
                if 0 <= idx < len(a.translations):
                    t = a.translations[idx]
                    bone.translation = Vec3(t.x, t.y, t.z)
            if motion.has_rotation and motion.frame_count > 0:
                idx = motion.first_rotation_index + min(frame, motion.frame_count - 1)
                if 0 <= idx < len(a.rotations):
                    r = a.rotations[idx]
                    bone.rotation = Quat(r.x, r.y, r.z, r.w)

        # FK
        self.skeleton.recompute_absolute_matrices()
        # Re-bake mesh
        self._rebake()

    # ─── INTERNAL ───────────────────────────────────────────────────────────
    def _restore_bind_pose(self):
        for b in self.skeleton.bones:
            bp = self._bind_pose.get(b.name)
            if bp:
                t, r = bp
                b.translation = Vec3(t.x, t.y, t.z)
                b.rotation = Quat(r.x, r.y, r.z, r.w)

    def _bake_vertices(self):
        """Transform tiap vertex pakai bone.absolute_matrix → world space.
        Return (positions, normals, uvs, triangles).
        """
        n_verts = len(self.mesh.vertices)
        positions = [None] * n_verts
        normals = [None] * n_verts
        uvs = [None] * n_verts
        identity = Mat4.identity()
        for i, v in enumerate(self.mesh.vertices):
            bone = self._bind_idx_to_bone.get(v.bone_index)
            bm = bone.absolute_matrix if bone else identity
            p = bm.transform_point(v.position)
            n = bm.transform_direction(v.normal)
            positions[i] = (p.x, p.y, p.z)
            normals[i] = (n.x, n.y, n.z)
            uvs[i] = (v.uv.x, 1.0 - v.uv.y)
        # Reversed winding (kompensasi X-flip seperti di loader.py)
        tris = []
        ib = self.mesh.index_buffer
        for f in range(self.mesh.num_primitives):
            a, b, c = ib[f*3], ib[f*3+1], ib[f*3+2]
            tris.append((a, c, b))
        return positions, normals, uvs, tris

    def _rebake(self):
        from ursina import Vec3 as UVec3
        positions, normals, _, _ = self._bake_vertices()
        # Update vertex list in-place
        for i, p in enumerate(positions):
            self._u_verts[i] = UVec3(*p)
        for i, n in enumerate(normals):
            self._u_norms[i] = UVec3(*n)
        # Trigger mesh rebuild
        self.umesh.vertices = self._u_verts
        self.umesh.normals = self._u_norms
        try:
            self.umesh.generate()
        except Exception:
            # Ursina Mesh.generate() butuh model attached — fallback: recreate
            pass
