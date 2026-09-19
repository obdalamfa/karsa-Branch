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

        for i, p in enumerate(self.telinga):
            s = self._sudut_kedut(self._kedut[i], dt, not tidur)
            try:
                if getattr(p, '_sumbu', 'z') == 'z':
                    p.rotation_z = s * getattr(p, '_arah', 1.0)
                else:
                    p.rotation_x = -s
            except Exception:
                pass
