"""market.py — Harga yang ingat apa yang sudah kau jual.

`economy.py` menetapkan NILAI kanonik tiap barang dan tidak boleh berubah: ia
adalah papan neraca desain, tempat pita 3,0-5,7 G/EN dan selisih beli-jual
dijaga. Modul ini adalah lapisan di atasnya — **HARGA hari ini**, yang boleh
menyimpang dari nilai dan selalu kembali mendekatinya.

Masalah yang diselesaikan. Dengan harga tetap, satu tanaman terbaik per musim
adalah satu-satunya jawaban benar, selamanya. Pemain menghitungnya sekali di
hari kelima lalu menanam labu sampai kiamat. Ladang jadi lembar kerja, bukan
keputusan.

Tiga gaya yang membuat papan itu bergerak:

1. **Kejenuhan.** Warung Bu Sari punya uang dan pelanggan yang terbatas. Tiap
   penjualan menekan harga barang itu. Angkanya dipatok pada NILAI, bukan
   jumlah: pasar menyerap kira-kira 1.800G dari satu jenis barang sebelum
   harganya jatuh setengah. Jadi 60 lobak dan 6 ikan legendaris melukai pasar
   sama dalamnya — yang membuat monokultur mahal jadi tidak lebih aman daripada
   monokultur murah.

2. **Pemulihan.** Tiap pagi harga ditarik 28% mendekati nilai asalnya. Luka
   sedalam -22% hilang dalam empat-lima hari. Cukup lama untuk terasa, cukup
   cepat untuk tidak menghukum.

3. **Permintaan.** Barang di luar musimnya mahal karena langka. Dan tiap pekan
   satu barang diumumkan dicari orang — alasan untuk membongkar gudang atau
   mengubah rencana tanam minggu ini.

Batasnya keras di 0,55x sampai 1,65x. Pasar boleh mengejutkan; ia tidak boleh
membuat satu pagi bernilai sepuluh hari kerja, dan tidak boleh membuat panen
sebulan jadi tidak berharga.

Tidak mengimpor Ursina. Hanya membaca dan menulis `state`.
"""
from __future__ import annotations

import random

from .data import CROPS
from .economy import ITEM_VALUES, item_name, sell_price

# Harga tidak boleh melewati pita ini, apa pun yang terjadi.
IDX_MIN = 0.55
IDX_MAX = 1.65

# Berapa bagian indeks yang hilang saat pasar "jenuh penuh".
_JATUH_PENUH = 0.45

# Nilai barang (dalam emas) yang diserap pasar sebelum jatuh sebesar itu.
# Inilah satu angka yang menentukan seluruh rasa sistem ini.
_DAYA_SERAP_GOLD = 1800.0

# Berapa bagian jarak ke 1.0 yang ditutup tiap pagi.
_PULIH_HARIAN = 0.28

# Pengali harga barang yang sedang di luar musimnya.
_PREMI_LUAR_MUSIM = 1.25

# Permintaan pekanan.
_PERMINTAAN_HARI  = 3
_PERMINTAAN_GAIN  = 1.5
_PERMINTAAN_TIAP  = 7

# Barang yang TIDAK ikut permintaan pekanan: bahan mentah toko dan benih.
# Mengumumkan "minggu ini jerami dicari orang" hanya membuat pemain membeli
# jerami dari toko lalu menjualnya kembali — mesin uang, bukan peristiwa.
_BUKAN_KOMODITAS = {'kayu', 'jerami', 'pakan'}


def _komoditas() -> list[str]:
    return [k for k, v in ITEM_VALUES.items()
            if v > 0 and not k.endswith('_seed') and k not in _BUKAN_KOMODITAS]


def _saturasi(item_id: str) -> float:
    """Berapa BUAH yang menjenuhkan pasar untuk barang ini."""
    base = max(10, sell_price(item_id))
    return max(6.0, min(140.0, _DAYA_SERAP_GOLD / base))


# ─────────────────────────────────────────────────────────────────────────────
# STATE
# ─────────────────────────────────────────────────────────────────────────────

def ensure(state) -> dict:
    """Pastikan `state.market` ada dan berbentuk benar. Aman berkali-kali."""
    m = getattr(state, 'market', None)
    if not isinstance(m, dict):
        m = {}
        state.market = m
    idx = m.get('idx')
    if not isinstance(idx, dict):
        m['idx'] = {}
    # Permintaan pekanan: {'item': str, 'sisa': int}
    d = m.get('demand')
    if not isinstance(d, dict):
        m['demand'] = {}
    return m


def index(state, item_id: str) -> float:
    """Indeks harga barang ini hari ini. 1.0 = persis nilai kanoniknya."""
    m = ensure(state)
    v = m['idx'].get(item_id, 1.0)
    try:
        v = float(v)
    except (TypeError, ValueError):
        v = 1.0
    return max(IDX_MIN, min(IDX_MAX, v))


def _musim_faktor(state, item_id: str) -> float:
    """Premi kelangkaan untuk hasil kebun di luar musimnya."""
    c = CROPS.get(item_id)
    if not c:
        return 1.0
    musim = state.get_season() if hasattr(state, 'get_season') else None
    if musim is None:
        return 1.0
    return 1.0 if musim in c.get('seasons', []) else _PREMI_LUAR_MUSIM


def demand_item(state) -> str | None:
    """Barang yang sedang dicari orang pekan ini, atau None."""
    d = ensure(state)['demand']
    if d.get('sisa', 0) > 0 and d.get('item'):
        return d['item']
    return None


def _demand_faktor(state, item_id: str) -> float:
    return _PERMINTAAN_GAIN if demand_item(state) == item_id else 1.0


def price(state, item_id: str) -> int:
    """Harga Warung HARI INI. 0 tetap 0 — barang tak laku tetap tak laku."""
    base = sell_price(item_id)
    if base <= 0:
        return 0
    p = base * index(state, item_id) * _musim_faktor(state, item_id) \
        * _demand_faktor(state, item_id)
    return max(1, int(round(p)))


def shipping_price(state, item_id: str) -> int:
    """Peti Kirim: harga hari ini dipotong tarif yang sama seperti dulu."""
    from .economy import SHIPPING_RATE
    p = price(state, item_id)
    return max(1, int(p * SHIPPING_RATE)) if p > 0 else 0


def inventory_value(state, inventory: dict) -> int:
    return sum(price(state, k) * max(0, q) for k, q in inventory.items())


def shippable_items(state, inventory: dict) -> list[tuple[str, int, int]]:
    """Isi Peti Kirim dengan harga hari ini.

    Aturan APA yang boleh masuk peti tetap milik economy.py (`is_shippable`) —
    itu keputusan desain, bukan keputusan harga. Yang berubah di sini cuma
    berapa peti membayarnya.
    """
    from .economy import is_shippable
    out = [(k, q, shipping_price(state, k) * q)
           for k, q in inventory.items()
           if q > 0 and is_shippable(k)]
    out.sort(key=lambda r: -r[2])
    return out


def sellable_items(state, inventory: dict) -> list[tuple[str, int, int]]:
    """[(item, jumlah, total_emas_hari_ini)] terurut paling berharga dulu."""
    out = [(k, q, price(state, k) * q)
           for k, q in inventory.items() if q > 0 and price(state, k) > 0]
    out.sort(key=lambda r: -r[2])
    return out


# ─────────────────────────────────────────────────────────────────────────────
# PERISTIWA
# ─────────────────────────────────────────────────────────────────────────────

def on_sold(state, item_id: str, qty: int) -> None:
    """Catat penjualan. Dipanggil dari SETIAP tempat yang menukar barang jadi
    emas — Warung, Peti Kirim, hadiah berbayar. Kalau ada satu jalur yang lupa
    memanggil ini, jalur itu jadi celah bebas-konsekuensi dan pemain akan
    menemukannya sebelum kita."""
    if qty <= 0 or sell_price(item_id) <= 0:
        return
    m = ensure(state)
    turun = _JATUH_PENUH * (qty / _saturasi(item_id))
    baru = max(IDX_MIN, index(state, item_id) - turun)
    m['idx'][item_id] = baru


def daily_tick(state, rng=None) -> dict:
    """Satu pagi di pasar. Return ringkasan untuk laporan.

    {'pulih': int, 'permintaan': str|None, 'permintaan_baru': bool}
    """
    if rng is None:
        rng = random
    m = ensure(state)
    idx = m['idx']

    # 1. Tarik semua harga kembali mendekati nilainya, plus derau kecil supaya
    #    papan tidak pernah benar-benar diam.
    pulih = 0
    for item in list(idx.keys()):
        v = float(idx[item])
        v += (1.0 - v) * _PULIH_HARIAN
        v += rng.uniform(-0.025, 0.025)
        v = max(IDX_MIN, min(IDX_MAX, v))
        if abs(v - 1.0) < 0.012:
            del idx[item]          # sudah pulih; jangan simpan sampah di save
            pulih += 1
        else:
            idx[item] = v

    # 2. Permintaan pekanan.
    d = m['demand']
    baru = False
    if d.get('sisa', 0) > 0:
        d['sisa'] -= 1
        if d['sisa'] <= 0:
            d.clear()
    hari = getattr(state, 'day', 1)
    if not d.get('item') and hari % _PERMINTAAN_TIAP == 0:
        pilihan = _komoditas()
        if pilihan:
            d['item'] = rng.choice(pilihan)
            d['sisa'] = _PERMINTAAN_HARI
            baru = True

    return {'pulih': pulih, 'permintaan': d.get('item'), 'permintaan_baru': baru}


def demand_note(state) -> str | None:
    """Kalimat pengumuman untuk pagi hari, atau None."""
    it = demand_item(state)
    if not it:
        return None
    sisa = ensure(state)['demand'].get('sisa', 0)
    return (f"Warung mencari {item_name(it)} — dibayar "
            f"{int(round((_PERMINTAAN_GAIN - 1) * 100))}% lebih ({sisa} hari lagi).")


def trend_mark(state, item_id: str) -> str:
    """Penanda pendek untuk daftar harga: naik, turun, atau diam."""
    i = index(state, item_id) * _musim_faktor(state, item_id) \
        * _demand_faktor(state, item_id)
    if i >= 1.30:
        return '^^'
    if i >= 1.08:
        return '^'
    if i <= 0.70:
        return 'vv'
    if i <= 0.92:
        return 'v'
    return '  '


def movers(state, n: int = 6) -> list[tuple[str, int, int, float]]:
    """Barang yang harganya paling jauh dari normal.

    [(item, harga_hari_ini, harga_normal, rasio)] — untuk papan harga di Warung.
    """
    out = []
    for item in _komoditas():
        base = sell_price(item)
        now = price(state, item)
        if base <= 0:
            continue
        rasio = now / base
        if abs(rasio - 1.0) >= 0.06:
            out.append((item, now, base, rasio))
    out.sort(key=lambda r: -abs(r[3] - 1.0))
    return out[:n]
