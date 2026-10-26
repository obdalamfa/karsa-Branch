"""panel_kartu.py — rupa panel menu: kartu berbingkai, kepala emas, isi tertata.

Kenapa ini ada. Sampai 26 Okt 2026 semua panel menu (I, J, M, H, P, N, F1,
warung, dapur, bengkel) adalah satu blok teks ASCII di atas lempeng gelap:
`[v] [0] Baru Datang`, bilah hati `*****-----`, dan peta yang digambar
dengan `---` dan `|`. Dari tangkapan layar, panel-panel itu terbaca sebagai
konsol debug, bukan sebagai bagian dari permainan yang sama dengan layar
judulnya.

Isinya sendiri tidak salah, jadi modul ini tidak mengganti mesinnya. Ia
memberi tiga hal:

  bingkai   satu kartu bersudut bulat dengan pita kepala, garis emas, dan
            kaki berisi kepingan tombol (dibaca dari teks petunjuk lama,
            jadi semua panel ikut tanpa disentuh satu per satu)
  tipografi judul bagian `── X ──` jadi baris emas, `[v]`/`[o]`/`[ ]` jadi
            tanda centang berwarna
  tata isi  empat panel yang paling sering dibuka digambar sungguhan:
            Jurnal (daftar tahap + kartu "sedang dikerjakan"), Peta (simpul
            dan jalur dari data portal scene, bukan tebakan), Hubungan
            (potret + hati), dan Panduan (kepingan tombol dua kolom).

Warna dan bentuk sengaja sama dengan layar judul (menu_judul.py): emas
(244,214,140) di atas biru-arang, belah ketupat sebagai penanda.
"""
from __future__ import annotations

import re

from ursina import Entity, Text, Texture, camera, color, destroy

EMAS = (244, 214, 140)
REDUP = (170, 166, 156)
TERANG = (232, 228, 218)
HIJAU = (128, 206, 140)
KARTU = (20, 22, 30)

# Ukuran kartu di ruang camera.ui (tinggi layar = 1).
W, H = 1.44, 0.90
KIRI = -W / 2 + 0.055
KANAN = W / 2 - 0.055
ATAS = H / 2
Y_JUDUL = ATAS - 0.062
Y_GARIS = ATAS - 0.108
Y_ISI = ATAS - 0.135
Y_KAKI = -ATAS + 0.045

_FONT = 'Montserrat-Bold.ttf'
_CACHE: dict = {}


# ── tekstur ─────────────────────────────────────────────────────────────
def _pil():
    from PIL import Image, ImageDraw, ImageFilter
    return Image, ImageDraw, ImageFilter


def kartu_tex(lebar_px=1440, tinggi_px=900, pita=True):
    """Kartu bersudut bulat: badan gelap, pita kepala sedikit lebih terang,
    bingkai emas tipis, dan bayangan lunak di sekeliling (ditanam di
    tekstur, jadi tidak butuh entity kedua)."""
    kunci = ('kartu', lebar_px, tinggi_px, pita)
    if kunci in _CACHE:
        return _CACHE[kunci]
    tex = None
    try:
        Image, ImageDraw, ImageFilter = _pil()
        pad = 26
        w, h = lebar_px + pad * 2, tinggi_px + pad * 2
        img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        bay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(bay).rounded_rectangle([pad, pad + 6, w - pad, h - pad + 6],
                                              radius=34, fill=(0, 0, 0, 150))
        img.alpha_composite(bay.filter(ImageFilter.GaussianBlur(14)))
        d = ImageDraw.Draw(img)
        kotak = [pad, pad, w - pad, h - pad]
        d.rounded_rectangle(kotak, radius=30, fill=(*KARTU, 244))
        # Pita kepala: rata bawahnya, bulat atasnya.
        if pita:
            _pita_kepala(img, w, h, pad, tinggi_px)
        # Bingkai emas tipis + garis dalam gelap: terbaca sebagai tepi timbul.
        d.rounded_rectangle(kotak, radius=30, outline=(*EMAS, 120), width=3)
        d.rounded_rectangle([pad + 5, pad + 5, w - pad - 5, h - pad - 5], radius=26,
                            outline=(0, 0, 0, 90), width=2)
        tex = Texture(img)
        tex.filtering = 'bilinear'
        _CACHE[kunci] = (tex, w / lebar_px, h / tinggi_px)
        return _CACHE[kunci]
    except Exception:
        _CACHE[kunci] = (None, 1.0, 1.0)
        return _CACHE[kunci]


def _pita_kepala(img, w, h, pad, tinggi_px):
    Image, ImageDraw, _ = _pil()
    pita = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    tp = int(tinggi_px * 0.118)
    ImageDraw.Draw(pita).rounded_rectangle([pad, pad, w - pad, pad + tp + 30],
                                           radius=30, fill=(36, 36, 46, 255))
    topeng = Image.new('L', (w, h), 0)
    ImageDraw.Draw(topeng).rectangle([0, 0, w, pad + tp], fill=255)
    img.paste(pita, (0, 0), Image.composite(pita, Image.new('RGBA', (w, h)), topeng)
              .getchannel('A'))


def kotak_tex(rasio=4.0, radius=0.25, isi=(255, 255, 255, 255), garis=None,
              tinggi=48):
    """Kotak bersudut bulat PUTIH (diwarnai lewat entity.color) dengan rasio
    tertentu; dipakai baris sorot, simpul peta, kepingan, bilah."""
    rasio = max(0.25, round(rasio * 4) / 4)
    kunci = ('kotak', rasio, radius, isi, garis, tinggi)
    if kunci in _CACHE:
        return _CACHE[kunci]
    tex = None
    try:
        Image, ImageDraw, _ = _pil()
        s = 3
        hh = tinggi * s
        ww = max(4, int(hh * rasio))
        img = Image.new('RGBA', (ww, hh), (255, 255, 255, 0))
        d = ImageDraw.Draw(img)
        r = int(min(ww, hh) * radius)
        d.rounded_rectangle([1, 1, ww - 2, hh - 2], radius=r, fill=isi,
                            outline=garis, width=(2 * s if garis else 0))
        img = img.resize((max(1, ww // s), tinggi), Image.LANCZOS)
        tex = Texture(img)
        tex.filtering = 'bilinear'
    except Exception:
        tex = None
    _CACHE[kunci] = tex
    return tex


def potret_tex(npc_id):
    """Potret warga dipotong bulat; None kalau tidak ada berkasnya."""
    kunci = ('potret', npc_id)
    if kunci in _CACHE:
        return _CACHE[kunci]
    tex = None
    try:
        from pathlib import Path
        p = Path(__file__).resolve().parent.parent / 'assets' / 'textures' / 'potret' / f'{npc_id}.png'
        if p.exists():
            Image, ImageDraw, _ = _pil()
            im = Image.open(p).convert('RGBA')
            n = min(im.size)
            im = im.crop(((im.width - n) // 2, 0, (im.width - n) // 2 + n, n)).resize((128, 128))
            topeng = Image.new('L', (128, 128), 0)
            ImageDraw.Draw(topeng).ellipse([2, 2, 125, 125], fill=255)
            bulat = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
            bulat.paste(im, (0, 0), topeng)
            ImageDraw.Draw(bulat).ellipse([2, 2, 125, 125], outline=(*EMAS, 200), width=4)
            tex = Texture(bulat)
            tex.filtering = 'bilinear'
    except Exception:
        tex = None
    _CACHE[kunci] = tex
    return tex


# ── kepingan kaki: "[ESC: tutup]" -> [ESC] tutup ────────────────────────
_POLA_HINT = re.compile(r'\[([^:\]]+):\s*([^\]]+)\]')


def urai_petunjuk(teks):
    """'[1-5: janjikan]   [ESC: Tutup]' -> [('1-5','janjikan'), ('ESC','Tutup')]."""
    return [(a.strip(), b.strip()) for a, b in _POLA_HINT.findall(teks or '')]


# ── tipografi isi teks ──────────────────────────────────────────────────
_JUDUL_BAGIAN = re.compile(r'^\s*[-─=]{2,}\s*(.+?)\s*[-─=]{2,}\s*$')


def hias_isi(teks):
    """Baris `── X ──` jadi judul emas; tanda [v]/[o]/[>] berwarna.

    Memakai tag warna Text Ursina (<emas>, <hijau>, ...). Tanda '<' di isi
    asli diganti dulu supaya tidak terbaca sebagai tag.
    """
    keluar = []
    for b in (teks or '').split('\n'):
        b = b.replace('<', '‹').replace('>', '›')
        m = _JUDUL_BAGIAN.match(b)
        if m:
            keluar.append(f'<emas>{m.group(1).upper()}<default>')
            continue
        # Montserrat tidak punya glif centang/lingkaran/segitiga (diukur
        # dengan PIL: tampil sebagai kotak kosong), jadi tandanya tetap
        # huruf yang ada di font, tapi berwarna.
        b = (b.replace('[v]', '<hijau>[•]<default>')
              .replace('[o]', '<emas>[•]<default>')
              .replace('[›]', '<emas>›<default>'))
        keluar.append(b)
    return '\n'.join(keluar)


def pasang_warna(t):
    t.text_colors['emas'] = color.rgb(*EMAS)
    t.text_colors['hijau'] = color.rgb(*HIJAU)
    t.text_colors['redup'] = color.rgb(*REDUP)
    t.text_colors['default'] = t.color


class Kanvas:
    """Wadah entity isi panel. Dibersihkan tiap render dan saat panel tutup."""

    def __init__(self):
        self.ents = []

    def bersih(self):
        for e in self.ents:
            try:
                destroy(e)
            except Exception:
                pass
        self.ents = []

    def quad(self, **kw):
        kw.setdefault('model', 'quad')
        kw.setdefault('transparent', True)
        e = Entity(parent=camera.ui, **kw)
        self.ents.append(e)
        return e

    def teks(self, isi, pos, skala=0.8, warna=TERANG, asal=(-0.5, 0), **kw):
        t = Text(isi, parent=camera.ui, font=_FONT, position=pos,
                 scale=skala * 1.2, color=color.rgb(*warna), origin=asal, **kw)
        pasang_warna(t)
        if '<' in isi:
            t.text = isi            # tag dibaca ulang setelah warnanya terdaftar
        self.ents.append(t)
        return t

    def kotak(self, cx, cy, w, h, warna, alfa=255, radius=0.30, z=0.06, garis=None):
        tex = kotak_tex(w / max(h, 1e-4), radius, garis=garis)
        return self.quad(texture=tex, scale=(w, h), position=(cx, cy), z=z,
                         color=color.rgba(*warna, alfa))

    def tuts(self, label, x, y, tinggi=0.028, kanan=False):
        """Kepingan tombol; kembalikan lebarnya."""
        from .panels import tuts_tex
        tex, rasio = tuts_tex(label, 30)
        w = tinggi * rasio
        cx = x - w / 2 if kanan else x + w / 2
        self.quad(texture=tex, scale=(w, tinggi), position=(cx, y), z=0.02,
                  color=color.white)
        return w


def gambar_kaki(kv, petunjuk, y=Y_KAKI):
    """Kepingan tombol berderet dari kiri: [ESC] tutup  [1-5] janjikan ..."""
    x = KIRI
    for tombol, kata in urai_petunjuk(petunjuk):
        w = kv.tuts(tombol, x, y)
        t = kv.teks(kata, (x + w + 0.010, y), skala=0.62, warna=REDUP)
        x += w + 0.020 + _lebar(t) + 0.030
    return x


def _lebar(t):
    try:
        tb = t.getTightBounds(camera.ui)
        if tb is not None:
            return float(tb[1].x - tb[0].x)
    except Exception:
        pass
    return 0.0


# ── panel yang digambar sungguhan ───────────────────────────────────────
def gambar_quest(kv, s):
    from .data import QUEST_STAGES, SIDE_QUESTS
    qs = s.quest_stage
    n = len(QUEST_STAGES)
    # Bilah kemajuan di bawah garis kepala.
    x0, lebar = KIRI, 0.56
    y = Y_ISI - 0.006
    kv.teks('TUGAS UTAMA', (x0, y), 0.60, EMAS)
    kv.teks(f'{min(qs, n)}/{n}', (x0 + lebar, y), 0.60, REDUP, asal=(0.5, 0))
    yb = y - 0.028
    kv.kotak(x0 + lebar / 2, yb, lebar, 0.010, (60, 60, 70), 255, 0.5)
    frak = max(0.0, min(1.0, qs / float(n)))
    if frak > 0:
        kv.kotak(x0 + lebar * frak / 2, yb, lebar * frak, 0.010, EMAS, 255, 0.5, z=0.05)

    baris_h = 0.046
    y = yb - 0.040
    for q in QUEST_STAGES:
        selesai, kini = q['s'] < qs, q['s'] == qs
        if kini:
            kv.kotak(x0 + lebar / 2 - 0.006, y, lebar + 0.030, baris_h - 0.004,
                     (244, 214, 140), 34, 0.35)
        cx = x0 + 0.012
        if selesai:
            kv.kotak(cx, y, 0.022, 0.022, HIJAU, 255, 0.5, z=0.04)
            kv.kotak(cx, y, 0.009, 0.009, (18, 40, 24), 255, 0.5, z=0.035)
        else:
            kv.kotak(cx, y, 0.022, 0.022, EMAS if kini else (90, 90, 100),
                     255 if kini else 200, 0.5, z=0.04,
                     garis=None)
            kv.kotak(cx, y, 0.012, 0.012, KARTU, 255, 0.5, z=0.035)
        warna = TERANG if kini else (REDUP if not selesai else (150, 170, 150))
        kv.teks(q['t'], (cx + 0.025, y + 0.008), 0.66 if kini else 0.6, EMAS if kini else warna)
        kv.teks(q['d'], (cx + 0.025, y - 0.012), 0.48, warna)
        y -= baris_h

    # Kolom kanan: kartu "sedang dikerjakan" + quest sampingan.
    xk = 0.06
    wk = KANAN - xk
    kini = next((q for q in QUEST_STAGES if q['s'] == qs), None)
    yk = Y_ISI - 0.006
    kv.teks('SEDANG DIKERJAKAN', (xk, yk), 0.60, EMAS)
    hk = 0.15
    kv.kotak(xk + wk / 2, yk - 0.030 - hk / 2, wk, hk, (40, 40, 52), 235, 0.12)
    kv.kotak(xk + 0.004, yk - 0.030 - hk / 2, 0.006, hk - 0.03, EMAS, 255, 0.5, z=0.05)
    if kini:
        kv.teks(kini['t'], (xk + 0.026, yk - 0.065), 1.0, TERANG)
        kv.teks(kini['d'], (xk + 0.026, yk - 0.105), 0.66, REDUP)
    else:
        kv.teks('Semua tugas utama selesai.', (xk + 0.026, yk - 0.08), 0.8, HIJAU)
    langkah = _langkah_tutorial(s)
    if langkah:
        kv.teks('Tutorial: ' + langkah, (xk + 0.026, yk - 0.140), 0.52, (200, 190, 160))

    ys = yk - 0.030 - hk - 0.050
    kv.teks('QUEST SAMPINGAN', (xk, ys), 0.60, EMAS)
    ys -= 0.040
    ada = False
    for qkey, status in (getattr(s, 'side_quests', {}) or {}).items():
        qd = SIDE_QUESTS.get(qkey)
        if not qd:
            continue
        ada = True
        done = status == 'completed'
        kv.kotak(xk + 0.010, ys, 0.018, 0.018, HIJAU if done else EMAS, 255, 0.5, z=0.04)
        kv.teks(qd['name'], (xk + 0.030, ys + 0.007), 0.58, TERANG if not done else REDUP)
        kv.teks(qd['desc'][:70], (xk + 0.030, ys - 0.012), 0.46, REDUP)
        ys -= 0.048
        if ys < Y_KAKI + 0.06:
            break
    if not ada:
        kv.teks('Belum ada. Warga kadang meminta tolong saat diajak bicara.',
                (xk, ys), 0.52, REDUP)


def _langkah_tutorial(s):
    try:
        from .tutorial import current_step
        cur = current_step(s)
        if cur is not None:
            return cur[1].get('label', '')
    except Exception:
        pass
    return ''


# Tata letak simpul peta: (kolom, baris) di kisi. Sambungannya TIDAK
# dipatok di sini -- dibaca dari portal scene saat panel dibuka, jadi peta
# tidak bisa lagi menggambar jalan yang tidak ada (peta ASCII lama
# menyambungkan Kuburan ke Desa; portal sebenarnya Kuburan <-> Lereng).
_TATA_PETA = {
    'swarga':    (1.0, 0.0),
    'naga_cave': (1.0, 1.0),
    'cemetery':  (0.0, 2.0),
    'mountain':  (1.0, 2.0),
    'dungeon':   (2.0, 1.0),
    'farm':      (0.0, 3.0),
    'town':      (1.0, 3.0),
    'lake':      (2.0, 3.0),
    'beach':     (1.0, 4.0),
}
_LABEL_PETA = {
    'farm': 'Kebun', 'town': 'Desa', 'mountain': 'Lereng Gunung',
    'lake': 'Danau', 'cemetery': 'Kuburan Tua', 'beach': 'Pantai Selatan',
    'naga_cave': 'Gua Sang Hyang', 'dungeon': 'Gua Bertingkat',
    'swarga': 'Swarga',
}
# Interior menempel pada scene luarnya.
_INDUK = {'house': 'farm', 'greenhouse': 'farm', 'shop': 'town', 'clinic': 'town',
          'studio': 'town', 'smith': 'town'}


def sambungan_peta():
    """Pasangan scene luar yang tersambung, dari data portal yang hidup."""
    from .scenes import SCENES
    pasang = set()
    for a, sc in SCENES.items():
        for p in getattr(sc, 'portals', []) or []:
            b = p[2]
            if a in _TATA_PETA and b in _TATA_PETA and a != b:
                pasang.add(tuple(sorted((a, b))))
    # Dungeon dimasuki lewat tangga di Gua Sang Hyang, bukan portal.
    pasang.add(('dungeon', 'naga_cave'))
    return sorted(pasang)


def gambar_peta(kv, s):
    from .scenes import SCENES
    cur = s.scene_name
    luar = _INDUK.get(cur, cur)
    # Kanvas: kiri dua pertiga kartu.
    x0, x1 = KIRI + 0.10, 0.17
    y0, y1 = Y_ISI - 0.05, Y_KAKI + 0.09
    def xy(k):
        c, r = _TATA_PETA[k]
        return (x0 + (x1 - x0) * c / 2.0, y0 - (y0 - y1) * r / 4.0)

    import math
    for a, b in sambungan_peta():
        (ax, ay), (bx, by) = xy(a), xy(b)
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy)
        sud = math.degrees(math.atan2(dy, dx))
        aktif = luar in (a, b)
        kv.quad(scale=(L, 0.006), position=((ax + bx) / 2, (ay + by) / 2), z=0.07,
                rotation_z=-sud,
                color=color.rgba(*(EMAS if aktif else (110, 106, 98)), 200 if aktif else 150))

    for k in _TATA_PETA:
        x, y = xy(k)
        label = _LABEL_PETA.get(k, k)
        if k == 'dungeon':
            label += f'  Lv.{getattr(s, "dungeon_level", 0)}'
        sini = k == luar
        w = 0.035 + 0.0105 * len(label)
        kv.kotak(x, y, w, 0.050, (54, 52, 62) if not sini else EMAS,
                 250, 0.5, z=0.05,
                 garis=None)
        if not sini:
            kv.kotak(x, y, w, 0.050, EMAS, 70, 0.5, z=0.045,
                     garis=(255, 255, 255, 255))
        kv.teks(label, (x, y), 0.62, (24, 22, 30) if sini else TERANG, asal=(0, 0))
        if sini:
            kv.teks('KAMU DI SINI', (x, y + 0.045), 0.46, EMAS, asal=(0, 0))

    # Kolom kanan: tempat dalam ruangan + keterangan hari.
    xk = 0.42
    yk = Y_ISI - 0.006
    kv.teks('LOKASI SEKARANG', (xk, yk), 0.60, EMAS)
    disp = getattr(SCENES.get(cur), 'display', None) or cur
    kv.teks(disp, (xk, yk - 0.045), 0.82, TERANG)
    if cur in _INDUK:
        kv.teks('di ' + _LABEL_PETA[_INDUK[cur]], (xk, yk - 0.080), 0.55, REDUP)
    yk -= 0.14
    kv.teks('DI DALAM RUANGAN', (xk, yk), 0.60, EMAS)
    yk -= 0.042
    for k, induk in _INDUK.items():
        nama = getattr(SCENES.get(k), 'display', k)
        sini = k == cur
        kv.kotak(xk + 0.008, yk, 0.012, 0.012, EMAS if sini else (110, 106, 98), 255, 0.5)
        kv.teks(f'{nama}', (xk + 0.024, yk), 0.56, EMAS if sini else TERANG)
        kv.teks(_LABEL_PETA[induk], (KANAN, yk), 0.48, REDUP, asal=(0.5, 0))
        yk -= 0.036
    yk -= 0.03
    kv.teks('HARI INI', (xk, yk), 0.60, EMAS)
    from .panels import UIManager
    kv.teks(f'Hari {s.day_in_season}, {UIManager._season_name(s)} tahun {s.year}',
            (xk, yk - 0.040), 0.58, TERANG)
    kv.teks(f'Cuaca: {s.weather}', (xk, yk - 0.072), 0.56, REDUP)


def gambar_relasi(kv, s):
    from .panels import _ALL_NPCS, ikon_tex
    try:
        from .data import HUMAN_NPCS, SUPERNATURAL_NPCS
    except Exception:
        HUMAN_NPCS, SUPERNATURAL_NPCS = _ALL_NPCS, {}
    hati = s.npc_hearts if isinstance(getattr(s, 'npc_hearts', None), dict) else {}
    tex_hati = ikon_tex('hp', 40)

    def kelompok(judul, ids, x, y, misteri):
        kv.teks(judul, (x, y), 0.60, EMAS)
        y -= 0.048
        lebar = 0.62
        for nid in ids:
            n = int(hati.get(nid, 0) or 0)
            nama = _ALL_NPCS.get(nid, {}).get('name', nid)
            kenal = n > 0 or not misteri
            pt = potret_tex(nid)
            if pt is not None and kenal:
                kv.quad(texture=pt, scale=(0.040, 0.040), position=(x + 0.020, y), z=0.03,
                        color=color.white)
            else:
                kv.kotak(x + 0.020, y, 0.040, 0.040, (60, 58, 70), 255, 0.5, z=0.03)
                kv.teks(nama[:1] if kenal else '?', (x + 0.020, y), 0.7, REDUP, asal=(0, 0))
            kv.teks(nama if kenal else '? ? ?', (x + 0.050, y), 0.60, TERANG if kenal else REDUP)
            # Sepuluh hati kecil: penuh berwarna, sisanya bayangan.
            hx = x + lebar - 10 * 0.021
            for i in range(10):
                kv.quad(texture=tex_hati, scale=(0.017, 0.017),
                        position=(hx + i * 0.021, y), z=0.03,
                        color=color.white if i < n else color.rgba(70, 70, 80, 200))
            y -= 0.046
            if y < Y_KAKI + 0.05:
                break
        return y

    warga = [k for k in HUMAN_NPCS if k in _ALL_NPCS]
    halus = [k for k in SUPERNATURAL_NPCS if k in _ALL_NPCS]
    # Yang paling akrab di atas: itulah yang sedang dipikirkan pemain.
    warga.sort(key=lambda k: (-int(hati.get(k, 0) or 0), _ALL_NPCS[k].get('name', k)))
    halus.sort(key=lambda k: (-int(hati.get(k, 0) or 0), _ALL_NPCS[k].get('name', k)))
    kelompok('WARGA LEMBAH', warga, KIRI, Y_ISI - 0.006, misteri=False)
    kelompok('MAKHLUK HALUS', halus, 0.03, Y_ISI - 0.006, misteri=True)


PANDUAN = (
    ('GERAK & KAMERA', (
        ('WASD', 'jalan'), ('SHIFT', 'lari (pakai energi)'),
        ('Q/E', 'putar kamera 45 derajat'), ('RODA', 'zoom kamera'),
    )),
    ('AKSI', (
        ('SPACE', 'pakai alat'), ('F', 'interaksi: bicara, surat, peti'),
        ('SHIFT+F', 'tangkap makhluk liar'), ('Z', 'serang (butuh pedang)'),
        ('X / C', 'tandai / jalankan antrian'), ('G', 'beri hadiah'),
        ('V', 'makan'), ('T', 'tidur (di rumah)'),
    )),
    ('ALAT', (
        ('1-9', 'pilih alat di roda kiri-atas'), ('R', 'ganti bibit'),
    )),
    ('MENU', (
        ('I', 'inventori'), ('J', 'jurnal tugas'), ('M', 'peta'),
        ('H', 'hubungan warga'), ('P', 'keinginan'), ('N', 'catatan lembah'),
        ('L', 'bangun / beli'), ('F6', 'papan permintaan'),
        ('F4', 'ekosistem & pasar'), ('F7', 'majelis batin'),
        ('TAB', 'ringkasan kebutuhan'), ('F2', 'ubah penampilan'),
        ('F5 / F9', 'simpan / muat'), ('ESC', 'menu jeda'),
    )),
)


def gambar_panduan(kv):
    kolom = [(KIRI, PANDUAN[:3]), (0.05, PANDUAN[3:])]
    for x, grup in kolom:
        y = Y_ISI - 0.006
        for judul, isi in grup:
            kv.teks(judul, (x, y), 0.60, EMAS)
            y -= 0.044
            for tombol, kata in isi:
                kv.tuts(tombol, x, y, tinggi=0.030)
                kv.teks(kata, (x + 0.130, y), 0.60, TERANG)
                y -= 0.035
            y -= 0.016
