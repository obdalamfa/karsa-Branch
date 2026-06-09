"""
animal_models.py — Builder hewan prosedural chibi/cute (lucu dan soft)

Gaya: kepala besar, kaki sangat pendek, mata bulat besar dengan iris berwarna,
pipi merah muda, senyum kecil, warna pastel lembut.
"""
from ursina import Entity, color
from pathlib import Path

_MODELS_DIR = Path(__file__).resolve().parent.parent / 'assets' / 'models'


def get_animal_model_file(animal_type: str):
    """Return nama model aset bila tersedia, else None."""
    for ext in ('.glb', '.obj'):
        if (_MODELS_DIR / f'animal_{animal_type}{ext}').exists():
            return f'animal_{animal_type}'
    return None


def _c(r, g, b):
    return color.rgb(r, g, b)


_BLUSH   = _c(248, 158, 165)   # pipi merah muda soft
_EYE_W   = _c(252, 252, 252)   # putih mata
_EYE_PU  = _c(22,  18,  22)    # pupil hitam


# ─── SPESIFIKASI CHIBI PER JENIS HEWAN ─────────────────────────────────────────
# Proporsi chibi: kaki pendek (leg ≤0.20), kepala besar (hsz = bw*1.05)
ANIMAL_SPECS = {
    'kucing': dict(
        body=(0.50, 0.44, 0.58), leg=0.13, legs=4,
        ear='pointy', tail='long',
        col  =_c(245, 175, 105),
        col2 =_c(88,  68,  48),
        belly=_c(255, 242, 218),
        iris =_c(60,  178,  80),
        size =0.90,
    ),
    'kelinci': dict(
        body=(0.46, 0.50, 0.46), leg=0.11, legs=4,
        ear='long', tail='puff',
        col  =_c(255, 215, 215),
        col2 =_c(95,  78,  88),
        belly=_c(255, 248, 248),
        iris =_c(210,  90, 140),
        size =0.82,
    ),
    'sapi': dict(
        body=(0.88, 0.74, 0.88), leg=0.17, legs=4,
        ear='side', tail='long', horns=True,
        col  =_c(252, 248, 238),
        col2 =_c(42,  38,  32),
        belly=_c(255, 252, 248),
        iris =_c(138, 100,  55),
        spots=True,
        size =1.10,
    ),
    'ayam': dict(
        body=(0.44, 0.46, 0.44), leg=0.13, legs=2,
        ear='none', tail='fan', beak=True, comb=True,
        col  =_c(255, 240, 162),
        col2 =_c(232,  92,  62),
        belly=_c(255, 248, 210),
        iris =_c(210, 142,  38),
        size =0.68,
    ),
    'kambing': dict(
        body=(0.58, 0.58, 0.60), leg=0.15, legs=4,
        ear='side', tail='tiny', horns=True, beard=True,
        col  =_c(222, 215, 200),
        col2 =_c(148, 130, 110),
        belly=_c(238, 232, 220),
        iris =_c(195, 172,  50),
        size =0.92,
    ),
    'bebek': dict(
        body=(0.50, 0.46, 0.50), leg=0.11, legs=2,
        ear='none', tail='up', beak=True,
        col  =_c(255, 232,  75),
        col2 =_c(240, 138,  52),
        belly=_c(255, 248, 180),
        iris =_c(198, 132,  38),
        size =0.68,
    ),
    'domba': dict(
        body=(0.72, 0.66, 0.72), leg=0.14, legs=4,
        ear='side', tail='tiny', fluffy=True,
        col  =_c(248, 248, 245),
        col2 =_c(62,  55,  52),
        belly=_c(238, 192, 192),
        iris =_c(148, 108,  72),
        size =0.98,
    ),
    'kuda': dict(
        body=(0.68, 0.72, 0.82), leg=0.24, legs=4,
        ear='pointy', tail='long', mane=True,
        col  =_c(210, 165, 105),
        col2 =_c(72,  50,  32),
        belly=_c(245, 228, 195),
        iris =_c(110,  78,  45),
        size =1.20,
    ),
    'rubah': dict(
        body=(0.50, 0.46, 0.60), leg=0.13, legs=4,
        ear='pointy', tail='bushy',
        col  =_c(238, 128,  58),
        col2 =_c(72,  50,  32),
        belly=_c(255, 248, 240),
        iris =_c(205, 132,  45),
        size =0.92,
    ),
}
_DEFAULT_SPEC = dict(
    body=(0.54, 0.50, 0.60), leg=0.16, legs=4, ear='side', tail='long',
    col=_c(185, 160, 130), col2=_c(72, 58, 45), belly=_c(210, 192, 168),
    iris=_c(110, 85, 48), size=1.0,
)

_WILD_SCALES = {
    'running_mushroom': 0.58,
    'firefly':          0.32,
    'mandrake':         0.52,
    'wild_herb':        0.50,
    'wild_berry':       0.46,
}


def _soft_cube():
    from .meshes import soft_cube_mesh
    return soft_cube_mesh()


def build_animal(actor, animal_type: str):
    """Rakit hewan chibi prosedural sebagai child-parts pada `actor`."""
    spec  = ANIMAL_SPECS.get(animal_type, _DEFAULT_SPEC)
    bw, bh, bd = spec['body']
    leg   = spec['leg']
    col   = spec['col']
    col2  = spec['col2']
    belly = spec.get('belly', col)
    iris  = spec.get('iris', _c(80, 130, 200))
    parts = []

    actor.model  = 'cube'
    actor.color  = color.clear
    actor.scale  = spec.get('size', 1.0)

    body_y = leg + bh * 0.5

    def part(model, pos, scale, c, **kw):
        e = Entity(parent=actor, model=model, position=pos, scale=scale, color=c, **kw)
        try: e.setLightOff()
        except Exception: pass
        parts.append(e)
        return e

    sc = _soft_cube()

    # ── Badan utama ──
    body_ent = part(sc, (0, body_y, 0), (bw, bh, bd), col)

    # ── Perut/belly ──
    part(sc, (0, body_y - bh*0.18, 0.02), (bw*0.68, bh*0.52, bd*0.75),
         belly if not spec.get('fluffy') else belly)

    # ── Bercak sapi (hitam, dua posisi) ──
    if spec.get('spots'):
        part(sc, (-bw*0.25,  body_y + bh*0.15,  bd*0.48), (bw*0.38, bh*0.38, 0.06), col2)
        part(sc, ( bw*0.30,  body_y - bh*0.10,  bd*0.48), (bw*0.28, bh*0.28, 0.06), col2)
        part(sc, ( bw*0.18,  body_y + bh*0.22, -bd*0.46), (bw*0.32, bh*0.32, 0.06), col2)

    # ── Kepala chibi (lebih besar dari badan) ──
    head_z = bd * 0.50 + bw * 0.10
    head_y = body_y + bh * 0.42
    hsz    = bw * 1.05
    head_ent = part(sc, (0, head_y, head_z), (hsz, hsz * 0.95, hsz), col)

    # ── Moncong / paruh ──
    if spec.get('beak'):
        part(sc, (0, head_y - hsz*0.08, head_z + hsz*0.48),
             (hsz*0.36, hsz*0.20, hsz*0.40), col2)
    else:
        part(sc, (0, head_y - hsz*0.10, head_z + hsz*0.46),
             (hsz*0.52, hsz*0.38, hsz*0.36), belly)

    # ── Mata besar chibi (4 layer: putih, iris, pupil, kilap) ──
    for sx in (-1, 1):
        ex = sx * hsz * 0.30
        ey = head_y + hsz * 0.08
        ez = head_z + hsz * 0.46
        part('sphere', (ex,           ey,           ez),       (hsz*0.28, hsz*0.28, hsz*0.08), _EYE_W)
        part('sphere', (ex,           ey,           ez+0.012), (hsz*0.21, hsz*0.21, hsz*0.08), iris)
        part('sphere', (ex,           ey,           ez+0.022), (hsz*0.13, hsz*0.13, hsz*0.08), _EYE_PU)
        part('sphere', (ex+sx*hsz*0.075, ey+hsz*0.090, ez+0.032),
             (hsz*0.058, hsz*0.058, hsz*0.04), _EYE_W)   # kilap kecil

    # ── Pipi blush ──
    for sx in (-1, 1):
        part(sc, (sx*hsz*0.38, head_y - hsz*0.04, head_z + hsz*0.44),
             (hsz*0.22, hsz*0.12, hsz*0.05), _BLUSH)

    # ── Senyum kecil (garis lekuk) ──
    part(sc, (0, head_y - hsz*0.20, head_z + hsz*0.47),
         (hsz*0.22, hsz*0.055, hsz*0.04), _c(195, 125, 110))

    # ── Telinga ──
    ear = spec.get('ear', 'side')
    if ear == 'pointy':
        for sx in (-1, 1):
            part(sc, (sx*hsz*0.30, head_y + hsz*0.58, head_z),
                 (hsz*0.28, hsz*0.55, hsz*0.20), col, rotation=(0, 0, sx*-15))
            part(sc, (sx*hsz*0.30, head_y + hsz*0.58, head_z),
                 (hsz*0.12, hsz*0.32, hsz*0.10), _BLUSH, rotation=(0, 0, sx*-15))
    elif ear == 'long':
        for sx in (-1, 1):
            part(sc, (sx*hsz*0.22, head_y + hsz*0.92, head_z),
                 (hsz*0.26, hsz*1.22, hsz*0.22), col, rotation=(0, 0, sx*-8))
            part(sc, (sx*hsz*0.22, head_y + hsz*0.92, head_z),
                 (hsz*0.11, hsz*0.82, hsz*0.10), _BLUSH, rotation=(0, 0, sx*-8))
    elif ear == 'side':
        for sx in (-1, 1):
            part(sc, (sx*hsz*0.62, head_y + hsz*0.18, head_z),
                 (hsz*0.34, hsz*0.20, hsz*0.24), col)

    # ── Tanduk ──
    if spec.get('horns'):
        for sx in (-1, 1):
            part(sc, (sx*hsz*0.30, head_y + hsz*0.65, head_z),
                 (hsz*0.14, hsz*0.42, hsz*0.14), _c(230, 218, 195),
                 rotation=(0, 0, sx*-28))

    # ── Jenggot (kambing) ──
    if spec.get('beard'):
        part(sc, (0, head_y - hsz*0.48, head_z + hsz*0.22),
             (hsz*0.22, hsz*0.38, hsz*0.14), col2)

    # ── Jengger (ayam) ──
    if spec.get('comb'):
        part(sc, (0,           head_y + hsz*0.55, head_z), (hsz*0.12, hsz*0.28, hsz*0.36), col2)
        part(sc, (-hsz*0.10,   head_y + hsz*0.52, head_z), (hsz*0.10, hsz*0.22, hsz*0.28), col2)
        part(sc, ( hsz*0.10,   head_y + hsz*0.52, head_z), (hsz*0.10, hsz*0.22, hsz*0.28), col2)

    # ── Surai (kuda) ──
    if spec.get('mane'):
        part(sc, (0, head_y + hsz*0.18, head_z - hsz*0.45),
             (hsz*0.22, hsz*0.65, bd*0.48), spec['belly'])
        part(sc, (0, body_y + bh*0.35, -bd*0.38),
             (bw*0.30, bh*0.60, bw*0.14), spec['belly'])

    # ── Kaki pendek chibi ──
    legs_n  = spec.get('legs', 4)
    leg_col = col if spec.get('fluffy') else col2
    leg_ents = []
    if legs_n == 4:
        for sx in (-1, 1):
            for sz in (-1, 1):
                leg_ents.append(part(sc, (sx*bw*0.30, leg*0.50, sz*bd*0.28),
                                     (bw*0.24, leg, bw*0.24), leg_col))
    else:
        for sx in (-1, 1):
            leg_ents.append(part(sc, (sx*bw*0.22, leg*0.50, 0),
                                 (bw*0.18, leg, bw*0.18), leg_col))

    # ── Ekor ──
    tail      = spec.get('tail', 'long')
    tail_z    = -bd * 0.50 - 0.04
    tail_ent  = None
    if tail == 'long':
        tail_ent = part(sc, (0, body_y + bh*0.22, tail_z),
                        (bw*0.20, bw*0.20, bd*0.55), col, rotation=(38, 0, 0))
    elif tail == 'bushy':   # rubah
        tail_ent = part(sc, (0, body_y + bh*0.06, tail_z - 0.08),
                        (bw*0.62, bw*0.58, bd*0.68), belly, rotation=(32, 0, 0))
        part(sc, (0, body_y + bh*0.10, tail_z - 0.04),
             (bw*0.38, bw*0.38, bd*0.40), col, rotation=(32, 0, 0))
    elif tail == 'puff':    # kelinci
        tail_ent = part('sphere', (0, body_y, tail_z),
                        (bw*0.42, bw*0.42, bw*0.42), _c(255, 248, 248))
    elif tail == 'fan':     # ayam
        for ox in (-0.06, 0, 0.06):
            e = part(sc, (ox, body_y + bh*0.46, tail_z),
                     (bw*0.22, bh*0.56, bw*0.18), col, rotation=(-28, ox*85, 0))
            if tail_ent is None:
                tail_ent = e
    elif tail == 'up':      # bebek
        tail_ent = part(sc, (0, body_y + bh*0.32, tail_z),
                        (bw*0.28, bh*0.38, bw*0.28), col, rotation=(-48, 0, 0))

    actor._animal_parts  = parts
    actor._anim_body     = body_ent
    actor._anim_head     = head_ent
    actor._anim_legs     = leg_ents
    actor._anim_tail     = tail_ent
    actor._anim_body_y   = body_y
    actor._anim_head_y   = head_y
    return parts


# ─── WILD ENTITY CHIBI BUILDERS ──────────────────────────────────────────────

def build_wild_entity(actor, kind: str):
    """Rakit entitas liar cute sebagai child-parts pada `actor`."""
    from .smooth_shader import apply_smooth
    parts = []
    actor.model  = 'cube'
    actor.color  = color.clear
    actor.scale  = _WILD_SCALES.get(kind, 0.50)

    def part(model, pos, scale, c, **kw):
        e = Entity(parent=actor, model=model, position=pos, scale=scale, color=c, **kw)
        apply_smooth(e, has_texture=False)
        parts.append(e)
        return e

    sc = _soft_cube()

    if   kind == 'running_mushroom': _build_mushroom(part, sc)
    elif kind == 'firefly':          _build_firefly(part, sc)
    elif kind == 'mandrake':         _build_mandrake(part, sc)
    elif kind == 'wild_herb':        _build_wild_herb(part, sc)
    elif kind == 'wild_berry':       _build_wild_berry(part, sc)

    actor._wild_parts = parts
    return parts


def _build_mushroom(part, sc):
    """Jamur berlari chibi — topi merah bintik putih, wajah lucu di tangkai."""
    # Tangkai putih gemuk
    part(sc, (0, 0.22, 0), (0.24, 0.44, 0.24), _c(248, 242, 232))
    # Topi merah besar
    part(sc, (0, 0.52, 0), (0.62, 0.40, 0.62), _c(222, 62, 52))
    # Pinggiran topi (putih)
    part(sc, (0, 0.34, 0), (0.72, 0.10, 0.68), _c(248, 244, 238))
    # Bintik putih topi (5)
    for ox, oz, sz in ((0.14, 0.14, 0.11), (-0.16, 0.08, 0.09),
                       (0.06, -0.18, 0.10), (-0.04, 0.18, 0.08), (0.20, -0.06, 0.08)):
        part(sc, (ox, 0.58, oz + 0.32), (sz, 0.06, sz * 0.5), _c(255, 252, 248))
    # Mata chibi di tangkai
    for sx in (-1, 1):
        ex = sx * 0.08
        part('sphere', (ex,            0.28,  0.14), (0.09, 0.09, 0.05), _EYE_W)
        part('sphere', (ex,            0.28,  0.152), (0.068, 0.068, 0.04), _c(62, 168, 75))
        part('sphere', (ex,            0.28,  0.162), (0.042, 0.042, 0.04), _EYE_PU)
        part('sphere', (ex+sx*0.025,   0.302, 0.170), (0.025, 0.025, 0.02), _EYE_W)
    # Pipi blush
    for sx in (-1, 1):
        part(sc, (sx*0.12, 0.24, 0.12), (0.10, 0.06, 0.04), _BLUSH)
    # Senyum
    part(sc, (0, 0.21, 0.14), (0.09, 0.025, 0.025), _c(175, 78, 78))
    # Kaki kecil (2)
    for sx in (-1, 1):
        part(sc, (sx*0.10, 0.05, 0.02), (0.10, 0.12, 0.10), _c(238, 228, 215))


def _build_firefly(part, sc):
    """Kunang-kunang chibi — tubuh hijau-kuning berkilau, sayap transparan."""
    # Tubuh oval kuning-hijau berkilau
    part(sc, (0, 0.28, 0), (0.28, 0.22, 0.22), _c(185, 228, 78))
    # Lingkaran cahaya (glow — solid warna lebih terang)
    part(sc, (0, 0.28, 0), (0.48, 0.38, 0.38), _c(225, 255, 140))
    # Kepala kuning cerah
    part(sc, (0, 0.44, 0), (0.22, 0.20, 0.20), _c(232, 248, 102))
    # Mata besar bulat
    for sx in (-1, 1):
        ex = sx * 0.07
        part('sphere', (ex,           0.46,  0.12), (0.088, 0.088, 0.05), _EYE_W)
        part('sphere', (ex,           0.46,  0.132),(0.065, 0.065, 0.04), _c(30, 160, 65))
        part('sphere', (ex,           0.46,  0.142),(0.040, 0.040, 0.03), _EYE_PU)
        part('sphere', (ex+sx*0.022,  0.476, 0.150),(0.024, 0.024, 0.02), _EYE_W)
    # Pipi kuning terang
    for sx in (-1, 1):
        part(sc, (sx*0.10, 0.44, 0.10), (0.08, 0.05, 0.03), _c(255, 232, 100))
    # Senyum kecil
    part(sc, (0, 0.43, 0.12), (0.07, 0.022, 0.022), _c(80, 150, 55))
    # Sayap (2 pasang kecil)
    for sx in (-1, 1):
        part(sc, (sx*0.28, 0.36, 0.00), (0.20, 0.12, 0.32), _c(215, 248, 205),
             rotation=(0, sx*28, 0))
        part(sc, (sx*0.24, 0.28, 0.02), (0.16, 0.08, 0.22), _c(228, 255, 185),
             rotation=(0, sx*22, 12))
    # Antena (2)
    for sx in (-1, 1):
        part(sc, (sx*0.07, 0.58, 0.04), (0.025, 0.16, 0.025), _c(155, 195, 68),
             rotation=(0, 0, sx*-25))
        part('sphere', (sx*0.10, 0.66, 0.04), (0.065, 0.065, 0.065), _c(248, 255, 108))


def _build_mandrake(part, sc):
    """Mandrake chibi — akar gemuk coklat, wajah teriak lucu, mahkota daun hijau."""
    # Akar tubuh coklat bulat
    part(sc, (0, 0.28, 0), (0.44, 0.56, 0.44), _c(185, 148, 100))
    # Garis tekstur akar
    part(sc, (0, 0.18, 0.23), (0.38, 0.42, 0.04), _c(165, 128, 82))
    # Kaki-akar (2 tonjolan bawah)
    for sx in (-1, 1):
        part(sc, (sx*0.14, 0.06, 0.02), (0.14, 0.18, 0.14), _c(158, 122, 80))
    # Kepala bulat hijau
    part(sc, (0, 0.65, 0), (0.46, 0.46, 0.46), _c(145, 188, 112))
    # Mata melotot besar (mandrake kaget)
    for sx in (-1, 1):
        ex = sx * 0.12
        part('sphere', (ex,           0.70,  0.24), (0.115, 0.115, 0.06), _EYE_W)
        part('sphere', (ex,           0.70,  0.255),(0.086, 0.086, 0.05), _c(48, 138, 58))
        part('sphere', (ex,           0.70,  0.268),(0.055, 0.055, 0.04), _EYE_PU)
        part('sphere', (ex+sx*0.032,  0.720, 0.278),(0.026, 0.026, 0.025),_EYE_W)
    # Mulut terbuka teriak
    part(sc, (0, 0.61, 0.24), (0.22, 0.18, 0.05), _c(22, 18, 22))
    part(sc, (0, 0.61, 0.245),(0.14, 0.08, 0.04), _c(185, 72, 72))
    # Pipi
    for sx in (-1, 1):
        part(sc, (sx*0.18, 0.64, 0.22), (0.12, 0.07, 0.04), _BLUSH)
    # Tangan kecil (opsional, ekspresi dramatis)
    for sx in (-1, 1):
        part(sc, (sx*0.30, 0.42, 0.10), (0.10, 0.08, 0.10), _c(158, 122, 80),
             rotation=(0, 0, sx*55))
    # Daun mahkota di atas (4 daun berbeda)
    for ox, rot_y, sz in ((0.00, 0, 0.26), (-0.15, -38, 0.20), (0.14, 32, 0.18), (0.02, 15, 0.15)):
        part(sc, (ox, 0.95, 0.04), (sz, sz*1.75, sz*0.12),
             _c(82, 162, 68), rotation=(0, rot_y, 0))


def _build_wild_herb(part, sc):
    """Herba liar chibi — gundukan hijau segar, daun memancar, wajah kecil."""
    # Gundukan tanah
    part(sc, (0, 0.07, 0), (0.44, 0.14, 0.44), _c(132, 105, 72))
    # Batang utama
    part(sc, (0, 0.26, 0), (0.07, 0.32, 0.07), _c(85, 158, 68))
    # 6 daun memancar ke berbagai arah
    leaf_data = [
        ( 0.20,  0.00,  22,  15, 0.16),
        (-0.20,  0.00, -22, -15, 0.16),
        ( 0.00,  0.22,   0,  12, 0.18),
        ( 0.14, -0.14,  45, -10, 0.14),
        (-0.14, -0.14, -45,  10, 0.14),
        ( 0.08,  0.16,  12,  -8, 0.13),
    ]
    for ox, oz, ry, rz, sz in leaf_data:
        g = int(165 + abs(ox) * 25)
        part(sc, (ox, 0.38, oz), (sz, sz*2.0, sz*0.11),
             _c(62, g, 55), rotation=(0, ry, rz))
    # Wajah di batang
    for sx in (-1, 1):
        part('sphere', (sx*0.046, 0.295, 0.05), (0.048, 0.048, 0.032), _EYE_PU)
    part(sc, (0, 0.268, 0.05), (0.065, 0.020, 0.020), _c(68, 145, 58))  # senyum
    # Bunga kecil di ujung batang
    part(sc, (0, 0.46, 0), (0.18, 0.18, 0.18), _c(245, 205, 75))
    part(sc, (0, 0.47, 0), (0.09, 0.09, 0.09), _c(248, 130, 48))


def _build_wild_berry(part, sc):
    """Beri liar chibi — buah bulat ungu-merah cerah, wajah ceria."""
    # Buah berry bulat besar
    part('sphere', (0, 0.26, 0), (0.45, 0.45, 0.45), _c(182, 58, 148))
    # Kilap buah
    part('sphere', (0.12, 0.36, 0.18), (0.14, 0.14, 0.12), _c(238, 175, 228))
    # Tangkai
    part(sc, (0, 0.50, 0), (0.05, 0.14, 0.05), _c(72, 142, 58))
    # Daun (3 kecil)
    for ox, rot_y in ((0.09, 35), (-0.09, -35), (0.00, 0)):
        part(sc, (ox, 0.54, 0.04), (0.16, 0.22, 0.09),
             _c(68, 165, 60), rotation=(0, rot_y, 0))
    # Mata chibi
    for sx in (-1, 1):
        ex = sx * 0.11
        part('sphere', (ex,          0.28,  0.23), (0.088, 0.088, 0.05), _EYE_W)
        part('sphere', (ex,          0.28,  0.242),(0.065, 0.065, 0.04), _c(135, 45, 175))
        part('sphere', (ex,          0.28,  0.252),(0.040, 0.040, 0.03), _EYE_PU)
        part('sphere', (ex+sx*0.025, 0.302, 0.260),(0.024, 0.024, 0.02), _EYE_W)
    # Pipi
    for sx in (-1, 1):
        part(sc, (sx*0.16, 0.24, 0.21), (0.10, 0.062, 0.04), _BLUSH)
    # Senyum
    part(sc, (0, 0.23, 0.23), (0.09, 0.026, 0.026), _c(188, 95, 155))


import math as _math

def update_anim_wild(actor, kind: str, t: float):
    """Animasikan entitas liar setiap frame — bob, goyang, melayang."""
    base_y = getattr(actor, '_base_y', 0.25)
    if kind == 'running_mushroom':
        # Lompat-lompat + condong kiri-kanan saat berlari
        actor.y = base_y + abs(_math.sin(t * 4.5)) * 0.14
        actor.rotation_z = _math.sin(t * 4.5) * 10
    elif kind == 'firefly':
        # Melayang naik-turun + putaran lambat
        actor.y = base_y + _math.sin(t * 1.8) * 0.20
        actor.rotation_y = t * 45 % 360
    elif kind == 'mandrake':
        # Bergoyang panik + memantul ringan
        actor.rotation_z = _math.sin(t * 3.2) * 8
        actor.y = base_y + abs(_math.sin(t * 3.2)) * 0.05
    elif kind == 'wild_herb':
        # Melambai tertiup angin
        actor.rotation_z = _math.sin(t * 1.4) * 5
        actor.rotation_x = _math.sin(t * 1.1) * 3
    elif kind == 'wild_berry':
        # Bob perlahan + sedikit ayun
        actor.y = base_y + _math.sin(t * 1.3) * 0.06
        actor.rotation_z = _math.sin(t * 0.9) * 4
