"""batin.py — Majelis Batin: 4 suara dalam kepala + skill-check 2d6
(DNA Disco Elysium, di-port dari prototipe three.js ke game Ursina).

Logika MURNI Python (tanpa Ursina) supaya bisa diuji terpisah; UI dirender
oleh panels.py yang membaca `Batin.lines` dan `state.batin`.

Empat suara:
  BARA  — amarah, harga diri, tubuh sebagai dalil
  AKAR  — tanah, kesabaran, ingatan ladang
  SUKMA — tenaga dalam, sandi, retak tempat cahaya masuk
  LAPAR — selera, bertahan hidup, hitungan jujur
"""
import random

VOICES = {
    'bara':  {'name': 'BARA',  'col': (217, 93, 93),  'desc': 'amarah, harga diri, tubuh'},
    'akar':  {'name': 'AKAR',  'col': (111, 174, 87), 'desc': 'tanah, kesabaran, ladang'},
    'sukma': {'name': 'SUKMA', 'col': (155, 126, 217),'desc': 'tenaga dalam, sandi, retak'},
    'lapar': {'name': 'LAPAR', 'col': (232, 149, 74), 'desc': 'selera, bertahan hidup'},
}

DIFF = {'sepele': 6, 'mudah': 7, 'sedang': 8, 'sukar': 10, 'berat': 12, 'mustahil': 13}
DIFF_NAME = {'sepele': 'Sepele', 'mudah': 'Mudah', 'sedang': 'Sedang',
             'sukar': 'Sukar', 'berat': 'Berat', 'mustahil': 'Mustahil'}


def _stat(state, voice):
    b = getattr(state, 'batin', None)
    return (b or {}).get(voice, 1)


def roll(state, voice, diff):
    """Lempar 2d6 + nilai suara vs ambang. 2 = gagal mutlak, 12 = sukses mutlak."""
    a, b = random.randint(1, 6), random.randint(1, 6)
    s = a + b
    tgt = DIFF[diff]
    st = _stat(state, voice)
    if s == 2:
        ok = False
    elif s == 12:
        ok = True
    else:
        ok = (s + st) >= tgt
    return {'ok': ok, 'txt': f'[{a}+{b}+{st} lwn {tgt}]'}


def pct(state, voice, diff):
    """Peluang sukses (%) ditampilkan di opsi — sebaran jumlah 2d6."""
    need = DIFF[diff] - _stat(state, voice)
    dist = {2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1}
    w = sum(dist[s] for s in range(2, 13) if s >= need)
    w = max(1, min(35, w))
    return round(w / 36 * 100)


def raise_voice(state, voice, n=1):
    b = getattr(state, 'batin', None)
    if isinstance(b, dict):
        b[voice] = b.get(voice, 1) + n


class Batin:
    """Penyimpan log suara + bendera sekali-ucap. Satu instance per game.

    Bendera sekali-ucap tinggal di `state.batin_sekali` (list, ikut disimpan),
    bukan di memori. Dulu ia sebuah set di sini, jadi PAGI PERTAMA muncul
    lagi di setiap sesi dan pilihannya bisa menaikkan suara +1 per sesi.
    Bendera dibaca lewat `self.state` tiap kali: F9 mengganti ISI state di
    tempat (app.py), jadi rujukan ke objeknya tetap benar.

    `lines` sengaja TIDAK disimpan: ia riwayat obrolan untuk panel, bukan
    keadaan permainan. Sesi baru mulai dengan log kosong.
    """

    def __init__(self, state):
        self.state = state
        self.lines = []        # [(voice, text)] — riwayat untuk panel

    def _sekali(self):
        s = getattr(self.state, 'batin_sekali', None)
        if not isinstance(s, list):
            s = []
            try:
                self.state.batin_sekali = s
            except Exception:
                pass
        return s

    def say(self, voice, text):
        self.lines.append((voice, text))
        if len(self.lines) > 60:
            self.lines.pop(0)

    def say_once(self, flag, voice, text):
        if not self.once(flag):
            return False
        self.say(voice, text)
        return True

    def once(self, flag):
        """True hanya pada panggilan pertama untuk `flag` (pemicu satu kali)."""
        sudah = self._sekali()
        if flag in sudah:
            return False
        sudah.append(flag)
        return True

    def check(self, voice, diff):
        return roll(self.state, voice, diff)
