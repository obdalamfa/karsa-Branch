"""
animation.py — Vitaboy animation parser (port dari Animation.cs / AnimationCodec.cs).

Format .anim (big-endian, TSO non-BCF):
    uint32 version
    long_pascal name        (int16 len + ascii)
    float duration_ms
    float distance
    byte  is_moving
    uint32 translation_count
    Vec3[translation_count]  (X negated)
    uint32 rotation_count
    Quat[rotation_count]     (Y, Z, W negated)
    uint32 motion_count
    Motion[motion_count]:
        uint32 unknown
        pascal bone_name
        uint32 frame_count
        float  duration_ms
        byte   has_translation
        byte   has_rotation
        int32  first_translation_index
        int32  first_rotation_index
        byte   has_props_list
        [if has_props_list]
            uint32 prop_list_count
            PropertyList[prop_list_count]
        byte   has_time_props
        [if has_time_props]
            uint32 time_prop_list_count
            TimePropertyList[time_prop_list_count]:
                uint32 items_count
                {int32 id, PropertyList} per item

PropertyList:
    uint32 props_count
    PropertyListItem[props_count]:
        uint32 pairs_count
        {pascal key, pascal value} per pair

Pemakaian:
    from game.vitaboy import Animation
    a = Animation.from_file('a2o-broom-fly-leftside.anim')
    print(a.name, a.duration_ms, len(a.motions))
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from .bcf_reader import BCFReader
from .mesh import Vec3
from .skeleton import Quat


@dataclass
class PropertyListItem:
    key_pairs: List[tuple] = field(default_factory=list)  # [(key, value), ...]


@dataclass
class PropertyList:
    items: List[PropertyListItem] = field(default_factory=list)


@dataclass
class TimePropertyListItem:
    id: int = 0
    properties: PropertyList = field(default_factory=PropertyList)


@dataclass
class TimePropertyList:
    items: List[TimePropertyListItem] = field(default_factory=list)


@dataclass
class AnimationMotion:
    bone_name: str = ''
    frame_count: int = 0
    duration: float = 0.0  # detik (bukan ms — meski FreeSO field-nya bernama "Duration")
    has_translation: bool = False
    has_rotation: bool = False
    first_translation_index: int = 0
    first_rotation_index: int = 0
    properties: List[PropertyList] = field(default_factory=list)
    time_properties: List[TimePropertyList] = field(default_factory=list)


@dataclass
class Animation:
    name: str = ''
    xskill_name: str = ''
    duration: float = 0.0  # detik (bukan ms — meski FreeSO field-nya bernama "Duration")
    distance: float = 0.0
    is_moving: int = 0

    translations: List[Vec3] = field(default_factory=list)
    rotations: List[Quat] = field(default_factory=list)
    motions: List[AnimationMotion] = field(default_factory=list)

    num_frames: int = 0
    fps: int = 0

    # ── PROPERTY LIST HELPER ────────────────────────────────────────────────
    @staticmethod
    def _read_property_list(io: BCFReader, bcf: bool) -> PropertyList:
        props_count = 1 if bcf else io.read_uint32()
        items: List[PropertyListItem] = []
        for _ in range(props_count):
            item = PropertyListItem()
            pairs_count = io.read_uint32()
            for _ in range(pairs_count):
                k = io.read_pascal_string()
                v = io.read_pascal_string()
                item.key_pairs.append((k, v))
            items.append(item)
        return PropertyList(items=items)

    # ── MAIN READ ───────────────────────────────────────────────────────────
    def read(self, io: BCFReader, bcf: bool = False):
        if bcf:
            self.name = io.read_pascal_string()
            self.xskill_name = io.read_pascal_string()
        else:
            _version = io.read_uint32()
            self.name = io.read_long_pascal_string()

        self.duration = io.read_float()
        self.distance = io.read_float()
        self.is_moving = io.read_int32() if bcf else io.read_byte()

        trans_count = io.read_uint32()
        if not bcf:
            self.translations = [
                Vec3(-io.read_float(), io.read_float(), io.read_float())
                for _ in range(trans_count)
            ]

        rot_count = io.read_uint32()
        if not bcf:
            self.rotations = [
                Quat(io.read_float(), -io.read_float(),
                     -io.read_float(), -io.read_float())
                for _ in range(rot_count)
            ]

        motion_count = io.read_uint32()
        self.num_frames = 0
        for _ in range(motion_count):
            m = AnimationMotion()
            if not bcf:
                _unknown = io.read_uint32()
            m.bone_name = io.read_pascal_string()
            m.frame_count = io.read_uint32()
            if m.frame_count > self.num_frames:
                self.num_frames = m.frame_count
            m.duration = io.read_float()
            m.has_translation = (io.read_int32() if bcf else io.read_byte()) == 1
            m.has_rotation = (io.read_int32() if bcf else io.read_byte()) == 1
            m.first_translation_index = io.read_int32()
            m.first_rotation_index = io.read_int32()

            has_props_list = bcf or io.read_byte() == 1
            if has_props_list:
                prop_list_count = io.read_uint32()
                m.properties = [
                    self._read_property_list(io, bcf)
                    for _ in range(prop_list_count)
                ]

            has_time_props = bcf or io.read_byte() == 1
            if has_time_props:
                tpl_count = io.read_uint32()
                tpl_list: List[TimePropertyList] = []
                for _ in range(tpl_count):
                    tpl = TimePropertyList()
                    items_count = io.read_uint32()
                    for _ in range(items_count):
                        item_id = io.read_int32()
                        item_props = self._read_property_list(io, bcf)
                        tpl.items.append(TimePropertyListItem(
                            id=item_id, properties=item_props
                        ))
                    tpl_list.append(tpl)
                m.time_properties = tpl_list

            self.motions.append(m)

        # FPS — duration di TSO original = milidetik, di FreeSO extracted = detik.
        # Heuristik: kalau > 100, asumsi ms; konversi ke detik.
        if self.duration > 100.0:
            self.duration = self.duration / 1000.0
        if self.duration > 0:
            self.fps = round(self.num_frames / self.duration)
        else:
            self.fps = 30

    # ── HELPERS ─────────────────────────────────────────────────────────────
    @classmethod
    def from_file(cls, path: str, bcf: bool = False) -> 'Animation':
        import io as _io
        a = cls()
        with open(path, 'rb') as f:
            data = f.read()
        r = BCFReader(_io.BytesIO(data))
        a.read(r, bcf)
        return a

    def get_bone_pose_at_frame(self, bone_name: str, frame: int) -> tuple:
        """Return (translation, rotation) untuk satu bone di frame tertentu.
        Translation = Vec3 atau None (kalau bone tidak punya translation track).
        Rotation = Quat atau None.
        """
        for m in self.motions:
            if m.bone_name == bone_name:
                t = r = None
                if m.has_translation and m.frame_count > 0:
                    idx = m.first_translation_index + min(frame, m.frame_count - 1)
                    if 0 <= idx < len(self.translations):
                        t = self.translations[idx]
                if m.has_rotation and m.frame_count > 0:
                    idx = m.first_rotation_index + min(frame, m.frame_count - 1)
                    if 0 <= idx < len(self.rotations):
                        r = self.rotations[idx]
                return t, r
        return None, None
