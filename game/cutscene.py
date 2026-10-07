"""cutscene.py — Sinema: adegan bercerita yang mengambil alih layar sebentar.

Kenapa modul ini ada. Lembah Karsa sudah punya tulang cerita yang utuh dan
konsisten — Paman Arsa yang mewariskan kebun, perjanjian yang gagal ia
pulihkan, Naga Bumi yang menunggu "yang pantas", dan air keabadian di ujung
dua belas tahap quest. Semua itu tersebar di `LORE_ITEMS`, `QUEST_STAGES`, dan
dialog NPC. Yang tidak pernah ada: satu momen pun ketika permainan BERHENTI
dan menceritakannya. Pemain membaca ceritanya di kotak pesan sekilas, di
sela-sela menyiram lobak.

Cutscene menyelesaikan itu dengan satu hal yang tidak bisa dilakukan pesan
sekilas: **mengambil kendali**. Selama sinema berjalan, waktu berhenti, pemain
tidak bisa berjalan, dan layar dipersempit jadi pita — mata tahu ini bukan
lagi giliranmu.

Cara ia mengunci permainan sengaja menumpang yang sudah ada, bukan bikin
gerbang baru: `app.update()` menjalankan `player.tick`, jam, entity, dan dunia
HANYA saat `panels.mode == 'hud'`. Jadi menyetel mode ke `'sinema'` sudah
membekukan semuanya tanpa satu baris pun kondisi tambahan. Yang perlu
dijalankan di luar gerbang itu cuma runner ini, karena kameranya harus tetap
bergerak saat dunia beku.

Naskahnya daftar BEAT, dan tiap beat satu tuple. Bentuk ini dipilih supaya
menambah adegan tidak butuh menyentuh kode runner sama sekali:

    ('teks',   'Pembicara', 'Kalimatnya.')   tunggu pemain menekan tombol
    ('narasi', 'Kalimatnya.')                sama, tanpa nama pembicara
    ('jeda',   detik)                        diam sejenak, tidak bisa dilewati
    ('kamera', jarak, pitch, detik)          geser kamera mulus
    ('lore',   'lore_id')                    beri catatan ke koleksi pemain
    ('goyang', kekuatan, detik)              getar kamera

Yang SENGAJA tidak ada: percabangan pilihan, dan suara. Percabangan sudah
punya rumahnya sendiri di `BRANCHING_DIALOGUES` dan menaruh cabang kedua di
sini akan membelah satu urusan jadi dua tempat. Suara menunggu berkasnya ada.
"""
from __future__ import annotations

from ursina import Entity, Text, camera, color, destroy, window

_FONT_NAME = 'Montserrat-Bold.ttf'

# Tinggi pita hitam atas-bawah, dalam satuan camera.ui (layar = 1.0 tinggi).
TINGGI_PITA = 0.11

# Berapa lama pita masuk dan keluar. Cukup cepat untuk tidak membosankan,
# cukup lambat untuk terbaca sebagai "adegan dimulai" alih-alih kedipan.
DURASI_PITA = 0.45


# ═══ NASKAH ═══════════════════════════════════════════════════════════════
# Dipicu dari tahap quest yang sudah ada di QUEST_STAGES, bukan dari pemicu
# baru: ceritanya sudah punya urutan, sinema tinggal menandai belokannya.
#
# Tiap kunci di sini dicocokkan `pemicu_tahap()` dengan `state.quest_stage`.
NASKAH: dict[str, dict] = {

    'datang': {
        'judul': 'Lembah Karsa',
        'tahap': 0,
        'beat': [
            ('kamera', 30.0, 55.0, 0.1),
            ('narasi', 'Surat itu datang tiga minggu lalu, dan kau membacanya '
                       'sampai kertasnya lusuh.'),
            ('kamera', 16.0, 32.0, 3.2),
            ('narasi', 'Paman Arsa tidak meninggalkan uang. Ia meninggalkan '
                       'tanah, dan sebaris kalimat.'),
            ('teks', 'Paman Arsa', '"Kalau kau datang, jangan datang untuk '
                                   'mengambil."'),
            ('jeda', 0.6),
            ('narasi', 'Kebunnya menunggu. Kotak posnya juga.'),
        ],
    },

    'panen_pertama': {
        'judul': 'Yang Diberi',
        'tahap': 2,
        'beat': [
            ('kamera', 9.0, 22.0, 1.6),
            ('narasi', 'Tiga lobak. Kecil, dan tanganmu kotor.'),
            ('teks', 'Paman Arsa', '"Tanah tidak berutang apa pun padamu. '
                                   'Ia cuma mengembalikan."'),
            ('narasi', 'Kau ingat kalimat itu tanpa tahu dari mana ingatannya '
                       'datang.'),
        ],
    },

    'mulut_gua': {
        'judul': 'Yang Digali Terlalu Dalam',
        'tahap': 5,
        'beat': [
            ('kamera', 20.0, 18.0, 2.2),
            ('narasi', 'Mulut gua itu lebih dingin dari udara di sekitarnya.'),
            ('goyang', 0.012, 0.9),
            ('narasi', 'Ada yang bergerak jauh di bawah — pelan, seperti napas '
                       'yang sangat panjang.'),
            ('teks', 'Bu Sari', '"Pamanmu turun ke sana sendirian. Berkali-kali. '
                                'Ia tidak pernah bilang untuk apa."'),
        ],
    },

    'naga': {
        'judul': 'Yang Menunggu',
        'tahap': 10,
        'beat': [
            ('kamera', 24.0, 12.0, 2.0),
            ('goyang', 0.03, 1.4),
            ('teks', 'Sang Hyang Naga', '"Aku tidak tidur. Aku menunggu."'),
            ('teks', 'Sang Hyang Naga', '"Yang sebelummu datang membawa besi. '
                                        'Ia pergi membawa penyesalan."'),
            ('jeda', 0.5),
            ('teks', 'Sang Hyang Naga', '"Kau membawa apa?"'),
        ],
    },

    'tamat': {
        'judul': 'Perjanjian Dipulihkan',
        'tahap': 11,
        'beat': [
            ('kamera', 14.0, 40.0, 2.6),
            ('narasi', 'Airnya jernih, dan dingin, dan tidak istimewa sama '
                       'sekali sampai kau menyentuhnya.'),
            ('lore', 'surat_paman_arsa_2'),
            ('teks', 'Paman Arsa', '"Aku tidak pernah pergi. Aku selalu di '
                                   'sini, di dalam tanah yang kau rawat."'),
            ('jeda', 0.8),
            ('narasi', 'Lembah Karsa aman. Sekarang giliranmu menjaganya.'),
        ],
    },
}


def pemicu_tahap(tahap: int) -> str | None:
    """Nama sinema yang seharusnya main pada tahap quest ini, kalau ada."""
    for nama, sk in NASKAH.items():
        if sk.get('tahap') == tahap:
            return nama
    return None


# ═══ RUNNER ═══════════════════════════════════════════════════════════════

class Sinema:
    """Pemutar satu adegan. Satu instans dipakai ulang sepanjang permainan."""

    def __init__(self, app):
        self.app = app
        self.aktif = False
        self.nama = None
        self._beat = []
        self._i = 0
        self._t = 0.0            # waktu di dalam beat berjalan
        self._menunggu = False   # beat ini menunggu tombol pemain
        self._ui = []
        self._pita_t = 0.0
        self._kam_awal = None
        self._kam_tuju = None
        self._goyang = (0.0, 0.0)

    # ── siklus hidup ──────────────────────────────────────
    def mulai(self, nama: str) -> bool:
        """Mainkan sinema `nama`. False kalau tidak ada atau sudah pernah."""
        sk = NASKAH.get(nama)
        if not sk or self.aktif:
            return False
        s = self.app.state
        sudah = getattr(s, 'sinema_selesai', None)
        if sudah is None:
            sudah = s.sinema_selesai = []
        if nama in sudah:
            return False

        self.nama = nama
        self._beat = list(sk['beat'])
        self._i = -1
        self._t = 0.0
        self._pita_t = 0.0
        self.aktif = True
        self.app.panels.mode = 'sinema'
        self.app.panels.set_hud_visible(False)
        self._bangun_ui(sk.get('judul', ''))
        self._maju()
        return True

    def _bangun_ui(self, judul: str):
        self._bongkar_ui()
        lebar = window.aspect_ratio
        # Pita hitam atas dan bawah. Dibuat selebar aspek layar, bukan 1.0 —
        # camera.ui membentang -aspect/2..+aspect/2 secara horizontal, jadi
        # quad selebar 1.0 menyisakan celah di layar lebar.
        for arah in (1, -1):
            self._ui.append(Entity(
                parent=camera.ui, model='quad', color=color.black,
                scale=(lebar + 0.02, TINGGI_PITA),
                position=(0, arah * (0.5 + TINGGI_PITA / 2), 0),
                z=-0.9))
        self._judul = Text(
            judul, parent=camera.ui, font=_FONT_NAME, origin=(0, 0),
            position=(0, 0.5 - TINGGI_PITA / 2), scale=1.05,
            color=color.rgb(235, 225, 190), z=-0.95)
        self._ui.append(self._judul)

        self._nama_t = Text(
            '', parent=camera.ui, font=_FONT_NAME, origin=(-0.5, 0),
            position=(-lebar / 2 + 0.09, -0.5 + TINGGI_PITA + 0.115),
            scale=0.95, color=color.rgb(255, 214, 120), z=-0.95)
        self._baris_t = Text(
            '', parent=camera.ui, font=_FONT_NAME, origin=(-0.5, 0.5),
            position=(-lebar / 2 + 0.09, -0.5 + TINGGI_PITA + 0.072),
            scale=0.85, color=color.rgb(240, 240, 235), z=-0.95)
        self._petunjuk = Text(
            '[SPACE] lanjut   [ESC] lewati', parent=camera.ui,
            font=_FONT_NAME, origin=(0.5, 0),
            position=(lebar / 2 - 0.03, -0.5 + TINGGI_PITA / 2),
            scale=0.62, color=color.rgb(150, 150, 145), z=-0.95)
        self._ui += [self._nama_t, self._baris_t, self._petunjuk]

    def _bongkar_ui(self):
        for e in self._ui:
            try:
                destroy(e)
            except Exception:
                pass
        self._ui = []

    def selesai(self):
        """Tutup sinema dan kembalikan kendali ke pemain."""
        if not self.aktif:
            return
        s = self.app.state
        if self.nama and self.nama not in s.sinema_selesai:
            s.sinema_selesai.append(self.nama)
        self._bongkar_ui()
        self.app.panels.set_hud_visible(True)
        self.aktif = False
        self.nama = None
        self._kam_awal = self._kam_tuju = None
        self._goyang = (0.0, 0.0)
        self.app.panels.mode = 'hud'

    # ── input ─────────────────────────────────────────────
    def input(self, key):
        if not self.aktif:
            return
        if key == 'escape':
            # Melewati sinema tetap menjalankan beat `lore`: catatan cerita
            # adalah barang yang dikumpulkan, bukan hiasan adegan, dan pemain
            # yang tidak sabar tidak boleh kehilangan koleksinya.
            for b in self._beat[max(0, self._i):]:
                if b and b[0] == 'lore':
                    self._beri_lore(b[1])
            self.selesai()
        elif key in ('space', 'enter', 'e') and self._menunggu:
            self._maju()

    # ── jalannya adegan ───────────────────────────────────
    def _maju(self):
        self._i += 1
        self._t = 0.0
        self._menunggu = False
        if self._i >= len(self._beat):
            self.selesai()
            return

        b = self._beat[self._i]
        jenis = b[0]

        if jenis == 'teks':
            self._nama_t.text = b[1]
            self._baris_t.text = b[2]
            self._menunggu = True
        elif jenis == 'narasi':
            self._nama_t.text = ''
            self._baris_t.text = b[1]
            self._menunggu = True
        elif jenis == 'jeda':
            pass                       # ditunggu di tick()
        elif jenis == 'kamera':
            self._kam_awal = (self.app.camera_dist, self.app.camera_pitch)
            self._kam_tuju = (float(b[1]), float(b[2]))
        elif jenis == 'goyang':
            self._goyang = (float(b[1]), float(b[2]))
        elif jenis == 'lore':
            self._beri_lore(b[1])
            self._maju()               # tidak memakan waktu
        else:
            self._maju()               # beat tak dikenal dilewati, tidak macet

    def _beri_lore(self, lore_id: str):
        try:
            self.app.player._add_lore(lore_id, self.app.panels)
        except Exception:
            pass

    def tick(self, dt: float):
        """Dipanggil tiap frame SELAMA sinema aktif, di luar gerbang 'hud'."""
        if not self.aktif:
            return
        self._t += dt
        self._pita_t = min(DURASI_PITA, self._pita_t + dt)

        # Pita meluncur masuk dari luar layar.
        p = self._pita_t / DURASI_PITA
        for i, e in enumerate(self._ui[:2]):
            arah = 1 if i == 0 else -1
            luar = 0.5 + TINGGI_PITA / 2
            dalam = 0.5 - TINGGI_PITA / 2
            e.y = arah * (luar + (dalam - luar) * p)

        b = self._beat[self._i] if 0 <= self._i < len(self._beat) else None
        if b is None:
            return
        jenis = b[0]

        if jenis == 'jeda':
            if self._t >= float(b[1]):
                self._maju()

        elif jenis == 'kamera' and self._kam_tuju:
            durasi = max(0.01, float(b[3]))
            k = min(1.0, self._t / durasi)
            # Smoothstep: berangkat dan berhenti pelan. Lerp lurus membuat
            # kamera terlihat disentak, dan sentakan itu yang paling cepat
            # membedakan adegan buatan tangan dari adegan yang dihitung.
            k = k * k * (3.0 - 2.0 * k)
            d0, p0 = self._kam_awal
            d1, p1 = self._kam_tuju
            self.app.camera_dist = d0 + (d1 - d0) * k
            self.app.camera_pitch = p0 + (p1 - p0) * k
            self.app._snap_camera_to_player()
            if k >= 1.0:
                self._maju()

        elif jenis == 'goyang':
            kuat, lama = self._goyang
            if self._t >= lama:
                self._goyang = (0.0, 0.0)
                self._maju()
            else:
                import random as _r
                sisa = 1.0 - (self._t / max(0.01, lama))
                camera.x = _r.uniform(-kuat, kuat) * sisa
                camera.y = _r.uniform(-kuat, kuat) * sisa
                if self._t + dt >= lama:
                    camera.x = camera.y = 0.0
