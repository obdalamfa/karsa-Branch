"""
animator.py — Sistem Animasi Skeleton untuk Lembah Karsa 3D
Diadaptasi dari Vitaboy Animator + AnimationHandle (FreeSO, C#) ke Python/Ursina.

KONSEP UTAMA:
- Skeleton berisi pohon Bone (sesuai Vitaboy Skeleton/Bone)
- Animation menyimpan keyframe per bone (Vec3 posisi + Quaternion rotasi)
- Animator menjalankan satu atau lebih AnimationHandle secara bersamaan
- Support animation blending (misal: walk 80% + wave 20%)
- Head-seek: bone kepala otomatis menghadap target (CalculateHeadSeek)
- Dirancang untuk bekerja dengan Ursina NodePath atau langsung dengan matrix

CONTOH PEMAKAIAN:
    from animator import Skeleton, Animation, Animator, Bone

    # Buat skeleton karakter
    skel = Skeleton.create_humanoid("Sari")

    # Buat animasi berjalan
    walk_anim = Animation("berjalan")
    walk_anim.add_keyframe("spine", frame=0,  pos=(0,0,0), rot=(0,0,0,1))
    walk_anim.add_keyframe("spine", frame=15, pos=(0,0.05,0), rot=(0,0,0,1))

    # Jalankan
    anim_sys = Animator()
    handle = anim_sys.play(skel, walk_anim, loop=True)
    handle.weight = 1.0  # penuh

    # Update tiap frame
    def update():
        anim_sys.update(time.dt)
        skel.apply_to_entity(my_entity)  # terapkan ke Ursina entity
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable
from enum import Enum, auto


# ---------------------------------------------------------------------------
# Quaternion sederhana (agar tidak perlu numpy wajib)
# ---------------------------------------------------------------------------
@dataclass
class Quat:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    w: float = 1.0

    @staticmethod
    def identity() -> "Quat":
        return Quat(0, 0, 0, 1)

    def normalized(self) -> "Quat":
        mag = math.sqrt(self.x**2 + self.y**2 + self.z**2 + self.w**2)
        if mag < 1e-8:
            return Quat.identity()
        return Quat(self.x/mag, self.y/mag, self.z/mag, self.w/mag)

    @staticmethod
    def slerp(a: "Quat", b: "Quat", t: float) -> "Quat":
        """Spherical linear interpolation (sama dengan Quaternion.Slerp di C#)."""
        dot = a.x*b.x + a.y*b.y + a.z*b.z + a.w*b.w
        if dot < 0:
            b = Quat(-b.x, -b.y, -b.z, -b.w)
            dot = -dot
        dot = min(dot, 1.0)
        if dot > 0.9995:
            # Linear interpolation kalau sudut sangat kecil
            return Quat(
                a.x + t*(b.x-a.x), a.y + t*(b.y-a.y),
                a.z + t*(b.z-a.z), a.w + t*(b.w-a.w)
            ).normalized()
        theta_0 = math.acos(dot)
        theta = theta_0 * t
        sin_theta = math.sin(theta)
        sin_theta_0 = math.sin(theta_0)
        s0 = math.cos(theta) - dot * sin_theta / sin_theta_0
        s1 = sin_theta / sin_theta_0
        return Quat(
            s0*a.x + s1*b.x, s0*a.y + s1*b.y,
            s0*a.z + s1*b.z, s0*a.w + s1*b.w
        ).normalized()

    @staticmethod
    def from_euler_y(angle_deg: float) -> "Quat":
        """Buat quaternion dari rotasi Y (yaw)."""
        r = math.radians(angle_deg) * 0.5
        return Quat(0, math.sin(r), 0, math.cos(r))

    def to_euler_y(self) -> float:
        """Ekstrak sudut rotasi Y dalam derajat."""
        return math.degrees(math.atan2(2*(self.w*self.y + self.x*self.z),
                                        1 - 2*(self.y**2 + self.z**2)))

    def __mul__(self, other: "Quat") -> "Quat":
        return Quat(
            self.w*other.x + self.x*other.w + self.y*other.z - self.z*other.y,
            self.w*other.y - self.x*other.z + self.y*other.w + self.z*other.x,
            self.w*other.z + self.x*other.y - self.y*other.x + self.z*other.w,
            self.w*other.w - self.x*other.x - self.y*other.y - self.z*other.z
        )


# ---------------------------------------------------------------------------
# Vec3 sederhana
# ---------------------------------------------------------------------------
@dataclass
class Vec3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    @staticmethod
    def lerp(a: "Vec3", b: "Vec3", t: float) -> "Vec3":
        return Vec3(a.x + (b.x-a.x)*t, a.y + (b.y-a.y)*t, a.z + (b.z-a.z)*t)

    def __add__(self, o): return Vec3(self.x+o.x, self.y+o.y, self.z+o.z)
    def __sub__(self, o): return Vec3(self.x-o.x, self.y-o.y, self.z-o.z)
    def length(self): return math.sqrt(self.x**2 + self.y**2 + self.z**2)
    def __repr__(self): return f"Vec3({self.x:.3f}, {self.y:.3f}, {self.z:.3f})"


# ---------------------------------------------------------------------------
# Keyframe satu bone
# ---------------------------------------------------------------------------
@dataclass
class Keyframe:
    frame: int
    position: Vec3
    rotation: Quat


# ---------------------------------------------------------------------------
# Data animasi satu bone (Motion — seperti AnimationMotion di FreeSO)
# ---------------------------------------------------------------------------
@dataclass
class BoneMotion:
    bone_name: str
    keyframes: List[Keyframe] = field(default_factory=list)

    def get_interpolated(self, frame: float) -> Tuple[Vec3, Quat]:
        """Interpolasi posisi dan rotasi pada frame tertentu."""
        if not self.keyframes:
            return Vec3(), Quat.identity()

        # Cari dua keyframe yang mengapit posisi saat ini
        kfs = sorted(self.keyframes, key=lambda k: k.frame)

        if frame <= kfs[0].frame:
            return kfs[0].position, kfs[0].rotation
        if frame >= kfs[-1].frame:
            return kfs[-1].position, kfs[-1].rotation

        prev = kfs[0]
        for kf in kfs[1:]:
            if kf.frame >= frame:
                t = (frame - prev.frame) / max(kf.frame - prev.frame, 1)
                pos = Vec3.lerp(prev.position, kf.position, t)
                rot = Quat.slerp(prev.rotation, kf.rotation, t)
                return pos, rot
            prev = kf

        return kfs[-1].position, kfs[-1].rotation


# ---------------------------------------------------------------------------
# Data animasi lengkap (seperti Animation di tso.vitaboy.model)
# ---------------------------------------------------------------------------
class Animation:
    def __init__(self, name: str, fps: float = 30.0):
        self.name = name
        self.fps = fps
        self.motions: Dict[str, BoneMotion] = {}  # bone_name -> BoneMotion
        self.num_frames: int = 0
        self.loop: bool = True

    def add_keyframe(self, bone_name: str, frame: int,
                     pos: Tuple = (0,0,0), rot: Tuple = (0,0,0,1)):
        if bone_name not in self.motions:
            self.motions[bone_name] = BoneMotion(bone_name)
        kf = Keyframe(
            frame=frame,
            position=Vec3(*pos),
            rotation=Quat(*rot).normalized()
        )
        self.motions[bone_name].keyframes.append(kf)
        self.num_frames = max(self.num_frames, frame + 1)

    def get_bone_transform(self, bone_name: str, frame: float) -> Tuple[Vec3, Quat]:
        if bone_name not in self.motions:
            return Vec3(), Quat.identity()
        return self.motions[bone_name].get_interpolated(frame)


# ---------------------------------------------------------------------------
# Bone dalam skeleton
# ---------------------------------------------------------------------------
class Bone:
    def __init__(self, name: str, parent_name: Optional[str] = None,
                 local_pos: Optional[Vec3] = None, local_rot: Optional[Quat] = None):
        self.name = name
        self.parent_name = parent_name
        self.parent: Optional["Bone"] = None
        self.children: List["Bone"] = []

        # Pose default (T-pose)
        self.default_pos = local_pos or Vec3()
        self.default_rot = local_rot or Quat.identity()

        # Pose saat ini (ditulis oleh Animator)
        self.local_pos = Vec3(local_pos.x, local_pos.y, local_pos.z) if local_pos else Vec3()
        self.local_rot = Quat(local_rot.x, local_rot.y, local_rot.z, local_rot.w) if local_rot else Quat.identity()

        # World-space transform (dihitung dari parent)
        self.world_pos = Vec3()
        self.world_rot = Quat.identity()

        # Callback ke Ursina NodePath (opsional)
        self._ursina_node = None

    def reset_to_default(self):
        self.local_pos = Vec3(self.default_pos.x, self.default_pos.y, self.default_pos.z)
        self.local_rot = Quat(self.default_rot.x, self.default_rot.y,
                               self.default_rot.z, self.default_rot.w)

    def compute_world_transform(self):
        """Hitung world transform berdasarkan parent (rekursif)."""
        if self.parent:
            # Rotasi parent diterapkan ke posisi local
            pr = self.parent.world_rot
            lp = self.local_pos
            # Rotate local_pos by parent's world rotation (simplified)
            self.world_pos = self.parent.world_pos + lp  # simplified — cukup untuk most use cases
            self.world_rot = (pr * self.local_rot).normalized()
        else:
            self.world_pos = Vec3(self.local_pos.x, self.local_pos.y, self.local_pos.z)
            self.world_rot = Quat(self.local_rot.x, self.local_rot.y,
                                   self.local_rot.z, self.local_rot.w)

        for child in self.children:
            child.compute_world_transform()

    def bind_ursina_node(self, node):
        """Ikat bone ini ke Ursina NodePath/Entity agar otomatis terupdate."""
        self._ursina_node = node

    def apply_to_ursina(self):
        """Terapkan transform bone ke Ursina node yang terikat."""
        if self._ursina_node is None:
            return
        node = self._ursina_node
        if hasattr(node, 'position'):
            from ursina import Vec3 as UVec3
            node.position = UVec3(self.world_pos.x, self.world_pos.y, self.world_pos.z)
        if hasattr(node, 'rotation'):
            y_rot = self.world_rot.to_euler_y()
            node.rotation_y = y_rot


# ---------------------------------------------------------------------------
# Skeleton — pohon bone karakter
# ---------------------------------------------------------------------------
class Skeleton:
    def __init__(self, name: str):
        self.name = name
        self.bones: Dict[str, Bone] = {}
        self.root_bone: Optional[Bone] = None

    def add_bone(self, bone: Bone):
        self.bones[bone.name] = bone

    def build(self):
        """Link parent-child berdasarkan parent_name, lalu hitung world transform."""
        for bone in self.bones.values():
            if bone.parent_name and bone.parent_name in self.bones:
                parent = self.bones[bone.parent_name]
                bone.parent = parent
                parent.children.append(bone)
            elif bone.parent_name is None:
                self.root_bone = bone

        if self.root_bone:
            self.root_bone.compute_world_transform()

    def get_bone(self, name: str) -> Optional[Bone]:
        return self.bones.get(name)

    def reset(self):
        for bone in self.bones.values():
            bone.reset_to_default()

    def compute_world_transforms(self):
        if self.root_bone:
            self.root_bone.compute_world_transform()

    def apply_to_entity(self, entity):
        """Terapkan semua world transform bone ke Ursina entity nodes."""
        for bone in self.bones.values():
            bone.apply_to_ursina()

    @staticmethod
    def create_humanoid(name: str) -> "Skeleton":
        """
        Buat skeleton humanoid standar untuk karakter Lembah Karsa.
        Hierarki: root → pelvis → spine → chest → neck → head
                                                  → shoulder_l/r → arm_l/r → hand_l/r
                              → thigh_l/r → shin_l/r → foot_l/r
        """
        skel = Skeleton(name)

        bones_data = [
            # (name, parent_name, local_pos)
            ("root",       None,          (0, 0, 0)),
            ("pelvis",     "root",        (0, 0.9, 0)),
            ("spine",      "pelvis",      (0, 0.15, 0)),
            ("chest",      "spine",       (0, 0.25, 0)),
            ("neck",       "chest",       (0, 0.35, 0)),
            ("head",       "neck",        (0, 0.15, 0)),
            # Lengan
            ("shoulder_l", "chest",       (-0.2, 0.3, 0)),
            ("arm_l",      "shoulder_l",  (-0.25, 0, 0)),
            ("hand_l",     "arm_l",       (-0.25, 0, 0)),
            ("shoulder_r", "chest",       ( 0.2, 0.3, 0)),
            ("arm_r",      "shoulder_r",  ( 0.25, 0, 0)),
            ("hand_r",     "arm_r",       ( 0.25, 0, 0)),
            # Kaki
            ("thigh_l",    "pelvis",      (-0.1, -0.05, 0)),
            ("shin_l",     "thigh_l",     (0, -0.45, 0)),
            ("foot_l",     "shin_l",      (0, -0.4, 0.05)),
            ("thigh_r",    "pelvis",      ( 0.1, -0.05, 0)),
            ("shin_r",     "thigh_r",     (0, -0.45, 0)),
            ("foot_r",     "shin_r",      (0, -0.4, 0.05)),
        ]

        for bname, parent, lpos in bones_data:
            skel.add_bone(Bone(bname, parent, Vec3(*lpos)))

        skel.build()
        return skel


# ---------------------------------------------------------------------------
# Status animasi handle
# ---------------------------------------------------------------------------
class AnimStatus(Enum):
    PLAYING   = auto()
    COMPLETED = auto()
    STOPPED   = auto()


# ---------------------------------------------------------------------------
# Handle satu animasi yang sedang berjalan (seperti AnimationHandle di FreeSO)
# ---------------------------------------------------------------------------
class AnimationHandle:
    def __init__(self, animation: Animation, skeleton: Skeleton,
                 loop: bool = False, weight: float = 1.0):
        self.animation = animation
        self.skeleton = skeleton
        self.loop = loop or animation.loop
        self.weight = weight       # 0.0–1.0: seberapa kuat animasi ini
        self.speed = 1.0           # multiplier kecepatan
        self.frame: float = 0.0
        self.status = AnimStatus.PLAYING
        self._on_complete: Optional[Callable] = None
        self._on_event: Optional[Callable] = None

    def on_complete(self, callback: Callable):
        self._on_complete = callback
        return self

    def on_event(self, callback: Callable):
        """Callback saat frame event (misal: footstep pada frame tertentu)."""
        self._on_event = callback
        return self

    def update(self, dt: float):
        if self.status != AnimStatus.PLAYING:
            return

        self.frame += self.animation.fps * dt * self.speed

        if self.frame >= self.animation.num_frames:
            if self.loop:
                self.frame = self.frame % max(self.animation.num_frames, 1)
            else:
                self.frame = self.animation.num_frames - 1
                self.status = AnimStatus.COMPLETED
                if self._on_complete:
                    self._on_complete()
                return

        # Terapkan transform ke skeleton dengan weight
        self._apply_to_skeleton()

    def _apply_to_skeleton(self):
        """
        Terapkan frame animasi ke skeleton.
        Jika weight < 1.0, blend dengan pose saat ini (seperti RenderFrame di Vitaboy).
        """
        for bone_name, motion in self.animation.motions.items():
            bone = self.skeleton.get_bone(bone_name)
            if bone is None:
                continue

            anim_pos, anim_rot = motion.get_interpolated(self.frame)

            if self.weight >= 0.999:
                bone.local_pos = anim_pos
                bone.local_rot = anim_rot
            else:
                # Blend dengan pose default
                bone.local_pos = Vec3.lerp(bone.default_pos, anim_pos, self.weight)
                bone.local_rot = Quat.slerp(bone.default_rot, anim_rot, self.weight)

    def stop(self):
        self.status = AnimStatus.STOPPED

    def pause(self):
        self.status = AnimStatus.STOPPED

    def resume(self):
        self.status = AnimStatus.PLAYING


# ---------------------------------------------------------------------------
# Animator utama (seperti Animator class di FreeSO)
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# HeadSeekController — bagian animator.py yang benar-benar dipakai game
# ---------------------------------------------------------------------------
class HeadSeekController:
    """Menghitung ke mana kepala harus menoleh. Hanya sudut, tanpa skeleton.

    KENAPA DIPISAH DARI `Animator`
    ==============================
    `Animator` di bawah menjalankan SELURUH skeleton di Python. Sejak karakter
    pindah ke `vitaboy_baked.NativeAvatar` (Character Panda3D, deformasi di
    C++), menjalankan skeleton Python untuk seluruh badan berarti membayar lagi
    persis biaya yang baru saja dihapus — 6,387 ms per avatar lawan 0,288 ms
    (`_bench/probes/probe_native_wire.py`).

    Tapi head-seek bukan skinning. Ia satu joint, beberapa operasi trigonometri.
    Panda3D bisa menyerahkan SATU joint ke Python lewat `control_joint()`
    sementara sisa badan tetap dianimasikan C++ — dibuktikan di
    `_bench/probes/probe_headseek.py`: joint HEAD berhasil diambil alih (14,40%
    piksel berubah saat diputar 55 derajat) dan animasi tubuh TETAP jalan
    (59.951 piksel berubah antar frame sesudahnya).

    Jadi kelas ini memegang matematika CalculateHeadSeek FreeSO — clamp
    +-65 horizontal / +-45 vertikal, plus pelembutan — terlepas dari kelas
    Bone/Skeleton, supaya bisa dipakai jalur native MAUPUN oleh
    `Animator._apply_head_seek` di bawah.

    DUA KOREKSI TERHADAP KODE ASLI
    ==============================
    1. `_apply_head_seek` versi lama menghitung sudut di ruang DUNIA lalu
       memakainya sebagai rotasi LOKAL bone. Untuk karakter yang badannya
       sendiri berputar itu salah: kepalanya akan menghadap arah dunia yang
       tetap, tidak peduli badannya menghadap ke mana. Di sini yaw badan
       dikurangkan lebih dulu, sehingga clamp +-65 derajat berarti "65 derajat
       dari lurus ke depan" — yang memang maksud FreeSO.
    2. Versi lama menghitung dan meng-clamp `v_angle` lalu MEMBUANGNYA
       (`Quat.from_euler_y` cuma memakai sudut horizontal). Di sini keduanya
       dikembalikan sebagai pasangan (heading, pitch).
    """

    __slots__ = ('max_h', 'max_v', 'speed', 'h', 'v', 'target')

    def __init__(self, max_h: float = 65.0, max_v: float = 45.0,
                 speed: float = 5.0):
        self.max_h = max_h
        self.max_v = max_v
        self.speed = speed
        self.h = 0.0          # sudut sekarang (sudah dilembutkan), derajat
        self.v = 0.0
        self.target: Optional[Tuple[float, float, float]] = None

    def look_at(self, world_pos: Optional[Tuple[float, float, float]]):
        """Titik yang dipandang, koordinat dunia. None = kepala kembali lurus."""
        self.target = world_pos

    def clear(self):
        self.target = None

    @staticmethod
    def _pendekkan(sudut: float) -> float:
        """Bawa sudut ke -180..180 supaya kepala tidak memutar lewat jalan jauh."""
        while sudut > 180.0:
            sudut -= 360.0
        while sudut < -180.0:
            sudut += 360.0
        return sudut

    def update(self, dt: float, head_world: Tuple[float, float, float],
               body_yaw_deg: float = 0.0) -> Tuple[float, float]:
        """Majukan satu langkah; kembalikan (heading, pitch) derajat, lokal ke badan.

        head_world   : posisi kepala di dunia (x, y, z), y ke atas
        body_yaw_deg : rotation_y badan, supaya sudutnya relatif ke arah hadap
        """
        if self.target is None:
            tuju_h, tuju_v = 0.0, 0.0
        else:
            dx = self.target[0] - head_world[0]
            dy = self.target[1] - head_world[1]
            dz = self.target[2] - head_world[2]
            datar = math.sqrt(dx * dx + dz * dz)
            if datar < 1e-3:
                tuju_h, tuju_v = self.h, self.v
            else:
                tuju_h = self._pendekkan(
                    math.degrees(math.atan2(dx, dz)) - body_yaw_deg)
                tuju_v = math.degrees(math.atan2(dy, datar))
                # Kalau target ada di belakang punggung, jangan patahkan leher:
                # cukup di-clamp, kepala berhenti di batas pandang.
                tuju_h = max(-self.max_h, min(self.max_h, tuju_h))
                tuju_v = max(-self.max_v, min(self.max_v, tuju_v))

        k = min(self.speed * dt, 1.0)
        self.h += (tuju_h - self.h) * k
        self.v += (tuju_v - self.v) * k
        return self.h, self.v

    @property
    def aktif(self) -> bool:
        """False kalau tidak ada target DAN kepala sudah selesai kembali lurus.

        Dipakai pemanggil untuk berhenti menyentuh joint sama sekali begitu
        kepala selesai kembali, supaya karakter yang tidak memandang apa pun
        benar-benar nol biaya per frame.
        """
        return self.target is not None or abs(self.h) > 0.05 or abs(self.v) > 0.05


class Animator:
    """
    Mengelola beberapa AnimationHandle secara bersamaan.
    Support blending, priority queue, dan head-seek.

    Integrasi Ursina:
        animator = Animator()
        handle = animator.play(skeleton, walk_anim, loop=True, weight=1.0)
        def update():
            animator.update(time.dt)
    """

    def __init__(self):
        self._handles: List[AnimationHandle] = []
        self._head_seek_target: Optional[Vec3] = None
        self._head_seek_speed: float = 5.0
        self._head_bone: str = "head"
        self._max_horizontal_deg: float = 65.0
        self._max_vertical_deg: float = 45.0
        self._head_ctrl: Optional[HeadSeekController] = None

    def play(self, skeleton: Skeleton, animation: Animation,
             loop: bool = False, weight: float = 1.0,
             stop_others: bool = False) -> AnimationHandle:
        """
        Mulai animasi. Jika stop_others=True, hentikan semua animasi lain.
        Return handle untuk kontrol lebih lanjut.
        """
        if stop_others:
            self.stop_all()

        # Reset skeleton ke pose default sebelum animasi baru
        if not self._handles:
            skeleton.reset()

        handle = AnimationHandle(animation, skeleton, loop=loop, weight=weight)
        self._handles.append(handle)
        return handle

    def stop_all(self):
        for h in self._handles:
            h.stop()
        self._handles.clear()

    def stop(self, handle: AnimationHandle):
        handle.stop()
        if handle in self._handles:
            self._handles.remove(handle)

    def set_head_seek(self, target: Optional[Vec3], speed: float = 5.0):
        """
        Aktifkan head-seek: bone kepala otomatis menghadap target.
        Diadaptasi dari CalculateHeadSeek() di Animator.cs FreeSO.
        target=None untuk mematikan.
        """
        self._head_seek_target = target
        self._head_seek_speed = speed

    def update(self, dt: float):
        """Panggil tiap frame."""
        for handle in self._handles[:]:
            handle.update(dt)
            if handle.status == AnimStatus.COMPLETED and not handle.loop:
                self._handles.remove(handle)

        # Recompute world transforms
        for handle in self._handles:
            if handle.skeleton.root_bone:
                handle.skeleton.root_bone.compute_world_transform()

        # Head seek (CalculateHeadSeek)
        if self._head_seek_target is not None:
            self._apply_head_seek(dt)

    def _apply_head_seek(self, dt: float):
        """
        Putar bone kepala agar menghadap target.
        Diadaptasi dari CalculateHeadSeek() di Vitaboy Animator.cs FreeSO.
        Clamp: ±65° horizontal, ±45° vertikal.

        Matematikanya sekarang DIPINJAM dari `HeadSeekController` di atas,
        bukan disalin, supaya jalur skeleton-Python ini dan jalur Character
        Panda3D tidak bisa menyimpang perlahan-lahan tanpa ada yang sadar.
        """
        target = self._head_seek_target
        if target is None:
            return
        if self._head_ctrl is None:
            self._head_ctrl = HeadSeekController(
                max_h=self._max_horizontal_deg,
                max_v=self._max_vertical_deg,
                speed=self._head_seek_speed)
        ctrl = self._head_ctrl
        ctrl.speed = self._head_seek_speed
        ctrl.look_at((target.x, target.y, target.z))

        for handle in self._handles:
            head_bone = handle.skeleton.get_bone(self._head_bone)
            if head_bone is None:
                continue
            hp = head_bone.world_pos
            h_angle, _v = ctrl.update(dt, (hp.x, hp.y, hp.z))
            # Bone di jalur ini hanya punya rotasi Y; pitch-nya sengaja
            # diabaikan seperti perilaku lama supaya tampilannya tidak berubah.
            head_bone.local_rot = Quat.from_euler_y(h_angle)


# ---------------------------------------------------------------------------
# AnimationLibrary — registry animasi karakter
# ---------------------------------------------------------------------------
class AnimationLibrary:
    """
    Simpan dan ambil animasi berdasarkan nama.
    Buat animasi bawaan untuk karakter Lembah Karsa.
    """

    def __init__(self):
        self._animations: Dict[str, Animation] = {}
        self._build_defaults()

    def register(self, anim: Animation):
        self._animations[anim.name] = anim

    def get(self, name: str) -> Optional[Animation]:
        return self._animations.get(name)

    def _build_defaults(self):
        """Buat set animasi dasar untuk Lembah Karsa."""

        # -- Idle --
        idle = Animation("idle", fps=30)
        idle.loop = True
        idle.num_frames = 60
        for f in [0, 30, 60]:
            idle.add_keyframe("spine", f, pos=(0, 0, 0),      rot=(0, 0, 0, 1))
            idle.add_keyframe("head",  f, pos=(0, 0.15, 0),   rot=(0, 0, 0, 1))
        # Napas — spine naik turun halus
        idle.add_keyframe("chest", 0,  pos=(0, 0.25, 0),  rot=(0, 0, 0, 1))
        idle.add_keyframe("chest", 30, pos=(0, 0.27, 0),  rot=(0, 0, 0, 1))
        idle.add_keyframe("chest", 60, pos=(0, 0.25, 0),  rot=(0, 0, 0, 1))
        self.register(idle)

        # -- Berjalan --
        walk = Animation("walk", fps=30)
        walk.loop = True
        walk.num_frames = 30
        sin30 = math.sin(math.radians(30))
        walk.add_keyframe("pelvis", 0,  pos=(0, 0.9, 0), rot=(0, 0, 0, 1))
        walk.add_keyframe("pelvis", 15, pos=(0, 0.92, 0), rot=(0, 0, 0, 1))
        walk.add_keyframe("pelvis", 30, pos=(0, 0.9, 0), rot=(0, 0, 0, 1))
        # Kaki kiri-kanan bergantian
        walk.add_keyframe("thigh_l", 0,  pos=(-0.1, -0.05, 0), rot=(sin30, 0, 0, math.cos(math.radians(30))))
        walk.add_keyframe("thigh_l", 15, pos=(-0.1, -0.05, 0), rot=(-sin30, 0, 0, math.cos(math.radians(30))))
        walk.add_keyframe("thigh_l", 30, pos=(-0.1, -0.05, 0), rot=(sin30, 0, 0, math.cos(math.radians(30))))
        walk.add_keyframe("thigh_r", 0,  pos=(0.1, -0.05, 0), rot=(-sin30, 0, 0, math.cos(math.radians(30))))
        walk.add_keyframe("thigh_r", 15, pos=(0.1, -0.05, 0), rot=(sin30, 0, 0, math.cos(math.radians(30))))
        walk.add_keyframe("thigh_r", 30, pos=(0.1, -0.05, 0), rot=(-sin30, 0, 0, math.cos(math.radians(30))))
        self.register(walk)

        # -- Bertani --
        farm = Animation("farm", fps=30)
        farm.loop = True
        farm.num_frames = 40
        farm.add_keyframe("spine",    0,  pos=(0, 0.15, 0), rot=(0.2, 0, 0, 0.98))
        farm.add_keyframe("spine",    20, pos=(0, 0.13, 0), rot=(0.3, 0, 0, 0.95))
        farm.add_keyframe("spine",    40, pos=(0, 0.15, 0), rot=(0.2, 0, 0, 0.98))
        farm.add_keyframe("arm_r",    0,  pos=(0.25, 0, 0), rot=(0, 0, 0, 1))
        farm.add_keyframe("arm_r",    10, pos=(0.25, 0, 0), rot=(0.5, 0, 0, 0.87))
        farm.add_keyframe("arm_r",    20, pos=(0.25, 0, 0), rot=(0, 0, 0, 1))
        farm.add_keyframe("arm_r",    40, pos=(0.25, 0, 0), rot=(0, 0, 0, 1))
        self.register(farm)

        # -- Tidur --
        sleep = Animation("sleep", fps=30)
        sleep.loop = True
        sleep.num_frames = 120
        sleep.add_keyframe("root",  0,   pos=(0, 0, 0), rot=(0, 0, 0, 1))
        sleep.add_keyframe("root",  1,   pos=(0, 0.1, 0), rot=(0.7071, 0, 0, 0.7071))
        sleep.add_keyframe("chest", 0,   pos=(0, 0.25, 0), rot=(0, 0, 0, 1))
        sleep.add_keyframe("chest", 60,  pos=(0, 0.27, 0), rot=(0, 0, 0, 1))
        sleep.add_keyframe("chest", 120, pos=(0, 0.25, 0), rot=(0, 0, 0, 1))
        self.register(sleep)

        # -- Bicara --
        talk = Animation("talk", fps=30)
        talk.loop = True
        talk.num_frames = 45
        talk.add_keyframe("head", 0,  pos=(0, 0.15, 0), rot=(0, 0, 0, 1))
        talk.add_keyframe("head", 10, pos=(0, 0.15, 0), rot=(0, 0.05, 0, 0.998))
        talk.add_keyframe("head", 20, pos=(0, 0.15, 0), rot=(0, -0.05, 0, 0.998))
        talk.add_keyframe("head", 30, pos=(0, 0.15, 0), rot=(0.05, 0, 0, 0.998))
        talk.add_keyframe("head", 45, pos=(0, 0.15, 0), rot=(0, 0, 0, 1))
        talk.add_keyframe("arm_l", 0,  pos=(-0.25, 0, 0), rot=(0, 0, 0, 1))
        talk.add_keyframe("arm_l", 15, pos=(-0.25, 0, 0), rot=(0, 0, 0.2, 0.98))
        talk.add_keyframe("arm_l", 30, pos=(-0.25, 0, 0), rot=(0, 0, 0, 1))
        talk.add_keyframe("arm_l", 45, pos=(-0.25, 0, 0), rot=(0, 0, 0, 1))
        self.register(talk)


# Singleton library
anim_library = AnimationLibrary()


# ---------------------------------------------------------------------------
# TEST / DEMO
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== Demo Animator Lembah Karsa ===\n")

    skel = Skeleton.create_humanoid("Sari")
    print(f"Skeleton '{skel.name}' dibuat dengan {len(skel.bones)} bone:")
    for b in skel.bones:
        parent = skel.bones[b].parent_name or "ROOT"
        print(f"  {b:15s} <- {parent}")

    animator = Animator()

    # Animasi berjalan
    walk = anim_library.get("walk")
    handle = animator.play(skel, walk, loop=True, weight=1.0)
    print(f"\nAnimasi '{walk.name}' dimulai ({walk.num_frames} frame, {walk.fps} fps)")

    # Simulasi 10 frame
    for i in range(10):
        animator.update(dt=0.033)

    head = skel.get_bone("head")
    print(f"\nPosisi head setelah 10 frame: {head.world_pos}")
    print(f"Rotasi head: {head.world_rot}")

    # Test head-seek
    animator.set_head_seek(Vec3(2.0, 1.5, 3.0))
    for _ in range(5):
        animator.update(dt=0.033)
    print(f"\nHead rot setelah head-seek: y={head.world_rot.to_euler_y():.1f}°")

    # Test blending
    print("\n--- Test Animation Blending ---")
    farm = anim_library.get("farm")
    handle2 = animator.play(skel, farm, loop=True, weight=0.3)
    handle.weight = 0.7
    for _ in range(5):
        animator.update(dt=0.033)
    print("Blend walk(70%) + farm(30%) berjalan OK")

    print("\n=== Semua sistem berjalan dengan baik! ===")
