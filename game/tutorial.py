"""
tutorial.py — Rantai tutorial "Lima Menit Pertama" (ROADMAP M1).

Langkah-langkah pemandu pemain baru sampai panen pertama. Predikat membaca
state yang SUDAH ADA (stats/inventory/day) — tidak menambah field state,
sehingga kompatibel dengan save lama (semua langkah otomatis selesai).

Dipakai oleh panels.py (objective tracker di HUD kiri-atas).
"""
from .data import QUEST_STAGES


# Tiap langkah: id, label singkat, hint lokasi/cara, dan salah satu dari:
#   done(s)  -> bool                  (langkah selesai?)
#   prog(s)  -> (sekarang, target)    (progress numerik; selesai bila >= target)
TUTORIAL_STEPS = [
    {
        'id': 'surat',
        'label': 'Baca surat Paman Arsa',
        'hint': 'Kotak pos ada di depan rumah - dekati lalu tekan [R]',
        'done': lambda s: bool(getattr(s, 'mail_read', False)),
    },
    {
        'id': 'cangkul',
        'label': 'Cangkul 3 petak tanah',
        'hint': 'Pilih Cangkul [1], hadap tanah kosong, tekan [SPACE]',
        'prog': lambda s: (s.stats.get('tilled', 0), 3),
    },
    {
        'id': 'tanam',
        'label': 'Tanam 3 benih lobak',
        'hint': 'Pilih Tanam [3] di petak yang sudah dicangkul, tekan [SPACE]',
        'prog': lambda s: (s.stats.get('lobak_planted', 0), 3),
    },
    {
        'id': 'siram',
        'label': 'Siram 3 petak',
        'hint': 'Pilih Siram [2], hadap petak tanaman, tekan [SPACE]',
        'prog': lambda s: (s.stats.get('watered', 0), 3),
    },
    {
        'id': 'tidur',
        'label': 'Tidur untuk ganti hari',
        'hint': 'Masuk rumah, berdiri di kasur, tekan [R]',
        'done': lambda s: getattr(s, 'day', 1) >= 2,
    },
    {
        'id': 'panen',
        'label': 'Panen lobak pertamamu',
        'hint': 'Lobak siap dalam beberapa hari - pilih Panen [4] lalu [SPACE]',
        'done': lambda s: s.stats.get('lobak_harvested', 0) >= 1,
    },
    {
        'id': 'kirim',
        'label': 'Kirim hasil ke Peti & tidur untuk dapat emas',
        'hint': 'Bawa panen ke Peti Kirim (tanda kuning) dekat rumah, tekan [R], lalu tidur [T]',
        'done': lambda s: s.stats.get('earned', 0) > 0,
    },
]


def _step_done(step, s) -> bool:
    try:
        if 'done' in step:
            return bool(step['done'](s))
        cur, target = step['prog'](s)
        return cur >= target
    except Exception:
        return False


def current_step(s):
    """Langkah tutorial aktif pertama yang belum selesai, atau None bila tamat."""
    for i, step in enumerate(TUTORIAL_STEPS):
        if not _step_done(step, s):
            return i, step
    return None


def tracker_lines(s):
    """(judul, baris_objektif, hint) untuk widget tracker HUD.

    Selama tutorial: tampilkan langkah ke-N. Setelah tamat: tampilkan
    quest utama aktif dari QUEST_STAGES (sistem yang sudah ada).
    """
    cur = current_step(s)
    if cur is not None:
        i, step = cur
        label = step['label']
        if 'prog' in step:
            try:
                now, target = step['prog'](s)
                label = f"{label}  ({min(now, target)}/{target})"
            except Exception:
                pass
        return (f"TUTORIAL  {i + 1}/{len(TUTORIAL_STEPS)}", label, step.get('hint', ''))

    stage = min(getattr(s, 'quest_stage', 0), len(QUEST_STAGES) - 1)
    q = QUEST_STAGES[stage]
    return (f"QUEST - {q['t']}", q['d'], '')
