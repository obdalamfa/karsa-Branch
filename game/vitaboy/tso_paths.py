"""
tso_paths.py — Auto-discover lokasi install The Sims Online.

User punya TSO di E:/Download/The Sims Online — kita resolve path standar
(skeleton, animations, body meshes) supaya kode lain tinggal panggil
`tso_path('skeletons/adult.skel')` tanpa hardcode path absolute.

Fallback: kalau TSO tidak ada, return None — caller harus handle (mis. pakai
default_adult_skeleton procedural).
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional


# ─── KANDIDAT LOKASI INSTALL ─────────────────────────────────────────────────
# Urutan: lokasi user → lokasi umum lain
_CANDIDATES = [
    Path('E:/Documents/Panda demo/panda_atb_demo/FreeSO/TSOClient/FSO.Windows/bin/The Sims Online/TSOClient'),
    Path('E:/Download/The Sims Online/TSOClient'),
    Path('C:/Program Files (x86)/Maxis/The Sims Online/TSOClient'),
    Path('C:/Program Files/Maxis/The Sims Online/TSOClient'),
]

# Lokasi backup untuk mesh/anim mentah (sudah di-extract dari .dat oleh FreeSO)
_FSO_EXTRACTED = Path(
    'E:/Documents/Panda demo/panda_atb_demo/FreeSO/TSOClient/FSO.Content.TSO/Content/Avatar'
)

_tso_root: Optional[Path] = None
_searched = False


def _discover() -> Optional[Path]:
    """Cari TSOClient/ directory pertama yang ada."""
    global _tso_root, _searched
    if _searched:
        return _tso_root
    _searched = True
    for cand in _CANDIDATES:
        if cand.exists() and (cand / 'avatardata' / 'skeletons').exists():
            _tso_root = cand
            return cand
        # Coba dengan struktur FreeSO Content/Avatar (bukan avatardata/)
        if cand.exists() and (cand / 'Avatar' / 'Meshes').exists():
            _tso_root = cand
            return cand
    return None


def tso_root() -> Optional[Path]:
    """Return root path TSOClient kalau ditemukan."""
    return _discover()


def tso_path(*parts: str) -> Optional[Path]:
    """Build path relative ke TSO root. Return None kalau TSO tidak ada
    atau file tidak ditemukan.

    Contoh:
        tso_path('avatardata', 'skeletons', 'adult.skel')
        → Path('E:/Download/.../TSOClient/avatardata/skeletons/adult.skel')
    """
    root = _discover()
    if root is None:
        return None
    p = root.joinpath(*parts)
    return p if p.exists() else None


def skeleton_path(name: str = 'adult') -> Optional[Path]:
    """Cari skeleton TSO. Default 'adult'.

    Cek lokasi standar TSO: avatardata/skeletons/<name>.skel
    Fallback: FreeSO Content/Avatar/Skeletons/...
    """
    p = tso_path('avatardata', 'skeletons', f'{name}.skel')
    if p:
        return p
    # FreeSO-style
    root = _discover()
    if root:
        skl_dir = root / 'Avatar' / 'Skeletons'
        if skl_dir.exists():
            for f in skl_dir.glob(f'{name}*.skel'):
                return f
    return None


def find_meshes(folder: str = 'bodies', pattern: str = '*.mesh') -> list[Path]:
    """List semua mesh standalone .mesh files.

    folder: hint kategori ('bodies' | 'heads' | 'hands' | 'accessories').
            Untuk TSO asli mesh ada di .dat archives — return [] sampai
            kita punya FAR3 parser. Untuk FreeSO extracted dataset semua
            mesh ada di satu folder Meshes/, di-prefix dengan kategori.
    """
    out: list[Path] = []
    root = _discover()
    if root:
        # Try avatardata/{folder}/meshes (.dat archive — skip untuk sekarang)
        # Try Content/Avatar/Meshes
        fso_dir = root / 'Avatar' / 'Meshes'
        if fso_dir.exists():
            out.extend(fso_dir.glob(pattern))
    # Fallback: FreeSO extracted dataset
    if _FSO_EXTRACTED.exists():
        meshes_dir = _FSO_EXTRACTED / 'Meshes'
        if meshes_dir.exists():
            files = sorted(meshes_dir.glob(pattern))
            # Filter by category prefix (best-effort)
            prefix_map = {
                'bodies': ('au-', 'b00', 'b01', 'fa-', 'ma-'),
                'heads':  ('h00', 'fa-', 'ma-'),
                'hands':  ('hag', 'r-', 'l-'),
                'accessories': ('fso-accessory', 'fso-', 'hat'),
            }
            prefixes = prefix_map.get(folder.lower())
            if prefixes:
                files = [f for f in files if f.name.lower().startswith(prefixes)]
            out.extend(files)
    return sorted(set(out))


def find_animations(pattern: str = '*.anim') -> list[Path]:
    """List semua animation files Vitaboy."""
    out: list[Path] = []
    root = _discover()
    if root:
        anim_dir = root / 'Avatar' / 'Animations'
        if anim_dir.exists():
            out.extend(anim_dir.glob(pattern))
    if _FSO_EXTRACTED.exists():
        anim_dir = _FSO_EXTRACTED / 'Animations'
        if anim_dir.exists():
            out.extend(anim_dir.glob(pattern))
    return sorted(set(out))
