"""uji_wishes.py — Membuktikan mesin Keinginan (Tahap 4) sebelum dipasang.

Yang diuji adalah hal-hal yang kalau salah membuat seluruh mekanismenya
bohong, bukan sekadar "fungsinya tidak melempar error":

  1. GARIS DASAR   "hasilkan 600G" pada pemain yang sudah pernah menjual
                   10.000G tidak boleh selesai seketika. Ini satu-satunya hal
                   yang membuat janji berarti; kalau ini salah, seluruh sistem
                   membayar pemain untuk masa lalunya.
  2. AMBANG        keinginan ambang tidak boleh ditawarkan kalau targetnya
                   sudah terlewati (selesai di detik ia dijanjikan).
  3. TETAP SEHARI  tawaran tidak boleh berubah tiap kali dibaca — kalau
                   berubah, pemain akan membuka-tutup panel sampai dapat
                   tawaran enak, dan itu mesin judi, bukan pilihan.
  4. RELEVANSI     tidak menawarkan panen tanaman yang benihnya tidak dimiliki.
  5. SLOT          empat, dan yang kelima ditolak.
  6. BAYAR         selesai = slot kosong lagi + Kebahagiaan naik TEPAT sebesar
                   `bayar`, sekali saja.
  7. HADIAH HIDUP  tiap hadiah harus menunjuk field yang BENAR-BENAR DIBACA
                   kode permainan. `state.upgrades` ada di save sejak lama dan
                   tidak dibaca di mana pun; hadiah semacam itu mengambil
                   Kebahagiaan dan memberi nol.
  8. SAVE          janji, Kebahagiaan dan hadiah harus bertahan bolak-balik.

Murni logika, tidak butuh jendela.

Pemakaian:
    python tools/uji_wishes.py
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import game.crops  # noqa: F401,E402  (daftarkan katalog tanaman dulu)
import game.wishes as w  # noqa: E402
from game.state import GameState  # noqa: E402

hasil: list[tuple[str, bool, str]] = []


def cek(nama: str, ok: bool, ket: str = ''):
    hasil.append((nama, bool(ok), ket))


def _state(**kw) -> GameState:
    s = GameState()
    s.char_name = 'Uji'
    for k, v in kw.items():
        setattr(s, k, v)
    return s


# ── 1. Garis dasar ──────────────────────────────────────────────────────────
def uji_garis_dasar():
    s = _state(gold=50)
    s.stats['earned'] = 10_000          # pemain kaya dengan riwayat panjang
    templat = w.KATALOG_BY_ID['kumpulkan_emas']
    param = {'n': 600}
    ok, _ = w.janjikan(s, {'id': 'kumpulkan_emas', 'param': param,
                           'teks': 'Hasilkan 600G dari menjual'})
    j = s.janji[0]
    maju, butuh = w.kemajuan(s, j)
    cek('garis dasar: tidak selesai seketika', ok and not w.selesai(s, j),
        f'maju={maju}/{butuh} padahal earned=10.000')
    cek('garis dasar: awal dicatat', j['awal'] == 10_000, f"awal={j['awal']}")

    s.stats['earned'] += 599
    cek('garis dasar: 599 dari 600 belum cukup', not w.selesai(s, j),
        f'maju={w.kemajuan(s, j)[0]}')
    s.stats['earned'] += 1
    cek('garis dasar: tepat 600 selesai', w.selesai(s, j))


# ── 2. Ambang ───────────────────────────────────────────────────────────────
def uji_ambang():
    s = _state(gold=99_999)
    kand = w.tawaran(s)
    punya_emas = [c for c in kand if c['id'] == 'punya_emas']
    cek('ambang: "punya NG" tidak ditawarkan ke pemain yang sudah lewat',
        not punya_emas, f'gold=99.999, tawaran={[c["id"] for c in kand]}')

    # Hati NPC: target harus selalu di atas yang sekarang.
    s2 = _state()
    from game.data import HUMAN_NPCS
    nid = sorted(HUMAN_NPCS)[0]
    s2.npc_hearts[nid] = 5
    for _ in range(12):
        p = w._param_hati(s2, __import__('random').Random(_))
        if p['npc'] == nid:
            cek('ambang: target hati selalu di atas yang sekarang',
                p['n'] > 5, f"sekarang 5, target {p['n']}")
            break


# ── 3. Tawaran tetap sehari ─────────────────────────────────────────────────
def uji_tetap_sehari():
    s = _state()
    a = [c['teks'] for c in w.tawaran(s)]
    b = [c['teks'] for c in w.tawaran(s)]
    cek('tawaran: sama kalau dibaca dua kali di hari yang sama', a == b,
        f'{len(a)} kandidat')
    s.day += 1
    c = [c['teks'] for c in w.tawaran(s)]
    cek('tawaran: berganti saat hari berganti', a != c)


# ── 4. Relevansi ────────────────────────────────────────────────────────────
def uji_relevansi():
    s = _state(inventory={})           # tanpa benih sama sekali
    kand = w.tawaran(s)
    cek('relevansi: tanpa benih, tidak ada keinginan panen-tanaman-tertentu',
        not [c for c in kand if c['id'] == 'panen_tanaman'],
        f'tawaran={[c["id"] for c in kand]}')

    s2 = _state(inventory={'tomat_seed': 3})
    ids = set()
    for d in range(1, 40):
        s2.day = d
        ids |= {(c['id'], c['param'].get('crop')) for c in w.tawaran(s2)}
    panen = {crop for i, crop in ids if i == 'panen_tanaman'}
    cek('relevansi: dengan benih tomat, hanya tomat yang pernah diminta',
        panen == {'tomat'}, f'tanaman diminta: {sorted(panen)}')

    s3 = _state(pickaxe_tier=0, sword_id='')
    kand3 = {c['id'] for c in w.tawaran(s3)}
    cek('relevansi: tanpa pickaxe tidak ada keinginan tambang/gua',
        not (kand3 & {'tambang', 'turun_gua'}), f'{sorted(kand3)}')
    cek('relevansi: tanpa pedang tidak ada keinginan kalahkan-mob',
        'kalahkan_mob' not in kand3)


# ── 5. Slot ─────────────────────────────────────────────────────────────────
def uji_slot():
    s = _state()
    terima = 0
    for n in (100, 200, 300, 400, 500, 600):
        ok, _ = w.janjikan(s, {'id': 'kumpulkan_emas', 'param': {'n': n},
                               'teks': f'Hasilkan {n}G'})
        terima += int(ok)
    cek('slot: hanya empat yang diterima', terima == w.SLOT_JANJI,
        f'{terima} diterima dari 6 percobaan')
    cek('slot: panjang daftar janji = 4', len(s.janji) == 4)
    ok, pesan = w.lupakan(s, 1)
    cek('slot: lupakan membebaskan satu', ok and len(s.janji) == 3, pesan)
    ok, _ = w.janjikan(s, {'id': 'kumpulkan_emas', 'param': {'n': 700},
                           'teks': 'Hasilkan 700G'})
    cek('slot: setelah dilupakan bisa berjanji lagi', ok and len(s.janji) == 4)


# ── 6. Pembayaran ───────────────────────────────────────────────────────────
def uji_bayar():
    s = _state()
    bayar = w.KATALOG_BY_ID['kumpulkan_emas']['bayar']
    w.janjikan(s, {'id': 'kumpulkan_emas', 'param': {'n': 100},
                   'teks': 'Hasilkan 100G'})
    lunas = w.periksa(s)
    cek('bayar: belum selesai, belum dibayar',
        not lunas and s.kebahagiaan == 0)
    s.stats['earned'] = 100
    lunas = w.periksa(s)
    cek('bayar: selesai -> dibayar tepat sebesar `bayar`',
        len(lunas) == 1 and s.kebahagiaan == bayar,
        f'kebahagiaan={s.kebahagiaan}, seharusnya {bayar}')
    cek('bayar: slot kosong lagi', not s.janji)
    lagi = w.periksa(s)
    cek('bayar: tidak dibayar dua kali',
        not lagi and s.kebahagiaan == bayar, f'kebahagiaan={s.kebahagiaan}')
    cek('bayar: total seumur hidup ikut naik', s.kebahagiaan_total == bayar)


# ── 7. Hadiah menunjuk field yang hidup ─────────────────────────────────────
def uji_hadiah_hidup():
    """Tiap hadiah harus mengubah field yang DIBACA kode permainan.

    Dibaca dari sumbernya, bukan diasumsikan — dan komentar dibuang lebih dulu,
    karena `tools/verifikasi.py` sudah pernah tertipu oleh contoh di dalam
    komentar yang terbaca seperti pemanggilan sungguhan.
    """
    import io
    import tokenize

    def tanpa_komentar(teks: str) -> str:
        try:
            keluar = []
            for tok in tokenize.generate_tokens(io.StringIO(teks).readline):
                if tok.type == tokenize.COMMENT:
                    continue
                if tok.type == tokenize.STRING:
                    keluar.append('""')
                    continue
                keluar.append(tok.string)
            return ' '.join(keluar)
        except (tokenize.TokenError, IndentationError, SyntaxError):
            return teks

    sumber = {}
    for p in (ROOT / 'game').rglob('*.py'):
        if p.name in ('state.py', 'wishes.py'):
            continue      # yang mendefinisikan/menulis, bukan yang MEMAKAI
        sumber[p.relative_to(ROOT).as_posix()] = tanpa_komentar(
            p.read_text(encoding='utf-8', errors='replace'))

    for h in w.HADIAH:
        f = h['field']
        # `\.{f}` TIDAK cocok di sini: tokenizer di atas menyambung token
        # dengan spasi, jadi `s.max_energy` jadi `s . max_energy` dan titiknya
        # tidak lagi menempel. Versi pertama uji ini karena itu menyatakan
        # KETIGA hadiah menunjuk field mati, padahal ketiganya dibaca — lulus
        # palsu dengan arah sebaliknya, tapi sama menyesatkannya.
        pakai = [n for n, t in sumber.items()
                 if re.search(rf'\.\s*{f}\b', t)]
        cek(f"hadiah '{h['id']}' mengubah field yang dibaca permainan",
            bool(pakai), f"{f} dibaca di: {', '.join(pakai[:3]) or 'TIDAK ADA'}")


# ── 7b. Hadiah benar-benar berlaku ──────────────────────────────────────────
def uji_beli_hadiah():
    s = _state()
    s.kebahagiaan = 10_000
    h = w.HADIAH_BY_ID['tenaga']
    en_lama, maks_lama = s.energy, s.max_energy
    ok, pesan = w.beli_hadiah(s, 'tenaga')
    cek('hadiah: max_energy naik', ok and s.max_energy == maks_lama + h['tambah'],
        f'{maks_lama} -> {s.max_energy} ({pesan})')
    cek('hadiah: energi sekarang ikut naik, bukan menunggu besok',
        s.energy == min(s.max_energy, en_lama + h['tambah']),
        f'{en_lama} -> {s.energy}')
    cek('hadiah: Kebahagiaan terpotong', s.kebahagiaan == 10_000 - h['harga'])

    for _ in range(h['maks'] + 3):
        w.beli_hadiah(s, 'tenaga')
    cek('hadiah: berhenti di batas maksimum',
        w.hadiah_terpakai(s, 'tenaga') == h['maks'],
        f"dibeli {w.hadiah_terpakai(s, 'tenaga')}x, maks {h['maks']}")

    s2 = _state()
    s2.kebahagiaan = 0
    ok2, pesan2 = w.beli_hadiah(s2, 'tenaga')
    cek('hadiah: tanpa Kebahagiaan ditolak dengan alasan', not ok2 and pesan2,
        pesan2)


# ── 8. Save bolak-balik ─────────────────────────────────────────────────────
def uji_save():
    import json
    from game.config import SAVE_FILE
    cadangan = None
    if os.path.exists(SAVE_FILE):
        cadangan = open(SAVE_FILE, encoding='utf-8').read()
    try:
        s = _state()
        w.janjikan(s, {'id': 'kumpulkan_emas', 'param': {'n': 300},
                       'teks': 'Hasilkan 300G'})
        s.stats['earned'] = 300
        w.periksa(s)
        w.beli_hadiah(s, 'pemulih') if s.kebahagiaan >= 200 else None
        s.kebahagiaan += 777
        tersimpan = s.save()
        cek('save: tertulis', tersimpan)
        s2, status = GameState.load_with_status()
        cek('save: termuat', status == 'ok' and s2 is not None, status)
        if s2 is None:
            return
        cek('save: Kebahagiaan bertahan', s2.kebahagiaan == s.kebahagiaan,
            f'{s.kebahagiaan} -> {s2.kebahagiaan}')
        cek('save: total seumur hidup bertahan',
            s2.kebahagiaan_total == s.kebahagiaan_total)
        cek('save: hadiah bertahan', s2.hadiah == s.hadiah,
            f'{s.hadiah} -> {s2.hadiah}')
        # Janji yang masih berjalan juga harus utuh, termasuk garis dasarnya.
        s3 = _state()
        w.janjikan(s3, {'id': 'panen_apa_saja', 'param': {'n': 10},
                        'teks': 'Panen 10 hasil kebun apa pun'})
        s3.stats['harvested'] = 4
        s3.save()
        s4, _ = GameState.load_with_status()
        cek('save: janji yang berjalan bertahan beserta garis dasarnya',
            s4 and len(s4.janji) == 1 and s4.janji[0]['awal'] == s3.janji[0]['awal'],
            f'{s3.janji[0] if s3.janji else None} -> '
            f'{s4.janji[0] if s4 and s4.janji else None}')
    finally:
        if cadangan is not None:
            with open(SAVE_FILE, 'w', encoding='utf-8') as f:
                f.write(cadangan)
        elif os.path.exists(SAVE_FILE):
            os.remove(SAVE_FILE)


# ── 9. Lingkaran penuh ──────────────────────────────────────────────────────
def uji_lingkaran_penuh():
    """Janji -> kerjakan -> dibayar -> belanja -> kemampuan naik.

    Kalau yang ini lulus, mekanisme Tahap 4 utuh dari ujung ke ujung.
    """
    s = _state(inventory={'tomat_seed': 5})
    kand = w.tawaran(s)
    if not kand:
        cek('lingkaran penuh: ada tawaran', False, 'tawaran kosong')
        return
    pilih = kand[0]
    ok, _ = w.janjikan(s, pilih)
    templat = w.KATALOG_BY_ID[pilih['id']]
    # Kerjakan: dorong penghitungnya sampai target, lewat jalur yang sama
    # dengan yang dipakai permainan (stats / gold / hearts).
    j = s.janji[0]
    butuh = j['butuh']
    if pilih['id'] == 'panen_tanaman':
        per = s.stats.setdefault('panen_tanaman', {})
        per[pilih['param']['crop']] = j['awal'] + butuh
    elif pilih['id'] == 'panen_apa_saja':
        s.stats['harvested'] = j['awal'] + butuh
    elif pilih['id'] == 'siram':
        s.stats['watered'] = j['awal'] + butuh
    elif pilih['id'] == 'kumpulkan_emas':
        s.stats['earned'] = j['awal'] + butuh
    elif pilih['id'] == 'punya_emas':
        s.gold = butuh
    elif pilih['id'] == 'olah':
        s.stats['processed'] = j['awal'] + butuh
    elif pilih['id'] == 'hadiah':
        s.stats['gifts'] = j['awal'] + butuh
    elif pilih['id'] == 'hasil_ternak':
        s.stats['produce_collected'] = j['awal'] + butuh
    elif pilih['id'] == 'hati_npc':
        s.npc_hearts[pilih['param']['npc']] = butuh
    elif pilih['id'] == 'tambang':
        s.stats['minerals_mined'] = j['awal'] + butuh
    elif pilih['id'] == 'turun_gua':
        s.stats['deepest_level'] = butuh
    elif pilih['id'] == 'kalahkan_mob':
        s.stats['mobs_killed'] = j['awal'] + butuh
    lunas = w.periksa(s)
    cek('lingkaran penuh: dijanjikan lalu dibayar',
        ok and len(lunas) == 1 and s.kebahagiaan == templat['bayar'],
        f"{pilih['teks']} -> +{s.kebahagiaan}")

    # Belanja sampai satu hadiah termurah terjangkau.
    termurah = min(w.HADIAH, key=lambda h: h['harga'])
    s.kebahagiaan = termurah['harga']
    maks_lama = getattr(s, termurah['field'])
    ok2, pesan = w.beli_hadiah(s, termurah['id'])
    cek('lingkaran penuh: Kebahagiaan jadi kemampuan permanen',
        ok2 and getattr(s, termurah['field']) > maks_lama,
        f"{termurah['nama']}: {maks_lama} -> {getattr(s, termurah['field'])}")


# ── 10. Panel bisa dicetak ──────────────────────────────────────────────────
def uji_panel():
    s = _state(inventory={'tomat_seed': 2}, pickaxe_tier=1)
    w.janjikan(s, {'id': 'panen_apa_saja', 'param': {'n': 10},
                   'teks': 'Panen 10 hasil kebun apa pun'})
    s.stats['harvested'] = 3
    baris = w.baris_panel(s)
    cek('panel: menghasilkan baris', len(baris) > 8, f'{len(baris)} baris')
    teks = '\n'.join(baris)
    cek('panel: menampilkan Kebahagiaan', 'Kebahagiaan' in teks)
    cek('panel: menampilkan bar kemajuan janji', '#' in teks and '3/10' in teks)
    cek('panel: menampilkan hadiah beserta harganya',
        all(h['nama'] in teks for h in w.HADIAH))
    cek('panel: tiap baris cukup pendek untuk panel',
        max(len(b) for b in baris) <= 76,
        f'terpanjang {max(len(b) for b in baris)} karakter')


UJI = [uji_garis_dasar, uji_ambang, uji_tetap_sehari, uji_relevansi, uji_slot,
       uji_bayar, uji_hadiah_hidup, uji_beli_hadiah, uji_save,
       uji_lingkaran_penuh, uji_panel]


def main():
    print()
    print('UJI MESIN KEINGINAN — Tahap 4')
    print('=' * 78)
    for fn in UJI:
        try:
            fn()
        except Exception as ex:
            import traceback
            cek(f'{fn.__name__} meledak', False, f'{type(ex).__name__}: {ex}')
            traceback.print_exc()
    lebar = max(len(n) for n, _, _ in hasil)
    for nama, ok, ket in hasil:
        tanda = 'LULUS' if ok else 'GAGAL'
        ekor = f'  {ket}' if ket else ''
        print(f'{tanda:>5s}  {nama:<{lebar}s}{ekor}')
    gagal = [n for n, ok, _ in hasil if not ok]
    print('-' * 78)
    print(f'{len(hasil) - len(gagal)}/{len(hasil)} lulus')
    if gagal:
        print('GAGAL: ' + '; '.join(gagal))
    sys.stdout.flush()
    sys.exit(1 if gagal else 0)


if __name__ == '__main__':
    main()
