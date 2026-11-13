"""mob_rupa.py — mob penyerang yang terbaca: papan nama + HP, aura, lingkar
ancaman, dan angka kerusakan.

Keluhan pemilik (3 Nov 2026): "mobs yang sifatnya menyerang diperbagus".
Tangkapan deretan tujuh mob + bos di gua menunjukkan empat cacat rupa:

  1. Bilah HP adalah dua kubus tipis yang diparent ke aktor. mob_gerak
     memutar aktor menghadap pemain, jadi bilahnya ikut berputar dan
     terbaca sebagai garis miring, bukan bilah.
  2. Mob tenggelam di lantai gua: genderuwo gelap di atas gelap, tikus
     sekecil kerikil. Tidak ada yang memisahkan mob dari lantai.
  3. Ancang-ancang serangan (windup) hanya kemerahan + condong. Pemain tidak
     tahu SEJAUH MANA pukulan itu kena -- padahal mob.py memang memeriksa
     radius (atk_r * 1,35), jadi mengelak itu mungkin, tapi tidak terlihat.
  4. Tidak ada angka kerusakan: pukulan ke dan dari mob terasa hampa.

Yang dipasang di sini, semuanya per aktor dan dibuang bersama aktornya:

  papan    billboard: nama jenis + bilah HP bersudut bulat (tetap memakai
           atribut _hp_bar/_bg_bar supaya kode lama yang mengecilkan dan
           menyembunyikannya tetap bekerja)
  aura     lingkaran gelap-merah lembut di kaki: memisahkan mob dari lantai
           dan langsung terbaca "musuh" (warga dan hewan tidak punya)
  ancaman  cincin merah yang MENGISI selama windup sampai jari-jari pukulan
           sungguhan; keluar dari cincin = selamat
  angka    angka kerusakan melayang naik lalu pudar (putih ke mob, merah ke
           pemain)
"""
from __future__ import annotations

import math

from ursina import Entity, Text, Texture, color, destroy

_TEX: dict = {}


def _tex(nama):
    if nama in _TEX:
        return _TEX[nama]
    tex = None
    try:
        from PIL import Image, ImageDraw, ImageFilter
        n = 128
        img = Image.new('RGBA', (n, n), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        if nama == 'aura':
            # Bercak radial lembut: pekat di tengah, pudar ke tepi.
            for i in range(32, 0, -1):
                r = n / 2 * i / 32
                a = int(150 * (1 - i / 32) ** 0.6)
                d.ellipse([n / 2 - r, n / 2 - r, n / 2 + r, n / 2 + r], fill=(255, 255, 255, a))
        elif nama == 'cincin':
            d.ellipse([6, 6, n - 6, n - 6], outline=(255, 255, 255, 255), width=7)
            img = img.filter(ImageFilter.GaussianBlur(1.0))
        elif nama == 'isi':
            d.ellipse([6, 6, n - 6, n - 6], fill=(255, 255, 255, 110))
        tex = Texture(img)
        tex.filtering = 'bilinear'
    except Exception:
        tex = None
    _TEX[nama] = tex
    return tex


NAMA = {
    'kelelawar': 'Kelelawar', 'tikus_gua': 'Tikus Gua', 'genderuwo': 'Genderuwo',
    'banaspati': 'Banaspati', 'kuntilanak': 'Kuntilanak', 'leak': 'Leak',
    'pocong': 'Pocong', 'bhutakala': 'Bhutakala',
}

# Warna aura per jenis: watak makhluknya, tetap condong merah (= bahaya).
_AURA = {
    'banaspati': (255, 120, 40), 'kuntilanak': (190, 120, 255), 'leak': (120, 255, 150),
    'pocong': (220, 220, 200), 'bhutakala': (255, 60, 30),
}


def pasang(actor, hp_y, sc=1.0):
    """Ganti bilah kubus lama dengan papan billboard + pasang aura & cincin."""
    from . import panel_kartu as PK
    for lama in ('_hp_bar', '_bg_bar'):
        e = getattr(actor, lama, None)
        if e is not None:
            try:
                destroy(e)
            except Exception:
                pass
    W = 1.0 * sc
    H = 0.13
    papan = Entity(parent=actor, position=(0, hp_y, 0), billboard=True)
    papan.setLightOff()
    t_bilah = PK.kotak_tex(W / H, 0.5)
    actor._bg_bar = Entity(parent=papan, model='quad', texture=t_bilah, scale=(W + 0.06, H + 0.05),
                           color=color.rgba(12, 12, 18, 220), z=0.01)
    actor._hp_bar = Entity(parent=papan, model='quad', texture=t_bilah, scale=(W, H),
                           origin=(-0.5, 0), x=-W / 2, color=color.rgb(226, 56, 60))
    for e in (actor._bg_bar, actor._hp_bar):
        e.setLightOff()
    nama = NAMA.get(getattr(actor, 'kind', ''), getattr(actor, 'kind', ''))
    if getattr(actor, 'is_boss', False):
        nama = 'Bhutakala, Penguasa Gua'
    actor._papan_nama = Text(nama, parent=papan, y=0.24, scale=6 * (1.2 if sc > 1 else 1.0),
                             origin=(0, 0), font='Montserrat-Bold.ttf',
                             color=color.rgb(255, 214, 190))
    actor._papan = papan
    actor._hp_w = W

    from .config import GROUND_H
    # Di permukaan lantai, bukan di y=0 aktor: lantai gua duduk di GROUND_H,
    # dan versi pertama yang ditaruh di 0,04 tersembunyi di bawahnya.
    y0 = (GROUND_H + 0.03) / max(0.01, sc)
    rgb = _AURA.get(getattr(actor, 'kind', ''), (200, 40, 40))
    actor._aura = Entity(parent=actor, model='quad', texture=_tex('aura'), rotation_x=90,
                         y=y0, scale=1.9, color=color.rgba(*rgb, 170))
    actor._cincin = Entity(parent=actor, model='quad', texture=_tex('cincin'), rotation_x=90,
                           y=y0 + 0.02, scale=1, color=color.rgba(255, 60, 50, 230), enabled=False)
    actor._cincin_isi = Entity(parent=actor, model='quad', texture=_tex('isi'), rotation_x=90,
                               y=y0 + 0.01, scale=0.01, color=color.rgba(255, 40, 30, 200),
                               enabled=False)
    for e in (actor._aura, actor._cincin, actor._cincin_isi):
        e.setLightOff()
        e.setDepthWrite(False)


def segarkan(actor, dt):
    """Per frame: lebar bilah dari HP, cincin ancaman dari windup."""
    from .config import TILE_SIZE as TS
    if getattr(actor, '_papan', None) is None:
        return
    mx = max(1, actor.mob_spec.get('max_hp', 1) or 1)
    r = max(0.0, min(1.0, actor.hp / mx))
    actor._hp_bar.scale_x = max(0.001, actor._hp_w * r)
    actor._hp_bar.color = (color.rgb(226, 56, 60) if r > 0.35
                           else color.rgb(255, 150, 60))
    windup = getattr(actor, 'windup_ms', 0) or 0
    if windup > 0 and not getattr(actor, 'dying', False):
        total = max(1, getattr(actor, 'windup_total', 1) or 1)
        k = 1.0 - windup / total
        # Diameter dunia = 2 x radius kena (atk_r * 1,35 petak), dibagi skala
        # aktor karena cincin anak aktor.
        sk = max(0.01, float(actor.scale_x))
        d = 2 * actor.atk_r * 1.35 * TS / sk
        actor._cincin.enabled = actor._cincin_isi.enabled = True
        actor._cincin.scale = d
        actor._cincin_isi.scale = max(0.01, d * k)
        denyut = 0.65 + 0.35 * math.sin(k * math.pi * 6)
        actor._cincin.color = color.rgba(255, 60, 50, int(150 + 100 * denyut))
    else:
        actor._cincin.enabled = actor._cincin_isi.enabled = False
    if getattr(actor, 'dying', False):
        for nama in ('_aura', '_papan'):
            e = getattr(actor, nama, None)
            if e is not None:
                e.enabled = False


# ── angka kerusakan ───────────────────────────────────────────────────
_ANGKA: list = []


def angka(pos, nilai, ke_pemain=False):
    """Angka kerusakan melayang di posisi dunia `pos`."""
    try:
        from ursina import scene
        # parent=scene: Text bawaan Ursina menempel ke camera.ui, dan angka
        # yang diberi posisi dunia di sana jatuh jauh di luar layar.
        t = Text(f'-{int(round(nilai))}', parent=scene, position=(pos[0], pos[1], pos[2]),
                 billboard=True,
                 scale=14 if ke_pemain else 12, origin=(0, 0), font='Montserrat-Bold.ttf',
                 color=color.rgb(255, 80, 70) if ke_pemain else color.rgb(255, 246, 220))
        t.setLightOff()
        t.setDepthTest(False)
        t.setBin('fixed', 50)
        rgb = (255, 80, 70) if ke_pemain else (255, 246, 220)
        _ANGKA.append([t, 0.0, pos[0], pos[1], pos[2], rgb])
    except Exception:
        pass


def tick_angka(dt):
    for rec in list(_ANGKA):
        t, u, x, y, z, rgb = rec
        u += dt
        rec[1] = u
        if u >= 0.9 or not t:
            try:
                destroy(t)
            except Exception:
                pass
            _ANGKA.remove(rec)
            continue
        t.position = (x, y + 0.9 * u, z)
        # Bukan `t.alpha`: setter Ursina itu membaca .h milik Color, dan warna
        # di sini Vec4 -- jebakan yang sama dengan tebing tembus (world.py).
        a = max(0.0, 1.0 - max(0.0, u - 0.45) / 0.45)
        t.color = color.rgba(*rgb, int(255 * a))
