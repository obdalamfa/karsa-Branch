from game.scenes.scene_base import ruang_denah

# Studio Maya. Pojok tidur di barat laut, rak buku & rak cat di utara, dua
# kuda-kuda lukis (ubin meja) di timur, meja cuci kuas di dinding barat.
# Tengah sengaja lapang: ruang kerja pelukis.
DENAH = """
#########
#BP.KKR.#
#.......#
#M....T.#
#N......#
#N....TC#
#J.L...P#
####D####
"""


def build_studio():
    return ruang_denah('studio', 'Studio Maya', DENAH, ('town', 22, 9))
