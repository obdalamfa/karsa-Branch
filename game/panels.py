"""
panels.py — 2D UI overlay untuk Ursina Engine.
Semua elemen UI menggunakan camera.ui sebagai parent (screen-space).

Layout layar (Ursina screen coords: -0.5 ke 0.5):
  ┌──────────────────────────────────┐
  │ [Tool] [Seed]    [Scene] [Cuaca] │  ← baris atas kiri / kanan
  │ HP ████░░░░░░                    │
  │ EN ████████░░                    │
  │ 💰 Gold: 100G      [Waktu/Hari]  │
  └──────────────────────────────────┘

Dialog box: muncul di bawah tengah.
Panel (inventori, quest, dll.): overlay penuh semi-transparan.
"""
import math
from pathlib import Path as _Path
from PIL import Image as _PILImg
from PIL import ImageDraw as _PILDraw
from PIL import ImageFont as _PILFont
from ursina import (Entity, Text, Texture, color, camera, destroy,
                    Vec2, Vec4, invoke, window)

from .config import SEASON_NAMES, NEED_LOW, NEED_CRITICAL, NEED_MAX

# Thermometer sprite textures (FreeSO up_thermo_slice pattern)
_THERMO_BG_TEX   = None   # up_thermo_slice      (inactive bar)
_THERMO_FILL_TEX = None   # up_thermo_slice_active (filled bar)

def _init_thermo_tex():
    global _THERMO_BG_TEX, _THERMO_FILL_TEX
    _a = _Path(__file__).resolve().parent.parent / 'assets' / 'ui'
    def _lt(name):
        p = _a / f'{name}.png'
        if p.exists():
            try:
                return Texture(_PILImg.open(p))
            except Exception:
                pass
        return None
    _THERMO_BG_TEX   = _lt('up_thermo_slice')
    _THERMO_FILL_TEX = _lt('up_thermo_slice_active')
from .data import CROPS
from .data import (HUMAN_NPCS, SUPERNATURAL_NPCS, ANIMAL_NPCS,
                   QUEST_STAGES, SWORD_RECIPES, PICKAXE_RECIPES, SHOP_ITEMS)

_ALL_NPCS = {**HUMAN_NPCS, **SUPERNATURAL_NPCS, **ANIMAL_NPCS}


# ═══════════════════════════════════════════════════════════════════════════
# IKON HUD — digambar PROSEDURAL dengan PIL, bukan berkas gambar baru
# ═══════════════════════════════════════════════════════════════════════════
#
# Kenapa modul ikon hidup di sini dan bukan di assets/: satu-satunya hal yang
# dibutuhkan HUD adalah bitmap RGBA kecil, dan menggambarnya saat start jauh
# lebih murah daripada menambah 20 berkas PNG yang harus ikut dijaga, dinamai,
# dan diberi lisensi. Ursina menerima PIL.Image langsung sebagai Texture
# (lihat ursina/texture.py) dan membalik gambarnya sendiri, jadi gambar PIL
# yang ditulis normal (y ke bawah) muncul tegak di layar.
#
# Texture BOLEH dibagi-pakai antar Entity — yang tidak boleh dibagi itu Mesh,
# karena Mesh adalah NodePath Panda3D dan sebuah NodePath cuma punya satu
# parent. Ikon di bawah sengaja di-cache; jangan meniru pola ini untuk mesh.
#
# Semua koordinat gambar dinormalkan 0..1 dengan (0,0) di KIRI-ATAS, jadi
# ukuran piksel akhirnya bisa diubah tanpa menyentuh satu pun bentuk.

_SS       = 4           # supersample sebelum diperkecil LANCZOS (anti-alias)
_IKON_CACHE: dict = {}

# Palet ikon = palet model 3D-nya (game/tool_models.py). Ikon cangkul dan
# cangkul yang dipegang karakter harus terbaca sebagai BENDA YANG SAMA;
# kalau warnanya beda, ikon jadi lambang, bukan gambar barangnya.
_I_GELAP  = ( 20,  28,  34, 255)
_I_KAYU   = (156, 116,  74, 255)
_I_KAYUT  = (110,  80,  50, 255)
_I_BAMBU  = (200, 178, 120, 255)
_I_BESI   = (168, 176, 186, 255)
_I_BESIT  = (104, 112, 122, 255)
_I_SENG   = (152, 162, 160, 255)
_I_ANYAM  = (198, 164, 106, 255)
_I_DAUN   = (114, 166,  88, 255)
_I_DAUNT  = ( 78, 122,  62, 255)
_I_AIR    = ( 96, 172, 214, 255)
_I_EMAS   = (232, 196,  96, 255)
_I_MERAH  = (198,  88,  80, 255)
_I_KRIM   = (240, 232, 206, 255)
_I_KAIN   = (150, 114,  92, 255)
_I_PUTIH  = (250, 250, 246, 255)


def _pena(n):
    img = _PILImg.new('RGBA', (n, n), (0, 0, 0, 0))
    return img, _PILDraw.Draw(img)


def _grs(d, n, p0, p1, w, isi, garis=_I_GELAP):
    """Batang tebal dari p0 ke p1. Garis gelap digambar lebih lebar DULU,
    lalu isinya menimpa — itu cara termurah mendapat outline yang rapi tanpa
    menghitung poligon offset."""
    a = (p0[0] * n, p0[1] * n)
    b = (p1[0] * n, p1[1] * n)
    if garis:
        d.line([a, b], fill=garis, width=max(1, int((w + 0.055) * n)))
    d.line([a, b], fill=isi, width=max(1, int(w * n)))


def _plg(d, n, pts, isi, garis=_I_GELAP, tebal=0.05):
    P = [(x * n, y * n) for x, y in pts]
    if garis and tebal:
        d.line(P + [P[0]], fill=garis, width=max(1, int(tebal * n)), joint='curve')
    d.polygon(P, fill=isi)
    if garis and tebal:
        d.line(P + [P[0]], fill=garis,
               width=max(1, int(tebal * n * 0.5)), joint='curve')


def _lkr(d, n, cx, cy, r, isi, garis=_I_GELAP, tebal=0.05):
    box = [(cx - r) * n, (cy - r) * n, (cx + r) * n, (cy + r) * n]
    if garis:
        d.ellipse(box, fill=isi, outline=garis, width=max(1, int(tebal * n)))
    else:
        d.ellipse(box, fill=isi)


def _bintang(cx, cy, r1, r2, sudut=5):
    pts = []
    for i in range(sudut * 2):
        r = r1 if i % 2 == 0 else r2
        a = -math.pi / 2 + i * math.pi / sudut
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


def _tetes(cx, cy, r, tinggi):
    """Tetesan air sebagai SATU poligon, bukan lingkaran + segitiga.
    Gabungan dua bentuk tidak bisa dikelilingi satu outline — dan tanpa
    outline ikon hilang di atas latar terang."""
    pts = []
    for i in range(33):
        a = math.radians(-40 + i * (260.0 / 32.0))
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    pts.append((cx, cy - tinggi))
    return pts


def _hati(cx, cy, s):
    pts = []
    for i in range(44):
        t = i / 44.0 * 2 * math.pi
        x = 16 * math.sin(t) ** 3
        y = (13 * math.cos(t) - 5 * math.cos(2 * t)
             - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((cx + x / 17.0 * s, cy - y / 17.0 * s))
    return pts


def _orang(d, n, cx, cy, s, isi):
    """Siluet kepala + bahu. Dipakai dua kali untuk ikon Sosial."""
    _lkr(d, n, cx, cy - 0.20 * s, 0.15 * s, isi)
    _plg(d, n, [(cx - 0.26 * s, cy + 0.42 * s), (cx - 0.24 * s, cy + 0.06 * s),
                (cx - 0.12 * s, cy - 0.04 * s), (cx + 0.12 * s, cy - 0.04 * s),
                (cx + 0.24 * s, cy + 0.06 * s), (cx + 0.26 * s, cy + 0.42 * s)],
         isi)


# ─── ALAT ────────────────────────────────────────────────────────────────
def _ika_cangkul(d, n):
    _grs(d, n, (0.78, 0.16), (0.42, 0.66), 0.10, _I_KAYU)
    _plg(d, n, [(0.48, 0.56), (0.16, 0.68), (0.12, 0.86), (0.50, 0.72)], _I_BESI)


def _ika_penyiram(d, n):
    _plg(d, n, [(0.34, 0.40), (0.78, 0.40), (0.72, 0.86), (0.40, 0.86)], _I_SENG)
    _grs(d, n, (0.36, 0.48), (0.12, 0.34), 0.09, _I_SENG)
    _plg(d, n, [(0.16, 0.22), (0.04, 0.28), (0.08, 0.42), (0.20, 0.36)], _I_SENG)
    _grs(d, n, (0.46, 0.40), (0.56, 0.24), 0.06, _I_BESIT)
    _grs(d, n, (0.56, 0.24), (0.70, 0.40), 0.06, _I_BESIT)
    _lkr(d, n, 0.12, 0.60, 0.055, _I_AIR)
    _lkr(d, n, 0.24, 0.74, 0.045, _I_AIR)


def _ika_benih(d, n):
    _plg(d, n, [(0.16, 0.90), (0.84, 0.90), (0.74, 0.74), (0.26, 0.74)], _I_KAYUT)
    _grs(d, n, (0.50, 0.80), (0.50, 0.40), 0.07, _I_DAUNT)
    _plg(d, n, [(0.50, 0.52), (0.24, 0.44), (0.26, 0.26), (0.48, 0.38)], _I_DAUN)
    _plg(d, n, [(0.50, 0.46), (0.76, 0.36), (0.78, 0.18), (0.52, 0.32)], _I_DAUN)


def _ika_bakul(d, n):
    _lkr(d, n, 0.36, 0.40, 0.13, _I_MERAH)
    _lkr(d, n, 0.62, 0.42, 0.11, _I_DAUN)
    _plg(d, n, [(0.12, 0.48), (0.88, 0.48), (0.74, 0.90), (0.26, 0.90)], _I_ANYAM)
    w = max(1, int(0.035 * n))
    for fy in (0.60, 0.72):
        d.line([(0.16 * n, fy * n), (0.84 * n, fy * n)], fill=_I_KAYUT, width=w)


def _ika_kapak(d, n):
    # Mata kapak WAJIB punya tepi atas dan bawah yang cekung; wedge cembung
    # penuh terbaca sebagai palu atau sekop pada 25 piksel — sudah diuji.
    _grs(d, n, (0.28, 0.96), (0.66, 0.24), 0.085, _I_KAYU)
    _plg(d, n, [(0.78, 0.34), (0.62, 0.20), (0.66, 0.02), (0.86, 0.02),
                (0.96, 0.16), (0.92, 0.34), (0.86, 0.44)], _I_BESI)


def _ika_kado(d, n):
    _plg(d, n, [(0.14, 0.44), (0.86, 0.44), (0.86, 0.88), (0.14, 0.88)], _I_MERAH)
    _plg(d, n, [(0.44, 0.44), (0.58, 0.44), (0.58, 0.88), (0.44, 0.88)],
         _I_EMAS, tebal=0.03)
    _plg(d, n, [(0.14, 0.56), (0.86, 0.56), (0.86, 0.66), (0.14, 0.66)],
         _I_EMAS, tebal=0.03)
    _plg(d, n, [(0.51, 0.42), (0.26, 0.22), (0.20, 0.36), (0.44, 0.44)], _I_EMAS)
    _plg(d, n, [(0.51, 0.42), (0.76, 0.22), (0.82, 0.36), (0.58, 0.44)], _I_EMAS)


def _ika_beliung(d, n):
    _grs(d, n, (0.50, 0.92), (0.50, 0.28), 0.09, _I_KAYU)
    _plg(d, n, [(0.06, 0.42), (0.30, 0.20), (0.70, 0.20), (0.94, 0.42),
                (0.68, 0.32), (0.32, 0.32)], _I_BESI)


def _ika_pedang(d, n):
    _plg(d, n, [(0.50, 0.06), (0.60, 0.20), (0.60, 0.60), (0.40, 0.60),
                (0.40, 0.20)], _I_BESI)
    _plg(d, n, [(0.24, 0.60), (0.76, 0.60), (0.76, 0.70), (0.24, 0.70)], _I_EMAS)
    _grs(d, n, (0.50, 0.70), (0.50, 0.88), 0.11, _I_KAYUT)
    _lkr(d, n, 0.50, 0.92, 0.08, _I_EMAS)


def _ika_pancing(d, n):
    _grs(d, n, (0.12, 0.90), (0.80, 0.14), 0.07, _I_BAMBU)
    d.line([(0.80 * n, 0.16 * n), (0.86 * n, 0.56 * n)],
           fill=_I_KRIM, width=max(1, int(0.030 * n)))
    _lkr(d, n, 0.86, 0.62, 0.09, _I_MERAH)
    _lkr(d, n, 0.34, 0.62, 0.055, _I_AIR)


def _ika_bawaan(d, n):
    _lkr(d, n, 0.50, 0.50, 0.34, _I_BESIT)


# ─── MOTIF ───────────────────────────────────────────────────────────────
def _ikm_mood(d, n):
    _lkr(d, n, 0.50, 0.50, 0.40, _I_EMAS)
    _lkr(d, n, 0.37, 0.42, 0.065, _I_GELAP, None)
    _lkr(d, n, 0.63, 0.42, 0.065, _I_GELAP, None)
    d.arc([0.28 * n, 0.40 * n, 0.72 * n, 0.76 * n], 20, 160,
          fill=_I_GELAP, width=max(1, int(0.075 * n)))


def _ikm_lapar(d, n):
    _grs(d, n, (0.30, 0.34), (0.30, 0.92), 0.10, _I_KRIM)
    for fx in (0.19, 0.30, 0.41):
        _grs(d, n, (fx, 0.10), (fx, 0.34), 0.055, _I_KRIM)
    _plg(d, n, [(0.62, 0.10), (0.78, 0.20), (0.78, 0.54), (0.62, 0.54)], _I_KRIM)
    _grs(d, n, (0.70, 0.52), (0.70, 0.92), 0.09, _I_KRIM)


def _ikm_nyaman(d, n):
    _plg(d, n, [(0.20, 0.22), (0.80, 0.22), (0.80, 0.58), (0.20, 0.58)], _I_KAIN)
    _plg(d, n, [(0.10, 0.54), (0.90, 0.54), (0.90, 0.70), (0.10, 0.70)], _I_KAYU)
    _plg(d, n, [(0.06, 0.42), (0.20, 0.42), (0.20, 0.70), (0.06, 0.70)], _I_KAYUT)
    _plg(d, n, [(0.80, 0.42), (0.94, 0.42), (0.94, 0.70), (0.80, 0.70)], _I_KAYUT)
    _grs(d, n, (0.20, 0.70), (0.20, 0.90), 0.07, _I_KAYUT)
    _grs(d, n, (0.80, 0.70), (0.80, 0.90), 0.07, _I_KAYUT)


def _ikm_higiene(d, n):
    _plg(d, n, _tetes(0.50, 0.62, 0.30, 0.56), _I_AIR)


def _ikm_kandung(d, n):
    _plg(d, n, [(0.12, 0.16), (0.36, 0.16), (0.36, 0.54), (0.12, 0.54)], _I_KRIM)
    _plg(d, n, [(0.34, 0.36), (0.88, 0.36), (0.76, 0.64), (0.44, 0.64)], _I_KRIM)
    _plg(d, n, [(0.46, 0.62), (0.74, 0.62), (0.78, 0.90), (0.42, 0.90)], _I_KRIM)


def _ikm_energi(d, n):
    _plg(d, n, [(0.60, 0.06), (0.22, 0.54), (0.44, 0.54), (0.36, 0.94),
                (0.78, 0.44), (0.54, 0.44)], _I_EMAS)


def _ikm_senang(d, n):
    _plg(d, n, _bintang(0.50, 0.52, 0.44, 0.19), _I_EMAS)


def _ikm_sosial(d, n):
    _orang(d, n, 0.66, 0.52, 0.86, _I_BAMBU)
    _orang(d, n, 0.36, 0.58, 1.00, _I_AIR)


def _ikm_ruang(d, n):
    _plg(d, n, [(0.08, 0.18), (0.92, 0.18), (0.92, 0.82), (0.08, 0.82)], _I_KAYU)
    _plg(d, n, [(0.20, 0.30), (0.80, 0.30), (0.80, 0.70), (0.20, 0.70)],
         _I_KRIM, tebal=0.035)
    _lkr(d, n, 0.66, 0.41, 0.075, _I_EMAS, None)
    _plg(d, n, [(0.22, 0.68), (0.44, 0.40), (0.64, 0.68)], _I_DAUNT, None)


def _ik_hp(d, n):
    _plg(d, n, _hati(0.50, 0.52, 0.44), _I_MERAH)


_GAMBAR_IKON = {
    'cangkul': _ika_cangkul, 'penyiram': _ika_penyiram, 'benih': _ika_benih,
    'bakul': _ika_bakul, 'kapak': _ika_kapak, 'kado': _ika_kado,
    'beliung': _ika_beliung, 'pedang': _ika_pedang, 'pancing': _ika_pancing,
    'bawaan': _ika_bawaan,
    'mood': _ikm_mood, 'lapar': _ikm_lapar, 'nyaman': _ikm_nyaman,
    'higiene': _ikm_higiene, 'kandung': _ikm_kandung, 'energi': _ikm_energi,
    'senang': _ikm_senang, 'sosial': _ikm_sosial, 'ruang': _ikm_ruang,
    'hp': _ik_hp,
}


def _font_ikon(px: int):
    p = _Path(__file__).resolve().parent.parent / 'assets' / 'fonts' / _FONT_NAME
    try:
        return _PILFont.truetype(str(p), px)
    except Exception:
        try:
            return _PILFont.load_default()
        except Exception:
            return None


def _chip_angka(d, n, teks: str):
    """Nomor pintasan di sudut kiri-bawah petak alat.

    Ini satu-satunya HURUF yang tersisa di blok alat, dan ia ada supaya
    pemain tahu petaknya bisa dipilih dengan angka tanpa ada satu baris
    manual pun di layar. Digambar di atas kepingan gelap karena angka krem
    telanjang hilang di atas bilah cangkul yang juga terang."""
    r = 0.15
    cx, cy = 0.17, 0.83
    d.ellipse([(cx - r) * n, (cy - r) * n, (cx + r) * n, (cy + r) * n],
              fill=(14, 20, 26, 225))
    f = _font_ikon(max(6, int(0.26 * n)))
    if f is None:
        return
    try:
        kotak = d.textbbox((0, 0), teks, font=f)
    except Exception:
        return
    w = kotak[2] - kotak[0]
    h = kotak[3] - kotak[1]
    d.text((cx * n - w / 2 - kotak[0], cy * n - h / 2 - kotak[1]),
           teks, font=f, fill=_I_KRIM)


def ikon_tex(nama: str, px: int = 64, angka: str = ''):
    """Texture ikon, dibuat sekali lalu dipakai ulang."""
    kunci = (nama, px, angka)
    if kunci in _IKON_CACHE:
        return _IKON_CACHE[kunci]
    fn = _GAMBAR_IKON.get(nama)
    tex = None
    if fn is not None:
        try:
            n = px * _SS
            img, d = _pena(n)
            fn(d, n)
            if angka:
                _chip_angka(d, n, angka)
            img = img.resize((px, px), _PILImg.LANCZOS)
            tex = Texture(img)
            tex.filtering = 'bilinear'
        except Exception:
            tex = None
    _IKON_CACHE[kunci] = tex
    return tex


def petak_tex(px: int = 64):
    """Petak bersudut tumpul, PUTIH, supaya bisa diwarnai lewat `color`
    entity — satu tekstur melayani petak terpilih maupun yang redup."""
    kunci = ('_petak', px, '')
    if kunci in _IKON_CACHE:
        return _IKON_CACHE[kunci]
    tex = None
    try:
        n = px * _SS
        img, d = _pena(n)
        r = int(0.18 * n)
        d.rounded_rectangle([int(0.03 * n), int(0.03 * n),
                             int(0.97 * n), int(0.97 * n)],
                            radius=r, fill=(255, 255, 255, 175),
                            outline=(255, 255, 255, 255),
                            width=max(2, int(0.045 * n)))
        img = img.resize((px, px), _PILImg.LANCZOS)
        tex = Texture(img)
        tex.filtering = 'bilinear'
    except Exception:
        tex = None
    _IKON_CACHE[kunci] = tex
    return tex


def tuts_tex(label: str, tinggi: int = 30):
    """Kepingan tombol keyboard (SPACE, E, TAB) sebagai gambar.

    Return (Texture, rasio_lebar_per_tinggi) supaya pemanggil bisa membuat
    quad dengan proporsi yang benar; label 'SPACE' lima kali lebih lebar
    daripada 'E' dan memaksanya ke kotak persegi membuat hurufnya gepeng."""
    kunci = ('_tuts', tinggi, label)
    if kunci in _IKON_CACHE:
        return _IKON_CACHE[kunci]
    hasil = (None, 1.0)
    try:
        h = tinggi * _SS
        f = _font_ikon(int(h * 0.52))
        tmp = _PILDraw.Draw(_PILImg.new('RGBA', (8, 8)))
        kotak = tmp.textbbox((0, 0), label, font=f)
        w_teks = kotak[2] - kotak[0]
        w = int(max(h, w_teks + h * 0.60))
        img = _PILImg.new('RGBA', (w, h), (0, 0, 0, 0))
        d = _PILDraw.Draw(img)
        d.rounded_rectangle([2, 2, w - 3, h - 3], radius=int(h * 0.26),
                            fill=(18, 26, 32, 232),
                            outline=(214, 228, 240, 245),
                            width=max(2, int(h * 0.055)))
        d.text(((w - w_teks) / 2 - kotak[0],
                (h - (kotak[3] - kotak[1])) / 2 - kotak[1]),
               label, font=f, fill=(238, 246, 252, 255))
        img = img.resize((max(1, w // _SS), tinggi), _PILImg.LANCZOS)
        tex = Texture(img)
        tex.filtering = 'bilinear'
        hasil = (tex, img.width / float(img.height))
    except Exception:
        hasil = (None, 1.0)
    _IKON_CACHE[kunci] = hasil
    return hasil


def _ui(model='quad', **kw):
    # Tidak pakai shader agar color property bekerja di camera.ui space.
    # transparent=True wajib agar alpha channel diterapkan oleh renderer.
    kw.setdefault('transparent', True)
    return Entity(parent=camera.ui, model=model, **kw)


_FONT_NAME = 'Montserrat-Bold.ttf'  # Ursina cari via glob(**) di asset_folder

def _txt(text='', pos=(0, 0), scale=1.0, col=color.white, **kw):
    kw.setdefault('font', _FONT_NAME)
    return Text(text, parent=camera.ui, position=pos,
                scale=scale * 1.2, color=col, **kw)


class UIManager:
    """Mengelola semua HUD dan panel."""

    def __init__(self, state):
        self.state       = state
        self.mode        = 'hud'    # 'hud' | 'dialog' | 'panel'
        self._panel_name = None
        self._dialog_lines: list = []
        self._dialog_idx  = 0
        self._dialog_npc  = None
        self._dlg_choices = []
        self._dlg_choice_idx = 0
        self._dlg_choices_active = False

        self._flash_ent = None
        self._flash_t   = 0.0

        _init_thermo_tex()
        self._build_hud()
        self._build_dialog_box()
        self._build_panel_bg()
        self._build_pie_menu()

        # Previous motives cache for Arrow indicators
        self._prev_hunger = None
        self._prev_social = None
        self._prev_fun = None
        self._prev_energy = None

    # ─── PUBLIC: UPDATE ──────────────────────────────────
    def update(self, state, dt: float = 0):
        self.state = state
        if self.mode == 'hud':
            # Petunjuk tombol punya UMUR. Setelah 30 detik ia padam sendiri;
            # pemain yang sudah tahu SPACE itu 'pakai' tidak perlu diberi
            # tahu lagi setiap detik sisa permainannya.
            if self._hint_umur < self._HINT_PADAM:
                self._hint_umur += max(0.0, dt)
            self._refresh_hud()
            self._update_motive_panel()
            self._update_action_readout()

        # Flash message timer
        if self._flash_t > 0:
            self._flash_t -= dt
            if self._flash_t <= 0 and self._flash_ent:
                self._flash_ent.enabled = False
                if hasattr(self, '_flash_bg'):
                    self._flash_bg.enabled = False

    # Urutan persis config.TOOLS dan tool_models.KIND_BY_TOOL_INDEX. Sembilan,
    # bukan delapan: daftar lama berhenti di 'Pedang' sehingga alat ke-9
    # (Pancing) selalu tampil dengan nama alat ke-8.
    _KIND_ALAT = ('cangkul', 'penyiram', 'benih', 'bakul', 'kapak',
                  'kado', 'beliung', 'pedang', 'pancing')

    # Tiga pintasan, bukan tujuh. Sisanya hidup di F1, dan roda alat di
    # kiri-atas sudah membawa nomornya sendiri di tiap petak.
    _PINTASAN = (('SPACE', 'Pakai'), ('E', 'Aksi'), ('TAB', 'Motif'))
    _HINT_PADAM = 30.0          # detik sebelum petunjuk memudar sendiri

    # ─── PUBLIC: HUD ─────────────────────────────────────
    def _build_hud(self):
        """HUD tipis yang MENEMPEL di tepi layar (patokan: AWL).

        Bentuk lama memakan seperempat layar dengan empat panel pejal: kotak
        alat 390x280 di kiri-atas, kotak waktu 660x280 di kanan-atas, panel
        SUASANA HATI 285x400 yang mengambang jauh dari tepi, dan pita tombol
        SELEBAR LAYAR di bawah. Diukur dari tangkapan layar 1920x1080: ~27%
        layar tertutup HUD.

        Patokannya justru kebalikannya — bilah stamina TIPIS menempel di
        kiri-atas, tanggal/musim/jam kecil di kanan-atas, petunjuk tombol
        kecil di kanan-bawah, dan latar panel nyaris tidak ada: teks duduk
        langsung di atas dunia dengan alas gelap setipis mungkin.

        Tiga aturan tata letak, dan tidak ada yang keempat:

        1. Semua dijangkar ke SUDUT lewat satu margin yang sama (`M`), jadi
           tidak ada blok yang "hampir" di tepi.
        2. Satu baris menampung sebanyak mungkin. Waktu/tanggal/cuaca dulu
           empat baris bertumpuk; sekarang satu baris rata kanan yang
           lebarnya dihitung dari teksnya sendiri (`_tata_kanan_atas`).
        3. Alas gelap dipas ke isinya tiap kali teksnya berubah, bukan
           dipatok ke kotak tetap. Pita bawah selebar layar mati karena
           alasan ini: ia dibuat selebar layar supaya prompt sepanjang apa
           pun tetap berlatar — padahal yang perlu melar cuma alasnya.

        Informasi tidak dibuang, cuma dikecilkan dan dipindahkan. Delapan
        motif tetap tampil lengkap di sudut kiri-bawah, dan TAB
        menyembunyikan/menampilkannya kalau pemain mau layar bersih.

        ── Putaran ALAT: gambar menggantikan kata ────────────────────────

        Tiga keluhan yang diperbaiki di sini, semuanya soal yang sama:
        layar ini menulis apa yang seharusnya ia GAMBARKAN.

        1. Sembilan baris motif berlabel KATA tanpa satu pun ikon. Sekarang
           tiap baris dipimpin ikon yang menggambarkan kebutuhannya —
           garpu-pisau, tetesan air, petir, bintang — dan katanya hilang.
           Panel menyusut dari 260 px jadi 173 px lebar sekaligus.
        2. Nama alat ditulis sebagai teks sementara tangan karakter memegang
           cangkul sepanjang permainan. Sekarang alatnya diwakili RODA
           sembilan petak berikon di kiri-atas, yang terpilih membesar dan
           menyala, dan cangkulnya cuma keluar ke tangan saat dipakai
           (lihat Player3D.refresh_held_tool).
        3. Angka '100/100' menempel di ujung bilah sehingga terbaca
           menindihnya. Jaraknya dinaikkan 0.010 -> 0.020 dan ukurannya
           diturunkan, dan tiap bilah kini dipimpin ikonnya sendiri (hati,
           petir) supaya bisa dibedakan tanpa membaca angkanya sama sekali.

        Dan yang keempat: baris motif terbawah dulu menempel ke tepi bawah
        layar sehingga terbaca terpotong. Bantalan bawah panel 0.002 ->
        0.010, jadi ada 28 px di bawah bilah terakhir.
        """
        TIME_C   = color.rgb(255, 255, 255)
        GOLD_C   = color.rgb(255, 215,  60)

        # ── Tepi layar yang sebenarnya ──
        # camera.ui membentang -aspect/2..+aspect/2 mendatar, BUKAN -0.5..0.5.
        # Angka mati 0.70 lahir dari menebak layar 16:9 lalu menjangkar teks di
        # KIRI-nya; tiap teks lalu tumbuh ke kanan sampai lewat tepi 0.889.
        # Itu sebabnya jam, tanggal, dan nama scene terpotong di screenshot.
        # Yang duduk di kanan dijangkar di KANAN (origin x = +0.5) supaya
        # tumbuhnya ke dalam layar, berapa pun panjang teksnya.
        self._edge_x = window.aspect_ratio / 2
        M = 0.013                       # jarak ke tepi: 14 px di layar 1080
        self._M   = M
        self._X_L = X_L = -self._edge_x + M
        self._X_R = X_R =  self._edge_x - M
        self._Y_T = Y_T =  0.5 - M
        self._Y_B = Y_B = -0.5 + M
        self._GAP = 0.014               # jarak antar potongan dalam satu baris
        self._RA  = (0.5, 0.0)          # rata kanan, jangkar tengah menegak

        # Tinggi satu baris teks di ruang camera.ui = Text.size * skala entity.
        # Dipakai untuk menumpuk baris tanpa menebak; skala di sini adalah
        # argumen `_txt`, yang dikalikan 1.2 di dalamnya.
        def _tinggi(s):
            return 0.025 * s * 1.2

        S_JAM   = 0.92                  # jam: satu-satunya teks yang boleh besar
        S_KECIL = 0.66
        h_jam   = _tinggi(S_JAM)
        h_kecil = _tinggi(S_KECIL)

        # ── Kanan Atas: satu baris jam/cuaca/tanggal + satu baris tipis ──
        # Empat baris jadi dua. Posisi mendatar dihitung ulang dari lebar
        # teksnya di `_tata_kanan_atas`, jadi teks sepanjang apa pun tetap
        # rata kanan dan tidak pernah menabrak yang di sebelahnya.
        r1 = Y_T - h_jam / 2
        r2 = r1 - h_jam / 2 - 0.004 - h_kecil / 2
        self._ROW1_Y, self._ROW2_Y = r1, r2
        self._time_txt    = _txt('06:00',         pos=(X_R, r1), scale=S_JAM,   col=TIME_C, origin=self._RA)
        self._weather_txt = _txt('^ Cerah',       pos=(X_R, r1), scale=S_KECIL, col=color.rgb(255, 240, 130), origin=self._RA)
        self._date_txt    = _txt('Hari 1 | Semi', pos=(X_R, r1), scale=S_KECIL, col=color.rgb(180, 205, 255), origin=self._RA)
        self._gold_txt    = _txt('§ 0G',          pos=(X_R, r2), scale=S_KECIL, col=GOLD_C, origin=self._RA)
        self._scene_txt   = _txt('> Kebun',       pos=(X_R, r2), scale=S_KECIL, col=color.rgb(150, 250, 170), origin=self._RA)

        # ── Kiri Atas: dua bilah stamina BERIKON + roda alat ──
        # Patokan menaruh satu bilah setebal 16 px menempel di sudut. Dua
        # bilah kita 15 px, bertumpuk, masing-masing dipimpin ikonnya sendiri
        # (hati untuk HP, petir untuk energi) supaya bisa dibedakan tanpa
        # membaca satu huruf pun, dan angkanya duduk 22 px di kanan ujung
        # bilah — bukan 11 px seperti dulu, di mana '100/100' terbaca
        # menindih ujung bilahnya.
        S_ANGKA  = 0.50
        LA       = (-0.5, 0.0)          # rata kiri, jangkar tengah menegak
        self._LA = LA

        self._IK_BAR     = IK_BAR = 0.017
        self._BAR_W      = 0.185
        self._BAR_H      = 0.014
        self._BAR_GAP    = 0.006        # jarak ikon -> bilah
        self._NUM_GAP    = 0.020        # jarak ujung bilah -> angka
        self._BAR_X_LEFT = X_L + IK_BAR + self._BAR_GAP
        BW, BH = self._BAR_W, self._BAR_H
        BX = self._BAR_X_LEFT

        hy = Y_T - 0.004 - BH / 2
        ey = hy - BH - 0.006
        self._hy, self._ey = hy, ey

        self._hp_ikon = _ui(scale=(IK_BAR, IK_BAR), z=0.02,
                            position=(X_L + IK_BAR / 2, hy),
                            texture=ikon_tex('hp', 40), color=color.white)
        self._en_ikon = _ui(scale=(IK_BAR, IK_BAR), z=0.02,
                            position=(X_L + IK_BAR / 2, ey),
                            texture=ikon_tex('energi', 40), color=color.white)

        # Alas bilah: tanpa ini bilah yang menyusut jadi tidak terbaca sebagai
        # "sisa dari sekian", cuma sebagai garis pendek yang berubah panjang.
        trek = color.rgb(18, 26, 30, 200)
        self._hp_trek = _ui(scale=(BW, BH), z=0.06,
                            position=(BX + BW / 2, hy), color=trek)
        self._en_trek = _ui(scale=(BW, BH), z=0.06,
                            position=(BX + BW / 2, ey), color=trek)
        self._hp_bar = _ui(scale=(BW, BH), z=0.03,
                           position=(BX + BW / 2, hy),
                           color=color.rgb(55, 210, 80))
        self._en_bar = _ui(scale=(BW, BH), z=0.03,
                           position=(BX + BW / 2, ey),
                           color=color.rgb(55, 205, 75))
        self._hp_val = _txt('', pos=(BX + BW + self._NUM_GAP, hy),
                            scale=S_ANGKA, col=color.rgb(214, 228, 236), origin=LA)
        self._en_val = _txt('', pos=(BX + BW + self._NUM_GAP, ey),
                            scale=S_ANGKA, col=color.rgb(214, 228, 236), origin=LA)

        # ── Roda alat: sembilan petak berikon, ala GTA/AWL ──
        # Yang terpilih membesar dan menyala penuh; sisanya diredupkan lewat
        # tint entity, bukan lewat tekstur kedua. Nomor pintasan dipanggang
        # ke dalam gambar ikonnya, jadi tidak ada satu baris teks
        # "[1-8] pilih alat" pun yang perlu berdiri di layar.
        # Petak terpilih dibesarkan PERSIS sebesar dua kali jaraknya ke
        # tetangga (0.033 + 2*0.005 = 0.043), jadi ia menyentuh tetangganya
        # tanpa pernah menindihnya, berapa pun petak yang sedang dipilih.
        self._SLOT   = SLOT   = 0.033
        self._SLOT_S = SLOT_S = 0.043
        self._SGAP   = SGAP   = 0.005
        self._RODA_W = len(self._KIND_ALAT) * SLOT + (len(self._KIND_ALAT) - 1) * SGAP
        y_roda = ey - BH / 2 - 0.009 - SLOT_S / 2
        self._y_roda = y_roda

        _petak = petak_tex(64)
        self._alat_petak, self._alat_ikon = [], []
        for i, kind in enumerate(self._KIND_ALAT):
            cx = X_L + SLOT / 2 + i * (SLOT + SGAP)
            self._alat_petak.append(
                _ui(scale=(SLOT, SLOT), z=0.09, position=(cx, y_roda),
                    texture=_petak, color=color.rgb(26, 34, 40, 200)))
            self._alat_ikon.append(
                _ui(scale=(SLOT * 0.80, SLOT * 0.80), z=0.04,
                    position=(cx, y_roda),
                    texture=ikon_tex(kind, 56, str(i + 1)),
                    color=color.rgb(182, 192, 200)))

        # Nama alat: satu kata, DI BAWAH petaknya, persis seperti 'Clippers'
        # di patokan. Ia menamai gambar, bukan menggantikannya.
        S_NAMA = 0.60
        h_nama = _tinggi(S_NAMA)
        self._h_nama = h_nama
        y_nama = y_roda - SLOT_S / 2 - 0.004 - h_nama / 2
        self._tool_name = _txt('Cangkul', pos=(X_L, y_nama), scale=S_NAMA,
                               col=color.rgb(255, 238, 154), origin=(0, 0))

        y_benih = y_nama - h_nama / 2 - 0.004 - h_kecil / 2
        self._seed_txt  = _txt('', pos=(X_L, y_benih),
                               scale=S_KECIL, col=color.rgb(155, 255, 155), origin=LA)

        # Buff dan antrian aksi: dua baris yang HAMPIR SELALU kosong, jadi
        # ongkos layarnya nol kecuali saat memang ada yang perlu dibaca.
        self._buff_txt  = _txt('', pos=(X_L, y_benih - h_kecil - 0.003),
                               scale=S_KECIL, col=color.rgb(120, 255, 180), origin=LA)
        self._queue_txt = _txt('', pos=(X_L, y_benih - h_kecil * 2 - 0.006),
                               scale=S_KECIL, col=color.rgb(255, 210, 80), origin=LA)

        # ── Kiri Bawah: ringkasan motif, menempel di SUDUT ──
        # Delapan motif ditumpuk vertikal dengan Suasana di puncaknya. Tanpa
        # ini seluruh mesin motif tidak terlihat oleh pemain, dan need yang
        # tak terlihat sama saja dengan tidak ada.
        #
        # Kolom NAMA dibuang seluruhnya dan diganti kolom IKON selebar 20 px:
        # blok yang tadinya 260 px lebar (kolom 'Kamar Kecil' menentukan
        # lebarnya) jadi 173 px, dan tidak ada satu kata pun tersisa di sana.
        from .motives import MOTIVES
        self._motive_keys = MOTIVES
        self._IK_N     = IK_N = 0.0185   # ikon motif, satu per baris
        self._NBAR_W   = 0.115
        self._NBAR_H   = 0.0125
        self._NROW     = 0.0215
        self._NGAP     = 0.006           # jarak ikon -> bilah
        NBH            = self._NBAR_H

        n = len(self._motive_keys)
        # Bantalan bawah 0.010, bukan 0.002. Dengan 0.002 baris 'Ruangan'
        # praktis menyentuh tepi alas dan terbaca sebagai baris yang
        # TERPOTONG, bukan baris terakhir — keluhan yang diukur, bukan selera.
        PAD     = 0.010
        y_need0 = Y_B + NBH / 2 + PAD            # motif terakhir, paling bawah
        y_mood  = y_need0 + (n - 1) * self._NROW + 0.028
        MOOD_H  = 0.017

        # Kata-katanya HILANG; yang tersisa gambar + bilah. Sembilan nama
        # motif berjejer tegak adalah blok teks terbesar di layar, dan
        # patokan (AWL) tidak menuliskan satu pun namanya. Entity label tetap
        # ada sebagai None supaya pemeriksa regresi yang mencarinya lewat
        # nama atribut tidak meledak — ia melewati yang None.
        self._mood_lbl = None
        self._need_lbl_ents = []
        self._NLBL_W = IK_N + self._NGAP
        self._NBAR_X = X_L + self._NLBL_W

        self._mood_ikon = _ui(scale=(IK_N, IK_N), z=0.02,
                              position=(X_L + IK_N / 2, y_mood),
                              texture=ikon_tex('mood', 40), color=color.white)
        self._need_ikon_ents = [
            _ui(scale=(IK_N, IK_N), z=0.02,
                position=(X_L + IK_N / 2, y_need0 + (n - 1 - i) * self._NROW),
                texture=ikon_tex(key, 40), color=color.white)
            for i, key in enumerate(self._motive_keys)]

        # Alas panel: tipis, bukan kotak 93% opak lagi. Tugasnya cuma menjamin
        # ikon dan bilah tetap terbaca di atas lantai terang; selebihnya biar
        # dunia yang kelihatan.
        panel_top = y_mood + MOOD_H / 2 + PAD
        panel_bot = y_need0 - NBH / 2 - PAD
        panel_w   = self._NLBL_W + self._NBAR_W + PAD * 2
        self._PAD_N, self._PANEL_W_N = PAD, panel_w
        # z eksplisit, dan ini bukan hiasan.
        #
        # Semua elemen camera.ui duduk di z=0, jadi Panda menyortir bin
        # transparannya tanpa urutan yang bisa diandalkan — dan yang menang
        # ternyata latar panelnya. Termometernya SELALU ada, cuma dilihat
        # menembus kotak gelap 93% opak: fill hijau rgb(120,200,130) terukur
        # jadi rgb(19,33,31) di layar, persis 0.926*latar + 0.074*fill. Itu
        # sebabnya panel motif terbaca mati sejak awal. Yang di belakang diberi
        # z lebih besar, yang di depan lebih kecil.
        self._motive_panel_bg = _ui(
            scale=(panel_w, panel_top - panel_bot),
            position=(X_L - PAD + panel_w / 2, (panel_top + panel_bot) / 2),
            z=0.10,
            color=color.rgb(12, 20, 24, 128))

        self._mood_bg = _ui(scale=(self._NBAR_W, MOOD_H), z=0.06,
                            position=(self._NBAR_X + self._NBAR_W / 2, y_mood),
                            color=color.rgb(28, 34, 40, 210))
        self._mood_fill = _ui(scale=(self._NBAR_W, MOOD_H), z=0.03,
                              position=(self._NBAR_X + self._NBAR_W / 2, y_mood),
                              color=color.rgb(120, 210, 140))

        self._need_bg_ents   = []
        self._need_fill_ents = []
        for i, key in enumerate(self._motive_keys):
            y = y_need0 + (n - 1 - i) * self._NROW
            self._need_bg_ents.append(
                _ui(scale=(self._NBAR_W, NBH), z=0.06,
                    position=(self._NBAR_X + self._NBAR_W / 2, y),
                    color=color.rgb(28, 34, 40, 200)))
            self._need_fill_ents.append(
                _ui(scale=(self._NBAR_W, NBH), z=0.03,
                    position=(self._NBAR_X + self._NBAR_W / 2, y),
                    color=color.rgb(120, 200, 130)))
        self._motif_tampil = True

        # ── Flash message tengah ───────────────────────────────
        self._flash_ent = _txt('', pos=(0, 0.108), scale=1.1,
                               col=color.rgb(255, 245, 80), origin=(0, 0))
        self._flash_ent.enabled = False

        # ── Scrim: jaminan kontras untuk teks HUD ──────────────
        #
        # Teks HUD putih tanpa apa pun di belakangnya menghilang total di atas
        # latar terang. Terukur di scene farm jam 10: kotak jam berisi 2.528
        # piksel dan 95% di antaranya nyaris putih — teksnya ADA, warnanya
        # benar, dan tidak satu pun huruf bisa dibaca karena bangunan di
        # belakangnya sama putihnya.
        #
        # Bukan diperbaiki dengan mengganti warna teks: latar dunia berubah
        # sepanjang hari dan antar-scene, jadi warna teks apa pun akan kalah di
        # suatu tempat. Yang dijamin harus latarnya sendiri.
        #
        # Yang berubah sekarang: ukurannya tidak lagi dipatok. Scrim kiri dulu
        # 0.30 x 0.27 dan scrim bawah SELEBAR LAYAR, keduanya dipilih supaya
        # muat untuk teks terpanjang yang mungkin. Sekarang ketiganya dipas
        # ulang ke isinya di `_pas_scrim`, jadi alasnya persis sebesar yang
        # dibutuhkan dan tidak sepiksel pun lebih.
        #
        # z lebih besar = di belakang. Pelajaran yang sudah dibayar sekali di
        # panel motif: semua elemen camera.ui duduk di z=0 dan Panda menyortir
        # bin transparannya tanpa urutan yang bisa diandalkan.
        SCRIM_C = color.rgb(10, 16, 20, 112)
        self._scrim_kanan = _ui(scale=(0.001, 0.001), z=0.20,
                                position=(X_R, r1), color=SCRIM_C)
        self._scrim_kiri  = _ui(scale=(0.001, 0.001), z=0.20,
                                position=(X_L, hy), color=SCRIM_C)
        self._scrim_bawah = _ui(scale=(0.001, 0.001), z=0.20,
                                position=(X_R, Y_B), color=SCRIM_C)

        # ── Bawah Kanan: petunjuk tombol ──────────────────────
        # Dua baris manual selebar 640 px yang menuliskan tujuh pintasan
        # LENGKAP dan tidak pernah pergi. Patokan menaruh empat prompt
        # pendek, tiap-tiap satu GLIF tombol bundar plus satu kata kerja.
        #
        # Jadi: tiga baris, tiap baris satu kepingan tombol bergambar plus
        # satu kata, dan seluruh bloknya padam sendiri setelah 30 detik —
        # petunjuk yang tidak pernah selesai mengajar berhenti jadi petunjuk
        # dan jadi perabot. F1 tetap membuka panduan penuh kapan saja.
        self._control_hint = _txt(
            '', pos=(X_R, Y_B), scale=0.60,
            col=color.rgb(225, 238, 255), origin=(0.5, -0.5)
        )

        S_TUTS   = 0.58
        H_TUTS   = 0.0165
        h_tuts   = _tinggi(S_TUTS)
        self._H_HINT = H_ROW = max(h_tuts, H_TUTS) + 0.005
        self._hint_baris = []
        for i, (tuts, kata) in enumerate(reversed(self._PINTASAN)):
            y = Y_B + H_ROW * (i + 0.5)
            tex, rasio = tuts_tex(tuts, 26)
            cap = _ui(scale=(H_TUTS * rasio, H_TUTS), z=0.02,
                      position=(X_R, y), texture=tex, color=color.white)
            txt = _txt(kata, pos=(X_R, y), scale=S_TUTS,
                       col=color.rgb(228, 240, 252), origin=(0.5, 0.0))
            self._hint_baris.append((cap, txt, H_TUTS * rasio))
        self._hint_umur = 0.0
        self._hint_tampil = True

    # ── Tata letak yang dihitung ulang saat teksnya berubah ──────────
    #
    # Dihitung ulang HANYA saat teks berubah, bukan tiap frame: `Text.width`
    # membuat TextNode baru dan mengukur ulang fontnya tiap kali dipanggil,
    # dan ada tujuh teks yang perlu diukur. Frame rate di proyek ini sudah
    # 18-64 ms/frame; mengukur font 420 kali sedetik untuk hasil yang sama
    # persis adalah ongkos yang tidak dibayar siapa pun.

    @staticmethod
    def _lebar(e):
        """Lebar teks yang BENAR-BENAR tergambar, di ruang camera.ui.

        Bukan `Text.width * scale_x`. Rumus itu mengukur ulang fontnya lewat
        TextNode sementara dan hasilnya meleset ~10% ke bawah dari yang
        tergambar — terlihat langsung di tangkapan pertama sebagai
        'Cangkul[1-8] pilih alat' yang menempel tanpa jarak, padahal jaraknya
        diberi 15 px. `getTightBounds` membaca simpul yang sama dengan yang
        dirender, jadi tidak bisa meleset dari apa yang dilihat pemain.
        """
        try:
            if not str(e.text).strip():
                return 0.0
        except Exception:
            pass
        try:
            tb = e.getTightBounds(camera.ui)
            if tb is not None:
                return float(tb[1].x - tb[0].x)
        except Exception:
            pass
        try:
            return e.width * e.scale_x
        except Exception:
            return 0.0

    def _pas_scrim(self, scrim, kiri, kanan, atas, bawah, pad=0.008):
        if kanan <= kiri or atas <= bawah:
            scrim.enabled = False
            return
        scrim.enabled = True
        w = (kanan - kiri) + pad * 2
        h = (atas - bawah) + pad * 2
        scrim.scale = (w, h)
        scrim.position = ((kiri + kanan) / 2, (atas + bawah) / 2)

    def _pasang_tepi(self):
        """Ikuti tepi layar yang SEKARANG, bukan yang saat HUD dibangun.

        `window.aspect_ratio` masih berubah SESUDAH UIManager dibangun —
        tools/capture.py mencatatnya sendiri: 'changed aspect ratio: 1.81 ->
        1.778'. HUD yang dijangkar ke angka lama meleset 0.016 satuan ui,
        dan itu 17 px: jam kanan-atas terpotong di sisi kanan sementara nama
        alat menggantung 3 px di luar sisi kiri. Terlihat di tangkapan
        pertama sesudah perubahan ini, bukan diduga-duga.

        Mengembalikan True kalau tepinya bergeser, supaya pemanggilnya tahu
        harus menata ulang.
        """
        ex = window.aspect_ratio / 2
        if abs(ex - self._edge_x) < 1e-6:
            return False
        self._edge_x = ex
        self._X_L = -ex + self._M
        self._X_R = ex - self._M
        self._tata_kiri()
        self._control_hint.x = self._X_R
        for cap, txt, _w in getattr(self, '_hint_baris', ()):
            txt.x = self._X_R
        return True

    def _tata_kiri(self):
        """Tempatkan ULANG seluruh isi sudut kiri dari X_L yang berlaku.

        Mutlak, bukan `e.x += dx`. Yang lama menyimpan daftar entity lalu
        menggesernya relatif, dan daftar itu (`_jangkar_kiri`) TIDAK PERNAH
        diisi sekali pun — jadi saat aspek berubah 1.81 -> 1.778 sesudah HUD
        dibangun, satu-satunya yang ikut pindah adalah bilah, karena bilah
        memang ditulis ulang dari `_BAR_X_LEFT` tiap frame. Sisanya diam.
        Menghitung ulang dari X_L membuat hasilnya sama berapa kali pun ini
        dipanggil.
        """
        X_L = self._X_L
        IK, BW, BH = self._IK_BAR, self._BAR_W, self._BAR_H
        bx = X_L + IK + self._BAR_GAP
        self._BAR_X_LEFT = bx
        hy, ey = self._hy, self._ey

        self._hp_ikon.position = (X_L + IK / 2, hy)
        self._en_ikon.position = (X_L + IK / 2, ey)
        for e, y in ((self._hp_trek, hy), (self._en_trek, ey)):
            e.position = (bx + BW / 2, y)
        self._hp_val.x = bx + BW + self._NUM_GAP
        self._en_val.x = bx + BW + self._NUM_GAP

        SLOT, SGAP = self._SLOT, self._SGAP
        for i in range(len(self._alat_petak)):
            cx = X_L + SLOT / 2 + i * (SLOT + SGAP)
            self._alat_petak[i].x = cx
            self._alat_ikon[i].x  = cx

        for e in (self._seed_txt, self._buff_txt, self._queue_txt):
            e.x = X_L

        # Motif di sudut kiri-bawah.
        IK_N = self._IK_N
        self._NBAR_X = nbx = X_L + self._NLBL_W
        self._mood_ikon.x = X_L + IK_N / 2
        for e in self._need_ikon_ents:
            e.x = X_L + IK_N / 2
        self._mood_bg.x = nbx + self._NBAR_W / 2
        for e in self._need_bg_ents:
            e.x = nbx + self._NBAR_W / 2
        self._motive_panel_bg.x = X_L - self._PAD_N + self._PANEL_W_N / 2

    def _tata_ulang_hud(self):
        """Susun ulang baris kanan-atas, kiri-atas, dan alas gelapnya."""
        X_L, X_R = self._X_L, self._X_R
        Y_T, Y_B = self._Y_T, self._Y_B
        G = self._GAP

        # Kanan atas, baris 1: jam paling kanan, lalu cuaca, lalu tanggal.
        x = X_R
        for e in (self._time_txt, self._weather_txt, self._date_txt):
            e.x = x
            if str(e.text).strip():
                x -= self._lebar(e) + G
        kiri1 = x + G if x < X_R else X_R

        # Kanan atas, baris 2: emas paling kanan, lalu nama scene.
        x = X_R
        for e in (self._gold_txt, self._scene_txt):
            e.x = x
            if str(e.text).strip():
                x -= self._lebar(e) + G
        kiri2 = x + G if x < X_R else X_R

        h1 = self._time_txt.height * self._time_txt.scale_y
        h2 = self._gold_txt.height * self._gold_txt.scale_y
        self._pas_scrim(self._scrim_kanan, min(kiri1, kiri2), X_R,
                        Y_T, self._ROW2_Y - h2 / 2, pad=0.008)

        # Kiri atas: nama alat dipusatkan DI BAWAH petak yang terpilih, lalu
        # dijepit supaya tidak keluar dari lebar roda. Nama yang mengambang
        # di kiri sementara petak yang menyala ada di kanan tidak menamai
        # apa pun; yang menamai adalah yang berdiri tepat di bawahnya.
        idx  = min(max(int(getattr(self.state, 'tool_index', 0)), 0),
                   len(self._alat_petak) - 1)
        w_nm = self._lebar(self._tool_name)
        cx   = X_L + self._SLOT / 2 + idx * (self._SLOT + self._SGAP)
        self._tool_name.x = min(max(cx, X_L + w_nm / 2),
                                X_L + self._RODA_W - w_nm / 2)

        kanan = max(
            X_L + self._RODA_W + 0.005,     # petak terpilih menyembul sedikit
            self._BAR_X_LEFT + self._BAR_W + self._NUM_GAP + self._lebar(self._hp_val),
            self._BAR_X_LEFT + self._BAR_W + self._NUM_GAP + self._lebar(self._en_val),
        )
        bawah = self._tool_name.y - self._h_nama / 2
        for e in (self._seed_txt, self._buff_txt, self._queue_txt):
            if str(e.text).strip():
                kanan = max(kanan, X_L + self._lebar(e))
                bawah = min(bawah, e.y - (e.height * e.scale_y) / 2)
        self._pas_scrim(self._scrim_kiri, X_L, kanan, Y_T, bawah, pad=0.008)

        # Kanan bawah: alas dipas ke petunjuk tombol, bukan selebar layar.
        ch = self._control_hint
        if str(ch.text).strip():
            self._pas_scrim(self._scrim_bawah,
                            X_R - self._lebar(ch), X_R,
                            Y_B + ch.height * ch.scale_y, Y_B, pad=0.007)
        elif getattr(self, '_hint_tampil', False) and self._hint_baris:
            kiri = X_R
            for cap, txt, w_cap in self._hint_baris:
                w_txt = self._lebar(txt)
                txt.x = X_R
                cap.x = X_R - w_txt - 0.006 - w_cap / 2
                kiri = min(kiri, cap.x - w_cap / 2)
            atas = self._hint_baris[-1][1].y + self._H_HINT / 2
            self._pas_scrim(self._scrim_bawah, kiri, X_R, atas, Y_B, pad=0.007)
        else:
            self._scrim_bawah.enabled = False

    def toggle_motive_panel(self):
        """TAB: sembunyikan/tampilkan ringkasan motif di sudut kiri-bawah.

        Delapan motif adalah informasi yang berguna, tapi ia juga satu-satunya
        blok HUD yang tetap memakan tempat walau pemain sudah hafal isinya.
        Disembunyikan, bukan dibuang.
        """
        self._motif_tampil = not getattr(self, '_motif_tampil', True)
        v = self._motif_tampil
        for e in (self._motive_panel_bg, self._mood_lbl, self._mood_ikon,
                  self._mood_bg, self._mood_fill):
            if e is not None:
                e.enabled = v
        for nama in self._DAFTAR_MOTIF:
            for e in getattr(self, nama, None) or []:
                e.enabled = v
        return v

    def _sorot_alat(self, idx: int):
        """Petak terpilih membesar dan menyala; sisanya diredupkan.

        Redupnya lewat tint entity, bukan lewat tekstur kedua: satu gambar
        per alat sudah cukup, dan mengalikannya dengan abu-abu memberi versi
        'tidak aktif' yang konsisten tanpa satu pun bitmap tambahan.
        """
        S, SB = self._SLOT, self._SLOT_S
        for i, (petak, ikon) in enumerate(zip(self._alat_petak, self._alat_ikon)):
            pilih = (i == idx)
            u = SB if pilih else S
            petak.scale = (u, u)
            ikon.scale  = (u * 0.80, u * 0.80)
            petak.color = (color.rgb(240, 216, 140, 240) if pilih
                           else color.rgb(26, 34, 40, 200))
            ikon.color  = (color.white if pilih
                           else color.rgb(182, 192, 200))

    def _pasang_hint(self, v: bool):
        v = bool(v)
        if v == getattr(self, '_hint_tampil', None):
            return
        self._hint_tampil = v
        for cap, txt, _w in getattr(self, '_hint_baris', ()):
            cap.enabled = v
            txt.enabled = v

    # Warna termometer: hijau aman, kuning waspada, merah mendesak. Pemain harus
    # bisa membaca "yang mana yang gawat" tanpa membaca satu kata pun.
    _MOTIVE_OK   = (108, 196, 128)
    _MOTIVE_WARN = (226, 178,  70)
    _MOTIVE_CRIT = (214,  86,  92)

    @staticmethod
    def _motive_color(v: float):
        """v dalam skala motif -100..+100."""
        if v <= -40:
            return color.rgb(*UIManager._MOTIVE_CRIT)
        if v <= 10:
            return color.rgb(*UIManager._MOTIVE_WARN)
        return color.rgb(*UIManager._MOTIVE_OK)

    def _update_action_readout(self):
        """Tampilkan aksi yang sedang dijalankan + sisa antrian.

        Tanpa ini pemain menekan E lalu tidak melihat apa pun terjadi selama
        beberapa puluh detik-sim, dan menyimpulkan tombolnya rusak.
        """
        txt = getattr(self, '_queue_txt', None)
        if txt is None:
            return
        q = getattr(getattr(self, 'player', None), 'queue', None)
        if q is None or not q.busy:
            txt.text = ''
            return
        cur = q.current
        bar_n = 10
        filled = int(round(cur.progress * bar_n))
        bar = '#' * filled + '.' * (bar_n - filled)
        sisa = len(q.items) - 1
        ekor = f'  (+{sisa} antri)' if sisa > 0 else ''
        txt.text = f'{cur.name}  [{bar}] {int(cur.progress*100)}%{ekor}'

    def _update_motive_panel(self):
        """Isi termometer dari mesin motif. Bar diisi dari kiri; skala -100..+100
        dipetakan ke 0..1 sehingga bar setengah berarti motif netral."""
        if not self._need_fill_ents:
            return
        eng = self.state.mv
        for i, key in enumerate(self._motive_keys):
            v = eng.get(key)
            frac = max(0.0, min(1.0, (v + 100.0) / 200.0))
            fill = self._need_fill_ents[i]
            fill.scale_x = max(0.001, self._NBAR_W * frac)
            fill.x = self._NBAR_X + fill.scale_x / 2
            fill.color = self._motive_color(v)
        m = eng.mood
        frac = max(0.0, min(1.0, (m + 100.0) / 200.0))
        self._mood_fill.scale_x = max(0.001, self._NBAR_W * frac)
        self._mood_fill.x = self._NBAR_X + self._mood_fill.scale_x / 2
        self._mood_fill.color = self._motive_color(m)

    def _refresh_hud(self):
        s = self.state
        BAR_W = self._BAR_W
        BAR_X_LEFT = self._BAR_X_LEFT

        def _shrink_bar(bar, x_left, full_w, ratio):
            """Bar fill: anchored di sisi kiri, lebar berubah sesuai ratio."""
            w = max(0.001, full_w * ratio)
            bar.scale_x = w
            bar.x = x_left + w / 2

        # HP bar
        hp_r = max(0.001, s.hp / max(s.max_hp, 1))
        _shrink_bar(self._hp_bar, BAR_X_LEFT, BAR_W, hp_r)
        if hp_r > 0.6:
            self._hp_bar.color = color.rgb(55, 210, 80)
        elif hp_r > 0.3:
            self._hp_bar.color = color.rgb(255, 170, 30)
        else:
            self._hp_bar.color = color.rgb(220, 55, 55)
        self._hp_val.text = f'{int(s.hp)}/{s.max_hp}'

        # EN bar
        en_r = max(0.001, s.energy / max(s.max_energy, 1))
        _shrink_bar(self._en_bar, BAR_X_LEFT, BAR_W, en_r)
        self._en_bar.color = color.rgb(220, 80, 55) if en_r <= 0.3 else color.rgb(55, 205, 75)
        self._en_val.text = f'{int(s.energy)}/{s.max_energy}'

        # Gold + buff (§ simbol web-style)
        self._gold_txt.text = f'§ {s.gold}G'
        self._buff_txt.text = '+'.join(b.upper() for b in s.buffs) if s.buffs else ''

        # Alat aktif: nama satu kata, dan petaknya yang menyala.
        from .config import TOOLS
        idx = min(max(int(s.tool_index), 0), len(self._alat_petak) - 1)
        self._tool_name.text = TOOLS[idx] if idx < len(TOOLS) else ''
        if idx != getattr(self, '_idx_alat_tampil', None):
            self._idx_alat_tampil = idx
            self._sorot_alat(idx)

        # Seed hint (hanya saat Tanam/Panen aktif). Baris '[1-8] pilih alat'
        # dibuang: nomornya sudah tercetak di tiap petak roda alat.
        if s.tool_index in (2, 3):
            seed_name = CROPS.get(s.seed_key, {}).get('name', s.seed_key)
            seed_qty  = s.inventory.get(s.seed_key + '_seed', 0)
            self._seed_txt.text = f'Q/R: {seed_name} x{seed_qty}'
        else:
            self._seed_txt.text = ''

        # Time / weather
        self._time_txt.text = s.get_time_str()
        w_icons = {'Cerah': '^', 'Hujan': '~', 'Badai': '!', 'Mendung': '-', 'Berangin': '='}
        self._weather_txt.text = f"{w_icons.get(s.weather, '?')} {s.weather}"

        # Date / scene
        season_n = SEASON_NAMES[s.season_index]
        self._date_txt.text = f'Hari {s.day_in_season} | {season_n} Thn {s.year}'
        from .scenes import SCENES
        sc_display = SCENES.get(s.scene_name,
                     type('o', (object,), {'display': s.scene_name})()).display
        self._scene_txt.text = f'> {sc_display}'
        
        # Petunjuk tombol: prompt aksi kontekstual menang atas tiga kepingan
        # tombol tetap. Kalau ada prompt, kepingannya minggir — dua blok teks
        # di sudut yang sama akan saling menabrak.
        prompt = str(getattr(s, 'action_prompt', '') or '')
        self._control_hint.text = prompt
        self._pasang_hint(not prompt and self._hint_umur < self._HINT_PADAM)

        # Susun ulang hanya kalau ada teks yang benar-benar berubah.
        tanda = (self._time_txt.text, self._date_txt.text,
                 self._weather_txt.text, self._scene_txt.text,
                 self._gold_txt.text, self._tool_name.text,
                 self._seed_txt.text, self._hp_val.text, self._en_val.text,
                 self._buff_txt.text, self._queue_txt.text,
                 self._control_hint.text, self._hint_tampil)
        geser = self._pasang_tepi()
        if geser or tanda != getattr(self, '_tanda_hud', None):
            self._tanda_hud = tanda
            self._tata_ulang_hud()

    # ─── PUBLIC: FLASH MESSAGE ───────────────────────────
    def flash_msg(self, text: str, duration: float = 1.2):
        if self._flash_ent:
            self._flash_ent.text    = text
            self._flash_ent.enabled = True
            if hasattr(self, '_flash_bg'):
                self._flash_bg.enabled = True
            self._flash_t           = duration

    def show_message(self, text: str, duration: float = 2.0):
        self.flash_msg(text, duration)

    # ─── PUBLIC: DIALOG ──────────────────────────────────
    def _build_dialog_box(self):
        # Background kotak dialog diperkecil
        self._dlg_bg = _ui(scale=(0.70, 0.18), position=(0, -0.38),
                            color=color.rgb(15, 8, 30, 220))
        self._dlg_border = _ui(scale=(0.71, 0.19), position=(0, -0.38),
                                color=color.rgb(100, 70, 160, 180))
        self._dlg_name = _txt('', pos=(-0.33, -0.31), scale=0.90,
                               col=color.rgb(220, 190, 255))
        self._dlg_text = _txt('', pos=(-0.33, -0.36), scale=0.85,
                               col=color.rgb(230, 220, 255))
        self._dlg_cont = _txt('[E / SPACE: lanjut]', pos=(0.15, -0.44),
                               scale=0.70, col=color.rgb(150, 130, 200))
        self._dlg_choice_ents = [
            _txt('', pos=(-0.33, -0.34 - i * 0.035), scale=0.80, col=color.rgb(200, 185, 230))
            for i in range(3)
        ]
        self._set_dialog_visible(False)

    def _set_dialog_visible(self, v: bool):
        for e in (self._dlg_bg, self._dlg_border,
                  self._dlg_name, self._dlg_text, self._dlg_cont):
            e.enabled = v
        for e in self._dlg_choice_ents:
            e.enabled = v if (self._dlg_choices_active and v) else False

    def start_dialog(self, npc_id: str, state, node_key: str = None):
        self.state      = state
        self._dialog_npc = npc_id
        self._dialog_idx = 0
        self._dlg_choices_active = False
        self._dlg_choices = []

        if node_key is not None:
            from .data import BRANCHING_DIALOGUES
            node = BRANCHING_DIALOGUES.get(node_key)
            if node:
                self._dialog_lines = [node]
            else:
                self._dialog_lines = ["..."]
        elif npc_id == 'mailbox':
            self._dialog_lines = [
                ["Surat dari Paman Arsa:"],
                ["Selamat datang di Lembah Karsa, keponakanku."],
                ["Rawat kebun ini baik-baik. Tanah di sini istimewa."],
                ["Kenali penduduk desa \u2014 mereka akan membantumu."],
                ["Jangan abaikan lembah ini. Suatu hari kau akan mengerti"],
                ["kenapa aku pergi. Bukan kabur \u2014 tapi mencari jawaban."],
                ["Ada perjanjian kuno yang harus dijaga."],
                ["Aku tidak cukup kuat untuk memenuhinya."],
                ["Tapi kau... kau bisa. Aku percaya padamu."],
                ["Salam hangat, Pamanmu Arsa."],
            ]
        else:
            npc_data = _ALL_NPCS.get(npc_id, {})
            dial_idx = state.npc_dialog_index.get(npc_id, 0)
            talks_raw = npc_data.get('talks', [["..."]])

            # Support new dict-based cascaded dialog format
            if isinstance(talks_raw, dict):
                hearts = state.npc_hearts.get(npc_id, 0)
                qs = state.quest_stage
                chosen = None
                # Priority: quest_11 > quest_10 > quest_5 > hearts_10 > hearts_7 > hearts_5 > hearts_3 > default
                if qs >= 11 and 'quest_11' in talks_raw:
                    chosen = talks_raw['quest_11']
                elif qs >= 10 and 'quest_10' in talks_raw:
                    chosen = talks_raw['quest_10']
                elif qs >= 5 and 'quest_5' in talks_raw:
                    chosen = talks_raw['quest_5']
                if chosen is None:
                    for h in (10, 7, 5, 3):
                        key = f'hearts_{h}'
                        if hearts >= h and key in talks_raw:
                            chosen = talks_raw[key]
                            break
                if chosen is None:
                    chosen = talks_raw.get('default', [["..."]])
                self._dialog_lines = [chosen[dial_idx % len(chosen)]]
            else:
                # Legacy list format fallback
                self._dialog_lines = [talks_raw[dial_idx % len(talks_raw)]]

        self._show_dialog_line()
        self.mode = 'dialog'

    def _show_dialog_line(self):
        if self._dialog_idx >= len(self._dialog_lines):
            self._end_dialog()
            return
        npc_data = _ALL_NPCS.get(self._dialog_npc, {})
        name     = npc_data.get('name', self._dialog_npc) if self._dialog_npc != 'mailbox' else 'Kotak Pos'
        line     = self._dialog_lines[self._dialog_idx]

        if isinstance(line, dict):
            # Branching node dictionary
            text = line.get('text', '')
            self._dlg_name.text = name
            self._dlg_text.text = text

            # Filter valid choices by condition
            choices = line.get('choices', [])
            valid_choices = []
            for c in choices:
                cond = c.get('condition')
                show = True
                if cond:
                    if 'min_hearts' in cond:
                        for nid, val in cond['min_hearts'].items():
                            if self.state.npc_hearts.get(nid, 0) < val:
                                show = False
                    if 'has_item' in cond:
                        item_req = cond['has_item']
                        if self.state.inventory.get(item_req, 0) <= 0:
                            show = False
                    if 'side_quest_active' in cond:
                        qkey = cond['side_quest_active']
                        if self.state.side_quests.get(qkey) != 'active':
                            show = False
                if show:
                    valid_choices.append(c)

            if valid_choices:
                self._dlg_choices = valid_choices
                self._dlg_choice_idx = 0
                self._dlg_choices_active = True

                # Expand dialog UI size for choices
                self._dlg_bg.scale_y = 0.26
                self._dlg_bg.y = -0.34
                self._dlg_border.scale_y = 0.27
                self._dlg_border.y = -0.34
                self._dlg_cont.text = '[Tekan 1-3 atau Arrow+Space]'
                self._dlg_text.y = -0.27

                self._refresh_dialog_choices_ui()
            else:
                self._dlg_choices_active = False
                self._dlg_choices = []
                self._dlg_bg.scale_y = 0.18
                self._dlg_bg.y = -0.38
                self._dlg_border.scale_y = 0.19
                self._dlg_border.y = -0.38
                self._dlg_cont.text = '[E / SPACE: lanjut]'
                self._dlg_text.y = -0.36
                for ent in self._dlg_choice_ents:
                    ent.enabled = False

            self._set_dialog_visible(True)
        else:
            # Legacy simple text line
            self._dlg_choices_active = False
            self._dlg_choices = []
            self._dlg_bg.scale_y = 0.18
            self._dlg_bg.y = -0.38
            self._dlg_border.scale_y = 0.19
            self._dlg_border.y = -0.38
            self._dlg_cont.text = '[E / SPACE: lanjut]'
            self._dlg_text.y = -0.36
            for ent in self._dlg_choice_ents:
                ent.enabled = False

            text = ' '.join(line) if isinstance(line, list) else line
            self._dlg_name.text = name
            self._dlg_text.text = text
            self._set_dialog_visible(True)

    def advance_dialog(self) -> bool:
        """Maju ke baris berikutnya. Return True jika dialog selesai."""
        if self._dlg_choices_active:
            # Cannot advance linearly while choices are active
            return False
        self._dialog_idx += 1
        if self._dialog_idx >= len(self._dialog_lines):
            self._end_dialog()
            return True
        self._show_dialog_line()
        return False

    def _end_dialog(self):
        # Majukan dialog index NPC
        if self._dialog_npc and self._dialog_npc != 'mailbox':
            s   = self.state
            npc = _ALL_NPCS.get(self._dialog_npc, {})
            idx = s.npc_dialog_index.get(self._dialog_npc, 0)
            s.npc_dialog_index[self._dialog_npc] = idx + 1
            s.npc_hearts[self._dialog_npc] = min(10, s.npc_hearts.get(self._dialog_npc, 0) + 0.1)
        self._set_dialog_visible(False)
        self.mode = 'hud'
        if hasattr(self, 'player') and self.player:
            self.player._check_quest_progress(self)

    def _refresh_dialog_choices_ui(self):
        for i, ent in enumerate(self._dlg_choice_ents):
            if i < len(self._dlg_choices):
                c = self._dlg_choices[i]
                prefix = '> ' if i == self._dlg_choice_idx else '  '
                ent.text = f"{prefix}[{i+1}] {c['text']}"
                if i == self._dlg_choice_idx:
                    ent.color = color.rgb(245, 215, 80)
                else:
                    ent.color = color.rgb(200, 185, 230)
                ent.enabled = True
            else:
                ent.text = ''
                ent.enabled = False

    def is_choice_active(self) -> bool:
        return self._dlg_choices_active

    def navigate_dialog_choices(self, delta: int):
        if not self._dlg_choices:
            return
        self._dlg_choice_idx = (self._dlg_choice_idx + delta) % len(self._dlg_choices)
        self._refresh_dialog_choices_ui()

    def confirm_dialog_choice(self):
        if not self._dlg_choices:
            return
        c = self._dlg_choices[self._dlg_choice_idx]
        self._execute_choice(c)

    def select_dialog_choice(self, idx: int):
        if 1 <= idx <= len(self._dlg_choices):
            self._dlg_choice_idx = idx - 1
            self.confirm_dialog_choice()

    def _execute_choice(self, c):
        s = self.state
        effect = c.get('effect')

        if effect:
            if 'hearts' in effect:
                for nid, val in effect['hearts'].items():
                    s.npc_hearts[nid] = min(10, s.npc_hearts.get(nid, 0) + val)
            if 'gold' in effect:
                s.gold = max(0, s.gold + effect['gold'])
            if 'energy' in effect:
                s.energy = max(0, min(s.max_energy, s.energy + effect['energy']))
            if 'sosial' in effect:
                s.sosial = max(0, min(NEED_MAX, s.sosial + effect['sosial']))
            if 'give_item' in effect:
                item = effect['give_item']
                s.inventory[item] = s.inventory.get(item, 0) + 1
            if 'take_item' in effect:
                item = effect['take_item']
                s.inventory[item] = max(0, s.inventory.get(item, 0) - 1)
            if 'start_side_quest' in effect:
                qkey = effect['start_side_quest']
                s.side_quests[qkey] = 'active'
                self.flash_msg(f"Quest baru: {qkey.replace('_', ' ').title()}", 3.0)
            if 'complete_side_quest' in effect:
                qkey = effect['complete_side_quest']
                s.side_quests[qkey] = 'completed'
                self.flash_msg(f"Quest selesai: {qkey.replace('_', ' ').title()}!", 3.0)
                s.stats['gifts'] = s.stats.get('gifts', 0) + 1
            if 'naga_defeated' in effect:
                s.naga_defeated = effect['naga_defeated']

        nxt = c.get('next')
        if nxt:
            self.start_dialog(self._dialog_npc, s, node_key=nxt)
        else:
            self._end_dialog()

    # ─── PUBLIC: PANEL ───────────────────────────────────
    def _build_panel_bg(self):
        self._panel_bg = _ui(scale=(1.5, 1.2), position=(0, 0),
                              color=color.rgb(10, 5, 20, 210))
        self._panel_title = _txt('', pos=(-0.45, 0.44), scale=1.2,
                                  col=color.rgb(220, 190, 255))
        self._panel_body  = _txt('', pos=(-0.45, 0.36), scale=0.80,
                                  col=color.rgb(210, 210, 230))
        self._panel_hint  = _txt('[ESC: tutup]', pos=(-0.45, -0.44), scale=0.75,
                                  col=color.rgb(140, 130, 180))
        self._set_panel_visible(False)

    # Entity yang membentuk HUD permainan. Didaftar sekali di sini supaya
    # menyembunyikannya tidak perlu menebak-nebak isi camera.ui — dan supaya
    # menambah elemen HUD baru cuma butuh satu nama di daftar ini.
    _NAMA_HUD = (
        '_tool_name', '_seed_txt', '_hp_bar', '_hp_val', '_en_bar', '_en_val',
        '_hp_trek', '_en_trek', '_hp_ikon', '_en_ikon',
        '_time_txt', '_date_txt', '_weather_txt', '_scene_txt', '_gold_txt',
        '_buff_txt', '_queue_txt', '_mood_bg', '_mood_fill', '_mood_lbl',
        '_mood_ikon', '_motive_panel_bg', '_control_hint',
    )
    # Yang ikut disembunyikan TAB: hanya ringkasan motif. Roda alat tidak —
    # ia jawaban atas "alat apa yang sedang kupegang", dan pertanyaan itu
    # tidak hilang ketika pemain menutup panel kebutuhannya.
    _DAFTAR_MOTIF = ('_need_bg_ents', '_need_fill_ents', '_need_lbl_ents',
                     '_need_ikon_ents')
    _DAFTAR_HUD = _DAFTAR_MOTIF + ('_alat_petak', '_alat_ikon')

    def set_hud_visible(self, v: bool):
        """Sembunyikan/tampilkan seluruh HUD permainan.

        Dibuat untuk sinema: adegan bercerita yang masih menampilkan bar
        energi dan panel suasana hati tidak terbaca sebagai adegan, ia
        terbaca sebagai permainan yang macet dengan pita hitam di atasnya.
        Terlihat jelas di tangkapan pertama — panel SUASANA HATI menabrak
        baris narasinya sendiri.
        """
        for nama in self._NAMA_HUD:
            e = getattr(self, nama, None)
            if e is not None:
                try:
                    e.enabled = v
                except Exception:
                    pass
        for nama in self._DAFTAR_HUD:
            for e in getattr(self, nama, None) or []:
                try:
                    e.enabled = v
                except Exception:
                    pass
        # Kepingan petunjuk tombol ikut padam saat sinema; ia bukan bagian
        # dari cerita, dan tiga kotak bertuliskan SPACE di sudut adegan
        # membuat adegannya terbaca sebagai permainan yang macet.
        for cap, txt, _w in getattr(self, '_hint_baris', ()):
            try:
                cap.enabled = v and self._hint_tampil
                txt.enabled = v and self._hint_tampil
            except Exception:
                pass
        # Scrim kontras ikut: tanpa ini pita hitamnya bertumpuk dengan
        # gradien gelap HUD dan tepinya terlihat sebagai dua lapis abu.
        for nama in ('_scrim_kanan', '_scrim_kiri', '_scrim_bawah'):
            e = getattr(self, nama, None)
            if e is not None:
                try:
                    e.enabled = v
                except Exception:
                    pass
        # Pilihan pemain menang atas "tampilkan lagi": kalau ringkasan motif
        # sengaja disembunyikan lewat TAB, keluar dari sinema tidak boleh
        # diam-diam menyalakannya kembali.
        if v and not getattr(self, '_motif_tampil', True):
            self._motif_tampil = True       # toggle akan membalikkannya
            self.toggle_motive_panel()

    def _set_panel_visible(self, v: bool):
        for e in (self._panel_bg, self._panel_title,
                  self._panel_body, self._panel_hint):
            e.enabled = v

    def open_panel(self, name: str):
        self._panel_name = name
        self._render_panel(name)
        self._set_panel_visible(True)
        self.mode = 'panel'

    def _render_panel(self, name: str):
        s = self.state
        titles = {
            'inventory': 'Inventori',
            'quest':     'Catatan Quest',
            'map':       'Peta Dunia',
            'relations': 'Hubungan NPC',
            'shop':      'Warung Bu Sari',
            'olahan':    'Dapur - Olah Hasil Panen',
            'crafting':  'Bengkel Pak Budi',
            'help':      'Panduan Kontrol',
            'catatan':   'Catatan Lembah',
        }
        self._panel_title.text = titles.get(name, name.capitalize())
        # Update hint sesuai panel
        if name == 'shop':
            self._panel_hint.text = ('[TAB atau 0: ganti BELI/JUAL]   [1-9: pilih baris]'
                                     '   [Q/R: halaman]   [ESC: Tutup]')
        elif name == 'olahan':
            self._panel_hint.text = '[1-9: Olah]   [Q/R: halaman]   [ESC: Tutup]'
        elif name == 'crafting':
            self._panel_hint.text = '[1-5: Pickaxe]   [6-9: Pedang]   [ESC: Tutup]'
        else:
            self._panel_hint.text = '[ESC: tutup]'

        if name == 'inventory':
            # Tas dulu mencetak kunci dict mentah tanpa harga ('lobak_seed: 3').
            # Angka yang tidak bisa ditemukan pemain tidak mengajarkan apa-apa,
            # jadi tiap baris kini membawa nama layak baca, harga satuan, nilai
            # total, dan - hanya kalau mengolahnya memang lebih untung - ke mana
            # barang itu sebaiknya pergi.
            from .economy import (item_name, sell_price, best_process_hint,
                                  inventory_value)
            lines = [f"Emas: {s.gold}G   HP: {s.hp}/{s.max_hp}   Energi: {s.energy}/{s.max_energy}",
                     f"Pickaxe: Tier {s.pickaxe_tier}   Pedang: {s.sword_id or 'Tidak punya'}", '']
            rows = [(k, q) for k, q in s.inventory.items() if q > 0]
            if rows:
                # Paling berharga di atas: itu yang sedang dipikirkan pemain.
                rows.sort(key=lambda r: (-sell_price(r[0]) * r[1], r[0]))
                lines.append(f"  {'BARANG':<18}{'JML':>4}{'@':>7}{'TOTAL':>8}   SARAN")
                for item, qty in rows[:19]:
                    harga = sell_price(item)
                    hrg_s = f"{harga}G" if harga else "-"
                    tot_s = f"{harga * qty}G" if harga else "-"
                    lines.append(f"  {item_name(item)[:18]:<18}{qty:>4}{hrg_s:>7}"
                                 f"{tot_s:>8}   {best_process_hint(item)}")
                lines.append('')
                lines.append("  Nilai seluruh tas bila dijual di Warung: "
                             f"{inventory_value(s.inventory)}G")
                lines.append("  Peti Kirim di kebun membayar 85% tanpa perlu jalan.")
            else:
                lines.append("  (Kosong)")
            self._panel_body.text = '\n'.join(lines[:28])

        elif name == 'quest':
            qs   = s.quest_stage
            lines= ["── TUGAS UTAMA ──", ""]
            for q in QUEST_STAGES:
                mark = '[v]' if q['s'] < qs else ('[>]' if q['s'] == qs else '[ ]')
                lines.append(f"  {mark} [{q['s']}] {q['t']}: {q['d']}")

            lines.append("")
            lines.append("── QUEST SAMPINGAN ──")
            lines.append("")

            has_side = False
            from .data import SIDE_QUESTS
            s_quests = getattr(s, 'side_quests', {})
            for qkey, status in s_quests.items():
                qdata = SIDE_QUESTS.get(qkey)
                if qdata:
                    mark = '[v]' if status == 'completed' else '[>]'
                    lines.append(f"  {mark} {qdata['name']}: {qdata['desc']}")
                    has_side = True

            if not has_side:
                lines.append("  (Tidak ada quest sampingan aktif)")
            self._panel_body.text = '\n'.join(lines[:28])

        elif name == 'map':
            cur = s.scene_name
            def _loc(key, label):
                return f'[{label}]' if cur != key else f'>>>{label}<<<'
            lines = [
                '',
                f"  {_loc('mountain','LERENG GUNUNG')}",
                '          |',
                f"  {_loc('farm','KEBUN')}---{_loc('town','DESA')}---{_loc('lake','DANAU')}",
                '              |',
                f"         {_loc('cemetery','KUBURAN')}",
                '              |',
                f"         {_loc('naga_cave','GUA HYANG')}",
                '              |',
                f"         {_loc('dungeon', 'DUNGEON Lv.' + str(s.dungeon_level))}",
                '',
                '  Indoor: [rumah] [warung] [klinik]',
                '          [studio] [bengkel]',
                '',
                f"  Lokasi : {s.scene_name}",
                f"  Hari   : {s.day_in_season} | {self._season_name(s)}  Thn {s.year}",
                f"  Cuaca  : {s.weather}",
            ]
            self._panel_body.text = '\n'.join(lines)

        elif name == 'relations':
            lines = []
            for npc_id in list(_ALL_NPCS.keys()):
                hearts = s.npc_hearts.get(npc_id, 0)
                bar    = '*' * int(hearts) + '-' * (10 - int(hearts))
                name_  = _ALL_NPCS[npc_id].get('name', npc_id)
                lines.append(f"  {name_:15s} {bar[:10]}")
            self._panel_body.text = '\n'.join(lines[:25])

        elif name == 'shop':
            # Warung sekarang punya dua sisi. Sebelumnya hanya BELI ada, jadi
            # setiap barang yang dikumpulkan pemain tidak punya jalan keluar
            # dan harganya tidak pernah terlihat di mana pun.
            lines = self._render_market(s)
            self._set_body(lines)

        elif name == 'olahan':
            lines = self._render_olahan(s)
            self._panel_body.text = '\n'.join(lines)

        elif name == 'crafting':
            inv = s.inventory
            lines = [
                f"Emas: {s.gold}G   Pickaxe: Tier {s.pickaxe_tier}   "
                f"Pedang: {s.sword_id or '-'}", '',
                "── PICKAXE ──",
            ]
            for i, r in enumerate(PICKAXE_RECIPES):
                need = ', '.join(f"{k}×{v}" for k, v in r['needs'].items())
                got_gold = s.gold >= r['cost_gold']
                got_mat  = all(inv.get(k, 0) >= v for k, v in r['needs'].items())
                already  = s.pickaxe_tier >= r['tier']
                mark = '[v]' if already else ('[o]' if (got_gold and got_mat) else '[ ]')
                lines.append(f"  [{i+1}] {mark} {r['name']:18s}  {r['cost_gold']:>4}G + {need}")
            lines.append('')
            lines.append("── PEDANG ──")
            for i, r in enumerate(SWORD_RECIPES):
                num = i + 6
                need = ', '.join(f"{k}×{v}" for k, v in r['needs'].items())
                got_gold = s.gold >= r['cost_gold']
                got_mat  = all(inv.get(k, 0) >= v for k, v in r['needs'].items())
                already  = s.sword_id == r['id']
                mark = '[v]' if already else ('[o]' if (got_gold and got_mat) else '[ ]')
                lines.append(f"  [{num}] {mark} {r['name']:18s}  {r['cost_gold']:>4}G + {need} (DMG {r['damage']})")
            lines.append('')
            lines.append("[ ]=kurang bahan  [o]=siap  [v]=sudah punya")
            self._panel_body.text = '\n'.join(lines)

        elif name == 'help':
            self._panel_body.text = (
                "── GERAK ──\n"
                "  WASD / Arrow  : Jalan\n"
                "  Shift+WASD    : Lari (pakai energi)\n\n"
                "── AKSI ──\n"
                "  SPACE  : Pakai alat aktif\n"
                "  E      : Pie Menu interaksi NPC\n"
                "  Z      : Serang (butuh pedang)\n"
                "  X      : Tambah/hapus tile ke Antrian\n"
                "  C      : Jalankan semua Antrian Aksi\n"
                "  F      : Tangkap makhluk liar\n"
                "  G      : Beri hadiah ke NPC\n"
                "  V      : Makan item (pulihkan HP/EN)\n"
                "  B      : Terbang (Sapoe Terbang)\n"
                "  Y      : Meluncur / Dash Stunt (-15 EN)\n"
                "  T      : Tidur (hanya di Rumah)\n\n"
                "── ALAT (angka 1-9) ──\n"
                "  Roda ikon di kiri-atas. Nomornya tercetak di tiap petak;\n"
                "  yang menyala adalah yang sedang dipilih, dan namanya\n"
                "  berdiri tepat di bawahnya. Alat baru keluar ke tangan\n"
                "  saat SPACE ditekan, lalu disimpan lagi sendiri.\n"
                "  1 Cangkul  2 Siram  3 Tanam  4 Panen  5 Kapak\n"
                "  6 Hadiah   7 Pickaxe 8 Pedang 9 Pancing\n"
                "  Q/R    : Ganti bibit\n\n"
                "── IKON KEBUTUHAN (kiri-bawah) ──\n"
                "  Wajah  Suasana hati (jumlah semua di bawahnya)\n"
                "  Garpu  Lapar        Kursi  Nyaman\n"
                "  Tetes  Higiene      Kloset Kamar Kecil\n"
                "  Petir  Energi       Bintang Senang\n"
                "  Orang  Sosial       Bingkai Ruangan\n\n"
                "── MENU ──\n"
                "  I: Inventori   M: Peta\n"
                "  J: Quest       H: Relasi NPC\n"
                "  N: Catatan Lembah (lore)\n"
                "  K: Warung, beli & JUAL (di Warung)\n"
                "  O: Dapur, olah hasil panen (di Rumah)\n"
                "  Peti Kirim di kebun: jual cepat 85% harga\n"
                "  U: Kerajinan (di Bengkel)\n"
                "  F2: Ubah penampilan karakter\n"
                "  F5: Simpan     F9: Muat\n"
                "  ESC: Tutup panel"
            )

        elif name == 'catatan':
            from .data import LORE_ITEMS
            lines = ['Fragmen cerita dan catatan yang kau temukan:', '']
            s_lore = getattr(s, 'lore_collected', [])
            if not s_lore:
                lines.append('  (Belum ada catatan. Jelajahi lembah lebih dalam.)')
            else:
                for lore_id in s_lore:
                    item = LORE_ITEMS.get(lore_id, {})
                    name_ = item.get('name', lore_id)
                    text_ = item.get('text', '')
                    lines.append(f'  [{name_}]')
                    # Word wrap the text to fit panel
                    words = text_.split()
                    line = '    '
                    for w in words:
                        if len(line) + len(w) + 1 > 60:
                            lines.append(line)
                            line = '    ' + w
                        else:
                            line += (' ' if len(line) > 4 else '') + w
                    if line.strip():
                        lines.append(line)
                    lines.append('')
            self._panel_body.text = '\n'.join(lines[:28])

    def _set_body(self, lines):
        self._panel_body.text = chr(10).join(lines)

    @staticmethod
    def _season_name(s):
        try:
            from .config import SEASON_NAMES
            return SEASON_NAMES[s.season_index]
        except Exception:
            return '-'

    # ─── PASAR: BELI / JUAL ──────────────────────────────
    # Sembilan baris per halaman karena input panel hanya menerima angka 1-9.
    ROWS_PER_PAGE = 9

    def _market_state(self):
        """(mode, halaman). Hidup di UIManager, bukan di save — ini keadaan
        layar, bukan keadaan dunia."""
        if not hasattr(self, '_market_mode'):
            self._market_mode = 'beli'
            self._market_page = 0
        return self._market_mode, self._market_page

    def cycle_market_mode(self):
        mode, _ = self._market_state()
        self._market_mode = 'jual' if mode == 'beli' else 'beli'
        self._market_page = 0
        self._render_panel(self._panel_name or 'shop')

    def market_page(self, delta: int):
        self._market_state()
        self._market_page = max(0, self._market_page + delta)
        self._render_panel(self._panel_name or 'shop')

    def _page_slice(self, rows):
        self._market_state()
        n_pages = max(1, -(-len(rows) // self.ROWS_PER_PAGE))
        self._market_page = min(self._market_page, n_pages - 1)
        start = self._market_page * self.ROWS_PER_PAGE
        return rows[start:start + self.ROWS_PER_PAGE], self._market_page, n_pages

    def _render_market(self, s) -> list:
        from .economy import (margin_hint, sellable_items, sell_price,
                              item_name, inventory_value)
        mode, _ = self._market_state()
        tab = ('>> BELI <<      jual' if mode == 'beli'
               else '   beli      >> JUAL <<')
        lines = [f"Emas: {s.gold}G   Musim: {self._season_name(s)}   "
                 f"Nilai tas: {inventory_value(s.inventory)}G",
                 tab, '']

        if mode == 'beli':
            rows, page, n_pages = self._page_slice(list(SHOP_ITEMS))
            lines.append(f"  {'BARANG':<20}{'HARGA':>6}  {'MUSIM':<11} HASILNYA NANTI")
            for i, it in enumerate(rows):
                mampu = '' if s.gold >= it['price'] else '  (gold kurang)'
                # Ternak yang sudah dibeli tetap terdaftar tapi ditandai, bukan
                # dihilangkan: daftar yang barisnya berpindah-pindah tiap kali
                # membeli membuat nomor pilihannya tidak bisa dihafal.
                if it.get('animal') in getattr(s, 'owned_animals', []):
                    mampu = '  (sudah di kandang)'
                lines.append(f"  [{i+1}] {it['name'][:16]:<16}{it['price']:>5}G  "
                             f"{it['season']:<11} {margin_hint(it)}{mampu}")
            lines.append('')
            lines.append("  Angka = beli 1. Kolom kanan memberi tahu berapa hasil")
            lines.append("  panennya nanti, jadi untung-ruginya terlihat sebelum bayar.")
        else:
            all_rows = sellable_items(s.inventory)
            if not all_rows:
                lines.append("  Tidak ada yang bisa dijual. Panen dulu, atau ambil")
                lines.append("  hasil ternak di kandang.")
                return lines
            rows, page, n_pages = self._page_slice(all_rows)
            lines.append(f"  {'BARANG':<20}{'JML':>4}{'@':>7}{'SEMUA':>8}")
            for i, (item, qty, total) in enumerate(rows):
                lines.append(f"  [{i+1}] {item_name(item)[:16]:<16}{qty:>4}"
                             f"{sell_price(item):>6}G{total:>7}G")
            lines.append('')
            lines.append("  Angka = jual SEMUA barang di baris itu, harga penuh.")
            lines.append("  Peti Kirim di kebun lebih cepat tapi hanya membayar 85%.")

        if n_pages > 1:
            lines.append(f"  -- halaman {page+1}/{n_pages}  [Q/R] --")
        return lines

    def _render_olahan(self, s) -> list:
        from .economy import (PROCESS_RECIPES, recipe_input_value,
                              recipe_output_value, recipe_uplift, item_name)
        lines = [f"Emas: {s.gold}G   Energi: {s.energy}/{s.max_energy}", '',
                 "Mengolah menambah sekitar 40% nilai, dibayar dengan energi.",
                 '']
        rows, page, n_pages = self._page_slice(list(PROCESS_RECIPES))
        lines.append(f"  {'HASIL':<20}{'DARI':<22}{'NILAI':>14}  EN")
        for i, r in enumerate(rows):
            bahan = ', '.join(f"{item_name(k)} x{v}" for k, v in r['needs'].items())
            punya = all(s.inventory.get(k, 0) >= v for k, v in r['needs'].items())
            cukup = s.energy >= r['en']
            mark  = '[o]' if (punya and cukup) else '[ ]'
            masuk = recipe_input_value(r)
            keluar = recipe_output_value(r)
            naik  = int(round((recipe_uplift(r) - 1) * 100))
            out_n = f"{item_name(r['out'])} x{r['n']}" if r['n'] > 1 else item_name(r['out'])
            lines.append(f"  [{i+1}]{mark} {out_n[:15]:<15}{bahan[:22]:<22}"
                         f"{masuk:>4}G > {keluar:>4}G +{naik}%{r['en']:>3}")
        lines.append('')
        lines.append("  [o] = bahan & energi cukup.  [ ] = belum bisa.")
        lines.append("  Pakan Ternak dinilai dari jerami yang tidak jadi dibeli")
        lines.append("  (18G/hari-pakan) — menjualnya rugi, memakainya untung.")
        if n_pages > 1:
            lines.append(f"  -- halaman {page+1}/{n_pages}  [Q/R] --")
        return lines

    # ─── PANEL ACTIONS (shop/craft) ──────────────────────
    def panel_action(self, idx: int) -> str:
        """Dipanggil dari app.input() saat user tekan angka di panel.
        idx 1-based. Return pesan untuk flash_msg."""
        if self._panel_name == 'shop':
            mode, _ = self._market_state()
            return (self._buy_shop_item(idx) if mode == 'beli'
                    else self._sell_stack(idx))
        elif self._panel_name == 'olahan':
            return self._process_item(idx)
        elif self._panel_name == 'crafting':
            return self._craft_item(idx)
        return ''

    def _buy_shop_item(self, idx: int) -> str:
        s = self.state
        rows, _page, _n = self._page_slice(list(SHOP_ITEMS))
        if not (1 <= idx <= len(rows)):
            return ''
        it = rows[idx - 1]
        if s.gold < it['price']:
            return f"Gold kurang ({it['price']}G)."

        # Ternak tidak masuk tas. Ia pindah ke kandang, dan itu satu-satunya
        # baris toko yang mengubah dunia alih-alih inventori.
        aid = it.get('animal')
        if aid:
            punya = getattr(s, 'owned_animals', None)
            if punya is None:
                punya = s.owned_animals = []
            if aid in punya:
                return f"{it['name']} sudah ada di kandangmu."
            s.gold -= it['price']
            punya.append(aid)
            if not s.shop_unlocked:
                s.shop_unlocked = True
            self._render_panel('shop')
            return (f"{it['name']} dibeli -{it['price']}G. "
                    f"Ia menunggu di kandang — beri makan hari ini.")

        s.gold -= it['price']
        s.inventory[it['id']] = s.inventory.get(it['id'], 0) + 1
        if not s.shop_unlocked:
            s.shop_unlocked = True
        self._render_panel('shop')   # refresh tampilan
        return f"Beli {it['name']} -{it['price']}G"

    def _sell_stack(self, idx: int) -> str:
        """Jual seluruh tumpukan di satu baris, harga penuh Warung.

        Per-tumpukan, bukan per-butir: pemain dengan 40 lobak tidak boleh harus
        menekan tombol 40 kali. Peti Kirim tetap ada untuk yang ingin menjual
        semuanya sekaligus dengan potongan.
        """
        from .economy import sellable_items, item_name
        s = self.state
        rows, _page, _n = self._page_slice(sellable_items(s.inventory))
        if not (1 <= idx <= len(rows)):
            return ''
        item, qty, total = rows[idx - 1]
        del s.inventory[item]
        s.gold += total
        s.stats['earned'] = s.stats.get('earned', 0) + total
        self._render_panel('shop')
        return f"Jual {item_name(item)} x{qty} +{total}G"

    def _process_item(self, idx: int) -> str:
        """Olah bahan mentah jadi barang lebih mahal, bayar dengan energi."""
        from .economy import (PROCESS_RECIPES, item_name, recipe_output_value,
                              recipe_input_value)
        s = self.state
        rows, _page, _n = self._page_slice(list(PROCESS_RECIPES))
        if not (1 <= idx <= len(rows)):
            return ''
        r = rows[idx - 1]
        for k, v in r['needs'].items():
            if s.inventory.get(k, 0) < v:
                return f"Bahan kurang: butuh {item_name(k)} x{v}."
        if s.energy < r['en']:
            return f"Energi kurang (butuh {r['en']})."
        for k, v in r['needs'].items():
            s.inventory[k] -= v
            if s.inventory[k] <= 0:
                del s.inventory[k]
        s.energy -= r['en']
        s.inventory[r['out']] = s.inventory.get(r['out'], 0) + r['n']
        s.stats['processed'] = s.stats.get('processed', 0) + 1
        self._render_panel('olahan')
        untung = recipe_output_value(r) - recipe_input_value(r)
        return (f"+{r['n']} {item_name(r['out'])} "
                f"(nilai naik {untung}G, -{r['en']} EN)")

    def _craft_item(self, idx: int) -> str:
        s = self.state
        # 1-5 = pickaxe, 6-9 = sword
        if 1 <= idx <= len(PICKAXE_RECIPES):
            r = PICKAXE_RECIPES[idx - 1]
            if s.pickaxe_tier >= r['tier']:
                return "Sudah punya tier ini atau lebih."
            return self._do_craft(r, set_pickaxe=r['tier'])
        si = idx - len(PICKAXE_RECIPES) - 1   # 6→0, 7→1, …
        if 0 <= si < len(SWORD_RECIPES):
            r = SWORD_RECIPES[si]
            if s.sword_id == r['id']:
                return "Sudah punya pedang ini."
            return self._do_craft(r, set_sword=r['id'])
        return ''

    def _do_craft(self, r: dict, set_pickaxe: int = None, set_sword: str = None) -> str:
        s = self.state
        if s.gold < r['cost_gold']:
            return f"Gold kurang ({r['cost_gold']}G)."
        for k, v in r['needs'].items():
            if s.inventory.get(k, 0) < v:
                return f"Bahan kurang: butuh {k}×{v}."
        # Konsumsi
        s.gold -= r['cost_gold']
        for k, v in r['needs'].items():
            s.inventory[k] -= v
        if set_pickaxe is not None:
            s.pickaxe_tier = set_pickaxe
        if set_sword is not None:
            s.sword_id = set_sword
        self._render_panel('crafting')
        return f"Berhasil membuat {r['name']}!"

    def close_all(self):
        self._set_dialog_visible(False)
        self._set_panel_visible(False)
        self.close_pie()
        self._panel_name = None
        self.mode = 'hud'

    # ─── ACTION QUEUE INDICATOR ─────────────────────────────
    def set_queue_count(self, n: int):
        self._queue_txt.text = f'[ANT:{n}] C=jalan' if n > 0 else ''

    # ─── PIE MENU (FreeSO VMThread.ActionStrings + MotiveAdChanges) ─
    def _build_pie_menu(self):
        BG = color.rgb(12, 6, 28, 235)
        BD = color.rgb(140, 80, 200, 220)
        self._pie_bg     = _ui(scale=(0.45, 0.32), position=(-0.14, -0.10), color=BG)
        self._pie_border = _ui(scale=(0.452, 0.322), position=(-0.14, -0.10), color=BD)
        self._pie_title  = _txt('', pos=(-0.34, 0.040), scale=0.90,
                                col=color.rgb(245, 215, 80))
        self._pie_items  = [
            _txt('', pos=(-0.34, 0.010 - i * 0.030), scale=0.80, col=color.white)
            for i in range(6)
        ]
        self._pie_fx     = _txt('', pos=(-0.34, -0.200), scale=0.72,
                                col=color.rgb(127, 220, 255))
        self._pie_hint   = _txt('[</> ] Pilih  [SPACE] OK  [ESC] Batal',
                                pos=(-0.34, -0.240), scale=0.65,
                                col=color.rgb(160, 140, 200))
        self._pie_hint.origin = (0, 0)
        self._set_pie_visible(False)

        self._pie_options:  list = []
        self._pie_selected: int  = 0
        self._pie_npc_id:   str  = ''
        self._pie_callback       = None

    def _set_pie_visible(self, v: bool):
        for e in [self._pie_bg, self._pie_border, self._pie_title,
                  self._pie_fx, self._pie_hint] + self._pie_items:
            e.enabled = v

    def open_pie_menu(self, npc_id: str, options: list, callback):
        """Open pie menu. options = [(action, label, available, effects_str), ...]"""
        self._pie_npc_id   = npc_id
        self._pie_options  = options
        self._pie_selected = 0
        self._pie_callback = callback
        self.mode = 'pie'
        self._set_pie_visible(True)
        self._refresh_pie_ui()

    def navigate_pie(self, delta: int):
        if not self._pie_options:
            return
        self._pie_selected = (self._pie_selected + delta) % len(self._pie_options)
        self._refresh_pie_ui()

    def confirm_pie(self):
        if not self._pie_options:
            return
        action, _, available, _ = self._pie_options[self._pie_selected]
        if available and self._pie_callback:
            cb  = self._pie_callback
            nid = self._pie_npc_id
            self.close_pie()
            cb(nid, action)

    def close_pie(self):
        self._set_pie_visible(False)
        self._pie_options  = []
        self._pie_callback = None
        if self.mode == 'pie':
            self.mode = 'hud'

    def _refresh_pie_ui(self):
        from .data import HUMAN_NPCS, SUPERNATURAL_NPCS, ANIMAL_NPCS
        all_d = {**HUMAN_NPCS, **SUPERNATURAL_NPCS, **ANIMAL_NPCS}
        # Menu perabot mengirim id 'obj:<Nama>' — pakai nama itu apa adanya,
        # jangan cari di daftar NPC (dulu judulnya tampil sebagai 'obj:12').
        if self._pie_npc_id.startswith('obj:'):
            self._pie_title.text = f">> {self._pie_npc_id[4:]}"
        else:
            npc = all_d.get(self._pie_npc_id, {})
            self._pie_title.text = f">> {npc.get('name', self._pie_npc_id)}"

        for i, item_ent in enumerate(self._pie_items):
            if i < len(self._pie_options):
                _, label, available, effects = self._pie_options[i]
                prefix  = '>' if i == self._pie_selected else ' '
                avail_s = '' if available else ' [terkunci]'
                item_ent.text  = f'{prefix} [{i+1}] {label}{avail_s}'
                if not available:
                    item_ent.color = color.rgb(100, 80, 120)
                elif i == self._pie_selected:
                    item_ent.color = color.rgb(245, 215, 80)
                else:
                    item_ent.color = color.rgb(200, 185, 230)
            else:
                item_ent.text = ''

        # Effects preview for selected option (FreeSO MotiveAdChanges)
        if self._pie_options:
            _, _, _, effects = self._pie_options[self._pie_selected]
            self._pie_fx.text = f'Efek: {effects}' if effects else ''
