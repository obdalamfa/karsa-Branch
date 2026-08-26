"""economy.py — Satu sumber kebenaran untuk NILAI setiap barang.

Kenapa modul ini ada. Sebelum ini harga tersebar di empat tempat yang tidak
saling tahu: `CROPS['sell']` (dibaca hanya oleh panen), `WILD_ITEMS['sell']`
(hanya dicetak ke layar, tidak pernah membayar), `MINERALS['sell']` (tidak
dibaca SIAPA PUN), dan `SHOP_ITEMS['price']` (hanya beli). Akibatnya rantai
nilai tidak pernah tersambung: panen langsung mencetak emas SEKALIGUS menaruh
barangnya di tas, jadi menjual tidak pernah ada gunanya dan gudang penuh
barang tanpa harga.

Rantai yang dibangun di sini:

    benih --beli--> tanam --siram--> panen --> [ jual mentah
                                              | OLAH jadi produk (+~40%)
                                              | jadikan PAKAN ternak ]
                                                        |
                                                  hasil ternak --> jual

Aturan yang dipakai untuk menyusun angka, semuanya ditulis ulang lengkap di
`docs/EKONOMI.md`:

1. **Energi, bukan waktu, adalah sumber daya langka.** Satu hari = 100 energi
   dan 900 detik nyata. Seorang pemain kehabisan energi jauh sebelum kehabisan
   jam. Jadi mata uang keseimbangan yang benar adalah **emas per energi**
   (G/EN), bukan emas per hari.
2. Tanaman dijaga di pita **3,0 - 5,7 G/EN**. Tanaman murah dan cepat ada di
   ujung bawah (modal kecil, uang cepat), tanaman mahal dan lambat di ujung
   atas (modal besar, plot terkunci berhari-hari).
3. **Mengolah menambah ~40% nilai** dengan bayaran 3 energi. Angkanya dipilih
   supaya jalur olahan mengalahkan jual-mentah sekitar +30..40% pada
   perhitungan rantai penuh — cukup untuk layak dikejar, tidak cukup untuk
   membuat jual mentah jadi bodoh.
4. **Ternak jumlahnya TETAP** (lima ekor di dunia, tidak bisa dibeli). Karena
   itu penghasilannya boleh sedikit lebih baik per energi daripada bertani
   (5-7,5 G/EN) tanpa merusak apa pun: ia mentok di sekitar 95G/hari bersih
   apa pun yang pemain lakukan. Ternak = gaji pokok, tani = usaha yang skalanya
   ikut energi.
5. **Selalu ada selisih beli-jual.** Barang yang dijual toko (benih, kayu,
   jerami) dibeli kembali di bawah harga jualnya, supaya tidak ada mesin uang
   dari membeli lalu menjual ulang.
"""
from __future__ import annotations

from .data import CROPS, WILD_ITEMS, MINERALS

# ─────────────────────────────────────────────────────────────────────────────
# HARGA JUAL — berapa emas yang dibayar Warung Bu Sari untuk satu buah.
# Ini angka kanonik. Semua tempat lain (tas, peti kirim, panel olah) menghitung
# turunannya dari sini, jadi tidak mungkin lagi dua layar menyebut harga beda.
# ─────────────────────────────────────────────────────────────────────────────

# Potongan yang diambil Peti Kirim di kebun. Menjual di rumah itu nyaman;
# berjalan ke warung itu ongkos waktu. Selisih 15% membuat perjalanan punya
# harga yang bisa dibaca pemain, bukan sekadar kerepotan tanpa imbalan.
SHIPPING_RATE = 0.85

# Nilai satu "hari-pakan": berapa emas yang DIHEMAT sekali memberi makan,
# diukur dari harga jerami di toko. Dipakai untuk menjelaskan kenapa mengolah
# jagung jadi pakan lebih untung daripada menjualnya.
FEED_DAY_VALUE = 18

_PRODUCE_VALUES = {
    'telur': 32,   # siklus 1 hari; ayam + bebek
    'susu':  42,   # siklus 1 hari; sapi
    'wol':   58,   # siklus 2 hari; kambing + domba
}

_PROCESSED_VALUES = {
    'acar_lobak':     145,
    'sup_bayam':      125,
    'jus_wortel':     145,
    'tepung_jagung':  200,
    'selai_stroberi': 230,
    'jamur_kering':   230,
    'saus_tomat':     275,
    'keripik_labu':   275,
    'keju':           175,
    'kue_telur':      180,
    'kain_wol':       240,
    # Pakan sengaja dihargai JAUH di bawah nilai gunanya (18G/hari-pakan).
    # Menjualnya rugi; itu pesannya — pakan dibuat untuk dipakai.
    'pakan':           10,
}

_SUPPLY_VALUES = {
    # Dijual toko seharga 20 / 18, dibeli kembali 12 / 9. Selisih 40-50% inilah
    # yang menutup celah beli-lalu-jual-ulang.
    'kayu':   12,
    'jerami':  9,
    'ikan':   45,   # rata-rata hasil memancing, kini jadi barang bukan emas
}


def _build_values() -> dict[str, int]:
    v: dict[str, int] = {}
    # Hasil panen mentah.
    for key, c in CROPS.items():
        v[key] = int(c['sell'])
        # Benih laku setengah harga beli: pemain boleh membuang benih musim
        # yang salah, tapi harus rugi untuk itu.
        v[f'{key}_seed'] = max(1, int(c['cost']) // 2)
    v.update(_PRODUCE_VALUES)
    v.update(_PROCESSED_VALUES)
    v.update(_SUPPLY_VALUES)
    for key, m in MINERALS.items():
        v[key] = int(m['sell'])
    for key, w in WILD_ITEMS.items():
        v[key] = int(w['sell'])
    return v


ITEM_VALUES: dict[str, int] = _build_values()


# ─── NAMA TAMPILAN ───────────────────────────────────────────────────────────
# Tas dulu menampilkan kunci mentah ('lobak_seed: 3'). Pemain tidak menabung
# kunci dict; dia menabung Benih Lobak.
_EXTRA_NAMES = {
    'telur': 'Telur',              'susu': 'Susu',
    'wol':   'Wol',                'kayu': 'Kayu',
    'jerami':'Jerami',             'pakan': 'Pakan Ternak',
    'ikan':  'Ikan',
    'acar_lobak': 'Acar Lobak',    'sup_bayam': 'Sup Bayam',
    'jus_wortel': 'Jus Wortel',    'tepung_jagung': 'Tepung Jagung',
    'selai_stroberi': 'Selai Stroberi', 'jamur_kering': 'Jamur Kering',
    'saus_tomat': 'Saus Tomat',    'keripik_labu': 'Keripik Labu',
    'keju': 'Keju',                'kue_telur': 'Kue Telur',
    'kain_wol': 'Kain Wol',
}


def _build_names() -> dict[str, str]:
    n: dict[str, str] = {}
    for key, c in CROPS.items():
        n[key] = c['name']
        n[f'{key}_seed'] = f"Benih {c['name']}"
    for key, m in MINERALS.items():
        n[key] = m['name']
    for key, w in WILD_ITEMS.items():
        n[key] = w['name']
    n.update(_EXTRA_NAMES)
    return n


ITEM_NAMES: dict[str, str] = _build_names()


def item_name(item_id: str) -> str:
    return ITEM_NAMES.get(item_id, item_id.replace('_', ' ').title())


def sell_price(item_id: str) -> int:
    """Harga yang dibayar Warung Bu Sari. 0 = tidak laku dijual."""
    return ITEM_VALUES.get(item_id, 0)


def shipping_price(item_id: str) -> int:
    """Harga di Peti Kirim kebun — 85% harga warung, minimal 1 kalau laku."""
    p = sell_price(item_id)
    return max(1, int(p * SHIPPING_RATE)) if p > 0 else 0


def inventory_value(inventory: dict) -> int:
    """Total emas kalau SEMUA isi tas dijual di warung."""
    return sum(sell_price(k) * max(0, q) for k, q in inventory.items())


# Barang yang boleh masuk Peti Kirim. SENGAJA tidak "semua yang laku": benih,
# pakan, kayu dan bijih adalah BAHAN. Tombol satu-klik yang ikut menjual bahan
# adalah jebakan, bukan kemudahan. Peti hanya mengambil hasil kebun, hasil
# ternak, olahan dan ikan; sisanya dijual satu per satu di Warung.
def is_shippable(item_id: str) -> bool:
    if sell_price(item_id) <= 0:
        return False
    if item_id.endswith('_seed'):
        return False
    if item_id in ('kayu', 'jerami', 'pakan'):
        return False
    if item_id in MINERALS:
        return False
    return True


def shippable_items(inventory: dict) -> list[tuple[str, int, int]]:
    """[(item, jumlah, total_emas_di_peti), ...] terurut dari paling berharga."""
    out = [(k, q, shipping_price(k) * q)
           for k, q in inventory.items()
           if q > 0 and is_shippable(k)]
    out.sort(key=lambda r: -r[2])
    return out


def sellable_items(inventory: dict) -> list[tuple[str, int, int]]:
    """Semua yang laku di Warung, harga penuh. Terurut paling berharga dulu."""
    out = [(k, q, sell_price(k) * q)
           for k, q in inventory.items() if q > 0 and sell_price(k) > 0]
    out.sort(key=lambda r: -r[2])
    return out


# ─────────────────────────────────────────────────────────────────────────────
# OLAHAN — mengubah hasil mentah jadi barang yang lebih mahal.
# Dikerjakan di Kompor. `en` adalah energi yang dibayar sekali per batch.
# ─────────────────────────────────────────────────────────────────────────────

PROCESS_RECIPES = [
    {'id': 'acar_lobak',     'out': 'acar_lobak',     'n': 1, 'needs': {'lobak': 4},    'en': 3},
    {'id': 'sup_bayam',      'out': 'sup_bayam',      'n': 1, 'needs': {'bayam': 3},    'en': 3},
    {'id': 'jus_wortel',     'out': 'jus_wortel',     'n': 1, 'needs': {'wortel': 3},   'en': 3},
    {'id': 'tepung_jagung',  'out': 'tepung_jagung',  'n': 1, 'needs': {'jagung': 3},   'en': 3},
    {'id': 'selai_stroberi', 'out': 'selai_stroberi', 'n': 1, 'needs': {'stroberi': 3}, 'en': 3},
    {'id': 'jamur_kering',   'out': 'jamur_kering',   'n': 1, 'needs': {'jamur': 3},    'en': 3},
    {'id': 'saus_tomat',     'out': 'saus_tomat',     'n': 1, 'needs': {'tomat': 3},    'en': 3},
    {'id': 'keripik_labu',   'out': 'keripik_labu',   'n': 1, 'needs': {'labu': 3},     'en': 3},
    {'id': 'keju',           'out': 'keju',           'n': 1, 'needs': {'susu': 3},     'en': 3},
    {'id': 'kue_telur',      'out': 'kue_telur',      'n': 1, 'needs': {'telur': 4},    'en': 3},
    {'id': 'kain_wol',       'out': 'kain_wol',       'n': 1, 'needs': {'wol': 3},      'en': 3},
    # Satu jagung jadi empat hari-pakan. Diukur dari harga jerami toko itu
    # 72G nilai pakai dari jagung yang kalau dijual cuma 48G — inilah alasan
    # ekonomis untuk memelihara ternak, bukan sekadar hiasan kandang.
    {'id': 'pakan',          'out': 'pakan',          'n': 4, 'needs': {'jagung': 1},   'en': 1,
     'as_feed': True},
]

PROCESS_BY_ID = {r['id']: r for r in PROCESS_RECIPES}


def recipe_input_value(r: dict) -> int:
    return sum(sell_price(k) * q for k, q in r['needs'].items())


def recipe_output_value(r: dict) -> int:
    """Nilai hasil. Untuk pakan yang diukur adalah nilai PAKAI (jerami yang
    tidak jadi dibeli), bukan harga jualnya — menjual pakan memang rugi."""
    if r.get('as_feed'):
        return FEED_DAY_VALUE * r['n']
    return sell_price(r['out']) * r['n']


def recipe_uplift(r: dict) -> float:
    """Rasio nilai keluar / nilai masuk. 1.40 = +40%."""
    src = recipe_input_value(r)
    return (recipe_output_value(r) / src) if src else 0.0


def recipes_using(item_id: str) -> list[dict]:
    return [r for r in PROCESS_RECIPES if item_id in r['needs']]


def best_process_hint(item_id: str) -> str:
    """Teks singkat untuk tas: 'olah -> Selai Stroberi +39%'.

    Hanya muncul kalau mengolah memang lebih untung. Kalau tidak, tas diam —
    petunjuk yang selalu menyala tidak mengajarkan apa-apa.
    """
    best, best_up = None, 1.0
    for r in recipes_using(item_id):
        up = recipe_uplift(r)
        if up > best_up:
            best, best_up = r, up
    if best is None:
        return ''
    tail = ' (pakan)' if best.get('as_feed') else ''
    return f"olah > {item_name(best['out'])} +{int(round((best_up - 1) * 100))}%{tail}"


# ─────────────────────────────────────────────────────────────────────────────
# TERNAK — hewan yang benar-benar menghasilkan.
#
# Bug yang diperbaiki di sini: `execute_pie_action` mencari kunci 'sapi_betina',
# 'ayam' dan 'kambing' di dalam ANIMAL_NPCS, yang kuncinya sebenarnya
# 'sapi_betsy', 'ayam_kuning', 'kambing_jenggot'. Peta itu TIDAK PERNAH cocok,
# jadi 'Ambil Hasil' selalu menjawab "Tidak ada hasil saat ini." dan sembilan
# hewan di dunia tidak pernah menghasilkan apa pun sejak ada.
#
# Kuncinya sekarang JENIS hewan (`ANIMAL_NPCS[id]['type']`), bukan id-nya, jadi
# hewan baru dengan jenis yang sama ikut bekerja tanpa perlu disebut lagi.
# ─────────────────────────────────────────────────────────────────────────────

ANIMAL_PRODUCE = {
    'sapi':    {'item': 'susu',  'cycle': 1},
    'ayam':    {'item': 'telur', 'cycle': 1},
    'bebek':   {'item': 'telur', 'cycle': 1},
    'kambing': {'item': 'wol',   'cycle': 2},
    'domba':   {'item': 'wol',   'cycle': 2},
    # kuda, kucing, rubah, kelinci sengaja tidak menghasilkan. Mereka teman,
    # bukan mesin. Memaksa semuanya bertelur akan membuat dunia terasa seperti
    # spreadsheet.
}

# Energi per pekerjaan kandang. Sengaja tidak nol: kalau memberi makan dan
# memungut hasil gratis, ternak jadi uang gratis dan bertani kehilangan makna.
EN_FEED    = 2
EN_COLLECT = 2

# Berapa hari satu kali pemberian makan bertahan.
FEED_DAYS = 1

# Barang yang sah dijadikan pakan, terurut dari yang paling masuk akal.
# Tanaman pangan boleh dipakai tapi boros — UI mengatakannya terang-terangan.
FEED_ITEMS = ['pakan', 'jerami', 'jagung', 'wortel', 'bayam', 'lobak']


def produce_for(species: str) -> dict | None:
    return ANIMAL_PRODUCE.get(species)


def pick_feed(inventory: dict) -> str | None:
    """Pakan termurah yang dimiliki pemain. Pakan buatan dipakai lebih dulu."""
    for k in FEED_ITEMS:
        if inventory.get(k, 0) > 0:
            return k
    return None


def has_feed(inventory: dict) -> bool:
    return pick_feed(inventory) is not None


def animal_record(state, animal_id: str) -> dict:
    """Catatan per ekor: sisa hari kenyang + hari sejak hasil terakhir."""
    if not isinstance(getattr(state, 'animals', None), dict):
        state.animals = {}
    return state.animals.setdefault(animal_id, {'kenyang': 0, 'siap': 0})


def animal_status(state, animal_id: str, species: str) -> tuple[bool, str]:
    """(siap dipanen?, alasan yang bisa dibaca pemain)."""
    prod = produce_for(species)
    if not prod:
        return False, 'Tidak menghasilkan'
    rec = animal_record(state, animal_id)
    if rec.get('siap', 0) >= prod['cycle']:
        return True, f"{item_name(prod['item'])} siap ({sell_price(prod['item'])}G)"
    if rec.get('kenyang', 0) <= 0:
        return False, 'Lapar — beri makan dulu'
    sisa = prod['cycle'] - rec.get('siap', 0)
    return False, f"{item_name(prod['item'])} dalam {sisa} hari"


def tick_animals_daily(state) -> int:
    """Dipanggil sekali saat hari berganti.

    Hewan yang kenyang maju satu langkah menuju hasil; hewan yang lapar
    berhenti maju. Itu seluruh "husbandry"-nya — jujur dan bisa dijelaskan
    dalam satu kalimat, bukan simulasi peternakan.
    """
    from .data import ANIMAL_NPCS
    maju = 0
    for aid, meta in ANIMAL_NPCS.items():
        prod = produce_for(meta.get('type', ''))
        if not prod:
            continue
        rec = animal_record(state, aid)
        if rec.get('kenyang', 0) > 0:
            rec['kenyang'] -= 1
            if rec.get('siap', 0) < prod['cycle']:
                rec['siap'] = rec.get('siap', 0) + 1
                maju += 1
    return maju


# ─── KATALOG BELI ────────────────────────────────────────────────────────────
# Katalognya sendiri disusun di data.SHOP_ITEMS (di sana CROPS sudah ada, jadi
# tidak ada impor melingkar). Di sini hanya pencariannya.

def buy_price(item_id: str) -> int:
    from .data import SHOP_ITEMS
    for it in SHOP_ITEMS:
        if it['id'] == item_id:
            return int(it['price'])
    return 0


def margin_hint(shop_item: dict) -> str:
    """Baris pengajaran di daftar beli: benih 5G jadi panen berapa?

    Ini satu-satunya tempat pemain bisa melihat seluruh rantai dalam satu
    kalimat sebelum mengeluarkan uang.
    """
    crop = shop_item.get('crop')
    if not crop or crop not in CROPS:
        return ''
    c = CROPS[crop]
    hasil = sell_price(crop)
    untung = hasil - int(shop_item['price'])
    n_siram = -(-int(c['days']) // 2)      # ceil(days/2) di musimnya sendiri
    return f"panen {hasil}G (+{untung}G, {n_siram}h)"
