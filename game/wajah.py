"""wajah.py — Wajah dan rambut, satu bahasa rupa untuk pemain dan NPC.

Sebelum modul ini, kepala pemain adalah kotak kulit polos dan NPC adalah
manekin `humanoid.obj` PUTIH MURNI (Color 1,1,1,1) setinggi 3,42 unit —
1,45 kali pemain — tanpa wajah, tanpa rambut, tanpa baju. Diukur, bukan
dikira: lihat catatan di docs.

Bahasa rupa yang diikuti datang dari game kehidupan Jepang (Story of Seasons,
Rune Factory, Harvest Moon), dan urutannya penting karena tiap langkah
menyelesaikan masalah yang berbeda:

  1. RAMBUT DULU. Poni yang menjorok di atas dahi adalah satu hal yang paling
     cepat mengubah kepala polos jadi karakter, dan ia sekaligus memberi
     kepala ARAH DEPAN yang terbaca dari jauh. Tanpa rambut, kepala dari depan
     dan dari belakang sama saja.
  2. MATA adalah fiturnya, bukan salah satu fitur. Besar, gelap, bentuk
     sederhana, duduk sedikit DI BAWAH garis tengah wajah — mata yang
     diletakkan tepat di tengah membuat wajah terbaca dewasa dan dingin.
     Besarnya sekitar sepertiga tinggi wajah yang terlihat: percobaan pertama
     memakai hampir setengahnya dan hasilnya terbaca sebagai kacamata hitam.
  3. KILAU. Mata anime tidak pernah hitam rata. Satu titik putih kecil di
     sudut yang SAMA pada kedua mata (cahaya datang dari satu arah) adalah
     beda antara "melihat" dan "melotot". Kilau simetris cermin terbaca
     sebagai dua bola mata, bukan wajah.
  4. MULUT sekecil mungkin, dan warnanya diredam. Pada kotak sekecil ini,
     merah menyala terbaca sebagai luka.
  5. Rona pipi. Murah, dan ia yang membuat kulit terbaca hidup.

Semua ukuran diberikan sebagai PECAHAN dari setengah-lebar kepala, jadi satu
resep yang sama pas di kepala pemain (setengah-lebar 0,175) maupun di kepala
manekin NPC (0,36) tanpa dua tabel angka yang harus dijaga sinkron.
"""
import math

from ursina import Entity, Vec3, color


MATA_WARNA  = (46, 36, 42)
# Mulut sengaja diredam: merah menyala pada bidang sekecil ini terbaca sebagai
# luka, bukan mulut.
MULUT_WARNA = (168, 108, 100)
PIPI_WARNA  = (243, 176, 172)


def derau(n: int, benih: int) -> float:
    """Derau 0..1 yang deterministik tapi tidak berirama, diumpani NOMOR.

    Diambil ke sini karena dipakai dua tempat (kedipan wajah dan kedutan
    telinga ternak) dan karena cara memanggilnya yang salah sudah sekali
    meloloskan metronom: versi pertama `Wajah._acak_jeda` mengumpaninya dengan
    `self._t`, yang di-nol-kan TEPAT SEBELUM pemanggilan, jadi deraunya selalu
    dievaluasi di sin(0) = 0 dan jaraknya selalu sama. Umpannya harus sesuatu
    yang memang berubah tiap kali — nomor kejadian — dan tanda tangan fungsi
    ini memaksanya.
    """
    return abs((math.sin((n + benih) * 12.9898) * 43758.5453) % 1.0)


def _kotak(induk, pos, skala, warna):
    e = Entity(model='cube', position=Vec3(*pos), scale=skala,
               color=warna, parent=induk)
    from .smooth_shader import apply_smooth
    apply_smooth(e, has_texture=False)
    return e


def bangun_rambut(induk, hw: float, ht: float, warna, maju: float = 0.0):
    """Batok, poni, tuft sisi dan belakang kepala. Return daftar entity.

    `hw` setengah-lebar kepala, `ht` setengah-tinggi kepala, keduanya dalam
    satuan induk. `maju` menggeser seluruh rambut ke depan (dipakai saat
    kepala di bawahnya bukan kotak, melainkan bola yang lebih ramping).
    """
    out = []
    def r(pos, skala):
        out.append(_kotak(induk, pos, skala, warna))
    # Poni sengaja menonjol lebih maju daripada bidang muka supaya ia
    # MENGGANTUNG di atas dahi, bukan menempel rata seperti stiker.
    out_hw = hw * 1.06
    r((0.0,  ht * 0.67, -hw * 0.07 + maju), (out_hw * 2, ht * 0.85, out_hw * 2))
    r((0.0,  ht * 0.35,  hw * 0.86 + maju), (out_hw * 2, ht * 0.56, hw * 0.55))
    r((-hw * 1.03, ht * 0.04, -hw * 0.06 + maju), (hw * 0.28, ht * 1.33, hw * 1.97))
    r(( hw * 1.03, ht * 0.04, -hw * 0.06 + maju), (hw * 0.28, ht * 1.33, hw * 1.97))
    r((0.0, -ht * 0.09, -hw * 1.05 + maju), (hw * 1.94, ht * 1.47, hw * 0.29))
    return out


def bangun_wajah(induk, hw: float, ht: float, muka_z: float):
    """Mata, kilau, mulut dan rona pipi pada bidang muka.

    `muka_z` adalah jarak bidang muka dari pusat kepala, dalam satuan induk.
    Semua fitur ditempel sedikit di depannya supaya tidak berkedip melawan
    permukaan kepala (z-fighting).

    Pemain DAN NPC sama-sama berkepala kotak-membulat (`chibi_head_mesh`),
    jadi satu bidang muka datar cukup untuk keduanya. Varian bola sempat ada
    untuk kepala manekin NPC — lengkap dengan perhitungan kedalaman per fitur
    dari persamaan bola, karena di bidang datar rona pipi di x = 0,71R
    melayang lepas dari permukaan dan menjulur seperti dua batang merah muda.
    Varian itu dibuang begitu kepala NPC ikut memakai bentuk yang sama:
    bola Ursina bersegi rendah, dan cel-shader di sini memotong terang-gelap
    pada ambang keras, jadi batas bayangannya membentuk tangga yang terlihat
    di pipi dari jarak dekat.
    """
    out, mata, kilau = [], [], []

    def kedalaman(x, y, maju):
        return muka_z + maju
    for sx in (-1, 1):
        x, y = sx * hw * 0.41, -ht * 0.26
        e = _kotak(induk, (x, y, kedalaman(x, y, 0.0)),
                   (hw * 0.34, ht * 0.28, hw * 0.08), color.rgb(*MATA_WARNA))
        mata.append(e); out.append(e)
        # Kilau di sudut yang SAMA pada kedua mata: satu arah cahaya.
        kx, ky = x - hw * 0.09, -ht * 0.19
        k = _kotak(induk, (kx, ky, kedalaman(kx, ky, hw * 0.046)),
                   (hw * 0.10, ht * 0.08, hw * 0.046), color.rgb(255, 255, 255))
        kilau.append(k); out.append(k)
    my = -ht * 0.71
    mulut = _kotak(induk, (0.0, my, kedalaman(0.0, my, 0.0)),
                   (hw * 0.22, ht * 0.07, hw * 0.069), color.rgb(*MULUT_WARNA))
    out.append(mulut)
    for sx in (-1, 1):
        # 0,60 bukan 0,71: pada kepala yang dibingkai rambut di kedua sisi,
        # 0,71 mendarat tepat di batas rambut dan separuh rona menggantung
        # keluar dari pipi.
        px, py = sx * hw * 0.60, -ht * 0.50
        out.append(_kotak(induk, (px, py, kedalaman(px, py, -hw * 0.023)),
                          (hw * 0.30, ht * 0.12, hw * 0.046),
                          color.rgb(*PIPI_WARNA)))
    return Wajah(mata, kilau, mulut, out)


class Wajah:
    """Pengendali wajah: kedipan, dan mata lelah.

    Wajah yang TIDAK PERNAH BERKEDIP adalah salah satu tanda uncanny yang
    paling tua dan paling murah dihilangkan — dan ia tersisa persis setelah
    karakter di sini akhirnya punya mata. Mata dan kilau sudah entity
    terpisah sejak awal, jadi kedipan cuma soal menyekakan tingginya.

    Tiga hal yang membuat kedipan terbaca sebagai kedipan, bukan kedutan:

      * CEPAT. Mata manusia menutup-membuka dalam 100-150 ms. Kedipan yang
        lebih lambat terbaca sebagai mengantuk, bukan berkedip.
      * TIDAK BERIRAMA. Jarak antar-kedip diacak 2,4-5,8 detik. Kedipan
        berjarak tetap adalah metronom, dan metronom terbaca sebagai mesin —
        cacat yang sama persis dengan `irama_sd_ms = 0` pada animasi aksi.
      * KILAU IKUT HILANG. Kilau yang tetap melayang saat mata tertutup
        terbaca sebagai dua titik putih di atas kelopak.

    Fase awalnya diambil dari `sum(ord(id))`, BUKAN `hash()` — Python mengacak
    hash string tiap proses, dan jebakan itu sudah dua kali memakan proyek ini
    (entities.py:262, lalu fase anggukan NPC dan napas hewan). Tanpa fase
    per-karakter, semua orang di layar berkedip serempak seperti pasukan.
    """

    TUTUP_MS   = 60.0      # menutup
    TAHAN_MS   = 25.0      # tertutup penuh
    BUKA_MS    = 75.0      # membuka, sedikit lebih lambat daripada menutup
    JEDA_MIN   = 2.4
    JEDA_MAKS  = 5.8
    LELAH_BUKA = 0.55      # tinggi mata saat energi habis

    def __init__(self, mata, kilau, mulut, semua):
        self.mata, self.kilau, self.mulut, self.semua = mata, kilau, mulut, semua
        self._tinggi0 = [float(e.scale_y) for e in mata]
        self._t = 0.0
        self._jeda = self.JEDA_MIN
        self._kedip_t = None
        self._lelah = 0.0
        self._tidur = False
        self._n = 0                 # nomor kedipan, umpan derau

    def fase_awal(self, kunci: str) -> None:
        """Sebar fase dari id karakter supaya tidak berkedip serempak."""
        self._benih = sum(map(ord, kunci)) % 997
        u = self._benih / 997.0
        self._t = u * self.JEDA_MAKS
        self._acak_jeda()

    def _acak_jeda(self) -> None:
        """Jarak ke kedipan berikutnya: deterministik, tapi tidak berirama.

        Versi pertama memakai `sin(self._t * 12,9898)` — dan `self._t` di-nol-kan
        TEPAT SEBELUM fungsi ini dipanggil, jadi deraunya selalu dievaluasi di
        sin(0) = 0 dan jaraknya selalu JEDA_MIN. Terukur: 12 kedipan dalam 30
        detik, semuanya berjarak 2,40 detik, simpangan baku 0,00 — metronom,
        yaitu persis cacat yang tabel ambang proyek ini sendiri sebut mesin.
        Umpannya sekarang NOMOR kedipan, yang memang berubah tiap kali.
        """
        self._n += 1
        u = derau(self._n, getattr(self, '_benih', 0))
        self._jeda = self.JEDA_MIN + u * (self.JEDA_MAKS - self.JEDA_MIN)

    def set_lelah(self, lelah: float) -> None:
        """0 = segar, 1 = habis. Mata menyipit, tidak menutup."""
        self._lelah = max(0.0, min(1.0, float(lelah)))

    def set_tidur(self, tidur: bool) -> None:
        """Mata terpejam penuh selama yang punya sedang tidur.

        Dipakai hewan ternak, yang memang tidur di kandang tiap malam dan
        sebelum ini tetap membelalak sepanjang malam. Beda dari `set_lelah`:
        lelah MENYIPIT (0,55 terbuka), tidur MENUTUP.
        """
        self._tidur = bool(tidur)

    def tick(self, dt: float) -> None:
        self._t += dt
        if self._kedip_t is None:
            if self._t >= self._jeda:
                self._kedip_t = 0.0
                self._t = 0.0
                self._acak_jeda()
        else:
            self._kedip_t += dt
            ms = self._kedip_t * 1000.0
            total = self.TUTUP_MS + self.TAHAN_MS + self.BUKA_MS
            if ms >= total:
                self._kedip_t = None
        # Bagian mata yang terbuka: 1 = penuh, 0 = tertutup.
        buka = 1.0
        if self._kedip_t is not None:
            ms = self._kedip_t * 1000.0
            if ms < self.TUTUP_MS:
                buka = 1.0 - ms / self.TUTUP_MS
            elif ms < self.TUTUP_MS + self.TAHAN_MS:
                buka = 0.0
            else:
                buka = (ms - self.TUTUP_MS - self.TAHAN_MS) / self.BUKA_MS
        buka *= 1.0 - (1.0 - self.LELAH_BUKA) * self._lelah
        if getattr(self, '_tidur', False):
            buka = 0.0
        for e, h0 in zip(self.mata, self._tinggi0):
            try:
                e.scale_y = max(0.02, h0 * buka)
            except Exception:
                pass
        for k in self.kilau:
            try:
                k.enabled = buka > 0.45
            except Exception:
                pass


def warna_rambut(state, indeks_default: int = 0):
    from .chargen import HAIR_PRESETS
    i = getattr(state, 'char_hair', indeks_default) or indeks_default
    rgb = HAIR_PRESETS[i][1] if i < len(HAIR_PRESETS) else HAIR_PRESETS[0][1]
    return color.rgb(*rgb)
