"""keahlian.py — Satu keahlian bawaan yang dipilih di layar Buat Karakter.

Tiap keahlian punya efek nyata di satu titik kode yang memang dipakai
permainan (bukan angka di layar saja). Disimpan di state.char_perk.
"""

KEAHLIAN = [
    ('kerbau',   'Tenaga Kerbau',   'Semua kerja makan energi 25% lebih sedikit.'),
    ('pedagang', 'Lidah Pedagang',  'Hasil panen dan barang laku 10% lebih mahal.'),
    ('ramah',    'Ramah Tamah',     'Hadiah menaikkan hati warga 50% lebih banyak.'),
    ('kijang',   'Kaki Kijang',     'Berjalan 15% lebih cepat.'),
    ('tangguh',  'Badan Tangguh',   'Energi dan HP maksimum +20.'),
    ('pancing',  'Sabar Memancing', 'Melempar kail hanya separuh energi.'),
]


def kode(state) -> str:
    i = getattr(state, 'char_perk', 0) or 0
    return KEAHLIAN[i % len(KEAHLIAN)][0]


def punya(state, k: str) -> bool:
    return state is not None and kode(state) == k


def terapkan_awal(state, player=None):
    """Efek yang berupa nilai dasar: dipanggil saat karakter dikonfirmasi
    dan saat game dimuat. Idempoten -- memakai penanda supaya bonus maksimum
    tidak ditambahkan dua kali."""
    sudah = getattr(state, 'keahlian_terpasang', '') or None
    k = kode(state)
    if sudah != k:
        if sudah == 'tangguh':
            state.max_energy -= 20
            state.max_hp -= 20
        if k == 'tangguh':
            state.max_energy += 20
            state.max_hp += 20
            state.energy = min(state.energy + 20, state.max_energy)
            state.hp = min(state.hp + 20, state.max_hp)
        state.keahlian_terpasang = k
    from . import economy
    economy.PENGALI_JUAL = 1.10 if k == 'pedagang' else 1.0
    if player is not None:
        from .config import PLAYER_SPEED
        player.speed = PLAYER_SPEED * (1.15 if k == 'kijang' else 1.0)
