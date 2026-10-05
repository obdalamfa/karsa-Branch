"""jobs.py — Papan Permintaan: yang DIMINTA warga, bukan yang kau inginkan.

Kenapa ini ada padahal sudah ada `sims_aspiration.py`. Keduanya terlihat mirip
di layar — daftar pendek tugas berhadiah — tapi arah datangnya berlawanan, dan
justru itu alasan keduanya perlu berdiri sendiri:

    KEINGINAN (S9)   datang dari DIRIMU. Abstrak, tentang keadaanmu sendiri
                     ("punya satu teman", "kumpulkan 300 Simoleon"), dan tidak
                     ada orang lain yang tahu kau memenuhinya.

    PERMINTAAN (ini) datang dari ORANG LAIN. Selalu konkret — barang yang harus
                     benar-benar berpindah tangan — selalu bernama, dan
                     memenuhinya mengubah hubunganmu dengan orang itu.

Sebelum ini `SIDE_QUESTS` di data.py berisi persis SATU entri hardcoded
('Bawakan 1 Stroberi untuk Maya'). Desa berisi empat belas orang yang tidak
pernah meminta apa pun.

Tiga aturan yang menentukan seluruh rasanya:

1. **Bayarannya dipatok ke HARGA PASAR HARI INI, bukan angka tetap.** Ini yang
   paling penting dan paling mudah salah. Dengan bayaran tetap, sebuah tugas
   pasti jadi lebih untung atau lebih rugi daripada menjual — dan begitu pemain
   menghitungnya sekali, salah satu dari keduanya mati selamanya. Dipatok ke
   pasar, papan ini selalu bernilai +35% di atas menjual, apa pun yang sedang
   terjadi pada harga. Kalau harga lobak jatuh karena kau membanjiri warung,
   permintaan lobak ikut membayar lebih sedikit. Ekonomi tidak punya pintu
   belakang.

2. **Tugas yang mustahil tidak pernah terbit.** Kepiting bakau hanya menggigit
   saat air surut; tanaman hanya tumbuh di musimnya; bijih dalam hanya ada di
   lantai yang belum tentu pernah kau capai. Papan yang memasang tugas mustahil
   mengajari pemain untuk berhenti membacanya. `fishing.tersedia()` memang
   dibangun untuk dipanggil dari sini.

3. **Permintaan kedaluwarsa, dan satu orang hanya meminta satu hal.** Papan
   yang menumpuk selamanya adalah daftar tugas, bukan desa.

Tidak mengimpor Ursina.
"""
from __future__ import annotations

import random

from .data import CROPS, MINERALS, HUMAN_NPCS
from .economy import item_name, sell_price

# Berapa banyak permintaan terpampang sekaligus.
SLOT = 3

# Umur satu permintaan, dalam hari.
UMUR_HARI = 3

# Bayaran = nilai pasar hari ini x ini. Satu-satunya angka yang menentukan
# apakah papan ini layak dikejar dibanding menjual langsung ke warung.
PREMI = 1.35

# Hati yang didapat dari memenuhi satu permintaan.
HATI = 0.4

# Barang yang tidak pernah diminta: bahan mentah toko (bisa dibeli lalu disetor
# untuk untung tanpa kerja) dan benih.
_BUKAN_PERMINTAAN = {'kayu', 'jerami', 'pakan', 'obor'}

_PANEN = [k for k in CROPS]
_OLAHAN = ['acar_lobak', 'sup_bayam', 'jus_wortel', 'tepung_jagung',
           'selai_stroberi', 'jamur_kering', 'saus_tomat', 'keripik_labu',
           'keju', 'kue_telur', 'kain_wol']
_TERNAK = ['telur', 'susu', 'wol']
_PUNGUT = ['wild_herb', 'wild_berry', 'running_mushroom', 'firefly']


# ─────────────────────────────────────────────────────────────────────────────
# STATE
# ─────────────────────────────────────────────────────────────────────────────

def ensure(state) -> dict:
    """Pastikan `state.jobs` ada dan isinya untuk HARI INI."""
    j = getattr(state, 'jobs', None)
    if not isinstance(j, dict):
        j = {}
        state.jobs = j
    j.setdefault('daftar', [])
    j.setdefault('hari', 0)
    j.setdefault('tuntas', 0)
    if j['hari'] != getattr(state, 'day', 1):
        _terbitkan(state, j)
    return j


def daftar(state) -> list[dict]:
    return ensure(state)['daftar']


# ─────────────────────────────────────────────────────────────────────────────
# PENERBITAN
# ─────────────────────────────────────────────────────────────────────────────

def _kandidat_antar(state, rng) -> list[tuple[str, int]]:
    """(item, jumlah) untuk permintaan barang biasa, hanya yang MASUK AKAL."""
    musim = state.get_season()
    keluar: list[tuple[str, int]] = []
    for k in _PANEN:
        if musim in CROPS[k].get('seasons', []):
            keluar.append((k, rng.randint(2, 5)))
    for k in _TERNAK:
        keluar.append((k, rng.randint(2, 4)))
    for k in _OLAHAN:
        keluar.append((k, rng.randint(1, 2)))
    return [(k, n) for k, n in keluar if k not in _BUKAN_PERMINTAAN]


def _kandidat_pancing(state, rng) -> list[tuple[str, int]]:
    """Hanya ikan yang BENAR-BENAR sedang menggigit di suatu perairan.

    Tanpa gerbang ini papan bisa meminta Kepiting Bakau pada hari yang airnya
    tidak pernah surut, dan pemain akan menghabiskan sore mencari sesuatu yang
    memang tidak ada.
    """
    from .fishing import tersedia, AIR_DANAU, AIR_PANTAI
    keluar = []
    for air in (AIR_DANAU, AIR_PANTAI):
        for sid in tersedia(state, air):
            keluar.append((sid, rng.randint(1, 3)))
    return keluar


def _kandidat_tambang(state, rng) -> list[tuple[str, int]]:
    """Bijih yang lantainya pernah dicapai pemain. Tidak meminta mithril dari
    orang yang belum pernah turun ke lantai sepuluh."""
    dalam = int(getattr(state, 'stats', {}).get('deepest_level', 0))
    return [(k, rng.randint(2, 5)) for k, m in MINERALS.items()
            if m.get('min_level', 1) <= max(1, dalam)]


def _kandidat_pungut(state, rng) -> list[tuple[str, int]]:
    from .ecology import WILD_STOK, abundance
    keluar = []
    for k in _PUNGUT:
        stok = WILD_STOK.get(k)
        # Jangan meminta apa yang lerengnya memang sudah habis — itu menyuruh
        # pemain menguras kolam yang justru sedang butuh didiamkan.
        if stok is None or abundance(state, stok) >= 0.30:
            keluar.append((k, rng.randint(2, 4)))
    return keluar


def _kandidat_basmi(state, rng) -> list[tuple[str, int]]:
    """Mob yang memang hidup di lantai yang pernah dicapai pemain.

    Ini satu-satunya jenis permintaan yang tidak menyetor barang, dan satu-
    satunya yang menyambungkan papan ke gua. Tanpanya papan ini cuma bicara
    tentang ladang dan air, padahal separuh permainan ada di bawah tanah.
    """
    dalam = int(getattr(state, 'stats', {}).get('deepest_level', 0))
    if dalam < 1:
        return []          # belum pernah turun; jangan minta apa pun dari gua
    from .data import MOB_TEMPLATES
    return [(k, rng.randint(2, 5)) for k, m in MOB_TEMPLATES.items()
            if m.get('min_lvl', 1) <= dalam]


def _nilai_rampasan(state, kind: str) -> int:
    """Nilai pasar rata-rata yang jatuh dari satu ekor mob jenis ini.

    Bayaran basmi tetap dipatok ke PASAR, sama seperti jenis permintaan lain —
    lewat barang yang dijatuhkan mob itu. Memberinya angka tetap akan membuka
    satu-satunya jalur penghasilan di game ini yang kebal terhadap ekonomi,
    dan pemain akan menemukannya.
    """
    from .data import MOB_TEMPLATES
    from .market import price as harga_kini
    drops = MOB_TEMPLATES.get(kind, {}).get('drops', {})
    return max(1, sum(harga_kini(state, k) * q for k, q in drops.items()))


def _bayaran(state, item: str, n: int) -> int:
    from .market import price as harga_kini
    from .data import MOB_TEMPLATES
    satuan = (_nilai_rampasan(state, item) if item in MOB_TEMPLATES
              else harga_kini(state, item))
    return max(1, int(round(satuan * n * PREMI)))


def _terbitkan(state, j: dict) -> None:
    """Susun papan hari ini: buang yang kedaluwarsa, isi slot yang kosong."""
    hari = getattr(state, 'day', 1)
    lalu = j.get('hari', 0)
    maju = max(0, hari - lalu) if lalu else 1

    hidup = []
    for t in j.get('daftar', []):
        t['sisa'] = int(t.get('sisa', UMUR_HARI)) - maju
        if t['sisa'] > 0:
            hidup.append(t)
    j['daftar'] = hidup
    j['hari'] = hari

    # Satu semai per hari, dan SEMUA pengundian lewat semai ini — termasuk
    # jumlah barang yang diminta. Versi pertama memakai `random` global untuk
    # jumlahnya, jadi papan hari yang sama bisa berbeda tiap kali fungsi ini
    # dipanggil: tidak bisa diuji, dan mustahil dibaca ulang saat melacak bug.
    rng = random.Random(hari * 977 + 13)
    sudah_minta = {t['npc'] for t in hidup}
    pemberi = [n for n in HUMAN_NPCS if n not in sudah_minta]
    rng.shuffle(pemberi)

    jenis_pool = [
        ('antar',   _kandidat_antar),
        ('pancing', _kandidat_pancing),
        ('tambang', _kandidat_tambang),
        ('pungut',  _kandidat_pungut),
        ('basmi',   _kandidat_basmi),
    ]

    while len(j['daftar']) < SLOT and pemberi:
        npc = pemberi.pop()
        rng.shuffle(jenis_pool)
        pilihan = None
        for jenis, ambil in jenis_pool:
            # Penyaring harga hanya berlaku untuk permintaan BARANG. Nama mob
            # bukan barang, jadi `sell_price('kelelawar')` itu 0 — memakai
            # penyaring yang sama untuk keduanya akan membuang seluruh jenis
            # 'basmi' tanpa satu pun error. Jenis yang hilang diam-diam adalah
            # bug yang paling mahal ditemukan di proyek ini.
            kand = [c for c in ambil(state, rng)
                    if jenis == 'basmi' or sell_price(c[0]) > 0]
            if kand:
                pilihan = (jenis, rng.choice(kand))
                break
        if pilihan is None:
            continue
        jenis, (item, n) = pilihan
        tugas = {
            'id':    f"{hari}_{npc}_{item}",
            'npc':   npc,
            'jenis': jenis,
            'item':  item,
            'n':     int(n),
            'bayar': _bayaran(state, item, int(n)),
            'sisa':  UMUR_HARI,
        }
        if jenis == 'basmi':
            # Kemajuan basmi diukur dari SELISIH, bukan dari total. Memakai
            # total akan membuat permintaan baru langsung tuntas bagi pemain
            # yang sudah pernah membunuh banyak mob sebelumnya.
            tugas['mulai'] = int(state.stats.get('mobs_killed', 0))
        j['daftar'].append(tugas)


# ─────────────────────────────────────────────────────────────────────────────
# PENYETORAN
# ─────────────────────────────────────────────────────────────────────────────

def punya(state, t: dict) -> int:
    """Kemajuan permintaan ini: isi tas, atau jumlah mob yang sudah dibasmi."""
    if t.get('jenis') == 'basmi':
        return max(0, int(state.stats.get('mobs_killed', 0)) - int(t.get('mulai', 0)))
    return int(state.inventory.get(t['item'], 0))


def bisa_setor(state, t: dict) -> bool:
    return punya(state, t) >= int(t['n'])


def setor(state, t: dict) -> tuple[bool, str]:
    """Setor satu permintaan. Return (berhasil, pesan)."""
    from .market import on_sold
    if not bisa_setor(state, t):
        kurang = int(t['n']) - punya(state, t)
        apa = (_nama_mob(t['item']) if t.get('jenis') == 'basmi'
               else item_name(t['item']))
        return False, f"Masih kurang {kurang} {apa}."

    if t.get('jenis') != 'basmi':
        state.inventory[t['item']] -= int(t['n'])
        if state.inventory[t['item']] <= 0:
            del state.inventory[t['item']]

    state.gold += int(t['bayar'])
    state.stats['earned'] = state.stats.get('earned', 0) + int(t['bayar'])

    # Barang yang disetor tetap MASUK PASAR — warga itu memakainya, menjualnya
    # lagi, atau memberikannya ke orang lain. Kalau papan ini tidak menekan
    # harga sementara warung menekan, pemain akan menyalurkan seluruh panennya
    # lewat papan dan harga tidak akan pernah bergerak lagi.
    if t.get('jenis') != 'basmi':
        on_sold(state, t['item'], int(t['n']))

    npc = t['npc']
    state.npc_hearts[npc] = min(10, state.npc_hearts.get(npc, 0) + HATI)

    j = ensure(state)
    j['daftar'] = [x for x in j['daftar'] if x.get('id') != t.get('id')]
    j['tuntas'] = int(j.get('tuntas', 0)) + 1

    nama = HUMAN_NPCS.get(npc, {}).get('name', npc)
    if t.get('jenis') == 'basmi':
        return True, (f"{nama} lega: {int(t['n'])} {_nama_mob(t['item'])} "
                      f"sudah dibasmi. +{int(t['bayar'])}G, +{HATI} hati.")
    return True, (f"{nama} menerima {int(t['n'])} {item_name(t['item'])}. "
                  f"+{int(t['bayar'])}G, +{HATI} hati.")


# ─────────────────────────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────────────────────────

def _nama_mob(kind: str) -> str:
    from .data import MOB_TEMPLATES
    return MOB_TEMPLATES.get(kind, {}).get('name', kind)


def _nama_minta(t: dict) -> str:
    return (_nama_mob(t['item']) if t.get('jenis') == 'basmi'
            else item_name(t['item']))


_KATA = {
    'antar':   'Antarkan',
    'basmi':   'Basmi',
    'pancing': 'Pancingkan',
    'tambang': 'Tambangkan',
    'pungut':  'Petikkan',
}


def lines(state) -> list[str]:
    """Isi panel Papan Permintaan."""
    from .market import price as harga_kini
    t_semua = daftar(state)
    keluar = [f"Emas: {state.gold}G   Hari ke-{getattr(state, 'day', 1)}   "
              f"Tuntas: {ensure(state).get('tuntas', 0)}", '']
    if not t_semua:
        keluar.append("  Papan kosong hari ini. Warga sedang tidak butuh apa-apa.")
        return keluar

    keluar.append(f"      {'DARI':<12}{'PERMINTAAN':<32}{'PUNYA':>8}{'BAYAR':>7}  SISA")
    for i, t in enumerate(t_semua):
        nama = HUMAN_NPCS.get(t['npc'], {}).get('name', t['npc'])
        minta = f"{_KATA.get(t['jenis'], 'Bawakan')} {t['n']} {_nama_minta(t)}"
        siap = 'v' if bisa_setor(state, t) else ' '
        keluar.append(
            f"  [{i+1}]{siap} {nama[:11]:<12}{minta[:31]:<32}"
            f"{punya(state, t):>4}/{t['n']:<3}{t['bayar']:>6}G{t['sisa']:>4}h")

    keluar.append('')
    keluar.append("  [v] = barangnya sudah cukup, tekan angkanya untuk menyetor.")
    keluar.append("  Bayaran mengikuti HARGA PASAR hari ini plus "
                  f"{int(round((PREMI - 1) * 100))}% — kalau kau")
    keluar.append("  membanjiri warung dengan lobak, permintaan lobak ikut turun.")
    keluar.append(f"  Tiap permintaan hangus setelah {UMUR_HARI} hari.")
    return keluar


def aksi(state, idx: int) -> str:
    """Tombol angka di panel. idx 1-based."""
    t_semua = daftar(state)
    if not (1 <= idx <= len(t_semua)):
        return ''
    _ok, pesan = setor(state, t_semua[idx - 1])
    return pesan
