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
    ('kamera', jarak, pitch, detik, putar)   ... sambil mengorbit `putar` derajat
    ('lore',   'lore_id')                    beri catatan ke koleksi pemain
    ('goyang', kekuatan, detik)              getar kamera
    ('gelap',  alpha, detik)                 layar memudar ke/dari hitam (1 = hitam)
    ('kartu',  'Judul', 'anak judul', detik) kartu judul besar di tengah layar
    ('tujuan', 'teks' | None)                kotak "tujuan berikutnya"; None =
                                             langkah tutorial yang sedang aktif

Adegan dipicu dua cara. `tahap`: belokan quest (QUEST_STAGES). `syarat`:
fungsi state -> bool untuk INTERAKSI PERTAMA (surat dibaca, cangkul pertama,
pertama kali tiba di desa, ...). Dua-duanya hanya dicek di HUD, jadi adegan
tidak pernah memotong dialog, modal batin, atau menu yang sedang terbuka --
ia menunggu sampai pemain kembali ke dunia.

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


def _pernah_bicara(s) -> bool:
    from .data import HUMAN_NPCS
    return any(v > 0 for k, v in (getattr(s, 'npc_dialog_index', None) or {}).items()
               if k in HUMAN_NPCS)


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
            ('gelap', 1.0, 0.01),
            ('kamera', 30.0, 40.0, 0.01, 140.0),
            ('kartu', 'LEMBAH KARSA',
             'sebuah kebun  ·  sebuah janji  ·  sesuatu di bawah tanah', 3.4),
            ('gelap', 0.0, 1.8),
            ('narasi', 'Surat itu datang tiga minggu lalu, dan kau membacanya '
                       'sampai kertasnya lusuh.'),
            ('kamera', 24.0, 36.0, 4.2, -60.0),
            ('narasi', 'Lembah Karsa: desa kecil di antara gunung dan laut, '
                       'tempat orang masih menyapa tanah sebelum mencangkulnya.'),
            ('narasi', 'Paman Arsa tidak meninggalkan uang. Ia meninggalkan '
                       'sepetak kebun, rumah kayu, dan sebaris kalimat.'),
            ('teks', 'Paman Arsa', '"Kalau kau datang, jangan datang untuk '
                                   'mengambil."'),
            ('kamera', 15.0, 30.0, 3.0, -80.0),
            ('narasi', 'Orang desa bilang pamanmu menjaga sesuatu. Tidak ada '
                       'yang tahu apa.'),
            ('jeda', 0.5),
            ('narasi', 'Kebunnya menunggu. Kotak posnya juga.'),
            ('teks', 'Kendali', 'WASD jalan  ·  SHIFT lari  ·  Q/E putar '
                                'kamera  ·  F interaksi  ·  SPACE pakai alat'
                                '  ·  F1 panduan'),
            ('teks', 'Kendali', 'I inventaris  ·  J jurnal quest  ·  M peta'
                                '  ·  T tidur di rumah  ·  F5 simpan'),
            ('tujuan', None),
        ],
    },

    # ── Interaksi pertama: tiap hal baru diberi satu adegan pendek ──────
    # Pendek dengan sengaja (dua-empat beat): yang dijaga rasa "ini momen",
    # bukan menahan pemain. Tiap adegan ditutup langkah tutorial berikutnya,
    # jadi cerita dan petunjuk datang bersama, bukan bersaing.

    'surat': {
        'judul': 'Surat dari Paman',
        'syarat': lambda s: bool(getattr(s, 'mail_read', False)),
        'beat': [
            ('kamera', 11.0, 26.0, 1.4, 20.0),
            ('teks', 'Paman Arsa', '"Kebun ini tidak butuh tangan yang kuat. '
                                   'Ia butuh tangan yang kembali besok."'),
            ('teks', 'Paman Arsa', '"Mulailah dari tiga petak. Tanah yang '
                                   'terlalu banyak diminta akan diam."'),
            ('narasi', 'Di bawah tanda tangannya ada gambar kecil: sebuah '
                       'cangkul, dan tiga kotak.'),
            ('tujuan', None),
        ],
    },

    'cangkul': {
        'judul': 'Tanah Pertama',
        'syarat': lambda s: s.stats.get('tilled', 0) >= 1,
        'beat': [
            ('kamera', 8.0, 20.0, 1.2, -25.0),
            ('narasi', 'Mata cangkul masuk lebih mudah dari dugaanmu. Tanah '
                       'ini pernah digarap -- lama, dan dengan sabar.'),
            ('narasi', 'Ada bau besi dan hujan. Bau yang sama dengan jaket '
                       'Paman Arsa.'),
            ('tujuan', None),
        ],
    },

    'tanam': {
        'judul': 'Benih',
        'syarat': lambda s: s.stats.get('lobak_planted', 0) >= 1,
        'beat': [
            ('kamera', 7.5, 24.0, 1.2, 15.0),
            ('narasi', 'Benih lobak, tidak lebih besar dari kuku kelingking.'),
            ('teks', 'Paman Arsa', '"Yang kecil tidak perlu ditolong. Cukup '
                                   'jangan dilupakan."'),
            ('tujuan', None),
        ],
    },

    'siram': {
        'judul': 'Air',
        'syarat': lambda s: s.stats.get('watered', 0) >= 1,
        'beat': [
            ('kamera', 9.0, 30.0, 1.0),
            ('narasi', 'Tanah menghitam saat air meresap. Tetangga bilang, '
                       'petak yang disiram tiap hari tumbuh lebih manis.'),
            ('tujuan', None),
        ],
    },

    'pagi_kedua': {
        'judul': 'Pagi Kedua',
        'syarat': lambda s: getattr(s, 'day', 1) >= 2,
        'beat': [
            ('gelap', 1.0, 0.01),
            ('gelap', 0.0, 1.4),
            ('kamera', 22.0, 40.0, 2.6, 35.0),
            ('narasi', 'Kau bangun sebelum ayam. Lembah masih berkabut, dan '
                       'untuk pertama kalinya kau tidak merasa tamu di sini.'),
            ('tujuan', None),
        ],
    },

    'kirim': {
        'judul': 'Peti Kirim',
        'syarat': lambda s: s.stats.get('earned', 0) > 0,
        'beat': [
            ('kamera', 12.0, 30.0, 1.4),
            ('narasi', 'Pagi ini peti kirim kosong, dan ada keping emas di '
                       'atas tutupnya. Seseorang di desa sudah membayar '
                       'kerjamu.'),
            ('teks', 'Paman Arsa', '"Jual secukupnya. Simpan yang kau perlu. '
                                   'Berikan sisanya."'),
            ('tujuan', None),
        ],
    },

    'warga': {
        'judul': 'Orang Lembah',
        # Indeks dialog diisi 0 untuk SEMUA warga sejak mereka muncul
        # (entities.py), jadi yang dihitung hanya warga manusia yang sudah
        # benar-benar diajak bicara (indeks > 0). Kotak pos juga menulis ke
        # sini dan bukan warga.
        'syarat': lambda s: _pernah_bicara(s),
        'beat': [
            ('kamera', 10.0, 22.0, 1.2, -20.0),
            ('narasi', 'Mereka mengenalmu sebelum kau memperkenalkan diri. '
                       'Kau keponakan Arsa -- itu sudah cukup.'),
            ('narasi', 'Ingat nama mereka. Bawa sesuatu sesekali [G]. Di '
                       'lembah ini, hadiah kecil diingat lebih lama dari '
                       'janji besar.'),
        ],
    },

    'ternak': {
        'judul': 'Yang Bernapas',
        'syarat': lambda s: (s.stats.get('produce_collected', 0) >= 1
                             or s.stats.get('trough_filled', 0) >= 1),
        'beat': [
            ('kamera', 9.0, 22.0, 1.2, 25.0),
            ('narasi', 'Hewan tidak peduli siapa yang mewarisi kebun. Mereka '
                       'peduli siapa yang datang tiap pagi.'),
            ('narasi', 'Isi palung, beri makan, sapa mereka [F]. Yang dirawat '
                       'akan memberi kembali.'),
        ],
    },

    'kota': {
        'judul': 'Desa Karsa',
        'syarat': lambda s: s.scene_name == 'town',
        'beat': [
            ('kamera', 30.0, 50.0, 0.01, -40.0),
            ('kamera', 20.0, 36.0, 3.0, 40.0),
            ('narasi', 'Warung, bengkel, klinik, dan papan pengumuman yang '
                       'tidak pernah kosong. Semua jalan di lembah berakhir '
                       'di sini.'),
            ('narasi', 'Hasil kebun dijual di Warung. Alat diperkuat di '
                       'Bengkel. Kabar desa ditempel di papan.'),
        ],
    },

    'pantai': {
        'judul': 'Pantai Selatan',
        'syarat': lambda s: s.scene_name == 'beach',
        'beat': [
            ('kamera', 26.0, 30.0, 2.8, 50.0),
            ('narasi', 'Mercusuar di ujung tanjung sudah lama mati. Kata '
                       'orang, kapal terakhir yang melihat cahayanya tidak '
                       'pernah berlabuh.'),
        ],
    },

    'danau': {
        'judul': 'Danau',
        'syarat': lambda s: s.scene_name == 'lake',
        'beat': [
            ('kamera', 22.0, 26.0, 2.6, -40.0),
            ('narasi', 'Airnya tenang sampai kau melempar kail. Lalu danau '
                       'ini ternyata penuh pendapat.'),
        ],
    },

    'gunung': {
        'judul': 'Lereng Gunung',
        'syarat': lambda s: s.scene_name == 'mountain',
        'beat': [
            ('kamera', 30.0, 42.0, 3.2, 60.0),
            ('narasi', 'Hutan pinus menutup lereng sampai ke tebing. Di '
                       'baliknya, mulut gua yang dijauhi orang desa.'),
            ('goyang', 0.006, 0.8),
            ('narasi', 'Tanah di sini terasa hangat, seperti ada yang '
                       'bernapas di bawahnya.'),
        ],
    },

    'kuburan': {
        'judul': 'Kuburan Tua',
        'syarat': lambda s: s.scene_name == 'cemetery',
        'beat': [
            ('kamera', 20.0, 34.0, 2.6, -45.0),
            ('narasi', 'Nisan-nisan tua tanpa nama. Lentera di sini menyala '
                       'sendiri saat senja, dan tidak ada yang mengaku '
                       'menyalakannya.'),
            ('narasi', 'Yang bergentayangan di sini bisa ditangkap '
                       '[Shift]+[F] -- kalau kau berani.'),
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


def _syarat_benar(sk, s) -> bool:
    f = sk.get('syarat')
    if f is None:
        return False
    try:
        return bool(f(s))
    except Exception:
        return False


def pemicu_baru(s) -> str | None:
    """Adegan interaksi-pertama yang syaratnya baru terpenuhi, kalau ada.
    Urutan NASKAH = urutan prioritas; yang sudah ditonton dilewati."""
    sudah = getattr(s, 'sinema_selesai', None) or []
    for nama, sk in NASKAH.items():
        if nama not in sudah and _syarat_benar(sk, s):
            return nama
    return None


def tandai_yang_sudah_lewat(s) -> list:
    """Save lama: interaksi yang SUDAH pernah dilakukan sebelum adegannya ada
    tidak diputar susulan -- pemain yang sudah panen sepuluh kali tidak perlu
    diceritakan cangkul pertamanya. Dipanggil saat boot dan saat F9 memuat,
    SEBELUM frame HUD pertama. Syarat yang bergantung pada scene tidak
    ditandai di sini, kecuali scene tempat pemain sedang berdiri."""
    if not hasattr(s, 'sinema_selesai') or s.sinema_selesai is None:
        s.sinema_selesai = []
    baru = []
    for nama, sk in NASKAH.items():
        if nama not in s.sinema_selesai and _syarat_benar(sk, s):
            s.sinema_selesai.append(nama)
            baru.append(nama)
    return baru


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
        self._gelap_awal = self._gelap_tuju = 0.0
        self._tirai = None         # quad hitam layar penuh untuk beat 'gelap'

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
        # Kamera pemain disimpan: adegan boleh terbang dan mengorbit, tapi
        # sesudahnya pemain harus mendapat kembali sudutnya sendiri -- kalau
        # tidak, arah WASD (relatif kamera) berubah diam-diam tiap adegan.
        self._kam_pemain = (self.app.camera_dist, self.app.camera_pitch,
                            self.app.camera_yaw)
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

        # Alas teks: pita gelap tipis tepat di atas pita bawah, memudar ke
        # atas. Dulu teks putih duduk langsung di atas dunia -- terbaca di
        # tanah gelap, hilang di langit atau pasir.
        alas = Entity(parent=camera.ui, model='quad',
                      color=color.rgba(0, 0, 0, 150),
                      scale=(lebar + 0.02, 0.15),
                      position=(0, -0.5 + TINGGI_PITA + 0.075), z=-0.92)
        self._ui.append(alas)
        self._alas = alas

        # Kartu judul (beat 'kartu') dan tirai hitam (beat 'gelap'). Tirai
        # di bawah teks kartu tapi di atas dunia dan pita.
        self._tirai = Entity(parent=camera.ui, model='quad',
                             color=color.rgba(0, 0, 0, 0),
                             scale=(lebar + 0.04, 1.04), z=-0.93)
        self._kartu_j = Text('', parent=camera.ui, font=_FONT_NAME,
                             origin=(0, 0), position=(0, 0.035), scale=3.2,
                             color=color.rgba(244, 226, 170, 0), z=-0.97)
        self._kartu_s = Text('', parent=camera.ui, font=_FONT_NAME,
                             origin=(0, 0), position=(0, -0.045), scale=0.95,
                             color=color.rgba(210, 205, 190, 0), z=-0.97)
        self._kartu_garis = Entity(parent=camera.ui, model='quad',
                                   color=color.rgba(244, 226, 170, 0),
                                   scale=(0.34, 0.0025), position=(0, -0.008),
                                   z=-0.97)
        self._ui += [self._tirai, self._kartu_j, self._kartu_s, self._kartu_garis]

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
        self._tirai = None
        kp = getattr(self, '_kam_pemain', None)
        if kp:
            self.app.camera_dist, self.app.camera_pitch, self.app.camera_yaw = kp
            self._kam_pemain = None
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
        elif key in ('space', 'enter', 'f') and self._menunggu:
            self._maju()
        elif key in ('space', 'enter', 'f') and 0 <= self._i < len(self._beat) \
                and self._beat[self._i][0] == 'kartu':
            b = self._beat[self._i]
            lama = max(1.6, float(b[3]) if len(b) > 3 else 3.0)
            self._t = max(self._t, lama - 0.7)

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

        self._nama_t.color = color.rgb(255, 214, 120)
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
            self._kam_awal = (self.app.camera_dist, self.app.camera_pitch,
                              self.app.camera_yaw)
            putar = float(b[4]) if len(b) > 4 else 0.0
            self._kam_tuju = (float(b[1]), float(b[2]),
                              self.app.camera_yaw + putar)
        elif jenis == 'gelap':
            self._gelap_awal = float(self._tirai.color[3]) if self._tirai else 0.0
            self._gelap_tuju = max(0.0, min(1.0, float(b[1])))
        elif jenis == 'kartu':
            self._kartu_j.text = b[1]
            self._kartu_s.text = b[2] if len(b) > 2 else ''
        elif jenis == 'tujuan':
            teks = b[1] if len(b) > 1 else None
            if teks is None:
                teks = self._tujuan_tutorial()
            if not teks:
                self._maju()           # tutorial tamat: tidak ada yang ditunjuk
                return
            self._nama_t.text = 'TUJUAN BERIKUTNYA'
            self._nama_t.color = color.rgb(150, 225, 160)
            self._baris_t.text = teks
            self._menunggu = True
            return
        elif jenis == 'goyang':
            self._goyang = (float(b[1]), float(b[2]))
        elif jenis == 'lore':
            self._beri_lore(b[1])
            self._maju()               # tidak memakan waktu
        else:
            self._maju()               # beat tak dikenal dilewati, tidak macet

    def _tujuan_tutorial(self) -> str:
        try:
            from .tutorial import current_step
            cur = current_step(self.app.state)
        except Exception:
            return ''
        if cur is None:
            return ''
        _, step = cur
        return f"{step['label']}.  {step.get('hint', '')}".strip()

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
            d0, p0, y0 = self._kam_awal
            d1, p1, y1 = self._kam_tuju
            self.app.camera_dist = d0 + (d1 - d0) * k
            self.app.camera_pitch = p0 + (p1 - p0) * k
            self.app.camera_yaw = y0 + (y1 - y0) * k
            self.app._snap_camera_to_player()
            if k >= 1.0:
                self._maju()

        elif jenis == 'gelap':
            durasi = max(0.01, float(b[2]))
            k = min(1.0, self._t / durasi)
            a_ = self._gelap_awal + (self._gelap_tuju - self._gelap_awal) * k
            self._tirai.color = color.rgba(0, 0, 0, a_ * 255)
            if k >= 1.0:
                self._maju()

        elif jenis == 'kartu':
            # Masuk 0,7 dtk, tahan, keluar 0,7 dtk. SPACE melompat ke keluar.
            lama = max(1.6, float(b[3]) if len(b) > 3 else 3.0)
            t = self._t
            if t < 0.7:
                a_ = t / 0.7
            elif t > lama - 0.7:
                a_ = max(0.0, (lama - t) / 0.7)
            else:
                a_ = 1.0
            self._kartu_j.color = color.rgba(244, 226, 170, a_ * 255)
            self._kartu_s.color = color.rgba(210, 205, 190, a_ * 220)
            self._kartu_garis.color = color.rgba(244, 226, 170, a_ * 200)
            # Judul sedikit membesar selama tampil: kartu yang diam terbaca
            # sebagai gambar, yang bergerak pelan terbaca sebagai adegan.
            self._kartu_j.scale = 3.0 + 0.25 * min(1.0, t / lama)
            if t >= lama:
                self._kartu_j.text = self._kartu_s.text = ''
                self._maju()

        elif jenis == 'goyang':
            kuat, lama = self._goyang
            if self._t >= lama:
                self._goyang = (0.0, 0.0)
                self.app._snap_camera_to_player()
                self._maju()
            else:
                # Getaran DI SEKITAR posisi kamera yang sah. Versi lama mengisi
                # camera.x/y (posisi dunia) dengan angka sekecil 0,01 -- kamera
                # terlempar ke dekat titik nol dunia selama getaran. Kekuatan
                # dikali 60 karena dulu dinyatakan dalam satuan layar.
                import random as _r
                self.app._snap_camera_to_player()
                sisa = 1.0 - (self._t / max(0.01, lama))
                camera.x += _r.uniform(-kuat, kuat) * 60 * sisa
                camera.y += _r.uniform(-kuat, kuat) * 60 * sisa
