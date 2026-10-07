"""icons_weapons.py — Ikon senjata pedang 64px prosedural (keluarga weapons).

Meniru pola tools/make_item_icons.py: render 4x (supersample) lalu LANCZOS ke
64px untuk tepi mulus. Palet MUTED ala Disco Elysium x Project Zomboid (rendah
saturasi, earthy), outline gelap ~x0.55, sedikit highlight kiri-atas.

Tiap pedang digambar diagonal: pommel/gagang kiri-bawah, ujung bilah kanan-atas.
Output PNG RGBA 64x64 transparan ke assets/textures/<id>.png.

Pakai: python tools/icons_weapons.py
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent.parent / 'assets' / 'textures'
OUT.mkdir(parents=True, exist_ok=True)
SS = 4                 # supersample
S = 64 * SS


def _new():
    return Image.new('RGBA', (S, S), (0, 0, 0, 0))


def _save(img, name):
    img = img.resize((64, 64), Image.LANCZOS)
    img.save(OUT / f'{name}.png')
    return name


def _shade(c, f):
    r, g, b = c[:3]
    a = c[3] if len(c) > 3 else 255
    return (max(0, min(255, int(r * f))),
            max(0, min(255, int(g * f))),
            max(0, min(255, int(b * f))),
            a)


def _poly_outline(d, pts, col, ow=2 * SS):
    """Polygon dengan garis tepi gelap supaya bentuk terbaca."""
    d.polygon(pts, fill=col, outline=_shade(col, 0.55))
    if ow > 0:
        d.line(pts + [pts[0]], fill=_shade(col, 0.50), width=ow, joint='curve')


def _line_quad(p0, p1, w):
    """Quad (4 titik) tegak lurus sepanjang ruas p0->p1 dengan lebar w."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L * (w / 2), dx / L * (w / 2)
    return [(p0[0] + nx, p0[1] + ny), (p1[0] + nx, p1[1] + ny),
            (p1[0] - nx, p1[1] - ny), (p0[0] - nx, p0[1] - ny)]


def _blade_glow(img, p0, p1, w, col):
    """Glow lembut sepanjang bilah (untuk mithril)."""
    gl = Image.new('RGBA', img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(gl)
    gd.polygon(_line_quad(p0, p1, w), fill=col + (130,))
    gl = gl.filter(ImageFilter.GaussianBlur(5 * SS))
    img.alpha_composite(gl)


def _highlight_line(img, p0, p1, w):
    """Garis kilau tipis kiri-atas di permukaan bilah."""
    hl = Image.new('RGBA', img.size, (0, 0, 0, 0))
    hd = ImageDraw.Draw(hl)
    # geser sedikit ke sisi kiri-atas bilah
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L * (w * 0.22), dx / L * (w * 0.22)
    a = (p0[0] + nx + dx * 0.12, p0[1] + ny + dy * 0.12)
    b = (p1[0] + nx - dx * 0.10, p1[1] + ny - dy * 0.10)
    hd.line([a, b], fill=(255, 255, 255, 90), width=max(1, int(w * 0.18)))
    hl = hl.filter(ImageFilter.GaussianBlur(2 * SS))
    img.alpha_composite(hl)


def sword(blade_col, guard_col, grip_col, *, glow=None):
    """Gambar pedang diagonal.

    blade_col : warna bilah
    guard_col : warna guard (palang) & pommel
    grip_col  : warna gagang
    glow      : warna glow lembut sepanjang bilah (opsional, mis. mithril)
    """
    img = _new()
    d = ImageDraw.Draw(img)

    # Titik acuan (kiri-bawah -> kanan-atas)
    pommel = (S * 0.20, S * 0.82)            # ujung gagang bawah
    grip_top = (S * 0.34, S * 0.66)          # batas gagang/guard
    blade_base = (S * 0.42, S * 0.58)        # pangkal bilah di atas guard
    tip = (S * 0.84, S * 0.16)               # ujung lancip bilah

    grip_w = 7 * SS
    blade_w = 14 * SS

    # ── Bilah (badan) ──
    if glow is not None:
        _blade_glow(img, blade_base, tip, blade_w + 6 * SS, glow)

    # bentuk bilah: pangkal lebar, ujung lancip (tetra/lozenge)
    dx, dy = tip[0] - blade_base[0], tip[1] - blade_base[1]
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L * (blade_w / 2), dx / L * (blade_w / 2)
    base_l = (blade_base[0] + nx, blade_base[1] + ny)
    base_r = (blade_base[0] - nx, blade_base[1] - ny)
    # sedikit pendek dari tip agar lancip bersih
    near_tip = (tip[0] - dx * 0.05, tip[1] - dy * 0.05)
    d.polygon([base_l, base_r, near_tip, tip], fill=blade_col,
              outline=_shade(blade_col, 0.55))

    # bevel: sisi kanan-bawah bilah sedikit lebih gelap (cahaya dari kiri-atas)
    mid_base = ((base_l[0] + base_r[0]) / 2, (base_l[1] + base_r[1]) / 2)
    d.polygon([mid_base, base_r, near_tip, tip], fill=_shade(blade_col, 0.90),
              outline=None)
    # ridge tengah bilah: garis tipis terang sebagai punggung bilah
    ridge_w = max(1, int(2 * SS))
    d.line([mid_base, near_tip], fill=_shade(blade_col, 1.18), width=ridge_w)

    # ── Guard (palang melintang) ──
    gdx, gdy = blade_base[0] - grip_top[0], blade_base[1] - grip_top[1]
    gl = math.hypot(gdx, gdy) or 1.0
    # arah melintang (tegak lurus arah bilah/gagang)
    gnx, gny = -(tip[1] - blade_base[1]) / L, (tip[0] - blade_base[0]) / L
    gcx = (grip_top[0] + blade_base[0]) / 2
    gcy = (grip_top[1] + blade_base[1]) / 2
    gh = 13 * SS   # setengah panjang guard
    gw = 5 * SS    # tebal guard
    ga = (gcx + gnx * gh, gcy + gny * gh)
    gb = (gcx - gnx * gh, gcy - gny * gh)
    guard_quad = _line_quad(ga, gb, gw)
    d.polygon(guard_quad, fill=guard_col, outline=_shade(guard_col, 0.5))
    # ujung guard sedikit bulat
    for end in (ga, gb):
        r = gw * 0.55
        d.ellipse([end[0] - r, end[1] - r, end[0] + r, end[1] + r],
                  fill=guard_col, outline=_shade(guard_col, 0.5))

    # ── Gagang ──
    grip_quad = _line_quad(pommel, grip_top, grip_w)
    d.polygon(grip_quad, fill=grip_col, outline=_shade(grip_col, 0.5))
    # lilitan gagang (garis melintang gelap)
    for t in (0.30, 0.50, 0.70):
        wx = pommel[0] + (grip_top[0] - pommel[0]) * t
        wy = pommel[1] + (grip_top[1] - pommel[1]) * t
        wnx, wny = -( grip_top[1] - pommel[1]), (grip_top[0] - pommel[0])
        wl = math.hypot(wnx, wny) or 1.0
        wnx, wny = wnx / wl * (grip_w * 0.55), wny / wl * (grip_w * 0.55)
        d.line([(wx + wnx, wy + wny), (wx - wnx, wy - wny)],
               fill=_shade(grip_col, 0.62), width=max(1, int(2 * SS)))

    # ── Pommel (bulatan ujung gagang) ──
    pr = 6 * SS
    d.ellipse([pommel[0] - pr, pommel[1] - pr, pommel[0] + pr, pommel[1] + pr],
              fill=guard_col, outline=_shade(guard_col, 0.5))

    # ── Highlight kilau bilah ──
    _highlight_line(img, blade_base, near_tip, blade_w)
    # titik kilau kecil di pommel kiri-atas
    hl = Image.new('RGBA', img.size, (0, 0, 0, 0))
    hd = ImageDraw.Draw(hl)
    hd.ellipse([pommel[0] - pr * 0.8, pommel[1] - pr * 0.8,
                pommel[0], pommel[1]], fill=(255, 255, 255, 70))
    hl = hl.filter(ImageFilter.GaussianBlur(2 * SS))
    img.alpha_composite(hl)

    return img


def main():
    made = []
    # sword_kayu: bilah kayu coklat muda, guard & gagang kayu lebih gelap
    made.append(_save(
        sword((170, 135, 90), (120, 92, 58), (108, 80, 50)),
        'sword_kayu'))
    # sword_besi: bilah baja abu, guard besi gelap, gagang coklat dibalut
    made.append(_save(
        sword((172, 180, 190), (96, 100, 108), (118, 86, 56)),
        'sword_besi'))
    # sword_emas: bilah emas muted, guard/pommel emas tua, gagang merah-coklat
    made.append(_save(
        sword((210, 180, 90), (158, 124, 48), (122, 60, 48)),
        'sword_emas'))
    # sword_mithril: bilah biru-perak pucat + glow lembut, gagang gelap
    made.append(_save(
        sword((150, 195, 210), (90, 110, 128), (70, 74, 86),
              glow=(170, 210, 230)),
        'sword_mithril'))

    print(f"[icons_weapons] {len(made)} ikon -> {OUT}")
    print("  " + ", ".join(made))


if __name__ == '__main__':
    main()
