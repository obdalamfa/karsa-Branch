"""probe_arah_matahari.py — Pilih arah matahari dengan angka, bukan selera.

Kompromi yang diukur (langkah 5 rencana workstream D): matahari dari
BELAKANG benda (relatif kamera bawaan, yaw 0, kamera di -z menatap +z)
membuat bayangan jatuh ke arah kamera dan kelihatan penuh, tapi muka yang
menghadap kamera -- wajah karakter -- jatuh di pita tergelap. Matahari dari
depan membalik keduanya. Probe ini mem-boot Game3D sekali (jalur probe_cahaya)
dan untuk tiap kandidat arah:

  * mengarahkan `g.sun` (DirectionalLight asli; sm_sun_dir dibaca darinya),
  * memotret kubus putih kalibrasi dengan dan tanpa kubus,
  * mencatat L muka depan (proksi wajah), L muka atas dan muka samping yang
    terlihat, dan `beda_min` = beda L terkecil antar tiga muka tampak
    (kecil = bentuk tidak terbaca, dua muka sewarna),
  * menghitung GEOMETRIS luas bayangan jatuhan kubus yang tampak di layar
    (poligon bayangan di tanah lewat lensa kamera asli, dikurangi bagian yang
    tertutup kubusnya sendiri), dalam piksel.

    xvfb-run -a -s "-screen 0 1024x768x24" python _bench/probes/probe_arah_matahari.py
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import probe_cahaya as pc  # noqa: E402


def _hull(pts):
    pts = sorted(set(pts))
    if len(pts) < 3:
        return pts
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0:
            hi.pop()
        hi.append(p)
    return lo[:-1] + hi[:-1]


def _arah(azimut, elevasi):
    """Arah RAMBAT sinar: azimut 0 = sinar merambat ke +z (matahari di
    belakang kamera, menyinari muka yang menghadap kamera), 90 = ke +x."""
    a, e = math.radians(azimut), math.radians(elevasi)
    return (math.sin(a) * math.cos(e), -math.sin(e), math.cos(a) * math.cos(e))


def ukur(args):
    g, base, save = pc._boot(args)
    from ursina import Entity, Vec3, scene as uscene
    from PIL import Image, ImageDraw
    from game.smooth_shader import apply_smooth
    from game.bayangan import TINGGI_TANAH
    pc._tunggu_konvergen(g, base, args.hour)
    # app.update() mengarahkan matahari sendiri tiap frame menurut jam
    # (cahaya.arahkan_matahari). Selama sapuan kandidat, itu dimatikan --
    # kalau tidak, tiap kandidat langsung ditimpa arah bawaan.
    import game.cahaya as _c
    _c.arahkan_matahari = lambda *a, **k: False

    p = g.player.world_position
    s = args.kubus
    cx, cz = p[0] + args.geser, p[2]
    y0 = TINGGI_TANAH + 0.2
    kubus = Entity(parent=uscene, model=pc._kubus_mesh(), position=Vec3(cx, y0 + s / 2, cz),
                   scale=Vec3(s, s, s), double_sided=True)
    apply_smooth(kubus)
    pelat = Entity(parent=uscene, model=pc._kubus_mesh((0.5, 0.5, 0.5, 1)),
                   position=Vec3(cx, y0 - 0.01, cz), scale=Vec3(6, 0.02, 6),
                   double_sided=True)
    apply_smooth(pelat)

    calon = []
    for az in range(0, 360, 45):
        calon.append(('az%d_el%d' % (az, args.elevasi), _arah(az, args.elevasi)))
    calon.append(('sekarang', tuple(pc_ for pc_ in (-0.5, -0.8, -0.4))))
    for extra in args.tambah:
        az, el = (float(v) for v in extra.split(','))
        calon.append(('az%g_el%g' % (az, el), _arah(az, el)))

    hasil = []
    for nama, d in calon:
        v = Vec3(*d).normalized()
        g.sun.look_at(g.sun.world_position + v)
        for _ in range(4):
            pc._tahan_jam(g, args.hour)
            base.taskMgr.step()
        tugas = list(base.taskMgr.getTasksNamed('update'))
        for t in tugas:
            t.remove()
        a = pc._tembak(base, Path(args.out) / f'arah_{nama}.png')
        kubus.enabled = False
        b = pc._tembak(base, Path(args.out) / f'arah_{nama}_tanpa.png')
        kubus.enabled = True
        for t in tugas:
            base.taskMgr.add(t)

        # Muka samping yang menghadap kamera: -x kalau kubus di kanan
        # pemain, +x kalau di kiri.
        sx_ = -1 if args.geser > 0 else 1
        muka = {'atas': (cx, y0 + s + 0.001, cz), 'depan': (cx, y0 + s / 2, cz - s / 2 - 0.001),
                'samping': (cx + sx_ * (s / 2 + 0.001), y0 + s / 2, cz)}
        L = {}
        for k, w in muka.items():
            xy = pc._proyeksi(base, w)
            if xy is not None and pc._berubah(a, b, xy):
                L[k] = round(pc._lum(pc._rata(a, xy)), 1)
        nilai = list(L.values())
        beda = min(abs(x - y) for i, x in enumerate(nilai) for y in nilai[i + 1:]) if len(nilai) >= 3 else None

        # Bayangan geometris: tiap sudut kubus diproyeksikan sepanjang v ke
        # bidang pelat (y = y0).
        sudut = [(cx + sx * s / 2, y0 + sy * s, cz + sz * s / 2)
                 for sx in (-1, 1) for sy in (0, 1) for sz in (-1, 1)]
        bay = []
        for q in sudut:
            t_ = (q[1] - y0) / max(1e-4, -v.y)
            bay.append((q[0] + v.x * t_, y0, q[2] + v.z * t_))
        w, h = a.size
        def topeng(titik):
            xy = [pc._proyeksi(base, q) for q in titik]
            xy = [q for q in xy if q is not None]
            m = Image.new('L', (w, h), 0)
            hl = _hull(xy)
            if len(hl) >= 3:
                ImageDraw.Draw(m).polygon(hl, fill=255)
            return m
        mb, mk = topeng(bay), topeng(sudut)
        tampak = sum(1 for x, y in zip(mb.getdata(), mk.getdata()) if x and not y)
        hasil.append({'calon': nama, 'arah': [round(c, 3) for c in v], 'L': L,
                      'beda_min': None if beda is None else round(beda, 1),
                      'bayangan_tampak_px': tampak})
    print('PROBE_JSON ' + json.dumps(hasil, ensure_ascii=False))
    for r in hasil:
        print(f"{r['calon']:14s} {r['arah']}  L={r['L']}  beda_min={r['beda_min']}  "
              f"bayangan={r['bayangan_tampak_px']}")
    sys.stdout.flush()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--scene', default='farm')
    ap.add_argument('--hour', type=float, default=10.0)
    ap.add_argument('--save', default='tools/fixtures/ladang_hari10_save.json')
    ap.add_argument('--scroll', type=int, default=4)
    ap.add_argument('--width', type=int, default=1280)
    ap.add_argument('--height', type=int, default=720)
    ap.add_argument('--kubus', type=float, default=1.2)
    ap.add_argument('--geser', type=float, default=3.0)
    ap.add_argument('--elevasi', type=float, default=50.0)
    ap.add_argument('--tambah', nargs='*', default=[], help='az,el tambahan')
    ap.add_argument('--out', default=str(pc.ROOT / '_bench' / 'shots' / 'arah'))
    a = ap.parse_args()
    Path(a.out).mkdir(parents=True, exist_ok=True)
    ukur(a)


if __name__ == '__main__':
    main()
