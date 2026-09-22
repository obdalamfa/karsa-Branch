"""bayangan.py — Menempelkan bayangan kontak ke PERMUKAAN TANAH.

Kenapa ini butuh modul sendiri, padahal isinya satu fungsi: menaruh quad
bayangan pada ketinggian yang benar ternyata tidak bisa dilakukan dengan
menulis angka di konstruktor, dan dua cara yang tampak benar keduanya salah.

Terukur, permukaan rumput ada di `GROUND_H + 0,04 = 0,24`:

  * Bayangan warga dipasang di y LOKAL 0,02 mendarat di y dunia 0,0137 —
    terkubur 23 cm di bawah tanah. Yang terlihat cuma serpihan di tempat
    tanahnya kebetulan cekung: 149 piksel dari frame 900x900.
  * Bayangan pemain dipasang dengan angka yang sama mendarat di y dunia
    0,92 — MELAYANG 68 cm di atas rumput, cakram gelap setinggi lutut. Ia
    sudah begitu sejak lama.

Dua sebabnya berbeda dan keduanya tidak terlihat dari kode di tempatnya:
node actor warga BERSKALA (manekin dikecilkan 2,35/3,42 = 0,687), jadi
0,245 lokal jadi 0,168 dunia; sedangkan pemain punya titik asal di y 0,90.

Dan `Entity.world_y = ...` milik Ursina tidak menolong — ia menulis ke y
LOKAL, jadi bayangan pemain justru naik ke 1,145. Yang dipakai di sini
transform Panda3D langsung (`set_pos(render, ...)`), yang memang menghitung
skala dan induk.
"""
from ursina import Vec3

from .config import GROUND_H

# Sedikit di atas tutup rumput (GROUND_H + 0,04) supaya tidak berkedip
# melawannya (z-fighting).
TINGGI_TANAH = GROUND_H + 0.045


def pin_ke_tanah(bayangan) -> None:
    """Kunci ketinggian `bayangan` ke permukaan tanah, x dan z tidak diubah."""
    if bayangan is None:
        return
    try:
        from direct.showbase.ShowBaseGlobal import base
        # setPos/getPos NodePath MENTAH, bukan set_position/get_position milik
        # Ursina: yang terakhir punya tanda tangan sendiri dan tidak menerima
        # node acuan, jadi memanggilnya dengan (render, Vec3) diam-diam
        # mendaratkan bayangan di tempat lain — terukur 0,0407 dan bukan 0,245.
        w = bayangan.getPos(base.render)
        bayangan.setPos(base.render, w[0], TINGGI_TANAH, w[2])
    except Exception:
        pass
