"""
skeleton.py — Port `tso.vitaboy.model/Skeleton.cs` (FreeSO) ke Python.

Membaca file .skel: pohon bone dengan translation (Vec3) dan rotation (Quat).
X-axis di-negate (sama dengan mesh).

Format:
  uint32 version (kalau !bcf)
  string name (pascal)
  int16 bone_count
  Bone[bone_count]:
    int32 unknown (kalau !bcf)
    string name (pascal)
    string parent_name (pascal)
    byte has_props (kalau !bcf; bcf=True selalu has_props)
    if has_props:
       int32 propertyCount
       for: int32 pairCount; KV[pairCount] (pascal, pascal)
    Vec3 translation (X negated)
    Quat rotation (X positive, Y/Z/W negated)
    int32 can_translate
    int32 can_rotate
    int32 unknown / scale-related

Lisensi: porting kode FreeSO (GPL v3).
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from .bcf_reader import BCFReader
from .mesh import Vec3


@dataclass
class Quat:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    w: float = 1.0


@dataclass
class Mat4:
    """Row-major 4x4 matrix sederhana. M[i] = baris i."""
    m: List[List[float]] = field(default_factory=lambda: [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ])

    @staticmethod
    def identity() -> 'Mat4':
        return Mat4()

    @staticmethod
    def from_translation(t: Vec3) -> 'Mat4':
        m = Mat4()
        m.m[3][0] = t.x
        m.m[3][1] = t.y
        m.m[3][2] = t.z
        return m

    @staticmethod
    def from_quat(q: Quat) -> 'Mat4':
        # Standar conversion quaternion → matrix (row-major, post-multiply convention sama dengan XNA)
        x, y, z, w = q.x, q.y, q.z, q.w
        xx, yy, zz = x*x, y*y, z*z
        xy, xz, yz = x*y, x*z, y*z
        wx, wy, wz = w*x, w*y, w*z
        m = Mat4()
        m.m[0] = [1 - 2*(yy + zz), 2*(xy + wz),     2*(xz - wy),     0.0]
        m.m[1] = [2*(xy - wz),     1 - 2*(xx + zz), 2*(yz + wx),     0.0]
        m.m[2] = [2*(xz + wy),     2*(yz - wx),     1 - 2*(xx + yy), 0.0]
        m.m[3] = [0.0, 0.0, 0.0, 1.0]
        return m

    def __mul__(self, other: 'Mat4') -> 'Mat4':
        """Row-major matrix multiplication: self * other."""
        a = self.m
        b = other.m
        r = Mat4()
        for i in range(4):
            for j in range(4):
                r.m[i][j] = sum(a[i][k] * b[k][j] for k in range(4))
        return r

    def transform_point(self, p: Vec3) -> Vec3:
        """Transform vec3 sebagai titik (with translation). Row-major convention."""
        x = p.x * self.m[0][0] + p.y * self.m[1][0] + p.z * self.m[2][0] + self.m[3][0]
        y = p.x * self.m[0][1] + p.y * self.m[1][1] + p.z * self.m[2][1] + self.m[3][1]
        z = p.x * self.m[0][2] + p.y * self.m[1][2] + p.z * self.m[2][2] + self.m[3][2]
        return Vec3(x, y, z)

    def transform_direction(self, v: Vec3) -> Vec3:
        """Transform vec3 sebagai arah (tanpa translation)."""
        x = v.x * self.m[0][0] + v.y * self.m[1][0] + v.z * self.m[2][0]
        y = v.x * self.m[0][1] + v.y * self.m[1][1] + v.z * self.m[2][1]
        z = v.x * self.m[0][2] + v.y * self.m[1][2] + v.z * self.m[2][2]
        return Vec3(x, y, z)


@dataclass
class Bone:
    name: str = ""
    parent_name: str = "NULL"
    translation: Vec3 = field(default_factory=Vec3)
    rotation: Quat = field(default_factory=Quat)
    can_translate: int = 0
    can_rotate: int = 0
    has_props: bool = False
    properties: List[List[Tuple[str, str]]] = field(default_factory=list)
    children: List['Bone'] = field(default_factory=list)
    index: int = -1
    # Computed
    absolute_position: Vec3 = field(default_factory=Vec3)
    absolute_matrix: Mat4 = field(default_factory=Mat4.identity)


class Skeleton:
    """Skeleton hewan/avatar FreeSO Vitaboy."""

    def __init__(self):
        self.name: str = ""
        self.bones: List[Bone] = []
        self.root: Optional[Bone] = None
        self._by_name: Dict[str, Bone] = {}

    @classmethod
    def from_file(cls, path: str, bcf: bool = False) -> 'Skeleton':
        with open(path, 'rb') as f:
            r = BCFReader(f)
            s = cls()
            s.read(r, bcf)
            return s

    def get_bone(self, name: str) -> Optional[Bone]:
        return self._by_name.get(name)

    def read(self, io: BCFReader, bcf: bool = False):
        if not bcf:
            _version = io.read_uint32()
        self.name = io.read_pascal_string()

        bone_count = io.read_int16()
        self.bones = []
        for i in range(bone_count):
            bone = self._read_bone(io, bcf)
            if bone is None:
                # BCF returns None for empty name → skip-without-increment in C#
                # Tetap loop sampai cukup terisi
                continue
            bone.index = len(self.bones)
            self.bones.append(bone)

        self._by_name = {b.name: b for b in self.bones}
        # Build child lists
        for b in self.bones:
            b.children = [c for c in self.bones if c.parent_name == b.name]
        # Find root
        for b in self.bones:
            if b.parent_name == "NULL":
                self.root = b
                break
        if self.root:
            self._compute_positions(self.root, Mat4.identity())

    def _read_bone(self, io: BCFReader, bcf: bool) -> Optional[Bone]:
        b = Bone()
        if not bcf:
            _unknown = io.read_int32()
        b.name = io.read_pascal_string()
        b.parent_name = io.read_pascal_string()
        b.has_props = bcf or (io.read_byte() > 0)
        if bcf and b.name == "":
            return None
        if b.has_props:
            prop_count = io.read_int32()
            prop: List[Tuple[str, str]] = []
            for _ in range(prop_count):
                pair_count = io.read_int32()
                for _ in range(pair_count):
                    k = io.read_pascal_string()
                    v = io.read_pascal_string()
                    prop.append((k, v))
            b.properties.append(prop)

        xx = -io.read_float()
        b.translation = Vec3(xx, io.read_float(), io.read_float())
        b.rotation = Quat(
            io.read_float(),
            -io.read_float(),
            -io.read_float(),
            -io.read_float(),
        )
        b.can_translate = io.read_int32()
        b.can_rotate = io.read_int32()
        # CanBlend + WiggleValue + WigglePower
        b.can_blend = io.read_int32()
        b.wiggle_value = io.read_float()
        b.wiggle_power = io.read_float()
        return b

    def recompute_absolute_matrices(self):
        """Re-run forward kinematics dari root. Panggil setelah set bone.translation/rotation
        untuk frame baru animasi."""
        if self.root:
            self._compute_positions(self.root, Mat4.identity())

    def _compute_positions(self, bone: Bone, world: Mat4):
        """Hitung absolute matrix tiap bone (rekursif, world-space).

        FreeSO: myWorld = (rotation * translation) * world
        """
        t_mat = Mat4.from_translation(bone.translation)
        r_mat = Mat4.from_quat(bone.rotation)
        local = r_mat * t_mat
        my_world = local * world
        bone.absolute_matrix = my_world
        bone.absolute_position = my_world.transform_point(Vec3(0, 0, 0))
        for c in bone.children:
            self._compute_positions(c, my_world)
