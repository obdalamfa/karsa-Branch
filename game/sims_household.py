"""sims_household.py — RUMAH TANGGA & SIMOLEON ala The Sims (milestone S8).

The Sims bukan tentang satu orang: kamu mengelola RUMAH TANGGA — beberapa
Sim berbagi satu dompet, satu rumah, dan tagihan yang datang tiap beberapa
hari. Modul ini menutup MVP dgn:

  ANGGOTA   — NPC yang sudah cukup dekat bisa diajak PINDAH ke rumahmu.
              Anggota ikut menanggung & menyumbang.
  DOMPET    — state.gold dipakai bersama (Simoleon rumah tangga).
  TAGIHAN   — datang tiap BILL_INTERVAL hari; besarnya ikut jumlah anggota
              dan objek yang kamu beli (rumah mewah = tagihan besar).
  SUMBANGAN — anggota yang bekerja menyetor sebagian penghasilan tiap hari.

Terhubung: relasi (S5) sbg syarat pindah, karier (S6) sbg sumber sumbangan,
placed_objects (S7) sbg dasar tagihan, advance_day sbg detak harian.
"""
from .sims_relationship import friendship, MAX_REL

# Syarat mengajak seseorang pindah: harus benar-benar dekat
MOVE_IN_MIN_FRIENDSHIP = 6.0
MAX_HOUSEHOLD = 4                 # termasuk pemain

BILL_INTERVAL_DAYS = 5            # tagihan tiap 5 hari
BILL_BASE = 40                    # dasar per rumah tangga
BILL_PER_MEMBER = 25              # tiap anggota tambahan
BILL_PER_OBJECT = 6               # tiap objek yang dibeli (listrik/perawatan)

MEMBER_DAILY_CONTRIB = 18         # setoran harian tiap anggota


def members(state) -> list:
    """Anggota rumah tangga selain pemain (list npc_id)."""
    if getattr(state, 'household', None) is None:
        state.household = []
    return state.household


def household_size(state) -> int:
    return 1 + len(members(state))


def can_move_in(state, npc_id: str):
    """(boleh, alasan_bila_tidak)."""
    if npc_id in members(state):
        return False, "Dia sudah tinggal bersamamu."
    if household_size(state) >= MAX_HOUSEHOLD:
        return False, f"Rumah penuh (maks {MAX_HOUSEHOLD} orang)."
    f = friendship(state, npc_id)
    if f < MOVE_IN_MIN_FRIENDSHIP:
        return False, (f"Belum cukup dekat ({f:.1f}/{MOVE_IN_MIN_FRIENDSHIP:.0f} hati).")
    return True, None


def move_in(state, npc_id: str):
    """Ajak pindah. Return (sukses, pesan)."""
    ok, why = can_move_in(state, npc_id)
    if not ok:
        return False, why
    members(state).append(npc_id)
    return True, f"{npc_id} kini tinggal bersamamu. Rumah tangga: {household_size(state)} orang."


def move_out(state, npc_id: str):
    """Anggota pindah keluar. Return (sukses, pesan)."""
    if npc_id not in members(state):
        return False, "Dia bukan anggota rumah tanggamu."
    members(state).remove(npc_id)
    return True, f"{npc_id} pindah keluar. Rumah tangga: {household_size(state)} orang."


def object_count(state) -> int:
    """Jumlah objek yang dibeli pemain di semua scene (dasar tagihan)."""
    rec = getattr(state, 'placed_objects', None) or {}
    return sum(len(v) for v in rec.values())


def bill_amount(state) -> int:
    """Besar tagihan berikutnya."""
    return int(BILL_BASE
               + BILL_PER_MEMBER * len(members(state))
               + BILL_PER_OBJECT * object_count(state))


def daily_contribution(state) -> int:
    """Setoran harian dari anggota rumah tangga."""
    return MEMBER_DAILY_CONTRIB * len(members(state))


def tick_day(state):
    """Dipanggil dari advance_day. Return dict ringkasan untuk UI, atau None.

    Urutan: anggota menyetor dulu, lalu tagihan bila jatuh tempo.
    """
    if getattr(state, 'household', None) is None:
        state.household = []
    contrib = daily_contribution(state)
    if contrib:
        state.gold += contrib

    days = int(getattr(state, 'bill_days', 0)) + 1
    bill = 0
    unpaid = False
    if days >= BILL_INTERVAL_DAYS:
        days = 0
        bill = bill_amount(state)
        if state.gold >= bill:
            state.gold -= bill
        else:
            # Tak mampu bayar: sisa jadi utang (gold boleh 0, tak minus)
            unpaid = True
            state.unpaid_bills = int(getattr(state, 'unpaid_bills', 0)) + (bill - state.gold)
            state.gold = 0
    state.bill_days = days
    if not contrib and not bill:
        return None
    return {'contrib': contrib, 'bill': bill, 'unpaid': unpaid,
            'size': household_size(state), 'objects': object_count(state)}


def summary(state) -> str:
    """Ringkasan untuk UI."""
    n = household_size(state)
    nm = ', '.join(members(state)) if members(state) else 'sendiri'
    nxt = BILL_INTERVAL_DAYS - int(getattr(state, 'bill_days', 0))
    return (f"Rumah tangga {n} orang ({nm}) - tagihan berikut "
            f"{bill_amount(state)}G dlm {nxt} hari")
