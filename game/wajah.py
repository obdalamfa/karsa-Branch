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
    out, mata, kilau, pipi = [], [], [], []
    from .meshes import permukaan

    def kedalaman(x, y, maju):
        """Kedalaman satu fitur, MENGIKUTI lengkung kepala.

        Versi pertama mengembalikan `muka_z + maju` — satu bidang datar untuk
        semua fitur. Itu benar selama kepala hampir kubus: pada eksponen 0,10
        permukaannya memang datar sempurna sampai ~0,8 setengah-lebar. Begitu
        bentuknya dibuat melengkung, bidang datar itu berbohong makin jauh ke
        arah sudut — terukur, pada eksponen 0,60 mulut melayang 11% dan rona
        pipi 8% setengah-lebar di depan muka.
        """
        return muka_z * permukaan(abs(x) / max(hw, 1e-6),
                                  abs(y) / max(ht, 1e-6)) + maju
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
        e = _kotak(induk, (px, py, kedalaman(px, py, -hw * 0.023)),
                   (hw * 0.30, ht * 0.12, hw * 0.046),
                   color.rgb(*PIPI_WARNA))
        pipi.append(e); out.append(e)
    return Wajah(mata, kilau, mulut, out, pipi=pipi)


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

    # Dua keadaan yang harus terbaca dari MATANYA, dan sengaja dibuat berbeda
    # ke dua arah supaya tidak bisa tertukar: sakit = kelopak berat DAN
    # kedipan yang melambat; senang = mata menyipit rapat dengan kedipan
    # normal. Kalau keduanya cuma "mata lebih pendek", pemain tidak bisa
    # membedakan hewan yang bahagia dari hewan yang mau roboh.
    SAKIT_BUKA  = 0.62
    SAKIT_JEDA  = 2.2      # pengali jarak antar-kedipan
    SENANG_BUKA = 0.38

    # ── kehangatan: seberapa dekat warga ini dengan pemain ──────────────
    # `npc_hearts` 0-10 sudah menggerakkan cabang dialog, hadiah dan gerbang
    # aksi — tapi wajah warga tidak pernah menunjukkannya. Warga yang baru
    # dikenal dan warga yang sudah 10 hati menatap pemain dengan rupa yang
    # sama persis. Tandanya sengaja dibuat HALUS: rona pipi melebar dan mata
    # melembut sedikit. Senyum lebar permanen terbaca sebagai topeng.
    HATI_PIPI   = 1.42     # lebar rona pipi pada 10 hati
    HATI_MATA   = 0.93     # mata melembut sedikit, bukan menyipit

    # ── mulut saat bicara ───────────────────────────────────────────────
    # Sebelum ini mulut tiap karakter TIDAK PERNAH bergerak — terukur, rentang
    # scale_y-nya 0,00000 sepanjang percakapan 20 detik. Salah satu dari tiga
    # animasi yang diminta brief ini bernama "berbicara", dan mulutnya diam.
    #
    # Yang dihindari: mulut yang membuka-menutup satu sinus. Bicara manusia
    # bukan getaran berperiode tetap — ia deret SUKU KATA yang panjangnya
    # berbeda-beda, dikelompokkan jadi frasa, dengan jeda di antaranya.
    # Sinus murni akan punya simpangan baku jarak nol, cacat metronom yang
    # sama yang sudah dua kali ditutup di proyek ini (kedipan §7, ekor §9).
    SUKU_MIN     = 0.115   # detik, suku kata tercepat
    SUKU_MAKS    = 0.235   # detik, suku kata terlambat  (~4-9 suku/detik)
    SUKU_BUKA    = 3.1     # kelipatan tinggi mulut diam saat terbuka penuh
    SUKU_LEBAR   = 1.18    # mulut ikut melebar sedikit, tidak cuma menganga
    FRASA_MIN    = 4       # suku kata per frasa
    FRASA_MAKS   = 9
    FRASA_JEDA_MIN = 0.22  # detik diam di antara frasa — tempat orang menarik
    FRASA_JEDA_MAKS = 0.58 # napas; tanpa ini bicaranya terbaca sebagai dengung
    MULUT_PULANG_MS = 90.0 # mulut kembali diam sesudah berhenti bicara

    def __init__(self, mata, kilau, mulut, semua, pipi=None):
        self.mata, self.kilau, self.mulut, self.semua = mata, kilau, mulut, semua
        self.pipi = list(pipi or [])
        self._pipi0 = []
        for e in self.pipi:
            try:
                self._pipi0.append((float(e.scale_x), float(e.scale_y)))
            except Exception:
                self._pipi0.append((1.0, 1.0))
        self._hati = 0.0
        self._tinggi0 = [float(e.scale_y) for e in mata]
        self._t = 0.0
        self._jeda = self.JEDA_MIN
        self._kedip_t = None
        self._lelah = 0.0
        self._tidur = False
        self._sakit = False
        self._senang = 0.0
        self._n = 0                 # nomor kedipan, umpan derau
        self._bicara = False
        self._suku_n = 0            # nomor suku kata, umpan derau
        self._suku_t = 0.0
        self._suku_lama = self.SUKU_MIN
        self._suku_tinggi = 1.0
        self._sisa_frasa = 0
        self._jeda_t = 0.0
        self._buka_mulut = 0.0      # 0 = diam, 1 = terbuka penuh
        self._mulut0 = None
        if mulut is not None:
            try:
                self._mulut0 = (float(mulut.scale_x), float(mulut.scale_y))
            except Exception:
                self._mulut0 = None

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

    def set_bicara(self, aktif: bool) -> None:
        """Nyalakan/matikan mulut bicara.

        Di tepi naiknya frasa dimulai dari awal: tiap baris dialog baru adalah
        ucapan baru, dan ucapan yang dimulai di tengah frasa sebelumnya
        terbaca sebagai potongan.
        """
        aktif = bool(aktif)
        if aktif and not self._bicara:
            self._suku_t = 0.0
            self._jeda_t = 0.0
            self._sisa_frasa = 0
            self._suku_lama = self.SUKU_MIN
        self._bicara = aktif

    def _suku_berikut(self) -> None:
        """Panjang dan bukaan suku kata berikutnya — berbeda-beda, tidak acak.

        Umpannya NOMOR suku kata, bukan waktu: jebakan umpan-waktu sudah sekali
        meloloskan kedipan metronom di modul ini sendiri.
        """
        self._suku_n += 1
        b = getattr(self, '_benih', 0)
        u = derau(self._suku_n, b)
        self._suku_lama = self.SUKU_MIN + u * (self.SUKU_MAKS - self.SUKU_MIN)
        # Bukaan tiap suku kata berbeda: deret suku kata yang sama tingginya
        # terbaca sebagai rahang berengsel, bukan orang berbicara.
        self._suku_tinggi = 0.42 + derau(self._suku_n, b + 517) * 0.58
        self._suku_t = 0.0
        if self._sisa_frasa <= 0:
            n = derau(self._suku_n, b + 823)
            self._sisa_frasa = int(self.FRASA_MIN
                                   + n * (self.FRASA_MAKS - self.FRASA_MIN))
        self._sisa_frasa -= 1

    def _tick_mulut(self, dt: float) -> None:
        if self.mulut is None or self._mulut0 is None:
            return
        if not self._bicara:
            # Pulang ke diam, tidak memotong: mulut yang menutup dalam satu
            # frame di akhir kalimat terbaca sebagai gambar yang diganti.
            self._buka_mulut = max(
                0.0, self._buka_mulut - dt * 1000.0 / self.MULUT_PULANG_MS)
        elif self._jeda_t > 0.0:
            self._jeda_t = max(0.0, self._jeda_t - dt)
            self._buka_mulut = max(0.0, self._buka_mulut - dt * 6.0)
        else:
            self._suku_t += dt
            if self._suku_t >= self._suku_lama:
                if self._sisa_frasa <= 0:
                    j = derau(self._suku_n, getattr(self, '_benih', 0) + 311)
                    self._jeda_t = (self.FRASA_JEDA_MIN
                                    + j * (self.FRASA_JEDA_MAKS
                                           - self.FRASA_JEDA_MIN))
                self._suku_berikut()
            v = self._suku_t / max(1e-6, self._suku_lama)
            # Kosinus terangkat: tertutup -> terbuka -> tertutup tanpa sudut
            # tajam di kedua ujungnya.
            self._buka_mulut = self._suku_tinggi * (
                0.5 - 0.5 * math.cos(math.tau * v))
        x0, y0 = self._mulut0
        b = self._buka_mulut
        try:
            self.mulut.scale_y = y0 * (1.0 + (self.SUKU_BUKA - 1.0) * b)
            self.mulut.scale_x = x0 * (1.0 + (self.SUKU_LEBAR - 1.0) * b)
        except Exception:
            pass

    def set_hati(self, tingkat: float) -> None:
        """0 = baru kenal, 1 = 10 hati. Kehangatan, bukan kegembiraan."""
        self._hati = max(0.0, min(1.0, float(tingkat)))

    def _tick_pipi(self) -> None:
        if not self.pipi:
            return
        k = 1.0 + (self.HATI_PIPI - 1.0) * self._hati
        for e, (x0, y0) in zip(self.pipi, self._pipi0):
            try:
                e.scale_x = x0 * k
                e.scale_y = y0 * (1.0 + (k - 1.0) * 0.55)
            except Exception:
                pass

    def set_keadaan(self, sakit: bool = False, senang: float = 0.0) -> None:
        """Keadaan yang terbaca dari mata. `senang` 0..1 dan meluruh sendiri."""
        self._sakit = bool(sakit)
        self._senang = max(0.0, min(1.0, float(senang)))

    def set_tidur(self, tidur: bool) -> None:
        """Mata terpejam penuh selama yang punya sedang tidur.

        Dipakai hewan ternak, yang memang tidur di kandang tiap malam dan
        sebelum ini tetap membelalak sepanjang malam. Beda dari `set_lelah`:
        lelah MENYIPIT (0,55 terbuka), tidur MENUTUP.
        """
        self._tidur = bool(tidur)

    def tick(self, dt: float) -> None:
        self._tick_pipi()
        self._tick_mulut(dt)
        self._t += dt
        if self._kedip_t is None:
            # Hewan sakit berkedip lebih jarang — kelopak yang berat bergerak
            # lebih malas, dan itu tanda kedua yang memisahkannya dari senang.
            jeda = self._jeda * (self.SAKIT_JEDA if self._sakit else 1.0)
            if self._t >= jeda:
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
        if getattr(self, '_sakit', False):
            buka *= self.SAKIT_BUKA
        elif getattr(self, '_senang', 0.0) > 0.0:
            buka *= 1.0 - (1.0 - self.SENANG_BUKA) * self._senang
        else:
            buka *= 1.0 - (1.0 - self.HATI_MATA) * getattr(self, '_hati', 0.0)
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
