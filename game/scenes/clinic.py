from game.config import *
from game.scenes.scene_base import Scene, _build_indoor_room


def build_clinic():
    """
    Klinik Pak Raka — bangunan kesehatan tahun 50an yang sudah reot.
    Ranjang pasien berjejer, meja pemeriksaan, rak obat setengah kosong.
    Nuansa rumah sakit abandonded Disco Elysium — dingin, sunyi, sedikit menakutkan.
    """
    objects = [
        # Ranjang pasien (kiri) — dua ranjang berjejer
        (1, 1, BD), (1, 2, BD),
        (3, 1, BD), (3, 2, BD),

        # Ranjang pasien (kanan) — dua lagi
        (11, 1, BD), (11, 2, BD),
        (13, 1, BD), (13, 2, BD),

        # Meja pemeriksaan tengah
        (6, 3, TB), (7, 3, TB), (8, 3, TB),
        (7, 4, CHR),             # kursi dokter

        # Rak obat (dinding belakang)
        (1, 5, SH), (2, 5, SH), (3, 5, SH),
        (11, 5, SH), (12, 5, SH), (13, 5, SH),

        # Lemari berkas/buku di pojok
        (13, 6, BS), (13, 5, BS),

        # Tanaman pot (sudah layu)
        (1, 6, PP),

        # Lampu baca/meja kecil
        (5, 1, TB),
        (5, 2, CHR),

        # Kalender jadwal pasien di dinding
        (7, 1, CAL),
    ]
    return _build_indoor_room('clinic', 'Klinik Pak Raka', objects,
                               ('town', 11, 9), w=15, h=8, theme='clinic')
