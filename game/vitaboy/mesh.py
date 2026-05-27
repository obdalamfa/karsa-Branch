"""
mesh.py — Port `tso.vitaboy.model/Mesh.cs` (FreeSO) ke Python.

Membaca file .mesh Vitaboy: vertex (pos + normal + UV), bone bindings,
blend data, dan index buffer. X-axis di-negate (FreeSO punya convention berbeda).

Format:
  int32 version
  int32 bone_count → string[boneCount] (pascal)
  int32 face_count → int32[face_count * 3] (triangles)
  int32 binding_count → BoneBinding[binding_count]
  int32 real_vertex_count → (float, float)[] UVs
  int32 blend_vertex_count → BlendData[]
  int32 real_vertex_count2 → (Vec3 pos, Vec3 normal)[real_vertex_count]
  (Vec3 pos, Vec3 normal)[blend_vertex_count] — blend verts/normals

Lisensi: porting kode FreeSO (GPL v3).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
from .bcf_reader import BCFReader


@dataclass
class Vec3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclass
class Vec2:
    x: float = 0.0
    y: float = 0.0


@dataclass
class VitaboyVertex:
    position: Vec3 = field(default_factory=Vec3)
    normal: Vec3 = field(default_factory=Vec3)
    uv: Vec2 = field(default_factory=Vec2)
    bone_index: int = 0    # set later via bone bindings


@dataclass
class BoneBinding:
    bone_index: int
    first_real_vertex: int
    real_vertex_count: int
    first_blend_vertex: int
    blend_vertex_count: int
    bone_name: str = ""


@dataclass
class BlendData:
    weight: float
    other_vertex: int


class VitaboyMesh:
    """Mesh karakter Vitaboy yang sudah di-parse dari file .mesh."""

    def __init__(self):
        self.skin_name: str = ""
        self.texture_name: str = ""
        self.bone_names: List[str] = []
        self.index_buffer: List[int] = []            # 3 per face
        self.bone_bindings: List[BoneBinding] = []
        self.vertices: List[VitaboyVertex] = []      # real vertices
        self.blend_data: List[BlendData] = []
        self.blend_verts: List[Vec3] = []
        self.blend_normals: List[Vec3] = []
        self.num_primitives: int = 0

    @classmethod
    def from_file(cls, path: str, bmf: bool = False) -> 'VitaboyMesh':
        with open(path, 'rb') as f:
            r = BCFReader(f)
            m = cls()
            m.read(r, bmf)
            return m

    def read(self, io: BCFReader, bmf: bool = False):
        if bmf:
            self.skin_name = io.read_pascal_string()
            self.texture_name = io.read_pascal_string()
        else:
            _version = io.read_int32()

        # Bone names
        bone_count = io.read_int32()
        self.bone_names = [io.read_pascal_string() for _ in range(bone_count)]

        # Index buffer (face triangles)
        face_count = io.read_int32()
        self.num_primitives = face_count
        self.index_buffer = [0] * (face_count * 3)
        for i in range(face_count):
            self.index_buffer[i*3 + 0] = io.read_int32()
            self.index_buffer[i*3 + 1] = io.read_int32()
            self.index_buffer[i*3 + 2] = io.read_int32()

        # Bone bindings
        binding_count = io.read_int32()
        self.bone_bindings = []
        for _ in range(binding_count):
            b = BoneBinding(
                bone_index=io.read_int32(),
                first_real_vertex=io.read_int32(),
                real_vertex_count=io.read_int32(),
                first_blend_vertex=io.read_int32(),
                blend_vertex_count=io.read_int32(),
            )
            idx = min(len(self.bone_names) - 1, b.bone_index)
            b.bone_name = self.bone_names[idx] if self.bone_names else ""
            self.bone_bindings.append(b)

        # Real vertex UVs (pass 1)
        real_vertex_count = io.read_int32()
        self.vertices = [VitaboyVertex() for _ in range(real_vertex_count)]
        for i in range(real_vertex_count):
            self.vertices[i].uv = Vec2(io.read_float(), io.read_float())

        # Blend data
        blend_vertex_count = io.read_int32()
        self.blend_data = []
        # Note: IoBuffer branch reads (Weight as int32 / 0x8000, OtherVertex int32).
        # BCFReadProxy (non-IoBuffer) reads (OtherVertex, Weight) — but standalone
        # .mesh files always use IoBuffer path.
        for _ in range(blend_vertex_count):
            weight_raw = io.read_int32()
            other = io.read_int32()
            self.blend_data.append(BlendData(weight=weight_raw / 0x8000, other_vertex=other))

        # Pass 2: real vertex positions + normals (X negated)
        _real2 = io.read_int32()
        for i in range(real_vertex_count):
            self.vertices[i].position = Vec3(
                -io.read_float(),
                 io.read_float(),
                 io.read_float()
            )
            self.vertices[i].normal = Vec3(
                -io.read_float(),
                 io.read_float(),
                 io.read_float()
            )
            n = self.vertices[i].normal
            if n.x == 0.0 and n.y == 0.0 and n.z == 0.0:
                self.vertices[i].normal = Vec3(0, 1, 0)

        # Blend vertices + normals
        self.blend_verts = []
        self.blend_normals = []
        for _ in range(blend_vertex_count):
            self.blend_verts.append(Vec3(-io.read_float(), io.read_float(), io.read_float()))
            self.blend_normals.append(Vec3(-io.read_float(), io.read_float(), io.read_float()))

        # Apply bone bindings → set vertex.bone_index per range
        for b in self.bone_bindings:
            for i in range(b.first_real_vertex, b.first_real_vertex + b.real_vertex_count):
                if 0 <= i < len(self.vertices):
                    self.vertices[i].bone_index = b.bone_index
