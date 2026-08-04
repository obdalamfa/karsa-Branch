"""sims_objects.py — Katalog OBJEK-BERAKSI ala The Sims (milestone S2).

Konsep inti Sims: objek "MENGIKLANKAN" (advertise) seberapa besar ia bisa
memenuhi sebuah motif. Sim memilih objek dengan skor iklan tertinggi:

    skor = bobot_pemenuhan * kekurangan_motif

Jadi ranjang (energi +45) sangat menarik saat energi 10, tapi hampir tak
menarik saat energi 95 — persis seperti The Sims.

Dipakai oleh:
- game/controllers/sims_action_controller.py (jalankan aksi + isi motif)
- (S3) autonomi: pilih objek terbaik utk motif terendah

Motif memakai NAMA FIELD GameState (lapar/sosial/senang/kandung/bersih/energy)
supaya bisa langsung di-setattr tanpa tabel terjemahan.
"""
from .config import (BD, ST, TV, CHR, BS, FP, MR, TB, KLK, WC, SWR,
                     NEED_MAX)

# tile_id → definisi objek.
#   label   : nama objek (untuk UI)
#   action  : nama interaksi (kata kerja, untuk UI)
#   motives : {field_state: delta_total} — diberikan BERTAHAP selama durasi
#   dur     : durasi aksi dalam DETIK REAL
#   anim    : pose/animasi yang dimainkan (opsional; dipakai bila ada)
SIMS_OBJECTS = {
    BD:  {'label': 'Ranjang',   'action': 'Tidur',        'dur': 6.0,
          'motives': {'energy': 60.0},                     'anim': 'sleep'},
    WC:  {'label': 'Toilet',    'action': 'Pakai Toilet', 'dur': 2.5,
          'motives': {'kandung': 95.0},                    'anim': 'sit'},
    SWR: {'label': 'Pancuran',  'action': 'Mandi',        'dur': 4.0,
          'motives': {'bersih': 85.0, 'senang': 5.0},      'anim': 'stand'},
    KLK: {'label': 'Kulkas',    'action': 'Ambil Makanan','dur': 2.0,
          'motives': {'lapar': 35.0},                      'anim': 'bend'},
    ST:  {'label': 'Kompor',    'action': 'Masak',        'dur': 4.5,
          'motives': {'lapar': 55.0},                      'anim': 'bend'},
    TB:  {'label': 'Meja Makan','action': 'Makan',        'dur': 3.0,
          'motives': {'lapar': 30.0, 'sosial': 8.0},       'anim': 'sit'},
    TV:  {'label': 'Televisi',  'action': 'Nonton TV',    'dur': 5.0,
          'motives': {'senang': 40.0},                     'anim': 'sit'},
    BS:  {'label': 'Rak Buku',  'action': 'Baca Buku',    'dur': 5.0,
          'motives': {'senang': 25.0},                     'anim': 'stand'},
    FP:  {'label': 'Perapian',  'action': 'Menghangatkan','dur': 4.0,
          'motives': {'senang': 18.0, 'energy': 8.0},      'anim': 'stand'},
    CHR: {'label': 'Kursi',     'action': 'Duduk',        'dur': 3.0,
          'motives': {'energy': 15.0, 'senang': 6.0},      'anim': 'sit'},
    MR:  {'label': 'Cermin',    'action': 'Berdandan',    'dur': 3.0,
          'motives': {'bersih': 20.0, 'senang': 6.0},      'anim': 'stand'},
}

# Semua motif yang bisa diiklankan objek (untuk validasi & autonomi S3)
MOTIVE_FIELDS = ('lapar', 'sosial', 'senang', 'kandung', 'bersih', 'energy')


def motive_value(state, field: str) -> float:
    """Nilai motif saat ini (energy dinormalkan ke skala 0-100)."""
    if field == 'energy':
        mx = max(getattr(state, 'max_energy', 100) or 100, 1)
        return float(getattr(state, 'energy', 0)) / mx * NEED_MAX
    return float(getattr(state, field, NEED_MAX))


def advertise_score(tile_id: int, state) -> float:
    """Skor iklan objek utk Sim dgn kondisi motif `state` sekarang.

    Makin besar KEKURANGAN motif & makin besar pemenuhan objek → makin menarik.
    Return 0.0 bila objek tak dikenal / tak menawarkan apa pun yang dibutuhkan.
    """
    obj = SIMS_OBJECTS.get(tile_id)
    if not obj:
        return 0.0
    score = 0.0
    for field, fill in obj['motives'].items():
        deficit = max(0.0, NEED_MAX - motive_value(state, field))
        score += (fill / NEED_MAX) * deficit
    return score


def best_motive(state) -> str:
    """Motif paling mendesak (nilai terendah) — dasar autonomi S3."""
    return min(MOTIVE_FIELDS, key=lambda f: motive_value(state, f))


def objects_in_scene(world, limit_ids=None):
    """Scan grid tile scene aktif → [(tile_id, tx, ty)] semua objek Sims.

    Memakai world.scene_obj.tiles (grid yang sama dipakai render & pathfinding).
    """
    sc = getattr(world, 'scene_obj', None)
    if sc is None:
        return []
    found = []
    for ty in range(sc.h):
        row = sc.tiles[ty]
        for tx in range(sc.w):
            tid = row[tx]
            if tid in SIMS_OBJECTS and (limit_ids is None or tid in limit_ids):
                found.append((tid, tx, ty))
    return found


def find_best_object(world, state, motive: str = None, from_tile=None):
    """Objek terbaik untuk dipakai sekarang.

    motive    : bila diberikan, hanya objek yang memenuhi motif itu.
    from_tile : (tx,ty) posisi Sim — dipakai sbg pemecah-seri (yang terdekat).
    Return (tile_id, tx, ty, skor) atau None.
    """
    best = None
    for tid, tx, ty in objects_in_scene(world):
        obj = SIMS_OBJECTS[tid]
        if motive and motive not in obj['motives']:
            continue
        score = advertise_score(tid, state)
        if score <= 0.0:
            continue
        if from_tile:                       # dekat sedikit lebih menarik
            dist = abs(tx - from_tile[0]) + abs(ty - from_tile[1])
            score -= dist * 0.35
        if best is None or score > best[3]:
            best = (tid, tx, ty, score)
    return best
