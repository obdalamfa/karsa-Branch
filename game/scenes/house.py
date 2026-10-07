from game.scenes.scene_base import ruang_denah

# Rumah Kamu. Kiri: kamar (kasur, lemari, peti, jam). Tengah: ruang duduk
# menghadap TV, perapian di depan pintu sebagai titik pandang. Kanan atas:
# dapur (kompor, kulkas, konter). Kanan bawah: meja makan, dan pojok mandi
# (kloset + pancuran) untuk motif kandung kemih & kebersihan ala Sims.
# Kolom pintu (x=4) kosong sampai dinding utara -- jalur utama.
DENAH = """
##########
#BPVFK.Sk#
#.......N#
#M.c.c...#
#........#
#C...cTc.#
#J.L...wu#
####D#####
"""


def build_house():
    return ruang_denah('house', 'Rumah Kamu', DENAH, ('farm', 3, 5))
