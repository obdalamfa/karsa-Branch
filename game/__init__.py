# Model OBJ dimuat lewat Assimp, bukan loader OBJ bawaan Panda. Loader bawaan
# MENGABAIKAN .mtl: seluruh model jadi satu geom berwarna abu default, jadi
# monster gua dan makhluk halus yang warnanya hanya ada di material (sayap,
# mata, cakar) tampil sebagai siluet putih. Harus diset sebelum OBJ pertama
# dimuat, dan paket ini diimpor lebih dulu daripada apa pun di game/.
from panda3d.core import loadPrcFileData as _prc
_prc('', 'load-file-type p3assimp')
