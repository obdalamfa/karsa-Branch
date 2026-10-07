from game.scenes.scene_base import ruang_denah

# Bengkel Budi. Tungku tempa di utara dengan landasan (ubin meja) dua ubin di
# depannya -- Budi menempa di antara keduanya, di luar jalur pintu. Meja kerja
# di timur, tong di dinding barat, rak senjata, dipan di pojok.
DENAH = """
#########
#R.F..RB#
#.......#
#C.T..NN#
#C......#
#.......#
#J....LP#
####D####
"""


def build_smith():
    return ruang_denah('smith', 'Bengkel Budi', DENAH, ('town', 12, 16))
