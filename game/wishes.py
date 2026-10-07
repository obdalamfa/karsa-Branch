"""wishes.py — Keinginan: arah tanpa mencabut kebebasan.

Kenapa modul ini ada
────────────────────
docs/TAHAPAN.md Tahap 4: *"Ini yang membuat game punya alasan untuk
dipedulikan. Sekarang sudah ada kebutuhan, objek, aksi, antrian — tapi pemain
bisa main lima menit lalu bertanya 'terus?'"*

Jawaban The Sims 3 adalah Wishes, dan yang penting dari Wishes BUKAN daftar
tugasnya. Quest sudah ada di proyek ini (`quest_controller.py`, sebelas tahap
berurutan) dan ia tidak menjawab "terus?" — karena quest memberi SATU jalan
yang sama untuk semua pemain. Wishes bekerja dengan cara berlawanan:

    quest     : game yang memutuskan, pemain mengikuti
    keinginan : pemain yang memutuskan, game membayar

Mekanismenya empat langkah, dan langkah KETIGA yang paling sering dilupakan:

    1. muncul   keinginan kontekstual — hanya yang masuk akal SEKARANG
    2. janji    pemain memilih sendiri empat yang mau dikejar
    3. BAYAR    memenuhinya membayar Kebahagiaan
    4. belanja  Kebahagiaan ditukar jadi kemampuan permanen

Tanpa langkah 4, Kebahagiaan cuma angka yang naik — dan angka yang tidak
bisa dibelanjakan tidak memberi arah apa pun. Itu sebabnya hadiahnya ikut
dibangun di sini, bukan ditunda.

Keputusan desain yang perlu ditulis
───────────────────────────────────
**Garis dasar dicatat saat DIJANJIKAN, bukan dihitung dari total seumur
hidup.** Ini inti kejujurannya. Kalau "kumpulkan 500G" diukur dari
`stats['earned']` apa adanya, pemain yang sudah pernah menjual 10.000G akan
menyelesaikannya seketika tanpa melakukan apa pun. Jadi tiap janji menyimpan
angka awalnya, dan kemajuan selalu selisih terhadap angka itu.

**Dua jenis keinginan, karena memang ada dua bentuk.**

    tambah  dihitung dari selisih: "panen 5 tomat", "kumpulkan 500G"
    ambang  dihitung dari nilai mutlak: "capai 4 hati dengan Sari"

Keinginan `ambang` hanya ditawarkan kalau pemain BELUM melewatinya — kalau
tidak, ia selesai di detik yang sama ia dijanjikan.

**Tawarannya tetap sepanjang hari.** Diundi dari benih `(tahun, hari)`, jadi
daftar yang sama muncul tiap kali panel dibuka. Tawaran yang berubah tiap
frame tidak bisa dipilih; tawaran yang berubah tiap panel dibuka mengajarkan
pemain untuk membuka-tutup panel sampai dapat yang enak.

**Belum ada bias sifat.** Di TS3 keinginan yang muncul dipengaruhi trait, dan
trait itu Tahap 6. Jadi `_bobot()` sudah menerima pengait biasnya sekarang —
supaya Tahap 6 menyambung, bukan merombak.

Modul ini murni logika: tidak mengimpor Ursina, tidak menyentuh Entity. Jadi
seluruh isinya bisa diuji tanpa jendela, dan `tools/uji_wishes.py`
memanfaatkannya.
"""
from __future__ import annotations

import random

# Empat slot, sama seperti The Sims 3. Bukan angka keramat, tapi ada alasannya:
# cukup untuk mengejar dua hal sekaligus sambil menyimpan dua cadangan, dan
# masih cukup sedikit untuk memaksa pemain MEMILIH. Delapan slot berarti tidak
# ada yang ditolak, dan kalau tidak ada yang ditolak tidak ada keputusan.
SLOT_JANJI = 4

# Berapa kandidat dipajang sekaligus.
TAWARAN = 5


# ─────────────────────────────────────────────────────────────────────────────
# PEMBACA KEADAAN — satu tempat, supaya keinginan tidak masing-masing menebak
# di mana angkanya disimpan.
# ─────────────────────────────────────────────────────────────────────────────
def _st(s, kunci: str, bawaan=0):
    return (getattr(s, 'stats', None) or {}).get(kunci, bawaan)


def _panen_tanaman(s, cid: str) -> int:
    """Berapa kali satu tanaman tertentu dipanen.

    Penghitung ini ditambahkan ke jalur panen bersama modul ini: sebelumnya
    hanya `lobak` yang punya penghitung sendiri, jadi keinginan per-tanaman
    tidak mungkin diukur untuk 16 tanaman lainnya.
    """
    per = (getattr(s, 'stats', None) or {}).get('panen_tanaman') or {}
    return int(per.get(cid, 0))


def _punya_benih(s) -> list[str]:
    inv = getattr(s, 'inventory', None) or {}
    return [k[:-5] for k, q in inv.items() if k.endswith('_seed') and q > 0]


def _nama(cid: str) -> str:
    from .economy import item_name
    return item_name(cid)


# ─────────────────────────────────────────────────────────────────────────────
# KATALOG KEINGINAN
#
# Tiap entri punya enam bagian, dan `relevan` adalah yang membuat daftar ini
# terasa hidup: keinginan yang tidak masuk akal sekarang tidak pernah muncul.
# "Panen 5 Tomat" tidak ditawarkan kalau pemain tidak punya benih tomat;
# "Capai 4 hati dengan Sari" tidak ditawarkan kalau sudah 5 hati.
# ─────────────────────────────────────────────────────────────────────────────
def _k(id, kategori, bayar, jenis, relevan, param, teks, ukur, butuh):
    return {'id': id, 'kategori': kategori, 'bayar': bayar, 'jenis': jenis,
            'relevan': relevan, 'param': param, 'teks': teks,
            'ukur': ukur, 'butuh': butuh}


KATALOG = [
    # ── Tani ────────────────────────────────────────────────────────────────
    _k('panen_tanaman', 'Tani', 90, 'tambah',
       relevan=lambda s: bool(_punya_benih(s)),
       param=lambda s, rng: {'crop': rng.choice(sorted(_punya_benih(s))),
                             'n': rng.choice([3, 5, 8])},
       teks=lambda s, p: f"Panen {p['n']} {_nama(p['crop'])}",
       ukur=lambda s, p: _panen_tanaman(s, p['crop']),
       butuh=lambda s, p: p['n']),

    _k('panen_apa_saja', 'Tani', 60, 'tambah',
       relevan=lambda s: True,
       param=lambda s, rng: {'n': rng.choice([5, 10, 15])},
       teks=lambda s, p: f"Panen {p['n']} hasil kebun apa pun",
       ukur=lambda s, p: _st(s, 'harvested'),
       butuh=lambda s, p: p['n']),

    _k('siram', 'Tani', 45, 'tambah',
       relevan=lambda s: True,
       param=lambda s, rng: {'n': rng.choice([10, 20])},
       teks=lambda s, p: f"Siram tanaman {p['n']} kali",
       ukur=lambda s, p: _st(s, 'watered'),
       butuh=lambda s, p: p['n']),

    # ── Ekonomi ─────────────────────────────────────────────────────────────
    _k('kumpulkan_emas', 'Ekonomi', 110, 'tambah',
       relevan=lambda s: True,
       param=lambda s, rng: {'n': rng.choice([300, 600, 1200])},
       teks=lambda s, p: f"Hasilkan {p['n']}G dari menjual",
       ukur=lambda s, p: _st(s, 'earned'),
       butuh=lambda s, p: p['n']),

    _k('punya_emas', 'Ekonomi', 140, 'ambang',
       relevan=lambda s: True,
       param=lambda s, rng: {'n': rng.choice([1000, 2500, 5000])},
       teks=lambda s, p: f"Punya {p['n']}G tersimpan sekaligus",
       ukur=lambda s, p: int(getattr(s, 'gold', 0)),
       butuh=lambda s, p: p['n']),

    _k('olah', 'Ekonomi', 100, 'tambah',
       relevan=lambda s: True,
       param=lambda s, rng: {'n': rng.choice([2, 4, 6])},
       teks=lambda s, p: f"Olah {p['n']} hasil panen jadi produk",
       ukur=lambda s, p: _st(s, 'processed'),
       butuh=lambda s, p: p['n']),

    # ── Sosial ──────────────────────────────────────────────────────────────
    _k('hati_npc', 'Sosial', 150, 'ambang',
       relevan=lambda s: bool(_calon_npc(s)),
       param=lambda s, rng: _param_hati(s, rng),
       teks=lambda s, p: f"Capai {p['n']} hati dengan {p['nama']}",
       ukur=lambda s, p: int((getattr(s, 'npc_hearts', None) or {}).get(p['npc'], 0)),
       butuh=lambda s, p: p['n']),

    _k('hadiah', 'Sosial', 70, 'tambah',
       relevan=lambda s: True,
       param=lambda s, rng: {'n': rng.choice([3, 6])},
       teks=lambda s, p: f"Beri {p['n']} hadiah ke penduduk desa",
       ukur=lambda s, p: _st(s, 'gifts'),
       butuh=lambda s, p: p['n']),

    # ── Ternak ──────────────────────────────────────────────────────────────
    _k('hasil_ternak', 'Ternak', 90, 'tambah',
       relevan=lambda s: True,
       param=lambda s, rng: {'n': rng.choice([3, 6, 10])},
       teks=lambda s, p: f"Pungut {p['n']} hasil ternak",
       ukur=lambda s, p: _st(s, 'produce_collected'),
       butuh=lambda s, p: p['n']),

    # ── Petualangan ─────────────────────────────────────────────────────────
    _k('tambang', 'Petualangan', 80, 'tambah',
       relevan=lambda s: int(getattr(s, 'pickaxe_tier', 0)) > 0,
       param=lambda s, rng: {'n': rng.choice([5, 12, 20])},
       teks=lambda s, p: f"Tambang {p['n']} bijih",
       ukur=lambda s, p: _st(s, 'minerals_mined'),
       butuh=lambda s, p: p['n']),

    _k('turun_gua', 'Petualangan', 160, 'ambang',
       relevan=lambda s: int(getattr(s, 'pickaxe_tier', 0)) > 0,
       param=lambda s, rng: _param_gua(s, rng),
       teks=lambda s, p: f"Turun sampai gua tingkat {p['n']}",
       ukur=lambda s, p: _st(s, 'deepest_level'),
       butuh=lambda s, p: p['n']),

    _k('kalahkan_mob', 'Petualangan', 120, 'tambah',
       relevan=lambda s: bool(getattr(s, 'sword_id', '')),
       param=lambda s, rng: {'n': rng.choice([3, 8, 15])},
       teks=lambda s, p: f"Kalahkan {p['n']} makhluk",
       ukur=lambda s, p: _st(s, 'mobs_killed'),
       butuh=lambda s, p: p['n']),
]

KATALOG_BY_ID = {k['id']: k for k in KATALOG}


def _calon_npc(s) -> list[tuple[str, str]]:
    """NPC yang hatinya masih bisa dinaikkan. (id, nama).

    `HUMAN_NPCS`, bukan `NPCS`: dict itu tidak ada di data.py. Versi pertama
    modul ini mengimpor nama yang salah, dan akibatnya TIDAK terlihat sebagai
    error — `tawaran()` menangkap exception per-keinginan supaya satu templat
    rusak tidak mengosongkan seluruh papan, jadi keinginan sosial cuma diam
    tidak pernah muncul. Ketahuan lewat tools/uji_wishes.py, bukan dengan
    memainkannya.
    """
    from .data import HUMAN_NPCS
    hearts = getattr(s, 'npc_hearts', None) or {}
    return [(nid, meta.get('name', nid)) for nid, meta in HUMAN_NPCS.items()
            if hearts.get(nid, 0) < 8]


def _param_hati(s, rng) -> dict:
    calon = sorted(_calon_npc(s))
    nid, nama = rng.choice(calon)
    punya = int((getattr(s, 'npc_hearts', None) or {}).get(nid, 0))
    # Targetnya SELALU di atas yang sekarang, kalau tidak ia selesai seketika.
    target = min(8, punya + rng.choice([2, 3, 4]))
    return {'npc': nid, 'nama': nama, 'n': max(punya + 1, target)}


def _param_gua(s, rng) -> dict:
    dalam = _st(s, 'deepest_level')
    return {'n': dalam + rng.choice([3, 5, 10])}


# ─────────────────────────────────────────────────────────────────────────────
# HADIAH — ke mana Kebahagiaan dibelanjakan.
#
# Tiap hadiah menunjuk field yang TERBUKTI DIBACA kode permainan. Itu bukan
# kehati-hatian berlebihan: `state.upgrades` (hoe/water/bag/axe) ada di save
# sejak lama dan TIDAK DIBACA DI MANA PUN, jadi menjual "upgrade cangkul"
# sebagai hadiah akan mengambil Kebahagiaan pemain dan memberi nol.
# `tools/uji_wishes.py` memeriksa syarat ini untuk tiap hadiah.
#
# `max_energy` dipilih sebagai hadiah utama karena doktrin economy.py sendiri:
# "Energi, bukan waktu, adalah sumber daya langka. Satu hari = 100 energi dan
# 900 detik nyata." Jadi menambah energi = menambah apa yang muat dalam satu
# hari, dan itu terasa di setiap tindakan.
# ─────────────────────────────────────────────────────────────────────────────
HADIAH = [
    {'id': 'tenaga',   'nama': 'Napas Panjang',   'harga': 300,
     'field': 'max_energy',   'tambah': 10,  'maks': 5,
     'teks': '+10 energi maksimum (hari yang lebih panjang)'},
    {'id': 'raga',     'nama': 'Badan Kuat',      'harga': 250,
     'field': 'max_hp',       'tambah': 15,  'maks': 4,
     'teks': '+15 HP maksimum'},
    {'id': 'pemulih',  'nama': 'Pulih Cepat',     'harga': 200,
     'field': 'hp_regen_rate','tambah': 0.4, 'maks': 3,
     'teks': '+0,4 HP per detik saat tidak bergerak'},
]

HADIAH_BY_ID = {h['id']: h for h in HADIAH}


# ─────────────────────────────────────────────────────────────────────────────
# TAWARAN
# ─────────────────────────────────────────────────────────────────────────────
def _bobot(s, templat) -> float:
    """Peluang relatif satu keinginan muncul.

    Sekarang rata. Pengait ini ada supaya Tahap 6 (traits) bisa memiringkan
    tawaran — sim Penyayang Hewan lebih sering diberi keinginan ternak —
    tanpa mengubah bentuk fungsi lain mana pun.
    """
    return 1.0


def _rng_hari(s) -> random.Random:
    """Undian yang TETAP sepanjang satu hari-game.

    Benihnya `(tahun, hari)` — bukan `time.time()`, bukan `random` global.
    Tawaran yang berubah tiap kali panel dibuka mengajarkan pemain untuk
    membuka-tutup panel sampai dapat tawaran yang enak; itu bukan pilihan,
    itu mesin judi.
    """
    return random.Random(int(getattr(s, 'year', 1)) * 1000
                         + int(getattr(s, 'day', 1)))


def _janji_list(s) -> list:
    j = getattr(s, 'janji', None)
    if not isinstance(j, list):
        j = []
        s.janji = j
    return j


def tawaran(s) -> list[dict]:
    """Kandidat keinginan hari ini: [{'id','param','teks','butuh','bayar',...}].

    Yang disaring keluar: keinginan yang tidak relevan sekarang, yang sudah
    dijanjikan, dan keinginan `ambang` yang targetnya sudah terlewati.
    """
    rng = _rng_hari(s)
    sudah = {(p['id'], _kunci_param(p.get('param', {}))) for p in _janji_list(s)}
    siap = []
    for templat in KATALOG:
        try:
            if not templat['relevan'](s):
                continue
            param = templat['param'](s, rng)
            butuh = int(templat['butuh'](s, param))
            sekarang = int(templat['ukur'](s, param))
            if templat['jenis'] == 'ambang' and sekarang >= butuh:
                continue
            if (templat['id'], _kunci_param(param)) in sudah:
                continue
            siap.append({
                'id': templat['id'], 'param': param,
                'kategori': templat['kategori'], 'bayar': templat['bayar'],
                'jenis': templat['jenis'], 'butuh': butuh,
                'teks': templat['teks'](s, param),
                'bobot': _bobot(s, templat),
            })
        except Exception:
            # Satu keinginan yang rusak tidak boleh mengosongkan seluruh papan.
            continue
    rng.shuffle(siap)
    return siap[:TAWARAN]


def _kunci_param(param: dict) -> tuple:
    return tuple(sorted((k, str(v)) for k, v in (param or {}).items()))


# ─────────────────────────────────────────────────────────────────────────────
# JANJI
# ─────────────────────────────────────────────────────────────────────────────
def janjikan(s, kandidat: dict) -> tuple[bool, str]:
    """Pindahkan satu kandidat ke slot janji, CATAT garis dasarnya."""
    janji = _janji_list(s)
    if len(janji) >= SLOT_JANJI:
        return False, f'Keempat slot janji sudah penuh. Lupakan satu dulu.'
    templat = KATALOG_BY_ID.get(kandidat['id'])
    if templat is None:
        return False, 'Keinginan tidak dikenal.'
    param = kandidat['param']
    janji.append({
        'id': kandidat['id'],
        'param': param,
        'teks': kandidat['teks'],
        'jenis': templat['jenis'],
        'bayar': templat['bayar'],
        'butuh': int(templat['butuh'](s, param)),
        # Inti kejujurannya: angka saat DIJANJIKAN.
        'awal': int(templat['ukur'](s, param)),
        'hari': int(getattr(s, 'day', 1)),
    })
    return True, f"Dijanjikan: {kandidat['teks']}"


def lupakan(s, slot: int) -> tuple[bool, str]:
    """Buang satu janji. Gratis — menghukum pemain karena berubah pikiran
    membuat mereka berhenti berjanji sama sekali."""
    janji = _janji_list(s)
    if not 0 <= slot < len(janji):
        return False, 'Slot itu kosong.'
    pergi = janji.pop(slot)
    return True, f"Dilupakan: {pergi['teks']}"


def kemajuan(s, janji: dict) -> tuple[int, int]:
    """(sekarang, butuh) untuk satu janji — sudah memperhitungkan garis dasar."""
    templat = KATALOG_BY_ID.get(janji['id'])
    if templat is None:
        return 0, max(1, int(janji.get('butuh', 1)))
    butuh = max(1, int(janji.get('butuh', 1)))
    nilai = int(templat['ukur'](s, janji['param']))
    if janji.get('jenis') == 'ambang':
        return min(nilai, butuh), butuh
    maju = nilai - int(janji.get('awal', 0))
    return max(0, min(maju, butuh)), butuh


def selesai(s, janji: dict) -> bool:
    maju, butuh = kemajuan(s, janji)
    return maju >= butuh


def periksa(s) -> list[dict]:
    """Bayar semua janji yang sudah terpenuhi. Dipanggil setelah tiap aksi
    yang bisa mengubah hitungan, dan sekali tiap pagi.

    Kembaliannya daftar janji yang baru saja dibayar, supaya pemanggilnya bisa
    memberi tahu pemain. Kalau tidak ada yang selesai, daftarnya kosong dan
    pemanggil tidak perlu melakukan apa pun.
    """
    janji = _janji_list(s)
    lunas = []
    for p in list(janji):
        if selesai(s, p):
            janji.remove(p)
            bayar = int(p.get('bayar', 0))
            s.kebahagiaan = int(getattr(s, 'kebahagiaan', 0)) + bayar
            s.kebahagiaan_total = int(getattr(s, 'kebahagiaan_total', 0)) + bayar
            lunas.append(p)
    return lunas


# ─────────────────────────────────────────────────────────────────────────────
# BELANJA HADIAH
# ─────────────────────────────────────────────────────────────────────────────
def _dimiliki(s) -> dict:
    d = getattr(s, 'hadiah', None)
    if not isinstance(d, dict):
        d = {}
        s.hadiah = d
    return d


def hadiah_terpakai(s, hid: str) -> int:
    return int(_dimiliki(s).get(hid, 0))


def bisa_beli(s, hid: str) -> tuple[bool, str]:
    h = HADIAH_BY_ID.get(hid)
    if h is None:
        return False, 'Hadiah tidak dikenal.'
    n = hadiah_terpakai(s, hid)
    if n >= h['maks']:
        return False, f"{h['nama']} sudah maksimum ({h['maks']}x)."
    if int(getattr(s, 'kebahagiaan', 0)) < h['harga']:
        kurang = h['harga'] - int(getattr(s, 'kebahagiaan', 0))
        return False, f"Kurang {kurang} Kebahagiaan."
    return True, ''


def beli_hadiah(s, hid: str) -> tuple[bool, str]:
    """Tukar Kebahagiaan jadi kemampuan permanen.

    Efeknya diterapkan LANGSUNG ke field yang dibaca permainan, bukan disimpan
    sebagai bendera yang menunggu seseorang membacanya nanti. Itu pelajaran
    dari `state.upgrades`, yang ada di save sejak lama dan tidak pernah dibaca
    siapa pun.
    """
    ok, pesan = bisa_beli(s, hid)
    if not ok:
        return False, pesan
    h = HADIAH_BY_ID[hid]
    s.kebahagiaan = int(getattr(s, 'kebahagiaan', 0)) - h['harga']
    _dimiliki(s)[hid] = hadiah_terpakai(s, hid) + 1
    lama = getattr(s, h['field'])
    baru = lama + h['tambah']
    setattr(s, h['field'], baru)
    # Menaikkan batas tanpa mengisi bedanya membuat hadiahnya terasa baru
    # dipakai besok pagi. Energi dan HP ikut naik sekarang.
    if h['field'] == 'max_energy':
        s.energy = min(baru, int(getattr(s, 'energy', 0)) + h['tambah'])
    elif h['field'] == 'max_hp':
        s.hp = min(baru, int(getattr(s, 'hp', 0)) + h['tambah'])
    return True, f"{h['nama']}: {h['teks']}"


# ─────────────────────────────────────────────────────────────────────────────
# TEKS SIAP PAKAI — aturan yang tidak bisa dilihat pemain bukan aturan.
# (Pelajaran yang sama sudah ditulis husbandry.py untuk ternak.)
# ─────────────────────────────────────────────────────────────────────────────
def _bar(maju: int, butuh: int, n: int = 10) -> str:
    isi = int(round(n * maju / max(1, butuh)))
    return '#' * isi + '.' * (n - isi)


def baris_panel(s) -> list[str]:
    """Isi panel Keinginan, siap dicetak baris per baris."""
    janji = _janji_list(s)
    kb = int(getattr(s, 'kebahagiaan', 0))
    total = int(getattr(s, 'kebahagiaan_total', 0))
    out = [f"Kebahagiaan: {kb}   (seumur hidup: {total})", '']

    out.append(f"JANJI  ({len(janji)}/{SLOT_JANJI})")
    if not janji:
        out.append('  (belum ada. Pilih dari tawaran di bawah dengan [1-5].)')
    for i, p in enumerate(janji, 1):
        maju, butuh = kemajuan(s, p)
        out.append(f"  [{i}] {p['teks']}")
        out.append(f"      [{_bar(maju, butuh)}] {maju}/{butuh}"
                   f"   +{p['bayar']} Kebahagiaan")
    out.append('')

    kandidat = tawaran(s)
    out.append('TAWARAN HARI INI')
    if not kandidat:
        out.append('  (tidak ada yang masuk akal hari ini — besok berganti.)')
    for i, c in enumerate(kandidat, 1):
        out.append(f"  [{i}] {c['teks']}"
                   f"   ({c['kategori']}, +{c['bayar']})")
    out.append('')

    out.append('HADIAH — tukar Kebahagiaan jadi kemampuan permanen')
    for i, h in enumerate(HADIAH, 1):
        n = hadiah_terpakai(s, h['id'])
        bisa, _ = bisa_beli(s, h['id'])
        tanda = 'o' if bisa else ' '
        # Dua baris, bukan satu: panel ini lebarnya terbatas dan baris yang
        # lebih dari ~76 karakter terpotong tanpa peringatan. Diuji di
        # tools/uji_wishes.py, bukan dikira-kira.
        out.append(f"  [{tanda}] [{chr(ord('a') + i - 1)}] {h['nama']:14s}"
                   f" {h['harga']:4d} Kebahagiaan   {n}/{h['maks']}x")
        out.append(f"          {h['teks']}")
    return out


def panduan() -> list[str]:
    return [
        'Keinginan muncul sendiri dari apa yang sedang kamu lakukan.',
        'Kamu tidak harus mengejarnya — itu intinya. Yang dijanjikan dibayar',
        'Kebahagiaan, dan Kebahagiaan ditukar jadi kemampuan permanen.',
        '',
        f'  [1-5] janjikan tawaran       (maksimal {SLOT_JANJI} janji sekaligus)',
        '  [shift+1-4] lupakan janji    (gratis, berubah pikiran itu wajar)',
        '  [a/b/c] beli hadiah',
        '',
        'Kemajuan dihitung dari saat kamu BERJANJI, bukan dari total seumur',
        'hidup — jadi "hasilkan 600G" berarti 600G baru, bukan 600G yang sudah',
        'ada di catatan.',
    ]
