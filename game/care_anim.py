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
        player.tick(), supaya aksi perawatan menang atas lerp-ke-nol idle."""
        t_ms = self.t * 1000.0
        keluar_u = None
        if self._batal_t is not None:
            keluar_u = min(1.0, self._batal_t * 1000.0 / self._KELUAR_MS)

        for j in self._jalur:
            ent = self._entitas(player, j.sendi)
            if ent is None:
                continue
            if keluar_u is None:
                nilai = j.nilai_pada(t_ms)
            else:
                asal = self._batal_dari.get(id(j), j._dasar_nilai)
                nilai = asal + (j._dasar_nilai - asal) * _keluar(keluar_u)
            try:
                setattr(ent, j.sifat, nilai)
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


RESEP = {
    'minum': {'fase': _FASE_MINUM, 'jalur': _resep_minum,
              'alat': 'ember', 'aliran': True},
    'gosok': {'fase': _FASE_GOSOK, 'jalur': _resep_gosok,
              'alat': 'sikat', 'aliran': False},
}


# ─── PABRIK ──────────────────────────────────────────────────────────────────
def mulai(player, jenis: str, titik_tuang=None, pemicu=None,
          saat_frame=None, saat_usai=None) -> AksiRawat | None:
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

    aksi = AksiRawat(jenis, resep['fase'], resep['jalur'](),
                     pemicu=pemicu, saat_frame=saat_frame, saat_usai=saat_usai)

    alat = resep.get('alat')
    if alat:
        _pasang_properti(player, alat)
    aksi.mulai(player)
    aksi.terapkan(player)
    player._care_anim = aksi
    return aksi


def _pasang_properti(player, kind: str) -> None:
    """Taruh benda kerja di tangan kanan, dan sembunyikan alat yang digenggam.

    Alat HUD (cangkul/sabit) tetap ada di tangan kalau tidak disembunyikan, jadi
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

    alat_hud = getattr(player, '_held_tool', None)
    if alat_hud is not None:
        alat_hud.enabled = False


def _lepas_properti(player) -> None:
    from ursina import destroy
    prop = getattr(player, '_care_prop', None)
    if prop is not None:
        try:
            destroy(prop)
        except Exception:
            pass
    player._care_prop = None
    alat_hud = getattr(player, '_held_tool', None)
    if alat_hud is not None:
        alat_hud.enabled = True


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
