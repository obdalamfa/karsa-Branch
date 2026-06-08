from game.config import *
from game.scenes.scene_base import Scene, _build_indoor_room


def build_studio():
    """
    Studio Maya — ruangan dokumen, penelitian, dan renungan.
    Ala Disco Elysium: meja penuh berkas, rak buku yang teratur tapi berat,
    satu cermin besar (Maya mengamati dirinya sendiri), tanaman sekarat.
    """
    objects = [
        # Meja penelitian utama (tengah-depan)
        (5, 2, TB), (6, 2, TB), (7, 2, TB), (8, 2, TB), (9, 2, TB),
        (6, 3, CHR), (7, 3, CHR), (8, 3, CHR),

        # Dinding buku (kiri penuh)
        (1, 1, BS), (2, 1, BS), (3, 1, BS), (4, 1, BS),
        (1, 2, BS), (2, 2, BS),
        (1, 3, BS),

        # Dinding buku (kanan)
        (11, 1, BS), (12, 1, BS), (13, 1, BS),
        (13, 2, BS), (13, 3, BS),

        # Meja kecil di pojok kanan (tempat berpikir)
        (12, 5, TB),
        (12, 6, CHR),
        (13, 5, MR),    # cermin besar untuk refleksi

        # Meja di pojok kiri (percobaan/eksperimen)
        (1, 5, TB), (2, 5, TB),
        (1, 6, ST),     # alat lab/kompor kecil
        (2, 6, CT),

        # Jam dinding besar
        (7, 1, CL),

        # Tanaman pot (sudah layu tapi dipertahankan)
        (4, 5, PP),
        (10, 5, PP),

        # Peti arsip
        (5, 5, CH),
        (9, 5, CH),

        # Kalender penelitian
        (10, 1, CAL),
    ]
    return _build_indoor_room('studio', 'Studio Maya', objects,
                               ('town', 22, 9), w=15, h=8, theme='studio')
