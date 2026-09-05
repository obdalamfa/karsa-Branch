"""care_anim.py — Aksi perawatan yang PUNYA DURASI, dan kenapa 350 ms tidak cukup.

Sebelum modul ini, satu-satunya animasi aksi di game adalah `_play_tool_anim()`:
350 ms, satu tembakan, amplop segitiga linier (`st = 1 - |2t - 1|`), satu sendi.
Diukur dengan `tools/anim_trace.py`, gerakan seperti itu selalu keluar dengan
angka yang sama:

    antisipasi 0    tahanan 0    ikutan 0    ease 1,00    jeda sekunder 0

Keempat nol itu bukan detail halus — itu daftar persis dari hal-hal yang
membedakan gerakan yang DIANIMASIKAN dari gerakan yang cuma di-lerp. Mata tidak
menghitungnya, tapi mata melihat akibatnya: aksi 350 ms terbaca sebagai kedutan,
bukan sebagai pekerjaan yang dilakukan seseorang.

Yang dibangun di sini, dan sebabnya:

  FASE          Satu pekerjaan bukan satu ayunan. Menuang air = ancang-ancang,
                turun, tuang, tegak kembali, redam. Tiap fase punya durasi
                sendiri, jadi bagian yang harus lambat boleh lambat tanpa
                memperlambat seluruh aksi.
  KURVA         Segitiga linier berarti kecepatan konstan lalu berbalik arah
                seketika — tidak ada benda bermassa yang bergerak begitu.
                Kurva di sini punya percepatan; itulah yang diukur `ease`.
  ANTISIPASI    Gerak BERLAWANAN sebelum ayunan utama. Tanpa ini penonton tidak
                pernah diberi tahu gerakan akan terjadi, dan aksi mulai dari nol.
  TAHANAN       Pose puncak ditahan supaya mata sempat membacanya. Pose yang
                cuma disinggung satu frame sama saja dengan tidak ada.
  IKUTAN        Kembali ke pose diam LEWAT sedikit lalu balik. Berhenti mati
                tepat di titik akhir hanya terjadi pada mesin.
  JEDA SEKUNDER Badan, kepala, dan lengan lain menyusul beberapa frame di
                belakang penggerak. Semua bagian bergerak di frame yang sama
                adalah tanda paling jelas rig yang mati.

Modul ini sengaja generik: yang khusus-minum hanya satu entri di `RESEP`.
Potongan berikutnya (gosok, panen, bicara) menambah resepnya sendiri di situ dan
memakai mesin yang sama — jangan menyalin mesinnya.

Jam internalnya diekspos sebagai `player._care_anim` dengan atribut `t` (detik
sejak mulai), `fase` (nama fase sekarang), dan `jenis` (nama resep).
`tools/record.py` membaca ketiganya ke dalam jejak, jadi ketiga nama itu adalah
KONTRAK — jangan diganti tanpa mengganti perekamnya juga.
"""
from __future__ import annotations

import math


# ─── KURVA ───────────────────────────────────────────────────────────────────
# Semua menerima u di 0..1 dan mengembalikan 0..1 (kecuali 'balik', yang memang
# boleh lewat dari 1 — itu gunanya).

def _linier(u: float) -> float:
    return u


def _masuk(u: float) -> float:
    """Mulai pelan, makin cepat. Untuk gerakan yang membangun momentum."""
    return u * u * u


def _keluar(u: float) -> float:
    """Cepat lalu melambat. Untuk gerakan yang menabrak pose dan ditahan."""
    return 1.0 - (1.0 - u) ** 3


def _halus(u: float) -> float:
    """Pelan-cepat-pelan (kubik). Kurva serba guna."""
    return 4 * u ** 3 if u < 0.5 else 1.0 - ((-2 * u + 2) ** 3) / 2


def _balik(u: float) -> float:
    """Lewat dari target lalu balik — dipakai untuk ujung ayunan yang berat."""
    c1 = 1.70158
    c3 = c1 + 1.0
    return 1.0 + c3 * (u - 1.0) ** 3 + c1 * (u - 1.0) ** 2


def _redam(u: float) -> float:
    """Osilasi teredam: mendekat, lewat sedikit, mengecil. Untuk pose diam."""
    if u <= 0.0:
        return 0.0
    if u >= 1.0:
        return 1.0
    return 1.0 - math.exp(-6.5 * u) * math.cos(9.0 * u)


KURVA = {
    'linier': _linier, 'masuk': _masuk, 'keluar': _keluar,
    'halus': _halus, 'balik': _balik, 'redam': _redam,
}


# ─── PEMETAAN NAMA SENDI ─────────────────────────────────────────────────────
# Nama pendek dipakai di resep DAN di tools/record.py (JOINTS). Dua tempat itu
# harus memakai kosakata yang sama, kalau tidak jejak tidak bisa dibaca balik.
SENDI = {
    'bahu_r':    '_pivot_shoulder_r',
    'bahu_l':    '_pivot_shoulder_l',
    'siku_r':    '_pivot_elbow_r',
    'siku_l':    '_pivot_elbow_l',
    'pinggul_r': '_pivot_hip_r',
    'pinggul_l': '_pivot_hip_l',
    'lutut_r':   '_pivot_knee_r',
    'lutut_l':   '_pivot_knee_l',
    'badan':     'body',
    'leher':     '_pivot_neck',
    'alat':      '_care_prop',      # benda yang dipegang selama aksi
    'alat_hud':  '_held_tool',     # alat yang sudah di tangan (cangkul, penyiram)
}


class Jalur:
    """Satu kanal animasi: satu sifat, satu sendi, satu deret kunci.

    `kunci` = [(t_ms, nilai, kurva), ...] terurut. `kurva` berlaku untuk RUAS
    yang berakhir di kunci itu. `jeda_ms` menggeser seluruh jalur ke belakang —
    inilah gerak sekunder: badan dan kepala membaca kurva yang sama beberapa
    frame lebih lambat daripada tangan.

    `dasar`:
      'nol'  nilai kunci adalah pose absolut (semua rotasi memakai ini)
      'awal' nilai kunci ditambahkan ke nilai saat aksi dimulai (untuk .y,
             yang punya pose diam bukan-nol dan berbeda tiap rig)
    """
    __slots__ = ('sendi', 'sifat', 'kunci', 'jeda_ms', 'dasar', '_dasar_nilai')

    def __init__(self, sendi: str, sifat: str, kunci: list,
                 jeda_ms: float = 0.0, dasar: str = 'nol'):
        self.sendi = sendi
        self.sifat = sifat
        self.kunci = kunci
        self.jeda_ms = float(jeda_ms)
        self.dasar = dasar
        self._dasar_nilai = 0.0

    @property
    def akhir_ms(self) -> float:
        return self.kunci[-1][0] + self.jeda_ms

    def nilai_pada(self, t_ms: float) -> float:
        t = t_ms - self.jeda_ms
        k = self.kunci
        if t <= k[0][0]:
            return self._dasar_nilai + k[0][1]
        if t >= k[-1][0]:
            return self._dasar_nilai + k[-1][1]
        for i in range(1, len(k)):
            t1, v1, kur = k[i]
            if t <= t1:
                t0, v0 = k[i - 1][0], k[i - 1][1]
                span = max(1e-6, t1 - t0)
                u = (t - t0) / span
                f = KURVA.get(kur, _halus)(u)
                return self._dasar_nilai + v0 + (v1 - v0) * f
        return self._dasar_nilai + k[-1][1]


class AksiRawat:
    """Satu aksi perawatan yang sedang berjalan.

    Dipegang di `player._care_anim`. Tidak pernah mengunci pemain: `batal()`
    memulangkan pose lewat ruas keluar 200 ms, dan `tick()` di player.py
    memanggilnya begitu pemain menekan tombol jalan. Ada juga pagar keras
    (`_BATAS_AMAN_MS`) supaya aksi yang macet tetap berakhir sendiri.
    """
    _BATAS_AMAN_MS = 6000.0
    _KELUAR_MS = 200.0

    def __init__(self, jenis: str, fase: list, jalur: list,
                 pemicu: list | None = None, saat_frame=None, saat_usai=None):
        self.jenis = jenis
        self.t = 0.0                 # detik sejak mulai — dibaca tools/record.py
        self.fase = fase[0][0] if fase else ''
        self.selesai = False

        self._fase = fase            # [(nama, durasi_ms), ...]
        self._batas = []
        akum = 0.0
        for nama, dur in fase:
            akum += float(dur)
            self._batas.append((nama, akum))
        self.total_ms = akum

        self._jalur = jalur
        self._pemicu = sorted(pemicu or [], key=lambda p: p[0])
        self._pemicu_i = 0
        self._saat_frame = saat_frame
        self._saat_usai = saat_usai

        self._batal_t = None         # detik sejak batal, None = belum dibatalkan
        self._batal_dari: dict = {}
        self._player = None

    # ── siklus hidup ────────────────────────────────────────────────────────
    def mulai(self, player) -> None:
        self._player = player
        for j in self._jalur:
            if j.dasar == 'awal':
                ent = self._entitas(player, j.sendi)
                j._dasar_nilai = float(getattr(ent, j.sifat, 0.0)) if ent else 0.0
            else:
                j._dasar_nilai = 0.0

    def batal(self) -> None:
        """Pulangkan pose ke diam dalam 200 ms lalu berhenti.

        Dipanggil saat pemain jalan, saat aksi baru menimpa yang lama, atau saat
        scene berganti. Tidak pernah memotong pose di tengah udara — memotong
        mendadak terlihat seperti glitch, bukan seperti pembatalan.
        """
        if self._batal_t is not None or self.selesai:
            return
        self._batal_dari = {}
        for j in self._jalur:
            self._batal_dari[id(j)] = j.nilai_pada(self.t * 1000.0)
        self._batal_t = 0.0
        self.fase = 'batal'

    def update(self, dt: float) -> None:
        if self.selesai:
            return
        self.t += dt
        t_ms = self.t * 1000.0

        if self._batal_t is not None:
            self._batal_t += dt
            if self._batal_t * 1000.0 >= self._KELUAR_MS:
                self.selesai = True
            return

        # Fase sekarang. Nama fase adalah bagian dari kontrak jejak.
        for nama, batas in self._batas:
            if t_ms <= batas:
                self.fase = nama
                break
        else:
            self.fase = self._batas[-1][0] if self._batas else ''

        while self._pemicu_i < len(self._pemicu) and t_ms >= self._pemicu[self._pemicu_i][0]:
            try:
                self._pemicu[self._pemicu_i][1](self)
            except Exception:
                import logging
                logging.warning('[RAWAT] pemicu gagal', exc_info=True)
            self._pemicu_i += 1

        if self._saat_frame is not None:
            try:
                self._saat_frame(self, dt)
            except Exception:
                import logging
                logging.warning('[RAWAT] saat_frame gagal', exc_info=True)

        if t_ms >= self.total_ms or t_ms >= self._BATAS_AMAN_MS:
            self.selesai = True

    # ── penerapan ke rig ────────────────────────────────────────────────────
    @staticmethod
    def _entitas(player, sendi: str):
        attr = SENDI.get(sendi)
        return getattr(player, attr, None) if attr else None

    def terapkan(self, player) -> None:
        """Tulis pose frame ini ke rig. Dipanggil SESUDAH blok animasi lain di
        player.tick(), supaya aksi perawatan menang atas lerp-ke-nol idle.

        Jalur yang menulis ke kanal yang SAMA dijumlahkan, bukan saling
        menimpa. Itu yang membuat kedalaman jongkok bisa ditambahkan sebagai
        lapisan di atas resep apa pun tanpa menulis ulang resepnya — dan tanpa
        lapisan terakhir diam-diam menghapus yang sebelumnya.
        """
        t_ms = self.t * 1000.0
        keluar_u = None
        if self._batal_t is not None:
            keluar_u = min(1.0, self._batal_t * 1000.0 / self._KELUAR_MS)

        akum: dict = {}
        for j in self._jalur:
            ent = self._entitas(player, j.sendi)
            if ent is None:
                continue
            if keluar_u is None:
                nilai = j.nilai_pada(t_ms)
            else:
                asal = self._batal_dari.get(id(j), j._dasar_nilai)
                nilai = asal + (j._dasar_nilai - asal) * _keluar(keluar_u)
            kunci = (j.sendi, j.sifat)
            simpul = akum.get(kunci)
            if simpul is None:
                akum[kunci] = [ent, j._dasar_nilai, nilai - j._dasar_nilai]
            else:
                simpul[2] += nilai - j._dasar_nilai

        for (_sendi, sifat), (ent, dasar, delta) in akum.items():
            try:
                setattr(ent, sifat, dasar + delta)
            except Exception:
                pass

    def usai(self, player) -> None:
        """Bereskan: pulangkan kanal ke pose dasar dan lepas properti."""
        for j in self._jalur:
            ent = self._entitas(player, j.sendi)
            if ent is None:
                continue
            try:
                setattr(ent, j.sifat, j._dasar_nilai)
            except Exception:
                pass
        if self._saat_usai is not None:
            try:
                self._saat_usai(self)
            except Exception:
                import logging
                logging.warning('[RAWAT] saat_usai gagal', exc_info=True)


# ─── RESEP ───────────────────────────────────────────────────────────────────
# Satu resep = fase + jalur. Angkanya ditulis dalam derajat dan milidetik supaya
# bisa dibandingkan langsung dengan tabel ambang di _bench/BRIEF.md.
#
# Bacaan pose 'minum' (rig voxel, rotation_x negatif = lengan mengayun KE DEPAN):
#   ancang  lengan ditarik ke belakang, ember terangkat sedikit  (antisipasi)
#   turun   kedua lengan mengayun ke depan-bawah, lutut menekuk   (ayunan utama)
#   tuang   pose puncak DITAHAN 620 ms sambil air mengalir        (tahanan)
#   tegak   kembali, lewat sedikit dari pose diam                 (ikutan)
#   redam   osilasi mengecil sampai berhenti                      (settle)
#
# Lengan kiri, siku, badan, leher dan lutut membaca kurva yang sama dengan jeda
# 70-170 ms — itulah gerak sekunder yang diukur kolom 'jeda' di anim_trace.

_FASE_MINUM = [('ancang', 300), ('turun', 420), ('tuang', 620),
               ('tegak', 480), ('redam', 300)]


def _resep_minum() -> list:
    return [
        # Penggerak: bahu kanan. Rentang 73°, puncak ditahan 620 ms.
        Jalur('bahu_r', 'rotation_x', [
            (0,     0.0,  'halus'),
            (300,  17.0,  'keluar'),      # antisipasi: tarik ke belakang
            (720, -52.0,  'masuk'),       # ayunan utama ke depan-bawah
            (1030, -56.0, 'halus'),       # menekan sedikit lebih dalam
            (1340, -50.0, 'halus'),       # ember hampir kosong, mulai naik
            (1820,   8.0, 'halus'),       # ikutan: lewat dari pose diam
            (2120,   0.0, 'redam'),
        ]),
        # Tangan kiri menopang ember — menyusul 120 ms di belakang tangan kanan.
        Jalur('bahu_l', 'rotation_x', [
            (0,     0.0, 'halus'),
            (300,  14.0, 'keluar'),
            (720, -43.0, 'masuk'),
            (1030, -46.0, 'halus'),
            (1340, -41.0, 'halus'),
            (1820,   7.0, 'halus'),
            (2120,   0.0, 'redam'),
        ], jeda_ms=120),
        Jalur('siku_r', 'rotation_x', [
            (0,     0.0, 'halus'),
            (300,   7.0, 'keluar'),
            (720, -28.0, 'masuk'),
            (1030, -34.0, 'halus'),
            (1340, -24.0, 'halus'),
            (1820,   5.0, 'halus'),
            (2120,   0.0, 'redam'),
        ], jeda_ms=70),
        Jalur('siku_l', 'rotation_x', [
            (0,     0.0, 'halus'),
            (300,   6.0, 'keluar'),
            (720, -24.0, 'masuk'),
            (1030, -29.0, 'halus'),
            (1340, -20.0, 'halus'),
            (1820,   4.0, 'halus'),
            (2120,   0.0, 'redam'),
        ], jeda_ms=170),
        # Badan mencondong ke depan MENGIKUTI tangan, bukan bersamaan.
        Jalur('badan', 'rotation_x', [
            (0,    0.0, 'halus'),
            (300, -5.0, 'keluar'),
            (720, 15.0, 'masuk'),
            (1030, 17.0, 'halus'),
            (1340, 14.0, 'halus'),
            (1820, -3.0, 'halus'),
            (2120,  0.0, 'redam'),
        ], jeda_ms=95),
        Jalur('leher', 'rotation_x', [
            (0,    0.0, 'halus'),
            (300, -6.0, 'keluar'),
            (720, 20.0, 'masuk'),
            (1030, 24.0, 'halus'),      # menunduk melihat palung
            (1340, 18.0, 'halus'),
            (1820, -4.0, 'halus'),
            (2120,  0.0, 'redam'),
        ], jeda_ms=140),
        # Lutut menekuk sedikit menahan berat ember. Kecil tapi bukan nol:
        # berdiri kaku sambil menuang air seember adalah tanda rig yang mati.
        Jalur('lutut_r', 'rotation_x', [
            (0,    0.0, 'halus'), (300, -3.0, 'keluar'), (720, 13.0, 'masuk'),
            (1030, 15.0, 'halus'), (1340, 12.0, 'halus'), (1820, -2.0, 'halus'),
            (2120, 0.0, 'redam'),
        ], jeda_ms=110),
        Jalur('lutut_l', 'rotation_x', [
            (0,    0.0, 'halus'), (300, -3.0, 'keluar'), (720, 13.0, 'masuk'),
            (1030, 15.0, 'halus'), (1340, 12.0, 'halus'), (1820, -2.0, 'halus'),
            (2120, 0.0, 'redam'),
        ], jeda_ms=150),
        Jalur('pinggul_r', 'rotation_x', [
            (0, 0.0, 'halus'), (300, 2.0, 'keluar'), (720, -9.0, 'masuk'),
            (1030, -10.0, 'halus'), (1340, -8.0, 'halus'), (1820, 1.5, 'halus'),
            (2120, 0.0, 'redam'),
        ], jeda_ms=110),
        Jalur('pinggul_l', 'rotation_x', [
            (0, 0.0, 'halus'), (300, 2.0, 'keluar'), (720, -9.0, 'masuk'),
            (1030, -10.0, 'halus'), (1340, -8.0, 'halus'), (1820, 1.5, 'halus'),
            (2120, 0.0, 'redam'),
        ], jeda_ms=150),
        # Turun badan: berat ember ditahan lutut, bukan cuma bahu.
        Jalur('badan', 'y', [
            (0, 0.0, 'halus'), (300, 0.030, 'keluar'), (720, -0.105, 'masuk'),
            (1030, -0.125, 'halus'), (1340, -0.098, 'halus'), (1820, 0.020, 'halus'),
            (2120, 0.0, 'redam'),
        ], jeda_ms=95, dasar='awal'),
        Jalur('leher', 'y', [
            (0, 0.0, 'halus'), (300, 0.030, 'keluar'), (720, -0.105, 'masuk'),
            (1030, -0.125, 'halus'), (1340, -0.098, 'halus'), (1820, 0.020, 'halus'),
            (2120, 0.0, 'redam'),
        ], jeda_ms=110, dasar='awal'),
        Jalur('bahu_r', 'y', [
            (0, 0.0, 'halus'), (300, 0.030, 'keluar'), (720, -0.105, 'masuk'),
            (1030, -0.125, 'halus'), (1340, -0.098, 'halus'), (1820, 0.020, 'halus'),
            (2120, 0.0, 'redam'),
        ], jeda_ms=95, dasar='awal'),
        Jalur('bahu_l', 'y', [
            (0, 0.0, 'halus'), (300, 0.030, 'keluar'), (720, -0.105, 'masuk'),
            (1030, -0.125, 'halus'), (1340, -0.098, 'halus'), (1820, 0.020, 'halus'),
            (2120, 0.0, 'redam'),
        ], jeda_ms=120, dasar='awal'),
        # Ember itu sendiri: dimiringkan sampai mulutnya menghadap bawah, dan
        # DITAHAN miring selama fase tuang. Tanpa ini air keluar dari ember yang
        # tegak — kesalahan yang langsung terlihat di filmstrip.
        Jalur('alat', 'rotation_x', [
            (0,     0.0, 'halus'),
            (300, -12.0, 'keluar'),
            (720,  88.0, 'masuk'),
            (1030, 104.0, 'halus'),
            (1340,  96.0, 'halus'),
            (1820, -10.0, 'halus'),
            (2120,   0.0, 'redam'),
        ], jeda_ms=40),
    ]



# ── GOSOK ────────────────────────────────────────────────────────────────────
# Menyikat bukan satu ayunan, ia lima sapuan. Yang membuatnya terbaca sebagai
# menyikat dan bukan sebagai lengan berkedut ada tiga:
#
#   1. JUMLAH   minimal empat pembalikan arah. Dua sapuan terbaca sebagai
#               ragu-ragu, bukan sebagai pekerjaan.
#   2. IRAMA    jarak antar sapuan sengaja TIDAK sama (300/300/340/290/360/310
#               ms). Metronom sempurna adalah tanda mesin; tangan manusia
#               selalu meleset sedikit. anim_trace mengukurnya sbg irama_sd_ms.
#   3. SAPUAN   lengan tidak cuma maju-mundur; ia juga menyapu ke SAMPING
#               (rotation_z) dengan fase yang digeser, jadi ujung sikat
#               menggambar bentuk lonjong di badan hewan, bukan garis lurus.
#
# Amplitudo tiap sapuan sengaja mengecil ke belakang: sapuan pertama paling
# dalam, yang terakhir paling ringan. Lima sapuan seragam terbaca sebagai
# perulangan; yang meredup terbaca sebagai satu pekerjaan yang selesai.
_FASE_GOSOK = [('dekat', 420), ('sapu', 1900), ('tarik', 380), ('redam', 300)]


def _resep_gosok() -> list:
    # (ms, derajat) sapuan utama pada bahu kanan
    bahu = [
        (0,      0.0, 'halus'),
        (160,   13.0, 'keluar'),      # antisipasi: tarik bahu ke belakang
        (420,  -58.0, 'masuk'),       # sikat menempel di badan hewan
        (720,  -30.0, 'halus'),       # sapuan 1 kembali
        (1020, -60.0, 'halus'),
        (1360, -33.0, 'halus'),
        (1650, -57.0, 'halus'),
        (2010, -31.0, 'halus'),
        (2320, -52.0, 'halus'),       # sapuan terakhir paling ringan
        (2600,   9.0, 'halus'),       # ikutan: lewat dari pose diam
        (2900,   0.0, 'redam'),
    ]

    def geser(kunci, skala, tambah=0.0, ms=0):
        """Salin jalur bahu dengan amplitudo lain dan waktu digeser.

        Dipakai untuk sendi pengikut. Menulis ulang delapan deret kunci dengan
        tangan adalah cara termurah membuat dua sendi diam-diam tidak sinkron.
        """
        return [(t + ms, v * skala + tambah, k) for t, v, k in kunci]

    return [
        Jalur('bahu_r', 'rotation_x', bahu),
        # Sapuan ke samping: fasenya DIGESER setengah sapuan terhadap gerak
        # maju-mundur, jadi ujung sikat menggambar lonjong, bukan garis.
        Jalur('bahu_r', 'rotation_z', [
            (0,     0.0, 'halus'),
            (160,  -4.0, 'keluar'),
            (420,   6.0, 'masuk'),
            (870,  20.0, 'halus'),
            (1190,  4.0, 'halus'),
            (1500, 19.0, 'halus'),
            (1830,  5.0, 'halus'),
            (2160, 17.0, 'halus'),
            (2460,  3.0, 'halus'),
            (2600, -3.0, 'halus'),
            (2900,  0.0, 'redam'),
        ]),
        Jalur('siku_r', 'rotation_x', geser(bahu, 0.52), jeda_ms=70),
        # Tangan kiri menahan badan hewan — diam di satu pose, bukan ikut
        # menyapu. Dua tangan yang menyikat bersamaan terlihat seperti orang
        # menepuk-nepuk, bukan menyikat.
        Jalur('bahu_l', 'rotation_x', [
            (0,     0.0, 'halus'),
            (160,   8.0, 'keluar'),
            (520, -34.0, 'masuk'),
            (2320, -31.0, 'halus'),     # ditahan hampir dua detik penuh
            (2600,   6.0, 'halus'),
            (2900,   0.0, 'redam'),
        ], jeda_ms=110),
        Jalur('siku_l', 'rotation_x', [
            (0,     0.0, 'halus'),
            (160,   4.0, 'keluar'),
            (520, -22.0, 'masuk'),
            (2320, -20.0, 'halus'),
            (2600,   4.0, 'halus'),
            (2900,   0.0, 'redam'),
        ], jeda_ms=160),
        # Badan ikut mengayun pelan mengikuti sapuan, TELAT 130 ms. Inilah
        # gerak sekunder yang membedakan badan bermassa dari boneka kayu.
        Jalur('badan', 'rotation_x', geser(bahu, -0.16), jeda_ms=130),
        Jalur('badan', 'rotation_z', geser(bahu, 0.075), jeda_ms=175),
        Jalur('leher', 'rotation_x', geser(bahu, -0.21, tambah=0.0), jeda_ms=150),
        Jalur('leher', 'rotation_y', geser(bahu, 0.10), jeda_ms=195),
        Jalur('lutut_r', 'rotation_x', geser(bahu, -0.11), jeda_ms=140),
        Jalur('lutut_l', 'rotation_x', geser(bahu, -0.11), jeda_ms=185),
        Jalur('badan', 'y', [
            (0, 0.0, 'halus'), (160, 0.022, 'keluar'), (420, -0.062, 'masuk'),
            (1020, -0.070, 'halus'), (2320, -0.052, 'halus'),
            (2600, 0.016, 'halus'), (2900, 0.0, 'redam'),
        ], jeda_ms=130, dasar='awal'),
        Jalur('bahu_r', 'y', [
            (0, 0.0, 'halus'), (160, 0.022, 'keluar'), (420, -0.062, 'masuk'),
            (1020, -0.070, 'halus'), (2320, -0.052, 'halus'),
            (2600, 0.016, 'halus'), (2900, 0.0, 'redam'),
        ], jeda_ms=130, dasar='awal'),
        Jalur('bahu_l', 'y', [
            (0, 0.0, 'halus'), (160, 0.022, 'keluar'), (420, -0.062, 'masuk'),
            (1020, -0.070, 'halus'), (2320, -0.052, 'halus'),
            (2600, 0.016, 'halus'), (2900, 0.0, 'redam'),
        ], jeda_ms=155, dasar='awal'),
        Jalur('leher', 'y', [
            (0, 0.0, 'halus'), (160, 0.022, 'keluar'), (420, -0.062, 'masuk'),
            (1020, -0.070, 'halus'), (2320, -0.052, 'halus'),
            (2600, 0.016, 'halus'), (2900, 0.0, 'redam'),
        ], jeda_ms=150, dasar='awal'),
        # Sikat itu sendiri berputar sedikit tiap sapuan — bulu menekan badan
        # hewan lalu lepas. Rentangnya kecil supaya tidak terlihat berputar.
        Jalur('alat', 'rotation_x', [
            (0,    0.0, 'halus'), (160, -8.0, 'keluar'), (420, 26.0, 'masuk'),
            (720, 12.0, 'halus'), (1020, 28.0, 'halus'), (1360, 13.0, 'halus'),
            (1650, 27.0, 'halus'), (2010, 12.0, 'halus'), (2320, 24.0, 'halus'),
            (2600, -6.0, 'halus'), (2900, 0.0, 'redam'),
        ], jeda_ms=45),
    ]



# ── PANEN ────────────────────────────────────────────────────────────────────
# Tiga hasil ternak diambil dengan tiga cara yang sama sekali berbeda, dan
# perbedaan itu POSTUR, bukan ikon. Memakai satu animasi "ambil" untuk
# ketiganya adalah cara tercepat membuat sapi, ayam, dan domba terasa seperti
# tiga peti yang berbeda warna:
#
#   perah   jongkok DALAM di samping sapi, dua tangan di bawah badannya,
#           tarikan berirama bergantian kiri-kanan, lalu bangkit membawa ember
#   telur   jongkok sedang, SATU tangan masuk ke sarang, ditahan lama (meraba),
#           lalu ditarik keluar pelan — yang ditahan adalah ketidakpastiannya
#   cukur   berdiri membungkuk, sapuan gunting PANJANG menyusuri punggung,
#           badan ikut berputar mengikuti sapuan
#
# Yang menyatukan ketiganya: hasilnya harus TERLIHAT berpindah ke tangan di
# akhir. Barang yang muncul di inventori tanpa pernah melewati layar adalah
# alasan utama "ambil hasil" terasa seperti mengklik tombol.

_FASE_PERAH = [('turun', 620), ('perah', 1560), ('bangkit', 520), ('redam', 300)]
_FASE_TELUR = [('turun', 520), ('raba', 900), ('angkat', 560), ('redam', 300)]
_FASE_CUKUR = [('bungkuk', 480), ('cukur', 1740), ('tegak', 520), ('redam', 300)]


def _turun_badan(dalam: float, t_turun: int, t_tahan: int, t_naik: int,
                 t_akhir: int, jeda: int = 0):
    """Kanal .y untuk jongkok/membungkuk. `dalam` dalam meter, negatif = turun."""
    return [
        (0, 0.0, 'halus'),
        (t_turun // 3, -dalam * 0.12, 'keluar'),      # antisipasi: sedikit naik
        (t_turun, dalam, 'masuk'),
        (t_tahan, dalam * 1.06, 'halus'),
        (t_naik, dalam * 0.9, 'halus'),
        (t_akhir - 300, -dalam * 0.10, 'halus'),      # ikutan saat bangkit
        (t_akhir, 0.0, 'redam'),
    ]


def _resep_perah() -> list:
    # Tarikan bergantian: kanan pada 780/1180/1580, kiri pada 980/1380/1780.
    # Dua tangan yang menarik bersamaan terlihat seperti meremas, bukan memerah.
    #
    # Sudutnya diukur, bukan ditebak — dan tebakan pertamanya terbalik, persis
    # seperti pada resep telur. Versi lama menahan bahu di -70..-87 derajat
    # karena angka besar terbaca seperti "menjulur ke bawah sapi". Yang
    # sebenarnya terjadi: lengan menggantung dari bahu, jadi sudut sebesar itu
    # MENGANGKATNYA. Diukur di dalam mesin sendiri (resep ditambal jadi
    # tanjakan lambat 0 -> -90 derajat, lalu tiap frame dicatat posisi ujung
    # ember di ruang lokal sapi):
    #
    #     bahu -10  ->  lx 0,74  ly 0,33      bahu -50  ->  lx 0,13  ly 0,83
    #     bahu -28  ->  lx 0,40  ly 0,49      bahu -71  ->  lx 0,06  ly 1,26
    #     bahu -32  ->  lx 0,33  ly 0,55      bahu -86  ->  lx 0,12  ly 2,05
    #
    # Torso sapi setengah-lebarnya 0,36 m dan punggungnya 1,37 m. Jadi resep
    # lama memegang ember di ly 1,26-2,05 pada lx 0,06 — di GARIS TENGAH sapi,
    # setinggi punggungnya. Yang dianimasikan bukan memerah, tapi menjulurkan
    # tangan melewati sapi sambil menenteng ember di atas tulang belakangnya.
    #
    # Ambing ada di lx 0,33-0,40, ly 0,49-0,55: bahu -28..-34 derajat. Seluruh
    # tarikan dipindahkan ke pita itu.
    kanan = [
        (0,     0.0, 'halus'), (200,  11.0, 'keluar'), (620, -30.0, 'masuk'),
        (780, -34.0, 'halus'), (980, -27.0, 'halus'), (1180, -35.0, 'halus'),
        (1380, -28.0, 'halus'), (1580, -34.0, 'halus'), (1780, -28.0, 'halus'),
        (2180,   8.0, 'halus'), (2500,  0.0, 'redam'),
    ]
    kiri = [
        (0,     0.0, 'halus'), (200,   9.0, 'keluar'), (620, -28.0, 'masuk'),
        (780, -27.0, 'halus'), (980, -33.0, 'halus'), (1180, -28.0, 'halus'),
        (1380, -34.0, 'halus'), (1580, -28.0, 'halus'), (1780, -33.0, 'halus'),
        (2180,   7.0, 'halus'), (2500,  0.0, 'redam'),
    ]
    turun = _turun_badan(-0.50, 620, 1780, 2180, 2500)
    lutut = [
        (0, 0.0, 'halus'), (200, -4.0, 'keluar'), (620, 62.0, 'masuk'),
        (1780, 58.0, 'halus'), (2180, -5.0, 'halus'), (2500, 0.0, 'redam'),
    ]
    return [
        Jalur('bahu_r', 'rotation_x', kanan),
        Jalur('bahu_l', 'rotation_x', kiri, jeda_ms=60),
        Jalur('siku_r', 'rotation_x', [(t, v * 0.46, k) for t, v, k in kanan], jeda_ms=70),
        Jalur('siku_l', 'rotation_x', [(t, v * 0.46, k) for t, v, k in kiri], jeda_ms=90),
        Jalur('lutut_r', 'rotation_x', lutut, jeda_ms=40),
        Jalur('lutut_l', 'rotation_x', lutut, jeda_ms=85),
        Jalur('pinggul_r', 'rotation_x', [(t, -v * 0.55, k) for t, v, k in lutut], jeda_ms=40),
        Jalur('pinggul_l', 'rotation_x', [(t, -v * 0.55, k) for t, v, k in lutut], jeda_ms=85),
        Jalur('badan', 'rotation_x', [
            (0, 0.0, 'halus'), (200, -4.0, 'keluar'), (620, 26.0, 'masuk'),
            (1780, 24.0, 'halus'), (2180, -4.0, 'halus'), (2500, 0.0, 'redam'),
        ], jeda_ms=110),
        Jalur('leher', 'rotation_x', [
            (0, 0.0, 'halus'), (200, -5.0, 'keluar'), (620, 30.0, 'masuk'),
            (1780, 27.0, 'halus'), (2180, -5.0, 'halus'), (2500, 0.0, 'redam'),
        ], jeda_ms=155),
        Jalur('badan', 'y', turun, jeda_ms=0, dasar='awal'),
        Jalur('bahu_r', 'y', turun, jeda_ms=25, dasar='awal'),
        Jalur('bahu_l', 'y', turun, jeda_ms=55, dasar='awal'),
        Jalur('leher', 'y', turun, jeda_ms=80, dasar='awal'),
        Jalur('alat', 'rotation_x', [
            (0, 0.0, 'halus'), (200, -6.0, 'keluar'), (620, 16.0, 'masuk'),
            (1780, 14.0, 'halus'), (2180, -5.0, 'halus'), (2500, 0.0, 'redam'),
        ], jeda_ms=50),
    ]


def _resep_telur() -> list:
    # Satu tangan masuk ke sarang dan DITAHAN 1100 ms. Tahanan itu isinya
    # meraba — bagian yang membuat mengambil telur terasa seperti mencari,
    # bukan seperti memungut.
    #
    # Sudutnya diukur, bukan ditebak. Versi pertama menahan bahu di -84 derajat
    # karena angka besar terbaca seperti "menjulur jauh". Yang sebenarnya
    # terjadi: lengan menggantung dari bahu, jadi -84 mengangkatnya ke
    # MENDATAR setinggi bahu. Sepanjang 900 ms meraba itu tangannya melayang
    # 0,38-0,46 m DI ATAS ayamnya, dan baru menyentuh sarang selama 330 ms
    # saat ditarik keluar. Jarak ke kotak badan ayam nol di rentang -52..-20
    # derajat; seluruh rabaan sekarang ada di dalam rentang itu.
    kanan = [
        (0,     0.0, 'halus'), (170,  14.0, 'keluar'), (520, -46.0, 'masuk'),
        (760, -38.0, 'halus'),                          # tangan masuk sarang
        (960, -43.0, 'halus'), (1180, -33.0, 'halus'),  # meraba, gerak kecil
        (1420, -41.0, 'halus'),
        (1620, -30.0, 'halus'),                         # telurnya ketemu
        (1860,  -8.0, 'keluar'),                        # ditarik keluar pelan
        (2040,   9.0, 'halus'), (2280,  0.0, 'redam'),
    ]
    # Badan tetap rendah sampai tangannya benar-benar keluar: kalau ia mulai
    # bangkit di tengah rabaan, tangannya ikut terangkat lepas dari sarang.
    turun = _turun_badan(-0.30, 520, 1620, 1980, 2280)
    return [
        Jalur('bahu_r', 'rotation_x', kanan),
        Jalur('siku_r', 'rotation_x', [(t, v * 0.55, k) for t, v, k in kanan], jeda_ms=65),
        # Tangan kiri menahan tepi sarang — diam, bukan ikut meraba.
        Jalur('bahu_l', 'rotation_x', [
            (0, 0.0, 'halus'), (170, 7.0, 'keluar'), (520, -40.0, 'masuk'),
            (1860, -37.0, 'halus'), (1980, 6.0, 'halus'), (2280, 0.0, 'redam'),
        ], jeda_ms=120),
        Jalur('lutut_r', 'rotation_x', [
            (0, 0.0, 'halus'), (170, -3.0, 'keluar'), (520, 40.0, 'masuk'),
            (1620, 38.0, 'halus'), (1980, -4.0, 'halus'), (2280, 0.0, 'redam'),
        ], jeda_ms=45),
        Jalur('lutut_l', 'rotation_x', [
            (0, 0.0, 'halus'), (170, -3.0, 'keluar'), (520, 40.0, 'masuk'),
            (1620, 38.0, 'halus'), (1980, -4.0, 'halus'), (2280, 0.0, 'redam'),
        ], jeda_ms=90),
        Jalur('badan', 'rotation_x', [
            (0, 0.0, 'halus'), (170, -5.0, 'keluar'), (520, 34.0, 'masuk'),
            (1620, 31.0, 'halus'), (1980, -5.0, 'halus'), (2280, 0.0, 'redam'),
        ], jeda_ms=105),
        Jalur('leher', 'rotation_x', [
            (0, 0.0, 'halus'), (170, -6.0, 'keluar'), (520, 38.0, 'masuk'),
            (1620, 35.0, 'halus'), (1980, -6.0, 'halus'), (2280, 0.0, 'redam'),
        ], jeda_ms=150),
        Jalur('badan', 'y', turun, dasar='awal'),
        Jalur('bahu_r', 'y', turun, jeda_ms=25, dasar='awal'),
        Jalur('bahu_l', 'y', turun, jeda_ms=55, dasar='awal'),
        Jalur('leher', 'y', turun, jeda_ms=80, dasar='awal'),
    ]


def _resep_cukur() -> list:
    # Sapuan PANJANG menyusuri punggung: rentang rotation_z besar, jumlah
    # sapuan sedikit. Kebalikan dari menggosok, yang pendek dan banyak —
    # itulah yang membedakan keduanya sekilas.
    kanan = [
        (0,     0.0, 'halus'), (190,  15.0, 'keluar'), (480, -62.0, 'masuk'),
        (960, -38.0, 'halus'), (1320, -64.0, 'halus'),
        (1760, -36.0, 'halus'), (2100, -60.0, 'halus'),
        (2420,  10.0, 'halus'), (2740,   0.0, 'redam'),
    ]
    sapu_z = [
        (0,    0.0, 'halus'), (190, -6.0, 'keluar'), (480,  30.0, 'masuk'),
        (960, -18.0, 'halus'), (1320, 32.0, 'halus'),
        (1760, -16.0, 'halus'), (2100, 28.0, 'halus'),
        (2420, -5.0, 'halus'), (2740, 0.0, 'redam'),
    ]
    return [
        Jalur('bahu_r', 'rotation_x', kanan),
        Jalur('bahu_r', 'rotation_z', sapu_z),
        Jalur('siku_r', 'rotation_x', [(t, v * 0.5, k) for t, v, k in kanan], jeda_ms=75),
        Jalur('bahu_l', 'rotation_x', [
            (0, 0.0, 'halus'), (190, 8.0, 'keluar'), (560, -44.0, 'masuk'),
            (2100, -41.0, 'halus'), (2420, 7.0, 'halus'), (2740, 0.0, 'redam'),
        ], jeda_ms=115),
        # Badan BERPUTAR mengikuti sapuan panjang — inilah yang membuat sapuan
        # terasa panjang. Tanpa putaran badan, lengan sepanjang apa pun tetap
        # terlihat menyapu tempat yang sama.
        Jalur('badan', 'rotation_y', [(t, v * 0.42, k) for t, v, k in sapu_z], jeda_ms=140),
        Jalur('badan', 'rotation_x', [
            (0, 0.0, 'halus'), (190, -5.0, 'keluar'), (480, 30.0, 'masuk'),
            (2100, 27.0, 'halus'), (2420, -5.0, 'halus'), (2740, 0.0, 'redam'),
        ], jeda_ms=120),
        Jalur('leher', 'rotation_x', [
            (0, 0.0, 'halus'), (190, -6.0, 'keluar'), (480, 26.0, 'masuk'),
            (2100, 23.0, 'halus'), (2420, -5.0, 'halus'), (2740, 0.0, 'redam'),
        ], jeda_ms=165),
        Jalur('leher', 'rotation_y', [(t, v * 0.5, k) for t, v, k in sapu_z], jeda_ms=195),
        Jalur('lutut_r', 'rotation_x', [
            (0, 0.0, 'halus'), (190, -3.0, 'keluar'), (480, 20.0, 'masuk'),
            (2100, 18.0, 'halus'), (2420, -3.0, 'halus'), (2740, 0.0, 'redam'),
        ], jeda_ms=130),
        Jalur('lutut_l', 'rotation_x', [
            (0, 0.0, 'halus'), (190, -3.0, 'keluar'), (480, 20.0, 'masuk'),
            (2100, 18.0, 'halus'), (2420, -3.0, 'halus'), (2740, 0.0, 'redam'),
        ], jeda_ms=175),
        Jalur('badan', 'y', _turun_badan(-0.20, 480, 2100, 2420, 2740), dasar='awal'),
        Jalur('bahu_r', 'y', _turun_badan(-0.20, 480, 2100, 2420, 2740), jeda_ms=25, dasar='awal'),
        Jalur('leher', 'y', _turun_badan(-0.20, 480, 2100, 2420, 2740), jeda_ms=70, dasar='awal'),
        Jalur('alat', 'rotation_x', [
            (0, 0.0, 'halus'), (190, -9.0, 'keluar'), (480, 34.0, 'masuk'),
            (960, 16.0, 'halus'), (1320, 36.0, 'halus'), (1760, 15.0, 'halus'),
            (2100, 32.0, 'halus'), (2420, -7.0, 'halus'), (2740, 0.0, 'redam'),
        ], jeda_ms=55),
    ]



# ── BICARA ───────────────────────────────────────────────────────────────────
# Selama kotak dialog terbuka, seluruh dunia game ini BERHENTI: app.py hanya
# memanggil player.tick() dan entities.update() saat mode == 'hud'. Jadi
# bercakap-cakap secara harfiah adalah dua patung dan sebuah kotak teks.
#
# Yang dibangun di sini bukan "animasi bicara" dalam arti mulut bergerak —
# rig ini tidak punya mulut. Yang membuat orang terbaca sedang berbicara
# adalah ISYARAT: tangan naik pada ketukan kalimat, kepala mengangguk sedikit
# di akhir frasa, berat badan berpindah di antara kalimat. Tiga ketukan
# dengan jarak tidak sama, karena kalimat manusia juga tidak berjarak sama.
#
# Loop, bukan sekali jalan: percakapan berlangsung selama pemain membaca, dan
# panjangnya tidak bisa diketahui di depan.
_FASE_BICARA = [('angkat', 380), ('ketukan', 2020), ('turun', 420), ('jeda', 380)]


def _resep_bicara() -> list:
    # Tangan kanan memberi isyarat; kiri hampir diam (satu tangan yang
    # berbicara terbaca sebagai orang, dua tangan simetris sebagai boneka).
    kanan = [
        (0,     0.0, 'halus'),
        (140,   7.0, 'keluar'),        # antisipasi kecil sebelum tangan naik
        (380, -38.0, 'masuk'),         # tangan naik ke depan dada
        (700, -26.0, 'halus'),         # ketukan 1
        (1010, -44.0, 'halus'),
        (1380, -28.0, 'halus'),        # ketukan 2 (jaraknya beda)
        (1700, -46.0, 'halus'),
        (2120, -30.0, 'halus'),        # ketukan 3
        (2400, -41.0, 'halus'),
        (2820,   6.0, 'halus'),        # tangan turun, lewat sedikit
        (3200,   0.0, 'redam'),
    ]
    # Kepala mengangguk di AKHIR frasa, bukan bersamaan dengan tangan —
    # anggukan yang jatuh tepat di ketukan tangan terlihat seperti boneka
    # tali yang digerakkan satu benang.
    angguk = [
        (0,    0.0, 'halus'),
        (140, -2.5, 'keluar'),
        (860,  9.0, 'masuk'),
        (1100, 1.0, 'halus'),
        (1560, 8.0, 'halus'),
        (1820, 0.5, 'halus'),
        (2280, 7.0, 'halus'),
        (2560, 0.5, 'halus'),
        (2820, -2.0, 'halus'),
        (3200, 0.0, 'redam'),
    ]
    # Berat badan berpindah di antara kalimat: pelan, periodenya lebih panjang
    # daripada ketukan tangan, jadi keduanya tidak pernah sinkron.
    berat = [
        (0,    0.0, 'halus'), (600, 2.6, 'halus'), (1500, -2.2, 'halus'),
        (2400, 2.0, 'halus'), (3200, 0.0, 'redam'),
    ]
    return [
        Jalur('bahu_r', 'rotation_x', kanan),
        Jalur('siku_r', 'rotation_x', [(t, v * 0.62, k) for t, v, k in kanan], jeda_ms=80),
        Jalur('bahu_l', 'rotation_x', [(t, v * 0.16, k) for t, v, k in kanan], jeda_ms=190),
        Jalur('leher', 'rotation_x', angguk, jeda_ms=0),
        Jalur('leher', 'rotation_y', [(t, v * 0.55, k) for t, v, k in berat], jeda_ms=120),
        Jalur('badan', 'rotation_z', berat, jeda_ms=90),
        Jalur('badan', 'rotation_x', [(t, v * 0.30, k) for t, v, k in angguk], jeda_ms=150),
        Jalur('badan', 'y', [
            (0, 0.0, 'halus'), (600, 0.014, 'halus'), (1500, -0.012, 'halus'),
            (2400, 0.011, 'halus'), (3200, 0.0, 'redam'),
        ], jeda_ms=90, dasar='awal'),
        Jalur('leher', 'y', [
            (0, 0.0, 'halus'), (600, 0.014, 'halus'), (1500, -0.012, 'halus'),
            (2400, 0.011, 'halus'), (3200, 0.0, 'redam'),
        ], jeda_ms=120, dasar='awal'),
    ]


# Mendengarkan: tidak diam, tapi jauh lebih kecil. Pendengar yang benar-benar
# beku sama merusaknya dengan pembicara yang beku.
_FASE_DENGAR = [('dengar', 2600), ('jeda', 600)]


def _resep_dengar() -> list:
    return [
        Jalur('leher', 'rotation_x', [
            (0, 0.0, 'halus'), (900, 5.0, 'masuk'), (1150, 0.5, 'halus'),
            (2100, 4.0, 'halus'), (2400, 0.5, 'halus'), (3200, 0.0, 'redam'),
        ]),
        Jalur('leher', 'rotation_y', [
            (0, 0.0, 'halus'), (1300, -3.0, 'halus'), (2500, 2.4, 'halus'),
            (3200, 0.0, 'redam'),
        ], jeda_ms=140),
        Jalur('badan', 'rotation_z', [
            (0, 0.0, 'halus'), (1100, 1.6, 'halus'), (2300, -1.4, 'halus'),
            (3200, 0.0, 'redam'),
        ], jeda_ms=110),
        Jalur('bahu_r', 'rotation_x', [
            (0, 0.0, 'halus'), (1100, -5.0, 'halus'), (2300, -1.5, 'halus'),
            (3200, 0.0, 'redam'),
        ], jeda_ms=170),
        Jalur('badan', 'y', [
            (0, 0.0, 'halus'), (1100, 0.010, 'halus'), (2300, -0.008, 'halus'),
            (3200, 0.0, 'redam'),
        ], jeda_ms=110, dasar='awal'),
    ]



# ── BELAI ────────────────────────────────────────────────────────────────────
# Belai adalah aksi yang dipakai sebagai TITIK NOL sepanjang pekerjaan ini:
# diukur, ia menghasilkan "TIDAK ADA SENDI YANG BERGERAK" — cuma sebuah pesan.
# Membiarkannya begitu sementara tetangganya di menu yang sama sudah bergerak
# adalah ketimpangan paling terlihat di pie menu ternak.
#
# Yang membedakannya dari Gosok, dan kenapa keduanya tetap ada:
#
#   Belai   1,56 detik, SATU tangan, tanpa alat, dua usapan pendek, gratis.
#           Rentangnya sengaja separuh gosok (45 vs 73 derajat) — ini sapaan,
#           bukan pekerjaan.
#   Gosok   2,9 detik, sikat di tangan, enam sapuan, memakai energi, dan
#           benar-benar membersihkan.
#
# Kalau keduanya dianimasikan dengan bobot yang sama, salah satunya jadi
# mubazir. Beda panjang dan beda jumlah tangan itulah yang membuat pemain
# tahu mana yang "cuma menyapa" tanpa membaca satu baris teks pun.
_FASE_BELAI = [('raih', 300), ('usap', 700), ('tarik', 320), ('redam', 240)]


def _resep_belai() -> list:
    kanan = [
        (0,     0.0, 'halus'),
        (120,   9.0, 'keluar'),      # antisipasi: tangan sedikit mundur
        (300, -41.0, 'masuk'),       # telapak mendarat di badan hewan
        (520, -28.0, 'halus'),       # usapan 1
        (720, -44.0, 'halus'),
        (1000, -30.0, 'halus'),      # usapan 2, lebih ringan
        (1320,   7.0, 'halus'),      # ikutan
        (1560,   0.0, 'redam'),
    ]
    # Usapan menyamping, fase digeser: telapak menyusuri, bukan menepuk.
    samping = [
        (0,    0.0, 'halus'),
        (120, -3.0, 'keluar'),
        (300,  8.0, 'masuk'),
        (620, 17.0, 'halus'),
        (900,  5.0, 'halus'),
        (1180, 14.0, 'halus'),
        (1320, -2.0, 'halus'),
        (1560,  0.0, 'redam'),
    ]
    return [
        Jalur('bahu_r', 'rotation_x', kanan),
        Jalur('bahu_r', 'rotation_z', samping),
        Jalur('siku_r', 'rotation_x', [(t, v * 0.55, k) for t, v, k in kanan], jeda_ms=65),
        # Tangan kiri TIDAK ikut. Satu tangan yang mengusap terbaca sebagai
        # sapaan; dua tangan simetris terbaca sebagai memegangi hewan.
        Jalur('badan', 'rotation_x', [(t, -v * 0.14, k) for t, v, k in kanan], jeda_ms=110),
        Jalur('leher', 'rotation_x', [(t, -v * 0.22, k) for t, v, k in kanan], jeda_ms=140),
        Jalur('leher', 'rotation_y', [(t, v * 0.30, k) for t, v, k in samping], jeda_ms=175),
        Jalur('badan', 'rotation_z', [(t, v * 0.16, k) for t, v, k in samping], jeda_ms=150),
        Jalur('badan', 'y', [
            (0, 0.0, 'halus'), (120, 0.014, 'keluar'), (300, -0.042, 'masuk'),
            (1000, -0.036, 'halus'), (1320, 0.012, 'halus'), (1560, 0.0, 'redam'),
        ], jeda_ms=110, dasar='awal'),
        Jalur('bahu_r', 'y', [
            (0, 0.0, 'halus'), (120, 0.014, 'keluar'), (300, -0.042, 'masuk'),
            (1000, -0.036, 'halus'), (1320, 0.012, 'halus'), (1560, 0.0, 'redam'),
        ], jeda_ms=110, dasar='awal'),
        Jalur('leher', 'y', [
            (0, 0.0, 'halus'), (120, 0.014, 'keluar'), (300, -0.042, 'masuk'),
            (1000, -0.036, 'halus'), (1320, 0.012, 'halus'), (1560, 0.0, 'redam'),
        ], jeda_ms=135, dasar='awal'),
    ]



# ─── ALAT PERTANIAN ──────────────────────────────────────────────────────────
# Semua aksi di bawah ini dulu memakai _play_tool_anim(): segitiga linier 350 ms
# pada satu sendi. Diukur, semuanya menghasilkan antisipasi 0, tahanan 0,
# ikutan 0, ease 1,00 dan jeda sekunder 0 — definisi gerakan yang di-lerp,
# bukan dianimasikan.
#
# Durasinya sengaja jauh lebih pendek daripada aksi ternak (1,15-1,35 detik
# lawan 2,3-2,7). Mengurus seekor sapi terjadi sekali sehari; mencangkul
# terjadi dua puluh kali berturut-turut, dan aksi 2,5 detik akan mengubah
# bertani jadi menunggu.

_FASE_CANGKUL = [('angkat', 430), ('hantam', 330), ('pantul', 200), ('redam', 190)]


def _resep_cangkul() -> list:
    # Cangkul diangkat ke atas kepala lalu dijatuhkan. Yang membuatnya terbaca
    # sebagai KERJA dan bukan sebagai kedutan: jeda 100 ms di titik tertinggi
    # (mata sempat membaca posenya) dan pantulan yang lewat dari pose diam
    # sebelum kembali — tanah memantulkan cangkul, ia tidak berhenti mati.
    kanan = [
        (0,      0.0, 'halus'),
        (140,   14.0, 'keluar'),    # antisipasi: tangan turun sedikit dulu
        (430, -128.0, 'masuk'),     # cangkul di atas kepala
        (530, -132.0, 'halus'),     # tahanan puncak
        (700,  -18.0, 'masuk'),     # hantaman
        (760,   -6.0, 'halus'),     # tanah
        (830,    7.0, 'halus'),     # ikutan: lewat dari pose diam
        (960,   -9.0, 'halus'),
        (1150,   0.0, 'redam'),
    ]
    return [
        Jalur('bahu_r', 'rotation_x', kanan),
        Jalur('bahu_l', 'rotation_x', [(t, v * 0.62, k) for t, v, k in kanan], jeda_ms=45),
        Jalur('siku_r', 'rotation_x', [(t, v * 0.30, k) for t, v, k in kanan], jeda_ms=70),
        Jalur('badan', 'rotation_x', [(t, -v * 0.16, k) for t, v, k in kanan], jeda_ms=110),
        Jalur('leher', 'rotation_x', [(t, -v * 0.10, k) for t, v, k in kanan], jeda_ms=150),
        Jalur('lutut_r', 'rotation_x', [(t, -v * 0.13, k) for t, v, k in kanan], jeda_ms=95),
        Jalur('lutut_l', 'rotation_x', [(t, -v * 0.13, k) for t, v, k in kanan], jeda_ms=125),
        Jalur('badan', 'y', [
            (0, 0.0, 'halus'), (140, 0.020, 'keluar'), (430, 0.045, 'masuk'),
            (700, -0.075, 'masuk'), (830, -0.030, 'halus'), (1150, 0.0, 'redam'),
        ], jeda_ms=90, dasar='awal'),
    ]


_FASE_SIRAM = [('angkat', 420), ('tuang', 700), ('tegak', 280), ('redam', 200)]


def _resep_siram() -> list:
    # Menuang butuh TAHANAN, bukan ayunan: penyiram dimiringkan lalu ditahan
    # 560 ms sementara airnya keluar. Versi lama memakai kurva segitiga yang
    # sama dengan mencangkul, jadi menyiram terlihat seperti memukul tanah
    # dengan penyiram.
    kanan = [
        (0,     0.0, 'halus'),
        (150,   9.0, 'keluar'),
        (420, -62.0, 'masuk'),
        (560, -68.0, 'halus'),      # mulut penyiram turun, air keluar
        (980, -64.0, 'halus'),
        (1120, -70.0, 'halus'),     # kibasan terakhir, sisa tetesnya
        (1250,   6.0, 'keluar'),    # ikutan
        (1400,   0.0, 'redam'),
    ]
    # Penyiramnya sendiri ikut miring. Tanpa ini airnya keluar dari alat yang
    # tetap tegak — bagian yang paling cepat terbaca salah.
    miring = [
        (0,     0.0, 'halus'), (150,  -5.0, 'keluar'), (420,  46.0, 'masuk'),
        (560,  54.0, 'halus'), (980,  52.0, 'halus'), (1120, 57.0, 'halus'),
        (1250, -4.0, 'keluar'), (1400, 0.0, 'redam'),
    ]
    return [
        Jalur('bahu_r', 'rotation_x', kanan),
        # dasar='awal': pose diam penyiram di tangan bukan nol (-12 deg), jadi
        # menulis sudut mutlak akan meluruskannya PERMANEN begitu aksi usai.
        Jalur('alat_hud', 'rotation_x', miring, jeda_ms=40, dasar='awal'),
        Jalur('siku_r', 'rotation_x', [(t, v * 0.42, k) for t, v, k in kanan], jeda_ms=60),
        Jalur('bahu_l', 'rotation_x', [(t, v * 0.22, k) for t, v, k in kanan], jeda_ms=105),
        Jalur('badan', 'rotation_x', [(t, -v * 0.14, k) for t, v, k in kanan], jeda_ms=95),
        Jalur('leher', 'rotation_x', [(t, -v * 0.19, k) for t, v, k in kanan], jeda_ms=135),
        Jalur('badan', 'y', [
            (0, 0.0, 'halus'), (150, 0.012, 'keluar'), (420, -0.048, 'masuk'),
            (1120, -0.042, 'halus'), (1250, 0.010, 'halus'), (1400, 0.0, 'redam'),
        ], jeda_ms=85, dasar='awal'),
    ]


_FASE_TANAM = [('turun', 430), ('tekan', 520), ('bangkit', 300), ('redam', 200)]


def _resep_tanam() -> list:
    # Berjongkok, benih ditaruh, tanahnya DITEPUK dua kali. Tepukan kedua yang
    # lebih ringan daripada yang pertama — dua tepukan yang sama besar terbaca
    # sebagai perulangan mesin.
    kanan = [
        (0,     0.0, 'halus'),
        (140,  10.0, 'keluar'),
        (430, -38.0, 'masuk'),      # tangan sampai di tanah
        (620, -30.0, 'halus'),      # tepuk 1
        (800, -36.0, 'halus'),
        (950, -28.0, 'halus'),      # tepuk 2, lebih ringan
        (1080,  7.0, 'keluar'),     # ikutan saat bangkit
        (1250,  0.0, 'redam'),
    ]
    turun = _turun_badan(-0.55, 430, 950, 1080, 1250)
    return [
        Jalur('bahu_r', 'rotation_x', kanan),
        Jalur('siku_r', 'rotation_x', [(t, v * 0.48, k) for t, v, k in kanan], jeda_ms=60),
        Jalur('bahu_l', 'rotation_x', [(t, v * 0.35, k) for t, v, k in kanan], jeda_ms=110),
        Jalur('lutut_r', 'rotation_x', [
            (0, 0.0, 'halus'), (140, -4.0, 'keluar'), (430, 86.0, 'masuk'),
            (950, 82.0, 'halus'), (1080, -5.0, 'halus'), (1250, 0.0, 'redam'),
        ], jeda_ms=40),
        Jalur('lutut_l', 'rotation_x', [
            (0, 0.0, 'halus'), (140, -4.0, 'keluar'), (430, 86.0, 'masuk'),
            (950, 82.0, 'halus'), (1080, -5.0, 'halus'), (1250, 0.0, 'redam'),
        ], jeda_ms=85),
        Jalur('badan', 'rotation_x', [
            (0, 0.0, 'halus'), (140, -6.0, 'keluar'), (430, 40.0, 'masuk'),
            (950, 37.0, 'halus'), (1080, -6.0, 'halus'), (1250, 0.0, 'redam'),
        ], jeda_ms=100),
        Jalur('leher', 'rotation_x', [
            (0, 0.0, 'halus'), (140, -7.0, 'keluar'), (430, 34.0, 'masuk'),
            (950, 31.0, 'halus'), (1080, -7.0, 'halus'), (1250, 0.0, 'redam'),
        ], jeda_ms=145),
        Jalur('badan', 'y', turun, dasar='awal'),
        Jalur('bahu_r', 'y', turun, jeda_ms=25, dasar='awal'),
        Jalur('bahu_l', 'y', turun, jeda_ms=55, dasar='awal'),
        Jalur('leher', 'y', turun, jeda_ms=80, dasar='awal'),
    ]


_FASE_PETIK = [('turun', 440), ('genggam', 380), ('tarik', 280), ('angkat', 200)]


def _resep_petik() -> list:
    # Memanen tanaman bukan memungut: ada TAHANAN saat tangannya menggenggam
    # dan menahan beban, lalu tarikan cepat saat akarnya lepas. Perbedaan
    # kecepatan antara dua bagian itulah yang membuat tanahnya terasa
    # melawan — pada segitiga linier 350 ms tidak ada bedanya sama sekali.
    kanan = [
        (0,     0.0, 'halus'),
        (150,  11.0, 'keluar'),
        (440, -36.0, 'masuk'),      # tangan di pangkal batang
        (640, -30.0, 'halus'),      # menggenggam, menahan
        (820, -33.0, 'halus'),
        (960, -74.0, 'masuk'),      # lepas — tarikan cepat ke atas
        (1080, -58.0, 'keluar'),
        (1180,   8.0, 'halus'),     # ikutan
        (1300,   0.0, 'redam'),
    ]
    turun = _turun_badan(-0.52, 440, 820, 1080, 1300)
    return [
        Jalur('bahu_r', 'rotation_x', kanan),
        Jalur('siku_r', 'rotation_x', [(t, v * 0.52, k) for t, v, k in kanan], jeda_ms=55),
        Jalur('bahu_l', 'rotation_x', [(t, v * 0.30, k) for t, v, k in kanan], jeda_ms=115),
        Jalur('lutut_r', 'rotation_x', [
            (0, 0.0, 'halus'), (150, -4.0, 'keluar'), (440, 82.0, 'masuk'),
            (820, 79.0, 'halus'), (1080, 22.0, 'masuk'), (1300, 0.0, 'redam'),
        ], jeda_ms=45),
        Jalur('lutut_l', 'rotation_x', [
            (0, 0.0, 'halus'), (150, -4.0, 'keluar'), (440, 82.0, 'masuk'),
            (820, 79.0, 'halus'), (1080, 22.0, 'masuk'), (1300, 0.0, 'redam'),
        ], jeda_ms=90),
        Jalur('badan', 'rotation_x', [
            (0, 0.0, 'halus'), (150, -6.0, 'keluar'), (440, 38.0, 'masuk'),
            (820, 35.0, 'halus'), (1080, -8.0, 'halus'), (1300, 0.0, 'redam'),
        ], jeda_ms=105),
        Jalur('leher', 'rotation_x', [
            (0, 0.0, 'halus'), (150, -7.0, 'keluar'), (440, 32.0, 'masuk'),
            (820, 29.0, 'halus'), (1080, -9.0, 'halus'), (1300, 0.0, 'redam'),
        ], jeda_ms=150),
        Jalur('badan', 'y', turun, dasar='awal'),
        Jalur('bahu_r', 'y', turun, jeda_ms=25, dasar='awal'),
        Jalur('bahu_l', 'y', turun, jeda_ms=55, dasar='awal'),
        Jalur('leher', 'y', turun, jeda_ms=80, dasar='awal'),
    ]


_FASE_TEBANG = [('ancang', 520), ('tebas', 300), ('tancap', 330), ('cabut', 200)]


def _resep_tebang() -> list:
    # Kapak MENANCAP sebelum dicabut. Fase tancap 330 ms itu yang membedakan
    # menebang dari memukul: tanpa ia, kapaknya memantul dari batang seperti
    # dari karet.
    kanan = [
        (0,     0.0, 'halus'),
        (170,  18.0, 'keluar'),     # antisipasi besar — kapak berat
        (520, -150.0, 'masuk'),     # ancang-ancang penuh di belakang kepala
        (640, -156.0, 'halus'),     # tahanan puncak
        (820, -30.0, 'masuk'),      # tebasan
        (880, -14.0, 'halus'),      # mata kapak masuk kayu
        (1010, -20.0, 'halus'),     # menancap: gerak kecil, bukan diam
        (1150,   9.0, 'keluar'),    # dicabut, lewat dari pose diam
        (1240,  -6.0, 'halus'),
        (1350,   0.0, 'redam'),
    ]
    # Ayunan diagonal, bukan tegak lurus: kapak datang dari bahu ke pinggang.
    samping = [
        (0,    0.0, 'halus'), (170,  -4.0, 'keluar'), (520,  26.0, 'masuk'),
        (820,  -9.0, 'masuk'), (1010, -6.0, 'halus'), (1350, 0.0, 'redam'),
    ]
    return [
        Jalur('bahu_r', 'rotation_x', kanan),
        Jalur('bahu_r', 'rotation_z', samping),
        Jalur('bahu_l', 'rotation_x', [(t, v * 0.66, k) for t, v, k in kanan], jeda_ms=50),
        Jalur('siku_r', 'rotation_x', [(t, v * 0.26, k) for t, v, k in kanan], jeda_ms=75),
        Jalur('badan', 'rotation_x', [(t, -v * 0.15, k) for t, v, k in kanan], jeda_ms=120),
        Jalur('badan', 'rotation_z', [(t, v * 0.55, k) for t, v, k in samping], jeda_ms=140),
        Jalur('leher', 'rotation_x', [(t, -v * 0.09, k) for t, v, k in kanan], jeda_ms=165),
        Jalur('lutut_r', 'rotation_x', [(t, -v * 0.12, k) for t, v, k in kanan], jeda_ms=100),
        Jalur('lutut_l', 'rotation_x', [(t, -v * 0.12, k) for t, v, k in kanan], jeda_ms=130),
        Jalur('badan', 'y', [
            (0, 0.0, 'halus'), (170, 0.024, 'keluar'), (520, 0.052, 'masuk'),
            (820, -0.086, 'masuk'), (1010, -0.052, 'halus'), (1350, 0.0, 'redam'),
        ], jeda_ms=95, dasar='awal'),
    ]


_FASE_TAMBANG = [('ancang', 500), ('hantam', 320), ('pantul', 300), ('redam', 180)]


def _resep_tambang() -> list:
    # Batu tidak menyerap: beliung MEMANTUL. Pantulannya (-34 sesudah -8) lebih
    # besar daripada pantulan cangkul di tanah (7 sesudah -6), dan itulah satu
    # -satunya hal yang membedakan rasa dua aksi ini sekilas.
    kanan = [
        (0,     0.0, 'halus'),
        (160,  20.0, 'keluar'),
        (500, -165.0, 'masuk'),
        (600, -170.0, 'halus'),
        (770,  -25.0, 'masuk'),     # hantaman
        (820,   -8.0, 'halus'),     # batu
        (900,  -34.0, 'keluar'),    # pantulan keras
        (1000, -16.0, 'halus'),
        (1120,   8.0, 'halus'),     # ikutan
        (1300,   0.0, 'redam'),
    ]
    return [
        Jalur('bahu_r', 'rotation_x', kanan),
        Jalur('bahu_r', 'rotation_z', [
            (0, 0.0, 'halus'), (160, 3.0, 'keluar'), (500, -17.0, 'masuk'),
            (820, 6.0, 'masuk'), (900, -4.0, 'halus'), (1300, 0.0, 'redam'),
        ]),
        Jalur('bahu_l', 'rotation_x', [(t, v * 0.58, k) for t, v, k in kanan], jeda_ms=45),
        Jalur('siku_r', 'rotation_x', [(t, v * 0.24, k) for t, v, k in kanan], jeda_ms=70),
        Jalur('badan', 'rotation_x', [(t, -v * 0.13, k) for t, v, k in kanan], jeda_ms=115),
        Jalur('leher', 'rotation_x', [(t, -v * 0.08, k) for t, v, k in kanan], jeda_ms=160),
        Jalur('lutut_r', 'rotation_x', [(t, -v * 0.11, k) for t, v, k in kanan], jeda_ms=100),
        Jalur('lutut_l', 'rotation_x', [(t, -v * 0.11, k) for t, v, k in kanan], jeda_ms=128),
        Jalur('badan', 'y', [
            (0, 0.0, 'halus'), (160, 0.026, 'keluar'), (500, 0.056, 'masuk'),
            (770, -0.082, 'masuk'), (900, -0.046, 'halus'), (1300, 0.0, 'redam'),
        ], jeda_ms=92, dasar='awal'),
    ]


RESEP = {
    'minum': {'fase': _FASE_MINUM, 'jalur': _resep_minum,
              'alat': 'ember', 'aliran': True},
    # Menggosok TIDAK diberi kelonggaran. Diuji dengan 0,05 m: tembusan pada
    # kambing turun 10 -> 5 dari 90 frame, tapi sentuhan pada SAPI jatuh dari
    # 54 ke 40 dari 90 — dan sapi hewan yang paling sering disikat. Sisa
    # tembusan 0,12 m pada kambing dibiarkan, tercatat, tidak ditukar dengan
    # kemunduran pada kasus yang paling sering terjadi.
    'gosok': {'fase': _FASE_GOSOK, 'jalur': _resep_gosok,
              'alat': 'sikat', 'aliran': False},
    'perah': {'fase': _FASE_PERAH, 'jalur': _resep_perah, 'alat': 'ember'},
    # Ayam torsonya cuma 0,22 x 0,30 m, jadi tangan yang meleset 11 cm ke
    # dalam sudah setengah menembus burungnya. Terukur: 17 dari 68 frame lebih
    # dalam dari 8 cm sebelum kelonggaran ini ditambahkan.
    'telur': {'fase': _FASE_TELUR, 'jalur': _resep_telur, 'alat': None,
              'renggang': 0.09},
    # `renggang` = meter tambahan jarak berdiri, DI ATAS jangkauan yang sudah
    # diskalakan. Mencukur menyapu panjang lewat rotation_z, jadi ujung
    # bilahnya menjulur lebih jauh ke dalam daripada aksi lain dengan
    # jangkauan yang sama — terukur, ia terbenam 9-22 cm ke dalam torso domba
    # sepanjang sapuan.
    'cukur': {'fase': _FASE_CUKUR, 'jalur': _resep_cukur, 'alat': 'gunting',
              'renggang': 0.18},
    'belai': {'fase': _FASE_BELAI, 'jalur': _resep_belai, 'alat': None},
    'bicara': {'fase': _FASE_BICARA, 'jalur': _resep_bicara, 'alat': None},
    'dengar': {'fase': _FASE_DENGAR, 'jalur': _resep_dengar, 'alat': None},

    # Alat pertanian. `alat_hud` = alat yang SUDAH digenggam pemain tetap
    # terlihat dan ikut bergerak; jangan disembunyikan lalu diganti properti,
    # karena yang benar memang alat itu sendiri.
    'cangkul': {'fase': _FASE_CANGKUL, 'jalur': _resep_cangkul, 'alat_hud': True},
    'siram':   {'fase': _FASE_SIRAM,   'jalur': _resep_siram,   'alat_hud': True},
    'tanam':   {'fase': _FASE_TANAM,   'jalur': _resep_tanam,   'alat_hud': True},
    'petik':   {'fase': _FASE_PETIK,   'jalur': _resep_petik,   'alat_hud': True},
    'tebang':  {'fase': _FASE_TEBANG,  'jalur': _resep_tebang,  'alat_hud': True},
    'tambang': {'fase': _FASE_TAMBANG, 'jalur': _resep_tambang, 'alat_hud': True},
}




# ─── LAPISAN UKURAN ──────────────────────────────────────────────────────────
def _lapisan_skala(jalur: list, skala: float) -> list:
    """Perkecil ayunan mengikuti besar hewan, dengan ujung-ujungnya utuh.

    Jongkok saja tidak cukup. Sapuan menyikat ditulis untuk lambung sapi:
    tegak, tinggi 0,37 m. Permukaan itu memang tegak, jadi sapuan tegak benar.
    Punggung ayam tingginya 0,44 m dan mendatar — sapuan yang sama menyapu
    setengah bagian atasnya di UDARA. Terukur pada ayam: ujung sikat berayun
    antara 0,49 m (menyentuh) dan 0,86 m (0,28 m di atas ayamnya), dua kali
    tiap sapuan.

    Jongkok tidak bisa menutupnya karena sudah mentok — 0,70 m pada karakter
    1,76 m sudah jongkok penuh, lebih dari itu badannya masuk tanah.

    Jadi yang diperkecil ayunannya, bukan pusatnya: tiap kunci ditarik ke
    arah garis diam (lurus dari kunci pertama ke kunci terakhir) sebanyak
    `1 - skala`. Ujung-ujungnya tidak bergerak, jadi aksinya tetap mulai dan
    berakhir di pose diam yang sama; yang mengecil cuma ayunan di tengahnya.
    Sudut bahu yang lebih kecil berarti lengan lebih menggantung, dan lengan
    yang lebih menggantung berarti tangan lebih RENDAH — arah yang memang
    dibutuhkan hewan pendek.

    Kanal `.y` dilewati: itu satuan meter dan bentuk waktunya dipinjam
    lapisan jongkok.
    """
    if skala >= 0.995:
        return jalur
    keluar = []
    for j in jalur:
        if j.sifat == 'y':
            keluar.append(j)
            continue
        t0, v0 = j.kunci[0][0], j.kunci[0][1]
        t1, v1 = j.kunci[-1][0], j.kunci[-1][1]
        rentang_t = max(1e-6, t1 - t0)
        baru = []
        for t, v, k in j.kunci:
            diam = v0 + (v1 - v0) * ((t - t0) / rentang_t)
            baru.append((t, diam + (v - diam) * skala, k))
        keluar.append(Jalur(j.sendi, j.sifat, baru,
                            jeda_ms=j.jeda_ms, dasar=j.dasar))
    return keluar


# ─── LAPISAN JONGKOK ─────────────────────────────────────────────────────────
def _lapisan_turun(jalur: list, turun: float) -> list:
    """Tambahkan `turun` meter kedalaman jongkok di atas resep apa pun.

    Bentuk waktunya DIPINJAM dari kanal `.y` yang sudah ada di resep, jadi
    lapisan ini masuk dan keluar bersamaan dengan gerakan aslinya — tidak ada
    jongkok yang muncul sebelum tangannya bergerak atau tertinggal sesudahnya.

    Kenapa perlu: satu resep menyikat yang benar untuk sapi (punggung 1,37 m)
    akan menyapu 70 cm di atas kepala ayam (punggung 0,44 m). Resep terpisah
    per spesies berarti sembilan resep yang harus dijaga tetap sinkron; satu
    lapisan kedalaman berarti satu.
    """
    if turun <= 0.005:
        return jalur
    contoh = next((j for j in jalur if j.sifat == 'y'), None)
    if contoh is None:
        return jalur
    puncak = min(v for _t, v, _k in contoh.kunci) or -1.0
    bentuk = [(t, v / puncak, k) for t, v, k in contoh.kunci]      # 0..1

    tambahan = []
    for sendi in ('badan', 'bahu_r', 'bahu_l', 'leher'):
        tambahan.append(Jalur(sendi, 'y',
                              [(t, -turun * u, k) for t, u, k in bentuk],
                              jeda_ms=contoh.jeda_ms))
    # Lutut dan pinggul ikut menekuk. Tanpa ini badan turun sementara kaki
    # tetap lurus — yang terlihat bukan jongkok, tapi tenggelam ke tanah.
    for sendi, kali in (('lutut_r', 118.0), ('lutut_l', 118.0),
                        ('pinggul_r', -52.0), ('pinggul_l', -52.0)):
        tambahan.append(Jalur(sendi, 'rotation_x',
                              [(t, turun * kali * u, k) for t, u, k in bentuk],
                              jeda_ms=contoh.jeda_ms + 20))
    tambahan.append(Jalur('badan', 'rotation_x',
                          [(t, turun * 26.0 * u, k) for t, u, k in bentuk],
                          jeda_ms=contoh.jeda_ms + 40))
    return jalur + tambahan


# ─── PABRIK ──────────────────────────────────────────────────────────────────
def mulai(player, jenis: str, titik_tuang=None, pemicu=None,
          saat_frame=None, saat_usai=None, turun: float = 0.0,
          skala: float = 1.0) -> AksiRawat | None:
    """Pasang aksi perawatan `jenis` ke `player`. Return aksinya, atau None.

    Aksi yang sedang berjalan DIBATALKAN dulu, bukan ditumpuk: dua pose yang
    saling menulis di frame yang sama menghasilkan kedutan, bukan dua gerakan.
    """
    resep = RESEP.get(jenis)
    if resep is None:
        return None

    lama = getattr(player, '_care_anim', None)
    if lama is not None and not lama.selesai:
        lama.usai(player)
    _lepas_properti(player)

    # Urutannya penting: ayunan diperkecil DULU, jongkok ditambahkan sesudahnya.
    # Terbalik, jongkoknya ikut diperkecil dan hewan pendek malah kurang
    # ditunduki — persis kebalikan dari yang dibutuhkan.
    jalur = _lapisan_turun(_lapisan_skala(resep['jalur'](), skala), turun)
    aksi = AksiRawat(jenis, resep['fase'], jalur,
                     pemicu=pemicu, saat_frame=saat_frame, saat_usai=saat_usai)

    # Alat HUD disembunyikan untuk SETIAP aksi perawatan, bukan hanya yang
    # punya properti sendiri. Tanpa ini pemain memberi isyarat sambil
    # mengacungkan cangkul saat bercakap-cakap, dan merogoh sarang ayam
    # dengan kapak masih tergenggam.
    if not resep.get('alat_hud'):
        _sembunyikan_alat_hud(player)
        alat = resep.get('alat')
        if alat:
            _pasang_properti(player, alat)
    aksi.mulai(player)
    aksi.terapkan(player)
    player._care_anim = aksi
    return aksi


def _sembunyikan_alat_hud(player) -> None:
    alat_hud = getattr(player, '_held_tool', None)
    if alat_hud is not None:
        alat_hud.enabled = False


def _kembalikan_alat_hud(player) -> None:
    alat_hud = getattr(player, '_held_tool', None)
    if alat_hud is not None:
        alat_hud.enabled = True


def _pasang_properti(player, kind: str) -> None:
    """Taruh benda kerja di tangan kanan.

    Alat HUD (cangkul/sabit) sudah disembunyikan oleh mulai(); tanpa itu
    pemain akan terlihat menuang air dari sebuah cangkul.
    """
    from ursina import Vec3
    try:
        from .tool_models import build_tool
        induk = getattr(player, '_pivot_elbow_r', None) or \
            getattr(player, '_pivot_shoulder_r', None) or player
        prop = build_tool(kind, parent=induk)
        if prop is not None:
            prop.position = Vec3(0.015, -0.335, 0.055)
            prop.rotation = Vec3(0, 0, 0)
        player._care_prop = prop
    except Exception:
        import logging
        logging.warning(f'[RAWAT] gagal membangun properti {kind!r}', exc_info=True)
        player._care_prop = None


def pasang_hasil(player) -> None:
    """Munculkan wadah hasil di tangan KIRI, di akhir aksi panen.

    Barang yang muncul di inventori tanpa pernah melewati layar adalah alasan
    utama "ambil hasil" terasa seperti mengklik tombol. Wadah ini hidup selama
    sisa animasi saja — cukup untuk mata melihat hasilnya berpindah tangan.
    """
    from ursina import Vec3
    lepas_hasil(player)
    try:
        from .tool_models import build_tool
        induk = getattr(player, '_pivot_elbow_l', None) or \
            getattr(player, '_pivot_shoulder_l', None) or player
        h = build_tool('hasil', parent=induk)
        if h is not None:
            h.position = Vec3(-0.015, -0.330, 0.050)
        player._care_hasil = h
    except Exception:
        import logging
        logging.warning('[RAWAT] gagal membangun wadah hasil', exc_info=True)
        player._care_hasil = None


def lepas_hasil(player) -> None:
    from ursina import destroy
    h = getattr(player, '_care_hasil', None)
    if h is not None:
        try:
            destroy(h)
        except Exception:
            pass
    player._care_hasil = None


def _lepas_properti(player) -> None:
    from ursina import destroy
    lepas_hasil(player)
    prop = getattr(player, '_care_prop', None)
    if prop is not None:
        try:
            destroy(prop)
        except Exception:
            pass
    player._care_prop = None
    _kembalikan_alat_hud(player)


def bereskan(player) -> None:
    """Akhiri aksi yang sedang berjalan dan kembalikan rig ke pose diam."""
    aksi = getattr(player, '_care_anim', None)
    if aksi is not None:
        aksi.usai(player)
    player._care_anim = None
    _lepas_properti(player)


# ─── ALIRAN AIR ──────────────────────────────────────────────────────────────
class AliranAir:
    """Kolom air tipis dari mulut ember ke permukaan palung.

    Partikel saja tidak cukup: di filmstrip 30 fps butiran terbaca sebagai noda,
    sedangkan kolom yang menyambungkan ember ke palung langsung menjelaskan apa
    yang sedang terjadi bahkan di satu frame diam.
    """

    def __init__(self, tujuan):
        from ursina import Entity, color
        self.tujuan = tujuan
        self._e = Entity(model='cube', color=color.rgba(126, 188, 214, 190),
                         scale=(0.055, 0.055, 0.1), enabled=False,
                         double_sided=True, unlit=True, transparent=True)
        self.aktif = False

    def nyala(self, on: bool) -> None:
        self.aktif = on
        if self._e:
            self._e.enabled = on

    def perbarui(self, asal) -> None:
        if not self.aktif or self._e is None or asal is None:
            return
        from ursina import Vec3
        a = Vec3(*asal)
        b = Vec3(*self.tujuan)
        tengah = (a + b) * 0.5
        d = (b - a).length()
        self._e.position = tengah
        self._e.look_at(b)
        self._e.scale = (0.055, 0.055, max(0.05, d))

    def hapus(self) -> None:
        from ursina import destroy
        if self._e is not None:
            try:
                destroy(self._e)
            except Exception:
                pass
            self._e = None
