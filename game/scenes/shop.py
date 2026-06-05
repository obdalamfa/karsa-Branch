from game.config import *
from game.scenes.scene_base import Scene, _build_indoor_room


def build_shop():
    """
    Warung Bu Sari — toko kelontong yang sepi, rak setengah kosong.
    Counter panjang memisahkan penjual dari pembeli.
    Suasana: toko yang masih buka tapi tidak yakin sampai kapan.
    """
    # Counter memanjang dari kiri ke kanan (pembatas pelanggan/penjual)
    counter_row = [(x, 5, CT) for x in range(1, 14)]

    # Rak barang di dinding belakang (sisi penjual)
    shelf_back = [(x, 1, SH) for x in range(1, 14)]
    shelf_mid  = [(x, 2, SH) for x in range(1, 7)]   # hanya setengah terisi

    objects = (
        counter_row +
        shelf_back +
        shelf_mid +
        [
            # Meja kasir + kursi Bu Sari
            (7, 4, TB),
            (7, 3, CHR),

            # Lemari penyimpanan di pojok
            (13, 3, BS),
            (13, 4, BS),

            # Pot tanaman di dekat pintu (layu)
            (1, 6, PP),

            # Kompor kecil (Bu Sari masak di dalam)
            (1, 3, ST),
            (2, 3, CT),

            # Kalender di dinding belakang
            (4, 1, CAL),
        ]
    )
    return _build_indoor_room('shop', 'Warung Bu Sari', objects,
                               ('town', 4, 9), w=15, h=8)
