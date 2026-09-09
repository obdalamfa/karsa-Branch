"""
naga_model.py — Naga Indosiar: naga emas Jawa prosedural.

Referensi visual: logo Indosiar — ular naga emas meringkuk dengan
kepala besar terbuka, tanduk banyak, kumis panjang, sirip punggung,
badan melingkar dari kepala tinggi ke ekor menggulung di bawah.
"""
from ursina import Entity, color
import math


def _c(r, g, b):   return color.rgb(r, g, b)
def _ca(r,g,b,a):  return color.rgba(r,g,b,a)

# ── Palet Naga Indosiar ──────────────────────────────────────────────────────
C_GOLD_BRIGHT  = _c(245, 210,  55)   # emas kilap (highlight)
C_GOLD_MID     = _c(215, 172,  38)   # emas utama
C_GOLD_DEEP    = _c(178, 130,  22)   # emas tua (bayangan)
C_BELLY        = _c(238, 208, 120)   # perut lebih terang
C_SCALE_DARK   = _c(148, 108,  18)   # sisik garis gelap
C_HORN         = _c(235, 225, 185)   # tanduk gading
C_WHISKER      = _c(252, 238, 180)   # kumis putih-emas
C_EYE_WHITE    = _c(240, 235, 215)   # sklera
C_EYE_IRIS     = _c(255,  88,  15)   # mata api oranye
C_EYE_PUPIL    = _c( 28,  18,   8)   # pupil gelap
C_TOOTH        = _c(248, 242, 222)   # gigi gading
C_TONGUE       = _c(205,  38,  38)   # lidah merah
C_FIN          = _c(198, 145,  22)   # sirip punggung (emas gelap)
C_CLAW         = _c(228, 218, 175)   # cakar gading

# ── Jalur badan (S-curve melingkar, Y=atas) ─────────────────────────────────
# Setiap titik: (x, y, z)  — koordinat lokal relatif ke actor root
_SPINE = [
    # Kepala (paling atas)
    ( 0.00, 4.60,  0.90),
    # Leher
    ( 0.00, 4.00,  0.60),
    ( 0.00, 3.45,  0.28),
    # Bahu / punggung atas melengkung ke kanan
    ( 0.22, 2.90,  0.00),
    ( 0.52, 2.42, -0.18),
    ( 0.72, 2.00, -0.38),
    ( 0.80, 1.60, -0.55),
    # Perut tengah melengkung ke kiri
    ( 0.65, 1.25, -0.72),
    ( 0.35, 0.98, -0.85),
    ( 0.00, 0.80, -0.90),
    (-0.32, 0.65, -0.82),
    (-0.55, 0.55, -0.58),
    # Ekor bawah kembali ke kanan
    (-0.62, 0.50, -0.28),
    (-0.52, 0.45,  0.05),
    (-0.28, 0.42,  0.30),
    (-0.02, 0.40,  0.48),
    ( 0.18, 0.38,  0.55),
    # Ujung ekor
    ( 0.28, 0.36,  0.58),
]

# Lebar segmen (menurun dari leher ke ujung ekor)
_WIDTHS = [0.92, 0.88, 0.84, 0.80, 0.76, 0.72, 0.68,
           0.62, 0.56, 0.50, 0.44, 0.38, 0.32, 0.26,
           0.20, 0.14, 0.09, 0.05]

# Segmen dengan belly (warna perut lebih terang) = indeks
_BELLY_SEGS = {4, 5, 6, 7, 8, 9, 10, 11, 12}


def _soft_cube():
    try:
        from .meshes import soft_cube_mesh
        return soft_cube_mesh()
    except Exception:
        return 'cube'


def _part(actor, model, pos, scale, col, **kw):
    e = Entity(parent=actor, model=model, position=pos,
               scale=scale, color=col, **kw)
    try: e.setLightOff()
    except Exception: pass
    return e


def _look_at(p0, p1):
    """Rotasi Y dan X agar menghadap dari p0 ke p1."""
    dx = p1[0] - p0[0];  dy = p1[1] - p0[1];  dz = p1[2] - p0[2]
    dist_xz = math.sqrt(dx*dx + dz*dz)
    ry = math.degrees(math.atan2(dx, dz))
    rx = -math.degrees(math.atan2(dy, max(dist_xz, 0.0001)))
    return (rx, ry, 0)


def build_naga(actor):
    """
    Rakit Naga Indosiar sebagai child-part pada actor (Entity).
    Actor dijadikan root tak terlihat; semua bagian adalah Entity anak.
    """
    sc_mesh = _soft_cube()

    actor.model  = 'cube'
    actor.color  = color.clear
    actor.scale  = 1.0

    # ── BADAN (segmen tulang punggung) ────────────────────────────────────────
    for i, (x, y, z) in enumerate(_SPINE[1:], start=1):
        w = _WIDTHS[min(i, len(_WIDTHS)-1)]
        # Arah ke segmen berikutnya untuk rotasi
        if i < len(_SPINE) - 1:
            rot = _look_at(_SPINE[i], _SPINE[i+1])
        else:
            rot = _look_at(_SPINE[i-1], _SPINE[i])

        col_body = C_BELLY if i in _BELLY_SEGS else C_GOLD_MID

        # Segmen utama
        _part(actor, sc_mesh, (x, y, z), (w, w * 0.92, w * 1.05), col_body,
              rotation=rot)

        # Overlay sisik — garis gelap tipis di punggung tiap segmen
        if i < 14:
            sx2 = w * 0.72;  sy2 = w * 0.18;  sz2 = w * 1.10
            _part(actor, sc_mesh, (x, y + w*0.42, z), (sx2, sy2, sz2),
                  C_SCALE_DARK, rotation=rot)

        # Sirip punggung — "paku" segitiga emas gelap
        if 1 <= i <= 10 and i % 2 == 0:
            fin_h = w * 0.65 * (1.0 - i * 0.06)
            _part(actor, sc_mesh, (x, y + w*0.48 + fin_h*0.5, z),
                  (w*0.10, fin_h, w*0.40), C_FIN, rotation=rot)

    # ── KEPALA ────────────────────────────────────────────────────────────────
    hx, hy, hz = _SPINE[0]
    hs = 1.05   # skala dasar kepala

    # Tengkorak utama — memanjang horizontal (seperti naga Cina)
    _part(actor, sc_mesh, (hx, hy, hz),          (hs*1.05, hs*0.78, hs*1.35), C_GOLD_MID)
    # Dahi menonjol
    _part(actor, sc_mesh, (hx, hy+hs*0.30, hz-hs*0.10), (hs*0.88, hs*0.35, hs*0.90), C_GOLD_BRIGHT)
    # Pipi (melebar)
    for sx in (-1, 1):
        _part(actor, sc_mesh, (hx + sx*hs*0.48, hy, hz),
              (hs*0.30, hs*0.62, hs*0.95), C_GOLD_MID)

    # Moncong atas (snout) — panjang ke depan
    _part(actor, sc_mesh, (hx, hy-hs*0.08, hz+hs*0.72),
          (hs*0.82, hs*0.50, hs*0.85), C_GOLD_MID)
    # Bibir atas
    _part(actor, sc_mesh, (hx, hy-hs*0.27, hz+hs*0.98),
          (hs*0.76, hs*0.16, hs*0.55), C_GOLD_BRIGHT)

    # Rahang bawah — lebih rendah (mulut terbuka)
    jaw_y = hy - hs*0.52
    _part(actor, sc_mesh, (hx, jaw_y, hz+hs*0.55),
          (hs*0.78, hs*0.38, hs*0.90), C_GOLD_MID)
    _part(actor, sc_mesh, (hx, jaw_y-hs*0.12, hz+hs*0.88),
          (hs*0.68, hs*0.18, hs*0.55), C_GOLD_DEEP)

    # Gigi atas — taring besar + gigi kecil
    for i, (gx_off, gz_off, gw, gh) in enumerate([
        (-0.28, 1.08, 0.10, 0.34),   # taring kiri atas
        ( 0.28, 1.08, 0.10, 0.34),   # taring kanan atas
        (-0.14, 1.06, 0.07, 0.22),
        ( 0.14, 1.06, 0.07, 0.22),
        ( 0.00, 1.05, 0.07, 0.18),
    ]):
        _part(actor, sc_mesh,
              (hx + gx_off*hs, hy - hs*0.28 - gh*hs*0.5, hz + gz_off*hs),
              (gw*hs, gh*hs, gw*hs), C_TOOTH)

    # Gigi bawah — taring bawah
    for gx_off, gz_off, gw, gh in [
        (-0.22, 0.90, 0.09, 0.28),
        ( 0.22, 0.90, 0.09, 0.28),
        ( 0.00, 0.88, 0.07, 0.18),
    ]:
        _part(actor, sc_mesh,
              (hx + gx_off*hs, jaw_y + gh*hs*0.5, hz + gz_off*hs),
              (gw*hs, gh*hs, gw*hs), C_TOOTH)

    # Lidah bercabang — menonjol keluar
    _part(actor, sc_mesh, (hx, jaw_y+hs*0.08, hz+hs*1.22),
          (hs*0.28, hs*0.06, hs*0.50), C_TONGUE)
    for sx in (-1, 1):
        _part(actor, sc_mesh,
              (hx + sx*hs*0.16, jaw_y+hs*0.08, hz+hs*1.48),
              (hs*0.08, hs*0.05, hs*0.28), C_TONGUE)

    # ── MATA ─────────────────────────────────────────────────────────────────
    for sx in (-1, 1):
        ex = hx + sx * hs * 0.44
        ey = hy + hs * 0.12
        ez = hz + hs * 0.42
        _part(actor, 'sphere', (ex, ey, ez),     (hs*0.20, hs*0.20, hs*0.20), C_EYE_WHITE)
        _part(actor, 'sphere', (ex, ey, ez+hs*0.07), (hs*0.14, hs*0.16, hs*0.10), C_EYE_IRIS)
        _part(actor, 'sphere', (ex, ey, ez+hs*0.11), (hs*0.07, hs*0.09, hs*0.06), C_EYE_PUPIL)
        # Alis tebal (tonjolan tulang alis)
        _part(actor, sc_mesh, (ex, ey+hs*0.16, ez),
              (hs*0.22, hs*0.08, hs*0.32), C_GOLD_DEEP)

    # ── TANDUK (ciri khas naga Jawa/Cina — banyak, melengkung) ───────────────
    horn_defs = [
        # (ox, oy, oz, sw, sh, sd, rx, ry, rz) — offset dari pusat kepala
        (-0.30, 0.50,  0.00,  0.12, 0.72, 0.10,  15, -25, 0),   # tanduk kiri utama
        ( 0.30, 0.50,  0.00,  0.12, 0.72, 0.10,  15,  25, 0),   # tanduk kanan utama
        (-0.22, 0.38, -0.20,  0.09, 0.55, 0.09,   5, -40, 0),   # tanduk kiri belakang
        ( 0.22, 0.38, -0.20,  0.09, 0.55, 0.09,   5,  40, 0),   # tanduk kanan belakang
        ( 0.00, 0.52, -0.05,  0.10, 0.48, 0.10,  20,   0, 0),   # tanduk tengah
        (-0.38, 0.32,  0.10,  0.07, 0.35, 0.07,  -5, -55, 10),  # tanduk kecil kiri
        ( 0.38, 0.32,  0.10,  0.07, 0.35, 0.07,  -5,  55,-10),  # tanduk kecil kanan
    ]
    for ox, oy, oz, sw, sh, sd, rx, ry, rz in horn_defs:
        _part(actor, sc_mesh,
              (hx + ox*hs, hy + oy*hs, hz + oz*hs),
              (sw*hs, sh*hs, sd*hs), C_HORN, rotation=(rx, ry, rz))

    # Crest/mahkota antara tanduk — tonjolan tulang emas
    _part(actor, sc_mesh, (hx, hy+hs*0.55, hz-hs*0.08),
          (hs*0.18, hs*0.22, hs*0.55), C_GOLD_BRIGHT)

    # ── KUMIS PANJANG (ciri khas naga Asia) ──────────────────────────────────
    whisker_defs = [
        # (ox_start, oy_start, oz_start, ox_end, oy_end, oz_end)
        # Kumis atas kiri (panjang, melengkung ke luar)
        (-0.44, 0.05, 0.95,  -1.10, -0.30, 1.55),
        (-0.44, 0.05, 0.95,  -1.50,  0.10, 1.20),
        # Kumis atas kanan
        ( 0.44, 0.05, 0.95,   1.10, -0.30, 1.55),
        ( 0.44, 0.05, 0.95,   1.50,  0.10, 1.20),
        # Kumis dagu (panjang ke bawah)
        (-0.18,-0.35, 0.80,  -0.35, -1.00, 1.10),
        ( 0.18,-0.35, 0.80,   0.35, -1.00, 1.10),
    ]
    for x0, y0, z0, x1, y1, z1 in whisker_defs:
        mx  = (x0 + x1) * 0.5;  my = (y0 + y1) * 0.5;  mz = (z0 + z1) * 0.5
        dx  = x1-x0; dy = y1-y0; dz = z1-z0
        L   = max(math.sqrt(dx*dx + dy*dy + dz*dz), 0.01)
        ry  = math.degrees(math.atan2(dx, dz))
        rx  = -math.degrees(math.atan2(dy, max(math.sqrt(dx*dx+dz*dz), 0.0001)))
        _part(actor, sc_mesh,
              (hx + mx*hs, hy + my*hs, hz + mz*hs),
              (hs*0.055, hs*0.055, L*hs), C_WHISKER,
              rotation=(rx, ry, 0))

    # ── CAKAR DEPAN ───────────────────────────────────────────────────────────
    # Kaki depan kecil — khas naga Cina (tidak besar)
    arm_data = [
        # (badan_idx, side_x, arm_dx, arm_dy)
        (4,  0.72,  0.28, -0.18),  # lengan kiri (badan ~titik 4)
        (4, -0.72, -0.28, -0.18),  # lengan kanan
    ]
    for seg_i, side_x, adx, ady in arm_data:
        bx, by, bz = _SPINE[seg_i]
        w = _WIDTHS[seg_i]
        # Lengan atas
        ax = bx + side_x * w * 0.52;  ay = by + ady * w;  az = bz
        _part(actor, sc_mesh, (ax, ay, az), (w*0.32, w*0.28, w*0.70),
              C_GOLD_MID, rotation=(0, 0, side_x * 25))
        # Lengan bawah
        ax2 = ax + adx * w * 0.6;  ay2 = ay - w * 0.55
        _part(actor, sc_mesh, (ax2, ay2, az), (w*0.24, w*0.50, w*0.24),
              C_GOLD_MID, rotation=(15, 0, side_x * 15))
        # Cakar (3 jari)
        for fi in range(3):
            fx = ax2 + (fi - 1) * w * 0.14
            _part(actor, sc_mesh,
                  (fx, ay2 - w*0.38, az + w*0.28),
                  (w*0.07, w*0.35, w*0.07), C_CLAW,
                  rotation=(-20, (fi-1)*15, 0))

    # ── SIRIP EKOR ────────────────────────────────────────────────────────────
    tail_tip = _SPINE[-1]
    for sx in (-1, 1):
        _part(actor, sc_mesh,
              (tail_tip[0] + sx*0.12, tail_tip[1]+0.10, tail_tip[2]),
              (0.08, 0.25, 0.35), C_FIN, rotation=(0, sx*30, sx*20))
    # Ujung ekor runcing
    _part(actor, sc_mesh, tail_tip, (0.04, 0.04, 0.32), C_GOLD_DEEP)
