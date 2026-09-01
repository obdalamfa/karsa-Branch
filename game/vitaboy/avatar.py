"""
avatar.py — Assembly multi-part Vitaboy avatar (Phase 9).

Sebuah avatar TSO terdiri dari beberapa mesh terpisah:
  - Body (terikat ke bone PELVIS atau ROOT)
  - Head (HEAD)
  - Left hand (L_HAND)
  - Right hand (R_HAND)
  - Hair (HEAD)
  - Accessory (variasi bone)

Tiap part = 1 binding = 1 mesh + 1 texture.

Konfigurasi avatar:
    avatar = VitaboyAvatar(parent_entity, [
        'fabd000_sl__defaultpjs.apr',   # body + clothing
        'fahd001_alt.apr',              # head
        'fahl003_longhair02.apr',       # hair
        # hands biasanya termasuk di body apr, atau pisah
    ])
    avatar.set_animation('a2a-talk-idle-loop')
    avatar.update(dt)

Tiap update: skeleton di-pose, semua part re-bake dengan transform bone yang sama.
"""
from __future__ import annotations
import io as _io
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from pathlib import Path

from .bcf_reader import BCFReader
from .mesh import VitaboyMesh, Vec3
from .skeleton import Skeleton, Mat4, Quat
from .animation import Animation
from .appearance import Appearance, Binding
from .registry import asset_registry


@dataclass
class AvatarPart:
    """Satu sub-mesh dalam avatar."""
    binding: Binding
    mesh: VitaboyMesh
    texture_bytes: Optional[bytes] = None
    texture_name: str = ''
    # True kalau .apr-nya kepala -> teksturnya dicat ulang jadi wajah chibi
    wajah_chibi: bool = False
    # True kalau .apr-nya mesh RAMBUT terpisah -> warnanya saja yang diganti
    rambut_chibi: bool = False
    # Ursina runtime objects
    entity = None
    umesh = None
    u_verts: list = field(default_factory=list)
    u_norms: list = field(default_factory=list)
    u_tris:  list = field(default_factory=list)
    u_uvs:   list = field(default_factory=list)


class VitaboyAvatar:
    """Multi-mesh avatar (body+head+hands) skinned ke 1 skeleton bersama."""

    # Counter global untuk stagger init phase antar avatar (supaya update tidak nge-bunch)
    _stagger_counter = 0

    def __init__(self, parent_entity, appearance_names: List[str],
                 scale: float = 0.30, tint=None, varian=None):
        from ursina import Entity, Vec3 as UVec3, color, Texture
        from PIL import Image
        from ..wajah import (apr_kepala, apr_rambut, tekstur_kepala_chibi,
                             tekstur_rambut_chibi, varian_wajah)
        if varian is None:
            varian = varian_wajah('')

        self.skeleton: Optional[Skeleton] = None
        self.parts: List[AvatarPart] = []
        self.animation: Optional[Animation] = None
        self._anim_time: float = 0.0
        self.fps: int = 30
        self.loop: bool = True
        self.playing: bool = True
        self.speed: float = 1.0
        # Throttle: re-bake max 10× per detik supaya tidak menghabiskan CPU Python
        self._update_interval: float = 1.0 / 10.0
        # Stagger: offset awal random kecil supaya avatar tidak update di frame sama
        VitaboyAvatar._stagger_counter = (VitaboyAvatar._stagger_counter + 1) % 10
        self._update_accum: float = (VitaboyAvatar._stagger_counter / 10.0) * self._update_interval
        # Skip update kalau parent entity disabled (off-scene)
        self._parent_entity = parent_entity

        reg = asset_registry()
        self.skeleton = reg.load_skel('adult')
        if self.skeleton is None:
            raise RuntimeError("VitaboyAvatar: adult.skel tidak ada di registry")

        # Save bind pose untuk reset tiap frame
        self._bind_pose: Dict[str, tuple] = {}
        for b in self.skeleton.bones:
            self._bind_pose[b.name] = (
                Vec3(b.translation.x, b.translation.y, b.translation.z),
                Quat(b.rotation.x, b.rotation.y, b.rotation.z, b.rotation.w),
            )

        # ── Load each appearance & build parts ────────────────────────────
        if tint is None:
            tint = color.white
        # Proporsi chibi + ganti rugi tingginya, sama persis dengan jalur
        # native di `vitaboy_baked.py`. Dua jalur ini harus menghasilkan
        # sosok yang sama; kalau tidak, mesin tanpa Character Panda3D akan
        # diam-diam menampilkan warga desa berproporsi berbeda.
        from ..wajah import SKALA_TINGGI
        self.root_entity = Entity(parent=parent_entity, scale=scale * SKALA_TINGGI)

        for apr_name in appearance_names:
            if not apr_name:
                continue
            apr_bytes = reg.read_bytes(apr_name)
            if apr_bytes is None:
                logging.warning(f"VitaboyAvatar: appearance '{apr_name}' tidak ditemukan")
                continue
            apr = Appearance.from_bytes(apr_bytes)
            for ref in apr.bindings:
                bnd_data = reg.read_by_id(ref.type_id, ref.file_id)
                if bnd_data is None:
                    continue
                bnd = Binding.from_bytes(bnd_data)
                if not bnd.has_mesh:
                    continue
                mesh_data = reg.read_by_id(bnd.mesh_type_id, bnd.mesh_file_id)
                if mesh_data is None:
                    continue
                mesh = VitaboyMesh()
                try:
                    mesh.read(BCFReader(_io.BytesIO(mesh_data)), bmf=False)
                except Exception as e:
                    logging.warning(f"VitaboyAvatar: mesh parse gagal: {e}")
                    continue

                part = AvatarPart(binding=bnd, mesh=mesh)
                # Load texture
                if bnd.has_texture:
                    tex_data = reg.read_by_id(bnd.texture_type_id, bnd.texture_file_id)
                    if tex_data:
                        part.texture_bytes = tex_data
                        part.wajah_chibi = apr_kepala(apr_name)
                        part.rambut_chibi = apr_rambut(apr_name)
                        part.texture_name = reg.filename_for_id(
                            bnd.texture_type_id, bnd.texture_file_id) or ''

                # Build per-vertex bone lookup
                part._bind_idx_to_bone = {}
                for binding in mesh.bone_bindings:
                    part._bind_idx_to_bone[binding.bone_index] = (
                        self.skeleton.get_bone(binding.bone_name)
                    )

                # Initial bake
                pos, nrm, uvs, tris = self._bake_part(part)
                part.u_verts = [UVec3(*p) for p in pos]
                part.u_norms = [UVec3(*n) for n in nrm]
                part.u_uvs = uvs
                part.u_tris = tris

                from ursina import Mesh as UMesh
                part.umesh = UMesh(
                    vertices=part.u_verts, triangles=part.u_tris,
                    normals=part.u_norms, uvs=part.u_uvs,
                    mode='triangle', static=False
                )

                # Build texture
                texture = None
                if part.texture_bytes:
                    try:
                        img = None
                        vid = varian.get('id', '')
                        if getattr(part, 'wajah_chibi', False):
                            img = tekstur_kepala_chibi(
                                part.texture_bytes, varian=varian,
                                kunci=(bnd.texture_type_id, bnd.texture_file_id,
                                       'chibi', vid))
                        elif getattr(part, 'rambut_chibi', False):
                            img = tekstur_rambut_chibi(
                                part.texture_bytes, varian=varian,
                                kunci=(bnd.texture_type_id, bnd.texture_file_id,
                                       'rambut', vid))
                        if img is None:
                            img = Image.open(_io.BytesIO(part.texture_bytes))
                        texture = Texture(img)
                        texture.filtering = True
                    except Exception as e:
                        logging.warning(f"VitaboyAvatar: tex load gagal: {e}")

                ekw = dict(model=part.umesh, parent=self.root_entity, color=tint)
                if texture:
                    ekw['texture'] = texture
                part.entity = Entity(**ekw)
                self.parts.append(part)

        if not self.parts:
            raise RuntimeError("VitaboyAvatar: tidak ada part yang berhasil di-load")

    # ─── BAKE ────────────────────────────────────────────────────────────
    def _bake_part(self, part: AvatarPart):
        """Re-bake vertex part pakai bone matrices saat ini.
        Tris + UVs di-cache (tidak berubah antar frame)."""
        mesh = part.mesh
        n_v = len(mesh.vertices)
        positions = [None] * n_v
        normals = [None] * n_v
        identity = Mat4.identity()

        from ..wajah import skala_vertex
        for i, v in enumerate(mesh.vertices):
            bone = part._bind_idx_to_bone.get(v.bone_index)
            bm = bone.absolute_matrix if bone else identity
            # Skala chibi terhadap titik asal tulang; lihat vitaboy_baked.py.
            s = skala_vertex(bone.name if bone else '')
            pos = v.position if s == 1.0 else Vec3(v.position.x * s,
                                                   v.position.y * s,
                                                   v.position.z * s)
            p = bm.transform_point(pos)
            n = bm.transform_direction(v.normal)
            positions[i] = (p.x, p.y, p.z)
            normals[i] = (n.x, n.y, n.z)

        # Cached: tris + uvs hanya dihitung pertama kali
        if not getattr(part, '_cached_tris', None):
            tris = []
            ib = mesh.index_buffer
            for f in range(mesh.num_primitives):
                a, b, c = ib[f*3], ib[f*3+1], ib[f*3+2]
                tris.append((a, c, b))   # reversed winding (X negated)
            part._cached_tris = tris
            part._cached_uvs = [(v.uv.x, 1.0 - v.uv.y) for v in mesh.vertices]
        return positions, normals, part._cached_uvs, part._cached_tris

    # ─── ANIMATION ───────────────────────────────────────────────────────
    def set_animation(self, name: str) -> bool:
        anim = asset_registry().load_anim(name)
        if anim is None:
            return False
        if getattr(self, 'animation', None) == anim:
            return True
        self.animation = anim
        self.fps = anim.fps if anim.fps > 0 else 30
        self._anim_time = 0.0
        return True

    def _restore_bind_pose(self):
        for b in self.skeleton.bones:
            t, r = self._bind_pose[b.name]
            b.translation = Vec3(t.x, t.y, t.z)
            b.rotation = Quat(r.x, r.y, r.z, r.w)

    def update(self, dt: float):
        if not self.animation or not self.playing or self.animation.num_frames <= 0:
            return
        # Skip kalau parent entity di-disable atau di-destroy
        try:
            if self._parent_entity and not self._parent_entity.enabled:
                return
        except Exception:
            return

        # Advance anim time tiap frame (smooth interpolation gap)
        self._anim_time += dt * self.speed

        # Throttle: hanya re-bake mesh max 15× per detik
        self._update_accum += dt
        if self._update_accum < self._update_interval:
            return
        self._update_accum = 0.0

        a = self.animation
        total = a.duration if a.duration > 0 else (a.num_frames / max(self.fps, 1))
        if self.loop:
            self._anim_time %= total
        elif self._anim_time >= total:
            self._anim_time = total
            self.playing = False

        frame = int((self._anim_time / total) * (a.num_frames - 1)) % a.num_frames

        # Pose skeleton dari animasi
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

        # FK + re-bake semua part
        self.skeleton.recompute_absolute_matrices()
        from ursina import Vec3 as UVec3
        for part in self.parts:
            pos, nrm, _, _ = self._bake_part(part)
            for i, p in enumerate(pos):
                part.u_verts[i].x, part.u_verts[i].y, part.u_verts[i].z = p
            for i, n in enumerate(nrm):
                part.u_norms[i].x, part.u_norms[i].y, part.u_norms[i].z = n
            try:
                part.umesh.vertices = part.u_verts
                part.umesh.normals = part.u_norms
                part.umesh.generate()
            except Exception:
                pass


# ─── PRESETS ──────────────────────────────────────────────────────────────
DEFAULT_FEMALE_OUTFIT = [
    'fabd000_sl__defaultpjs.apr',   # body + clothes
    'fahd001_alt.apr',              # head
    'fahl003_longhair02.apr',       # hair
]

# `mahd000_proxy.apr` sengaja TIDAK dipakai di sini: teksturnya
# (`c000madrk_proxy.jpg`) adalah petak biru bertaburan tanda tanya — kepala
# placeholder Maxis, bukan wajah. Lihat game/vitaboy_npc.py.
DEFAULT_MALE_OUTFIT = [
    'mabd002_casual.apr',
    'mahd001_ross.apr',
]
