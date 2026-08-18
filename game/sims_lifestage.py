"""sims_lifestage.py — TAHAP HIDUP ala The Sims (milestone S10).

Sim menua seiring hari dan tahapnya BENAR-BENAR mengubah permainan, bukan
sekadar label:

  ANAK    — belum boleh bekerja, cepat bosan (butuh main), badan lebih kecil,
            tapi belajar cepat (XP skill x1.35).
  DEWASA  — serba normal; masa produktif untuk karier.
  LANSIA  — energi lebih cepat terkuras & langkah lebih lambat, tetapi
            pengalaman membuat interaksi sosial & skill lebih berbobot.

Umur dihitung dari hari yang dijalani (state.age_days), bukan waktu nyata.
"""

STAGES = ('anak', 'dewasa', 'lansia')

# Ambang umur (hari) untuk MASUK tahap
STAGE_START = {'anak': 0, 'dewasa': 14, 'lansia': 60}

# tahap → sifat yang berpengaruh
STAGE_TRAITS = {
    'anak':   {'label': 'Anak',   'scale': 0.72, 'speed': 1.05,
               'skill_mult': 1.35, 'social_mult': 1.0,  'energy_decay': 1.0,
               'fun_decay': 1.6,  'can_work': False},
    'dewasa': {'label': 'Dewasa', 'scale': 1.0,  'speed': 1.0,
               'skill_mult': 1.0,  'social_mult': 1.0,  'energy_decay': 1.0,
               'fun_decay': 1.0,  'can_work': True},
    'lansia': {'label': 'Lansia', 'scale': 0.94, 'speed': 0.78,
               'skill_mult': 1.15, 'social_mult': 1.25, 'energy_decay': 1.45,
               'fun_decay': 0.85, 'can_work': True},
}


def stage_for_age(age_days: int) -> str:
    """Tahap hidup untuk umur tertentu."""
    s = 'anak'
    for name in STAGES:
        if age_days >= STAGE_START[name]:
            s = name
    return s


def current_stage(state) -> str:
    st = getattr(state, 'life_stage', '') or ''
    return st if st in STAGE_TRAITS else 'dewasa'


def traits(state) -> dict:
    return STAGE_TRAITS[current_stage(state)]


def stage_label(state) -> str:
    return traits(state)['label']


def can_work(state) -> bool:
    return traits(state)['can_work']


def skill_multiplier(state) -> float:
    return traits(state)['skill_mult']


def social_multiplier(state) -> float:
    return traits(state)['social_mult']


def speed_multiplier(state) -> float:
    return traits(state)['speed']


def body_scale(state) -> float:
    return traits(state)['scale']


def age_one_day(state):
    """Dipanggil dari advance_day. Return nama tahap BARU bila naik, else None."""
    state.age_days = int(getattr(state, 'age_days', 0)) + 1
    before = current_stage(state)
    after = stage_for_age(state.age_days)
    if after != before:
        state.life_stage = after
        return after
    state.life_stage = before
    return None


def days_to_next_stage(state):
    """Sisa hari menuju tahap berikutnya, atau None bila sudah lansia."""
    cur = current_stage(state)
    idx = STAGES.index(cur)
    if idx + 1 >= len(STAGES):
        return None
    nxt = STAGES[idx + 1]
    return max(0, STAGE_START[nxt] - int(getattr(state, 'age_days', 0)))


def summary(state) -> str:
    d = days_to_next_stage(state)
    tail = f", {d} hari lagi menua" if d is not None else ", tahap terakhir"
    return f"{stage_label(state)} (umur {int(getattr(state,'age_days',0))} hari){tail}"
