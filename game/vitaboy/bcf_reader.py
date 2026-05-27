"""
bcf_reader.py — Port `tso.files/Utils/IoBuffer.cs` (FreeSO) ke Python.

Pembaca binary big-endian untuk file Vitaboy (.mesh / .skel / .anim).
FreeSO menyimpan data dalam BIG_ENDIAN — Python default little-endian, jadi
semua read pakai struct '>' prefix.

Lisensi: porting kode dari FreeSO (GPL v3). Kode Python ini juga GPL v3.
"""
from __future__ import annotations
import struct
from typing import BinaryIO


class BCFReader:
    """Pembaca byte-level binary big-endian, drop-in untuk Mesh/Skeleton/Anim.

    Mengikuti API IoBuffer.cs:
      read_int32, read_uint32, read_int16, read_uint16, read_int64,
      read_float, read_byte, read_pascal_string, read_long_pascal_string, read_bytes.
    """

    def __init__(self, stream: BinaryIO):
        self.stream = stream

    # ── primitives ────────────────────────────────────────────────────────
    def read_byte(self) -> int:
        b = self.stream.read(1)
        if not b:
            raise EOFError("BCFReader: unexpected EOF on read_byte")
        return b[0]

    def read_bytes(self, n: int) -> bytes:
        return self.stream.read(n)

    def read_int32(self) -> int:
        return struct.unpack('>i', self.stream.read(4))[0]

    def read_uint32(self) -> int:
        return struct.unpack('>I', self.stream.read(4))[0]

    def read_int16(self) -> int:
        return struct.unpack('>h', self.stream.read(2))[0]

    def read_uint16(self) -> int:
        return struct.unpack('>H', self.stream.read(2))[0]

    def read_int64(self) -> int:
        return struct.unpack('>q', self.stream.read(8))[0]

    def read_float(self) -> float:
        # FreeSO quirk: IoBuffer.ReadFloat() pakai BinaryReader.ReadSingle()
        # yang SELALU little-endian, walaupun Order=BIG_ENDIAN.
        # Hanya integer yang di-byte-swap.
        return struct.unpack('<f', self.stream.read(4))[0]

    def read_pascal_string(self) -> str:
        """1-byte length-prefixed ASCII string."""
        n = self.read_byte()
        return self.stream.read(n).decode('ascii', errors='replace')

    def read_long_pascal_string(self) -> str:
        """int16-length-prefixed ASCII string."""
        n = self.read_int16()
        return self.stream.read(n).decode('ascii', errors='replace')

    # ── stream control ────────────────────────────────────────────────────
    def position(self) -> int:
        return self.stream.tell()

    def seek(self, pos: int):
        self.stream.seek(pos)

    @classmethod
    def from_file(cls, path: str) -> 'BCFReader':
        return cls(open(path, 'rb'))

    @classmethod
    def from_bytes(cls, data: bytes) -> 'BCFReader':
        import io
        return cls(io.BytesIO(data))
