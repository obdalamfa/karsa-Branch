"""make_walk4.py — Lengkapi walk cycle 2-frame → 4-frame (ROADMAP M5).

Aset lama punya <base>_idle/_walk1/_walk2 (dua pose KONTAK: kaki kiri maju,
kaki kanan maju). Siklus jalan yang enak dilihat butuh pose PASSING di antara
keduanya — saat kedua kaki berdekatan dan badan terangkat paling tinggi.

Script ini membuat <base>_walk3 & <base>_walk4 (dua pose passing) dengan
deformasi vertex prosedural, TANPA Blender — matematika dicocokkan dengan
aset lama (diukur dari selisih npc_arya.obj vs npc_arya_walk1.obj):

    tinggi      = sumbu Y
    kaki        = vertex di bawah 42% tinggi
    ayun kaki   = sumbu Z, ±0.15*H, arah per sisi X
    angkat kaki = sumbu Y, sampai 0.045*H (hanya kaki yang mengayun maju)
    badan       = ikut sedikit (counter-lean) + terangkat saat passing

Idempoten: menulis ulang file yang sama bila dijalankan lagi.
Pakai:  python tools/make_walk4.py            (semua model yang punya walk1+2)
        python tools/make_walk4.py npc_arya   (model tertentu)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODELS = ROOT / 'assets' / 'models'

LEG_RATIO   = 0.42     # batas tinggi kaki (dari dasar)
SWING       = 0.15     # amplitudo ayun kaki (× tinggi)
LIFT        = 0.045    # angkat kaki mengayun (× tinggi)
BODY_LEAN   = 0.011    # badan ikut condong (× tinggi)
BODY_RISE   = 0.030    # badan terangkat saat passing (× tinggi)


def read_obj(path):
    """Return (lines, vertex_indices) — semua baris disimpan apa adanya."""
    lines = path.read_text(errors='ignore').splitlines()
    vidx = [i for i, l in enumerate(lines) if l.startswith('v ')]
    return lines, vidx


def parse_v(line):
    a = line.split()
    return float(a[1]), float(a[2]), float(a[3])


def deform(lines, vidx, phase, passing=False):
    """Terapkan pose berjalan. phase -1..1; passing=True → badan terangkat."""
    verts = [parse_v(lines[i]) for i in vidx]
    ys = [v[1] for v in verts]
    xs = [v[0] for v in verts]
    ymin, ymax = min(ys), max(ys)
    H = max(ymax - ymin, 1e-6)
    xc = (min(xs) + max(xs)) * 0.5
    leg_top = ymin + LEG_RATIO * H

    out = list(lines)
    for i, (x, y, z) in zip(vidx, verts):
        if y < leg_top:
            side = 1.0 if x >= xc else -1.0
            nz = z + SWING * H * phase * side
            ny = y
            if side * phase > 0:                 # kaki yang mengayun ke depan
                ny = y + LIFT * H * abs(phase)
            nx = x
        else:
            nx = x
            ny = y + (BODY_RISE * H if passing else 0.0)
            nz = z - BODY_LEAN * H * phase       # badan menyeimbangkan
        out[i] = f"v {nx:.6f} {ny:.6f} {nz:.6f}"
    return out


def bases_with_walk():
    """Model yang punya _walk1 & _walk2 (kandidat dilengkapi jadi 4-frame)."""
    out = []
    for p in sorted(MODELS.glob('*_walk1.obj')):
        base = p.name[:-len('_walk1.obj')]
        if (MODELS / f'{base}_walk2.obj').exists():
            out.append(base)
    return out


def build(base):
    src = MODELS / f'{base}.obj'
    if not src.exists():
        return False, f'{base}: sumber tak ada'
    lines, vidx = read_obj(src)
    if not vidx:
        return False, f'{base}: tak ada vertex'
    # walk3 & walk4 = dua pose PASSING (badan naik, kaki hampir rapat)
    for name, phase in ((f'{base}_walk3.obj', 0.45), (f'{base}_walk4.obj', -0.45)):
        out = deform(lines, vidx, phase, passing=True)
        (MODELS / name).write_text('\n'.join(out) + '\n')
    return True, base


def main():
    targets = sys.argv[1:] or bases_with_walk()
    ok = 0
    for base in targets:
        good, msg = build(base)
        if good:
            ok += 1
        else:
            print('SKIP', msg)
    print(f'WALK4_DONE {ok}/{len(targets)} model dapat _walk3 & _walk4')


if __name__ == '__main__':
    main()
