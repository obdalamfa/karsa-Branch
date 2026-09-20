"""gerak_ternak.py — Telinga berkedut dan ekor mengibas.

Ini menutup sisa terakhir daftar "yang masih terbuka" di RUPA_KARAKTER.md §6:
ternak sudah bermata dan ikut berkedip, tapi telinga dan ekornya masih kaku.
Yang membuatnya lebih dari kosmetik: seluruh brief proyek ini adalah INTERAKSI
perawatan ternak, dan hewan yang disikat selama 2,7 detik tanpa menggerakkan
telinga maupun ekor tidak memberi satu pun tanda bahwa ia merasakan sikatnya.
Badannya memang sudah condong ke arah sikat (`FarmAnimal._tick_sikat`), tapi
itu satu gerakan untuk satu benda utuh — bukan reaksi.

Tiga hal yang membuat gerak ini terbaca sebagai hidup, bukan sebagai motor:

  * EKOR TIDAK BOLEH BERAYUN SATU SINUS. Satu sinus murni punya jarak
    antar-lintasan-nol yang SAMA PERSIS tiap kali, dan itu simpangan baku nol —
    cacat "metronom" yang tabel ambang proyek ini sendiri sebut mesin, dan yang
    sudah sekali memakan kedipan wajah. Jadi ayunannya dua sinus berperiode
    tidak sepadan (0,61x), yang membuat jaraknya berubah-ubah tanpa acak.
  * TELINGA BERKEDUT, BUKAN BERAYUN. Telinga yang berayun terus-menerus
    terbaca sebagai kipas. Yang benar: diam lama, lalu SATU sentakan cepat
    (70 ms keluar, 190 ms pulang) di jarak yang tidak berirama.
  * MENYENTUH HARUS TERBACA. Tiap sapuan sikat memicu sentakan telinga dan
    melebarkan ayunan ekor 3x. Inilah bagian yang benar-benar menjawab brief:
    pemain harus bisa melihat hewannya bereaksi terhadap tangannya.

Malam hari ekor melambat dan menyempit, telinga berhenti berkedut sama sekali —
hewan tidur tidak mengibas-ngibas.
"""
import math

from .wajah import derau


class GerakTernak:
    """Pengendali telinga dan ekor satu ekor ternak."""

    EKOR_DIAM_DERAJAT  = 5.5      # amplitudo saat hewan cuma berdiri
    EKOR_DIAM_PERIODE  = 4.6
    EKOR_RAWAT_DERAJAT = 17.0     # saat sedang disikat / dibelai
    EKOR_RAWAT_PERIODE = 1.35
    # Sinus kedua sengaja TIDAK sepadan dengan yang pertama. 0,61 dipilih dekat
    # 1/golden ratio: makin jauh dari pecahan sederhana, makin lama polanya
    # berulang, dan makin tidak berirama jarak antar-lintasan-nolnya.
    EKOR_SINUS2        = 0.61
    EKOR_BOBOT2        = 0.42
    EKOR_TEGAK         = 0.35     # bagian ayunan yang jadi gerak maju-mundur
    EKOR_LERP          = 3.2      # kecepatan amplitudo menyusul keadaan baru

    TELINGA_JEDA_MIN   = 2.8
    TELINGA_JEDA_MAKS  = 8.5
    TELINGA_DERAJAT    = 26.0
    TELINGA_KELUAR_MS  = 70.0
    TELINGA_PULANG_MS  = 190.0

    TIDUR_REDAM        = 0.22
    TIDUR_LAMBAT       = 1.8
    TIDUR_TELINGA      = -15.0    # telinga mengendur selama tidur

    # ── keadaan yang harus TERLIHAT pada hewannya ───────────────────────
    # husbandry.py membuka dengan kalimatnya sendiri: "Aturan yang tidak bisa
    # dilihat pemain bukan aturan." Ia lalu memberi tiap hewan takaran kenyang,
    # air, bersih, hitungan lalai dan jalur sakit — dan seluruhnya cuma muncul
    # sebagai TEKS di panel. Sapi sakit dan sapi yang baru disikat terlihat
    # sama persis. Dua keadaan itu sekarang terbaca dari telinga dan ekornya,
    # dan sengaja dibuat BERLAWANAN arah supaya tidak bisa tertukar.
    SAKIT_TELINGA      = -30.0    # telinga layu ke bawah
    SAKIT_EKOR_REDAM   = 0.38
    SAKIT_EKOR_LAMBAT  = 1.55
    SENANG_TELINGA     = 15.0     # telinga tegak
    SENANG_EKOR_LEBAR  = 1.55
    SENANG_EKOR_CEPAT  = 0.72
    KEADAAN_LERP       = 2.6      # telinga layu/tegak menyusul pelan

    def __init__(self, telinga, ekor, kunci: str):
        self.telinga, self.ekor = list(telinga), list(ekor)
        # sum(ord) — BUKAN hash(), yang diacak ulang tiap proses Python. Jebakan
        # yang sama sudah tiga kali memakan proyek ini (entities.py:262, fase
        # napas hewan, fase kedipan wajah). Tanpa fase per-ekor, sekandang
        # mengibaskan ekor serempak dan terbaca sebagai satu benda.
        self._benih = sum(map(ord, kunci or 'ternak')) % 997
        u = self._benih / 997.0
        self._t = u * self.EKOR_DIAM_PERIODE
        self._amp = self.EKOR_DIAM_DERAJAT
        self._periode = self.EKOR_DIAM_PERIODE
        # Tiap telinga punya jam sendiri: dua telinga yang berkedut berbarengan
        # terbaca sebagai satu engsel, bukan dua telinga.
        self._sakit = False
        self._senang = 0.0
        self._telinga_geser = 0.0   # sudut tetap telinga (layu/tegak) saat ini
        self._kedut = []
        for i, _ in enumerate(self.telinga):
            self._kedut.append({'t': u * self.TELINGA_JEDA_MAKS + i * 1.7,
                                'jeda': self.TELINGA_JEDA_MIN, 'n': i * 13,
                                'sentak': None})
            self._acak_jeda(i)

    # ── telinga ──────────────────────────────────────────────────────────
    def _acak_jeda(self, i: int) -> None:
        """Jarak ke kedutan berikutnya: deterministik, tapi tidak berirama.

        Umpannya NOMOR kedutan, bukan waktu — pelajaran dari `Wajah._acak_jeda`,
        yang versi pertamanya memakai `sin(self._t)` tepat sesudah `_t` di-nol-kan
        sehingga deraunya selalu dievaluasi di sin(0) dan jaraknya selalu sama.
        """
        k = self._kedut[i]
        k['n'] += 1
        u = derau(k['n'], self._benih + i * 131)
        k['jeda'] = self.TELINGA_JEDA_MIN + u * (self.TELINGA_JEDA_MAKS
                                                 - self.TELINGA_JEDA_MIN)

    def set_keadaan(self, sakit: bool = False, senang: float = 0.0) -> None:
        """`sakit` dari husbandry.care_of(); `senang` 0..1, meluruh sesudah
        hewannya dirawat."""
        self._sakit = bool(sakit)
        self._senang = max(0.0, min(1.0, float(senang)))

    def sentuh(self) -> None:
        """Satu sapuan sikat mendarat: kedua telinga menyentak sekarang.

        Diberi jeda kecil antar-telinga supaya bukan satu gerakan kembar.
        """
        for i, k in enumerate(self._kedut):
            if k['sentak'] is None:
                k['sentak'] = -i * 0.045
                k['t'] = 0.0
                self._acak_jeda(i)

    def _sudut_kedut(self, k, dt: float, boleh: bool) -> float:
        if k['sentak'] is None:
            if not boleh:
                return 0.0
            k['t'] += dt
            if k['t'] >= k['jeda']:
                k['sentak'] = 0.0
                k['t'] = 0.0
                self._acak_jeda(self._kedut.index(k))
            return 0.0
        k['sentak'] += dt
        ms = k['sentak'] * 1000.0
        if ms < 0.0:                       # jeda antar-telinga
            return 0.0
        if ms < self.TELINGA_KELUAR_MS:
            f = ms / self.TELINGA_KELUAR_MS
        elif ms < self.TELINGA_KELUAR_MS + self.TELINGA_PULANG_MS:
            sisa = (ms - self.TELINGA_KELUAR_MS) / self.TELINGA_PULANG_MS
            # Pulang dengan sedikit LEWAT: telinga yang berhenti persis di nol
            # terbaca sebagai tuas, bukan otot.
            f = math.cos(sisa * math.pi * 0.5) - 0.12 * math.sin(sisa * math.pi)
        else:
            k['sentak'] = None
            return 0.0
        return self.TELINGA_DERAJAT * f

    # ── ekor ─────────────────────────────────────────────────────────────
    def _sudut_ekor(self) -> float:
        a = math.tau * self._t / max(0.05, self._periode)
        pokok = math.sin(a)
        kedua = math.sin(a * self.EKOR_SINUS2 + 1.1) * self.EKOR_BOBOT2
        return self._amp * (pokok + kedua) / (1.0 + self.EKOR_BOBOT2)

    # ── satu frame ───────────────────────────────────────────────────────
    def tick(self, dt: float, sikat: float = 0.0, tidur: bool = False) -> None:
        sikat = max(0.0, min(1.0, float(sikat)))
        amp_t = (self.EKOR_DIAM_DERAJAT
                 + (self.EKOR_RAWAT_DERAJAT - self.EKOR_DIAM_DERAJAT) * sikat)
        per_t = (self.EKOR_DIAM_PERIODE
                 + (self.EKOR_RAWAT_PERIODE - self.EKOR_DIAM_PERIODE) * sikat)
        if self._sakit:
            amp_t *= self.SAKIT_EKOR_REDAM
            per_t *= self.SAKIT_EKOR_LAMBAT
        elif self._senang > 0.0:
            amp_t *= 1.0 + (self.SENANG_EKOR_LEBAR - 1.0) * self._senang
            per_t *= 1.0 - (1.0 - self.SENANG_EKOR_CEPAT) * self._senang
        if tidur:
            amp_t *= self.TIDUR_REDAM
            per_t *= self.TIDUR_LAMBAT
        # Amplitudo menyusul pelan, tidak melompat: ekor yang langsung melebar
        # di frame pertama sapuan terbaca sebagai saklar.
        k = min(1.0, self.EKOR_LERP * dt)
        self._amp += (amp_t - self._amp) * k
        self._periode += (per_t - self._periode) * k
        self._t += dt

        sudut = self._sudut_ekor()
        for p in self.ekor:
            try:
                if getattr(p, '_sumbu', 'z') == 'y':
                    p.rotation_y = sudut
                    p.rotation_x = sudut * self.EKOR_TEGAK
                else:
                    p.rotation_z = sudut
                    p.rotation_x = sudut * self.EKOR_TEGAK
            except Exception:
                pass

        # Telinga layu (sakit) atau tegak (senang) adalah sudut TETAP yang
        # ditambahkan ke sentakan, bukan menggantikannya: hewan sakit tetap
        # sesekali berkedut, cuma dari posisi yang lebih rendah.
        geser_t = 0.0
        if self._sakit:
            geser_t = self.SAKIT_TELINGA
        elif self._senang > 0.0:
            geser_t = self.SENANG_TELINGA * self._senang
        if tidur:
            # Telinga hewan tidur mengendur setengah layu, dan tidak pernah
            # lebih tegak daripada itu — hewan yang tertidur dengan telinga
            # waspada terbaca sebagai hewan yang pura-pura tidur.
            geser_t = min(geser_t, self.TIDUR_TELINGA)
        self._telinga_geser += (geser_t - self._telinga_geser) * min(
            1.0, self.KEADAAN_LERP * dt)

        for i, p in enumerate(self.telinga):
            s = self._sudut_kedut(self._kedut[i], dt, not tidur)
            try:
                if getattr(p, '_sumbu', 'z') == 'z':
                    p.rotation_z = (s + self._telinga_geser) * getattr(p, '_arah', 1.0)
                else:
                    # Tanda geser DIBALIK di sini, dan itu bukan kelalaian.
                    # Pada telinga tegak, sentakan memakai -s karena sentakan
                    # menyurukkan telinga KE BELAKANG (menjauhi muka). Tapi
                    # layu juga ke belakang dan waspada ke depan, jadi geseran
                    # keadaan berjalan di sumbu yang sama dengan tanda kebalikan
                    # sentakan: kalau ikut -geser, hewan SAKIT justru berdiri
                    # dengan telinga condong ke depan — telinga waspada.
                    p.rotation_x = -s + self._telinga_geser
            except Exception:
                pass
