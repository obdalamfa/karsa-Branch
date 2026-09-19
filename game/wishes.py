"""wishes.py — Keinginan yang dijanjikan, dan Tekad yang dibayarkannya.

Kenapa modul ini ada, dan kenapa bentuknya begini.

Kalau wish cuma menaikkan motif, ia tidak menambah apa pun: delapan motif
sudah ada dan semuanya meluruh. Yang membuat Wishes bekerja di The Sims 3
adalah bayarannya BERTAHAN — itu bedanya antara "hari ini lancar" dan "aku
sedang membangun sesuatu". Jadi bayarannya di sini adalah **Tekad**, poin yang
tidak pernah meluruh, dan Tekad dibelanjakan untuk perabot dan resep.

Itu bukan pilihan sembarangan. Neraca motif (issue #6) diseimbangkan di
sekitar SUPLAI PERABOT: 54,5% hidup pemain habis mengurus motif, dan
satu-satunya cara menurunkan angka itu adalah perabot yang lebih baik. Jadi
Tekad membeli hal yang langsung mengubah neraca yang pemain rasakan tiap hari.
Papan skor yang tidak bisa dibelanjakan akan diabaikan dalam tiga hari.

PREMIS LAMA YANG DIBUANG. Tiket #7 menduga wish bisa lahir dari mesin otonomi:
ambil kandidat berskor tertinggi SETELAH membuang interaksi yang mengiklankan
motif paling mendesak, dan yang tersisa adalah "keinginan" dan bukan
"kebutuhan". Diukur ulang di tools/proto_wish.py, kedua kolom itu identik di
hampir setiap baris — aksi berskor tertinggi JARANG mengiklankan motif paling
mendesak, jadi menyaringnya tidak membuang apa pun dari puncak. Wish di sini
karena itu datang dari katalog yang ditulis tangan, bukan dari mesin iklan.

SATU PREDIKAT, DUA PEMICU. Tiap wish punya satu fungsi `ukur(state)` dan satu
ambang. Wish "lakukan X" dan wish "punya X" karena itu memakai mesin yang
sama; yang membedakan cuma apakah ambangnya RELATIF terhadap keadaan saat
dijanjikan. Itu sebabnya "panen 5 tanaman" tidak butuh mesin sendiri: ia
mengukur pencacah panen yang sudah ada, dan menyimpan nilainya saat dijanjikan
sebagai dasar.

Pemeriksaannya dijalankan di dua tempat, dengan predikat yang sama:
  - tiap kali sebuah aksi tuntas (supaya "lakukan X" membayar SEKETIKA — itu
    bagian yang memuaskan), dan
  - sekali tiap pagi saat bangun (supaya wish berbentuk keadaan dunia tidak
    perlu diperiksa tiap frame).
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable

# Berapa yang boleh dijanjikan sekaligus, dan berapa yang mengambang.
#
# Sims 3 memakai empat slot janji. Katalog kita jauh lebih kecil, dan dengan
# empat slot pemain hampir tidak pernah harus MEMILIH — padahal memilih itulah
# mekaniknya: menjanjikan satu berarti melepas yang lain. Dua slot membuat
# pilihannya terasa, empat yang mengambang menjaga tawarannya tetap segar.
SLOT_JANJI   = 2
SLOT_AMBANG  = 4

# Diundi ulang tiap pagi. Bangun tidur baru jadi beat yang nyata sejak #10
# (advance_day mensimulasikan malam, bukan melompatinya), jadi ada tempat
# alaminya dan pemain punya satu titik tetap untuk melihat tawaran baru.


@dataclass
class Wish:
    """Satu keinginan yang bisa dijanjikan.

    `ukur` mengembalikan satu angka dari state. `target` dibandingkan dengan
    angka itu — secara MUTLAK kalau `relatif` False ("punya 3 ekor ternak"),
    atau terhadap nilai saat dijanjikan kalau True ("panen 5 lagi").
    """
    id: str
    teks: str
    tekad: int
    ukur: Callable
    target: float
    relatif: bool = True
    # Hanya ditawarkan kalau ini True — mencegah wish yang mustahil atau
    # sudah terlampaui muncul di papan.
    layak: Callable | None = None


def _aksi(state, *nama) -> float:
    """Berapa kali aksi-aksi ini tuntas sejak permainan dimulai."""
    hit = getattr(state, 'aksi_hitung', None) or {}
    return float(sum(hit.get(n, 0) for n in nama))


def _panen(state) -> float:
    st = state.stats
    return float(st.get('lobak_harvested', 0) + st.get('corn_harvested', 0))


def _hati_tertinggi(state) -> float:
    nilai = list((state.npc_hearts or {}).values())
    return float(max(nilai)) if nilai else 0.0


# ─── KATALOG ─────────────────────────────────────────────────────────────────
# Tekad dihargai kasar menurut berapa hari kerja yang dituntut: 1 = sore hari,
# 2 = satu hari, 3-4 = beberapa hari. Harga perabot di belanja Tekad
# diturunkan dari sini, bukan sebaliknya.
KATALOG: list[Wish] = [
    Wish('panen_5', 'Panen 5 hasil kebun', 2, _panen, 5),
    Wish('tambang_4', 'Tambang 4 bongkah mineral', 2,
         lambda s: float(s.stats.get('minerals_mined', 0)), 4),
    Wish('emas_300', 'Kumpulkan 300G lagi', 3,
         lambda s: float(s.gold), 300),
    Wish('masak_2', 'Masak dua kali', 1,
         lambda s: _aksi(s, 'Masak', 'Siapkan Makanan'), 2),
    Wish('santai_3', 'Bersantai tiga kali', 2,
         lambda s: _aksi(s, 'Nonton TV', 'Baca Buku', 'Duduk di Dermaga'), 3),
    Wish('ngobrol_2', 'Duduk mengobrol dua kali', 2,
         lambda s: _aksi(s, 'Duduk Ngobrol'), 2),
    Wish('tidur_3', 'Tidur cukup tiga malam', 2,
         lambda s: float(s.stats.get('malam_cukup', 0)), 3),
    Wish('hadiah_2', 'Beri dua hadiah', 2,
         lambda s: float(s.stats.get('gifts', 0)), 2),

    # ── berbentuk keadaan dunia: mutlak, bukan selisih ──
    Wish('ternak_2', 'Punya dua ekor ternak', 4,
         lambda s: float(len(getattr(s, 'owned_animals', []) or [])), 2,
         relatif=False,
         layak=lambda s: len(getattr(s, 'owned_animals', []) or []) < 2),
    Wish('ternak_4', 'Punya empat ekor ternak', 5,
         lambda s: float(len(getattr(s, 'owned_animals', []) or [])), 4,
         relatif=False,
         layak=lambda s: 2 <= len(getattr(s, 'owned_animals', []) or []) < 4),
    Wish('hati_3', 'Punya seorang teman (3 hati)', 3,
         _hati_tertinggi, 3.0, relatif=False,
         layak=lambda s: _hati_tertinggi(s) < 3.0),
    Wish('hati_6', 'Punya sahabat (6 hati)', 5,
         _hati_tertinggi, 6.0, relatif=False,
         layak=lambda s: 3.0 <= _hati_tertinggi(s) < 6.0),
    Wish('gua_3', 'Turun sampai lantai 3 gua', 4,
         lambda s: float(s.stats.get('deepest_level', 0)), 3,
         relatif=False,
         layak=lambda s: s.stats.get('deepest_level', 0) < 3),
]

_PETA = {w.id: w for w in KATALOG}


def wish_by_id(wid: str) -> Wish | None:
    return _PETA.get(wid)


# ─── PAPAN ───────────────────────────────────────────────────────────────────

def _papan(state) -> dict:
    """Baris state yang dipakai modul ini, dibuat kalau belum ada.

    Disimpan sebagai dict biasa dan bukan dataclass karena GameState.save
    memakai json.dump(__dict__).
    """
    p = getattr(state, 'wishes', None)
    if not isinstance(p, dict):
        p = {}
        state.wishes = p
    p.setdefault('janji', {})      # id -> dasar (nilai ukur saat dijanjikan)
    p.setdefault('ambang', [])     # id yang sedang ditawarkan
    p.setdefault('selesai', [])    # id yang sudah tuntas, tidak ditawarkan lagi
    return p


def _tersedia(state) -> list:
    p = _papan(state)
    out = []
    for w in KATALOG:
        if w.id in p['selesai'] or w.id in p['janji']:
            continue
        if w.layak is not None and not w.layak(state):
            continue
        out.append(w)
    return out


def undi(state, rng=None) -> list:
    """Isi ulang papan tawaran. Dipanggil tiap pagi dari advance_day.

    Yang SUDAH DIJANJIKAN tidak diganggu — itu inti mekaniknya: janji bertahan
    sampai tuntas atau dilepas, sementara sisanya berganti. Kalau yang
    mengambang ikut diundi bersama yang dijanjikan, tidak ada yang hilang saat
    memilih, dan memilih berhenti punya harga.
    """
    p = _papan(state)
    rng = rng or random.Random(state.day * 7919 + 13)
    kandidat = _tersedia(state)
    rng.shuffle(kandidat)
    p['ambang'] = [w.id for w in kandidat[:SLOT_AMBANG]]
    return list(p['ambang'])


def janjikan(state, wid: str) -> tuple[bool, str]:
    """Pindahkan satu wish dari papan tawaran ke slot janji."""
    p = _papan(state)
    w = _PETA.get(wid)
    if w is None:
        return False, 'Keinginan itu tidak ada.'
    if wid in p['janji']:
        return False, 'Sudah dijanjikan.'
    if len(p['janji']) >= SLOT_JANJI:
        return False, (f'Slot janji penuh ({SLOT_JANJI}). Lepas salah satu '
                       f'dulu.')
    # Dasar disimpan SAAT dijanjikan, bukan saat diundi: kalau tidak, pemain
    # yang sudah memanen empat kali sebelum menjanjikan "panen 5" akan
    # menuntaskannya dengan satu panen.
    p['janji'][wid] = w.ukur(state) if w.relatif else 0.0
    return True, f'Dijanjikan: {w.teks}'


def lepas(state, wid: str) -> tuple[bool, str]:
    p = _papan(state)
    if wid not in p['janji']:
        return False, 'Bukan janji yang sedang berjalan.'
    del p['janji'][wid]
    w = _PETA.get(wid)
    return True, f'Dilepas: {w.teks if w else wid}'


def kemajuan(state, wid: str) -> tuple[float, float]:
    """(sudah, perlu) untuk ditampilkan. Keduanya dalam satuan wish itu."""
    w = _PETA.get(wid)
    p = _papan(state)
    if w is None:
        return 0.0, 0.0
    dasar = p['janji'].get(wid, 0.0 if not w.relatif else w.ukur(state))
    kini = w.ukur(state)
    if w.relatif:
        return max(0.0, kini - dasar), float(w.target)
    return kini, float(w.target)


def periksa(state) -> list:
    """Tuntaskan janji yang syaratnya sudah terpenuhi. Return daftar Wish.

    Dipanggil dari dua tempat dengan predikat yang sama: saat sebuah aksi
    tuntas, dan sekali tiap pagi. Tidak ada jalur ketiga, jadi wish berbentuk
    aksi dan wish berbentuk keadaan dunia tidak bisa berselisih.
    """
    p = _papan(state)
    tuntas = []
    for wid in list(p['janji'].keys()):
        w = _PETA.get(wid)
        if w is None:
            del p['janji'][wid]
            continue
        sudah, perlu = kemajuan(state, wid)
        if sudah + 1e-9 >= perlu:
            del p['janji'][wid]
            p['selesai'].append(wid)
            state.tekad = getattr(state, 'tekad', 0) + w.tekad
            tuntas.append(w)
    if tuntas and len(p['ambang']) < SLOT_AMBANG:
        # Papan tidak dibiarkan kosong sampai besok pagi: kalau pemain baru
        # saja menuntaskan sesuatu, saat itulah ia paling ingin melihat yang
        # berikutnya.
        undi(state)
    return tuntas


def catat_aksi(state, nama: str) -> None:
    """Cacah satu aksi yang baru tuntas. Dipanggil dari TimeController.tick."""
    hit = getattr(state, 'aksi_hitung', None)
    if not isinstance(hit, dict):
        hit = {}
        state.aksi_hitung = hit
    hit[nama] = hit.get(nama, 0) + 1


def ringkas(state) -> list:
    """Baris siap-tampil untuk panel. [(judul, isi), ...]"""
    p = _papan(state)
    baris = []
    if p['janji']:
        for wid in p['janji']:
            w = _PETA.get(wid)
            if w is None:
                continue
            sudah, perlu = kemajuan(state, wid)
            baris.append((f'[JANJI] {w.teks}',
                          f'{sudah:g}/{perlu:g}  -> +{w.tekad} Tekad'))
    else:
        baris.append(('[JANJI] (belum ada)',
                      f'Pilih dari tawaran di bawah, maksimal {SLOT_JANJI}.'))
    # Nomornya HARUS dihitung dari daftar yang sudah disaring, bukan dari
    # posisi asli di papan. Versi pertama memakai enumerate() atas `ambang`
    # lalu melewati yang sudah dijanjikan, jadi setelah pemain menjanjikan
    # tawaran pertama, sisanya tampil bernomor 2/3/4 sementara `_wish_action`
    # mengindeks daftar tersaring — menekan 2 menjanjikan tawaran KETIGA.
    # Terlihat langsung di tangkapan layar pertama panel ini.
    for i, wid in enumerate(tawaran(state), 1):
        w = _PETA.get(wid)
        if w is None:
            continue
        baris.append((f'  {i}. {w.teks}', f'+{w.tekad} Tekad'))
    return baris


def tawaran(state) -> list:
    """Id tawaran yang belum dijanjikan, urut sesuai yang tampil di panel.

    Satu-satunya sumber urutan itu, dipakai oleh yang MENGGAMBAR dan yang
    MENERIMA TOMBOL — kalau keduanya menghitungnya sendiri-sendiri, nomor di
    layar dan nomor yang ditekan akan berselisih lagi.
    """
    p = _papan(state)
    return [w for w in p['ambang'] if w not in p['janji']]
