"""
far3.py — Reader untuk FAR3 archive format (FreeSO / TSO).

Format header (little-endian):
    char[8]  magic = "FAR!byAZ"
    uint32   version = 3
    uint32   manifest_offset
[seek manifest_offset]
    uint32   num_files
    Entry[num_files]:
        uint32  decompressed_size
        uint24  compressed_size  (3 bytes: b0 | b1<<8 | b2<<16, LE)
        byte    data_type
        uint32  data_offset
        byte    is_compressed
        byte    access_number
        uint16  filename_length
        uint32  type_id
        uint32  file_id
        byte[]  filename (ascii, filename_length)

Entry data (if is_compressed == 0x01):
    skip 9 bytes
    uint32   compressed_size
    uint16   compression_id   (0xFB10 = QFS/RefPack)
    if 0xFB10:
        uint24 decompressed_size (BIG-endian: b0<<16 | b1<<8 | b2)
        byte[] compressed_data → QFS_decompress()

Lisensi: port dari FreeSO (GPL v3).
"""
from __future__ import annotations
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union


@dataclass
class Far3Entry:
    decompressed_size: int = 0
    compressed_size: int = 0
    data_type: int = 0
    data_offset: int = 0
    is_compressed: int = 0
    access_number: int = 0
    filename_length: int = 0
    type_id: int = 0
    file_id: int = 0
    filename: str = ''


# ─── QFS / RefPack DECOMPRESSOR ──────────────────────────────────────────────
def qfs_decompress(data: bytes, decompressed_size: int) -> bytes:
    """Decompress RefPack/QFS stream (Maxis proprietary, port dari Decompresser.cs).

    Reference: http://wiki.niotso.org/RefPack
    """
    out = bytearray(decompressed_size)
    dst = 0
    src = 0
    n = len(data)
    while src < n:
        b0 = data[src]; src += 1
        if b0 <= 0x7F:
            # 0x00-0x7F: 2-byte op, copy from history + plain literals
            if src >= n: break
            b1 = data[src]; src += 1
            n_plain = b0 & 0x03
            # plain literals
            out[dst:dst+n_plain] = data[src:src+n_plain]
            dst += n_plain; src += n_plain
            if dst >= decompressed_size: break
            offset = ((b0 & 0x60) << 3) + b1 + 1
            n_copy = ((b0 & 0x1C) >> 2) + 3
            # offset copy from output history (dst - offset)
            s = dst - offset
            for i in range(n_copy):
                out[dst + i] = out[s + i]
            dst += n_copy
            if dst >= decompressed_size: break
        elif b0 <= 0xBF:
            # 0x80-0xBF: 3-byte op
            if src + 1 >= n: break
            b1 = data[src]; src += 1
            b2 = data[src]; src += 1
            n_plain = (b1 >> 6) & 0x03
            out[dst:dst+n_plain] = data[src:src+n_plain]
            dst += n_plain; src += n_plain
            if dst >= decompressed_size: break
            offset = ((b1 & 0x3F) << 8) + b2 + 1
            n_copy = (b0 & 0x3F) + 4
            s = dst - offset
            for i in range(n_copy):
                out[dst + i] = out[s + i]
            dst += n_copy
            if dst >= decompressed_size: break
        elif b0 <= 0xDF:
            # 0xC0-0xDF: 4-byte op
            if src + 2 >= n: break
            n_plain = b0 & 0x03
            b1 = data[src]; src += 1
            b2 = data[src]; src += 1
            b3 = data[src]; src += 1
            out[dst:dst+n_plain] = data[src:src+n_plain]
            dst += n_plain; src += n_plain
            if dst >= decompressed_size: break
            offset = ((b0 & 0x10) << 12) + (b1 << 8) + b2 + 1
            n_copy = ((b0 & 0x0C) << 6) + b3 + 5
            s = dst - offset
            for i in range(n_copy):
                out[dst + i] = out[s + i]
            dst += n_copy
            if dst >= decompressed_size: break
        elif b0 <= 0xFB:
            # 0xE0-0xFB: literal-only run, length = ((b0&0x1F)<<2)+4
            n_plain = ((b0 & 0x1F) << 2) + 4
            out[dst:dst+n_plain] = data[src:src+n_plain]
            dst += n_plain; src += n_plain
            if dst >= decompressed_size: break
        else:
            # 0xFC-0xFF: end marker, 0-3 final literals
            n_plain = b0 & 0x03
            out[dst:dst+n_plain] = data[src:src+n_plain]
            dst += n_plain; src += n_plain
            break
    return bytes(out)


# ─── FAR3 ARCHIVE ────────────────────────────────────────────────────────────
class Far3Archive:
    """Reader untuk satu FAR3 archive (.dat file).

    Usage:
        ar = Far3Archive('skeletons.dat')
        names = ar.list_filenames()
        data = ar.read('adult.skel')   # by filename atau by file_id (int)

    Archive di-lazy-load: header + manifest dibaca saat init, data file di-read
    on-demand.
    """

    HEADER = b'FAR!byAZ'

    def __init__(self, path: Union[str, Path]):
        self.path = Path(path)
        self.entries: List[Far3Entry] = []
        self._by_name: Dict[str, Far3Entry] = {}
        self._by_id: Dict[int, Far3Entry] = {}
        self._read_manifest()

    def _read_manifest(self):
        with open(self.path, 'rb') as f:
            head = f.read(8)
            if head != self.HEADER:
                raise ValueError(f"Bukan FAR3 archive: {self.path} (header={head!r})")
            version = struct.unpack('<I', f.read(4))[0]
            if version != 3:
                raise ValueError(f"FAR3 version {version} tidak didukung (expect 3)")
            manifest_offset = struct.unpack('<I', f.read(4))[0]

            f.seek(manifest_offset)
            num_files = struct.unpack('<I', f.read(4))[0]
            for _ in range(num_files):
                e = Far3Entry()
                e.decompressed_size = struct.unpack('<I', f.read(4))[0]
                b0, b1, b2 = f.read(3)
                e.compressed_size = (b2 << 16) | (b1 << 8) | b0
                e.data_type = f.read(1)[0]
                e.data_offset = struct.unpack('<I', f.read(4))[0]
                e.is_compressed = f.read(1)[0]
                e.access_number = f.read(1)[0]
                e.filename_length = struct.unpack('<H', f.read(2))[0]
                e.type_id = struct.unpack('<I', f.read(4))[0]
                e.file_id = struct.unpack('<I', f.read(4))[0]
                e.filename = f.read(e.filename_length).decode('ascii', errors='replace')
                self.entries.append(e)
                self._by_name.setdefault(e.filename, e)
                self._by_id[e.file_id] = e

    # ─── ACCESS ────────────────────────────────────────────────────────────
    def list_filenames(self) -> List[str]:
        return [e.filename for e in self.entries]

    def has(self, key: Union[str, int]) -> bool:
        return key in self._by_name or key in self._by_id

    def get_entry(self, key: Union[str, int]) -> Optional[Far3Entry]:
        if isinstance(key, int):
            return self._by_id.get(key)
        return self._by_name.get(key)

    def read(self, key: Union[str, int]) -> bytes:
        """Return raw decompressed bytes untuk entry."""
        entry = self.get_entry(key)
        if entry is None:
            raise KeyError(f"Entry tidak ditemukan: {key}")
        return self._read_entry_data(entry)

    def read_all(self) -> Dict[str, bytes]:
        return {e.filename: self._read_entry_data(e) for e in self.entries}

    def _read_entry_data(self, entry: Far3Entry) -> bytes:
        with open(self.path, 'rb') as f:
            f.seek(entry.data_offset)
            if entry.is_compressed == 0x01:
                # Header 9 bytes (skipped) + uint32 filesize + uint16 compression_id
                f.seek(9, 1)
                filesize = struct.unpack('<I', f.read(4))[0]
                comp_id = struct.unpack('<H', f.read(2))[0]
                if comp_id == 0xFB10:
                    # 3-byte BIG-endian decompressed size
                    b0, b1, b2 = f.read(3)
                    decompressed_size = (b0 << 16) | (b1 << 8) | b2
                    raw = f.read(filesize)
                    return qfs_decompress(raw, decompressed_size)
                else:
                    # Rewind, treat as raw (uncommon)
                    f.seek(-15, 1)
                    return f.read(entry.decompressed_size)
            else:
                return f.read(entry.decompressed_size)

    def __len__(self) -> int:
        return len(self.entries)

    def __contains__(self, key) -> bool:
        return self.has(key)

    def __repr__(self) -> str:
        return f"<Far3Archive '{self.path.name}' files={len(self.entries)}>"


# ─── CONVENIENCE: BROWSE TSO ARCHIVES ────────────────────────────────────────
def list_tso_archives() -> List[Path]:
    """Return semua .dat archives di TSO install."""
    from .tso_paths import tso_root
    root = tso_root()
    if root is None:
        return []
    return sorted(root.glob('**/*.dat'))
