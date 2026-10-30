"""panel_daftar.py — panel berbaris: Warung, Dapur, Bengkel, Papan, Keinginan,
Ekosistem.

Keenam panel ini sampai 30 Okt 2026 adalah tabel teks berkolom yang disusun
dengan spasi (`f"{nama:<16}{harga:>5}G"`). Di font proporsional kolom itu
tidak pernah lurus -- Papan Permintaan terbaca miring -- dan Ekosistem
meluber keluar kartu sampai menimpa kepingan ESC.

Di sini tiap baris digambar sungguhan: kepingan nomor (tombol yang
benar-benar ditekan), ikon barang, judul + keterangan, kolom kanan yang
dijangkar ke x tetap (jadi lurus berapa pun lebar hurufnya), dan pil status
(SIAP / KURANG / PUNYA). Datanya diambil dari fungsi yang sama dengan teks
lamanya -- SHOP_ITEMS, sellable_items, PROCESS_RECIPES, resep bengkel,
jobs.daftar, wishes.tawaran -- dan dalam URUTAN yang sama, jadi nomor yang
tergambar selalu nomor yang dijalankan `panel_action`.
"""
from __future__ import annotations

from ursina import color

from . import panel_kartu as PK

MERAH = (226, 104, 104)
BIRU = (132, 176, 236)


# ── widget ─────────────────────────────────────────────────────────────
def tab_kapsul(kv, x, y, label, aktif):
    """Deretan kapsul tab; yang aktif emas. Kembalikan x ujung kanan."""
    for i, t in enumerate(label):
        w = 0.040 + 0.0125 * len(t)
        pilih = i == aktif
        kv.kotak(x + w / 2, y, w, 0.040, PK.EMAS if pilih else (60, 58, 70), 255, 0.5)
        kv.teks(t, (x + w / 2, y), 0.60, (24, 22, 30) if pilih else PK.REDUP, asal=(0, 0))
        x += w + 0.010
    return x


def info(kv, x, y, label, nilai, warna=PK.TERANG):
    """'Label  nilai' kecil di pita atas; kembalikan x berikutnya."""
    t1 = kv.teks(label, (x, y), 0.50, PK.REDUP)
    x += PK._lebar(t1) + 0.008
    t2 = kv.teks(nilai, (x, y), 0.62, warna)
    return x + PK._lebar(t2) + 0.030


def pil(kv, x_kanan, y, teks, warna):
    w = 0.026 + 0.0105 * len(teks)
    kv.kotak(x_kanan - w / 2, y, w, 0.030, warna, 235, 0.5, z=0.05)
    kv.teks(teks, (x_kanan - w / 2, y), 0.46, (20, 22, 28), asal=(0, 0))
    return w


def baris(kv, ui, y, nomor, judul, sub='', kolom=(), status=None, item=None,
          redup=False, sorot=False, x0=None, x1=None, h=0.050):
    """Satu baris daftar.

    kolom  : [(x_kanan, teks, warna)] -- dijangkar rata kanan di x tetap
    status : (teks, warna) pil di ujung kanan, atau None
    item   : id barang untuk ikon (tekstur crop/item, atau cakram warna)
    """
    x0 = PK.KIRI if x0 is None else x0
    x1 = PK.KANAN if x1 is None else x1
    if sorot:
        kv.kotak((x0 + x1) / 2, y, x1 - x0 + 0.012, h - 0.006, PK.EMAS, 30, 0.3, z=0.075)
    else:
        kv.kotak((x0 + x1) / 2, y, x1 - x0 + 0.012, h - 0.006, (255, 255, 255), 8, 0.3, z=0.075)
    x = x0
    if nomor is not None:
        x += kv.tuts(str(nomor), x, y, tinggi=0.028) + 0.012
    if item is not None and ui is not None:
        tex = ui._item_icon_tex(item)
        if tex is not None:
            kv.quad(texture=tex, scale=(0.036, 0.036), position=(x + 0.018, y), z=0.04,
                    color=color.white if not redup else color.rgba(255, 255, 255, 120))
        else:
            c = ui._item_icon_color(item)
            kv.kotak(x + 0.018, y, 0.028, 0.028,
                     tuple(int(v * 255) for v in (c[0], c[1], c[2])), 140 if redup else 255, 0.5,
                     z=0.04)
        x += 0.046
    wj = PK.TERANG if not redup else PK.REDUP
    if sub:
        kv.teks(judul, (x, y + 0.009), 0.60, wj)
        kv.teks(sub, (x, y - 0.012), 0.45, PK.REDUP)
    else:
        kv.teks(judul, (x, y), 0.62, wj)
    for xk, teks, warna in kolom:
        kv.teks(teks, (xk, y), 0.58, warna if not redup else PK.REDUP, asal=(0.5, 0))
    if status:
        pil(kv, x1, y, *status)


def judul_bagian(kv, x, y, teks, ekor=''):
    kv.teks(teks, (x, y), 0.58, PK.EMAS)
    if ekor:
        kv.teks(ekor, (PK.KANAN, y), 0.50, PK.REDUP, asal=(0.5, 0))


def catatan(kv, y, teks):
    kv.teks(teks, (PK.KIRI, y), 0.48, PK.REDUP)


def halaman(kv, page, n_pages):
    if n_pages > 1:
        kv.teks(f'halaman {page + 1}/{n_pages}', (PK.KANAN, PK.Y_KAKI), 0.52, PK.REDUP,
                asal=(0.5, 0))


# ── Warung ─────────────────────────────────────────────────────────────
def gambar_warung(kv, ui, s):
    from .data import SHOP_ITEMS
    from .economy import margin_hint, item_name
    from .market import (price as harga_kini, sellable_items, inventory_value,
                         trend_mark, demand_note)
    mode, _ = ui._market_state()
    y = PK.Y_ISI - 0.022
    xe = tab_kapsul(kv, PK.KIRI, y, ('BELI', 'JUAL'), 0 if mode == 'beli' else 1)
    x = xe + 0.03
    x = info(kv, x, y, 'Emas', f'{s.gold}G', PK.EMAS)
    info(kv, x, y, 'Nilai tas', f'{inventory_value(s, s.inventory)}G')
    y -= 0.050
    note = demand_note(s)
    if note:
        kv.kotak(0, y, PK.W - 0.11, 0.036, PK.EMAS, 40, 0.4)
        kv.teks(note, (PK.KIRI + 0.012, y), 0.52, PK.EMAS)
        y -= 0.046
    XH, XM, XN = 0.10, 0.30, PK.KANAN - 0.13

    if mode == 'beli':
        rows, page, n_pages = ui._page_slice(list(SHOP_ITEMS))
        kv.teks('HARGA', (XH, y), 0.46, PK.REDUP, asal=(0.5, 0))
        kv.teks('MUSIM', (XM, y), 0.46, PK.REDUP, asal=(0.5, 0))
        kv.teks('HASIL PANEN NANTI', (XN, y), 0.46, PK.REDUP, asal=(0.5, 0))
        y -= 0.036
        for i, it in enumerate(rows):
            punya = it.get('animal') in getattr(s, 'owned_animals', [])
            mampu = s.gold >= it['price']
            status = (('DI KANDANG', PK.REDUP) if punya else
                      (None if mampu else ('EMAS KURANG', MERAH)))
            baris(kv, ui, y, i + 1, it['name'],
                  kolom=((XH, f"{it['price']}G", PK.EMAS),
                         (XM, str(it.get('season', '')), PK.REDUP),
                         (XN, margin_hint(it), PK.TERANG)),
                  status=status, item=it.get('id'), redup=punya or not mampu)
            y -= 0.050
        catatan(kv, y - 0.004, 'Angka = beli 1. Kolom kanan: hasil panennya nanti, '
                               'jadi untung-ruginya terlihat sebelum bayar.')
    else:
        all_rows = sellable_items(s, s.inventory)
        if not all_rows:
            kv.teks('Tidak ada yang bisa dijual. Panen dulu, atau ambil hasil ternak di kandang.',
                    (PK.KIRI, y - 0.02), 0.60, PK.REDUP)
            return
        rows, page, n_pages = ui._page_slice(all_rows)
        kv.teks('JML', (XH - 0.06, y), 0.46, PK.REDUP, asal=(0.5, 0))
        kv.teks('HARGA', (XH + 0.06, y), 0.46, PK.REDUP, asal=(0.5, 0))
        kv.teks('SEMUA', (XM + 0.05, y), 0.46, PK.REDUP, asal=(0.5, 0))
        kv.teks('ARAH HARGA', (XN, y), 0.46, PK.REDUP, asal=(0.5, 0))
        y -= 0.036
        for i, (item, qty, total) in enumerate(rows):
            tren = trend_mark(s, item)
            naik = tren.startswith('^')
            turun = tren.startswith('v')
            kata = ('naik' if naik else 'turun' if turun else 'normal') + \
                   (' tajam' if len(tren.strip()) > 1 else '')
            baris(kv, ui, y, i + 1, item_name(item),
                  kolom=((XH - 0.06, f'x{qty}', PK.TERANG),
                         (XH + 0.06, f'{harga_kini(s, item)}G', PK.EMAS),
                         (XM + 0.05, f'{total}G', PK.EMAS),
                         (XN, kata, PK.HIJAU if naik else MERAH if turun else PK.REDUP)),
                  item=item)
            y -= 0.050
        catatan(kv, y - 0.004, 'Angka = jual SEMUA barang di baris itu. Menjual banyak '
                               'sekaligus menekan harganya; ia pulih tiap pagi.')
    halaman(kv, page, n_pages)


# ── Dapur ──────────────────────────────────────────────────────────────
def gambar_dapur(kv, ui, s):
    from .economy import (PROCESS_RECIPES, recipe_input_value, recipe_output_value,
                          recipe_uplift, item_name)
    y = PK.Y_ISI - 0.022
    x = info(kv, PK.KIRI, y, 'Emas', f'{s.gold}G', PK.EMAS)
    x = info(kv, x, y, 'Energi', f'{s.energy}/{s.max_energy}', PK.TERANG)
    kv.teks('Mengolah menambah sekitar 40% nilai, dibayar dengan energi.',
            (PK.KANAN, y), 0.48, PK.REDUP, asal=(0.5, 0))
    y -= 0.050
    rows, page, n_pages = ui._page_slice(list(PROCESS_RECIPES))
    XV, XN, XE = 0.22, 0.38, 0.48
    kv.teks('NILAI BAHAN > HASIL', (XV, y), 0.46, PK.REDUP, asal=(0.5, 0))
    kv.teks('UNTUNG', (XN, y), 0.46, PK.REDUP, asal=(0.5, 0))
    kv.teks('ENERGI', (XE, y), 0.46, PK.REDUP, asal=(0.5, 0))
    y -= 0.036
    for i, r in enumerate(rows):
        bahan = ', '.join(f"{item_name(k)} x{v}" for k, v in r['needs'].items())
        punya = all(s.inventory.get(k, 0) >= v for k, v in r['needs'].items())
        cukup = s.energy >= r['en']
        out_n = f"{item_name(r['out'])} x{r['n']}" if r['n'] > 1 else item_name(r['out'])
        naik = int(round((recipe_uplift(r) - 1) * 100))
        bisa = punya and cukup
        baris(kv, ui, y, i + 1, out_n, sub='dari ' + bahan,
              kolom=((XV, f'{recipe_input_value(r)}G > {recipe_output_value(r)}G', PK.EMAS),
                     (XN, f'+{naik}%', PK.HIJAU),
                     (XE, f"{r['en']}", PK.TERANG)),
              status=('SIAP', PK.HIJAU) if bisa else
                     (('BAHAN KURANG', MERAH) if not punya else ('LELAH', MERAH)),
              item=r['out'], redup=not bisa, sorot=bisa)
        y -= 0.052
    catatan(kv, y - 0.004, 'Pakan Ternak dinilai dari jerami yang tidak jadi dibeli '
                           '(18G/hari-pakan): menjualnya rugi, memakainya untung.')
    halaman(kv, page, n_pages)


# ── Bengkel ────────────────────────────────────────────────────────────
TAB_BENGKEL = ('Pickaxe', 'Pedang', 'Perkakas')


def resep_bengkel(tab):
    from .data import PICKAXE_RECIPES, SWORD_RECIPES, CRAFT_RECIPES
    return (PICKAXE_RECIPES, SWORD_RECIPES, CRAFT_RECIPES)[tab]


def gambar_bengkel(kv, ui, s):
    from .economy import item_name
    tab = getattr(ui, '_craft_tab', 0)
    y = PK.Y_ISI - 0.022
    xe = tab_kapsul(kv, PK.KIRI, y, TAB_BENGKEL, tab)
    x = info(kv, xe + 0.03, y, 'Emas', f'{s.gold}G', PK.EMAS)
    x = info(kv, x, y, 'Pickaxe', f'Tier {s.pickaxe_tier}')
    info(kv, x, y, 'Pedang', item_name(s.sword_id) if s.sword_id else '-')
    y -= 0.060
    inv = s.inventory
    XG = 0.16
    kv.teks('BIAYA', (XG, y), 0.46, PK.REDUP, asal=(0.5, 0))
    y -= 0.036
    for i, r in enumerate(resep_bengkel(tab)):
        bahan = ', '.join(f"{item_name(k)} {inv.get(k, 0)}/{v}" for k, v in r['needs'].items())
        cukup_e = s.gold >= r['cost_gold']
        cukup_b = all(inv.get(k, 0) >= v for k, v in r['needs'].items())
        if tab == 0:
            sudah = s.pickaxe_tier >= r['tier']
        elif tab == 1:
            sudah = s.sword_id == r['id']
        else:
            sudah = False
        sub = bahan
        if tab == 1:
            sub += f"   ·   DMG {r['damage']}"
        if tab == 2 and r.get('desc'):
            sub += f"   ·   {r['desc']}"
        status = (('PUNYA', PK.REDUP) if sudah else
                  ('SIAP', PK.HIJAU) if (cukup_e and cukup_b) else
                  ('EMAS KURANG', MERAH) if not cukup_e else ('BAHAN KURANG', MERAH))
        baris(kv, ui, y, i + 1, r['name'], sub=sub,
              kolom=((XG, f"{r['cost_gold']}G" if r['cost_gold'] else '-', PK.EMAS),),
              status=status, item=r.get('id'), redup=sudah or status[0] != 'SIAP',
              sorot=status[0] == 'SIAP')
        y -= 0.056
    catatan(kv, y - 0.004, 'Q/E pindah kelompok. Angka = buat barang di baris itu.')


# ── Papan permintaan ───────────────────────────────────────────────────
def gambar_papan(kv, ui, s):
    from .jobs import daftar, bisa_setor, punya, ensure, _KATA, _nama_minta, UMUR_HARI, PREMI
    from .data import HUMAN_NPCS
    y = PK.Y_ISI - 0.022
    x = info(kv, PK.KIRI, y, 'Emas', f'{s.gold}G', PK.EMAS)
    info(kv, x, y, 'Tuntas', str(ensure(s).get('tuntas', 0)))
    y -= 0.060
    t_semua = daftar(s)
    if not t_semua:
        kv.teks('Papan kosong hari ini. Warga sedang tidak butuh apa-apa.',
                (PK.KIRI, y), 0.62, PK.REDUP)
        return
    XP, XB, XS = 0.20, 0.34, 0.45
    kv.teks('PUNYA', (XP, y), 0.46, PK.REDUP, asal=(0.5, 0))
    kv.teks('BAYAR', (XB, y), 0.46, PK.REDUP, asal=(0.5, 0))
    kv.teks('SISA', (XS, y), 0.46, PK.REDUP, asal=(0.5, 0))
    y -= 0.040
    for i, t in enumerate(t_semua):
        nama = HUMAN_NPCS.get(t['npc'], {}).get('name', t['npc'])
        minta = f"{_KATA.get(t['jenis'], 'Bawakan')} {t['n']} {_nama_minta(t)}"
        siap = bisa_setor(s, t)
        x0 = PK.KIRI
        # Potret peminta di kiri judul.
        pt = PK.potret_tex(t['npc'])
        h = 0.064
        kv.kotak(0, y, PK.W - 0.098, h - 0.006, PK.EMAS if siap else (255, 255, 255),
                 34 if siap else 8, 0.3, z=0.075)
        w = kv.tuts(str(i + 1), x0, y, tinggi=0.028) + 0.012
        if pt is not None:
            kv.quad(texture=pt, scale=(0.046, 0.046), position=(x0 + w + 0.023, y),
                    z=0.04, color=color.white)
        kv.teks(minta, (x0 + w + 0.056, y + 0.010), 0.62, PK.TERANG)
        kv.teks(nama, (x0 + w + 0.056, y - 0.013), 0.46, PK.REDUP)
        n_punya = punya(s, t)
        # Bilah kecil "punya / butuh".
        frak = max(0.0, min(1.0, n_punya / max(1, t['n'])))
        kv.kotak(XP, y - 0.012, 0.09, 0.008, (60, 60, 70), 255, 0.5)
        if frak > 0:
            kv.kotak(XP - 0.045 + 0.045 * frak, y - 0.012, 0.09 * frak, 0.008,
                     PK.HIJAU if siap else PK.EMAS, 255, 0.5, z=0.05)
        kv.teks(f'{n_punya}/{t["n"]}', (XP, y + 0.008), 0.56, PK.TERANG, asal=(0, 0))
        kv.teks(f"{t['bayar']}G", (XB, y), 0.60, PK.EMAS, asal=(0.5, 0))
        kv.teks(f"{t['sisa']} hari", (XS, y), 0.56, PK.REDUP, asal=(0.5, 0))
        pil(kv, PK.KANAN, y, 'SETOR' if siap else 'KURANG', PK.HIJAU if siap else MERAH)
        y -= 0.070
    catatan(kv, y - 0.004, f'Bayaran mengikuti harga pasar hari ini plus '
                           f'{int(round((PREMI - 1) * 100))}%. Tiap permintaan hangus '
                           f'setelah {UMUR_HARI} hari.')


# ── Keinginan ──────────────────────────────────────────────────────────
def gambar_keinginan(kv, ui, s):
    from .wishes import (_janji_list, kemajuan, tawaran, HADIAH, hadiah_terpakai,
                         bisa_beli, SLOT_JANJI)
    janji = _janji_list(s)
    kb = int(getattr(s, 'kebahagiaan', 0))
    total = int(getattr(s, 'kebahagiaan_total', 0))
    y = PK.Y_ISI - 0.022
    x = info(kv, PK.KIRI, y, 'Kebahagiaan', str(kb), PK.EMAS)
    info(kv, x, y, 'seumur hidup', str(total))
    y -= 0.056

    # Kolom kiri: janji dengan bilah kemajuan.
    xl, xr = PK.KIRI, -0.02
    judul_bagian(kv, xl, y, f'JANJI  {len(janji)}/{SLOT_JANJI}')
    yl = y - 0.044
    if not janji:
        kv.teks('Belum ada. Pilih dari tawaran di kanan dengan [1-5].', (xl, yl), 0.52,
                PK.REDUP)
    for i, p in enumerate(janji, 1):
        maju, butuh = kemajuan(s, p)
        frak = max(0.0, min(1.0, maju / max(1, butuh)))
        kv.kotak((xl + xr) / 2, yl - 0.012, xr - xl, 0.078, (40, 40, 52), 235, 0.15)
        kv.tuts(str(i + 5), xl + 0.008, yl + 0.006, tinggi=0.026)
        kv.teks(p['teks'], (xl + 0.050, yl + 0.006), 0.58, PK.TERANG)
        kv.kotak(xl + 0.050 + 0.15, yl - 0.026, 0.30, 0.010, (60, 60, 70), 255, 0.5)
        if frak > 0:
            kv.kotak(xl + 0.050 + 0.15 * frak, yl - 0.026, 0.30 * frak, 0.010,
                     PK.HIJAU, 255, 0.5, z=0.05)
        kv.teks(f'{maju}/{butuh}   +{p["bayar"]}', (xr - 0.012, yl - 0.026), 0.48,
                PK.EMAS, asal=(0.5, 0))
        yl -= 0.092
    if janji:
        kv.teks('Angka 6-9 melupakan janji di kartu itu.', (xl, yl + 0.02), 0.44, PK.REDUP)

    # Kolom kanan: tawaran hari ini, lalu hadiah.
    xk = 0.03
    judul_bagian(kv, xk, y, 'TAWARAN HARI INI')
    yk = y - 0.044
    kand = tawaran(s)
    if not kand:
        kv.teks('Tidak ada yang masuk akal hari ini; besok berganti.', (xk, yk), 0.52,
                PK.REDUP)
    for i, c in enumerate(kand, 1):
        baris(kv, ui, yk, i, c['teks'], sub=c['kategori'],
              kolom=((PK.KANAN - 0.01, f"+{c['bayar']}", PK.EMAS),), x0=xk, h=0.050)
        yk -= 0.050
    yk -= 0.020
    judul_bagian(kv, xk, yk, 'HADIAH')
    yk -= 0.044
    for i, h in enumerate(HADIAH):
        n = hadiah_terpakai(s, h['id'])
        bisa, _ = bisa_beli(s, h['id'])
        baris(kv, ui, yk, chr(ord('A') + i), h['nama'], sub=h['teks'],
              kolom=((PK.KANAN - 0.12, f"{h['harga']}", PK.EMAS),
                     (PK.KANAN - 0.01, f"{n}/{h['maks']}x", PK.REDUP)),
              x0=xk, redup=not bisa, sorot=bisa)
        yk -= 0.054


# ── Ekosistem ──────────────────────────────────────────────────────────
GRUP_EKO = (
    ('AIR', ('ikan_danau', 'ikan_pantai', 'ikan_gua')),
    ('HUTAN', ('herba_gunung', 'jamur_gunung', 'mandrake', 'kayu_gunung')),
    ('PANTAI', ('kerang_pantai',)),
    ('LEMBAH', ('kunang',)),
    ('BAWAH TANAH', ('bijih_dangkal', 'bijih_tengah', 'bijih_dalam')),
)


def gambar_ekosistem(kv, ui, s):
    from .ecology import (ensure, abundance, STOCKS, status_word, tide_phase,
                          tide_level)
    from .market import movers, demand_note
    from .economy import item_name
    ensure(s)
    # Kolom kiri: kolam per tempat, bilah sungguhan.
    xl, xr = PK.KIRI, 0.02
    y = PK.Y_ISI - 0.010
    for judul, kunci in GRUP_EKO:
        judul_bagian(kv, xl, y, judul)
        y -= 0.034
        for k in kunci:
            a = abundance(s, k)
            warna = PK.HIJAU if a >= 0.6 else (PK.EMAS if a >= 0.3 else MERAH)
            kv.teks(STOCKS[k]['label'], (xl + 0.010, y), 0.52, PK.TERANG)
            bx, bw = xl + 0.30, 0.20
            kv.kotak(bx + bw / 2, y, bw, 0.010, (60, 60, 70), 255, 0.5)
            if a > 0:
                kv.kotak(bx + bw * a / 2, y, bw * a, 0.010, warna, 255, 0.5, z=0.05)
            kv.teks(f'{int(round(a * 100))}%', (xr, y), 0.48, warna, asal=(0.5, 0))
            y -= 0.028
        y -= 0.010
    kv.teks(f'Pasang surut pantai: {tide_phase(s)} ({int(round(tide_level(s) * 100))}%)',
            (xl, y), 0.48, BIRU)
    kv.teks('Kolam pulih paling cepat saat terisi separuh.', (xl, y - 0.024), 0.44,
            PK.REDUP)

    # Kolom kanan: pasar, rekor pancing.
    xk = 0.10
    y = PK.Y_ISI - 0.010
    judul_bagian(kv, xk, y, 'PASAR HARI INI')
    y -= 0.036
    gerak = movers(s, 6)
    if not gerak:
        kv.teks('Semua harga di sekitar nilai normalnya.', (xk, y), 0.52, PK.REDUP)
        y -= 0.030
    for item, kini, normal, rasio in gerak:
        naik = rasio > 1
        kv.teks(item_name(item), (xk + 0.010, y), 0.54, PK.TERANG)
        kv.teks(f'{kini}G', (PK.KANAN - 0.13, y), 0.54, PK.EMAS, asal=(0.5, 0))
        kv.teks(f"{'+' if naik else '-'}{abs(int(round((rasio - 1) * 100)))}%",
                (PK.KANAN, y), 0.52, PK.HIJAU if naik else MERAH, asal=(0.5, 0))
        y -= 0.030
    note = demand_note(s)
    if note:
        y -= 0.006
        kv.teks(note[:58], (xk, y), 0.44, PK.EMAS)
        y -= 0.030
    try:
        from .fishing import SPESIES, tersedia, perairan_untuk
        log = getattr(s, 'fish_log', None) or {}
        rek = sorted(((k, v) for k, v in log.items() if k in SPESIES),
                     key=lambda r: -float(r[1]))
        y -= 0.016
        judul_bagian(kv, xk, y, 'REKOR PANCING')
        y -= 0.036
        if not rek:
            kv.teks('Belum ada tangkapan.', (xk + 0.010, y), 0.50, PK.REDUP)
            y -= 0.030
        for sid, kg in rek[:5]:
            kv.teks(item_name(sid), (xk + 0.010, y), 0.54, PK.TERANG)
            kv.teks(f'{float(kg):.2f} kg', (PK.KANAN, y), 0.52, PK.EMAS, asal=(0.5, 0))
            y -= 0.030
        umpan = tersedia(s, perairan_untuk(s, None))
        if umpan:
            y -= 0.010
            kv.teks('Menggigit di sini: ' + ', '.join(item_name(u) for u in umpan[:4]),
                    (xk, y), 0.46, BIRU)
    except Exception:
        pass
