from game.config import *
from game.scenes.scene_base import Scene, _build_indoor_room


def build_house():
    """
    Kamar sewaan pemain — sempit, berantakan, bernuansa Disco Elysium.
    Kasur kotor di pojok, meja robet dengan botol kosong, lemari penuh
    barang tak berguna, kompor seadanya, TV kecil yang hampir mati.
    """
    objects = [
        # Sudut tidur (kiri atas) — kasur tunggal + koper/peti
        (1, 1, BD), (2, 1, BD),
        (1, 2, CH),          # peti di samping kasur (barang bawaan)

        # Rak buku/dokumen (kanan atas) — penuh berkas
        (12, 1, BS), (13, 1, BS),
        (11, 1, PP),         # tanaman pot setengah layu

        # Cermin retak di dinding
        (1, 3, MR),

        # Area makan/kerja (tengah) — meja + dua kursi
        (6, 3, TB), (7, 3, TB),
        (6, 2, CHR), (8, 3, CHR),

        # TV tua di sudut kanan
        (13, 3, TV),
        (13, 4, CHR),

        # Dapur (kanan bawah) — kompor + counter
        (11, 5, ST), (12, 5, ST),
        (11, 6, CT), (12, 6, CT),
        (13, 5, SH),

        # Jam dinding usang
        (7, 1, CL),

        # Kalender sobek
        (9, 1, CAL),

        # Perapian kecil di sisi kiri (suasana)
        (1, 5, FP),
    ]
    return _build_indoor_room('house', 'Kamar Pemain', objects,
                               ('farm', 3, 5), w=15, h=8)
