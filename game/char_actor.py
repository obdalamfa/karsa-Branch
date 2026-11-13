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
# Tinggi pinggang (unit dunia) untuk poros condong lapisan gerak.
TINGGI_PINGGANG = 1.05


# Gaya per tokoh yang tidak dipanggang ke rig: skala dan tinggi melayang
# (meter di atas tanah). Bidadari peri kecil yang terbang; dewa angin
# mengambang sejengkal. Diayun naik-turun pelan supaya terbaca melayang,
# bukan tersangkut di udara.
_GAYA = {
    'npc_bidadari':   {'skala': 0.6, 'melayang': 0.9},
    'npc_dewa_angin': {'skala': 1.0, 'melayang': 0.25},
}


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
        # Poros: satu simpul di antara entity dan rig, tempat lapisan gerak
        # prosedural (jus_gerak.py: condong, gepeng, putar) dipasang tanpa
        # menyentuh tulang maupun klip. Di titik telapak, jadi gepeng dan
        # condong berporos di tanah.
        self.poros = parent.attachNewNode('poros_gerak')
        # Pinggang: condong dan putar badan berporos di sini, bukan di
        # telapak. Berporos di telapak, condong 30 derajat membuat seluruh
        # tokoh miring kaku seperti papan yang mau tumbang (tangkapan pertama
        # jongkok memanen).
        self.pinggang = self.poros.attachNewNode('poros_pinggang')
        self.pinggang.setPos(0, TINGGI_PINGGANG, 0)
        self._tubuh = self.pinggang.attachNewNode('poros_tubuh')
        self._tubuh.setPos(0, -TINGGI_PINGGANG, 0)
        self.actor.reparentTo(self._tubuh)
        # Model menghadap -Z; entity game menganggap rotation_y 0 = menghadap +Z.
        self.actor.setH(180)
        gaya = _GAYA.get(name, {})
        self.actor.setScale(SKALA * gaya.get('skala', 1.0))
        self._ke_tengah(parent)
        self._melayang = gaya.get('melayang', 0.0)
        self._y_dasar = self.actor.getY()
        self._t_ayun = 0.0
        _warnai_material_polos(self.actor)
        self.anims = set(self.actor.getAnimNames())
        self.actor.enableBlend()
        self._bobot = {'idle': 1.0, 'walk': 0.0}
        for a in self._bobot:
            if a in self.anims:
                self.actor.loop(a)
                self.actor.setControlEffect(a, self._bobot[a])
        self._sekali = None
        self._sekali_t = 0.0
        self._sekali_dur = 1.0

    def _ke_tengah(self, parent):
        """Tarik model ke titik asal entity-nya, di bidang mendatar.

        Kelima belas .glb diekspor dari satu berkas Blender tempat semua tokoh
        berdiri berjajar, dan posisi jajarannya ikut terekspor: Arya bergeser
        1,3 m, Cici 10,4 m, Bowo 11,7 m dari titik entity-nya. Akibatnya
        warga terlihat berdiri jauh dari tempat yang dipakai jadwal, pie menu,
        dan kamera -- di layar mereka seperti hilang. Tinggi tidak disentuh:
        telapak memang di y 0.
        """
        try:
            b = self.actor.getTightBounds(parent)
        except Exception:
            b = None
        if not b:
            return
        lo, hi = b
        cx, cz = (lo.x + hi.x) / 2, (lo.z + hi.z) / 2
        p = self.actor.getPos()
        self.actor.setPos(p.x - cx, p.y, p.z - cz)

    def update(self, dt, laju):
        """laju: kecepatan dunia sekarang (0 = diam)."""
        if self._melayang:
            import math
            self._t_ayun += dt
            self.actor.setY(self._y_dasar + self._melayang
                            + math.sin(self._t_ayun * 1.6) * 0.08)
        jalan = 1.0 if laju > 0.05 else 0.0
        langkah = min(1.0, dt / _BAUR)
        w = self._bobot['walk'] + (jalan - self._bobot['walk']) * langkah
        self._bobot['walk'], self._bobot['idle'] = w, 1.0 - w
        if self._sekali is not None:
            self._sekali_t += dt
            if self._sekali_t >= self._sekali_dur:
                self.actor.setControlEffect(self._sekali, 0.0)
                self._sekali = None
        self._terapkan_baur(self.bobot_kerja())
        if 'walk' in self.anims and laju > 0.05:
            self.actor.setPlayRate(max(0.6, min(2.8, laju / _LAJU_ACUAN)), 'walk')

    # Baur klip kerja: masuk cepat (supaya ayunan tidak telat dari tombol),
    # keluar lebih lambat (supaya pulihnya terbaca sebagai gerak, bukan
    # potongan). Dulu bobot dibanting 0 -> 1 -> 0 dalam satu frame.
    _BAUR_MASUK = 0.07
    _BAUR_KELUAR = 0.22

    def mainkan_sekali(self, nama, laju=1.0):
        """Animasi kerja (hoe/swing/water) diputar sekali, dibaur masuk-keluar
        di atas baur diam/jalan."""
        if nama not in self.anims:
            return False
        if self._sekali and self._sekali != nama:
            self.actor.setControlEffect(self._sekali, 0.0)
        self.actor.setPlayRate(laju, nama)
        self.actor.play(nama)
        self._sekali = nama
        self._sekali_t = 0.0
        self._sekali_dur = max(0.1, self.actor.getDuration(nama) / max(0.1, laju))
        self._terapkan_baur(0.0)
        return True

    def bobot_kerja(self) -> float:
        """Bobot klip kerja sekarang (0..1), untuk probe dan lapisan gerak."""
        if self._sekali is None:
            return 0.0
        t, d = self._sekali_t, self._sekali_dur
        masuk = min(1.0, t / self._BAUR_MASUK)
        keluar = min(1.0, max(0.0, (d - t) / self._BAUR_KELUAR))
        return max(0.0, min(masuk, keluar))

    def _terapkan_baur(self, w):
        if self._sekali is not None:
            self.actor.setControlEffect(self._sekali, w)
        for a, b in self._bobot.items():
            if a in self.anims:
                self.actor.setControlEffect(a, b * (1.0 - w))

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
            self.poros.removeNode()
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
