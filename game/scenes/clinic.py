from game.scenes.scene_base import ruang_denah

# Klinik Pak Raka. Utara: dua ranjang pasien, jam, lemari obat. Meja
# resepsionis di timur (Pak Raka berjaga di belakangnya), kursi tunggu di
# dinding barat, rak berkas di timur.
DENAH = """
#########
#B.BJRRR#
#.......#
#P...NN.#
#.......#
#c.....K#
#c.L...P#
####D####
"""


def build_clinic():
    return ruang_denah('clinic', 'Klinik Pak Raka', DENAH, ('town', 11, 9))
