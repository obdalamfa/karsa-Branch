"""motives.py — Mesin motif ala The Sims 1.

Menggantikan tiga need seragam yang lama (lapar/sosial/senang, semuanya meluruh
dalam 3,5–5,8 HARI in-game) dengan delapan motif berskala −100..+100 dan laju
peluruhan asli TS1. Angka konstanta di sini diambil dari
`VMTS1MotiveDecay.Constants` lewat FreeSO; lihat `docs/PLAY_SIMS1.md` §6.

Kenapa ini penting untuk playability, bukan sekadar kesetiaan:
    Need lama tidak pernah mendesak. Tiga motif yang semuanya butuh berhari-hari
    untuk turun berarti pemain tidak pernah merasakan tekanan, dan tanpa tekanan
    tidak ada alasan untuk melakukan apa pun. TS1 memakai TIGA TEMPO berbeda —
    cepat (Comfort ~6,7 jam, Bladder ~8 jam) yang menginterupsi terus-menerus,
    sedang (Hunger ~11,6 jam, Energy 16 jam) yang membentuk struktur hari, dan
    lambat (Hygiene ~20 jam, Social berhari-hari) yang membentuk struktur minggu.
    Tiga skala waktu adalah minimum untuk menghasilkan ritme.

Dua sifat yang sengaja dipertahankan karena keduanya yang paling dikenang orang:
    1. Hunger satu-satunya motif non-linear — turun cepat saat kenyang, melambat
       saat lapar.
    2. Hunger menaikkan laju Bladder. Ini satu-satunya kopling antar-motif di
       seluruh sistem, dan sumber sebagian besar komedi TS1.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

# ─── DAFTAR MOTIF ────────────────────────────────────────
# Urutan ini dipakai sebagai urutan tampilan di panel dan sebagai indeks bobot.
MOTIVES = ('lapar', 'nyaman', 'higiene', 'kandung', 'energi', 'senang',
           'sosial', 'ruang')

LABELS = {
    'lapar':   'Lapar',
    'nyaman':  'Nyaman',
    'higiene': 'Higiene',
    'kandung': 'Kamar Kecil',
    'energi':  'Energi',
    'senang':  'Senang',
    'sosial':  'Sosial',
    'ruang':   'Ruangan',
}

MOTIVE_MIN, MOTIVE_MAX = -100.0, 100.0

# Motif yang dipakai pada perhitungan Happy untuk autonomi. Perhatikan `mood`
# ikut serta, jadi mood terhitung dua kali — itu disengaja di TS1: sim yang
# mood-nya jatuh jadi lebih putus asa secara global, bukan hanya pada motif
# yang bermasalah.
WEIGHT_MOTIVES = ('energi', 'nyaman', 'lapar', 'higiene', 'kandung',
                  'mood', 'ruang', 'sosial', 'senang')
WEIGHT = 1.0 / len(WEIGHT_MOTIVES)

# ─── KURVA KONTRIBUSI ────────────────────────────────────
# Memetakan motif mentah → "effective motive". Cekung dan jenuh: turunan besar
# di nilai rendah, hampir datar di nilai tinggi. Seluruh perilaku "prioritas
# Maslow" muncul GRATIS dari bentuk kurva ini — tidak ada tabel prioritas di
# mana pun. Sim lapar −80 menilai +20 hunger jauh lebih tinggi daripada sim
# kenyang +40 menilai +20 hunger yang sama (faktor ~11x).
_X = (-100, -80, -60, -40, -20, 0, 20, 40, 60, 80, 100)
_C_FISIK  = (-100, -78, -58, -40, -24, -10, 0, 6, 10, 12, 13)
_C_SOSIAL = (-100, -82, -64, -47, -31, -16, 0, 14, 26, 36, 45)

# Motif tubuh memakai kurva fisik (cap rendah — tubuh berhenti menuntut saat
# terpenuhi). Fun dan Social memakai kurva sosial (cap jauh lebih tinggi —
# masih menarik walau sudah cukup). Mood dan Room linear.
_CURVE_OF = {
    'lapar': _C_FISIK, 'nyaman': _C_FISIK, 'higiene': _C_FISIK,
    'kandung': _C_FISIK, 'energi': _C_FISIK,
    'senang': _C_SOSIAL, 'sosial': _C_SOSIAL,
}


def _interp(table, x: float) -> float:
    """Interpolasi linier pada tabel titik kontrol yang sejajar _X."""
    if x <= _X[0]:
        return float(table[0])
    if x >= _X[-1]:
        return float(table[-1])
    for i in range(len(_X) - 1):
        if _X[i] <= x <= _X[i + 1]:
            span = _X[i + 1] - _X[i]
            t = (x - _X[i]) / span
            return table[i] + (table[i + 1] - table[i]) * t
    return float(table[-1])


def contribution(motive: str, value: float) -> float:
    """Effective motive — nilai yang benar-benar dipakai saat menilai aksi."""
    table = _CURVE_OF.get(motive)
    if table is None:      # mood, ruang → linear
        return float(value)
    return _interp(table, value)


# ─── LAJU PELURUHAN (poin per tick; 1 tick = 2 menit-sim) ─
# Dari VMTS1MotiveDecay.Constants.
HUNGER_RATIO       = 0.0021   # dikali (100 + lapar) → non-linear
HUNGER_TO_BLADDER  = 0.3
COMFORT_ACTIVE     = 0.4      # sim aktif
COMFORT_NEUTRAL    = 0.5
COMFORT_LAZY       = 0.6      # sim malas kehilangan comfort lebih cepat
HYGIENE_AWAKE      = 0.17
HYGIENE_ASLEEP     = 0.08
BLADDER_AWAKE      = 0.3
BLADDER_ASLEEP     = 0.15
ENERGY_SPAN        = 180.0
WAKE_HOURS         = 16.0
ENERGY_AWAKE       = ENERGY_SPAN / (30.0 * WAKE_HOURS)   # 0.375
ENERGY_SLEEP_GAIN  = 1.286                                # +38,6 per jam-sim
FUN_AWAKE          = 0.25
SOCIAL_BASE        = 0.055
SOCIAL_OUTGOING    = 0.000125    # dikali Outgoing 0..1000
WAKE_HOUR          = 7

SIM_MINUTES_PER_TICK = 2.0


@dataclass
class Motives:
    """Delapan motif satu sim, plus akumulator pecahan.

    Akumulator menyimpan sisa dalam 1/1000 poin supaya pembulatan tidak
    menumpuk — persis pola TS1.
    """
    lapar:   float = 60.0
    nyaman:  float = 50.0
    higiene: float = 70.0
    kandung: float = 70.0
    energi:  float = 80.0
    senang:  float = 40.0
    sosial:  float = 40.0
    ruang:   float = 0.0      # dihitung ulang tiap tick dari ruangan sekitar

    asleep:  bool = False
    # Kepribadian 0..1000, skala TS1. Active rendah (malas) mempercepat
    # peluruhan Nyaman; Outgoing tinggi mempercepat peluruhan Sosial.
    active:   int = 500
    outgoing: int = 500

    _acc: dict = field(default_factory=dict)
    _tick_carry: float = 0.0

    # ── akses ──
    def get(self, name: str) -> float:
        return float(getattr(self, name, 0.0))

    def add(self, name: str, amount: float) -> None:
        if name not in MOTIVES:
            return
        v = self.get(name) + amount
        setattr(self, name, max(MOTIVE_MIN, min(MOTIVE_MAX, v)))

    @property
    def mood(self) -> float:
        """Rata-rata aritmetik delapan motif. Sederhana supaya pemain bisa
        menghitungnya di kepala sambil melihat panel — itu keputusan desain."""
        return sum(self.get(m) for m in MOTIVES) / len(MOTIVES)

    def as_dict(self) -> dict:
        d = {m: self.get(m) for m in MOTIVES}
        d['mood'] = self.mood
        return d

    # ── persistensi (GameState.save memakai json.dump(__dict__), jadi yang
    #    disimpan harus dict biasa, bukan dataclass) ──
    def to_save(self) -> dict:
        d = {m: round(self.get(m), 3) for m in MOTIVES}
        d.update(asleep=self.asleep, active=self.active, outgoing=self.outgoing)
        return d

    def load_save(self, d: dict) -> None:
        if not isinstance(d, dict):
            return
        for m in MOTIVES:
            if m in d:
                try:
                    setattr(self, m, max(MOTIVE_MIN, min(MOTIVE_MAX, float(d[m]))))
                except (TypeError, ValueError):
                    pass
        self.asleep = bool(d.get('asleep', self.asleep))
        for k in ('active', 'outgoing'):
            try:
                setattr(self, k, int(d.get(k, getattr(self, k))))
            except (TypeError, ValueError):
                pass

    # ── peluruhan ──
    def _decay_rate(self, name: str) -> float:
        if name == 'lapar':
            return HUNGER_RATIO * (100.0 + self.lapar)
        if name == 'nyaman':
            # Konstanta TS1 diindeks oleh sifat Active, bukan "malas". Sim
            # dengan Active RENDAH (malas) kehilangan Nyaman lebih CEPAT, jadi
            # ia lebih sering mencari kursi. Kepribadian masuk ke laju
            # peluruhan, bukan cuma ke pilihan aksi.
            if self.active > 666:
                return COMFORT_ACTIVE
            if self.active < 666:
                return COMFORT_LAZY
            return COMFORT_NEUTRAL
        if name == 'higiene':
            return HYGIENE_ASLEEP if self.asleep else HYGIENE_AWAKE
        if name == 'kandung':
            base = BLADDER_ASLEEP if self.asleep else BLADDER_AWAKE
            # Satu-satunya kopling antar-motif: makan mempercepat kandung kemih.
            return base + HUNGER_TO_BLADDER * (HUNGER_RATIO * (100.0 + self.lapar))
        if name == 'energi':
            return -ENERGY_SLEEP_GAIN if self.asleep else ENERGY_AWAKE
        if name == 'senang':
            return 0.0 if self.asleep else FUN_AWAKE
        if name == 'sosial':
            return SOCIAL_BASE + SOCIAL_OUTGOING * self.outgoing
        return 0.0    # ruang tidak meluruh — dihitung dari lingkungan

    def tick(self, sim_minutes: float) -> None:
        """Jalankan peluruhan untuk `sim_minutes` menit-sim yang telah berlalu."""
        self._tick_carry += sim_minutes
        ticks = int(self._tick_carry // SIM_MINUTES_PER_TICK)
        if ticks <= 0:
            return
        self._tick_carry -= ticks * SIM_MINUTES_PER_TICK

        for name in MOTIVES:
            if name == 'ruang':
                continue
            rate = self._decay_rate(name)
            if rate == 0.0:
                continue
            # akumulasi dalam 1/1000 poin
            acc = self._acc.get(name, 0.0) + rate * 1000.0 * ticks
            whole = int(acc // 1000.0)
            self._acc[name] = acc - whole * 1000.0
            if whole:
                self.add(name, -whole)

    def wants_to_wake(self, hour: float) -> bool:
        """Sim bangun otomatis jam 7 kalau energinya sudah cukup."""
        return self.asleep and hour >= WAKE_HOUR and self.energi >= 80.0


# ─── ADVERTISING ─────────────────────────────────────────

@dataclass
class Advert:
    """Satu janji motif dari satu interaksi.

    `minimum` adalah GERBANG, bukan bonus: iklan hanya berlaku kalau motif sim
    sudah berada di bawah nilai ini. Itu yang mencegah sim makan saat kenyang
    tanpa perlu satu pun aturan prioritas.
    """
    motive: str
    delta: float
    minimum: float | None = None


@dataclass
class Interaction:
    """Satu baris menu pada sebuah objek.

    Iklan menempel pada INTERAKSI, bukan pada objek — kulkas tidak "memberi
    +40 lapar"; interaksi *Ambil Makanan* pada kulkas yang mengiklankan lapar,
    sementara interaksi *Bersihkan* pada kulkas yang sama mengiklankan ruang.
    Objek yang sama menawarkan beberapa janji berbeda.
    """
    name: str
    adverts: list = field(default_factory=list)
    duration: float = 60.0          # menit-sim
    attenuation: float = 0.3        # falloff jarak; makin besar makin lokal
    auto_first: bool = False        # True = selalu ambil skor tertinggi
    autonomous: bool = True         # False = hanya boleh diperintah pemain


def score_interaction(motives: Motives, inter: Interaction, distance_tiles: float) -> float:
    """Delta-happy yang diprediksi dari satu interaksi, setelah falloff jarak.

    Ini bentuk ringkas dari VMFindBestAction: karena base_happy saling
    meniadakan kecuali untuk motif yang diiklankan, skornya setara dengan
    jumlah selisih kontribusi pada motif-motif yang diiklankan saja.
    """
    total = 0.0
    for ad in inter.adverts:
        cur = motives.get(ad.motive)
        # Gerbang minimum: lewati kalau motif masih di atas ambang.
        if ad.minimum is not None and cur > ad.minimum:
            continue
        predicted = max(MOTIVE_MIN, min(MOTIVE_MAX, cur + ad.delta))
        gain = contribution(ad.motive, predicted) - contribution(ad.motive, cur)
        total += gain * WEIGHT
    if total <= 0.0:
        return 0.0
    return total / (1.0 + inter.attenuation * max(0.0, distance_tiles))


def choose_action(motives: Motives, candidates, rng):
    """Pilih satu (objek, interaksi) secara otonom.

    `candidates` = iterable of (obj, interaction, distance_tiles).

    Empat skor teratas masuk ke ROULETTE BERBOBOT, bukan argmax. Itu bukan
    kelalaian — keacakan terkendali inilah sumber "kebodohan" sim yang lucu dan
    yang membuat rumah terasa hidup alih-alih deterministik.
    """
    scored = []
    for obj, inter, dist in candidates:
        if not inter.autonomous:
            continue
        s = score_interaction(motives, inter, dist)
        if s > 1e-6:
            scored.append((s, obj, inter))
    if not scored:
        return None

    scored.sort(key=lambda t: -t[0])
    top = scored[:4]
    best = top[0]
    if best[2].auto_first or len(top) == 1:
        return best[1], best[2]

    total = sum(t[0] for t in top)
    r = rng.random() * total
    acc = 0.0
    for t in top:
        acc += t[0]
        if r <= acc:
            return t[1], t[2]
    return best[1], best[2]
