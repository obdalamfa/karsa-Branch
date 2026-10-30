"""dua_desa.py — logika babak 2 Cerita Dua Desa yang tidak butuh mesin game.

Fungsi murni di atas GameState + data.py: titipan harian, Lomba Antar-Desa,
jadwal khusus warga, syarat opsi cerita, dan pesan pagi. Yang MENGUBAH state
dan memberi tahu pemain ada di QuestController; panels.py hanya menampilkan.
Dipisah begini supaya semuanya bisa diperiksa tanpa membuka jendela Ursina.
Lihat docs/CERITA_DUA_DESA.md.
"""
import random

from .data import (CROPS, HUMAN_NPCS, SCHEDULES, SEASONAL_EVENTS, KERUKUNAN_MAKS,
                   TITIPAN, PAPAN_TITIPAN, TITIPAN_PER_HARI, TITIPAN_IMBALAN,
                   LOMBA_ANTAR_DESA, JADWAL_LOMBA, JADWAL_GOTONG_ROYONG,
                   JADWAL_JALAN_TERBUKA)
from .economy import PROCESS_RECIPES, sell_price

# Tahap pertama babak 2 dan tahap Gotong Royong di jalur dua_desa
# (data.QUEST_STAGES). Sebelum TAHAP_BABAK2 papan titipan masih kosong.
TAHAP_BABAK2 = 3
TAHAP_GOTONG = 6
JAM_GOTONG   = (6, 18)


# ─── Titipan ─────────────────────────────────────────────────────────────────

def kunci_hari(state) -> str:
    """'tahun-musim-hari': sama sepanjang satu hari, berganti tiap pagi."""
    return f"{state.year}-{state.season_index}-{state.day_in_season}"


def titipan_hari_ini(state, papan: str) -> list[dict]:
    """Titipan yang tertempel di papan `papan` ('karsa'/'lawang') hari ini.

    Deterministik dari tanggal, jadi simpan-muat tidak mengocok ulang daftar
    dan tidak ada daftar yang perlu disimpan di save. Titipan tanaman mentah
    hanya ikut diundi di musim tanamannya.
    """
    musim = state.get_season()
    calon = [t for t in TITIPAN if t['papan'] == papan
             and (t['item'] not in CROPS or musim in CROPS[t['item']]['seasons'])]
    rng = random.Random(f"titipan-{kunci_hari(state)}-{papan}")
    return rng.sample(calon, min(TITIPAN_PER_HARI, len(calon)))


def selesai_hari_ini(state) -> list[str]:
    """Id titipan yang sudah diantar HARI INI (catatan hari lain diabaikan)."""
    rec = state.titipan or {}
    return list(rec.get('selesai', [])) if rec.get('hari') == kunci_hari(state) else []


def imbalan(titipan: dict) -> int:
    """Emas untuk satu titipan: ~1,3x harga Warung, dibulatkan ke 5G."""
    nilai = sell_price(titipan['item']) * titipan['n'] * TITIPAN_IMBALAN
    return max(5, int(round(nilai / 5.0)) * 5)


def nama_peminta(titipan: dict) -> str:
    npc = titipan.get('npc')
    if npc:
        return HUMAN_NPCS.get(npc, {}).get('name', npc)
    return PAPAN_TITIPAN[titipan['papan']]['warga']


def bar_kerukunan(nilai: int, lebar: int = 20) -> str:
    isi = max(0, min(lebar, int(round(lebar * nilai / KERUKUNAN_MAKS))))
    return '#' * isi + '-' * (lebar - isi)


# ─── Lomba Antar-Desa ────────────────────────────────────────────────────────

def _acara_lomba() -> dict:
    return SEASONAL_EVENTS['lomba_antar_desa']


def hari_lomba(state) -> bool:
    ev = _acara_lomba()
    return state.get_season().lower() == ev['season'] and state.day_in_season == ev['day']


def besok_lomba(state) -> bool:
    ev = _acara_lomba()
    return state.get_season().lower() == ev['season'] and state.day_in_season == ev['day'] - 1


def lomba_berlangsung(state) -> bool:
    j0, j1 = LOMBA_ANTAR_DESA['jam']
    return hari_lomba(state) and j0 <= state.get_hour() < j1


def lawan_lomba(state) -> str | None:
    """Id juru masak desa seberang, atau None kalau pemain belum bermitra."""
    return LOMBA_ANTAR_DESA['lawan'].get(state.mitra_desa)


def nilai_lawan(state, kategori: str) -> int:
    """Nilai lawan satu kategori tahun ini: tetap sepanjang tahun, naik tiap tahun."""
    k = LOMBA_ANTAR_DESA['kategori'][kategori]
    rng = random.Random(f"lomba-{state.year}-{kategori}")
    return k['dasar'] + k['naik'] * max(0, state.year - 1) + rng.randint(0, k['acak'])


def catatan_lomba(state) -> dict:
    """Hasil lomba TAHUN INI; kosong kalau belum ikut atau catatannya tahun lalu."""
    rec = state.lomba or {}
    return rec if rec.get('tahun') == state.year else {}


def baris_lomba(state) -> str | None:
    """Satu baris Lomba Antar-Desa untuk panel J, dipakai teks mentahnya
    (UIManager._quest_dua_desa_lines) dan kartunya (panel_kartu): hasil tahun
    ini, hari H, atau kapan lomba berikutnya."""
    ev = SEASONAL_EVENTS.get('lomba_antar_desa')
    if not ev:
        return None
    hasil = catatan_lomba(state)
    kategori = LOMBA_ANTAR_DESA['kategori']
    if any(k in hasil for k in kategori):
        ringkas = ', '.join(f"{kategori[k]['nama']} {'MENANG' if hasil[k]['menang'] else 'kalah'}"
                            for k in kategori if k in hasil)
        return f"{ev['name']} tahun ini: {ringkas}"
    if hari_lomba(state):
        j0, j1 = LOMBA_ANTAR_DESA['jam']
        return f"{ev['name']}: HARI INI {j0:02d}.00-{j1:02d}.00, temui juri di lapangan"
    from .scenes import SCENES
    tempat = getattr(SCENES.get(ev['scene']), 'display', ev['scene'])
    return f"{ev['name']}: {ev['season'].capitalize()} hari ke-{ev['day']} di {tempat}"


def pilihan_lomba(state, kategori: str) -> list[tuple[str, int, int]]:
    """Tiga calon terbaik pemain untuk satu kategori: [(item, jumlah, nilai)].

    Masak = satu olahan, nilainya harga barang. Panen = satu tumpukan hasil
    kebun mentah (maks 'maks' butir), nilainya jumlah x harga.
    """
    inv = state.inventory
    if kategori == 'masak':
        masakan = {r['out'] for r in PROCESS_RECIPES} - set(LOMBA_ANTAR_DESA['bukan_masakan'])
        rows = [(it, 1, sell_price(it)) for it in masakan if inv.get(it, 0) > 0]
    else:
        maks = LOMBA_ANTAR_DESA['kategori']['panen']['maks']
        rows = [(it, min(q, maks), sell_price(it) * min(q, maks))
                for it, q in inv.items() if it in CROPS and q > 0]
    rows.sort(key=lambda r: (-r[2], r[0]))
    return rows[:3]


# ─── Jadwal, syarat opsi, pesan pagi ─────────────────────────────────────────

def gotong_royong_tiba(state) -> bool:
    return (state.dua_desa_stage == TAHAP_GOTONG and state.gotong_royong_hari > 0
            and state.day >= state.gotong_royong_hari)


def jadwal_npc(npc_id: str, state) -> list:
    """Jadwal yang berlaku hari ini untuk `npc_id` (format SCHEDULES).

    Prioritas: hari Lomba > gotong royong > jalan lama terbuka > SCHEDULES.
    Dipanggil EntitiesManager._update_npc_schedules() tiap kali jadwal
    disegarkan, jadi perubahan cerita langsung terlihat tanpa memuat ulang.
    """
    if hari_lomba(state) and npc_id in JADWAL_LOMBA:
        return JADWAL_LOMBA[npc_id]
    if gotong_royong_tiba(state) and npc_id in JADWAL_GOTONG_ROYONG:
        return JADWAL_GOTONG_ROYONG[npc_id]
    if state.jalan_lama_terbuka and npc_id in JADWAL_JALAN_TERBUKA:
        return JADWAL_JALAN_TERBUKA[npc_id]
    return SCHEDULES.get(npc_id, [])


def syarat_opsi(state, syarat: dict) -> tuple[bool, str]:
    """(boleh dipilih, keterangan efek di pie menu) untuk opsi DUA_DESA_OPSI."""
    if syarat.get('gotong_royong'):
        if not gotong_royong_tiba(state):
            return False, 'Mulai esok pagi, di longsor Dukuh Lawang'
        j0, j1 = JAM_GOTONG
        if not (j0 <= state.get_hour() < j1):
            return False, f'Penggalian hanya {j0:02d}.00-{j1:02d}.00'
        if state.scene_name != 'lawang':
            return False, 'Penggalian ada di longsor Dukuh Lawang'
        return True, 'Buka jalan lama bersama dua desa'
    if state.dua_desa_stage >= TAHAP_BABAK2:
        return True, f'Cerita Dua Desa - Kerukunan {state.kerukunan}'
    return True, 'Cerita Dua Desa'


def pesan_pagi(state) -> str | None:
    """Kabar yang diumumkan saat pemain bangun pada hari `state`, atau None."""
    if hari_lomba(state):
        j0, j1 = LOMBA_ANTAR_DESA['jam']
        return f"Hari ini: Lomba Antar-Desa!\nDi lapangan Dukuh Lawang, {j0:02d}.00-{j1:02d}.00."
    if besok_lomba(state):
        return "Besok: Lomba Antar-Desa di Dukuh Lawang.\nSiapkan masakan dan panen terbaikmu!"
    if state.dua_desa_stage == TAHAP_GOTONG and state.day == state.gotong_royong_hari:
        return "Warga Karsa berangkat ke Dukuh Lawang\nuntuk menggali longsor bersama."
    return None
