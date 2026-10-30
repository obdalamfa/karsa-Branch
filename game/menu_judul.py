"""menu_judul.py — layar judul: hal pertama yang dilihat pemain.

Dulu `python main.py` langsung membuka Buat Karakter (game baru) atau
langsung menaruh pemain di kebun (save ada). Tidak ada judul, tidak ada
pilihan "lanjutkan atau mulai baru", dan tidak ada momen yang memberi tahu
"ini Lembah Karsa". Layar ini mengisi celah itu dengan bahan yang sudah ada:
dunia yang sudah dimuat di belakangnya, kamera yang pelan mengorbit kebun,
dan nama game.

Mode panel-nya 'judul'. Seperti 'sinema', mode itu ada di luar gerbang
`mode == 'hud'` di app.update(), jadi dunia beku (waktu, pemain, entity)
sementara kamera tetap diputar oleh `tick()` di sini.

Hanya `run()` (main.py, jalur pemain) yang membukanya. Alat ukur yang
membangun `Game3D()` langsung tidak melewati layar ini; layar ini sendiri
diuji `tools/probe_sinema.py` lewat `Game3D(layar_judul=True)`, persis jalur
`run()`.
"""
from __future__ import annotations

from ursina import Entity, Text, camera, color, destroy, mouse, window

_FONT = 'Montserrat-Bold.ttf'

EMAS = (244, 214, 140)
REDUP = (196, 190, 176)

PANDUAN = (
    "WASD  jalan            SHIFT  lari\n"
    "Q / E  putar kamera     roda mouse  zoom\n"
    "1-9  pilih alat         SPACE  pakai alat\n"
    "F  interaksi            SHIFT+F  tangkap\n"
    "I  inventaris  J  jurnal  M  peta  L  bangun\n"
    "T  tidur (di rumah)     F7  Majelis Batin\n"
    "F5 / F9  simpan / muat  F1  panduan lengkap"
)


class MenuJudul:
    """Layar judul. Dibuat sekali di boot, dibongkar saat pemain masuk."""

    def __init__(self, app, ada_save: bool):
        self.app = app
        self.aktif = True
        self._t = 0.0
        self._ents = []
        self._layar = 'utama'            # 'utama' | 'panduan' | 'konfirmasi'
        self._ada_save = ada_save
        self._pilih = 0
        self._bangun()
        self._isi_pilihan()

    # ── susunan ───────────────────────────────────────────────────────
    def _e(self, **kw):
        kw.setdefault('model', 'quad')
        e = Entity(parent=camera.ui, **kw)
        self._ents.append(e)
        return e

    def _txt(self, teks, **kw):
        t = Text(teks, parent=camera.ui, font=_FONT, **kw)
        self._ents.append(t)
        return t

    def _bangun(self):
        lebar = window.aspect_ratio
        kiri = -lebar / 2

        # Gradasi gelap dari kiri: dunia tetap terlihat di kanan, teks
        # terbaca di kiri. Satu quad dengan warna per-vertex -- pita
        # bertingkat (versi pertama) terlihat sebagai garis-garis vertikal.
        from ursina import Mesh
        w = 1.05
        gelap, bening = color.rgba(8, 10, 18, 215), color.rgba(8, 10, 18, 0)
        self._e(model=Mesh(vertices=[(-.5, -.5, 0), (.5, -.5, 0), (.5, .5, 0), (-.5, .5, 0)],
                           triangles=[(0, 1, 2), (0, 2, 3)],
                           colors=[gelap, bening, bening, gelap]),
                scale=(w, 1.02), position=(kiri + w / 2, 0), z=0.5)
        # Pita sinematik atas-bawah tipis.
        for arah in (1, -1):
            self._e(color=color.rgba(0, 0, 0, 200), scale=(lebar + 0.02, 0.06),
                    position=(0, arah * 0.47), z=0.4)

        x = kiri + 0.11
        self._judul = self._txt('LEMBAH KARSA', origin=(-0.5, 0),
                                position=(x, 0.25), scale=3.0,
                                color=color.rgb(*EMAS), z=0.1)
        self._garis = self._e(color=color.rgb(*EMAS), scale=(0.0, 0.003),
                              position=(x, 0.205), origin=(-0.5, 0), z=0.1)
        self._anak = self._txt('sebuah kebun  ·  sebuah janji  ·  sesuatu di '
                               'bawah tanah', origin=(-0.5, 0),
                               position=(x, 0.175), scale=0.82,
                               color=color.rgb(*REDUP), z=0.1)

        self._item = []
        for i in range(4):
            t = self._txt('', origin=(-0.5, 0), position=(x + 0.03, 0.03 - i * 0.075),
                          scale=1.35, color=color.rgb(*REDUP), z=0.1)
            self._item.append(t)
        # Penanda pilihan: belah ketupat kecil (quad diputar 45 derajat),
        # bukan karakter ">" -- font tidak menjamin glif ornamen.
        self._penanda = self._e(color=color.rgb(*EMAS), scale=(0.016, 0.016),
                                rotation_z=45, position=(x + 0.008, 0.03), z=0.1)
        self._sorot = self._e(color=color.rgba(244, 214, 140, 28),
                              scale=(0.46, 0.062), origin=(-0.5, 0),
                              position=(x - 0.02, 0.03), z=0.2)

        self._ket = self._txt('', origin=(-0.5, 0.5), position=(x, -0.29),
                              scale=0.8, color=color.rgb(*REDUP), z=0.1)
        self._kaki = self._txt('[W/S] pilih    [ENTER] masuk', origin=(0.5, 0),
                               position=(lebar / 2 - 0.04, -0.47), scale=0.7,
                               color=color.rgb(150, 146, 136), z=0.05)

        # Panel panduan (layar 'panduan'), disembunyikan dulu.
        self._p_bg = self._e(color=color.rgba(10, 12, 20, 225),
                             scale=(0.72, 0.42), position=(0.28, -0.02), z=0.15)
        self._p_teks = self._txt(PANDUAN, origin=(0, 0), position=(0.28, -0.02),
                                 scale=0.82, color=color.rgb(225, 222, 210), z=0.1)
        for e in (self._p_bg, self._p_teks):
            e.enabled = False

        # Tirai: masuk dari hitam.
        self._tirai = self._e(color=color.rgba(0, 0, 0, 255),
                              scale=(lebar + 0.04, 1.04), z=-0.5)

    # ── isi ───────────────────────────────────────────────────────────
    def _isi_pilihan(self):
        if self._layar == 'konfirmasi':
            self._opsi = [('baru_ya', 'Ya, mulai dari awal'), ('batal', 'Batal')]
            self._ket.text = ('Save lama tidak dihapus sekarang, tapi akan '
                              'tertimpa\nsaat permainan baru disimpan.')
        elif self._layar == 'panduan':
            self._opsi = [('batal', 'Kembali')]
            self._ket.text = ''
        else:
            self._opsi = []
            if self._ada_save:
                self._opsi.append(('lanjut', 'Lanjutkan'))
            self._opsi += [('baru', 'Permainan Baru'), ('panduan', 'Panduan'),
                           ('keluar', 'Keluar')]
            nama = getattr(self.app.state, 'char_name', '') if self._ada_save else ''
            s = self.app.state
            self._ket.text = (f'{nama}  ·  Hari {s.day_in_season}, {s.get_season_name()}' if nama
                              else '')
        self._pilih = min(self._pilih, len(self._opsi) - 1)
        for i, t in enumerate(self._item):
            t.text = self._opsi[i][1] if i < len(self._opsi) else ''
        tampil_p = self._layar == 'panduan'
        self._p_bg.enabled = self._p_teks.enabled = tampil_p
        self._segarkan()

    def _segarkan(self):
        for i, t in enumerate(self._item):
            pilih = i == self._pilih
            t.color = color.rgb(*EMAS) if pilih else color.rgb(*REDUP)
        y = self._item[self._pilih].y
        self._penanda.y = y
        self._sorot.y = y

    # ── input ─────────────────────────────────────────────────────────
    def input(self, key):
        if not self.aktif:
            return
        if key in ('w', 'up arrow', 'scroll up'):
            self._pilih = (self._pilih - 1) % len(self._opsi)
            self._segarkan()
        elif key in ('s', 'down arrow', 'scroll down'):
            self._pilih = (self._pilih + 1) % len(self._opsi)
            self._segarkan()
        elif key in ('enter', 'space', 'f'):
            self._jalankan(self._opsi[self._pilih][0])
        elif key == 'left mouse down':
            i = self._di_bawah_mouse()
            if i is not None:
                self._pilih = i
                self._jalankan(self._opsi[i][0])
        elif key == 'escape' and self._layar != 'utama':
            self._jalankan('batal')

    def _di_bawah_mouse(self):
        try:
            mx, my = mouse.position[0], mouse.position[1]
        except Exception:
            return None
        for i, t in enumerate(self._item[:len(self._opsi)]):
            if abs(my - t.y) < 0.032 and t.x - 0.04 < mx < t.x + 0.5:
                return i
        return None

    def _jalankan(self, aksi):
        if aksi == 'lanjut':
            self.app._tutup_judul(baru=False)
        elif aksi == 'baru':
            if self._ada_save:
                self._layar = 'konfirmasi'
                self._pilih = 1                     # aman: Batal terpilih
                self._isi_pilihan()
            else:
                self.app._tutup_judul(baru=True)
        elif aksi == 'baru_ya':
            self.app._tutup_judul(baru=True)
        elif aksi == 'panduan':
            self._layar = 'panduan'
            self._pilih = 0
            self._isi_pilihan()
        elif aksi == 'batal':
            self._layar = 'utama'
            self._pilih = 0
            self._isi_pilihan()
        elif aksi == 'keluar':
            from ursina import application
            application.quit()

    # ── per frame ─────────────────────────────────────────────────────
    def tick(self, dt):
        if not self.aktif:
            return
        self._t += dt
        t = self._t
        # Tirai memudar 1,6 dtk; garis judul memanjang; penanda berdenyut.
        self._tirai.color = color.rgba(0, 0, 0, max(0.0, 1.0 - t / 1.6) * 255)
        self._garis.scale_x = min(0.42, t * 0.35)
        import math
        self._penanda.scale = 0.016 + 0.003 * math.sin(t * 4.0)
        i = self._di_bawah_mouse()
        if i is not None and i != self._pilih:
            self._pilih = i
            self._segarkan()
        # Kamera mengorbit pelan di sekitar pemain: dunia hidup di belakang
        # menu, tanpa satu pun entity baru.
        a = self.app
        a.camera_yaw = (a.camera_yaw + dt * 5.0) % 360.0
        a.camera_pitch = 26.0
        a.camera_dist = 24.0
        a._snap_camera_to_player()

    def bongkar(self):
        self.aktif = False
        for e in self._ents:
            try:
                destroy(e)
            except Exception:
                pass
        self._ents = []
