"""
default_skeleton.py — Skeleton T-pose adult synthetic.

Original "adult.skel" tersimpan di TSO .dat archive yang tidak ada di install
FreeSO ini. Sebagai pengganti, kita konstruksi skeleton manual dengan hierarchy
dan translation bone standar TSO/Vitaboy (T-pose), supaya .mesh files bisa
di-bake ke world space dan dirender.

Bone tree (sesuai nama yang muncul di au-blue.mesh dan lainnya):
  ROOT
  └── PELVIS
      ├── SPINE → SPINE1
      │            ├── NECK → HEAD
      │            ├── R_ARM → R_FOREARM → R_HAND
      │            └── L_ARM → L_FOREARM → L_HAND
      ├── R_LEG → R_CALF → R_FOOT
      └── L_LEG → L_CALF → L_FOOT
"""
from __future__ import annotations
from typing import List
from .skeleton import Skeleton, Bone, Quat, Mat4
from .mesh import Vec3


# Bind translation (local relative to parent). X negated agar konsisten dengan
# mesh.read() yang juga negate X (FreeSO convention).
_BIND_POSE_T_ADULT = [
    # (name, parent, translation x, y, z)
    ("ROOT",      "NULL",    0.00, 0.00, 0.00),
    ("PELVIS",    "ROOT",    0.00, 0.85, 0.00),
    ("SPINE",     "PELVIS",  0.00, 0.10, 0.00),
    ("SPINE1",    "SPINE",   0.00, 0.18, 0.00),
    ("NECK",      "SPINE1",  0.00, 0.20, 0.00),
    ("HEAD",      "NECK",    0.00, 0.18, 0.00),
    ("R_ARM",     "SPINE1",  0.18, 0.16, 0.00),
    ("R_FOREARM", "R_ARM",   0.28, 0.00, 0.00),
    ("R_HAND",    "R_FOREARM",0.24, 0.00, 0.00),
    ("L_ARM",     "SPINE1", -0.18, 0.16, 0.00),
    ("L_FOREARM", "L_ARM",  -0.28, 0.00, 0.00),
    ("L_HAND",    "L_FOREARM",-0.24,0.00, 0.00),
    ("R_LEG",     "PELVIS",  0.10, -0.05, 0.00),
    ("R_CALF",    "R_LEG",   0.00, -0.40, 0.00),
    ("R_FOOT",    "R_CALF",  0.00, -0.42, 0.05),
    ("L_LEG",     "PELVIS", -0.10, -0.05, 0.00),
    ("L_CALF",    "L_LEG",   0.00, -0.40, 0.00),
    ("L_FOOT",    "L_CALF",  0.00, -0.42, 0.05),
]


def default_adult_skeleton() -> Skeleton:
    """Bangun Skeleton T-pose adult hardcoded — pengganti adult.skel yang tidak tersedia."""
    skel = Skeleton()
    skel.name = "adult-synthetic"
    bones: List[Bone] = []
    for i, (name, parent, tx, ty, tz) in enumerate(_BIND_POSE_T_ADULT):
        b = Bone()
        b.name = name
        b.parent_name = parent
        b.translation = Vec3(tx, ty, tz)
        b.rotation = Quat(0.0, 0.0, 0.0, 1.0)
        b.index = i
        b.can_translate = 1
        b.can_rotate = 1
        bones.append(b)

    skel.bones = bones
    skel._by_name = {b.name: b for b in bones}
    for b in bones:
        b.children = [c for c in bones if c.parent_name == b.name]
    for b in bones:
        if b.parent_name == "NULL":
            skel.root = b
            break
    if skel.root:
        skel._compute_positions(skel.root, Mat4.identity())
    return skel
