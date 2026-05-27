"""
appearance.py + binding.py — Vitaboy appearance/binding parsers.

`.apr` (appearance, big-endian):
    uint32 version
    uint32 thumb_file_id
    uint32 thumb_type_id
    uint32 num_bindings
    [uint32 file_id, uint32 type_id] × num_bindings   (refs to .bnd)

`.bnd` (binding, big-endian):
    uint32 version (must be 1)
    pascal bone (1-byte len + ascii)
    uint32 mesh_type
    if mesh_type == 8:
        uint32 mesh_group_id
        uint32 mesh_file_id
        uint32 mesh_type_id
    uint32 texture_type
    if texture_type == 8:
        uint32 texture_group_id
        uint32 texture_file_id
        uint32 texture_type_id

Pemakaian:
    apr = Appearance.from_bytes(bytes_from_registry)
    print(apr.bindings)  # list of (file_id, type_id) pairs

    bnd = Binding.from_bytes(bytes)
    print(bnd.bone, bnd.mesh_file_id, bnd.texture_file_id)
"""
from __future__ import annotations
import io as _io
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .bcf_reader import BCFReader


@dataclass
class AppearanceBindingRef:
    file_id: int = 0
    type_id: int = 0


@dataclass
class Appearance:
    name: str = ''
    thumb_file_id: int = 0
    thumb_type_id: int = 0
    bindings: List[AppearanceBindingRef] = field(default_factory=list)
    type: int = 0
    zero: int = 0

    def read(self, io: BCFReader, bcf: bool = False):
        if bcf:
            self.name = io.read_pascal_string()
            self.type = io.read_int32()
            self.zero = io.read_int32()
            n = io.read_uint32()
            # BCF includes bindings verbatim — skip for now (not used by TSO original)
            return
        _version = io.read_uint32()
        self.thumb_file_id = io.read_uint32()
        self.thumb_type_id = io.read_uint32()
        n = io.read_uint32()
        self.bindings = []
        for _ in range(n):
            ref = AppearanceBindingRef(
                file_id=io.read_uint32(),
                type_id=io.read_uint32(),
            )
            self.bindings.append(ref)

    @classmethod
    def from_bytes(cls, data: bytes) -> 'Appearance':
        a = cls()
        a.read(BCFReader(_io.BytesIO(data)))
        return a

    @classmethod
    def from_file(cls, path: str) -> 'Appearance':
        with open(path, 'rb') as f:
            return cls.from_bytes(f.read())


@dataclass
class Binding:
    bone: str = ''
    mesh_group_id: int = 0
    mesh_file_id: int = 0
    mesh_type_id: int = 0
    has_mesh: bool = False
    texture_group_id: int = 0
    texture_file_id: int = 0
    texture_type_id: int = 0
    has_texture: bool = False

    def read(self, io: BCFReader, bcf: bool = False):
        if bcf:
            self.bone = io.read_pascal_string()
            self.has_mesh = True
            # BCF: mesh_name string, censor_flag i32, zero i32 — kita skip resolve, simpan name saja
            return
        _version = io.read_uint32()
        self.bone = io.read_pascal_string()
        mesh_type = io.read_uint32()
        if mesh_type == 8:
            self.has_mesh = True
            self.mesh_group_id = io.read_uint32()
            self.mesh_file_id = io.read_uint32()
            self.mesh_type_id = io.read_uint32()
        texture_type = io.read_uint32()
        if texture_type == 8:
            self.has_texture = True
            self.texture_group_id = io.read_uint32()
            self.texture_file_id = io.read_uint32()
            self.texture_type_id = io.read_uint32()

    @classmethod
    def from_bytes(cls, data: bytes) -> 'Binding':
        b = cls()
        b.read(BCFReader(_io.BytesIO(data)))
        return b

    @classmethod
    def from_file(cls, path: str) -> 'Binding':
        with open(path, 'rb') as f:
            return cls.from_bytes(f.read())
