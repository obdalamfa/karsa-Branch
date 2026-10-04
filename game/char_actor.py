"""Karakter manusia ter-rig (assets/models/actors/<nama>.glb) dengan animasi tulang.

Mengganti mesh-swap 5 pose: animasi diputar Panda3D dengan interpolasi, dan
peralihan diam<->jalan dibaurkan bobotnya supaya tidak ada pose yang meloncat.
.glb dibuat oleh tools/blender_export_actor_glb.py dari characters_vitaboy.blend.
"""
import logging
from pathlib import Path

_ACTOR_DIR = Path(__file__).resolve().parent.parent / 'assets' / 'models' / 'actors'

# Model 1,75 m; dunia game diskalakan untuk tokoh setinggi ~2,3 unit.
SKALA = 1.3
# Kecepatan dunia (unit/detik) yang cocok dengan langkah animasi walk pada laju 1,0.
_LAJU_ACUAN = 3.0
# Detik yang dibutuhkan baur bobot untuk berpindah penuh antar animasi.
_BAUR = 0.18


def actor_path(name):
    p = _ACTOR_DIR / f'{name}.glb'
    return p if p.exists() else None


def _linear_ke_srgb(c):
    return c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def _warnai_material_polos(np):
    # Mesh tanpa tekstur (tangan) hanya membawa warna di Material glTF, yang
    # tidak dibaca shader Ursina -- tanpa ini tangan tampil putih polos.
    from panda3d.core import MaterialAttrib, TextureAttrib, ColorAttrib
    for gnp in np.findAllMatches('**/+GeomNode'):
        gn = gnp.node()
        for i in range(gn.getNumGeoms()):
            st = gn.getGeomState(i)
            if st.hasAttrib(TextureAttrib) and st.getAttrib(TextureAttrib).getNumOnStages():
                continue
            if not st.hasAttrib(MaterialAttrib):
                continue
            m = st.getAttrib(MaterialAttrib).getMaterial()
            c = m.getBaseColor() if m.hasBaseColor() else m.getDiffuse()
            warna = (_linear_ke_srgb(c[0]), _linear_ke_srgb(c[1]), _linear_ke_srgb(c[2]), 1.0)
            gn.setGeomState(i, st.setAttrib(ColorAttrib.makeFlat(warna)))


class CharActor:
    """Satu Actor Panda3D di bawah entity Ursina, dengan baur idle/walk."""

    def __init__(self, parent, name):
        from direct.actor.Actor import Actor
        from panda3d.core import Filename
        self.actor = Actor(Filename.fromOsSpecific(str(actor_path(name))).getFullpath())
        self.actor.reparentTo(parent)
        # Model menghadap -Z; entity game menganggap rotation_y 0 = menghadap +Z.
        self.actor.setH(180)
        self.actor.setScale(SKALA)
        _warnai_material_polos(self.actor)
        self.anims = set(self.actor.getAnimNames())
        self.actor.enableBlend()
        self._bobot = {'idle': 1.0, 'walk': 0.0}
        for a in self._bobot:
            if a in self.anims:
                self.actor.loop(a)
                self.actor.setControlEffect(a, self._bobot[a])
        self._sekali = None

    def update(self, dt, laju):
        """laju: kecepatan dunia sekarang (0 = diam)."""
        if self._sekali is not None:
            ctrl = self.actor.getAnimControl(self._sekali)
            if ctrl is not None and ctrl.isPlaying():
                return
            self.actor.setControlEffect(self._sekali, 0.0)
            self._sekali = None
        jalan = 1.0 if laju > 0.05 else 0.0
        langkah = min(1.0, dt / _BAUR)
        w = self._bobot['walk'] + (jalan - self._bobot['walk']) * langkah
        self._bobot['walk'], self._bobot['idle'] = w, 1.0 - w
        for a, b in self._bobot.items():
            if a in self.anims:
                self.actor.setControlEffect(a, b)
        if 'walk' in self.anims and laju > 0.05:
            self.actor.setPlayRate(max(0.6, min(2.8, laju / _LAJU_ACUAN)), 'walk')

    def mainkan_sekali(self, nama):
        """Animasi kerja (hoe/swing/water) diputar penuh sekali di atas baur jalan."""
        if nama not in self.anims:
            return False
        for a in self._bobot:
            if a in self.anims:
                self.actor.setControlEffect(a, 0.0)
        self.actor.setControlEffect(nama, 1.0)
        self.actor.play(nama)
        self._sekali = nama
        return True

    def pegangan(self):
        """Entity Ursina yang mengikuti tulang tangan kanan (untuk alat)."""
        if getattr(self, '_pegangan', None) is None:
            from ursina import Entity
            # Transformasi sendi relatif ke node Character, bukan akar Actor:
            # node rig glTF di antaranya membawa transformasinya sendiri.
            karakter = self.actor.find('**/+Character')
            sendi = self.actor.exposeJoint(karakter.attachNewNode('R_HAND_kait'),
                                           'modelRoot', 'R_HAND')
            self._pegangan = Entity()
            self._pegangan.reparentTo(sendi)
        return self._pegangan

    def hapus(self):
        try:
            self.actor.cleanup()
            self.actor.removeNode()
        except Exception:
            pass


def build_char_actor(parent, name):
    if actor_path(name) is None:
        return None
    try:
        return CharActor(parent, name)
    except Exception:
        logging.warning('Actor %r gagal dimuat', name, exc_info=True)
        return None
