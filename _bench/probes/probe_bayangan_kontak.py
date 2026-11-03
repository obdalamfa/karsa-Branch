"""probe_bayangan_kontak.py — Bentuk bayangan kontak pemain dan luas bayangan
statis, di game ASLI (jalur Game3D yang sama dengan probe_cahaya).

Dua frame dibandingkan untuk tiap bayangan: dengan dan tanpa node
bayangannya. Piksel yang berubah adalah jejak bayangan itu di layar.

  pemain:  isi_kotak  = piksel jejak / luas kotak pembatasnya. Quad persegi
                        yang dilihat miring mengisi kotaknya ~0,9-1,0; cakram
                        ~0,6-0,8.
           lunak      = porsi piksel jejak yang gelapnya < 60% dari gelap
                        terdalam (p90). Quad ber-alpha rata ~0; cakram berbulu
                        jauh di atasnya.
  statis:  jumlah cakram dan porsi piksel dunia yang digelapkannya.

    xvfb-run -a -s "-screen 0 1024x768x24" python _bench/probes/probe_bayangan_kontak.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import probe_cahaya as pc  # noqa: E402


def _jejak(a, b, kotak=None, ambang=4):
    w, h = a.size
    x0, y0, x1, y1 = kotak or (0, 0, w, h)
    titik = []
    for y in range(max(0, y0), min(h, y1)):
        for x in range(max(0, x0), min(w, x1)):
            pa, pb = a.getpixel((x, y)), b.getpixel((x, y))
            d = sum(pb) - sum(pa)          # b tanpa bayangan -> lebih terang
            if d >= ambang * 3:
                titik.append((x, y, d))
    return titik


def ukur(args):
    g, base, save = pc._boot(args)
    n_konv = pc._tunggu_konvergen(g, base, args.hour)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    hasil = {'scene': args.scene, 'hour': args.hour, 'frame_konvergen': n_konv}

    a = pc._tembak(base, out / 'kontak_a.png')
    sh = getattr(g.player, '_shadow', None)
    p = g.player.world_position
    kaki = pc._proyeksi(base, (p[0], 0.25, p[2]))
    if sh is not None and kaki is not None:
        sh.hide()
        b = pc._tembak(base, out / 'kontak_b_tanpa_pemain.png')
        sh.show()
        r = args.jendela
        # Batas atas jendela sedikit di atas titik kaki: badan pemain bergerak
        # (napas idle) di antara dua frame dan jangan ikut terhitung jejak.
        t = _jejak(a, b, (kaki[0] - r, kaki[1] - args.atas, kaki[0] + r, kaki[1] + r))
        if t:
            xs = [q[0] for q in t]; ys = [q[1] for q in t]
            kotak = (max(xs) - min(xs) + 1) * (max(ys) - min(ys) + 1)
            ds = sorted(q[2] for q in t)
            p90 = ds[int(0.9 * (len(ds) - 1))]
            hasil['pemain'] = {
                'piksel': len(t),
                'kotak': [min(xs), min(ys), max(xs), max(ys)],
                'isi_kotak': round(len(t) / kotak, 3),
                'lunak': round(sum(1 for d in ds if d < 0.6 * p90) / len(ds), 3),
                'gelap_p90': p90 / 3,
            }
            a.crop((kaki[0] - r, kaki[1] - r, kaki[0] + r, kaki[1] + r)).resize(
                (r * 4, r * 4)).save(out / 'kontak_kaki.png')
    st = getattr(g.world, '_bayangan_statis', None)
    hasil['statis_cakram'] = getattr(st, 'jumlah_cakram', 0) if st is not None else 0
    if st is not None:
        st.hide()
        c = pc._tembak(base, out / 'kontak_c_tanpa_statis.png')
        st.show()
        w, h = a.size
        k = tuple(int(v * (w if i % 2 == 0 else h)) for i, v in enumerate(pc.KOTAK_DUNIA))
        t = _jejak(a, c, k)
        hasil['statis_porsi_dunia'] = round(len(t) / ((k[2] - k[0]) * (k[3] - k[1])), 4)
    else:
        hasil['statis_porsi_dunia'] = 0.0
    hasil['entity'] = len(__import__('ursina').scene.entities)
    print('PROBE_JSON ' + json.dumps(hasil, ensure_ascii=False))
    sys.stdout.flush()
    base.userExit() if hasattr(base, 'userExit') else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--scene', default='farm')
    ap.add_argument('--hour', type=float, default=10.0)
    ap.add_argument('--save', default='tools/fixtures/ladang_hari10_save.json')
    ap.add_argument('--scroll', type=int, default=4)
    ap.add_argument('--width', type=int, default=1280)
    ap.add_argument('--height', type=int, default=720)
    ap.add_argument('--jendela', type=int, default=70)
    ap.add_argument('--atas', type=int, default=28)
    ap.add_argument('--out', default=str(pc.ROOT / '_bench' / 'shots' / 'kontak'))
    ukur(ap.parse_args())


if __name__ == '__main__':
    main()
