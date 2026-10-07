from game.scenes.scene_base import ruang_denah

# Warung Bu Sari. Belakang: rak dagangan + kompor (warung masak). Konter
# melintang dengan CELAH di ujung timur (x=7) supaya Bu Sari bisa keluar-masuk
# -- konter lama menutup satu baris penuh dan mengurung pemain di depan pintu.
# Depan: dua meja kopi dengan kursi untuk pembeli.
DENAH = """
#########
#RR.S.RR#
#.......#
#NNNNNN.#
#.......#
#cTc.cTc#
#P.....P#
####D####
"""


def build_shop():
    return ruang_denah('shop', 'Warung Bu Sari', DENAH, ('town', 23, 1))
