"""probe_dua_desa.py — logika babak 2 "Cerita Dua Desa" tanpa membuka jendela.

game/dua_desa.py sengaja murni di atas GameState, jadi probe ini tidak perlu
boot Ursina: cukup membuat GameState kosong dan memanggil fungsinya. Yang
MENGUBAH state (serahkan_titipan, ikut_lomba, buka_jalan_lama, pilih_mitra)
diuji lewat QuestController dengan panels tiruan yang merekam flash.

Yang diperiksa, per kelompok:

  titipan   deterministik per tanggal, dua entri unik, hanya tanaman musim ini,
            papan sesuai, dan tidak mengubah state
  imbalan   ~1,3x harga Warung, dibulatkan 5G, selalu di atas menjual biasa
  nama      nama peminta dari npc, atau "Warga Karsa/Lawang" bila tanpa nama
  bar       bar kerukunan 20 kolom dan lebar lain
  lomba     nilai lawan naik tiap tahun, baris panel (hasil > hari-H > jadwal),
            pilihan masak/panen, dan seluruh cabang menang/kalah
  jadwal    prioritas lomba > gotong royong > jalan terbuka > SCHEDULES
  syarat    keterangan pie menu untuk tiap sebab opsi terkunci
  pesan     kabar pagi hari-H, besok, dan gotong royong
  alur      maju tak pernah mundur, pilih mitra sekali, kerukunan dijepit

    python tools/probe_dua_desa.py
"""
from __future__ import annotations

import copy
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from game import dua_desa as dd  # noqa: E402
from game.config import SEASONS  # noqa: E402
from game.controllers.quest_controller import QuestController  # noqa: E402
from game.data import (CROPS, DUA_DESA_OPSI, HUMAN_NPCS, JADWAL_GOTONG_ROYONG,  # noqa: E402
                       JADWAL_JALAN_TERBUKA, JADWAL_LOMBA, KERUKUNAN_MAKS,
                       LOMBA_ANTAR_DESA, MITRA_DESA, PAPAN_TITIPAN, SCHEDULES,
                       SEASONAL_EVENTS, TITIPAN, TITIPAN_PER_HARI)
from game.economy import PROCESS_RECIPES, item_name, sell_price  # noqa: E402
from game.state import GameState  # noqa: E402

hasil: list[tuple[str, bool, str]] = []


def cek(nama, ok, ket=''):
    hasil.append((nama, bool(ok), str(ket)))


def _state(**kw):
    return GameState(**kw)


def _hari(musim, hari_ke, jam=9, tahun=1, scene='lawang', hari_total=None, **kw):
    """GameState pada satu tanggal. `day` ikut diisi karena gotong_royong_tiba
    membandingkan state.day, bukan day_in_season."""
    return GameState(season_index=SEASONS.index(musim), day_in_season=hari_ke,
                     day=hari_ke if hari_total is None else hari_total,
                     time_minutes=jam * 60.0, year=tahun, scene_name=scene, **kw)


class Papan:
    """Tiruan panels: satu-satunya yang dipakai controller adalah flash_msg."""

    def __init__(self):
        self.pesan = []

    def flash_msg(self, msg, detik=None, **kw):
        self.pesan.append(str(msg))


class Dunia:
    def __init__(self, scene='lawang'):
        self.scene_name = scene


def _ev_lomba():
    return SEASONAL_EVENTS['lomba_antar_desa']


def _tanggal_lomba(jam=9, **kw):
    ev = _ev_lomba()
    return _hari(ev['season'].capitalize(), ev['day'], jam=jam, **kw)


def _pesan_lomba(kategori, calon, lawan):
    k = LOMBA_ANTAR_DESA['kategori'][kategori]
    item, n, nilai = calon
    nama = item_name(item) + (f" x{n}" if n > 1 else '')
    menang = nilai > lawan
    naik = (LOMBA_ANTAR_DESA['kerukunan_ikut']
            + (LOMBA_ANTAR_DESA['kerukunan_menang'] if menang else 0))
    hasil_teks = f"MENANG! +{k['hadiah']}G" if menang else "Kalah tipis."
    pesan = f"{k['nama']}: {nama} {nilai} vs {lawan}. {hasil_teks}\nKerukunan +{naik}"
    return menang, naik, pesan


# ─── Titipan ─────────────────────────────────────────────────────────────────

def _calon(papan, musim):
    return [t for t in TITIPAN if t['papan'] == papan
            and (t['item'] not in CROPS or musim in CROPS[t['item']]['seasons'])]


def uji_titipan():
    s = _hari('Semi', 1)
    kunci = dd.kunci_hari(s)
    cek('kunci hari = tahun-musim-hari', kunci == '1-0-1', kunci)

    for papan in ('karsa', 'lawang'):
        a = dd.titipan_hari_ini(s, papan)
        b = dd.titipan_hari_ini(_hari('Semi', 1), papan)
        cek(f'titipan {papan} deterministik untuk tanggal yang sama',
            [t['id'] for t in a] == [t['id'] for t in b], str([t['id'] for t in a]))
        cek(f'titipan {papan} berisi TITIPAN_PER_HARI entri',
            len(a) == TITIPAN_PER_HARI, f'{len(a)} entri')
        cek(f'titipan {papan} tidak dobel', len({t['id'] for t in a}) == len(a),
            str(len({t['id'] for t in a})))
        cek(f'titipan {papan} semuanya dari papan itu',
            all(t['papan'] == papan for t in a))
        calon = {t['id'] for t in _calon(papan, 'Semi')}
        cek(f'titipan {papan} diambil dari calon musim ini',
            {t['id'] for t in a} <= calon,
            f'luar calon: {sorted({t["id"] for t in a} - calon)}')
        segar = all(t['item'] not in CROPS or 'Semi' in CROPS[t['item']]['seasons']
                    for t in a)
        cek(f'titipan {papan} hanya barang yang bisa dipenuhi musim ini', segar,
            str([t['item'] for t in a]))

    # lawang Semi hari 1 memang papan ini — dipin supaya pengocokan yang berubah
    # ketahuan, bukan cuma "dua entri apa saja".
    cek('papan lawang Semi hari 1 = wortel + stroberi',
        sorted(t['id'] for t in dd.titipan_hari_ini(s, 'lawang'))
        == ['l_rukmi_wortel', 'l_sekar_stroberi'],
        str([t['id'] for t in dd.titipan_hari_ini(s, 'lawang')]))
    cek('papan karsa Semi hari 1 = telur + kain wol',
        sorted(t['id'] for t in dd.titipan_hari_ini(s, 'karsa'))
        == ['k_guru_kain', 'k_sari_telur'],
        str([t['id'] for t in dd.titipan_hari_ini(s, 'karsa')]))

    # Tanaman mentah hanya diundi di musimnya: labu (Gugur) dan wortel
    # (Semi/Gugur) tidak boleh muncul sepanjang Panas, bukan cuma hari ini.
    panas = set()
    for h in range(1, 29):
        panas |= {t['id'] for t in dd.titipan_hari_ini(_hari('Panas', h), 'lawang')}
    cek('Panas tidak pernah menitipkan labu atau wortel',
        'l_warga_labu' not in panas and 'l_rukmi_wortel' not in panas,
        str(sorted(panas)))
    cek('papan Panas punya 5 calon (jagung, tomat, kayu, acar, saus)',
        len(_calon('lawang', 'Panas')) == 5, str(len(_calon('lawang', 'Panas'))))

    # Variasi: papan tidak boleh menempelkan dua entri yang sama terus.
    ragam = set()
    for musim in SEASONS:
        for h in range(1, 13):
            ragam |= {t['id'] for t in dd.titipan_hari_ini(_hari(musim, h), 'lawang')}
    cek('papan lawang berganti-ganti antar hari (>=4 id berbeda)',
        len(ragam) >= 4, f'{len(ragam)} id: {sorted(ragam)}')

    # Membaca papan tidak boleh mengubah state (rng lokal, bukan global).
    segar = _hari('Semi', 1)
    sebelum = copy.deepcopy(segar.__dict__)
    dd.titipan_hari_ini(segar, 'karsa')
    dd.titipan_hari_ini(segar, 'lawang')
    cek('membaca papan tidak mengubah state', segar.__dict__ == sebelum)

    # selesai_hari_ini hanya percaya catatan hari ini.
    cek('selesai_hari_ini kosong tanpa catatan', dd.selesai_hari_ini(segar) == [])
    segar.titipan = {'hari': kunci, 'selesai': ['x']}
    cek('selesai_hari_ini membaca catatan hari ini', dd.selesai_hari_ini(segar) == ['x'])
    segar.titipan = {'hari': '0-0-0', 'selesai': ['x']}
    cek('selesai_hari_ini mengabaikan catatan hari lain', dd.selesai_hari_ini(segar) == [])


# ─── Imbalan, nama, bar ──────────────────────────────────────────────────────

def uji_imbalan():
    buruk = []
    for t in TITIPAN:
        emas = dd.imbalan(t)
        polos = sell_price(t['item']) * t['n']
        rasio = emas / polos
        if emas % 5 or emas < 5 or emas <= polos or not (1.25 <= rasio <= 1.35):
            buruk.append((t['id'], emas, polos, round(rasio, 4)))
    cek('imbalan bulat 5G, minimal 5G, selalu di atas harga jual', not buruk, str(buruk))
    cek('imbalan ~1,25-1,35x harga Warung',
        not buruk or all(1.25 <= b[3] <= 1.35 for b in buruk if b[3]),
        str(buruk[:3]))

    pakai = {t['id']: dd.imbalan(t) for t in TITIPAN}
    for tid, harap in (('k_sari_telur', 125), ('l_rukmi_lobak', 100),
                       ('k_maya_kue', 235), ('l_warga_saus', 360)):
        cek(f'imbalan {tid} = {harap}G', pakai.get(tid) == harap, str(pakai.get(tid)))


def uji_nama():
    by_id = {t['id']: t for t in TITIPAN}
    for tid, harap in (('k_sari_telur', 'Bu Sari'), ('l_rukmi_lobak', 'Mbah Rukmi'),
                       ('l_warga_tomat', 'Warga Lawang'), ('k_raka_wol', 'Pak Raka')):
        cek(f'nama peminta {tid} = {harap}', dd.nama_peminta(by_id[tid]) == harap,
            dd.nama_peminta(by_id[tid]))
    # Warga tanpa npc memakai nama papan, bukan id mentah.
    for papan, harap in (('karsa', PAPAN_TITIPAN['karsa']['warga']),
                         ('lawang', PAPAN_TITIPAN['lawang']['warga'])):
        t = {'id': 'x', 'papan': papan, 'npc': None, 'item': 'kayu', 'n': 1}
        cek(f'nama peminta tanpa npc papan {papan} = {harap}',
            dd.nama_peminta(t) == harap, dd.nama_peminta(t))


def uji_bar():
    cek('bar (50,10) = #####-----', dd.bar_kerukunan(50, 10) == '#####-----',
        dd.bar_kerukunan(50, 10))
    cek('bar (200,4) dijepit = ####', dd.bar_kerukunan(200, 4) == '####',
        dd.bar_kerukunan(200, 4))
    cek('bar 0 = 20 strip', dd.bar_kerukunan(0) == '-' * 20, dd.bar_kerukunan(0))
    cek('bar 100 = 20 pagar', dd.bar_kerukunan(100) == '#' * 20, dd.bar_kerukunan(100))
    cek('bar 50 = 10 pagar + 10 strip',
        dd.bar_kerukunan(50) == '#' * 10 + '-' * 10, dd.bar_kerukunan(50))


# ─── Lomba: nilai, baris, pilihan ────────────────────────────────────────────

def uji_nilai_lawan():
    for kategori in ('masak', 'panen'):
        k = LOMBA_ANTAR_DESA['kategori'][kategori]
        nilai = [dd.nilai_lawan(_hari('Semi', 1, tahun=y), kategori) for y in (1, 2, 3)]
        batas = []
        for i, y in enumerate((1, 2, 3)):
            lo = k['dasar'] + k['naik'] * (y - 1)
            batas.append(lo <= nilai[i] <= lo + k['acak'])
        cek(f'nilai lawan {kategori} di dalam dasar..dasar+naik+acak', all(batas),
            str(nilai))
        if kategori == 'masak':
            cek('nilai lawan masak naik ketat tiap tahun',
                nilai[0] < nilai[1] < nilai[2], str(nilai))
        else:
            cek('nilai lawan panen tidak pernah turun',
                nilai[0] <= nilai[1] <= nilai[2], str(nilai))
        # Tetap sepanjang tahun yang sama (benih rng per tahun+kategori).
        cek(f'nilai lawan {kategori} tetap di tahun yang sama',
            dd.nilai_lawan(_hari('Semi', 1, tahun=2), kategori) == nilai[1],
            str(dd.nilai_lawan(_hari('Semi', 1, tahun=2), kategori)))


def uji_baris_lomba():
    ev = _ev_lomba()
    s = _hari('Semi', 1)
    cek('baris lomba jauh hari menyebut tanggal dan tempat',
        dd.baris_lomba(s) == f"{ev['name']}: {ev['season'].capitalize()} "
                             f"hari ke-{ev['day']} di Dukuh Lawang",
        str(dd.baris_lomba(s)))

    hari_h = _tanggal_lomba()
    cek('baris lomba hari-H menyebut jam dan juri',
        dd.baris_lomba(hari_h) == f"{ev['name']}: HARI INI 09.00-17.00, "
                                  f"temui juri di lapangan",
        str(dd.baris_lomba(hari_h)))

    hari_h.lomba = {'tahun': 1, 'masak': {'item': 'saus_tomat', 'n': 1,
                                          'nilai': 275, 'lawan': 182, 'menang': True}}
    cek('baris lomba mengutamakan hasil tahun ini di hari-H',
        dd.baris_lomba(hari_h) == f"{ev['name']} tahun ini: Lomba Masak MENANG",
        str(dd.baris_lomba(hari_h)))

    hari_h.lomba = {'tahun': 1, 'masak': {'menang': False}, 'panen': {'menang': True}}
    cek('baris lomba meringkas kedua kategori',
        dd.baris_lomba(hari_h) == f"{ev['name']} tahun ini: "
                                  f"Lomba Masak kalah, Panen Terbesar MENANG",
        str(dd.baris_lomba(hari_h)))

    # Catatan tahun lalu tidak boleh terus dipajang di tahun baru.
    hari_h.lomba = {'tahun': 0, 'masak': {'menang': True}}
    cek('catatan lomba tahun lalu tidak dipakai',
        dd.baris_lomba(hari_h) == f"{ev['name']}: HARI INI 09.00-17.00, "
                                  f"temui juri di lapangan",
        str(dd.baris_lomba(hari_h)))

    simpan = SEASONAL_EVENTS.pop('lomba_antar_desa')
    try:
        cek('baris lomba None bila acara tidak terdaftar', dd.baris_lomba(s) is None,
            str(dd.baris_lomba(s)))
    finally:
        SEASONAL_EVENTS['lomba_antar_desa'] = simpan


def uji_pilihan_lomba():
    s = _hari('Semi', 1)
    s.inventory = {'saus_tomat': 1, 'kue_telur': 1, 'acar_lobak': 1,
                   'tomat': 15, 'labu': 2, 'lobak': 3}
    cek('pilihan masak terbaik = saus, kue, acar',
        dd.pilihan_lomba(s, 'masak') == [('saus_tomat', 1, 275), ('kue_telur', 1, 180),
                                         ('acar_lobak', 1, 145)],
        str(dd.pilihan_lomba(s, 'masak')))
    cek('pilihan panen mengambil tumpukan terbesar lebih dulu',
        dd.pilihan_lomba(s, 'panen') == [('tomat', 10, 650), ('labu', 2, 132),
                                         ('lobak', 3, 78)],
        str(dd.pilihan_lomba(s, 'panen')))

    s.inventory = {'pakan': 1, 'kain_wol': 1}
    cek('pakan/kain wol tidak boleh ikut lomba masak',
        dd.pilihan_lomba(s, 'masak') == [], str(dd.pilihan_lomba(s, 'masak')))
    s.inventory = {'telur': 5}
    cek('barang mentah bukan olahan tidak ikut lomba masak',
        dd.pilihan_lomba(s, 'masak') == [], str(dd.pilihan_lomba(s, 'masak')))
    s.inventory = {}
    cek('tanpa isi pilihan kosong', dd.pilihan_lomba(s, 'panen') == [],
        str(dd.pilihan_lomba(s, 'panen')))

    # Panen sengaja TIDAK menyaring musim: kebun pemain boleh panen kapan saja.
    semi = _hari('Semi', 1, )
    semi.inventory = {'labu': 2}
    cek('panen labu tetap boleh di musim Semi',
        dd.pilihan_lomba(semi, 'panen') == [('labu', 2, 132)],
        str(dd.pilihan_lomba(semi, 'panen')))

    seri = _hari('Semi', 1)
    seri.inventory = {'stroberi': 2, 'jamur': 2}
    cek('nilai seri diurutkan menurut id (jamur sebelum stroberi)',
        [r[0] for r in dd.pilihan_lomba(seri, 'panen')] == ['jamur', 'stroberi'],
        str(dd.pilihan_lomba(seri, 'panen')))


# ─── Tahap, syarat, jadwal, pesan ────────────────────────────────────────────

def uji_tahap():
    qc = QuestController(_state())
    cek('tahap_babak(1) = 0,1,2', [q['s'] for q in qc.tahap_babak(1)] == [0, 1, 2],
        str([q['s'] for q in qc.tahap_babak(1)]))
    cek('tahap_babak(2) = 3..6', [q['s'] for q in qc.tahap_babak(2)] == [3, 4, 5, 6],
        str([q['s'] for q in qc.tahap_babak(2)]))
    cek('tahap_dua_desa = 0..6',
        [q['s'] for q in qc.tahap_dua_desa()] == list(range(7)),
        str([q['s'] for q in qc.tahap_dua_desa()]))
    for tahap, harap in ((0, 1), (2, 1), (3, 2), (6, 2), (7, 2), (99, 2)):
        cek(f'babak_aktif({tahap}) = {harap}', qc.babak_aktif(tahap) == harap,
            str(qc.babak_aktif(tahap)))


def uji_syarat():
    gotong = {'gotong_royong': True}
    cek('opsi gotong terkunci sebelum tahap 6',
        dd.syarat_opsi(_hari('Semi', 1, dua_desa_stage=5, gotong_royong_hari=1), gotong)
        == (False, 'Mulai esok pagi, di longsor Dukuh Lawang'),
        str(dd.syarat_opsi(_hari('Semi', 1, dua_desa_stage=5, gotong_royong_hari=1), gotong)))
    s = _hari('Semi', 1, jam=19, dua_desa_stage=6, gotong_royong_hari=1)
    cek('opsi gotong terkunci di luar 06.00-18.00',
        dd.syarat_opsi(s, gotong) == (False, 'Penggalian hanya 06.00-18.00'),
        str(dd.syarat_opsi(s, gotong)))
    s = _hari('Semi', 1, jam=9, scene='farm', dua_desa_stage=6, gotong_royong_hari=1)
    cek('opsi gotong terkunci di luar longsor Lawang',
        dd.syarat_opsi(s, gotong) == (False, 'Penggalian ada di longsor Dukuh Lawang'),
        str(dd.syarat_opsi(s, gotong)))
    s = _hari('Semi', 1, jam=9, scene='lawang', dua_desa_stage=6, gotong_royong_hari=1)
    cek('opsi gotong terbuka tepat waktu dan tempat',
        dd.syarat_opsi(s, gotong) == (True, 'Buka jalan lama bersama dua desa'),
        str(dd.syarat_opsi(s, gotong)))

    b = {}
    s = _hari('Semi', 1, dua_desa_stage=3, kerukunan=25)
    cek('opsi biasa menyebut kerukunan sejak babak 2',
        dd.syarat_opsi(s, b) == (True, 'Cerita Dua Desa - Kerukunan 25'),
        str(dd.syarat_opsi(s, b)))
    s = _hari('Semi', 1, dua_desa_stage=2)
    cek('opsi biasa tanpa angka sebelum babak 2',
        dd.syarat_opsi(s, b) == (True, 'Cerita Dua Desa'), str(dd.syarat_opsi(s, b)))

    gotong_opsi = [o for per_tahap in DUA_DESA_OPSI.values()
                   for o in per_tahap.values() if o[0] == 'Mulai Gotong Royong']
    cek('DUA_DESA_OPSI gotong memakai syarat yang diuji',
        len(gotong_opsi) == 2 and all(o[2:] == ({'gotong_royong': True},)
                                      for o in gotong_opsi),
        str(gotong_opsi))


def uji_jadwal():
    lomba = _tanggal_lomba()
    cek('hari lomba: sekar memakai JADWAL_LOMBA',
        dd.jadwal_npc('sekar', lomba) == JADWAL_LOMBA['sekar'],
        str(dd.jadwal_npc('sekar', lomba)))

    gotong = _hari('Semi', 1, jam=9, dua_desa_stage=6, gotong_royong_hari=1)
    cek('gotong royong: arya memakai JADWAL_GOTONG_ROYONG',
        dd.jadwal_npc('arya', gotong) == JADWAL_GOTONG_ROYONG['arya'],
        str(dd.jadwal_npc('arya', gotong)))

    terbuka = _hari('Semi', 1, dua_desa_stage=7, jalan_lama_terbuka=True)
    cek('jalan terbuka: maya memakai JADWAL_JALAN_TERBUKA',
        dd.jadwal_npc('maya', terbuka) == JADWAL_JALAN_TERBUKA['maya'],
        str(dd.jadwal_npc('maya', terbuka)))

    biasa = _hari('Semi', 1)
    cek('tanpa acara: sari kembali ke SCHEDULES',
        dd.jadwal_npc('sari', biasa) == SCHEDULES.get('sari', []),
        str(dd.jadwal_npc('sari', biasa)))
    cek('npc tak dikenal tanpa jadwal', dd.jadwal_npc('entah_siapa', biasa) == [],
        str(dd.jadwal_npc('entah_siapa', biasa)))

    # Prioritas: lomba menang atas gotong royong, gotong menang atas jalan.
    dua = _tanggal_lomba(dua_desa_stage=6, gotong_royong_hari=1, jalan_lama_terbuka=True)
    cek('prioritas: lomba > gotong royong',
        dd.jadwal_npc('kades_hardjo', dua) == JADWAL_LOMBA['kades_hardjo'],
        str(dd.jadwal_npc('kades_hardjo', dua)))
    cek('prioritas: gotong royong > jalan terbuka',
        dd.jadwal_npc('arya', gotong) == JADWAL_GOTONG_ROYONG['arya'],
        str(dd.jadwal_npc('arya', gotong)))


def uji_pesan_pagi():
    ev = _ev_lomba()
    cek('pesan pagi hari-H menyebut lomba dan jam',
        dd.pesan_pagi(_tanggal_lomba()) ==
        "Hari ini: Lomba Antar-Desa!\nDi lapangan Dukuh Lawang, 09.00-17.00.",
        repr(dd.pesan_pagi(_tanggal_lomba())))
    cek('pesan pagi sehari sebelum lomba',
        dd.pesan_pagi(_hari(ev['season'].capitalize(), ev['day'] - 1)) ==
        "Besok: Lomba Antar-Desa di Dukuh Lawang.\nSiapkan masakan dan panen terbaikmu!",
        repr(dd.pesan_pagi(_hari(ev['season'].capitalize(), ev['day'] - 1))))
    gotong = _hari('Semi', 1, dua_desa_stage=6, gotong_royong_hari=1)
    cek('pesan pagi hari gotong royong',
        dd.pesan_pagi(gotong) ==
        "Warga Karsa berangkat ke Dukuh Lawang\nuntuk menggali longsor bersama.",
        repr(dd.pesan_pagi(gotong)))
    cek('pesan pagi hari biasa kosong', dd.pesan_pagi(_hari('Semi', 1)) is None,
        repr(dd.pesan_pagi(_hari('Semi', 1))))


# ─── Alur lewat QuestController ──────────────────────────────────────────────

def uji_maju():
    s = _state(dua_desa_stage=2)
    qc = QuestController(s)
    p = Papan()
    cek('maju menolak mundur', qc.maju_dua_desa(1, p) is False)
    cek('maju mundur tidak memberi pesan', p.pesan == [], str(p.pesan))
    cek('maju 2->3 diterima', qc.maju_dua_desa(3, p) is True, str(s.dua_desa_stage))
    cek('maju 2->3 memberi pesan Juru Titip',
        p.pesan == ['Cerita Dua Desa: Juru Titip. Lihat quest (J).'], str(p.pesan))
    # Ulangi dengan stage 6 supaya pesannya bersih.
    s6 = _state(dua_desa_stage=6)
    p3 = Papan()
    QuestController(s6).maju_dua_desa(7, p3)
    cek('maju 6->7 memberi pesan babak selesai',
        p3.pesan == ['Cerita Dua Desa: babak 2 selesai.'], str(p3.pesan))


def uji_pilih_mitra():
    s = _hari('Semi', 1)
    qc = QuestController(s)
    p = Papan()
    cek('pilih mitra karsa diterima', qc.pilih_mitra('karsa', p) is True)
    cek('mitra tercatat karsa', s.mitra_desa == 'karsa', s.mitra_desa)
    cek('bonus benih karsa = stroberi + wortel 5',
        s.inventory == {'lobak_seed': 3, 'stroberi_seed': 5, 'wortel_seed': 5}
        or all(s.inventory.get(k, 0) >= v for k, v in
               {'stroberi_seed': 5, 'wortel_seed': 5}.items()),
        str(s.inventory))
    cek('pilih mitra menutup babak 1 (tahap 3)', s.dua_desa_stage == 3,
        str(s.dua_desa_stage))
    cek('pilih mitra memberi satu pesan bonus', len(p.pesan) == 1, str(p.pesan))
    cek('pesan bonus menyebut nama mitra',
        'mitra' in p.pesan[0] and MITRA_DESA['karsa']['nama'] in p.pesan[0],
        str(p.pesan[0]))
    cek('pilih mitra kedua diabaikan', qc.pilih_mitra('lawang', p) is False)
    cek('desa tak dikenal ditolak', QuestController(_state()).pilih_mitra('entah') is False)

    lw = _hari('Semi', 1, inventory={'lobak_seed': 3})
    cek('pilih mitra lawang memberi pakan 15',
        QuestController(lw).pilih_mitra('lawang') is True and lw.inventory['pakan'] == 15,
        str(lw.inventory))


def uji_kerukunan():
    for awal, n, harap_naik, harap_akhir in ((95, 20, 5, 100), (10, -50, -10, 0),
                                             (100, 5, 0, 100), (50, 10, 10, 60)):
        s = _state(kerukunan=awal)
        naik = QuestController(s).tambah_kerukunan(n)
        cek(f'kerukunan {awal}{n:+d} -> {harap_akhir} (naik {harap_naik})',
            (naik, s.kerukunan) == (harap_naik, harap_akhir), f'{naik}, {s.kerukunan}')


def uji_serahkan():
    papan_kosong = _state(dua_desa_stage=2)
    cek('titipan ditolak sebelum babak 2',
        QuestController(papan_kosong).serahkan_titipan('karsa', 1) == '')
    cek('indeks 0 ditolak',
        QuestController(_hari('Semi', 1, dua_desa_stage=3)).serahkan_titipan('lawang', 0)
        == '')
    cek('indeks 99 ditolak',
        QuestController(_hari('Semi', 1, dua_desa_stage=3)).serahkan_titipan('lawang', 99)
        == '')

    kurang = _hari('Semi', 1, dua_desa_stage=3)
    cek('barang kurang menyebut kebutuhan dan milik',
        QuestController(kurang).serahkan_titipan('lawang', 1) ==
        'Barang kurang: butuh Wortel x3 (punya 0).',
        repr(QuestController(kurang).serahkan_titipan('lawang', 1)))

    s = _hari('Semi', 1, dua_desa_stage=3, inventory={'wortel': 3, 'telur': 3})
    qc = QuestController(s)
    emas_awal = s.gold
    pesan = qc.serahkan_titipan('lawang', 1)
    cek('antar titipan lawang memberi imbalan dan kerukunan',
        pesan == 'Mbah Rukmi: Terima kasih! +135G, Kerukunan +5', repr(pesan))
    cek('emas bertambah 135', s.gold == emas_awal + 135, f'{emas_awal} -> {s.gold}')
    cek('kerukunan naik 5', s.kerukunan == 5, str(s.kerukunan))
    cek('hati Mbah Rukmi naik 0,5', s.npc_hearts.get('mbah_rukmi') == 0.5,
        str(s.npc_hearts))
    cek('wortel habis dari tas', 'wortel' not in s.inventory, str(s.inventory))
    cek('catatan titipan hari ini menyimpan id',
        s.titipan.get('selesai') == ['l_rukmi_wortel']
        and s.titipan.get('hari') == dd.kunci_hari(s), str(s.titipan))
    cek('statistik titipan lawang dihitung', s.stats.get('titipan_lawang') == 1,
        str(s.stats.get('titipan_lawang')))

    pesan2 = qc.serahkan_titipan('karsa', 1)
    cek('antar titipan karsa kedua menutup tahap Juru Titip',
        pesan2 == 'Bu Sari: Terima kasih! +125G, Kerukunan +5\n'
                  'Cerita Dua Desa: Akar Perselisihan. Lihat quest (J).',
        repr(pesan2))
    cek('tahap maju ke 4 setelah dua papan dilayani', s.dua_desa_stage == 4,
        str(s.dua_desa_stage))
    cek('emas total bertambah 260', s.gold == emas_awal + 260, f'{emas_awal} -> {s.gold}')
    cek('statistik titipan karsa dihitung', s.stats.get('titipan_karsa') == 1,
        str(s.stats.get('titipan_karsa')))

    cek('titipan hari yang sama tidak bisa diantar dua kali',
        qc.serahkan_titipan('lawang', 1) == 'Titipan itu sudah kau antar hari ini.',
        repr(qc.serahkan_titipan('lawang', 1)))


def uji_lomba():
    ev = _ev_lomba()
    isi = {'saus_tomat': 1, 'kue_telur': 1, 'acar_lobak': 1,
           'tomat': 15, 'labu': 2, 'lobak': 3}

    di_luar = _hari(ev['season'].capitalize(), ev['day'] - 1, jam=9,
                    mitra_desa='karsa', inventory=isi)
    cek('lomba tidak bisa diikuti di luar hari-H',
        QuestController(di_luar).ikut_lomba('masak', 1) == '')
    tanpa_mitra = _tanggal_lomba(mitra_desa='', inventory=isi)
    cek('lomba butuh desa mitra', QuestController(tanpa_mitra).ikut_lomba('masak', 1) == '')

    # Masak menang: calon terbaik (275) di atas lawan tahun ini.
    s = _tanggal_lomba(mitra_desa='karsa', inventory=dict(isi))
    emas_awal = s.gold
    lawan = dd.nilai_lawan(s, 'masak')
    calon = dd.pilihan_lomba(s, 'masak')
    menang, naik, harap = _pesan_lomba('masak', calon[0], lawan)
    pesan = QuestController(s).ikut_lomba('masak', 1)
    cek('lomba masak: calon terbaik menang', menang, str((calon[0], lawan)))
    cek('lomba masak: pesan hasil menang', pesan == harap, repr(pesan))
    cek('lomba masak: emas hadiah 300',
        s.gold == emas_awal + LOMBA_ANTAR_DESA['kategori']['masak']['hadiah'],
        f'{emas_awal} -> {s.gold}')
    cek('lomba masak: kerukunan +15', s.kerukunan == naik == 15, str(s.kerukunan))
    cek('lomba masak: hati kedua juri penuh',
        all(s.npc_hearts.get(j) == 1.0 for j in LOMBA_ANTAR_DESA['juri']),
        str(s.npc_hearts))
    cek('lomba masak: hasil tercatat tahun ini',
        s.lomba.get('tahun') == s.year and s.lomba['masak']['menang'] is True,
        str(s.lomba))
    cek('lomba masak: saus tomat terpakai', 'saus_tomat' not in s.inventory,
        str(s.inventory))
    cek('lomba masak: tidak bisa dua kali setahun',
        QuestController(s).ikut_lomba('masak', 1) == 'Kau sudah ikut Lomba Masak tahun ini.',
        repr(QuestController(s).ikut_lomba('masak', 1)))

    # Masak kalah: calon terlemah (145) di bawah lawan tahun ini.
    k = _tanggal_lomba(mitra_desa='karsa', inventory=dict(isi))
    k_awal = k.gold
    lawan = dd.nilai_lawan(k, 'masak')
    calon = dd.pilihan_lomba(k, 'masak')
    kalah, naik, harap = _pesan_lomba('masak', calon[-1], lawan)
    pesan = QuestController(k).ikut_lomba('masak', len(calon))
    cek('lomba masak: calon terlemah kalah', not kalah, str((calon[-1], lawan)))
    cek('lomba masak: pesan hasil kalah', pesan == harap, repr(pesan))
    cek('lomba masak: kalah tidak memberi emas', k.gold == k_awal, f'{k_awal} -> {k.gold}')
    cek('lomba masak: kalah tetap menaikkan kerukunan 5', k.kerukunan == 5,
        str(k.kerukunan))

    # Panen menang: 10 tomat (650) di atas lawan.
    p = _tanggal_lomba(mitra_desa='lawang', inventory=dict(isi))
    p_awal = p.gold
    lawan = dd.nilai_lawan(p, 'panen')
    calon = dd.pilihan_lomba(p, 'panen')
    menang, naik, harap = _pesan_lomba('panen', calon[0], lawan)
    pesan = QuestController(p).ikut_lomba('panen', 1)
    cek('lomba panen: tumpukan terbesar menang', menang, str((calon[0], lawan)))
    cek('lomba panen: pesan hasil menang', pesan == harap, repr(pesan))
    cek('lomba panen: hadiah 200', p.gold == p_awal + 200, f'{p_awal} -> {p.gold}')
    cek('lomba panen: sisa tomat 5', p.inventory.get('tomat') == 5, str(p.inventory))
    cek('lomba panen: kerukunan +15', p.kerukunan == 15, str(p.kerukunan))

    # Panen kalah: satu lobak (26) jauh di bawah lawan.
    q = _tanggal_lomba(mitra_desa='lawang', inventory={'lobak': 1})
    q_awal = q.gold
    lawan = dd.nilai_lawan(q, 'panen')
    calon = dd.pilihan_lomba(q, 'panen')
    kalah, naik, harap = _pesan_lomba('panen', calon[0], lawan)
    pesan = QuestController(q).ikut_lomba('panen', 1)
    cek('lomba panen: satu lobak kalah', not kalah, str((calon[0], lawan)))
    cek('lomba panen: pesan hasil kalah', pesan == harap, repr(pesan))
    cek('lomba panen: kalah tidak memberi emas', q.gold == q_awal, f'{q_awal} -> {q.gold}')


def uji_buka_jalan():
    s = _state(kerukunan=50, dua_desa_stage=6, gotong_royong_hari=6)
    dunia = Dunia()
    p = Papan()
    qc = QuestController(s)
    cek('buka jalan lama diterima', qc.buka_jalan_lama(p, dunia) is True)
    cek('jalan lama tercatat terbuka', s.jalan_lama_terbuka is True)
    cek('gotong royong selesai (hari 0)', s.gotong_royong_hari == 0,
        str(s.gotong_royong_hari))
    cek('kerukunan naik 20', s.kerukunan == 70, str(s.kerukunan))
    cek('tahap maju ke 7', s.dua_desa_stage == 7, str(s.dua_desa_stage))
    cek('scene dimuat ulang (nama dikosongkan)', dunia.scene_name is None,
        str(dunia.scene_name))
    cek('pesan jalan terbuka tepat',
        p.pesan == ['Babak 2 selesai: jalan lama ke Gua Sang Hyang\n'
                    'terbuka! Kerukunan +20'], str(p.pesan))
    cek('buka jalan lama kedua diabaikan', qc.buka_jalan_lama(p, dunia) is False)

    penuh = _state(kerukunan=95, dua_desa_stage=6)
    pp = Papan()
    QuestController(penuh).buka_jalan_lama(pp, Dunia())
    cek('kerukunan dijepit 100 saat jalan terbuka',
        penuh.kerukunan == KERUKUNAN_MAKS == 100, str(penuh.kerukunan))
    cek('pesan menyebut kenaikan yang sungguh terjadi (+5)',
        pp.pesan and pp.pesan[0].endswith('Kerukunan +5'), str(pp.pesan))

    j = _state(day=5)
    cek('jadwalkan gotong royong menerima', QuestController(j).jadwalkan_gotong_royong() is True)
    cek('gotong royong dijadwalkan besok (hari 6)', j.gotong_royong_hari == 6,
        str(j.gotong_royong_hari))
    sudah = _state(day=5, jalan_lama_terbuka=True)
    cek('gotong royong tidak dijadwalkan bila jalan sudah terbuka',
        QuestController(sudah).jadwalkan_gotong_royong() is False)


# ─── Main ────────────────────────────────────────────────────────────────────

def jalankan(nama, fn):
    try:
        fn()
    except Exception:
        traceback.print_exc()
        cek(f'{nama} tanpa pengecualian', False, 'lihat traceback')


def main():
    for nama, fn in (('titipan', uji_titipan), ('imbalan', uji_imbalan),
                     ('nama', uji_nama), ('bar', uji_bar), ('nilai lawan', uji_nilai_lawan),
                     ('baris lomba', uji_baris_lomba), ('pilihan lomba', uji_pilihan_lomba),
                     ('tahap', uji_tahap), ('syarat opsi', uji_syarat),
                     ('jadwal npc', uji_jadwal), ('pesan pagi', uji_pesan_pagi),
                     ('maju', uji_maju), ('pilih mitra', uji_pilih_mitra),
                     ('kerukunan', uji_kerukunan), ('serahkan titipan', uji_serahkan),
                     ('ikut lomba', uji_lomba), ('buka jalan', uji_buka_jalan)):
        jalankan(nama, fn)

    gagal = [h for h in hasil if not h[1]]
    for nama, ok, ket in hasil:
        print(f'  {"LULUS" if ok else "GAGAL"}  {nama:58s} {ket}')
    print(f'{len(hasil) - len(gagal)}/{len(hasil)} lulus')
    sys.stdout.flush()
    os._exit(1 if gagal else 0)


if __name__ == '__main__':
    main()
