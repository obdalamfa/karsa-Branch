"""sims_aspiration.py — KEINGINAN & ASPIRASI ala The Sims (milestone S9).

Dua lapis motivasi, persis The Sims:

  KEINGINAN (wants) — target jangka PENDEK yang muncul tiap hari, tiga
      sekaligus. Memenuhinya memberi Simoleon + rasa senang. Isinya menyesuaikan
      keadaanmu (kalau belum punya kerja, muncul keinginan melamar kerja).

  ASPIRASI (aspiration) — tujuan HIDUP jangka panjang yang kamu pilih sekali.
      Tuntas = hadiah besar + gelar permanen.

Terhubung: skill/karier (S6), relasi (S5), rumah tangga (S8), emas & motif.
"""
from .config import NEED_MAX

WANT_SLOTS = 3


def _lvl(state, sk):
    from .sims_career import skill_level
    return skill_level(state, sk)


def _friends_at_least(state, n_hearts):
    return sum(1 for v in (state.npc_hearts or {}).values() if v >= n_hearts)


# ── KEINGINAN HARIAN ──────────────────────────────────────────────────────
# id → (label, syarat(state)->bool, hadiah_gold, hadiah_senang, relevan(state)->bool)
WANTS = {
    'kerja_hari_ini': ("Bekerja hari ini", lambda s: bool(getattr(s, 'worked_today', False)),
                       60, 12, lambda s: bool(getattr(s, 'career', ''))),
    'cari_kerja':     ("Melamar pekerjaan", lambda s: bool(getattr(s, 'career', '')),
                       80, 15, lambda s: not getattr(s, 'career', '')),
    'skill_tani':     ("Bertani level 2", lambda s: _lvl(s, 'bertani') >= 2,
                       70, 12, lambda s: _lvl(s, 'bertani') < 2),
    'skill_masak':    ("Memasak level 2", lambda s: _lvl(s, 'memasak') >= 2,
                       70, 12, lambda s: _lvl(s, 'memasak') < 2),
    'punya_teman':    ("Punya 1 teman (3 hati)", lambda s: _friends_at_least(s, 3.0) >= 1,
                       75, 15, lambda s: _friends_at_least(s, 3.0) < 1),
    'sahabat':        ("Punya sahabat (5 hati)", lambda s: _friends_at_least(s, 5.0) >= 1,
                       110, 18, lambda s: _friends_at_least(s, 5.0) < 1),
    'kaya_300':       ("Kumpulkan 300 Simoleon", lambda s: s.gold >= 300,
                       60, 10, lambda s: s.gold < 300),
    'rumah_ramai':    ("Ajak seseorang tinggal bersama",
                       lambda s: len(getattr(s, 'household', []) or []) >= 1,
                       120, 20, lambda s: len(getattr(s, 'household', []) or []) < 1),
    'beli_perabot':   ("Beli 1 perabot",
                       lambda s: sum(len(v) for v in (getattr(s, 'placed_objects', {}) or {}).values()) >= 1,
                       65, 12,
                       lambda s: sum(len(v) for v in (getattr(s, 'placed_objects', {}) or {}).values()) < 1),
    'bersih_diri':    ("Jaga kebersihan di atas 70", lambda s: s.bersih >= 70,
                       45, 8, lambda s: True),
}


# ── ASPIRASI HIDUP ────────────────────────────────────────────────────────
# id → (label, deskripsi, syarat(state)->bool, hadiah_gold, gelar)
ASPIRATIONS = {
    'juragan':   ("Juragan Tani", "Capai pangkat tertinggi di kariermu",
                  lambda s: int(getattr(s, 'career_level', 0)) >= 3, 1200, "Sang Juragan"),
    'ahli':      ("Ahli Serba Bisa", "Tiga skill mencapai level 5",
                  lambda s: sum(1 for k in ('bertani', 'memasak', 'logika', 'kebugaran',
                                            'karisma', 'kerajinan') if _lvl(s, k) >= 5) >= 3,
                  1000, "Sang Ahli"),
    'dicintai':  ("Dicintai Sedesa", "Punya 4 sahabat (5 hati)",
                  lambda s: _friends_at_least(s, 5.0) >= 4, 900, "Kesayangan Desa"),
    'hartawan':  ("Hartawan", "Kumpulkan 5000 Simoleon",
                  lambda s: s.gold >= 5000, 800, "Sang Hartawan"),
    'keluarga':  ("Rumah Penuh", "Rumah tangga berisi 4 orang",
                  lambda s: 1 + len(getattr(s, 'household', []) or []) >= 4,
                  1100, "Kepala Keluarga"),
}


# ── KEINGINAN: pembuatan & pemeriksaan ────────────────────────────────────
def _wants(state) -> list:
    if getattr(state, 'wants', None) is None:
        state.wants = []
    return state.wants


def roll_wants(state):
    """Susun ulang daftar keinginan harian (hanya yang RELEVAN dgn keadaan)."""
    pool = [wid for wid, w in WANTS.items() if w[4](state) and not w[1](state)]
    pool.sort()                                     # deterministik → mudah diuji
    state.wants = pool[:WANT_SLOTS]
    return list(state.wants)


def check_wants(state):
    """Periksa keinginan yang baru terpenuhi. Return list (label, gold).

    Hadiah langsung diberikan (emas + rasa senang).
    """
    done = []
    for wid in list(_wants(state)):
        w = WANTS.get(wid)
        if not w:
            _wants(state).remove(wid)
            continue
        if w[1](state):
            state.gold += w[2]
            state.senang = min(NEED_MAX, state.senang + w[3])
            _wants(state).remove(wid)
            state.wants_done = int(getattr(state, 'wants_done', 0)) + 1
            done.append((w[0], w[2]))
    return done


def want_lines(state):
    """Teks keinginan untuk UI."""
    return [f"{WANTS[w][0]}  (+{WANTS[w][2]}G)" for w in _wants(state) if w in WANTS]


# ── ASPIRASI ──────────────────────────────────────────────────────────────
def set_aspiration(state, aid: str) -> bool:
    if aid not in ASPIRATIONS:
        return False
    state.aspiration = aid
    return True


def aspiration_info(state):
    aid = getattr(state, 'aspiration', '')
    return ASPIRATIONS.get(aid)


def check_aspiration(state):
    """Return (label, gold, gelar) bila BARU tuntas, else None."""
    if getattr(state, 'aspiration_done', False):
        return None
    info = aspiration_info(state)
    if not info:
        return None
    label, _desc, cond, gold, title = info
    if cond(state):
        state.aspiration_done = True
        state.gold += gold
        state.title = title
        return label, gold, title
    return None


def aspiration_line(state) -> str:
    info = aspiration_info(state)
    if not info:
        return "Aspirasi: belum dipilih"
    label, desc, cond, gold, _t = info
    mark = "TUNTAS" if getattr(state, 'aspiration_done', False) else \
           ("siap!" if cond(state) else "berjalan")
    return f"Aspirasi: {label} — {desc} [{mark}]"
