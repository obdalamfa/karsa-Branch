"""fishing.py — Memancing yang punya jawaban untuk "di mana, dan kapan".

Apa yang ada sebelum ini, seluruhnya:

    if random.random() < 0.55:
        s.inventory['ikan'] += 1

Satu lemparan koin, satu jenis ikan, angka yang sama di danau tengah hari
musim panas maupun di pantai tengah malam musim dingin badai. Tidak ada satu
pun keadaan dunia yang mengubah hasilnya, jadi tidak ada satu pun alasan untuk
memilih tempat, jam, atau cuaca. Dermaga jadi tombol, bukan tempat.

Modul ini menambahkan tiga hal, dan sengaja hanya tiga:

1. **Spesies yang terikat keadaan.** Tiap ikan punya perairan, musim, jam,
   cuaca, dan — di pantai — pasang-surutnya sendiri. Kepiting bakau hanya
   muncul saat air surut; ikan layur hanya di malam musim dingin yang berbadai.
   Yang membuat ini bekerja bukan jumlah spesiesnya, tapi kenyataan bahwa
   sebagian besar spesies TIDAK tersedia pada satu waktu tertentu: papan
   pilihan yang selalu penuh sama tidak berartinya dengan papan yang kosong.

2. **Jendela gigitan.** Melempar dan menarik dipisah. Umpan menggantung
   beberapa detik, ikan menggigit, dan pemain punya jendela pendek untuk
   menyentak. Ini satu-satunya bagian yang mengubah memancing dari transaksi
   jadi kejadian — dan ia gratis, karena tidak butuh UI baru sama sekali,
   cuma teks yang sudah ada.

3. **Ukuran.** Tiap tangkapan punya berat, dan beratnya mengalikan harga.
   Rekor pribadi per spesies disimpan di `state.fish_log`. Ini yang membuat
   ikan mas ke-lima-puluh masih layak dilihat.

Kelimpahan kolam (`ecology.py`) mengalikan peluang gigitan, dan tiap tangkapan
mengurangi kolamnya. Jadi danau yang digiling benar-benar terasa mati — bukan
lewat pesan, lewat pelampung yang diam.

Tidak mengimpor Ursina. Semua fungsi di sini menerima `state` dan mengembalikan
data; yang menggambar dan berbunyi ada di interaction_controller.
"""
from __future__ import annotations

import random

from .ecology import (abundance, take, tide_is_low, tide_fish_bonus,
                      yield_multiplier)

# ─────────────────────────────────────────────────────────────────────────────
# PERAIRAN
#
# Tiap perairan memetakan ke satu kolam ekologi. Pemetaan ini sengaja di sini
# dan bukan di ecology.py: ecology tahu tentang KOLAM, fishing tahu tentang
# TEMPAT, dan yang menghubungkan keduanya adalah aturan permainan.
# ─────────────────────────────────────────────────────────────────────────────

AIR_DANAU  = 'danau'
AIR_PANTAI = 'pantai'
AIR_GUA    = 'gua'

STOK_PERAIRAN = {
    AIR_DANAU:  'ikan_danau',
    AIR_PANTAI: 'ikan_pantai',
    AIR_GUA:    'ikan_gua',
}


def perairan_untuk(state, world=None) -> str:
    """Perairan mana yang sedang dipancing pemain.

    Danau di dasar gua hanya ada di lantai terakhir dungeon; sisanya dibedakan
    per scene. Scene tak dikenal yang punya air diperlakukan sebagai danau —
    lebih baik memberi tangkapan biasa daripada menolak diam-diam.
    """
    scene = getattr(state, 'scene_name', '')
    if scene == 'dungeon' and getattr(world, 'dungeon_level', 0) == 13:
        return AIR_GUA
    if scene == 'beach':
        return AIR_PANTAI
    return AIR_DANAU


# ─────────────────────────────────────────────────────────────────────────────
# SPESIES
#
# `air`     perairan tempat ia hidup
# `musim`   None = sepanjang tahun, atau daftar nama musim
# `jam`     None = kapan saja, atau (mulai, selesai) jam 0-23; melewati tengah
#           malam ditulis dengan mulai > selesai, mis. (19, 4)
# `cuaca`   None = cuaca apa pun, atau daftar
# `pasang`  None = tak peduli, 'surut' = hanya saat air surut
# `bobot`   kelangkaan relatif DI ANTARA yang sedang tersedia
# `kg`      (min, maks) berat; harga dikalikan berat/berat_tengah
# ─────────────────────────────────────────────────────────────────────────────

SPESIES: dict[str, dict] = {
    # ── DANAU KARSA ──────────────────────────────────────
    # `ikan` yang lama dipertahankan sebagai tangkapan paling umum. Menghapusnya
    # akan mematahkan quest dan save yang menyebut namanya, dan tangkapan biasa
    # yang tidak istimewa memang perlu ada — tanpa dasar yang membosankan,
    # tidak ada yang terasa langka.
    'ikan':            {'air': AIR_DANAU,  'musim': None, 'jam': None,
                        'cuaca': None, 'pasang': None, 'bobot': 34, 'kg': (0.3, 1.4)},
    'ikan_mas':        {'air': AIR_DANAU,  'musim': None, 'jam': (5, 18),
                        'cuaca': None, 'pasang': None, 'bobot': 22, 'kg': (0.5, 3.0)},
    'ikan_nila':       {'air': AIR_DANAU,  'musim': ['Semi', 'Panas'], 'jam': (5, 18),
                        'cuaca': None, 'pasang': None, 'bobot': 18, 'kg': (0.4, 2.0)},
    'ikan_gabus':      {'air': AIR_DANAU,  'musim': None, 'jam': (19, 4),
                        'cuaca': None, 'pasang': None, 'bobot': 12, 'kg': (0.8, 4.5)},
    'belut':           {'air': AIR_DANAU,  'musim': None, 'jam': (19, 4),
                        'cuaca': ['Hujan', 'Badai'], 'pasang': None, 'bobot': 8, 'kg': (0.4, 2.2)},
    'udang_galah':     {'air': AIR_DANAU,  'musim': ['Panas'], 'jam': (4, 9),
                        'cuaca': None, 'pasang': None, 'bobot': 9, 'kg': (0.1, 0.6)},

    # ── PANTAI SELATAN ───────────────────────────────────
    'ikan_kembung':    {'air': AIR_PANTAI, 'musim': None, 'jam': None,
                        'cuaca': None, 'pasang': None, 'bobot': 30, 'kg': (0.2, 0.9)},
    'ikan_kakap':      {'air': AIR_PANTAI, 'musim': ['Panas', 'Gugur'], 'jam': (15, 20),
                        'cuaca': None, 'pasang': None, 'bobot': 14, 'kg': (1.0, 6.0)},
    'cumi':            {'air': AIR_PANTAI, 'musim': None, 'jam': (19, 4),
                        'cuaca': None, 'pasang': None, 'bobot': 16, 'kg': (0.2, 1.5)},
    # Satu-satunya spesies yang gerbangnya adalah pasang-surut. Ia yang membuat
    # `tide_phase()` jadi sesuatu yang pemain periksa, bukan hiasan panel.
    'kepiting_bakau':  {'air': AIR_PANTAI, 'musim': None, 'jam': None,
                        'cuaca': None, 'pasang': 'surut', 'bobot': 15, 'kg': (0.3, 1.8)},
    'ikan_layur':      {'air': AIR_PANTAI, 'musim': ['Dingin'], 'jam': (19, 4),
                        'cuaca': ['Hujan', 'Badai'], 'pasang': None, 'bobot': 7, 'kg': (0.6, 3.5)},

    # ── DANAU DASAR GUA ──────────────────────────────────
    'ikan_buta':       {'air': AIR_GUA,    'musim': None, 'jam': None,
                        'cuaca': None, 'pasang': None, 'bobot': 30, 'kg': (0.2, 1.1)},
    'ikan_legendaris': {'air': AIR_GUA,    'musim': None, 'jam': None,
                        'cuaca': None, 'pasang': None, 'bobot': 4,  'kg': (8.0, 24.0)},
}

# Peluang dasar ada yang menggigit sama sekali, sebelum dikalikan kelimpahan
# dan bonus pasang. Sengaja sedikit di atas 0,55 yang lama: memancing sekarang
# memakan waktu nyata (jendela gigitan), jadi tiap lemparan harus lebih sering
# berbuah supaya total kesabarannya tidak justru bertambah.
PELUANG_DASAR = 0.62

# Jendela gigitan, dalam detik nyata.
TUNGGU_MIN    = 1.2    # paling cepat umpan disambar
TUNGGU_MAKS   = 4.5    # paling lama
JENDELA       = 1.1    # berapa lama pemain boleh terlambat menyentak

EN_LEMPAR = 2          # energi per lemparan, sama seperti sebelumnya


def _jam_cocok(jam: int, rentang) -> bool:
    if rentang is None:
        return True
    mulai, selesai = rentang
    if mulai <= selesai:
        return mulai <= jam <= selesai
    return jam >= mulai or jam <= selesai        # melewati tengah malam


def tersedia(state, air: str) -> list[str]:
    """Spesies yang BISA menggigit di sini, sekarang juga.

    Dipakai juga oleh panel dan papan kerja sampingan, supaya tugas 'tangkap
    kepiting bakau' tidak pernah diberikan pada hari yang mustahil.
    """
    jam    = state.get_hour() if hasattr(state, 'get_hour') else 12
    musim  = state.get_season() if hasattr(state, 'get_season') else 'Semi'
    cuaca  = getattr(state, 'weather', 'Cerah')
    surut  = tide_is_low(state)

    keluar = []
    for sid, sp in SPESIES.items():
        if sp['air'] != air:
            continue
        if sp['musim'] is not None and musim not in sp['musim']:
            continue
        if not _jam_cocok(jam, sp['jam']):
            continue
        if sp['cuaca'] is not None and cuaca not in sp['cuaca']:
            continue
        if sp['pasang'] == 'surut' and not surut:
            continue
        keluar.append(sid)
    return keluar


# Jala Ikan (data.py: "Meningkatkan peluang memancing") sudah ada di katalog
# kerajinan jauh sebelum modul ini. Bonusnya dihitung DI SINI dan hanya di sini
# — versi lama menuliskannya langsung di interaction_controller sebagai
# `0.55 + 0.20`, dan begitu peluangnya pindah ke modul sendiri, rumus yang
# tertinggal di controller akan diam-diam menyimpang dari yang dipakai.
BONUS_JALA = 0.20


def peluang_gigit(state, air: str) -> float:
    """Peluang 0..1 bahwa lemparan ini akan disambut gigitan."""
    stok = STOK_PERAIRAN.get(air, 'ikan_danau')
    p = PELUANG_DASAR * yield_multiplier(state, stok)
    if air == AIR_PANTAI:
        # Ikan menggigit paling rajin saat air bergerak, bukan saat diam.
        p *= tide_fish_bonus(state)
    if getattr(state, 'inventory', {}).get('jala', 0) > 0:
        p += BONUS_JALA
    return max(0.05, min(0.95, p))


def tunggu_gigitan(rng=None) -> float:
    """Berapa detik umpan menggantung sebelum disambar."""
    if rng is None:
        rng = random
    return rng.uniform(TUNGGU_MIN, TUNGGU_MAKS)


def pilih_spesies(state, air: str, rng=None) -> str | None:
    """Undi satu spesies dari yang sedang tersedia. None kalau tidak ada."""
    if rng is None:
        rng = random
    kandidat = tersedia(state, air)
    if not kandidat:
        return None
    bobot = [SPESIES[k]['bobot'] for k in kandidat]
    return rng.choices(kandidat, weights=bobot)[0]


def undi_berat(sid: str, rng=None) -> float:
    """Berat satu tangkapan, condong ke ukuran kecil.

    Dua undian dan ambil yang terkecil: ikan besar harus jarang tanpa perlu
    tabel terpisah, dan pemain harus benar-benar terkejut saat dapat yang besar.
    """
    if rng is None:
        rng = random
    lo, hi = SPESIES[sid]['kg']
    return round(min(rng.uniform(lo, hi), rng.uniform(lo, hi)), 2)


def pengali_harga(sid: str, kg: float) -> float:
    """Berat relatif terhadap ukuran tengah, dijepit di 0,6x-2,2x.

    Dijepit supaya satu tangkapan raksasa tidak pernah menggantikan sehari
    bekerja — memancing tetap salah satu jalur uang, bukan lotere.
    """
    lo, hi = SPESIES[sid]['kg']
    tengah = (lo + hi) / 2.0
    if tengah <= 0:
        return 1.0
    return max(0.6, min(2.2, kg / tengah))


def catat_rekor(state, sid: str, kg: float) -> bool:
    """Simpan rekor pribadi. Return True kalau ini rekor baru."""
    log = getattr(state, 'fish_log', None)
    if not isinstance(log, dict):
        log = {}
        state.fish_log = log
    lama = log.get(sid)
    try:
        lama = float(lama)
    except (TypeError, ValueError):
        lama = None
    if lama is None or kg > lama:
        log[sid] = kg
        return True
    return False


def tarik(state, air: str, sid: str, rng=None) -> dict:
    """Selesaikan satu tangkapan: berat, nilai, rekor, dan kurangi kolam.

    Return dict siap dipakai UI: {'id', 'kg', 'nilai', 'rekor'}.
    """
    if rng is None:
        rng = random
    from .market import price as harga_kini

    kg = undi_berat(sid, rng)
    nilai = max(1, int(round(harga_kini(state, sid) * pengali_harga(sid, kg))))
    rekor = catat_rekor(state, sid, kg)

    state.inventory[sid] = state.inventory.get(sid, 0) + 1
    take(state, STOK_PERAIRAN.get(air, 'ikan_danau'), 1)
    return {'id': sid, 'kg': kg, 'nilai': nilai, 'rekor': rekor}


def ringkas_perairan(state, air: str) -> str:
    """Satu baris untuk panel: seberapa hidup air ini sekarang."""
    from .ecology import status_word
    stok = STOK_PERAIRAN.get(air, 'ikan_danau')
    n = len(tersedia(state, air))
    return (f"{status_word(state, stok)} — {n} jenis sedang menggigit "
            f"({int(round(abundance(state, stok) * 100))}% isi)")
