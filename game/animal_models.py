"""
animal_models.py — Builder hewan prosedural low-poly (kucing, kelinci, sapi, dll.)

Dua jalur:
  1. build_animal(actor, type) — rakit mesh prosedural dari primitif (default sekarang).
  2. WIRING ASET: bila ada file assets/models/animal_<type>.glb/.obj, entities.py akan
     memuat itu lebih dulu (lihat get_animal_model_file). Jadi tinggal taruh file →
     otomatis upgrade tanpa ubah kode.

Gaya: low-poly soft-cube (membaur dengan estetika game), warna earthy.
"""
from ursina import Entity, color
from pathlib import Path

_MODELS_DIR = Path(__file__).resolve().parent.parent / 'assets' / 'models'


def get_animal_model_file(animal_type: str):
    """Return nama model aset bila tersedia (untuk upgrade di masa depan), else None."""
    for ext in ('.glb', '.obj'):
        if (_MODELS_DIR / f'animal_{animal_type}{ext}').exists():
            return f'animal_{animal_type}'
    return None


def _c(r, g, b):
    return color.rgb(r, g, b)


# ─── SPESIFIKASI PER JENIS HEWAN ──────────────────────────────────────────────
# body=(w,h,d), leg_len, legs(2/4), ear, tail, extras..., col, col2(aksen), size
ANIMAL_SPECS = {
    'kucing':  dict(body=(0.42, 0.38, 0.78), leg=0.26, legs=4, ear='pointy',
                    tail='long',  col=_c(198, 130, 58),  col2=_c(225, 170, 100), size=0.95),  # Oren oranye
    'kelinci': dict(body=(0.40, 0.42, 0.50), leg=0.18, legs=4, ear='long',
                    tail='puff',  col=_c(225, 222, 215), col2=_c(245, 245, 240), size=0.85),  # Pinky putih
    'sapi':    dict(body=(0.78, 0.70, 1.25), leg=0.45, legs=4, ear='side',
                    tail='long', horns=True, col=_c(232, 228, 220), col2=_c(70, 62, 58), size=1.15),
    'ayam':    dict(body=(0.38, 0.42, 0.42), leg=0.20, legs=2, ear='none',
                    tail='fan',  beak=True, comb=True, col=_c(228, 220, 200), col2=_c(200, 70, 55), size=0.7),
    'kambing': dict(body=(0.52, 0.55, 0.95), leg=0.40, legs=4, ear='side',
                    tail='tiny', horns=True, beard=True, col=_c(180, 168, 148), col2=_c(120, 105, 88), size=0.95),
    'bebek':   dict(body=(0.42, 0.40, 0.62), leg=0.16, legs=2, ear='none',
                    tail='up',   beak=True, col=_c(235, 230, 215), col2=_c(210, 160, 60), size=0.7),
    'domba':   dict(body=(0.62, 0.62, 0.92), leg=0.32, legs=4, ear='side',
                    tail='tiny', fluffy=True, col=_c(225, 222, 212), col2=_c(60, 55, 52), size=1.0),
    'kuda':    dict(body=(0.62, 0.78, 1.30), leg=0.62, legs=4, ear='pointy',
                    tail='long', mane=True, col=_c(120, 88, 58),  col2=_c(70, 50, 35), size=1.25),
    'rubah':   dict(body=(0.42, 0.40, 0.82), leg=0.28, legs=4, ear='pointy',
                    tail='bushy', col=_c(192, 96, 48),  col2=_c(240, 235, 228), size=0.95),
}
_DEFAULT_SPEC = dict(body=(0.5, 0.45, 0.85), leg=0.3, legs=4, ear='side',
                     tail='long', col=_c(150, 130, 105), col2=_c(110, 95, 80), size=1.0)


def _soft_cube():
    from .meshes import soft_cube_mesh
    return soft_cube_mesh()


def build_animal(actor, animal_type: str):
    """Rakit hewan prosedural sebagai child-parts pada `actor` (Entity/FarmAnimal)."""
    spec = ANIMAL_SPECS.get(animal_type, _DEFAULT_SPEC)
    bw, bh, bd = spec['body']
    leg = spec['leg']
    col = spec['col']; col2 = spec['col2']
    parts = []

    # Actor sebagai parent tak terlihat (model dummy)
    actor.model = 'cube'
    actor.color = color.clear
    actor.scale = spec.get('size', 1.0)

    body_y = leg + bh * 0.5

    def part(model, pos, scale, c, **kw):
        e = Entity(parent=actor, model=model, position=pos, scale=scale, color=c, **kw)
        try: e.setLightOff()
        except Exception: pass
        parts.append(e)
        return e

    sc = _soft_cube()

    # Badan
    part(sc, (0, body_y, 0), (bw, bh, bd), col)
    # Perut/aksen bawah
    part(sc, (0, body_y - bh*0.25, 0), (bw*0.92, bh*0.45, bd*0.9), col2 if spec.get('fluffy') else col)

    # Kepala (di depan, +Z)
    head_z = bd * 0.5 + bw * 0.2
    head_y = body_y + bh * 0.35
    hsz = bw * 0.9
    part(sc, (0, head_y, head_z), (hsz, hsz, hsz), col)

    # Moncong / paruh
    if spec.get('beak'):
        part(sc, (0, head_y - hsz*0.1, head_z + hsz*0.45), (hsz*0.4, hsz*0.25, hsz*0.5), spec['col2'])
    else:
        part(sc, (0, head_y - hsz*0.15, head_z + hsz*0.4), (hsz*0.55, hsz*0.4, hsz*0.45), col)

    # Mata (dua titik gelap)
    for sx in (-1, 1):
        part('sphere', (sx*hsz*0.28, head_y + hsz*0.1, head_z + hsz*0.42),
             (hsz*0.16, hsz*0.16, hsz*0.16), _c(28, 24, 22))

    # Telinga
    ear = spec.get('ear', 'side')
    if ear == 'pointy':
        for sx in (-1, 1):
            part(sc, (sx*hsz*0.3, head_y + hsz*0.55, head_z), (hsz*0.22, hsz*0.5, hsz*0.18), col,
                 rotation=(0, 0, sx*-12))
    elif ear == 'long':   # kelinci
        for sx in (-1, 1):
            part(sc, (sx*hsz*0.25, head_y + hsz*0.9, head_z), (hsz*0.2, hsz*1.1, hsz*0.18), col,
                 rotation=(0, 0, sx*-8))
    elif ear == 'side':   # sapi/kambing/domba
        for sx in (-1, 1):
            part(sc, (sx*hsz*0.55, head_y + hsz*0.2, head_z), (hsz*0.3, hsz*0.18, hsz*0.22), col)

    # Tanduk
    if spec.get('horns'):
        for sx in (-1, 1):
            part(sc, (sx*hsz*0.3, head_y + hsz*0.6, head_z), (hsz*0.14, hsz*0.4, hsz*0.14),
                 _c(225, 215, 195), rotation=(0, 0, sx*-30))

    # Jenggot (kambing)
    if spec.get('beard'):
        part(sc, (0, head_y - hsz*0.5, head_z + hsz*0.2), (hsz*0.2, hsz*0.4, hsz*0.15), col2)

    # Jengger (ayam)
    if spec.get('comb'):
        part(sc, (0, head_y + hsz*0.55, head_z), (hsz*0.15, hsz*0.3, hsz*0.4), spec['col2'])

    # Surai (kuda)
    if spec.get('mane'):
        part(sc, (0, head_y + hsz*0.2, head_z - hsz*0.4), (hsz*0.25, hsz*0.7, bd*0.5), col2)

    # Kaki
    legs_n = spec.get('legs', 4)
    if legs_n == 4:
        for sx in (-1, 1):
            for sz in (-1, 1):
                part(sc, (sx*bw*0.32, leg*0.5, sz*bd*0.32), (bw*0.22, leg, bw*0.22),
                     col2 if not spec.get('fluffy') else col)
    else:  # 2 kaki (burung)
        for sx in (-1, 1):
            part(sc, (sx*bw*0.2, leg*0.5, 0), (bw*0.16, leg, bw*0.16), spec.get('col2', col))

    # Ekor
    tail = spec.get('tail', 'long')
    tail_z = -bd * 0.5 - 0.05
    if tail == 'long':
        part(sc, (0, body_y + bh*0.2, tail_z), (bw*0.18, bw*0.18, bd*0.5), col,
             rotation=(35, 0, 0))
    elif tail == 'bushy':  # rubah
        part(sc, (0, body_y, tail_z - 0.1), (bw*0.5, bw*0.5, bd*0.6), spec['col2'],
             rotation=(30, 0, 0))
    elif tail == 'puff':   # kelinci
        part('sphere', (0, body_y, tail_z), (bw*0.35, bw*0.35, bw*0.35), _c(245, 245, 240))
    elif tail == 'fan':    # ayam
        part(sc, (0, body_y + bh*0.4, tail_z), (bw*0.5, bh*0.6, bw*0.2), col,
             rotation=(-30, 0, 0))
    elif tail == 'up':     # bebek
        part(sc, (0, body_y + bh*0.3, tail_z), (bw*0.3, bh*0.4, bw*0.3), col,
             rotation=(-45, 0, 0))
    # 'tiny' → no visible tail

    actor._animal_parts = parts
    return parts
