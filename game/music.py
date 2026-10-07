"""
music.py — Musik adaptif berlapis: SUASANA (musik) + LATAR (bunyi tempat).

Dulu tiap scene memutar satu loop 16 detik yang sama sepanjang hari. Sekarang
musik dipilih dari keadaan dunia:

    bahaya (musuh dekat) > tempat khusus (gua, swarga, rumah...) >
    cuaca (hujan/badai) > waktu (fajar, siang, senja, malam)

dan musim menggeser nada dasar serta tempo, jadi Musim Dingin terdengar lebih
rendah dan lambat daripada Musim Panas pada suasana yang sama.

Latar adalah lapisan terpisah (angin, burung, jangkrik, hujan, ombak, tetes
gua, perapian) yang berganti sendiri, sehingga musik "siang" di sawah dan di
kota tetap terdengar berbeda.

Semua dirender prosedural dengan numpy di thread latar dan disimpan di memori;
loop yang belum siap tidak menghentikan game, ia hanya mulai saat selesai.
Kalau numpy tidak ada, `AVAILABLE` False dan sound.py memakai sistem lama.
"""
import math
import random
import threading

import pygame

try:
    import numpy as np
    AVAILABLE = True
except Exception:  # numpy opsional di runtime
    np = None
    AVAILABLE = False

_RATE = 22050
_LOOP_BARS = 8

# ─── Kanal: dua untuk musik dan dua untuk latar, supaya bisa crossfade ───────
_CH_MUSIC = (0, 1)
_CH_BED = (2, 3)
_FADE_MS = 2500
_FADE_FAST_MS = 600


# ═══ RESEP SUASANA ══════════════════════════════════════════════════════════
# chords: derajat akor dalam tangga nada (0 = tonik), satu per birama.
# lead: 'pluck' (petik, seperti kecapi/gamelan lembut) atau 'pad' (panjang).
# density: peluang ada not melodi pada tiap ketukan setengah.
# Tangga nada pentatonik dipakai untuk rasa Nusantara (slendro-ish / pelog-ish).
SCALES = {
    'mayor':     [0, 2, 4, 7, 9],          # pentatonik mayor, cerah
    'minor':     [0, 3, 5, 7, 10],         # pentatonik minor
    'pelog':     [0, 1, 3, 7, 8],          # warna pelog, misterius
    'dorian':    [0, 2, 3, 5, 7, 9, 10],
    'lydian':    [0, 2, 4, 6, 7, 9, 11],   # mengambang, sakral
}

MOODS = {
    'fajar':   dict(root=62, scale='mayor',  bpm=72,  chords=[0, 3, 1, 4, 0, 3, 2, 4],
                    lead='pluck', density=0.35, pad=0.06, lead_vol=0.05, bass=0.05, seed=11),
    'siang':   dict(root=67, scale='mayor',  bpm=96,  chords=[0, 3, 4, 0, 1, 3, 4, 0],
                    lead='pluck', density=0.55, pad=0.05, lead_vol=0.055, bass=0.06, seed=12,
                    perc=0.012),
    'senja':   dict(root=64, scale='dorian', bpm=76,  chords=[0, 5, 3, 4, 0, 5, 2, 4],
                    lead='pluck', density=0.40, pad=0.07, lead_vol=0.045, bass=0.05, seed=13),
    'malam':   dict(root=57, scale='minor',  bpm=60,  chords=[0, 3, 4, 2, 0, 3, 1, 0],
                    lead='pluck', density=0.22, pad=0.07, lead_vol=0.035, bass=0.04, seed=14),
    'hujan':   dict(root=60, scale='minor',  bpm=66,  chords=[0, 2, 3, 1, 0, 2, 4, 0],
                    lead='pad',   density=0.25, pad=0.08, lead_vol=0.03, bass=0.04, seed=15),
    'badai':   dict(root=55, scale='pelog',  bpm=80,  chords=[0, 1, 0, 3, 0, 1, 4, 3],
                    lead='pad',   density=0.30, pad=0.09, lead_vol=0.03, bass=0.07, seed=16),
    'rumah':   dict(root=60, scale='mayor',  bpm=70,  chords=[0, 3, 0, 4, 1, 3, 4, 0],
                    lead='pluck', density=0.40, pad=0.08, lead_vol=0.04, bass=0.04, seed=17),
    'pasar':   dict(root=65, scale='mayor',  bpm=108, chords=[0, 4, 3, 4, 0, 4, 1, 0],
                    lead='pluck', density=0.65, pad=0.04, lead_vol=0.05, bass=0.06, seed=18,
                    perc=0.015),
    'pantai':  dict(root=62, scale='lydian', bpm=84,  chords=[0, 1, 0, 4, 0, 1, 5, 4],
                    lead='pluck', density=0.40, pad=0.06, lead_vol=0.045, bass=0.05, seed=19),
    'misteri': dict(root=52, scale='pelog',  bpm=56,  chords=[0, 1, 0, 3, 0, 1, 4, 0],
                    lead='pluck', density=0.18, pad=0.07, lead_vol=0.035, bass=0.05, seed=20),
    'gua':     dict(root=45, scale='pelog',  bpm=50,  chords=[0, 0, 1, 0, 3, 3, 1, 0],
                    lead='pad',   density=0.15, pad=0.08, lead_vol=0.03, bass=0.06, seed=21),
    'sakral':  dict(root=62, scale='lydian', bpm=58,  chords=[0, 1, 0, 4, 0, 1, 2, 0],
                    lead='pad',   density=0.30, pad=0.09, lead_vol=0.035, bass=0.04, seed=22),
    'bahaya':  dict(root=57, scale='minor',  bpm=138, chords=[0, 3, 4, 2, 0, 3, 4, 4],
                    lead='pluck', density=0.75, pad=0.04, lead_vol=0.05, bass=0.09, seed=23,
                    perc=0.03),
}

# Musim menggeser nada dasar (semiton) dan tempo.
SEASON_SHIFT = {
    'Semi':   (0,  1.00),
    'Panas':  (2,  1.06),
    'Gugur':  (-1, 0.95),
    'Dingin': (-3, 0.88),
}

# Tempat yang punya suasana sendiri, tidak ikut jam.
_PLACE_MOOD = {
    'house': 'rumah', 'clinic': 'rumah', 'studio': 'rumah', 'greenhouse': 'rumah',
    'shop': 'pasar', 'smith': 'pasar',
    'dungeon': 'gua', 'naga_cave': 'gua',
    'swarga': 'sakral',
}
_INDOOR = {'house', 'clinic', 'studio', 'greenhouse', 'shop', 'smith'}
_UNDERGROUND = {'dungeon', 'naga_cave'}

# Latar (bunyi tempat) per scene saat siang; malam diganti jangkrik di luar.
_PLACE_BED = {
    'farm': 'angin', 'town': 'angin', 'mountain': 'hutan', 'cemetery': 'hutan',
    'lake': 'air', 'beach': 'ombak', 'swarga': 'angin',
    'dungeon': 'tetes', 'naga_cave': 'tetes',
    'house': 'perapian', 'clinic': 'sunyi', 'studio': 'sunyi', 'greenhouse': 'sunyi',
    'shop': 'sunyi', 'smith': 'perapian',
}


def choose(scene, hour, weather, combat=False):
    """Pilih (suasana, latar) dari keadaan dunia. Fungsi murni, mudah diuji."""
    indoor = scene in _INDOOR
    under = scene in _UNDERGROUND
    raining = weather in ('Hujan', 'Badai') and not indoor and not under
    night = hour >= 20 or hour < 5

    if combat:
        mood = 'bahaya'
    elif scene in _PLACE_MOOD:
        mood = _PLACE_MOOD[scene]
    elif scene == 'cemetery' or (scene == 'mountain' and night):
        mood = 'misteri'
    elif raining:
        mood = 'badai' if weather == 'Badai' else 'hujan'
    elif scene == 'beach' and 7 <= hour < 18:
        mood = 'pantai'
    elif 5 <= hour < 8:
        mood = 'fajar'
    elif 8 <= hour < 17:
        mood = 'pasar' if scene == 'town' and 9 <= hour < 15 else 'siang'
    elif 17 <= hour < 20:
        mood = 'senja'
    else:
        mood = 'malam'

    bed = _PLACE_BED.get(scene, 'angin')
    if raining:
        bed = 'hujan'
    elif night and not indoor and not under and bed in ('angin', 'hutan'):
        bed = 'jangkrik'
    return mood, bed


# ═══ SINTESIS ═══════════════════════════════════════════════════════════════
def _hz(midi):
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)


def _tone(freq, n, kind):
    t = np.arange(n) / _RATE
    ph = 2 * np.pi * freq * t
    if kind == 'pad':
        # Dua osilator sedikit detune: lebih lebar, tidak "beep".
        return 0.5 * np.sin(ph) + 0.35 * np.sin(ph * 1.003) + 0.15 * np.sin(2 * ph)
    if kind == 'pluck':
        # Harmonik berbobot ala bilah logam lembut (bonang/kecapi).
        return np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.12 * np.sin(3.01 * ph)
    return np.sin(ph)


def _place(buf, sig, start):
    """Tambah sinyal ke buffer loop; ekor yang lewat ujung membungkus ke awal
    sehingga loop tersambung tanpa klik."""
    n = len(buf)
    start %= n
    end = start + len(sig)
    if end <= n:
        buf[start:end] += sig
    else:
        cut = n - start
        buf[start:] += sig[:cut]
        rest = sig[cut:]
        while len(rest):
            m = min(len(rest), n)
            buf[:m] += rest[:m]
            rest = rest[m:]


def _note(freq, dur, kind, vol, attack, release):
    n = max(1, int(dur * _RATE))
    sig = _tone(freq, n, kind)
    env = np.ones(n)
    a = min(n, max(1, int(attack * _RATE)))
    env[:a] = np.linspace(0, 1, a)
    if kind == 'pluck':
        env *= np.exp(-np.arange(n) / (_RATE * max(0.05, dur * 0.35)))
    r = min(n, max(1, int(release * _RATE)))
    env[-r:] *= np.linspace(1, 0, r)
    return vol * sig * env


def _stable(text):
    """Benih yang sama di tiap jalan (hash() str diacak per proses)."""
    return sum((i + 1) * ord(ch) for i, ch in enumerate(text))


def render_mood(name, season='Semi'):
    p = MOODS[name]
    shift, tempo = SEASON_SHIFT.get(season, (0, 1.0))
    root = p['root'] + shift
    scale = SCALES[p['scale']]
    beat = 60.0 / (p['bpm'] * tempo)
    bar = beat * 4
    n = int(bar * _LOOP_BARS * _RATE)
    buf = np.zeros(n)
    rng = random.Random(p['seed'] * 31 + _stable(season))

    def deg(d, octave=0):
        o, i = divmod(d, len(scale))
        return root + scale[i] + 12 * (o + octave)

    melody_pos = 2 * len(scale)  # mulai di oktaf atas
    for b, c in enumerate(p['chords'][:_LOOP_BARS]):
        t0 = int(b * bar * _RATE)
        chord = [deg(c), deg(c + 2), deg(c + 4)]
        # Pad: akor panjang, serangan pelan, ekor masuk birama berikut.
        for m in chord:
            _place(buf, _note(_hz(m), bar * 1.25, 'pad', p['pad'] / 3, bar * 0.3, bar * 0.5), t0)
        # Bass: akar akor di ketukan 1 dan 3.
        for k in (0, 2):
            _place(buf, _note(_hz(deg(c, -2)), beat * 1.8, 'sine', p['bass'], 0.02, beat * 0.8),
                   t0 + int(k * beat * _RATE))
        # Melodi: jalan acak berbobot di tangga nada, condong ke nada akor.
        for h in range(8):
            if rng.random() > p['density']:
                continue
            step = rng.choice([-2, -1, -1, 0, 1, 1, 2])
            melody_pos = max(len(scale), min(3 * len(scale), melody_pos + step))
            if h % 4 == 0 and rng.random() < 0.6:  # ketukan kuat → nada akor
                melody_pos = min(range(len(scale), 3 * len(scale) + 1),
                                 key=lambda d: abs(d - melody_pos) + (0 if (d - c) % 2 == 0 else 3))
            dur = beat * (1.5 if p['lead'] == 'pluck' else 2.5)
            vel = p['lead_vol'] * (1.0 if h % 2 == 0 else 0.75)
            _place(buf, _note(_hz(deg(melody_pos)), dur, p['lead'], vel,
                              0.005 if p['lead'] == 'pluck' else 0.3, dur * 0.4),
                   t0 + int(h * beat / 2 * _RATE))
        # Perkusi lembut (kendang/shaker samar) untuk suasana yang bergerak.
        if p.get('perc'):
            for h in range(8):
                L = int(0.04 * _RATE)
                hit = np.random.default_rng(b * 8 + h).uniform(-1, 1, L) * np.linspace(1, 0, L) ** 3
                acc = 1.0 if h % 2 == 0 else 0.55
                _place(buf, p['perc'] * acc * hit, t0 + int(h * beat / 2 * _RATE))
            _place(buf, _note(70, beat * 0.5, 'sine', p['perc'] * 3, 0.002, beat * 0.4), t0)
    return _finish(buf, 0.9)


def render_bed(name, seconds=12.0):
    n = int(seconds * _RATE)
    t = np.arange(n) / _RATE
    rng = np.random.default_rng(_stable(name))
    noise = rng.uniform(-1, 1, n)

    def lowpass(x, a):
        # Filter satu kutub sebagai konvolusi kernel eksponensial: tanpa loop
        # Python, jadi thread render tidak menahan GIL dan frame game.
        k = a * (1 - a) ** np.arange(int(6 / a))
        return np.convolve(np.concatenate([x[-len(k):], x]), k, 'full')[len(k):len(k) + len(x)]

    # Gelombang lambat yang berulang tepat di panjang loop.
    def slow(cycles, phase=0.0):
        return 0.5 + 0.5 * np.sin(2 * np.pi * cycles * t / seconds + phase)

    buf = np.zeros(n)
    if name in ('angin', 'hutan'):
        buf += lowpass(noise, 0.03) * 1.6 * (0.35 + 0.65 * slow(2) * slow(3, 1.0))
    if name == 'hutan':
        for _ in range(9):  # kicau burung: sapuan nada tinggi pendek
            s = rng.integers(0, n)
            L = int(rng.uniform(0.06, 0.14) * _RATE)
            f = np.linspace(rng.uniform(2600, 3400), rng.uniform(3200, 4200), L)
            chirp = np.sin(2 * np.pi * np.cumsum(f) / _RATE) * np.hanning(L) * 0.05
            _place(buf, chirp, s)
    if name == 'jangkrik':
        buf += lowpass(noise, 0.02) * 0.5 * slow(2)
        trill = (np.sin(2 * np.pi * 4300 * t) * (np.sin(2 * np.pi * 30 * t) > 0.3)
                 * (slow(6) > 0.45))
        buf += trill * 0.012
    if name == 'hujan':
        buf += lowpass(noise, 0.35) * 0.18 + lowpass(noise, 0.05) * 0.6
        for _ in range(140):  # tetes besar acak di atap/daun
            s = rng.integers(0, n)
            L = int(0.02 * _RATE)
            _place(buf, rng.uniform(-1, 1, L) * np.linspace(1, 0, L) ** 2 * 0.05, s)
    if name == 'air':
        buf += lowpass(noise, 0.04) * 0.9 * (0.4 + 0.6 * slow(5) * slow(3, 2.0))
    if name == 'ombak':
        swell = slow(2) ** 3 + 0.6 * slow(3, 1.7) ** 4
        buf += lowpass(noise, 0.08) * 1.2 * swell
    if name == 'tetes':
        buf += np.sin(2 * np.pi * 50 * t) * 0.03 * slow(1)
        for _ in range(7):
            s = rng.integers(0, n)
            L = int(0.4 * _RATE)
            f = rng.uniform(900, 1600)
            _place(buf, np.sin(2 * np.pi * f * np.arange(L) / _RATE)
                   * np.exp(-np.arange(L) / (0.06 * _RATE)) * 0.06, s)
    if name == 'perapian':
        buf += lowpass(noise, 0.02) * 0.4
        for _ in range(120):
            s = rng.integers(0, n)
            L = int(rng.uniform(0.003, 0.012) * _RATE)
            _place(buf, rng.uniform(-1, 1, L) * rng.uniform(0.02, 0.07), s)
    # 'sunyi': sengaja hampir kosong, hanya dengung ruangan.
    if name == 'sunyi':
        buf += lowpass(noise, 0.01) * 0.25
    # Sambungkan ujung loop dengan crossfade pendek agar tidak klik.
    x = int(0.25 * _RATE)
    buf[:x] = buf[:x] * np.linspace(0, 1, x) + buf[-x:] * np.linspace(1, 0, x)
    buf = buf[:-x]
    return _finish(buf, 0.6)


def _finish(buf, ceiling):
    peak = np.max(np.abs(buf)) or 1.0
    buf = np.tanh(buf / peak * 1.2) / math.tanh(1.2) * ceiling  # limiter lembut
    pcm = (buf * 32767).astype(np.int16)
    channels = (pygame.mixer.get_init() or (0, 0, 1))[2]
    if channels > 1:
        pcm = np.repeat(pcm[:, None], channels, axis=1)
    return pygame.mixer.Sound(buffer=np.ascontiguousarray(pcm).tobytes())


# ═══ PEMUTAR ════════════════════════════════════════════════════════════════
class _Layer:
    """Satu lapisan dengan dua kanal bergantian supaya pergantian crossfade."""

    def __init__(self, ids):
        self.channels = [pygame.mixer.Channel(i) for i in ids]
        self.active = 0
        self.key = None
        self.base_vol = 0.0

    def play(self, key, snd, vol, fade_ms):
        old = self.channels[self.active]
        old.fadeout(fade_ms)
        self.active ^= 1
        ch = self.channels[self.active]
        ch.set_volume(vol)
        ch.play(snd, loops=-1, fade_ms=fade_ms)
        self.key = key
        self.base_vol = vol

    def set_gain(self, gain, dt):
        ch = self.channels[self.active]
        target = max(0.0, min(1.0, self.base_vol * gain))
        cur = ch.get_volume()
        ch.set_volume(cur + (target - cur) * min(1.0, 3.0 * dt))


class MusicDirector:
    MUSIC_VOL = 0.42
    BED_VOL = 0.30

    def __init__(self):
        pygame.mixer.set_num_channels(max(16, pygame.mixer.get_num_channels()))
        pygame.mixer.set_reserved(4)  # efek suara tidak akan mencuri kanal 0-3
        self.music = _Layer(_CH_MUSIC)
        self.bed = _Layer(_CH_BED)
        self._cache = {}
        self._pending = set()
        self._lock = threading.Lock()
        self.want = (None, None)

    # Render di thread supaya game tidak membeku saat suasana baru dibutuhkan.
    def _get(self, key):
        with self._lock:
            if key in self._cache:
                return self._cache[key]
            if key in self._pending:
                return None
            self._pending.add(key)
        threading.Thread(target=self._render, args=(key,), daemon=True).start()
        return None

    def _render(self, key):
        try:
            kind, name, season = key
            snd = render_mood(name, season) if kind == 'm' else render_bed(name)
        except Exception as e:
            print(f"[Music] gagal render {key}: {e}")
            snd = None
        with self._lock:
            self._cache[key] = snd
            self._pending.discard(key)

    def prewarm(self, season='Semi'):
        for b in ('angin', 'jangkrik', 'perapian', 'hujan'):
            self._get(('b', b, ''))
        for m in ('fajar', 'siang', 'senja', 'malam', 'rumah'):
            self._get(('m', m, season))

    def update(self, scene, hour, weather, season, combat=False, gain=1.0, dt=0.016):
        mood, bed = choose(scene, hour, weather, combat)
        fade = _FADE_FAST_MS if combat or self.music.key and self.music.key[1] == 'bahaya' else _FADE_MS
        mkey = ('m', mood, season)
        if self.music.key != mkey:
            snd = self._get(mkey)
            if snd is not None:
                self.music.play(mkey, snd, self.MUSIC_VOL, fade)
        bkey = ('b', bed, '')
        if self.bed.key != bkey:
            snd = self._get(bkey)
            if snd is not None:
                self.bed.play(bkey, snd, self.BED_VOL, _FADE_MS)
        self.music.set_gain(gain, dt)
        self.bed.set_gain(1.0, dt)
        self.want = (mood, bed)
