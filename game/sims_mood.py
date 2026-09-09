"""sims_mood.py — MOOD / EMOSI ala The Sims (milestone S4).

Mood lahir dari MOTIF: satu kebutuhan yang kritis mendominasi perasaan Sim
(lapar berat → "Kelaparan"), kalau semua aman barulah rata-rata motif yang
menentukan (gembira → lesu → muram).

Mood lalu MEMENGARUHI permainan:
- kecepatan aksi objek  (mood bagus → lebih cepat selesai)
- keberhasilan sosial   (mood bagus → interaksi lebih mudah berhasil)

Dipakai oleh:
- controllers/sims_action_controller.py  (skala durasi aksi)
- controllers/interaction_controller.py  (bonus interaksi sosial)
- panels.py                              (chip mood di HUD)
"""
from .config import NEED_CRITICAL, NEED_LOW, NEED_HIGH
from .sims_objects import MOTIVE_FIELDS, motive_value

# id → (label, warna RGB, kecepatan aksi, bonus sosial)
#   speed : pengali durasi aksi (<1 = lebih cepat)
#   social: tambahan peluang/efek interaksi sosial (persen poin)
MOODS = {
    'gembira':  ('Gembira',   (120, 210, 140), 0.85, +15),
    'baik':     ('Baik',      (150, 190, 160), 1.00,   0),
    'lesu':     ('Lesu',      (170, 165, 130), 1.15, -10),
    'muram':    ('Muram',     (150, 130, 140), 1.30, -20),
    # Mood dominan dari satu motif kritis (mengalahkan rata-rata)
    'lapar':    ('Kelaparan', (215, 150, 70),  1.35, -20),
    'lelah':    ('Kelelahan', (130, 150, 200), 1.40, -20),
    'kebelet':  ('Kebelet',   (200, 185, 90),  1.45, -30),
    'jijik':    ('Jijik',     (120, 165, 195), 1.25, -25),
    'kesepian': ('Kesepian',  (90, 160, 155),  1.15, -15),
    'bosan':    ('Bosan',     (165, 135, 180), 1.20, -10),
}

# motif kritis → mood dominan. Urutan = prioritas (paling mendesak dulu).
_CRITICAL_MOOD = (
    ('kandung', 'kebelet'),
    ('lapar',   'lapar'),
    ('energy',  'lelah'),
    ('bersih',  'jijik'),
    ('sosial',  'kesepian'),
    ('senang',  'bosan'),
)


def current_mood(state) -> str:
    """id mood Sim sekarang."""
    # 1) Satu motif kritis mendominasi perasaan
    for field, mood_id in _CRITICAL_MOOD:
        if motive_value(state, field) <= NEED_CRITICAL:
            return mood_id
    # 2) Selain itu: rata-rata seluruh motif
    avg = sum(motive_value(state, f) for f in MOTIVE_FIELDS) / len(MOTIVE_FIELDS)
    if avg >= NEED_HIGH:
        return 'gembira'
    if avg >= NEED_LOW + 10:
        return 'baik'
    if avg >= NEED_LOW - 10:
        return 'lesu'
    return 'muram'


def mood_label(state) -> str:
    return MOODS[current_mood(state)][0]


def mood_color(state):
    return MOODS[current_mood(state)][1]


def mood_speed_multiplier(state) -> float:
    """Pengali durasi aksi objek. <1 = Sim bersemangat, >1 = loyo."""
    return MOODS[current_mood(state)][2]


def mood_social_bonus(state) -> int:
    """Tambahan efek interaksi sosial (poin). Negatif saat mood buruk."""
    return MOODS[current_mood(state)][3]
