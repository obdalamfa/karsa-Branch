"""crops.py — Katalog tanaman desa: sayur, palawija, padi, dan POHON.

Kenapa modul ini ada
────────────────────
`game/data.py` sudah punya CROPS dengan delapan tanaman, tapi bentuk datanya
hanya cukup untuk "tanam → tunggu → panen": nama, hari, harga, musim. Tidak ada
kebutuhan air, tidak ada jumlah hasil, tidak ada tanaman yang bisa dipetik
berulang, dan sama sekali tidak ada pohon. Pemilik minta tiga hal:
palawija, pohon yang bisa ditanam, dan aturan yang kelihatan.

Modul ini TIDAK menulis ulang data.py (file itu dipegang agen ekonomi). Ia
MENDAFTARKAN diri ke `data.CROPS` saat diimpor, dengan aturan ketat:
**hanya kunci yang belum ada yang ditambahkan.** Harga dan hari yang sudah
ditulis di data.py selalu menang. Jadi agen ekonomi boleh memindahkan
harga ke data.py kapan saja dan modul ini akan tunduk otomatis.

Skala waktu — dibaca dulu sebelum protes angkanya
─────────────────────────────────────────────────
Delapan tanaman lama sudah menyiratkan satu skala, dan skala itu dipertahankan
supaya keseimbangan lama tidak berubah:

    1 hari-game ≈ 22 hari lapangan (≈ 3 minggu)

Bukti dari data lama: lobak asli 30-40 hari → 2 hari-game (35/22 = 1,6).
Wortel 70-80 → 3 (75/22 = 3,4). Jagung 90-100 → 4 (95/22 = 4,3). Labu
100-120 → 5 (110/22 = 5,0). Bayam 40-50 → 2. Semua cocok. Jadi setiap
tanaman baru dihitung `hari_game = round(hari_asli / 22)`, minimal 2.

POHON memakai skala berbeda, dan ini disengaja: mangga okulasi berbuah setelah
±3 tahun (1.095 hari). Di skala 22 itu 50 hari-game — hampir dua musim penuh
hanya untuk satu pohon. Jadi pohon dipadatkan:

    1 hari-game ≈ 40 hari lapangan  (untuk pohon saja)

Mangga jadi 27 hari, kelapa genjah 32, pisang 8. Ini bohong yang jujur:
urutan dan RASIO antar pohon tetap benar (pisang paling cepat, kelapa dan
nangka paling lama), hanya rentangnya yang dipadatkan agar muat dalam satu
tahun-game 112 hari.

Musim
─────
Indonesia tidak punya empat musim; game punya. Pemetaannya:
    Semi   ≈ awal musim hujan   (tanam padi, awal tanam)
    Panas  ≈ kemarau            (palawija lahan kering)
    Gugur  ≈ akhir kemarau      (palawija kedua, panen raya)
    Dingin ≈ puncak musim hujan (padi rendeng, sayur dataran tinggi)

Palawija adalah tanaman kedua SETELAH padi di lahan kering — makanya sebagian
besar berdiri di Panas/Gugur, bukan di musim hujan.

Perbedaan mekanis tanaman vs pohon (ini inti permintaan pemilik)
───────────────────────────────────────────────────────────────
    TANAMAN                         POHON
    matang 2-14 hari                matang 8-32 hari
    perlu disiram TIAP hari         hanya bibit yang perlu disiram
    mati kalau kekeringan           bibit bisa mati, pohon dewasa tidak
    dipanen → petak kosong          dipanen → pohon TETAP berdiri
    (kecuali yang tumbuh_lagi)      berbuah lagi tiap N hari, selamanya
    tile tetap bisa dilewati        tile jadi TERHALANG permanen
    mati kalau salah musim? tidak,  hidup sepanjang musim, tapi hanya
    hanya tumbuh setengah laju      BERBUAH di musim buahnya
"""
from __future__ import annotations


# ─── KEBUTUHAN AIR ───────────────────────────────────────────────────────────
# Berapa hari tanaman sanggup tidak disiram sebelum layu. Angka ini yang
# membuat "kebutuhan air" jadi aturan, bukan label. Singkong dan sorgum memang
# tanaman tahan kering — itulah alasan orang menanamnya di lahan tadah hujan.
TOLERANSI_KERING = {'tinggi': 1, 'sedang': 2, 'rendah': 3}

# Setelah `toleransi` hari kering tanaman LAYU (berhenti tumbuh, warna coklat).
# Disiram saat layu → hidup lagi, tapi umurnya mundur satu hari.
# Setelah `toleransi + MATI_EKSTRA` hari kering tanaman MATI dan harus dibongkar
# dengan cangkul. Ada dua tahap supaya pemain punya kesempatan menyelamatkan.
MATI_EKSTRA = 2


# ─── KATALOG TANAMAN SEMUSIM ─────────────────────────────────────────────────
# Kunci tambahan di luar bentuk data.py yang lama:
#   kind          jenis     : 'sayur' | 'palawija' | 'padi'
#   air           kebutuhan : 'tinggi' | 'sedang' | 'rendah'
#   hasil         berapa buah per panen
#   tumbuh_lagi   0 = sekali panen. >0 = hari sampai buah berikutnya siap.
#   petik         berapa kali bisa dipetik ulang (hanya kalau tumbuh_lagi > 0)
#   bentuk        siluet: umbi|daun|rumpun|tegak|rambat|padi|jamur
#   warna/buah    warna daun & warna hasil (dipakai world.py buat render)
#   real          catatan lapangan — sumber angka `days`
CROP_CATALOG: dict[str, dict] = {

    # ── DELAPAN LAMA ── nilai days/sell/cost/seasons SAMA PERSIS dengan
    # data.py; yang ditambahkan hanya kolom baru. Kalau data.py berubah,
    # data.py yang menang (lihat register_into).
    'lobak': {
        'name': 'Lobak', 'kind': 'sayur', 'days': 2, 'sell': 22, 'cost': 5,
        'seasons': ['Semi'], 'air': 'sedang', 'hasil': 1,
        'tumbuh_lagi': 0, 'petik': 0, 'bentuk': 'umbi',
        'warna': (108, 148, 74), 'buah': (214, 205, 190),
        'real': 'lobak 30-40 hari',
    },
    'wortel': {
        'name': 'Wortel', 'kind': 'sayur', 'days': 3, 'sell': 35, 'cost': 8,
        'seasons': ['Semi', 'Gugur'], 'air': 'sedang', 'hasil': 1,
        'tumbuh_lagi': 0, 'petik': 0, 'bentuk': 'umbi',
        'warna': (96, 140, 70), 'buah': (198, 118, 48),
        'real': 'wortel 70-80 hari',
    },
    'stroberi': {
        'name': 'Stroberi', 'kind': 'sayur', 'days': 4, 'sell': 55, 'cost': 12,
        'seasons': ['Semi'], 'air': 'tinggi', 'hasil': 2,
        # Stroberi tanaman TAHUNAN: satu rumpun dipetik berkali-kali dalam satu
        # musim, tidak dicabut tiap panen.
        'tumbuh_lagi': 2, 'petik': 3, 'bentuk': 'rumpun',
        'warna': (86, 132, 66), 'buah': (176, 62, 62),
        'real': 'stroberi 80-90 hari sampai buah pertama, lalu panen berulang',
    },
    'jagung': {
        'name': 'Jagung', 'kind': 'palawija', 'days': 4, 'sell': 48, 'cost': 10,
        'seasons': ['Panas'], 'air': 'sedang', 'hasil': 2,
        'tumbuh_lagi': 0, 'petik': 0, 'bentuk': 'tegak',
        'warna': (110, 152, 68), 'buah': (206, 176, 72),
        'real': 'jagung 90-100 hari',
    },
    'tomat': {
        'name': 'Tomat', 'kind': 'sayur', 'days': 5, 'sell': 65, 'cost': 14,
        'seasons': ['Panas'], 'air': 'tinggi', 'hasil': 2,
        # Tomat indeterminate terus berbuah sampai batangnya habis.
        'tumbuh_lagi': 2, 'petik': 4, 'bentuk': 'rumpun',
        'warna': (82, 126, 62), 'buah': (188, 66, 52),
        'real': 'tomat 100-110 hari, panen bertahap',
    },
    'labu': {
        'name': 'Labu', 'kind': 'sayur', 'days': 5, 'sell': 70, 'cost': 15,
        'seasons': ['Gugur'], 'air': 'sedang', 'hasil': 1,
        'tumbuh_lagi': 0, 'petik': 0, 'bentuk': 'rambat',
        'warna': (94, 136, 64), 'buah': (198, 138, 56),
        'real': 'labu 100-120 hari',
    },
    'bayam': {
        'name': 'Bayam', 'kind': 'sayur', 'days': 2, 'sell': 30, 'cost': 7,
        'seasons': ['Dingin'], 'air': 'tinggi', 'hasil': 2,
        # Bayam petik (bukan bayam cabut): dipangkas, tumbuh lagi dari pangkal.
        'tumbuh_lagi': 1, 'petik': 2, 'bentuk': 'daun',
        'warna': (74, 128, 60), 'buah': (98, 152, 70),
        'real': 'bayam 40-50 hari, dipetik 2-3 kali',
    },
    'jamur': {
        'name': 'Jamur', 'kind': 'sayur', 'days': 3, 'sell': 55, 'cost': 12,
        'seasons': ['Dingin'], 'air': 'tinggi', 'hasil': 3,
        'tumbuh_lagi': 1, 'petik': 2, 'bentuk': 'jamur',
        'warna': (150, 138, 118), 'buah': (196, 182, 158),
        'real': 'jamur tiram 30-45 hari per siklus baglog',
    },

    # ── PADI ── pokok, bukan palawija. Butuh air paling banyak: sawah digenangi.
    'padi': {
        'name': 'Padi', 'kind': 'padi', 'days': 5, 'sell': 45, 'cost': 9,
        'seasons': ['Semi', 'Dingin'], 'air': 'tinggi', 'hasil': 3,
        'tumbuh_lagi': 0, 'petik': 0, 'bentuk': 'padi',
        'warna': (128, 158, 78), 'buah': (204, 186, 108),
        'real': 'padi sawah 110-120 hari; ditanam awal musim hujan',
    },

    # ── PALAWIJA ── tanaman kedua di lahan kering setelah padi.
    'kacang_tanah': {
        'name': 'Kacang Tanah', 'kind': 'palawija', 'days': 5, 'sell': 62, 'cost': 14,
        'seasons': ['Panas', 'Gugur'], 'air': 'sedang', 'hasil': 2,
        'tumbuh_lagi': 0, 'petik': 0, 'bentuk': 'rumpun',
        'warna': (104, 144, 66), 'buah': (186, 156, 108),
        'real': 'kacang tanah 90-110 hari; polong masak di dalam tanah',
    },
    'kedelai': {
        'name': 'Kedelai', 'kind': 'palawija', 'days': 4, 'sell': 52, 'cost': 12,
        'seasons': ['Gugur'], 'air': 'sedang', 'hasil': 2,
        'tumbuh_lagi': 0, 'petik': 0, 'bentuk': 'rumpun',
        'warna': (98, 138, 62), 'buah': (196, 178, 112),
        'real': 'kedelai 75-90 hari; palawija sesudah padi',
    },
    'ubi_kayu': {
        'name': 'Singkong', 'kind': 'palawija', 'days': 14, 'sell': 150, 'cost': 10,
        'seasons': ['Semi', 'Panas', 'Gugur'], 'air': 'rendah', 'hasil': 4,
        # Singkong TIDAK tumbuh lagi: umbinya dibongkar, batangnya dicabut.
        # Batang itu dipakai jadi stek untuk tanam berikutnya — makanya panen
        # singkong mengembalikan satu bibit (lihat interaction_controller).
        'tumbuh_lagi': 0, 'petik': 0, 'bentuk': 'umbi',
        'warna': (86, 124, 58), 'buah': (162, 132, 96),
        'real': 'singkong 8-12 bulan; paling lama, tapi tahan kering dan hasilnya berat',
    },
    'ubi_jalar': {
        'name': 'Ubi Jalar', 'kind': 'palawija', 'days': 6, 'sell': 70, 'cost': 10,
        'seasons': ['Panas', 'Gugur'], 'air': 'sedang', 'hasil': 3,
        'tumbuh_lagi': 0, 'petik': 0, 'bentuk': 'rambat',
        'warna': (92, 132, 68), 'buah': (168, 106, 92),
        'real': 'ubi jalar 100-150 hari; sulurnya menutup tanah',
    },
    'kacang_hijau': {
        'name': 'Kacang Hijau', 'kind': 'palawija', 'days': 3, 'sell': 40, 'cost': 7,
        'seasons': ['Panas', 'Gugur'], 'air': 'rendah', 'hasil': 2,
        'tumbuh_lagi': 0, 'petik': 0, 'bentuk': 'rumpun',
        'warna': (100, 146, 72), 'buah': (108, 148, 78),
        'real': 'kacang hijau 55-65 hari; palawija tercepat, sering ditanam di sisa lengas tanah',
    },
    'sorgum': {
        'name': 'Sorgum', 'kind': 'palawija', 'days': 5, 'sell': 58, 'cost': 9,
        'seasons': ['Panas', 'Gugur'], 'air': 'rendah', 'hasil': 3,
        'tumbuh_lagi': 0, 'petik': 0, 'bentuk': 'tegak',
        'warna': (114, 140, 70), 'buah': (172, 92, 68),
        'real': 'sorgum 100-120 hari; paling tahan kering di antara serealia',
    },
    'kacang_panjang': {
        'name': 'Kacang Panjang', 'kind': 'palawija', 'days': 2, 'sell': 28, 'cost': 6,
        'seasons': ['Semi', 'Panas', 'Gugur'], 'air': 'sedang', 'hasil': 2,
        # Dipetik berkali-kali dari batang yang sama — persis seperti di kebun.
        'tumbuh_lagi': 1, 'petik': 4, 'bentuk': 'rambat',
        'warna': (88, 134, 64), 'buah': (110, 158, 76),
        'real': 'kacang panjang 45-60 hari, lalu dipetik tiap 2-3 hari selama sebulan',
    },
    'cabai': {
        'name': 'Cabai', 'kind': 'palawija', 'days': 4, 'sell': 75, 'cost': 15,
        'seasons': ['Panas', 'Gugur'], 'air': 'sedang', 'hasil': 2,
        'tumbuh_lagi': 2, 'petik': 5, 'bentuk': 'rumpun',
        'warna': (76, 122, 60), 'buah': (192, 58, 48),
        'real': 'cabai 75-90 hari sampai petik pertama, lalu berbuah 6 bulan',
    },
}


# ─── KATALOG POHON ───────────────────────────────────────────────────────────
# Kunci khusus pohon:
#   is_tree       penanda; dipakai semua kode lain untuk memisah jalur pohon
#   days          umur (hari-game) sampai pohon DEWASA dan mulai bisa berbuah
#   panen_tiap    jeda hari antar panen setelah dewasa
#   hasil         buah per panen
#   musim_buah    musim saat pohon berbuah; [] = sepanjang tahun
#   tinggi        tinggi pohon dewasa dalam meter (siluet)
#   real          umur berbuah asli, sumber angka `days`
TREE_CATALOG: dict[str, dict] = {
    'pohon_pisang': {
        'name': 'Pisang', 'is_tree': True, 'kind': 'pohon',
        'days': 8, 'panen_tiap': 3, 'hasil': 5,
        'sell': 34, 'cost': 40, 'seasons': ['Semi', 'Panas', 'Gugur', 'Dingin'],
        'musim_buah': [], 'tinggi': 3.2, 'air': 'sedang',
        'warna': (92, 142, 72), 'buah': (200, 176, 70), 'bentuk': 'pisang',
        'real': 'pisang berbuah 9-12 bulan dari anakan; tandan baru tiap ~4 bulan',
    },
    'pohon_pepaya': {
        'name': 'Pepaya', 'is_tree': True, 'kind': 'pohon',
        'days': 9, 'panen_tiap': 2, 'hasil': 3,
        'sell': 40, 'cost': 45, 'seasons': ['Semi', 'Panas', 'Gugur', 'Dingin'],
        'musim_buah': [], 'tinggi': 3.4, 'air': 'sedang',
        'warna': (86, 136, 68), 'buah': (206, 146, 62), 'bentuk': 'pepaya',
        'real': 'pepaya berbuah 8-10 bulan, lalu terus-menerus',
    },
    'pohon_jambu': {
        'name': 'Jambu Biji', 'is_tree': True, 'kind': 'pohon',
        'days': 16, 'panen_tiap': 5, 'hasil': 6,
        'sell': 30, 'cost': 70, 'seasons': ['Semi', 'Panas', 'Gugur', 'Dingin'],
        'musim_buah': ['Semi', 'Gugur'], 'tinggi': 3.8, 'air': 'sedang',
        'warna': (80, 128, 64), 'buah': (176, 190, 118), 'bentuk': 'rindang',
        'real': 'jambu biji berbuah 2 tahun dari bibit; dua kali panen setahun',
    },
    'pohon_rambutan': {
        'name': 'Rambutan', 'is_tree': True, 'kind': 'pohon',
        'days': 22, 'panen_tiap': 9, 'hasil': 12,
        'sell': 26, 'cost': 110, 'seasons': ['Semi', 'Panas', 'Gugur', 'Dingin'],
        'musim_buah': ['Dingin'], 'tinggi': 4.4, 'air': 'sedang',
        'warna': (66, 114, 58), 'buah': (182, 58, 62), 'bentuk': 'rindang',
        'real': 'rambutan okulasi berbuah 3-4 tahun; musim buah sekali setahun (Des-Feb)',
    },
    'pohon_mangga': {
        'name': 'Mangga', 'is_tree': True, 'kind': 'pohon',
        'days': 26, 'panen_tiap': 9, 'hasil': 8,
        'sell': 38, 'cost': 130, 'seasons': ['Semi', 'Panas', 'Gugur', 'Dingin'],
        'musim_buah': ['Gugur'], 'tinggi': 4.8, 'air': 'rendah',
        'warna': (72, 118, 58), 'buah': (198, 162, 62), 'bentuk': 'rindang',
        'real': 'mangga okulasi berbuah ~3 tahun; berbunga di akhir kemarau',
    },
    'pohon_nangka': {
        'name': 'Nangka', 'is_tree': True, 'kind': 'pohon',
        'days': 30, 'panen_tiap': 10, 'hasil': 2,
        'sell': 190, 'cost': 150, 'seasons': ['Semi', 'Panas', 'Gugur', 'Dingin'],
        'musim_buah': [], 'tinggi': 5.0, 'air': 'rendah',
        'warna': (64, 108, 54), 'buah': (168, 158, 74), 'bentuk': 'rindang',
        'real': 'nangka berbuah 3-4 tahun; buah tunggal sangat berat',
    },
    'pohon_kelapa': {
        'name': 'Kelapa', 'is_tree': True, 'kind': 'pohon',
        'days': 32, 'panen_tiap': 4, 'hasil': 4,
        'sell': 48, 'cost': 160, 'seasons': ['Semi', 'Panas', 'Gugur', 'Dingin'],
        'musim_buah': [], 'tinggi': 5.6, 'air': 'rendah',
        'warna': (78, 126, 62), 'buah': (150, 128, 78), 'bentuk': 'kelapa',
        'real': 'kelapa genjah berbuah 3-4 tahun; tandan baru tiap bulan',
    },
}


# ─── PENDAFTARAN KE data.CROPS ───────────────────────────────────────────────
def register_into(target: dict) -> dict:
    """Gabungkan katalog ke dict CROPS milik data.py.

    Aturannya satu: **apa yang sudah ada di target tidak pernah ditimpa.**
    Kunci baru ditambahkan, kolom baru pada entri lama di-setdefault. Dengan
    begitu agen ekonomi bisa menulis harga di data.py dan harganya menang,
    sementara kolom mekanis (air, hasil, bentuk) tetap terisi dari sini.
    """
    for cid, spec in list(CROP_CATALOG.items()) + list(TREE_CATALOG.items()):
        entry = target.setdefault(cid, {})
        for k, v in spec.items():
            entry.setdefault(k, v)
    return target


def register_consumables(target: dict) -> dict:
    """Supaya tombol Makan (V) tidak meledak untuk tanaman baru.

    Nilainya diturunkan dari harga jual — bukan angka acak: makin mahal hasil
    panen, makin mengenyangkan. Sama seperti register_into, tidak menimpa.
    """
    for cid, spec in CROP_CATALOG.items():
        if cid in target:
            continue
        hp = max(6, min(34, int(spec['sell'] * 0.28)))
        en = max(4, min(30, int(spec['sell'] * 0.20)))
        target[cid] = {'heal_hp': hp, 'heal_energy': en,
                       'desc': f'+{hp} HP, +{en} EN'}
    for tid, spec in TREE_CATALOG.items():
        if tid in target:
            continue
        hp = max(8, min(30, int(spec['sell'] * 0.30)))
        target[tid] = {'heal_hp': hp, 'heal_energy': max(4, hp // 2),
                       'desc': f'+{hp} HP, +{max(4, hp // 2)} EN'}
    return target


def seed_shop_rows() -> list[dict]:
    """Baris toko untuk semua benih baru — DIEKSPOR, tidak dipasang sendiri.

    Panel toko sekarang memilih barang dengan tombol angka 1-9, jadi menambah
    18 baris ke SHOP_ITEMS akan membuat sebagian besar tidak bisa dibeli.
    Agen ekonomi yang memegang panel itu; daftar ini disiapkan supaya mereka
    tinggal memasangnya setelah panel toko bisa berhalaman.
    """
    rows = []
    for cid, spec in CROP_CATALOG.items():
        if cid in ('lobak', 'wortel', 'stroberi', 'jagung',
                   'tomat', 'labu', 'bayam', 'jamur'):
            continue    # sudah ada di SHOP_ITEMS
        rows.append({'id': f'{cid}_seed', 'name': f"Benih {spec['name']}",
                     'price': spec['cost'], 'season': '/'.join(spec['seasons'])})
    for tid, spec in TREE_CATALOG.items():
        rows.append({'id': f'{tid}_seed', 'name': f"Bibit {spec['name']}",
                     'price': spec['cost'], 'season': 'all'})
    return rows


SEED_SHOP_ROWS = seed_shop_rows()


def _install():
    """Pasang katalog ke data.py sekali saat modul diimpor."""
    from . import data
    register_into(data.CROPS)
    register_consumables(data.CONSUMABLES)


_install()


# ─── QUERY ───────────────────────────────────────────────────────────────────
def spec(cid: str) -> dict:
    """Ambil spesifikasi lengkap. Sumbernya data.CROPS supaya harga yang
    ditulis agen ekonomi ikut terbawa."""
    from .data import CROPS
    return CROPS.get(cid) or CROP_CATALOG.get(cid) or TREE_CATALOG.get(cid) or {}


def is_tree(cid: str) -> bool:
    return bool(spec(cid).get('is_tree'))


def crop_ids() -> list[str]:
    return list(CROP_CATALOG.keys())


def tree_ids() -> list[str]:
    return list(TREE_CATALOG.keys())


# ─── TAHAP PERTUMBUHAN ───────────────────────────────────────────────────────
# Lima tahap, dan tiap tahap WAJIB punya siluet berbeda (lihat world.py).
# Nama tahap ini juga yang ditampilkan ke pemain, jadi harus bahasa manusia.
TAHAP_TANAMAN = ['Benih', 'Tunas', 'Muda', 'Dewasa', 'Siap Panen']
TAHAP_POHON   = ['Bibit', 'Pohon Muda', 'Pohon Dewasa', 'Berbuah']


def crop_stage(cid: str, soil: dict) -> int:
    """0..4 — 4 berarti siap dipanen."""
    sp = spec(cid)
    days = max(1, sp.get('days', 4))
    age  = soil.get('age', 0)
    if age >= days:
        return 4
    # Empat tahap pertumbuhan dibagi rata sepanjang umur matang.
    return min(3, int(age / days * 4))


def tree_stage(cid: str, soil: dict) -> int:
    """0..3 — 3 berarti pohon dewasa yang sedang membawa buah matang."""
    sp = spec(cid)
    days = max(1, sp.get('days', 20))
    age  = soil.get('age', 0)
    if age >= days:
        return 3 if soil.get('siap') else 2
    if age >= days * 0.55:
        return 1
    return 0


def stage_name(cid: str, soil: dict) -> str:
    if is_tree(cid):
        return TAHAP_POHON[tree_stage(cid, soil)]
    return TAHAP_TANAMAN[crop_stage(cid, soil)]


def is_ready(cid: str, soil: dict) -> bool:
    """Siap dipanen? Satu-satunya sumber kebenaran untuk pertanyaan itu."""
    if soil.get('mati'):
        return False
    if is_tree(cid):
        return bool(soil.get('siap'))
    return soil.get('age', 0) >= max(1, spec(cid).get('days', 4))


def needs_water(cid: str, soil: dict) -> bool:
    """Perlu disiram hari ini? Pohon dewasa tidak pernah perlu."""
    if soil.get('mati'):
        return False
    if soil.get('watered'):
        return False
    if is_tree(cid):
        # Hanya bibit yang perlu disiram; pohon dewasa mencari air sendiri.
        return soil.get('age', 0) < spec(cid).get('days', 20)
    return True


def status_line(cid: str, soil: dict) -> str:
    """Satu baris keadaan untuk ditampilkan ke pemain. Aturan yang tidak
    bisa dilihat pemain bukan aturan."""
    sp = spec(cid)
    nama = sp.get('name', cid)
    if soil.get('mati'):
        return f"{nama}: MATI kekeringan — bongkar dengan cangkul"
    if soil.get('layu'):
        return f"{nama}: LAYU — siram hari ini atau mati"
    if is_ready(cid, soil):
        sisa = soil.get('petik', 0)
        ulang = f" (bisa dipetik {sisa}x lagi)" if sisa else ""
        return f"{nama}: SIAP PANEN{ulang}"
    if needs_water(cid, soil):
        return f"{nama}: {stage_name(cid, soil)} — belum disiram hari ini"
    return f"{nama}: {stage_name(cid, soil)} — sudah disiram"


# ─── PERTUMBUHAN HARIAN ──────────────────────────────────────────────────────
def grow_all(state) -> dict:
    """Jalankan satu malam untuk SEMUA petak. Dipanggil dari TimeController.

    Mengembalikan ringkasan {'layu': n, 'mati': n, 'siap': n, 'buah': n}
    supaya pemain bisa diberi tahu pagi harinya apa yang terjadi semalam —
    tanpa itu, tanaman mati diam-diam dan pemain tidak pernah belajar.
    """
    musim = state.get_season()
    lap = {'layu': 0, 'mati': 0, 'siap': 0, 'buah': 0}
    for soil in state.soil.values():
        cid = soil.get('crop')
        if not cid:
            continue
        if is_tree(cid):
            _grow_tree(soil, cid, musim, lap)
        else:
            _grow_crop(soil, cid, musim, lap)
    return lap


def _grow_crop(soil: dict, cid: str, musim: str, lap: dict) -> None:
    sp = spec(cid)
    if soil.get('mati'):
        return

    disiram = soil.pop('watered', False)

    if not disiram:
        # Hari kering. Ini satu-satunya tempat kebutuhan air jadi konsekuensi.
        kering = soil.get('kering', 0) + 1
        soil['kering'] = kering
        tol = TOLERANSI_KERING.get(sp.get('air', 'sedang'), 2)
        if kering > tol + MATI_EKSTRA:
            soil['mati'] = True
            soil['layu'] = False
            lap['mati'] += 1
        elif kering > tol:
            soil['layu'] = True
            lap['layu'] += 1
        return

    # Disiram. Kalau sedang layu, hari ini dipakai untuk pulih, bukan tumbuh —
    # pemain merasakan biaya kelalaiannya tanpa kehilangan seluruh petak.
    soil['kering'] = 0
    if soil.get('layu'):
        soil['layu'] = False
        soil['age'] = max(0, soil.get('age', 0) - 1)
        return

    sudah_siap = is_ready(cid, soil)
    # Laju lama dipertahankan: 2 di musimnya, 1 di luar musim.
    soil['age'] = soil.get('age', 0) + (2 if musim in sp.get('seasons', []) else 1)
    if not sudah_siap and is_ready(cid, soil):
        lap['siap'] += 1


def _grow_tree(soil: dict, cid: str, musim: str, lap: dict) -> None:
    sp = spec(cid)
    if soil.get('mati'):
        return
    matang = max(1, sp.get('days', 20))
    umur   = soil.get('age', 0)

    if umur < matang:
        # ── Fase bibit: masih butuh disiram, dan masih bisa mati. Inilah
        # ongkos menanam pohon — bertahun-tahun perhatian sebelum berbuah.
        disiram = soil.pop('watered', False)
        if not disiram:
            kering = soil.get('kering', 0) + 1
            soil['kering'] = kering
            tol = TOLERANSI_KERING.get(sp.get('air', 'sedang'), 2)
            # Bibit pohon lebih tahan daripada sayur: akarnya sudah dalam.
            if kering > tol + MATI_EKSTRA + 2:
                soil['mati'] = True
                soil['layu'] = False
                lap['mati'] += 1
            elif kering > tol + 1:
                soil['layu'] = True
                lap['layu'] += 1
            return
        soil['kering'] = 0
        if soil.get('layu'):
            soil['layu'] = False
            return
        soil['age'] = umur + 1
        if soil['age'] >= matang:
            lap['siap'] += 1     # pohon baru saja dewasa
        return

    # ── Fase dewasa: tidak perlu disiram lagi, tidak bisa mati kekeringan.
    soil.pop('watered', None)
    soil['kering'] = 0
    musim_buah = sp.get('musim_buah') or []
    if musim_buah and musim not in musim_buah:
        # Di luar musim buah pohon tetap hidup, hanya tidak berbuah. Itu beda
        # mendasar dari tanaman semusim, yang tumbuh setengah laju.
        return
    if soil.get('siap'):
        return
    t = soil.get('buah_t', 0) + 1
    soil['buah_t'] = t
    if t >= max(1, sp.get('panen_tiap', 5)):
        soil['siap'] = True
        soil['buah_t'] = 0
        lap['buah'] += 1


# ─── PANEN ───────────────────────────────────────────────────────────────────
def harvest(soil: dict, cid: str) -> tuple[int, bool]:
    """Ambil hasil dari satu petak.

    Return (jumlah, petak_kosong). `petak_kosong=True` berarti pemanggil harus
    menghapus entri soil — tanaman sekali panen. `False` berarti tanaman atau
    pohon tetap berdiri dan akan berbuah lagi.
    """
    sp = spec(cid)
    jumlah = max(1, sp.get('hasil', 1))

    if is_tree(cid):
        soil['siap'] = False
        soil['buah_t'] = 0
        return jumlah, False       # pohon TIDAK PERNAH hilang setelah dipanen

    sisa = soil.get('petik', 0)
    if sp.get('tumbuh_lagi', 0) > 0 and sisa > 0:
        soil['petik'] = sisa - 1
        # Mundurkan umur sebanyak jeda tumbuh-lagi, bukan ke nol: batangnya
        # sudah ada, yang tumbuh cuma buah berikutnya.
        soil['age'] = max(0, sp.get('days', 4) - sp.get('tumbuh_lagi', 1))
        return jumlah, False
    return jumlah, True


def plant_payload(cid: str) -> dict:
    """Isi awal entri soil untuk satu tanaman/pohon yang baru ditanam."""
    sp = spec(cid)
    d = {'crop': cid, 'age': 0, 'tilled': True, 'kering': 0}
    if is_tree(cid):
        d['buah_t'] = 0
        d['siap'] = False
    else:
        d['petik'] = sp.get('petik', 0) if sp.get('tumbuh_lagi', 0) else 0
    return d


# ─── TEKS PANDUAN (dipakai panel Tani & Ternak) ─────────────────────────────
def guide_lines() -> list[str]:
    """Tabel tanaman untuk dibaca DI DALAM game."""
    out = ['── TANAMAN SEMUSIM ──',
           '  nama            hari  musim            air     hasil  ulang']
    for cid, sp in CROP_CATALOG.items():
        s = spec(cid)
        musim = '/'.join(m[:3] for m in s.get('seasons', [])) or '-'
        ulang = f"{s.get('petik', 0)}x tiap {s.get('tumbuh_lagi')}h" if s.get('tumbuh_lagi') else 'sekali'
        out.append(f"  {s.get('name', cid):15s} {s.get('days', 0):>3}   "
                   f"{musim:15s}  {s.get('air', '-'):6s}  {s.get('hasil', 1):>3}   {ulang}")
    out += ['', '── POHON (tanam sekali, panen selamanya) ──',
            '  nama            dewasa  buah tiap  hasil  musim buah']
    for tid, sp in TREE_CATALOG.items():
        s = spec(tid)
        mb = '/'.join(m[:3] for m in (s.get('musim_buah') or [])) or 'sepanjang tahun'
        out.append(f"  {s.get('name', tid):15s} {s.get('days', 0):>4}h   "
                   f"{s.get('panen_tiap', 0):>5}h    {s.get('hasil', 1):>3}   {mb}")
    out += ['',
            'Air: tinggi = layu setelah 1 hari tidak disiram, sedang = 2, rendah = 3.',
            'Layu masih bisa diselamatkan dengan menyiram. Dua hari kemudian: mati.',
            'Pohon: hanya BIBIT yang perlu disiram. Pohon dewasa tidak pernah mati',
            'kering, tidak hilang saat dipanen, dan tilenya terhalang permanen.']
    return out
