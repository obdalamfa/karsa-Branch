from game.config import *
from game.scenes.scene_base import Scene, _build_indoor_room


def build_smith():
    """
    Bengkel Budi — pandai besi yang keras kepala.
    Ruangan panas, gelap, penuh alat dan logam.
    Perapian di tengah sebagai pusat aktivitas.
    Rak alat di semua sisi. Meja kerja berat.
    """
    objects = [
        # Perapian/tungku utama — jantung bengkel
        (7, 2, FP),
        (8, 2, FP),

        # Meja kerja berat (tempa logam)
        (5, 3, TB), (6, 3, TB), (7, 3, TB), (8, 3, TB),

        # Rak alat di dinding kiri
        (1, 1, SH), (1, 2, SH), (1, 3, SH),
        (2, 1, SH),

        # Rak hasil kerja di dinding kanan
        (13, 1, SH), (13, 2, SH), (13, 3, SH),
        (12, 1, SH),

        # Peti logam/material mentah
        (3, 1, CH),
        (11, 1, CH),
        (11, 5, CH),

        # Meja admin kecil di pojok (catatan pesanan)
        (1, 5, TB),
        (1, 6, CHR),
        (2, 5, BS),

        # Cermin kecil (untuk cek hasil kerja)
        (13, 5, MR),

        # Kompor/alat ekstra
        (3, 5, ST),
        (4, 5, CT),
    ]
    return _build_indoor_room('smith', 'Bengkel Budi', objects,
                               ('town', 12, 16), w=15, h=8, theme='smith')
