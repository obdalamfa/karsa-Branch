"""husbandry.py — Cara mengurus hewan, dan cara pemain MELIHAT aturannya.

Pemilik: *"cara ngurus hewan juga dijelasin."* Sebelum modul ini, mengurus
hewan berarti tiga tombol tanpa akibat: Belai (+8 senang), Beri Makan (+1 hati),
Ambil Hasil (hasil muncul dari udara kalau hati >= 2). Tidak ada yang bisa
salah, jadi tidak ada yang perlu dipelajari — dan karena tidak ada yang perlu
dipelajari, tidak ada yang bisa dijelaskan.

Modul ini memberi tiap hewan tiga takaran yang turun tiap hari, satu jadwal
produksi yang bergantung pada ketiganya, dan satu jalur sakit kalau ditelantarkan.
Lalu — bagian yang sama pentingnya — ia menyediakan teks keadaan siap pakai
(`status_lines`, `short_status`) supaya semua itu muncul di pie menu dan di
panel Tani & Ternak. **Aturan yang tidak bisa dilihat pemain bukan aturan.**

Loop hariannya:

    pagi   : kenyang -45, air -55, bersih -30
    siang  : pemain beri makan (+60), beri minum (isi penuh), bersihkan (isi penuh)
    malam  : kalau kenyang >= 40, air >= 30, bersih >= 25 dan tidak sakit,
             hitungan produksi maju satu hari
    lalai  : kenyang atau air menyentuh 0 → +1 hari lalai; 3 hari lalai → SAKIT
    sakit  : tidak menghasilkan apa pun, hati turun tiap hari; sembuh setelah
             dua hari berturut-turut kenyang/air/bersih semua >= 60

Angkanya dipilih supaya ritmenya jelas: **makan dan minum tiap hari, bersihkan
kandang tiap tiga hari.** Bukan angka acak — itu memang ritme kandang sungguhan.
"""
from __future__ import annotations

# ─── AMBANG ──────────────────────────────────────────────────────────────────
SUSUT_KENYANG = 45
SUSUT_AIR     = 55
SUSUT_BERSIH  = 30

ISI_PAKAN   = 60     # satu ikat pakan
ISI_MINUM   = 100    # seember penuh dari sumur
ISI_BERSIH  = 100

MIN_KENYANG_PRODUKSI = 40
MIN_AIR_PRODUKSI     = 30
MIN_BERSIH_PRODUKSI  = 25

LALAI_JADI_SAKIT = 3
SEMBUH_BUTUH_HARI = 2
AMBANG_SEHAT = 60


# ─── ATURAN PER SPESIES ──────────────────────────────────────────────────────
# `tiap` = jeda hari antar hasil. Ayam bertelur tiap hari, domba dicukur
# sebulan sekali — di skala game itu 5 hari. `pakan` = item yang diterima,
# dicoba berurutan dari inventori pemain.
SPECIES_CARE: dict[str, dict] = {
    'sapi': {
        'kandang': True,
        'label': 'Sapi', 'produk': 'susu', 'produk_label': 'Susu',
        'tiap': 1, 'jumlah': 1, 'aksi': 'Perah', 'siap_teks': 'Siap diperah',
        'pakan': ['rumput', 'jerami', 'jagung'], 'harga': 40,
        'catatan': 'Sapi perah butuh air paling banyak — susu 87% air.',
    },
    'ayam': {
        'kandang': True,
        'label': 'Ayam', 'produk': 'telur', 'produk_label': 'Telur',
        'tiap': 1, 'jumlah': 1, 'aksi': 'Ambil Telur', 'siap_teks': 'Ada telur di sarang',
        'pakan': ['jagung', 'dedak', 'kacang_hijau'], 'harga': 30,
        'catatan': 'Ayam berhenti bertelur kalau kandang kotor atau kekurangan pakan.',
    },
    'bebek': {
        'kandang': True,
        'label': 'Bebek', 'produk': 'telur_bebek', 'produk_label': 'Telur Bebek',
        'tiap': 2, 'jumlah': 1, 'aksi': 'Ambil Telur', 'siap_teks': 'Ada telur bebek',
        'pakan': ['dedak', 'jagung', 'bayam'], 'harga': 38,
        'catatan': 'Bebek perlu air lebih sering daripada unggas lain.',
    },
    'kambing': {
        'kandang': True,
        'label': 'Kambing', 'produk': 'susu_kambing', 'produk_label': 'Susu Kambing',
        'tiap': 2, 'jumlah': 1, 'aksi': 'Perah', 'siap_teks': 'Siap diperah',
        'pakan': ['rumput', 'jerami', 'ubi_jalar'], 'harga': 45,
        'catatan': 'Kambing paling tahan pakan seadanya, tapi kandang basah bikin sakit.',
    },
    'domba': {
        'kandang': True,
        'label': 'Domba', 'produk': 'wol', 'produk_label': 'Wol',
        'tiap': 5, 'jumlah': 1, 'aksi': 'Cukur', 'siap_teks': 'Bulu siap dicukur',
        'pakan': ['rumput', 'jerami'], 'harga': 55,
        'catatan': 'Wol tumbuh pelan: sekali cukur per lima hari.',
    },
    'kuda': {
        'kandang': True,
        'label': 'Kuda', 'produk': None, 'produk_label': None,
        'tiap': 0, 'jumlah': 0, 'aksi': None, 'siap_teks': None,
        'pakan': ['rumput', 'jerami', 'wortel'], 'harga': 0,
        'catatan': 'Kuda tidak menghasilkan apa-apa, tapi tetap harus diberi makan.',
    },
    'kucing': {
        'kandang': False,
        'label': 'Kucing', 'produk': None, 'produk_label': None,
        'tiap': 0, 'jumlah': 0, 'aksi': None, 'siap_teks': None,
        'pakan': ['ikan', 'telur', 'susu'], 'harga': 0,
        'catatan': 'Kucing menjaga lumbung dari tikus. Beri makan, jangan dikandangkan.',
    },
    'kelinci': {
        'kandang': False,
        'label': 'Kelinci', 'produk': None, 'produk_label': None,
        'tiap': 0, 'jumlah': 0, 'aksi': None, 'siap_teks': None,
        'pakan': ['wortel', 'bayam', 'rumput'], 'harga': 0,
        'catatan': 'Kelinci paling cepat sakit kalau kandangnya kotor.',
    },
    'rubah': {
        'label': 'Rubah', 'liar': True, 'produk': None, 'produk_label': None,
        'tiap': 0, 'jumlah': 0, 'aksi': None, 'siap_teks': None,
        'pakan': [], 'harga': 0,
        'catatan': 'Rubah hewan LIAR — tidak diurus, dan mengincar ayammu.',
    },
}

# Kelinci dan kucing lebih cepat kotor/lapar (badannya kecil, makannya sering).
PENGALI_SUSUT = {'kelinci': 1.3, 'kucing': 1.2, 'ayam': 1.1, 'sapi': 1.0}


def species_of(animal_id: str) -> str:
    from .data import ANIMAL_NPCS
    return ANIMAL_NPCS.get(animal_id, {}).get('type', '')


def care_rules(animal_id: str) -> dict:
    return SPECIES_CARE.get(species_of(animal_id), {})


def is_livestock(animal_id: str) -> bool:
    """Hewan yang memang diurus (rubah liar tidak)."""
    r = care_rules(animal_id)
    return bool(r) and not r.get('liar')


# Scene yang airnya terbuka. Hewan yang tinggal di sini tidak pernah kehausan:
# bebek di danau berenang di air minumnya. Tanpa pengecualian ini, air yang
# sekarang menggerbangi produksi menghukum bebek karena tinggal di tempat yang
# memang tempatnya — palung hanya ada di kandang kebun, jadi takarannya meluruh
# sampai nol dan ia PASTI jatuh sakit, tanpa satu pun cara bagi pemain untuk
# mencegahnya. Aturan yang tidak bisa dipatuhi bukan aturan, itu jebakan.
SCENE_BERAIR = {'lake', 'beach'}


def di_air_terbuka(state, animal_id: str) -> bool:
    pos = getattr(state, 'npc_positions', {}).get(animal_id) or {}
    return pos.get('scene') in SCENE_BERAIR


def air_mandiri(state, animal_id: str) -> bool:
    """Hewan yang mencari minumnya sendiri, jadi takaran air tidak berlaku.

    Dua hal masuk ke sini, dan keduanya karena sebab yang sama: palung hanya
    ada di KANDANG kebun, jadi hewan yang tidak berada di dalamnya tidak punya
    satu pun cara untuk diberi minum oleh pemain.

      air terbuka   bebek di danau berenang di air minumnya
      tidak dikandangkan
                    kucing dan kelinci berkeliaran; catatan spesiesnya sendiri
                    sudah bilang "Beri makan, jangan dikandangkan". Mereka
                    minum dari mana saja seperti kucing sungguhan.

    Tanpa ini, air yang sekarang menggerbangi produksi menghukum mereka karena
    hidup di tempat yang memang tempatnya: takarannya meluruh sampai nol, tiga
    hari lalai, lalu SAKIT dan hati turun tiap hari — tanpa jalan keluar.
    Aturan yang tidak bisa dipatuhi bukan aturan, itu jebakan. Bug yang sama
    ditemukan dua kali: pertama pada bebek, lalu pada kucing dan kelinci.
    """
    return di_air_terbuka(state, animal_id) or not is_penned(animal_id)


def is_penned(animal_id: str) -> bool:
    """Hewan yang tinggal di KANDANG, jadi berbagi palung minum yang sama.

    Kucing dan kelinci diurus tapi tidak dikandangkan — catatan spesiesnya
    sendiri sudah mengatakannya ("Beri makan, jangan dikandangkan"). Tanpa
    pemisahan ini, mengisi palung sapi memanggil kucing dari seberang kebun
    ke palung ternak, dan takaran air kucing ikut menentukan tinggi air yang
    ditampilkan palung.
    """
    r = care_rules(animal_id)
    return bool(r) and not r.get('liar') and bool(r.get('kandang'))


# ─── KEADAAN PER HEWAN ───────────────────────────────────────────────────────
def care_of(state, animal_id: str) -> dict:
    """Ambil (atau buat) catatan perawatan satu hewan.

    Disimpan di `state.animal_care` supaya ikut ke save file — kelalaian harus
    punya ingatan, kalau tidak menelantarkan hewan tidak pernah ada biayanya.
    """
    store = getattr(state, 'animal_care', None)
    if store is None:
        store = {}
        state.animal_care = store
    rec = store.get(animal_id)
    if rec is None:
        rec = {'kenyang': 100, 'air': 100, 'bersih': 100,
               'produk_t': 0, 'produk_siap': False,
               'lalai': 0, 'sakit': False, 'sembuh_t': 0,
               'hari_makan': 0, 'hari_minum': 0, 'hari_bersih': 0}
        store[animal_id] = rec
    return rec


def _clamp(v: float) -> int:
    return int(max(0, min(100, v)))


# ─── TICK HARIAN ─────────────────────────────────────────────────────────────
def daily_tick(state) -> dict:
    """Satu malam berlalu untuk semua ternak. Dipanggil dari TimeController.

    Mengembalikan ringkasan supaya pemain bisa diberi tahu pagi harinya:
    {'lapar': [nama...], 'sakit': [nama...], 'siap': [nama...]}
    """
    from .data import ANIMAL_NPCS
    lap = {'lapar': [], 'sakit': [], 'siap': []}

    for aid, meta in ANIMAL_NPCS.items():
        if not is_livestock(aid):
            continue
        r    = care_rules(aid)
        rec  = care_of(state, aid)
        mult = PENGALI_SUSUT.get(meta.get('type', ''), 1.0)

        rec['kenyang'] = _clamp(rec['kenyang'] - SUSUT_KENYANG * mult)
        if air_mandiri(state, aid):
            rec['air'] = 100        # mencari minumnya sendiri
        else:
            rec['air'] = _clamp(rec['air'] - SUSUT_AIR * mult)
        rec['bersih']  = _clamp(rec['bersih']  - SUSUT_BERSIH  * mult)

        # ── Kelalaian. Yang dihitung adalah takaran yang MENYENTUH nol, bukan
        # yang sekadar rendah: satu hari sibuk tidak boleh langsung bikin sakit.
        if rec['kenyang'] <= 0 or rec['air'] <= 0:
            rec['lalai'] += 1
            lap['lapar'].append(meta.get('name', aid))
        else:
            rec['lalai'] = max(0, rec['lalai'] - 1)

        if rec['lalai'] >= LALAI_JADI_SAKIT and not rec['sakit']:
            rec['sakit'] = True
            rec['sembuh_t'] = 0
            lap['sakit'].append(meta.get('name', aid))
            # Hewan yang sakit karena ditelantarkan berhenti percaya.
            state.npc_hearts[aid] = max(0, state.npc_hearts.get(aid, 0) - 2)

        if rec['sakit']:
            if (rec['kenyang'] >= AMBANG_SEHAT and rec['air'] >= AMBANG_SEHAT
                    and rec['bersih'] >= AMBANG_SEHAT):
                rec['sembuh_t'] += 1
                if rec['sembuh_t'] >= SEMBUH_BUTUH_HARI:
                    rec['sakit'] = False
                    rec['lalai'] = 0
                    rec['sembuh_t'] = 0
            else:
                rec['sembuh_t'] = 0
                state.npc_hearts[aid] = max(0, state.npc_hearts.get(aid, 0) - 1)
            continue    # sakit = tidak berproduksi sama sekali

        # ── Produksi. Tiga syarat, semuanya harus lulus.
        if not r.get('produk'):
            continue
        if (rec['kenyang'] >= MIN_KENYANG_PRODUKSI
                and rec['air'] >= MIN_AIR_PRODUKSI
                and rec['bersih'] >= MIN_BERSIH_PRODUKSI):
            rec['produk_t'] += 1
            if rec['produk_t'] >= max(1, r.get('tiap', 1)) and not rec['produk_siap']:
                rec['produk_siap'] = True
                rec['produk_t'] = 0
                lap['siap'].append(meta.get('name', aid))
        else:
            # Gagal produksi hari ini. Hitungan TIDAK mundur — hanya berhenti.
            pass

    return lap


# ─── AKSI PERAWATAN ──────────────────────────────────────────────────────────
def feed_item(state, animal_id: str) -> str | None:
    """Pakan pertama di inventori yang diterima spesies ini."""
    r = care_rules(animal_id)
    for item in r.get('pakan', []):
        if state.inventory.get(item, 0) > 0:
            return item
    return None


def feed(state, animal_id: str) -> tuple[bool, str]:
    r = care_rules(animal_id)
    if not r:
        return False, "Hewan ini tidak diurus."
    item = feed_item(state, animal_id)
    if not item:
        pakan = ', '.join(r.get('pakan', [])) or '-'
        return False, f"Tidak punya pakan. {r['label']} makan: {pakan}."
    state.inventory[item] -= 1
    rec = care_of(state, animal_id)
    rec['kenyang'] = _clamp(rec['kenyang'] + ISI_PAKAN)
    rec['hari_makan'] = state.day
    state.npc_hearts[animal_id] = min(10, state.npc_hearts.get(animal_id, 0) + 0.5)
    return True, f"Diberi {item}. Kenyang {rec['kenyang']}%."


def water(state, animal_id: str) -> tuple[bool, str]:
    rec = care_of(state, animal_id)
    if rec['air'] >= 95:
        return False, "Tempat minumnya masih penuh."
    rec['air'] = ISI_MINUM
    rec['hari_minum'] = state.day
    return True, "Tempat minum diisi penuh. Air 100%."


def clean(state, animal_id: str) -> tuple[bool, str]:
    rec = care_of(state, animal_id)
    if rec['bersih'] >= 95:
        return False, "Kandangnya masih bersih."
    rec['bersih'] = ISI_BERSIH
    rec['hari_bersih'] = state.day
    state.npc_hearts[animal_id] = min(10, state.npc_hearts.get(animal_id, 0) + 0.5)
    return True, "Kandang dibersihkan. Bersih 100%."


def collect(state, animal_id: str) -> tuple[bool, str, str | None, int]:
    """Ambil hasil ternak. Return (berhasil, pesan, nama_produk, jumlah)."""
    r   = care_rules(animal_id)
    rec = care_of(state, animal_id)
    if not r.get('produk'):
        return False, f"{r.get('label', 'Hewan')} tidak menghasilkan apa-apa.", None, 0
    if rec['sakit']:
        return False, "Sedang sakit — tidak menghasilkan sampai sembuh.", None, 0
    if not rec['produk_siap']:
        sisa = max(1, r.get('tiap', 1)) - rec['produk_t']
        return False, f"Belum siap. {r['produk_label']} berikutnya ~{sisa} hari lagi.", None, 0
    rec['produk_siap'] = False
    jml = max(1, r.get('jumlah', 1))
    state.inventory[r['produk']] = state.inventory.get(r['produk'], 0) + jml
    return True, f"+{jml} {r['produk_label']}", r['produk'], jml


# ─── TEKS KEADAAN — ini yang membuat aturannya kelihatan ─────────────────────
def _label_kenyang(v: int, sudah_makan_hari_ini: bool) -> str:
    if v <= 0:
        return 'KELAPARAN!'
    if v < 40:
        return 'Lapar'
    if v < 70:
        return 'Mulai lapar'
    return 'Kenyang' if sudah_makan_hari_ini else 'Kenyang'


def _label_air(v: int) -> str:
    if v <= 0:
        return 'KEHAUSAN!'
    if v < 25:
        return 'Haus'
    if v < 60:
        return 'Mulai haus'
    return 'Cukup minum'


def _label_bersih(v: int) -> str:
    if v < 30:
        return 'Kandang KOTOR!'
    if v < 60:
        return 'Kandang mulai kotor'
    return 'Kandang bersih'


def short_status(state, animal_id: str) -> str:
    """Satu frasa untuk judul pie menu — hal paling mendesak lebih dulu."""
    if not is_livestock(animal_id):
        return 'liar'
    rec = care_of(state, animal_id)
    r   = care_rules(animal_id)
    if rec['sakit']:
        return 'SAKIT'
    if rec['kenyang'] <= 0 or rec['air'] <= 0:
        return 'KELAPARAN'
    if rec['produk_siap'] and r.get('siap_teks'):
        return r['siap_teks']
    if rec['hari_makan'] != state.day:
        return 'Belum diberi makan hari ini'
    if rec['bersih'] < 30:
        return 'Kandang kotor'
    return 'Sehat'


def status_lines(state, animal_id: str) -> list[str]:
    """Laporan lengkap satu hewan, siap ditempel ke flash_msg atau panel."""
    from .data import ANIMAL_NPCS
    meta = ANIMAL_NPCS.get(animal_id, {})
    nama = meta.get('name', animal_id)
    r    = care_rules(animal_id)
    if not r:
        return [f"{nama}: bukan hewan ternak."]
    if r.get('liar'):
        return [f"{nama} ({r['label']}) — hewan liar.", r['catatan']]

    rec = care_of(state, animal_id)
    makan_hari_ini = rec['hari_makan'] == state.day
    out = [f"{nama} — {r['label']}"]
    if rec['sakit']:
        out.append("  KONDISI  : SAKIT (ditelantarkan). Tidak menghasilkan.")
        out.append(f"             Sembuh setelah {SEMBUH_BUTUH_HARI} hari kenyang,")
        out.append(f"             minum, dan kandang bersih semua di atas {AMBANG_SEHAT}%.")
    out.append(f"  Kenyang  : {rec['kenyang']:>3}%  {_label_kenyang(rec['kenyang'], makan_hari_ini)}")
    if not makan_hari_ini:
        out.append("             Belum diberi makan hari ini.")
    out.append(f"  Air      : {rec['air']:>3}%  {_label_air(rec['air'])}")
    out.append(f"  Kandang  : {rec['bersih']:>3}%  {_label_bersih(rec['bersih'])}")

    if r.get('produk'):
        if rec['produk_siap']:
            out.append(f"  Hasil    : {r['siap_teks']} ({r['aksi']})")
        else:
            sisa = max(1, r.get('tiap', 1)) - rec['produk_t']
            out.append(f"  Hasil    : {r['produk_label']} ~{sisa} hari lagi")
            if rec['kenyang'] < MIN_KENYANG_PRODUKSI:
                out.append(f"             TERHENTI: kenyang harus >= {MIN_KENYANG_PRODUKSI}%")
            elif rec['air'] < MIN_AIR_PRODUKSI:
                out.append(f"             TERHENTI: air harus >= {MIN_AIR_PRODUKSI}%")
            elif rec['bersih'] < MIN_BERSIH_PRODUKSI:
                out.append(f"             TERHENTI: kandang harus >= {MIN_BERSIH_PRODUKSI}%")
    else:
        out.append("  Hasil    : tidak menghasilkan")
    out.append(f"  Hati     : {state.npc_hearts.get(animal_id, 0)}/10")
    out.append(f"  {r['catatan']}")
    return out


def herd_overview(state) -> list[str]:
    """Ringkasan seluruh ternak untuk panel Tani & Ternak."""
    from .data import ANIMAL_NPCS
    out = ['  nama       jenis     kenyang  air  kandang  hasil']
    ada = False
    for aid, meta in ANIMAL_NPCS.items():
        if not is_livestock(aid):
            continue
        ada = True
        r   = care_rules(aid)
        rec = care_of(state, aid)
        if rec['sakit']:
            hasil = 'SAKIT'
        elif rec['produk_siap']:
            hasil = r.get('siap_teks', 'siap')
        elif r.get('produk'):
            hasil = f"{max(1, r.get('tiap', 1)) - rec['produk_t']}h lagi"
        else:
            hasil = '-'
        out.append(f"  {meta.get('name', aid):10s} {r['label']:9s} "
                   f"{rec['kenyang']:>5}%  {rec['air']:>3}%  {rec['bersih']:>5}%   {hasil}")
    if not ada:
        out.append('  (belum ada ternak)')
    return out


def guide_lines() -> list[str]:
    """Aturan ternak, ditulis untuk dibaca DI DALAM game."""
    return [
        '── MENGURUS HEWAN ──',
        '  Klik hewan (atau tekan E di dekatnya) untuk membuka menu:',
        '    Cek Kondisi  — laporan lengkap kenyang / air / kandang / hasil',
        '    Beri Makan   — +60% kenyang, memakai satu pakan dari inventori',
        '    Beri Minum   — isi tempat minum sampai penuh, gratis',
        '    Bersihkan    — kandang kembali 100%, memakai 3 energi',
        '    Ambil Hasil  — hanya kalau hasilnya sudah siap',
        '',
        '  Tiap pagi: kenyang -45, air -55, kandang -30.',
        f'  Jadi: BERI MAKAN DAN MINUM TIAP HARI, bersihkan kandang tiap 3 hari.',
        '',
        '── SYARAT HASIL ──',
        f'  Hewan hanya menghasilkan kalau kenyang >= {MIN_KENYANG_PRODUKSI}%,',
        f'  air >= {MIN_AIR_PRODUKSI}%, kandang >= {MIN_BERSIH_PRODUKSI}%, dan tidak sakit.',
        '  Kalau salah satu kurang, hitungan panennya BERHENTI (tidak mundur).',
        '',
        '── AKIBAT KELALAIAN ──',
        f'  Kenyang atau air menyentuh 0% = 1 hari lalai. {LALAI_JADI_SAKIT} hari lalai = SAKIT.',
        '  Hewan sakit: tidak menghasilkan apa-apa, dan hati turun tiap hari.',
        f'  Sembuh butuh {SEMBUH_BUTUH_HARI} hari berturut-turut dengan semua takaran >= {AMBANG_SEHAT}%.',
        '',
        '── PAKAN PER JENIS ──',
    ] + [
        f"  {r['label']:9s}: {', '.join(r['pakan']) if r['pakan'] else '(liar, tidak diberi makan)'}"
        for r in SPECIES_CARE.values()
    ] + [
        '',
        '── JADWAL HASIL ──',
    ] + [
        f"  {r['label']:9s}: {r['produk_label']} tiap {r['tiap']} hari ({r['aksi']})"
        if r.get('produk') else f"  {r['label']:9s}: tidak menghasilkan"
        for r in SPECIES_CARE.values()
    ]
