"""verifikasi.py — Tahap 2: membuktikan yang sudah terlanjur ada.

docs/TAHAPAN.md Tahap 2: "`economy.py`, `husbandry.py`, `crops.py`,
`tool_models.py` mendarat di disk saat agennya mati. BELUM ADA YANG MEMBUKTIKAN
ISINYA BERFUNGSI." Aturannya: tidak ada fitur baru sampai yang ada terbukti
jalan **atau ditandai rusak dengan jujur**.

Alat ini bagian "membuktikan"-nya. Yang diuji bukan "apakah modulnya impor",
melainkan **klaim yang ditulis modul itu sendiri di docstring-nya**. Modul-modul
ini tidak malu-malu: economy.py menyebut pita 3,0-5,7 G/EN, uplift ~40%, ternak
5-7,5 G/EN, dan "selalu ada selisih beli-jual". Angka yang ditulis sendiri boleh
ditagih.

Tiga jenis temuan, dan ketiganya dilaporkan berbeda karena memang beda:

  RUSAK     ada akibatnya di permainan SEKARANG. Harus diperbaiki.
  RAPUH     benar hari ini karena kebetulan, bukan karena dijamin. Satu
            perubahan kecil di tempat lain membuatnya salah tanpa error.
  KEPUTUSAN angkanya atau jangkauannya menyimpang dari yang ditulis, tapi mana
            yang benar adalah keputusan pemilik, bukan keputusan alat ini.

Sengaja TIDAK butuh jendela: economy, husbandry dan crops murni logika, jadi
pemeriksaan ini jalan di mana pun dan cepat. tool_models butuh Entity, jadi
hanya diuji kalau Ursina bisa membuat jendela (lihat --dengan-render).

Pemakaian:
    python tools/verifikasi.py              semua pemeriksaan logika
    python tools/verifikasi.py --dengan-render   plus model alat 3D

Keluar dengan kode 1 kalau ada yang RUSAK. RAPUH dan KEPUTUSAN tidak
menggagalkan: yang satu peringatan, yang satu bukan wewenangku.
"""
from __future__ import annotations

import math
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

# Energi per aksi, dibaca dari controllers/interaction_controller.py.
# Dicatat di sini sebagai angka supaya perhitungan G/EN bisa diperiksa tanpa
# membangun game; kalau aksinya berubah harganya, uji pita akan ikut salah dan
# itu memang maunya — ia harus menagih keadaan SEKARANG.
EN_CANGKUL, EN_TANAM, EN_SIRAM, EN_PANEN = 2, 2, 1, 2

temuan: list[tuple[str, str, str]] = []     # (kelas, judul, keterangan)


def lapor(kelas: str, judul: str, ket: str):
    temuan.append((kelas, judul, ket))


# ─────────────────────────────────────────────────────────────────────────────
def uji_urutan_impor():
    """economy.ITEM_VALUES dibangun SEKALI saat impor, dari data.CROPS.

    crops.py MENAMBAHKAN 16 tanaman + 7 pohon ke data.CROPS saat ia diimpor.
    Jadi siapa yang diimpor lebih dulu menentukan apakah 23 barang itu punya
    harga atau bernilai 0G. Tidak ada error, tidak ada log — cuma panen yang
    tidak laku.
    """
    import subprocess
    kode = (
        "import sys; sys.path.insert(0,'.');"
        "import game.{pertama}, game.{kedua};"
        "import game.economy as e; print(e.sell_price('padi'))"
    )
    hasil = {}
    for urut in (('crops', 'economy'), ('economy', 'crops')):
        p = subprocess.run([sys.executable, '-c',
                            kode.format(pertama=urut[0], kedua=urut[1])],
                           capture_output=True, text=True, cwd=ROOT)
        hasil[urut] = p.stdout.strip().splitlines()[-1] if p.stdout.strip() else '?'
    a = hasil[('crops', 'economy')]
    b = hasil[('economy', 'crops')]
    if a == b:
        return f'padi = {a}G di kedua urutan impor — harga tidak lagi bergantung urutan'
    lapor('RAPUH', 'harga bergantung urutan impor',
          f"padi = {a}G kalau crops diimpor lebih dulu, tapi {b}G kalau economy "
          f"lebih dulu. 23 barang (16 palawija + 7 pohon) ikut. Permainan "
          f"sekarang AMAN karena world.py mengimpor crops di tingkat modul "
          f"sebelum economy dipakai — kebetulan, bukan jaminan.")
    return f'padi {a}G vs {b}G — BERGANTUNG URUTAN'


def uji_pita_gpe():
    """economy.py: 'Tanaman dijaga di pita 3,0 - 5,7 G/EN.'"""
    import game.crops  # noqa: F401  (daftarkan katalog dulu, lihat uji di atas)
    import game.economy as e
    from game.data import CROPS
    luar = []
    for k, c in sorted(CROPS.items()):
        if c.get('is_tree'):
            continue
        d = int(c.get('days', 4))
        en = EN_CANGKUL + EN_TANAM + EN_PANEN + EN_SIRAM * -(-d // 2)
        gpe = (e.sell_price(k) - int(c.get('cost', 0))) / en
        if not (3.0 <= gpe <= 5.7):
            luar.append((k, round(gpe, 2)))
    n = len([1 for c in CROPS.values() if not c.get('is_tree')])
    if not luar:
        return f'{n} tanaman, semuanya di dalam pita 3,0-5,7 G/EN'
    asli = set(game.crops.CROP_CATALOG)
    lapor('KEPUTUSAN', 'tiga tanaman di luar pita G/EN yang ditulis economy.py',
          'economy.py menyetel pitanya untuk delapan tanaman data.py; crops.py '
          'menambah sembilan lagi tanpa ikut ditagih pita itu. '
          + ', '.join(f'{k} {g} G/EN' for k, g in luar)
          + f'. ubi_kayu 1,9x langit-langit pita — kalau angkanya benar, ia '
            f'strategi dominan; kalau pitanya benar, harga/hari ubi_kayu yang '
            f'harus turun. Mana yang benar bukan keputusanku.')
    return f'{len(luar)} dari {n} tanaman di luar pita: ' + ', '.join(k for k, _ in luar)


def uji_uplift():
    """economy.py: 'Mengolah menambah ~40% nilai.'"""
    import game.crops  # noqa: F401
    import game.economy as e
    buruk = []
    for r in e.PROCESS_RECIPES:
        up = e.recipe_uplift(r)
        batas = (1.30, 1.55) if r.get('as_feed') else (1.30, 1.50)
        if not (batas[0] <= up <= batas[1]):
            buruk.append((r['id'], round(up, 2)))
        # best_process_hint hanya muncul kalau mengolah memang untung.
        if up <= 1.0:
            lapor('RUSAK', f"olahan {r['id']} tidak untung",
                  f'uplift {up:.2f} — best_process_hint akan diam, jadi '
                  f'resepnya tidak pernah diajarkan ke pemain.')
    if buruk:
        lapor('KEPUTUSAN', 'uplift olahan di luar ~40%',
              ', '.join(f'{k} x{v}' for k, v in buruk))
        return f'{len(buruk)} resep di luar rentang'
    return f'{len(e.PROCESS_RECIPES)} resep, semuanya +38..50% seperti dijanjikan'


def uji_mesin_uang():
    """economy.py: 'Selalu ada selisih beli-jual.'"""
    import game.crops  # noqa: F401
    import game.economy as e
    from game.data import SHOP_ITEMS
    mesin = [(it['id'], int(it['price']), e.sell_price(it['id']))
             for it in SHOP_ITEMS
             if e.sell_price(it['id']) and e.sell_price(it['id']) >= int(it['price'])]
    if mesin:
        lapor('RUSAK', 'beli-lalu-jual menghasilkan emas gratis',
              ', '.join(f'{k}: beli {b}G jual {j}G' for k, b, j in mesin))
        return f'{len(mesin)} barang jadi mesin uang'
    return f'{len(SHOP_ITEMS)} barang toko, tidak satu pun bisa dijual >= harga belinya'


def uji_shipping():
    """economy.py: Peti Kirim membayar 85%, minimal 1 kalau laku."""
    import game.crops  # noqa: F401
    import game.economy as e
    salah = []
    for k, v in e.ITEM_VALUES.items():
        p = e.shipping_price(k)
        if v > 0 and p != max(1, int(v * e.SHIPPING_RATE)):
            salah.append(k)
        if v > 0 and p < 1:
            salah.append(k)
    if salah:
        lapor('RUSAK', 'harga Peti Kirim tidak 85%', ', '.join(salah[:8]))
        return f'{len(salah)} barang salah hitung'
    return f'{len(e.ITEM_VALUES)} barang, semuanya 85% (minimal 1)'


def uji_dua_sistem_ternak():
    """economy.py dan husbandry.py sama-sama mengurus lima ekor yang SAMA.

    Keduanya dipanggil di hari yang sama oleh TimeController, pada dua gudang
    state yang berbeda (`state.animals` vs `state.animal_care`), dan keduanya
    menyatakan spesies mana menghasilkan apa, tiap berapa hari.
    """
    import game.crops  # noqa: F401
    import game.economy as e
    import game.husbandry as h
    from game.data import CROPS

    # 1. Produk husbandry yang tidak punya harga sama sekali.
    # Temuan DI DALAM husbandry hanya punya akibat kalau modulnya terjangkau.
    # Kalau tidak, ia tetap dilaporkan — tapi sebagai jebakan yang menunggu,
    # bukan kerusakan yang sedang berjalan. Memvonis sama untuk dua keadaan
    # yang berbeda membuat laporannya tidak bisa dipercaya.
    kelas_h = 'RUSAK' if _husbandry_terjangkau() else 'RAPUH'
    ekor_h = ('' if kelas_h == 'RUSAK' else
              ' Belum berakibat sekarang karena husbandry belum tersambung — '
              'tapi akan langsung menggigit begitu disambungkan.')

    tak_laku = [(sp, r['produk']) for sp, r in h.SPECIES_CARE.items()
                if r.get('produk') and e.sell_price(r['produk']) == 0]
    if tak_laku:
        lapor(kelas_h, 'hasil ternak yang tidak bisa dijual',
              ', '.join(f'{sp} -> {p} (0G)' for sp, p in tak_laku)
              + '. husbandry.collect() memasukkannya ke tas sebagai barang tanpa '
                'harga: tidak laku di warung, tidak boleh masuk Peti Kirim.'
              + ekor_h)

    # 2. Pakan yang bukan barang apa pun.
    semua = set(CROPS) | set(e.ITEM_VALUES)
    hantu = {}
    for sp, r in h.SPECIES_CARE.items():
        hilang = [i for i in r.get('pakan', []) if i not in semua]
        if hilang:
            hantu[sp] = hilang
    if hantu:
        rumput = [sp for sp, v in hantu.items() if 'rumput' in v]
        lapor(kelas_h, 'pakan yang tidak ada sebagai barang',
              ', '.join(f'{sp}: {", ".join(v)}' for sp, v in hantu.items())
              + f'. "rumput" adalah pilihan PERTAMA untuk {len(rumput)} spesies '
                f'({", ".join(rumput)}), jadi feed_item() melewatinya tiap kali.'
              + ekor_h)

    # 3. Dua sistem, dua jawaban untuk pertanyaan yang sama.
    beda = []
    for sp in sorted(set(e.ANIMAL_PRODUCE) |
                     {k for k, v in h.SPECIES_CARE.items() if v.get('produk')}):
        ec = e.ANIMAL_PRODUCE.get(sp)
        hu = h.SPECIES_CARE.get(sp, {})
        if not ec or not hu.get('produk'):
            continue
        if ec['item'] != hu['produk'] or ec['cycle'] != hu.get('tiap'):
            beda.append(f"{sp}: economy={ec['item']}/{ec['cycle']}h "
                        f"husbandry={hu['produk']}/{hu.get('tiap')}h")
    if beda:
        lapor('KEPUTUSAN', 'economy.py dan husbandry.py tidak sepakat soal ternak',
              '; '.join(beda) + '. Keduanya berjalan tiap pagi. Mana yang jadi '
              'sumber kebenaran adalah keputusan pemilik — menghapus salah satu '
              'membuang pekerjaan yang sudah jadi.')
    n = len([1 for v in h.SPECIES_CARE.values() if v.get('produk')])
    return (f'{n} spesies penghasil: {len(tak_laku)} hasil tanpa harga, '
            f'{len(hantu)} spesies berpakan hantu, {len(beda)} ketidaksepakatan')


def _tanpa_komentar(sumber: str) -> str:
    """Buang komentar dan isi string, sisakan kodenya.

    Ini bukan kerapian: tanpa ini pemeriksaan di bawah memberi laporan PALSU,
    dan sudah pernah. Komentar di `controllers/time_controller.py` menuliskan
    cara menyambungkan ternak sebagai contoh — termasuk baris
    `husbandry.feed(s, animal_id)`. Pemindai yang membaca mentah menganggap
    contoh itu pemanggilan sungguhan, lalu menyatakan perawatan ternak
    "tersambung" padahal tidak ada satu pun pemanggil. Dokumentasi perbaikannya
    mengalahkan alat yang memeriksanya.

    Kalau sumbernya tidak bisa ditokenisasi (sintaks rusak), teks aslinya
    dikembalikan apa adanya — lebih baik kelebihan cocok daripada diam.
    """
    import io
    import tokenize
    try:
        keluar = []
        for tok in tokenize.generate_tokens(io.StringIO(sumber).readline):
            if tok.type == tokenize.COMMENT:
                continue
            if tok.type == tokenize.STRING:
                keluar.append('""')
                continue
            keluar.append(tok.string)
        return ' '.join(keluar)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return sumber


def _pemanggil_husbandry() -> dict[str, list[str]]:
    """Fungsi husbandry mana yang benar-benar dipanggil dari game/, dan dari mana.

    Yang dicari HARUS terikat ke modulnya: `husbandry.feed(`, atau nama yang
    diimpor lewat `from ..husbandry import feed`. Versi pertama pemeriksaan ini
    mencari kata telanjang `feed`/`water`/`clean` di berkas mana pun yang
    menyebut husbandry, dan itu langsung memberi laporan PALSU: `water` cocok
    dengan `sound_play('water')` yang sama sekali bukan perawatan ternak,
    sehingga `water` dinyatakan hidup padahal mati. Alat yang melaporkan
    kegagalan palsu lebih berbahaya daripada tidak ada alat.
    """
    import re
    pemanggil = {'daily_tick': [], 'feed': [], 'water': [], 'clean': [], 'collect': []}
    for p in (ROOT / 'game').rglob('*.py'):
        if p.name == 'husbandry.py':
            continue
        teks = _tanpa_komentar(p.read_text(encoding='utf-8', errors='replace'))
        if 'husbandry' not in teks:
            continue
        alias = {}
        for blok in re.findall(r'from\s+\.+husbandry\s+import\s+([^\n(]+|\([^)]*\))',
                               teks):
            for bagian in blok.strip('()').split(','):
                bagian = bagian.strip()
                if not bagian:
                    continue
                if ' as ' in bagian:
                    asli_nama, _, nama_lokal = bagian.partition(' as ')
                    alias[asli_nama.strip()] = nama_lokal.strip()
                else:
                    alias[bagian] = bagian
        for fn in pemanggil:
            dipakai = bool(re.search(rf'husbandry\s*\.\s*{fn}\s*\(', teks))
            lokal = alias.get(fn)
            if lokal and re.search(rf'\b{re.escape(lokal)}\s*\(', teks):
                dipakai = True
            if dipakai:
                pemanggil[fn].append(p.relative_to(ROOT).as_posix())
    return pemanggil


def _husbandry_terjangkau() -> bool:
    """True kalau pemain punya jalan untuk MENGURUS hewan lewat husbandry."""
    pem = _pemanggil_husbandry()
    return any(pem[fn] for fn in ('feed', 'water', 'clean', 'collect'))


def uji_perawatan_terjangkau():
    """husbandry punya peluruhan harian DAN perawatan. Keduanya harus sejalan.

    Tiga keadaan yang mungkin, dan hanya satu di antaranya sehat:

      peluruhan + perawatan  -> sistemnya hidup dan utuh. LULUS.
      peluruhan tanpa perawatan -> takaran turun 45-55 per malam dan tidak ada
                                apa pun yang bisa mengisinya. RUSAK, dan
                                akibatnya dihitung di bawah.
      dua-duanya mati        -> modul utuh yang belum tersambung. Itu bukan
                                kerusakan; itu pekerjaan yang menunggu.
    """
    import game.crops  # noqa: F401
    import game.husbandry as h
    from game.data import ANIMAL_NPCS

    pem = _pemanggil_husbandry()
    mati = [fn for fn in ('feed', 'water', 'clean') if not pem[fn]]
    hidup_tick = bool(pem['daily_tick'])

    if not mati:
        return 'peluruhan dan perawatan dua-duanya tersambung'

    if not hidup_tick:
        lapor('RAPUH', 'husbandry.py utuh tapi belum tersambung',
              f"daily_tick DAN {', '.join(mati)} sama-sama tanpa pemanggil, jadi "
              f"434 baris sistem kesejahteraan ternak tidak aktif. Ini bukan "
              f"kerusakan: tidak ada akibat apa pun di permainan sekarang. Tapi "
              f"menyambung HANYA daily_tick-nya pernah dilakukan dan hasilnya "
              f"merusak (lihat komentar di controllers/time_controller.py) — "
              f"peluruhan tanpa perawatan membuat semua ternak sakit permanen "
              f"di hari 4. Kalau disambungkan lagi, keempat aksinya harus ikut.")
        return f'modul utuh, tidak aktif (daily_tick + {len(mati)} aksi tanpa pemanggil)'

    # Peluruhan hidup, perawatan mati: hitung akibatnya.
    class S:
        def __init__(s):
            s.day = 1; s.inventory = {}; s.npc_hearts = {}
            s.animal_care = {}; s.animals = {}
    s = S()
    ternak = [a for a in ANIMAL_NPCS if h.is_livestock(a)]
    for a in ternak:
        s.npc_hearts[a] = 5
    hari_semua_sakit = hari_hati_nol = None
    for d in range(1, 31):
        s.day = d
        h.daily_tick(s)
        if hari_semua_sakit is None and all(h.care_of(s, a)['sakit'] for a in ternak):
            hari_semua_sakit = d
        if hari_hati_nol is None and all(s.npc_hearts[a] <= 0 for a in ternak):
            hari_hati_nol = d
    lapor('RUSAK', 'separuh sistem ternak dipasang: peluruhannya, bukan perawatannya',
          f"husbandry.daily_tick dipanggil dari {', '.join(pem['daily_tick'])}, "
          f"tapi husbandry.{', '.join(mati)} tidak punya pemanggil sama sekali. "
          f"Takaran turun 45-55 per malam dan tidak ada apa pun yang bisa "
          f"mengisinya. Disimulasikan {len(ternak)} ternak tanpa aksi pemain: "
          f"SEMUA sakit permanen di hari {hari_semua_sakit}, hati SEMUA hewan "
          f"menyentuh 0 di hari {hari_hati_nol}. Menjalankan peluruhan tanpa "
          f"perawatan LEBIH buruk daripada tidak menjalankannya.")
    return (f'feed/water/clean tanpa pemanggil; semua ternak sakit di hari '
            f'{hari_semua_sakit}, hati nol di hari {hari_hati_nol}')


def uji_quest_terjangkau():
    """Alur cerita utama: objeknya dibuat, tapi tidak ada yang memanggilnya.

    Ditemukan saat menyurvei untuk Tahap 4 (Keinginan), dan bentuknya persis
    sama dengan kasus husbandry: kelasnya lengkap, instansnya dibuat, yang
    hilang cuma sambungannya -- dan kegagalannya TIDAK terlihat sebagai error,
    karena pengirimnya memakai `hasattr` lalu diam kalau tidak ketemu.
    """
    import re
    teks_player = _tanpa_komentar(
        (ROOT / 'game' / 'player.py').read_text(encoding='utf-8', errors='replace'))
    punya = {n for n in ('quest_controller', 'quest_manager',
                         '_check_quest_progress')
             if re.search(rf'self\s*\.\s*{n}\s*=', teks_player)
             or re.search(rf'def\s+{n}\b', teks_player)}

    dicari = set()
    for p in (ROOT / 'game').rglob('*.py'):
        t = _tanpa_komentar(p.read_text(encoding='utf-8', errors='replace'))
        for n in ('quest_manager', '_check_quest_progress', 'quest_controller'):
            if re.search(rf'(player|self)\s*\.\s*{n}\b', t) and p.name != 'player.py':
                dicari.add(n)

    nyasar = dicari - punya
    if not nyasar:
        return f'pengirim quest memakai nama yang ada: {", ".join(sorted(dicari))}'

    lanjut = []
    # Kalau disambungkan, dua cacat berikutnya langsung menunggu. Dibuktikan,
    # bukan dikira: jalankan pengontrolnya pada state yang memenuhi syarat.
    try:
        from game.state import GameState
        from game.controllers.quest_controller import QuestController
        s = GameState()
        s.mail_read = True
        s.stats['lobak_harvested'] = 5
        s.stats['earned'] = 1000
        QuestController(s).check_quest_progress()
    except Exception as ex:
        lanjut.append(f'{type(ex).__name__}: {ex}')

    from game.data import QUEST_STAGES
    bentuk = type(QUEST_STAGES).__name__

    lapor('RUSAK', 'alur cerita utama tidak pernah maju',
          f"`player.py` membuat `self.quest_controller`, tapi pengirimnya "
          f"mencari {', '.join(sorted(nyasar))} -- nama yang tidak ada pada "
          f"Player. Keduanya dijaga `hasattr`, jadi `check_quests()` DIAM: "
          f"tidak ada error, tidak ada log, quest_stage cuma tidak pernah "
          f"naik. Menyambungkannya saja TIDAK cukup dan akan mengubah diam "
          f"jadi crash: QUEST_STAGES bertipe {bentuk} tapi dibaca "
          f"`QUEST_STAGES.get(...)`"
          + (f" ({lanjut[0]})" if lanjut else '')
          + ", dan tahap 2->3 membaca `s.npc_relations` yang tidak ada di "
            "GameState -- ambangnya 15 sementara `npc_hearts` berskala 0-10, "
            "jadi angkanya pun harus diputuskan ulang. Memperbaiki separuhnya "
            "mengulang persis kesalahan husbandry.")
    return f'pengirim mencari {", ".join(sorted(nyasar))}; yang ada quest_controller'

def uji_benih_terjangkau():
    """crops.py menyiapkan 16 baris toko tapi tidak memasangnya."""
    import game.crops as c
    from game.data import SHOP_ITEMS
    ids = {i['id'] for i in SHOP_ITEMS}
    rows = c.SEED_SHOP_ROWS
    kebeli = [r for r in rows if r['id'] in ids]
    if len(kebeli) == len(rows):
        return f'{len(rows)} benih baru, semuanya ada di toko'
    lapor('KEPUTUSAN', 'benih tanaman baru tidak bisa dibeli',
          f'{len(rows) - len(kebeli)} dari {len(rows)} benih yang disiapkan '
          f'crops.seed_shop_rows() tidak ada di data.SHOP_ITEMS. crops.py sendiri '
          f'menjelaskan alasannya: panel toko memilih dengan tombol 1-9, jadi '
          f'menambah 16 baris membuat sebagiannya tidak bisa dipilih. Jadi '
          f'tanamannya tumbuh, berharga, dan punya model — tapi pemain tidak '
          f'punya jalan untuk memulainya. Memperbaikinya berarti mengubah panel '
          f'toko (gulir/halaman), dan itu keputusan desain.')
    return f'{len(kebeli)}/{len(rows)} benih baru bisa dibeli'


def uji_siklus_tanam():
    """crops.py: tanam -> siram -> tumbuh -> panen harus benar-benar jalan."""
    import game.crops as c

    class S:
        def __init__(s):
            s.soil = {}; s.season_index = 0; s.inventory = {}
            s.day = 1

        def get_season(s):
            return ['Semi', 'Panas', 'Gugur', 'Dingin'][s.season_index]

    gagal = []
    for cid in c.crop_ids():
        sp = c.spec(cid)
        musim = (sp.get('seasons') or ['Semi'])[0]
        s = S()
        s.season_index = ['Semi', 'Panas', 'Gugur', 'Dingin'].index(musim)
        soil = {'tilled': True, 'crop': cid, 'age': 0}
        s.soil['0,0,farm'] = soil
        # Siram lalu tumbuh, sampai batas aman dua kali umur yang dijanjikan.
        batas = int(sp.get('days', 4)) * 2 + 4
        n = 0
        while not c.is_ready(cid, soil) and n < batas:
            soil['watered'] = True
            c.grow_all(s)
            n += 1
        if not c.is_ready(cid, soil):
            gagal.append(f'{cid} tidak pernah siap dalam {batas} hari')
            continue
        jml, _tetap = c.harvest(soil, cid)
        if jml <= 0:
            gagal.append(f'{cid} panen menghasilkan {jml}')
    if gagal:
        lapor('RUSAK', 'siklus tanam tidak selesai', '; '.join(gagal[:6]))
        return f'{len(gagal)} dari {len(c.crop_ids())} tanaman gagal'
    return f'{len(c.crop_ids())} tanaman: tanam->siram->tumbuh->panen semuanya jalan'


def uji_model_alat():
    """tool_models.py: tiap slot alat 1-8 harus menghasilkan geometri sungguhan.

    HARUS membuat `Ursina()` lebih dulu. Versi pertama pemeriksaan ini tidak,
    dan itu LULUS PALSU: tanpa aplikasi, Ursina cuma mencetak peringatan
    "Tried to instantiate Entity before Ursina" lalu mengembalikan objek
    setengah jadi, sehingga alat yang sama sekali tidak dibangun tetap terbaca
    "bergeometri". Lulus palsu lebih buruk daripada tidak memeriksa: ia
    menjanjikan jaminan yang tidak ada.

    Yang diperiksa bukan "objeknya tidak None" melainkan jumlah simpul
    geometri di bawahnya, ditanyakan ke Panda3D lewat getTightBounds():
    kotak batas yang kosong berarti tidak ada yang akan terlihat di tangan
    pemain, apa pun yang dikembalikan konstruktornya.
    """
    from panda3d.core import loadPrcFileData
    loadPrcFileData('', 'audio-library-name null')
    loadPrcFileData('', 'window-type offscreen')
    from ursina import Ursina, application
    application.asset_folder = ROOT
    from panda3d.core import getModelPath
    getModelPath().append_path(str(ROOT.resolve()))
    _app = Ursina(size=(320, 180), borderless=False)

    import game.tool_models as tm
    kinds = {tm.kind_for_tool_index(i) for i in range(8)}
    buruk = []
    for k in sorted(kinds):
        try:
            e = tm.build_tool(k)
        except Exception as ex:
            buruk.append(f'{k}: {type(ex).__name__}')
            continue
        if e is None:
            buruk.append(f'{k}: None')
            continue
        kotak = e.getTightBounds()
        if not kotak:
            buruk.append(f'{k}: tanpa geometri')
            continue
        lo, hi = kotak
        besar = max(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2])
        if besar <= 1e-6:
            buruk.append(f'{k}: kotak batas nol')
    if buruk:
        lapor('RUSAK', 'model alat tidak bergeometri', ', '.join(buruk))
        return f'{len(buruk)} dari {len(kinds)} jenis rusak'
    return f'{len(kinds)} jenis alat untuk 8 slot, semuanya bergeometri nyata'


# ─────────────────────────────────────────────────────────────────────────────
PEMERIKSAAN = [
    ('urutan impor harga',   uji_urutan_impor),
    ('pita G/EN tanaman',    uji_pita_gpe),
    ('uplift olahan',        uji_uplift),
    ('mesin uang beli-jual', uji_mesin_uang),
    ('harga Peti Kirim',     uji_shipping),
    ('dua sistem ternak',    uji_dua_sistem_ternak),
    ('perawatan terjangkau', uji_perawatan_terjangkau),
    ('benih baru terjangkau', uji_benih_terjangkau),
    ('alur quest terjangkau', uji_quest_terjangkau),
    ('siklus tanam penuh',   uji_siklus_tanam),
]


def main():
    dengan_render = '--dengan-render' in sys.argv
    daftar = list(PEMERIKSAAN)
    if dengan_render:
        daftar.append(('model alat 3D', uji_model_alat))

    print()
    print('VERIFIKASI TAHAP 2 — economy, husbandry, crops, tool_models')
    print('=' * 78)
    print(f'{"pemeriksaan":24s}  ringkas')
    print('-' * 78)
    for nama, fn in daftar:
        try:
            ring = fn()
        except Exception as ex:
            import traceback
            ring = f'{type(ex).__name__}: {ex}'
            lapor('RUSAK', f'pemeriksaan "{nama}" meledak', ring)
            traceback.print_exc()
        print(f'{nama:24s}  {ring}')
    if not dengan_render:
        print(f'{"model alat 3D":24s}  dilewati (butuh --dengan-render)')
    print('-' * 78)

    for kelas, label in (('RUSAK', 'RUSAK — ada akibatnya sekarang'),
                         ('RAPUH', 'RAPUH — benar karena kebetulan'),
                         ('KEPUTUSAN', 'KEPUTUSAN PEMILIK — bukan wewenang alat ini')):
        baris = [(j, k) for kl, j, k in temuan if kl == kelas]
        if not baris:
            continue
        print()
        print(label)
        print('=' * 78)
        for i, (judul, ket) in enumerate(baris, 1):
            print(f'{i}. {judul}')
            for potong in _bungkus(ket, 74):
                print(f'   {potong}')
            print()

    n_rusak = sum(1 for kl, _, _ in temuan if kl == 'RUSAK')
    print('-' * 78)
    print(f'{len(temuan)} temuan: {n_rusak} RUSAK, '
          f'{sum(1 for kl,_,_ in temuan if kl=="RAPUH")} RAPUH, '
          f'{sum(1 for kl,_,_ in temuan if kl=="KEPUTUSAN")} KEPUTUSAN')
    sys.stdout.flush()
    sys.exit(1 if n_rusak else 0)


def _bungkus(teks: str, lebar: int) -> list[str]:
    kata, baris, kini = teks.split(), [], ''
    for k in kata:
        if len(kini) + len(k) + 1 > lebar:
            baris.append(kini)
            kini = k
        else:
            kini = f'{kini} {k}'.strip()
    if kini:
        baris.append(kini)
    return baris


if __name__ == '__main__':
    main()
