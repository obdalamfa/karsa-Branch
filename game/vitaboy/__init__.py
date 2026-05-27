"""
vitaboy/ — Port modular FSO Vitaboy (mesh + skeleton + anim) ke Python.

API utama:
    from game.vitaboy import VitaboyMesh, Skeleton, load_vitaboy_static, vitaboy_stats

Lisensi: kode FreeSO asli (C#) di-port ke Python. Dirilis di bawah GPL v3
sesuai lisensi sumber.
"""
from .bcf_reader import BCFReader
from .mesh import VitaboyMesh, VitaboyVertex, BoneBinding, BlendData, Vec3, Vec2
from .skeleton import Skeleton, Bone, Quat, Mat4
from .loader import load_vitaboy_static, vitaboy_stats
from .default_skeleton import default_adult_skeleton
from .tso_paths import tso_root, tso_path, skeleton_path, find_meshes, find_animations
from .animation import Animation, AnimationMotion, PropertyList, PropertyListItem
from .actor import VitaboyActor
from .far3 import Far3Archive, Far3Entry, qfs_decompress, list_tso_archives
from .registry import AssetRegistry, asset_registry
from .appearance import Appearance, Binding, AppearanceBindingRef
from .avatar import VitaboyAvatar, AvatarPart, DEFAULT_FEMALE_OUTFIT, DEFAULT_MALE_OUTFIT

__all__ = [
    'BCFReader',
    'VitaboyMesh', 'VitaboyVertex', 'BoneBinding', 'BlendData', 'Vec3', 'Vec2',
    'Skeleton', 'Bone', 'Quat', 'Mat4',
    'load_vitaboy_static', 'vitaboy_stats',
    'default_adult_skeleton',
    'tso_root', 'tso_path', 'skeleton_path', 'find_meshes', 'find_animations',
    'Animation', 'AnimationMotion', 'PropertyList', 'PropertyListItem',
    'VitaboyActor',
    'Far3Archive', 'Far3Entry', 'qfs_decompress', 'list_tso_archives',
    'AssetRegistry', 'asset_registry',
]
