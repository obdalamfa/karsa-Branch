"""ecology.py — Dunia yang bisa habis, dan yang pulih kalau didiamkan.

Kenapa modul ini ada. Sebelum ini setiap sumber daya liar adalah keran tak
terbatas: memancing selalu 55% berhasil sampai kiamat, `respawn_wild_at_morning()`
menempelkan 2-4 herba baru ke `state.wild_entities` **setiap pagi tanpa batas
apa pun** (entities.py) sehingga daftar itu tumbuh selamanya, dan bijih di gua
tidak pernah tahu sudah berapa banyak yang diangkut keluar. Akibatnya tidak ada
satu pun keputusan pemain yang punya ongkos jangka panjang. Memanen berlebihan
tidak merugikan siapa pun, jadi menahan diri juga tidak menguntungkan siapa pun.

Yang dibangun di sini adalah **stok**: kolam angka bernama yang turun saat
dipanen dan naik saat didiamkan.

    stok_besok = stok + r_efektif * stok * (1 - stok/kapasitas) + imigrasi

Itu pertumbuhan logistik, kurva yang sama yang dipakai biolog perikanan. Tiga
sifatnya yang membuatnya layak dipakai di game, bukan cuma benar di kertas:

1. **Kolam penuh tidak tumbuh.** Menahan diri di luar batas tidak memberi
   apa-apa, jadi pemain tidak dihukum karena rajin.
2. **Pemulihan tercepat ada di setengah kapasitas.** Panen berkelanjutan yang
   optimal justru MENGURAS kolam sampai separuh, bukan menjaganya penuh. Ini
   satu-satunya bagian yang berlawanan dengan naluri, dan sengaja dipertahankan
   — ia yang membuat "berapa banyak boleh diambil" jadi pertanyaan sungguhan.
3. **Kolam yang dikuras habis nyaris tidak pulih**, karena suku logistik
   dikalikan stok yang tersisa. Ini mode kegagalan yang nyata dan yang membuat
   seluruh sistem punya taring.

Suku `imigrasi` kecil ditambahkan justru supaya taring itu tidak jadi racun:
tanpanya, stok yang menyentuh nol akan mati permanen dan sebuah save bisa rusak
tanpa bisa diperbaiki. Dengan imigrasi, danau yang dikosongkan tetap pulih —
hanya saja butuh belasan hari, dan pemain merasakan setiap harinya.

Musim, cuaca, dan pasang-surut mengalikan `r`. Ikan berkembang di musim panas
dan hampir berhenti di musim dingin; hujan menyuburkan hutan; badai justru
melempar kerang ke pantai. Semua faktornya ada di satu tempat di bawah supaya
bisa disetel tanpa berburu ke seluruh kode.

Modul ini tidak mengimpor Ursina dan tidak menyentuh dunia 3D. Ia hanya
membaca dan menulis `state`, jadi bisa diuji tanpa membuka jendela.
"""
from __future__ import annotations

import math

# ─────────────────────────────────────────────────────────────────────────────
# DEFINISI STOK
#
# `cap`   kapasitas — angka tertinggi yang dicapai kolam kalau tidak diganggu.
# `r`     laju pemulihan harian pada kondisi netral (musim semi, cerah).
# `jenis` menentukan pengali musim/cuaca mana yang dipakai.
# `label` nama yang dibaca pemain di panel Ekosistem.
# ─────────────────────────────────────────────────────────────────────────────

STOCKS: dict[str, dict] = {
    # ── AIR ──────────────────────────────────────────────
    'ikan_danau':   {'cap': 60,  'r': 0.22, 'jenis': 'ikan',   'label': 'Ikan Danau Karsa'},
    'ikan_pantai':  {'cap': 80,  'r': 0.26, 'jenis': 'ikan',   'label': 'Ikan Pantai Selatan'},
    # Danau di dasar gua tidak kena musim dan tidak kena hujan. Ia pulih paling
    # lambat di seluruh game, dan itulah yang membuat Ikan Legendaris langka
    # tanpa perlu satu pun angka peluang tambahan.
    'ikan_gua':     {'cap': 24,  'r': 0.09, 'jenis': 'gelap',  'label': 'Ikan Danau Legendaris'},

    # ── HUTAN & GUNUNG ───────────────────────────────────
    'herba_gunung': {'cap': 40,  'r': 0.30, 'jenis': 'hijau',  'label': 'Herba & Beri Liar'},
    'jamur_gunung': {'cap': 30,  'r': 0.24, 'jenis': 'hijau',  'label': 'Jamur Lari'},
    'mandrake':     {'cap': 8,   'r': 0.06, 'jenis': 'hijau',  'label': 'Mandrake'},
    'kayu_gunung':  {'cap': 120, 'r': 0.12, 'jenis': 'kayu',   'label': 'Pohon Lereng'},

    # ── PANTAI ───────────────────────────────────────────
    'kerang_pantai':{'cap': 45,  'r': 0.34, 'jenis': 'pasang', 'label': 'Kerang & Damparan'},

    # ── LEMBAH ───────────────────────────────────────────
    'kunang':       {'cap': 50,  'r': 0.40, 'jenis': 'hijau',  'label': 'Kunang-kunang'},

    # ── BAWAH TANAH ──────────────────────────────────────
    # "Pemulihan" bijih bukan batu yang tumbuh; ia adalah lorong baru yang
    # terbuka saat langit-langit runtuh. Karena itu lajunya paling kecil dan
    # tidak peduli musim.
    'bijih_dangkal':{'cap': 200, 'r': 0.16, 'jenis': 'batu',   'label': 'Urat Bijih Lv.1-5'},
    'bijih_tengah': {'cap': 140, 'r': 0.11, 'jenis': 'batu',   'label': 'Urat Bijih Lv.6-10'},
    'bijih_dalam':  {'cap': 90,  'r': 0.07, 'jenis': 'batu',   'label': 'Urat Bijih Lv.11-13'},
}

# Pengali laju pemulihan per musim. Indeks = state.season_index
# (0 Semi, 1 Panas, 2 Gugur, 3 Dingin).
_MUSIM = {
    'ikan':   (1.10, 1.25, 1.00, 0.55),
    'hijau':  (1.35, 1.10, 1.20, 0.30),
    'kayu':   (1.20, 1.00, 0.90, 0.45),
    'pasang': (1.00, 1.20, 1.00, 0.80),
    'batu':   (1.00, 1.00, 1.00, 1.00),
    'gelap':  (1.00, 1.00, 1.00, 1.00),
}

# Pengali laju pemulihan per cuaca kemarin.
_CUACA = {
    'Cerah':    {'hijau': 0.95, 'ikan': 1.00, 'pasang': 1.05},
    'Mendung':  {'hijau': 1.05, 'ikan': 1.05},
    'Hujan':    {'hijau': 1.30, 'ikan': 1.15, 'pasang': 0.80},
    'Berangin': {'hijau': 1.00, 'pasang': 1.15, 'kayu': 0.85},
    # Badai merusak yang hidup di air dangkal tapi melemparkan damparan ke
    # pantai. Satu-satunya cuaca yang menukar satu sumber daya dengan yang lain.
    'Badai':    {'hijau': 1.10, 'ikan': 0.85, 'pasang': 1.60, 'kayu': 0.70},
}

# Berapa banyak stok yang hilang sekali panen. Bukan selalu 1: menebang pohon
# mengambil jauh lebih banyak dari hutan daripada memetik satu beri.
BIAYA_PANEN = {
    'kayu_gunung': 3.0,
    'mandrake':    1.0,
}


def _musim_faktor(jenis: str, season_index: int) -> float:
    tabel = _MUSIM.get(jenis)
    if not tabel:
        return 1.0
    return tabel[season_index % 4]


def _cuaca_faktor(jenis: str, weather: str) -> float:
    return _CUACA.get(weather, {}).get(jenis, 1.0)


# ─────────────────────────────────────────────────────────────────────────────
# AKSES STOK
# ─────────────────────────────────────────────────────────────────────────────

def ensure(state) -> dict:
    """Pastikan `state.eco` ada dan lengkap. Aman dipanggil berkali-kali.

    Save lama tidak punya field ini sama sekali; save yang dibuat sebelum satu
    stok ditambahkan tidak punya kuncinya. Keduanya diisi di sini dengan kolam
    PENUH, bukan kosong — pemain lama tidak boleh dihukum karena dunianya baru
    saja belajar cara habis.
    """
    eco = getattr(state, 'eco', None)
    if not isinstance(eco, dict):
        eco = {}
        state.eco = eco
    for key, spec in STOCKS.items():
        if key not in eco or not isinstance(eco[key], (int, float)):
            eco[key] = float(spec['cap'])
        else:
            eco[key] = max(0.0, min(float(spec['cap']), float(eco[key])))
    return eco


def stock(state, key: str) -> float:
    """Isi kolam sekarang. Kunci tak dikenal mengembalikan 0.0."""
    if key not in STOCKS:
        return 0.0
    return ensure(state).get(key, 0.0)


def capacity(key: str) -> float:
    spec = STOCKS.get(key)
    return float(spec['cap']) if spec else 0.0


def abundance(state, key: str) -> float:
    """Kelimpahan 0.0-1.0. Ini angka yang dibaca semua sistem lain."""
    cap = capacity(key)
    return (stock(state, key) / cap) if cap else 0.0


def take(state, key: str, n: float = 1.0) -> bool:
    """Ambil dari kolam. Return False kalau isinya sudah tidak cukup.

    Pemanggil BOLEH mengabaikan False dan tetap memberi hasil ke pemain — lihat
    `yield_multiplier()`. Yang tidak boleh adalah mengambil tanpa mencatat.
    """
    if key not in STOCKS:
        return True
    eco = ensure(state)
    biaya = n * BIAYA_PANEN.get(key, 1.0)
    if eco[key] < biaya:
        eco[key] = 0.0
        return False
    eco[key] -= biaya
    return True


def give(state, key: str, n: float = 1.0) -> None:
    """Kembalikan ke kolam — melepas ikan, menanam pohon, kandang ternak liar."""
    if key not in STOCKS:
        return
    eco = ensure(state)
    eco[key] = min(capacity(key), eco[key] + n)


def yield_multiplier(state, key: str) -> float:
    """Pengali peluang/hasil berdasarkan kelimpahan, 0.25-1.15.

    Sengaja TIDAK pernah nol. Kolam kosong membuat panen jadi menyedihkan, bukan
    mustahil — pemain harus bisa melihat sendiri bahwa tempat itu sudah habis,
    dan tetap punya jalan pulang. Kolam yang melimpah memberi bonus kecil supaya
    ada alasan mencari tempat yang belum dijamah.
    """
    a = abundance(state, key)
    if a >= 0.85:
        return 1.15
    if a >= 0.55:
        return 1.0
    if a >= 0.30:
        return 0.75
    if a >= 0.12:
        return 0.45
    return 0.25


def status_word(state, key: str) -> str:
    """Satu kata untuk HUD dan panel. Pemain tidak menabung angka desimal."""
    a = abundance(state, key)
    if a >= 0.85:
        return 'Melimpah'
    if a >= 0.55:
        return 'Sehat'
    if a >= 0.30:
        return 'Menipis'
    if a >= 0.12:
        return 'Kritis'
    return 'Habis'


# ─────────────────────────────────────────────────────────────────────────────
# PASANG SURUT
#
# Dua pasang dan dua surut per hari, digeser sedikit tiap hari supaya jam
# terbaiknya bergerak dan pemain harus benar-benar melihat langit, bukan
# menghafal satu jadwal.
# ─────────────────────────────────────────────────────────────────────────────

def tide_level(state) -> float:
    """0.0 = surut terendah, 1.0 = pasang tertinggi."""
    menit = getattr(state, 'time_minutes', 360.0)
    hari  = getattr(state, 'day', 1)
    fase  = ((menit / 1440.0) * 2.0 + hari * 0.13) % 1.0
    return 0.5 - 0.5 * math.cos(2.0 * math.pi * fase)


def tide_phase(state) -> str:
    """'Surut', 'Air Naik', 'Pasang', atau 'Air Turun'."""
    lv = tide_level(state)
    if lv < 0.22:
        return 'Surut'
    if lv > 0.78:
        return 'Pasang'
    # Naik atau turun: lihat sedikit ke depan, bukan turunan analitik — lebih
    # pendek dan tidak bisa salah tanda.
    menit = getattr(state, 'time_minutes', 360.0)
    hari  = getattr(state, 'day', 1)
    fase  = ((menit + 20.0) / 1440.0 * 2.0 + hari * 0.13) % 1.0
    depan = 0.5 - 0.5 * math.cos(2.0 * math.pi * fase)
    return 'Air Naik' if depan > lv else 'Air Turun'


def tide_is_low(state) -> bool:
    """Kolam pasang terbuka. Ini gerbang untuk memungut kerang di pantai."""
    return tide_level(state) < 0.30


def tide_fish_bonus(state) -> float:
    """Ikan menggigit paling rajin saat air bergerak, bukan saat diam.

    Nelayan sungguhan menyebutnya 'running tide'. Di sini ia jadi alasan untuk
    datang ke pantai pada jam tertentu, bukan kapan saja.
    """
    lv = tide_level(state)
    gerak = 1.0 - abs(lv - 0.5) * 2.0   # 1.0 di tengah, 0.0 di puncak/palung
    return 0.85 + 0.35 * gerak


# ─────────────────────────────────────────────────────────────────────────────
# PUTARAN HARIAN
# ─────────────────────────────────────────────────────────────────────────────

def daily_tick(state) -> dict[str, float]:
    """Satu malam pemulihan. Return {kunci: perubahan} untuk laporan pagi.

    Dipanggil dari TimeController.advance_day(), satu kali per hari, SEBELUM
    cuaca hari baru diundi — pertumbuhan semalam ditentukan oleh cuaca yang
    baru saja lewat, bukan yang belum terjadi.
    """
    eco = ensure(state)
    musim  = getattr(state, 'season_index', 0)
    cuaca  = getattr(state, 'weather', 'Cerah')
    delta: dict[str, float] = {}

    for key, spec in STOCKS.items():
        cap = float(spec['cap'])
        cur = float(eco[key])
        jenis = spec['jenis']
        r = float(spec['r']) * _musim_faktor(jenis, musim) * _cuaca_faktor(jenis, cuaca)

        tumbuh   = r * cur * (1.0 - cur / cap) if cap > 0 else 0.0
        imigrasi = max(0.4, cap * 0.012)
        baru     = max(0.0, min(cap, cur + tumbuh + imigrasi))

        delta[key] = baru - cur
        eco[key] = baru

    return delta


def morning_note(state, delta: dict[str, float]) -> str | None:
    """Satu kalimat untuk pemain — hanya kalau ada yang layak dikatakan.

    Sengaja diam saat semuanya baik-baik saja. Pemberitahuan yang muncul tiap
    pagi berhenti dibaca pada pagi keempat.
    """
    kritis = [STOCKS[k]['label'] for k in STOCKS
              if abundance(state, k) < 0.30]
    if kritis:
        return f"Lembah menipis: {', '.join(kritis[:2])}. Beri waktu pulih."
    pulih = [k for k, d in delta.items()
             if d > 0 and abundance(state, k) > 0.9 and STOCKS[k]['cap'] * 0.9 > 0]
    if len(pulih) >= len(STOCKS) - 1:
        return "Lembah penuh lagi. Semua yang kau ambil sudah tumbuh kembali."
    return None


def report_lines(state) -> list[str]:
    """Isi panel Ekosistem. Satu baris per kolam, dikelompokkan per tempat."""
    ensure(state)
    grup = [
        ('AIR',        ['ikan_danau', 'ikan_pantai', 'ikan_gua']),
        ('HUTAN',      ['herba_gunung', 'jamur_gunung', 'mandrake', 'kayu_gunung']),
        ('PANTAI',     ['kerang_pantai']),
        ('LEMBAH',     ['kunang']),
        ('BAWAH TANAH',['bijih_dangkal', 'bijih_tengah', 'bijih_dalam']),
    ]
    lines: list[str] = []
    for judul, kunci in grup:
        lines.append(f"── {judul} ──")
        for k in kunci:
            a = abundance(state, k)
            bar = '#' * int(round(a * 14)) + '.' * (14 - int(round(a * 14)))
            lines.append(f"  {STOCKS[k]['label'][:22]:<22} [{bar}] "
                         f"{int(round(a * 100)):>3}%  {status_word(state, k)}")
        lines.append('')
    lines.append(f"Pasang surut pantai: {tide_phase(state)} "
                 f"({int(round(tide_level(state) * 100))}%)")
    lines.append("Kolam pulih paling cepat saat terisi separuh — memanen habis")
    lines.append("justru membuatnya butuh berhari-hari untuk kembali.")
    return lines


# ─────────────────────────────────────────────────────────────────────────────
# POPULASI LIAR
#
# `state.wild_entities` adalah wujud NYATA dari stok di atas: angka di kolam
# menentukan berapa banyak herba yang benar-benar berdiri di lereng pagi ini.
# Tanpa tabel ini kedua sistem akan menyimpang — kolam bisa habis sementara
# lerengnya tetap penuh tanaman, dan pemain tidak akan pernah percaya angka
# mana pun lagi.
#
# Dulu `respawn_wild_at_morning()` menempelkan 2-4 entri BARU tiap pagi tanpa
# batas atas, jadi save yang dimainkan sebulan membawa ratusan herba hantu yang
# ikut disimpan, di-tick, dan digambar selamanya.
# ─────────────────────────────────────────────────────────────────────────────

WILD_POPULASI = [
    # (jenis, scene, jumlah_saat_kolam_penuh, kunci_stok)
    ('wild_herb',        'mountain', 9, 'herba_gunung'),
    ('wild_berry',       'mountain', 7, 'herba_gunung'),
    ('wild_herb',        'farm',     3, 'herba_gunung'),
    ('wild_berry',       'farm',     2, 'herba_gunung'),
    ('running_mushroom', 'mountain', 4, 'jamur_gunung'),
    ('running_mushroom', 'farm',     2, 'jamur_gunung'),
    ('mandrake',         'mountain', 3, 'mandrake'),
    ('firefly',          'farm',     5, 'kunang'),
    ('firefly',          'town',     4, 'kunang'),
    ('firefly',          'lake',     6, 'kunang'),
]

# Jenis liar mana mengurangi kolam mana saat dipetik.
WILD_STOK = {
    'wild_herb':        'herba_gunung',
    'wild_berry':       'herba_gunung',
    'running_mushroom': 'jamur_gunung',
    'mandrake':         'mandrake',
    'firefly':          'kunang',
}


def wild_target(state, kind: str, scene: str) -> int:
    """Berapa banyak `kind` yang PANTAS berdiri di `scene` pagi ini.

    Akar kuadrat, bukan perbandingan lurus: kolam yang tinggal seperempat masih
    menyisakan setengah tanamannya berdiri. Lereng yang mendadak gundul terbaca
    sebagai bug; lereng yang menipis pelan-pelan terbaca sebagai akibat.
    """
    for k, sc, penuh, stok in WILD_POPULASI:
        if k == kind and sc == scene:
            return int(round(penuh * math.sqrt(max(0.0, abundance(state, stok)))))
    return 0


def wild_targets(state) -> dict[tuple[str, str], int]:
    return {(k, sc): wild_target(state, k, sc) for k, sc, _n, _s in WILD_POPULASI}
