"""sims_career.py — SKILL & KARIER ala The Sims (milestone S6).

Dua sistem yang saling mengunci:

  SKILL  — naik dgn MELAKUKAN, bukan dibeli. Tiap aksi objek / pakai alat
           memberi XP ke skill terkait. Level 0-10, tiap level butuh XP
           makin banyak.

  KARIER — pekerjaan berjadwal. Bekerja pada jam kerja di lokasi kerja,
           dapat gaji harian. NAIK PANGKAT butuh skill relevan + jumlah
           hari kerja, jadi skill benar-benar berguna.

Terhubung ke sistem lain:
- Mood (S4) memengaruhi kinerja kerja -> besar gaji.
- advance_day (TimeController) -> reset shift harian.
"""
from .config import NEED_MAX

MAX_SKILL_LEVEL = 10

# id -> (label, deskripsi singkat)
SKILLS = {
    'bertani':   ('Bertani',   'Cangkul, tanam, siram, panen'),
    'memasak':   ('Memasak',   'Kompor & kulkas'),
    'logika':    ('Logika',    'Membaca buku'),
    'kebugaran': ('Kebugaran', 'Menambang & bertarung'),
    'karisma':   ('Karisma',   'Interaksi sosial'),
    'kerajinan': ('Kerajinan', 'Crafting & menempa'),
}


def xp_to_next(level: int) -> float:
    """XP yang dibutuhkan untuk naik DARI level ini ke level berikutnya."""
    return 40.0 + 22.0 * (level ** 1.5)


# id -> definisi karier. ranks: (nama, gaji/hari, syarat level skill, syarat hari)
CAREERS = {
    'tani': {
        'label': 'Buruh Tani', 'skill': 'bertani',
        'start': 8, 'end': 16, 'scene': 'farm',
        'ranks': [
            ('Buruh Panen',      45, 0, 0),
            ('Petani Terampil',  80, 2, 3),
            ('Mandor Sawah',    140, 4, 8),
            ('Juragan Tani',    240, 6, 15),
        ],
    },
    'pandai_besi': {
        'label': 'Pandai Besi', 'skill': 'kerajinan',
        'start': 9, 'end': 17, 'scene': 'smith',
        'ranks': [
            ('Tukang Pikul',     50, 0, 0),
            ('Asisten Tempa',    95, 2, 3),
            ('Pandai Besi',     165, 4, 8),
            ('Empu Pusaka',     280, 6, 15),
        ],
    },
    'warung': {
        'label': 'Pelayan Warung', 'skill': 'karisma',
        'start': 10, 'end': 18, 'scene': 'shop',
        'ranks': [
            ('Pencuci Piring',   40, 0, 0),
            ('Pelayan',          75, 2, 3),
            ('Juru Masak',      130, 4, 8),
            ('Pemilik Warung',  220, 6, 15),
        ],
    },
}


# --- SKILL ---------------------------------------------------------------
def _skills(state) -> dict:
    if getattr(state, 'skills', None) is None:
        state.skills = {}
    return state.skills


def skill_level(state, skill_id: str) -> int:
    return int(_skills(state).get(skill_id, {}).get('lv', 0))


def skill_xp(state, skill_id: str) -> float:
    return float(_skills(state).get(skill_id, {}).get('xp', 0.0))


def add_skill_xp(state, skill_id: str, amount: float):
    """Tambah XP. Return (level_sekarang, naik_level_bool)."""
    if skill_id not in SKILLS or amount <= 0:
        return skill_level(state, skill_id), False
    sk = _skills(state).setdefault(skill_id, {'lv': 0, 'xp': 0.0})
    sk['xp'] = float(sk.get('xp', 0.0)) + float(amount)
    leveled = False
    while sk['lv'] < MAX_SKILL_LEVEL and sk['xp'] >= xp_to_next(sk['lv']):
        sk['xp'] -= xp_to_next(sk['lv'])
        sk['lv'] += 1
        leveled = True
    return sk['lv'], leveled


def skill_summary(state) -> str:
    parts = [f"{SKILLS[k][0]} {v['lv']}" for k, v in sorted(_skills(state).items())
             if v.get('lv', 0) > 0]
    return ' - '.join(parts) if parts else 'Belum ada skill'


# --- KARIER --------------------------------------------------------------
def career_id(state):
    return getattr(state, 'career', None)


def career_rank(state) -> int:
    return int(getattr(state, 'career_level', 0))


def career_info(state):
    """(career_dict, rank_tuple) atau (None, None) bila menganggur."""
    cid = career_id(state)
    if not cid or cid not in CAREERS:
        return None, None
    c = CAREERS[cid]
    r = c['ranks'][min(career_rank(state), len(c['ranks']) - 1)]
    return c, r


def join_career(state, cid: str) -> bool:
    if cid not in CAREERS:
        return False
    state.career = cid
    state.career_level = 0
    state.work_days = 0
    state.worked_today = False
    return True


def is_work_hour(state) -> bool:
    c, _ = career_info(state)
    if not c:
        return False
    h = state.get_hour()
    return c['start'] <= h < c['end']


def at_workplace(state) -> bool:
    c, _ = career_info(state)
    return bool(c) and state.scene_name == c['scene']


def can_work_now(state):
    """(boleh, alasan_bila_tidak)."""
    c, _ = career_info(state)
    if not c:
        return False, "Kamu belum punya pekerjaan."
    if getattr(state, 'worked_today', False):
        return False, "Kamu sudah bekerja hari ini."
    if not is_work_hour(state):
        return False, f"Jam kerja {c['start']}:00-{c['end']}:00."
    if not at_workplace(state):
        return False, f"Kamu harus di {c['scene']} untuk bekerja."
    return True, None


def work_shift(state):
    """Jalankan satu shift kerja. Return dict hasil atau None bila tak boleh.
    Gaji dipengaruhi MOOD (kinerja): mood bagus dibayar lebih."""
    ok, _why = can_work_now(state)
    if not ok:
        return None
    from .sims_mood import mood_social_bonus, mood_label
    c, rank = career_info(state)
    name, wage, _req_lv, _req_days = rank
    perf = 1.0 + mood_social_bonus(state) / 100.0
    pay = max(1, int(round(wage * perf)))
    state.gold += pay
    state.worked_today = True
    state.work_days = int(getattr(state, 'work_days', 0)) + 1
    state.energy = max(0, state.energy - 25)          # kerja melelahkan
    state.sosial = min(NEED_MAX, state.sosial + 10)   # bertemu orang
    lv, leveled = add_skill_xp(state, c['skill'], 28.0)
    return {'pay': pay, 'rank': name, 'perf': perf, 'mood': mood_label(state),
            'skill': c['skill'], 'skill_level': lv, 'leveled': leveled}


def promotion_status(state):
    """(bisa_naik, nama_pangkat_berikut, teks_syarat)."""
    c, _ = career_info(state)
    if not c:
        return False, None, "Belum bekerja."
    nxt_i = career_rank(state) + 1
    if nxt_i >= len(c['ranks']):
        return False, None, "Sudah pangkat tertinggi."
    nname, _w, req_lv, req_days = c['ranks'][nxt_i]
    have_lv = skill_level(state, c['skill'])
    have_days = int(getattr(state, 'work_days', 0))
    ok = have_lv >= req_lv and have_days >= req_days
    txt = (f"{nname}: butuh {SKILLS[c['skill']][0]} {req_lv} (kini {have_lv})"
           f" & {req_days} hari kerja (kini {have_days})")
    return ok, nname, txt


def try_promote(state):
    """Naik pangkat bila syarat terpenuhi. Return nama pangkat baru / None."""
    ok, nname, _ = promotion_status(state)
    if not ok:
        return None
    state.career_level = career_rank(state) + 1
    return nname


def reset_daily(state):
    """Dipanggil dari advance_day - shift baru tersedia."""
    state.worked_today = False
