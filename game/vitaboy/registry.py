"""
registry.py — Registry asset Vitaboy: ambil mesh/anim/skel by name dari TSO/FreeSO.

Search priority:
  1. FAR3 archive yang terdaftar (TSO .dat — ribuan asset)
  2. Folder standalone (FreeSO extracted)

Pemakaian:
    from game.vitaboy import asset_registry
    data = asset_registry.read_anim('a2a-greet')   # auto-search
    anim = asset_registry.load_anim('a2a-greet')   # langsung jadi Animation
"""
from __future__ import annotations
import io as _io
from pathlib import Path
from typing import Dict, List, Optional, Union

from .far3 import Far3Archive, list_tso_archives
from .tso_paths import find_meshes, find_animations, skeleton_path
from .bcf_reader import BCFReader
from .mesh import VitaboyMesh
from .skeleton import Skeleton
from .animation import Animation


class AssetRegistry:
    """Cache + lookup index untuk semua aset Vitaboy.

    Pertama kali dibuat: scan archives + folder, index by filename.
    Lazy-load file body (di-cache setelah pertama read).
    """

    # Versi cache — bump kalau format _index berubah supaya cache lama dibuang
    CACHE_VERSION = 2

    def __init__(self, autoload: bool = True):
        # Map: filename → (source_type, source_ref, entry_or_path)
        # source_type: 'far3' | 'file'
        # source_ref: Path ke archive (atau None untuk file)
        self._index: Dict[str, tuple] = {}
        # Map: (type_id, file_id) → (archive_path, entry_filename)
        # Untuk resolve binding/appearance refs (FAR3 file_id is unique per type_id)
        self._id_index: Dict[tuple, tuple] = {}
        # Cache decoded asset (Animation/Skeleton/VitaboyMesh)
        self._anim_cache: Dict[str, Animation] = {}
        self._mesh_cache: Dict[str, VitaboyMesh] = {}
        self._skel_cache: Dict[str, Skeleton] = {}
        # Cache Far3Archive yang sudah dibuka — supaya tidak open ulang per read
        self._archive_cache: Dict[str, Far3Archive] = {}
        if autoload:
            self.load_or_scan()

    # ─── CACHE FILE ────────────────────────────────────────────────────────
    @staticmethod
    def _cache_path() -> Path:
        # Lokasi: 3d/.vitaboy_index.pkl (di-gitignore tidak masalah, generated)
        from .tso_paths import tso_root
        root = tso_root()
        if root is None:
            return Path(__file__).parent / '.vitaboy_index.pkl'
        # Cache key di-anchor ke TSO root path
        return Path(__file__).parent / '.vitaboy_index.pkl'

    def load_or_scan(self):
        """Load index dari cache disk kalau ada + valid; else scan ulang."""
        cache_file = self._cache_path()
        if cache_file.exists():
            try:
                import pickle
                with open(cache_file, 'rb') as f:
                    cached = pickle.load(f)
                if cached.get('version') == self.CACHE_VERSION:
                    # Validate: cek kalau archives tracked masih ada dengan size sama
                    arch_meta = cached.get('archives', {})
                    valid = all(Path(p).exists() and Path(p).stat().st_size == sz
                                for p, sz in arch_meta.items())
                    if valid:
                        self._index = cached['index']
                        self._id_index = cached.get('id_index', {})
                        return
            except Exception:
                pass
        # Cache miss → full scan + save
        self.scan()
        try:
            self._save_cache()
        except Exception:
            pass

    def _save_cache(self):
        import pickle
        ser_index = {}
        arch_paths = {}
        for k, (src_type, src_ref, ref) in self._index.items():
            if src_type == 'far3':
                arch_paths[str(src_ref)] = Path(src_ref).stat().st_size
                ser_index[k] = ('far3', str(src_ref), ref)
            else:
                ser_index[k] = ('file', None, str(ref))
        data = {
            'version': self.CACHE_VERSION,
            'archives': arch_paths,
            'index': ser_index,
            'id_index': self._id_index,
        }
        with open(self._cache_path(), 'wb') as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

    # ─── BUILD INDEX ──────────────────────────────────────────────────────
    def scan(self):
        """Index ulang semua archive + folder. Simpan path archive (string),
        bukan objek Far3Archive (lazy-open saat read)."""
        self._index.clear()
        self._id_index.clear()
        self._archive_cache.clear()
        # 1. TSO archives
        for dat_path in list_tso_archives():
            try:
                ar = Far3Archive(dat_path)
                self._archive_cache[str(dat_path)] = ar
                for entry in ar.entries:
                    key = entry.filename.lower()
                    if key not in self._index:
                        self._index[key] = ('far3', str(dat_path), entry)
                    # Index by (type_id, file_id) for ContentID resolution
                    id_key = (entry.type_id, entry.file_id)
                    if id_key not in self._id_index:
                        self._id_index[id_key] = (str(dat_path), entry.filename)
            except Exception:
                pass

        # 2. Standalone file dataset (FreeSO extracted) — pakai sebagai backup
        for path in find_meshes('bodies') + find_meshes('heads') + find_meshes('accessories'):
            key = path.name.lower()
            self._index.setdefault(key, ('file', None, path))
        for path in find_animations():
            self._index.setdefault(path.name.lower(), ('file', None, path))

    def _get_archive(self, path: str) -> Far3Archive:
        """Lazy open archive (cache after first use)."""
        if path not in self._archive_cache:
            self._archive_cache[path] = Far3Archive(path)
        return self._archive_cache[path]

    # ─── LOOKUP & READ ────────────────────────────────────────────────────
    def list_keys(self, suffix: str = '') -> List[str]:
        """List nama file di index. `suffix` filter: '.anim', '.mesh', '.skel'."""
        keys = list(self._index.keys())
        if suffix:
            keys = [k for k in keys if k.endswith(suffix.lower())]
        return sorted(keys)

    def find(self, name: str, suffix: str = '.anim') -> Optional[str]:
        """Cari entry by substring (case-insensitive). Return exact key kalau ada.

        Contoh: find('a2a-greet') → 'a2a-greet-target.anim'
        """
        nl = name.lower()
        # Exact match dulu
        if nl in self._index:
            return nl
        if (nl + suffix) in self._index:
            return nl + suffix
        # Substring match
        for k in self._index:
            if k.endswith(suffix.lower()) and nl in k:
                return k
        return None

    def read_bytes(self, name: str, suffix: str = '') -> Optional[bytes]:
        """Return raw bytes dari archive atau file."""
        if not name:
            return None
        key = self.find(name, suffix) if suffix else (name.lower() if name.lower() in self._index else None)
        if key is None:
            # Coba sebagai langsung
            if name.lower() in self._index:
                key = name.lower()
            else:
                return None
        src_type, src_ref, ref = self._index[key]
        if src_type == 'far3':
            ar = self._get_archive(src_ref)
            return ar.read(ref.filename)
        else:
            ref_path = Path(ref) if isinstance(ref, str) else ref
            with open(ref_path, 'rb') as f:
                return f.read()

    # ─── TYPED LOADERS ────────────────────────────────────────────────────
    def load_anim(self, name: str) -> Optional[Animation]:
        key = self.find(name, '.anim')
        if key is None:
            return None
        if key in self._anim_cache:
            return self._anim_cache[key]
        data = self.read_bytes(key)
        if not data:
            return None
        a = Animation()
        a.read(BCFReader(_io.BytesIO(data)))
        self._anim_cache[key] = a
        return a

    def load_mesh(self, name: str) -> Optional[VitaboyMesh]:
        key = self.find(name, '.mesh')
        if key is None:
            return None
        if key in self._mesh_cache:
            return self._mesh_cache[key]
        data = self.read_bytes(key)
        if not data:
            return None
        m = VitaboyMesh()
        m.read(BCFReader(_io.BytesIO(data)), bmf=False)
        self._mesh_cache[key] = m
        return m

    # ─── CONTENT ID RESOLVER (untuk .apr / .bnd refs) ────────────────────
    def read_by_id(self, type_id: int, file_id: int) -> Optional[bytes]:
        """Resolve (type_id, file_id) → bytes via FAR3 archives.
        Dipakai untuk follow refs di Appearance.bindings dan Binding mesh/texture."""
        ref = self._id_index.get((type_id, file_id))
        if ref is None:
            return None
        archive_path, entry_name = ref
        ar = self._get_archive(archive_path)
        return ar.read(entry_name)

    def has_id(self, type_id: int, file_id: int) -> bool:
        return (type_id, file_id) in self._id_index

    def filename_for_id(self, type_id: int, file_id: int) -> Optional[str]:
        ref = self._id_index.get((type_id, file_id))
        return ref[1] if ref else None

    def load_skel(self, name: str = 'adult') -> Optional[Skeleton]:
        # adult.skel khusus: di TSO ada standalone file di avatardata/skeletons/
        key = self.find(name, '.skel')
        if key is None:
            sp = skeleton_path(name)
            if sp:
                return Skeleton.from_file(str(sp))
            return None
        if key in self._skel_cache:
            return self._skel_cache[key]
        data = self.read_bytes(key)
        if not data:
            return None
        s = Skeleton()
        s.read(BCFReader(_io.BytesIO(data)), bcf=False)
        self._skel_cache[key] = s
        return s

    # ─── STATS ────────────────────────────────────────────────────────────
    def stats(self) -> dict:
        anims  = sum(1 for k in self._index if k.endswith('.anim'))
        meshes = sum(1 for k in self._index if k.endswith('.mesh'))
        skels  = sum(1 for k in self._index if k.endswith('.skel'))
        outs   = sum(1 for k in self._index if k.endswith('.oft'))
        apps   = sum(1 for k in self._index if k.endswith('.apr'))
        # Count unique archive paths
        archives = set()
        for _k, (st, sr, _e) in self._index.items():
            if st == 'far3':
                archives.add(sr)
        return {
            'archives': len(archives),
            'total_entries': len(self._index),
            'anims': anims, 'meshes': meshes, 'skels': skels,
            'outfits': outs, 'appearances': apps,
        }


# Singleton — lazy-init agar tidak scan saat import module
_registry: Optional[AssetRegistry] = None


def asset_registry() -> AssetRegistry:
    """Lazy singleton."""
    global _registry
    if _registry is None:
        _registry = AssetRegistry(autoload=True)
    return _registry
