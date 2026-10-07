"""sims_relationship.py — RELASI dua-meter ala The Sims (milestone S5).

The Sims memisahkan dua hubungan yang berbeda:
    PERSAHABATAN (friendship) — tumbuh dari ngobrol, hadiah, perhatian
    ASMARA       (romance)    — tumbuh dari gombal/rayuan, TAPI butuh modal
                                persahabatan dulu (tak bisa merayu orang asing)

Kompatibilitas: meter persahabatan MEMAKAI ULANG `state.npc_hearts` yang sudah
ada (0-10) — semua gate lama (dialog, hadiah lore, pie menu) tetap berlaku.
Asmara memakai dict baru `state.npc_romance`.

Relasi juga MELUNTUR bila diabaikan (dipanggil dari advance_day), sehingga
pertemanan perlu dirawat — bukan sekadar angka yang naik selamanya.
"""
from .config import NEED_MAX  # noqa: F401  (dipakai pemanggil)

MAX_REL = 10.0

# ambang → label (dicek dari yang tertinggi)
FRIEND_LEVELS = (
    (8.0, 'Sahabat Karib'),
    (5.0, 'Sahabat'),
    (3.0, 'Teman'),
    (1.0, 'Kenalan'),
    (0.0, 'Orang Asing'),
)
ROMANCE_LEVELS = (
    (8.0, 'Kekasih'),
    (5.0, 'Pacar'),
    (3.0, 'Dekat'),
    (1.0, 'Naksir'),
    (0.0, '—'),
)

# Asmara butuh modal persahabatan (aturan Sims: kenal dulu, baru merayu)
ROMANCE_MIN_FRIENDSHIP = 3.0

# Peluruhan per hari bila TIDAK ada interaksi (asmara luntur lebih cepat)
DECAY_FRIEND_PER_DAY  = 0.15
DECAY_ROMANCE_PER_DAY = 0.25
# Hari tanpa interaksi sebelum mulai luntur (masa tenggang)
DECAY_GRACE_DAYS = 2


def _lvl(table, value: float) -> str:
    for threshold, label in table:
        if value >= threshold:
            return label
    return table[-1][1]


def friendship(state, npc_id: str) -> float:
    return float(state.npc_hearts.get(npc_id, 0))


def romance(state, npc_id: str) -> float:
    return float(getattr(state, 'npc_romance', {}).get(npc_id, 0))


def friend_label(state, npc_id: str) -> str:
    return _lvl(FRIEND_LEVELS, friendship(state, npc_id))


def romance_label(state, npc_id: str) -> str:
    return _lvl(ROMANCE_LEVELS, romance(state, npc_id))


def _touch(state, npc_id: str):
    """Catat hari interaksi terakhir (dasar peluruhan)."""
    if getattr(state, 'npc_last_social', None) is None:
        state.npc_last_social = {}
    state.npc_last_social[npc_id] = int(getattr(state, 'day', 1))


def add_friendship(state, npc_id: str, base: float) -> float:
    """Naikkan persahabatan, diskala MOOD (S4). Return delta nyata."""
    from .sims_mood import mood_social_bonus
    delta = max(0.05, base * (1.0 + mood_social_bonus(state) / 100.0))
    state.npc_hearts[npc_id] = min(MAX_REL, friendship(state, npc_id) + delta)
    _touch(state, npc_id)
    return delta


def can_romance(state, npc_id: str) -> bool:
    """Boleh merayu? Perlu modal persahabatan lebih dulu."""
    return friendship(state, npc_id) >= ROMANCE_MIN_FRIENDSHIP


def add_romance(state, npc_id: str, base: float):
    """Coba naikkan asmara. Return (berhasil, delta, pesan).

    Gagal bila belum cukup akrab — dan itu MENURUNKAN sedikit persahabatan
    (canggung), persis konsekuensi rayuan prematur di The Sims.
    """
    from .sims_mood import mood_social_bonus
    if getattr(state, 'npc_romance', None) is None:
        state.npc_romance = {}
    if not can_romance(state, npc_id):
        state.npc_hearts[npc_id] = max(0.0, friendship(state, npc_id) - 0.3)
        _touch(state, npc_id)
        return False, -0.3, "Terlalu cepat — kalian belum cukup akrab."
    delta = max(0.05, base * (1.0 + mood_social_bonus(state) / 100.0))
    state.npc_romance[npc_id] = min(MAX_REL, romance(state, npc_id) + delta)
    _touch(state, npc_id)
    return True, delta, None


def decay_relationships(state):
    """Luntur harian bila diabaikan. Dipanggil dari TimeController.advance_day.

    Return jumlah relasi yang meluntur (untuk uji/umpan balik).
    """
    if getattr(state, 'npc_last_social', None) is None:
        state.npc_last_social = {}
    if getattr(state, 'npc_romance', None) is None:
        state.npc_romance = {}
    today = int(getattr(state, 'day', 1))
    faded = 0
    for npc_id in set(list(state.npc_hearts.keys()) + list(state.npc_romance.keys())):
        last = state.npc_last_social.get(npc_id)
        if last is None:
            state.npc_last_social[npc_id] = today   # mulai hitung dari sekarang
            continue
        if today - last <= DECAY_GRACE_DAYS:
            continue
        f = friendship(state, npc_id)
        r = romance(state, npc_id)
        if f > 0:
            state.npc_hearts[npc_id] = max(0.0, f - DECAY_FRIEND_PER_DAY)
            faded += 1
        if r > 0:
            state.npc_romance[npc_id] = max(0.0, r - DECAY_ROMANCE_PER_DAY)
            faded += 1
    return faded


def summary(state, npc_id: str) -> str:
    """Ringkasan relasi untuk UI: 'Teman 3.5❤ · Naksir 1.2♥'."""
    f, r = friendship(state, npc_id), romance(state, npc_id)
    txt = f"{friend_label(state, npc_id)} {f:.1f}"
    if r > 0:
        txt += f" · {romance_label(state, npc_id)} {r:.1f}"
    return txt
