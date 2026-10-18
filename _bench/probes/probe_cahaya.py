"""probe_cahaya.py — Angka cahaya dunia dari kubus kalibrasi di game ASLI.

Dibuat SEBELUM cahaya diubah, supaya tiap perubahan berikutnya punya garis
dasar yang terukur, bukan "kelihatannya lebih hidup". Kritikus buta sudah lima
kali menyebut cahaya farm datar dan tanpa bayangan; angka di sini yang
memutuskan apakah perubahan menjawabnya.

Jalur yang ditempuh sama dengan tools/capture.py (aturan #2 CLAUDE.md): save
fixture, Game3D, sinema ditandai sudah ditonton, scene diganti lewat
`state.scene_name` + `taskMgr.step()`, jarak kamera lewat roda mouse sungguhan
(`g.input('scroll up')`). Yang ditambahkan probe cuma benda ukurnya:

  * dua KUBUS PUTIH (albedo 1,0, normal per muka eksplisit, mesh dibuat
    sendiri per entity -- aturan #3), satu di kiri dan satu di kanan pemain,
    supaya kamera melihat muka +x di kubus kiri dan muka -x di kubus kanan;
  * dua PELAT KELABU (albedo 0,5) di bawahnya: tanah ladang ditint per ubin,
    jadi "tanah teduh lawan terbuka" yang diukur di tanah asli tercampur
    tint. Pelat memberi albedo yang sama di kedua titik.

Semua dipasang `apply_smooth`, jadi menempuh fragmen yang sama dengan dunia.

Jam DITAHAN (time_minutes ditulis ulang tiap langkah) dan probe menunggu
sampai warna lampu berhenti bergerak: lerp di app.py bergantung pada dt, jadi
tanpa menunggu, angkanya bergantung pada kecepatan mesin.

Tiap titik sampel diperiksa tidak tertutup: frame dengan dan tanpa benda ukur
dibandingkan, dan sampel yang pikselnya tidak berubah dibuang.

    xvfb-run -a -s "-screen 0 1024x768x24" python _bench/probes/probe_cahaya.py
    ... probe_cahaya.py --hour 17.6 --json hasil.json

Tanpa --mode, probe menjalankan dirinya dua kali (dengan post dan dengan
KARSA_NO_POST=1) di subproses, karena post dipasang saat Game3D dibangun.

Garis dasar 294f869 (farm, fixture ladang_hari10, 1280x720, mesin sesi):

    jam   mode    terang/gelap  B/G gelap-terang  atas/depan  pelat buka/teduh  p50   p95
    10    post    1,471         -0,039            1,516       0,996             53,4  96,0
    10    nopost  1,522         -0,052            1,566       1,000             42,2  90,7
    17,6  post    1,502         +0,065            1,574       0,992             43,7  72,6
    17,6  nopost  1,583         +0,072            1,658       1,000             31,8  64,3

Artinya: sisi gelap cuma LEBIH REDUP, bukan lebih sejuk (B/G-nya malah turun
siang hari), dan tanah tidak pernah teduh di mana pun (buka/teduh = 1,00:
tidak ada bayangan jatuhan sama sekali).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Kotak dunia di luar HUD, sama dengan ukur_kontras (kiri/atas/bawah dibuang).
KOTAK_DUNIA = (0.22, 0.17, 0.92, 0.80)


def _kubus_mesh(warna=(1, 1, 1, 1)):
    """Kubus satuan berpusat di titik asal, normal per muka. Mesh BARU tiap
    panggilan -- jangan pernah dibagi antar-Entity (aturan #3)."""
    from ursina import Mesh, Vec3
    muka = [
        # normal, sumbu u, sumbu v
        ((0, 1, 0), (1, 0, 0), (0, 0, 1)),
        ((0, -1, 0), (1, 0, 0), (0, 0, -1)),
        ((1, 0, 0), (0, 0, 1), (0, 1, 0)),
        ((-1, 0, 0), (0, 0, -1), (0, 1, 0)),
        ((0, 0, 1), (-1, 0, 0), (0, 1, 0)),
        ((0, 0, -1), (1, 0, 0), (0, 1, 0)),
    ]
    v, n, t, c = [], [], [], []
    for nn, uu, vv in muka:
        b = len(v)
        for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            p = [0.5 * nn[i] + 0.5 * su * uu[i] + 0.5 * sv * vv[i] for i in range(3)]
            v.append(Vec3(*p))
            n.append(Vec3(*nn))
            c.append(warna)
        # Urutan lilitan tidak penting: smooth_shader membalik normal yang
        # membelakangi kamera dan entity dipasang double_sided.
        t += [(b, b + 1, b + 2), (b, b + 2, b + 3)]
    return Mesh(vertices=v, triangles=t, normals=n, colors=c)


def _boot(args):
    from panda3d.core import loadPrcFileData
    loadPrcFileData('', 'load-display pandagl')
    loadPrcFileData('', 'window-type onscreen')
    loadPrcFileData('', 'sync-video false')
    loadPrcFileData('', 'audio-library-name null')
    import logging
    logging.basicConfig(level=logging.ERROR)
    sys.path.insert(0, str(ROOT))
    os.chdir(ROOT)
    from ursina import application
    application.asset_folder = ROOT
    application.fonts_folder = ROOT / 'assets' / 'fonts'
    from panda3d.core import getModelPath
    getModelPath().append_path(str(ROOT.resolve()))
    import game.config as cfg
    cfg.SCREEN_W, cfg.SCREEN_H = args.width, args.height

    save = ROOT / cfg.SAVE_FILE
    if save.exists():
        print(f'PROBE_ERR: {save.name} sudah ada; probe tidak menimpanya',
              file=sys.stderr)
        sys.exit(2)
    import atexit
    import shutil
    shutil.copyfile(ROOT / args.save, save)
    atexit.register(lambda: save.unlink(missing_ok=True))

    from game.app import Game3D
    g = Game3D()
    try:
        from game.cutscene import NASKAH
        g.state.sinema_selesai = list(NASKAH)
    except Exception:
        pass
    from direct.showbase.ShowBaseGlobal import base
    for _ in range(10):
        base.taskMgr.step()
    g.state.scene_name = args.scene
    for _ in range(30):
        base.taskMgr.step()
    if g.world.scene_name != args.scene:
        print(f'PROBE_ERR: scene {g.world.scene_name}, minta {args.scene}',
              file=sys.stderr)
        sys.exit(2)
    for _ in range(args.scroll):
        g.input('scroll up')
        for _ in range(2):
            base.taskMgr.step()
    return g, base, save


def _tahan_jam(g, hour):
    g.state.time_minutes = float(hour) * 60.0


def _tunggu_konvergen(g, base, hour, maks=900):
    """Langkahkan sampai warna lampu dan kamera berhenti bergerak."""
    def snap():
        s, a = g.sun.color, g.ambient.color
        from ursina import camera
        p = camera.world_position
        return (s[0], s[1], s[2], a[0], a[1], a[2]), (p[0], p[1], p[2])
    tenang = 0
    lama_c, lama_p = snap()
    for i in range(maks):
        _tahan_jam(g, hour)
        base.taskMgr.step()
        c, p = snap()
        dc = max(abs(x - y) for x, y in zip(c, lama_c))
        dp = max(abs(x - y) for x, y in zip(p, lama_p))
        lama_c, lama_p = c, p
        tenang = tenang + 1 if (dc < 2e-4 and dp < 2e-3) else 0
        if tenang >= 6:
            return i + 1
    return -1


def _tembak(base, path):
    from panda3d.core import Filename
    from PIL import Image
    for _ in range(2):
        base.graphicsEngine.renderFrame()
    img = base.win.getScreenshot()
    img.write(Filename.fromOsSpecific(str(path)))
    return Image.open(path).convert('RGB')


def _proyeksi(base, p):
    """Titik dunia -> piksel jendela, atau None kalau di luar frustum."""
    from panda3d.core import Point2, Point3
    pc = base.cam.getRelativePoint(base.render, Point3(*p))
    p2 = Point2()
    if not base.camLens.project(pc, p2):
        return None
    w, h = base.win.getXSize(), base.win.getYSize()
    return (int(round((p2.x + 1) * 0.5 * w)), int(round((1 - p2.y) * 0.5 * h)))


def _lum(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def _rata(im, xy, r=2):
    x0, y0 = xy
    px = [im.getpixel((x, y)) for x in range(x0 - r, x0 + r + 1)
          for y in range(y0 - r, y0 + r + 1)
          if 0 <= x < im.size[0] and 0 <= y < im.size[1]]
    n = max(1, len(px))
    return tuple(sum(p[i] for p in px) / n for i in range(3))


def _berubah(a, b, xy, r=2, ambang=6):
    """True kalau seluruh petak sampel berubah antara dua frame (= milik benda
    ukur, bukan tertutup benda lain)."""
    x0, y0 = xy
    for x in range(x0 - r, x0 + r + 1):
        for y in range(y0 - r, y0 + r + 1):
            if not (0 <= x < a.size[0] and 0 <= y < a.size[1]):
                return False
            pa, pb = a.getpixel((x, y)), b.getpixel((x, y))
            if max(abs(pa[i] - pb[i]) for i in range(3)) < ambang:
                return False
    return True


def _statistik_dunia(im):
    w, h = im.size
    b = tuple(int(v * (w if i % 2 == 0 else h)) for i, v in enumerate(KOTAK_DUNIA))
    px = list(im.crop(b).resize((320, 180)).getdata())
    L = sorted(_lum(p) for p in px)
    n = len(L)
    pct = lambda q: L[int(q * (n - 1))]
    return {'p5': round(pct(.05), 1), 'p50': round(pct(.5), 1),
            'p95': round(pct(.95), 1),
            'p95/p5': round(pct(.95) / max(1.0, pct(.05)), 2)}


def ukur(args):
    g, base, save = _boot(args)
    from ursina import Entity, Vec3, scene as uscene, color
    from game.smooth_shader import apply_smooth

    n_konv = _tunggu_konvergen(g, base, args.hour)

    # Arah matahari yang BENAR-BENAR dipakai fragmen (uniform di scene).
    si = uscene.getShaderInput('sm_sun_dir')
    sd = si.getVector()
    sun_dir = Vec3(sd[0], sd[1], sd[2]).normalized()
    L = -sun_dir

    from game.bayangan import TINGGI_TANAH
    p = g.player.world_position
    # Pelat diangkat sedikit di atas bedeng ladang: bedeng lebih tinggi dari
    # jalan setapak dan menutup pelat yang rata dengan tanah.
    y0 = TINGGI_TANAH + args.angkat
    s = args.kubus
    benda = []
    sampel = {}          # nama -> titik dunia
    ndl = {}
    for sisi, dx in (('kiri', -args.geser), ('kanan', args.geser)):
        cx, cz = p[0] + dx, p[2] + args.maju
        pelat = Entity(parent=uscene, model=_kubus_mesh((0.5, 0.5, 0.5, 1)),
                       position=Vec3(cx, y0 - 0.01, cz),
                       scale=Vec3(args.pelat, 0.02, args.pelat), double_sided=True)
        kubus = Entity(parent=uscene, model=_kubus_mesh(),
                       position=Vec3(cx, y0 + s / 2, cz),
                       scale=Vec3(s, s, s), double_sided=True)
        for e in (pelat, kubus):
            apply_smooth(e)
            benda.append(e)
        sampel[f'{sisi}_atas'] = (cx, y0 + s + 0.001, cz)
        ndl[f'{sisi}_atas'] = L.y
        sampel[f'{sisi}_depan'] = (cx, y0 + s / 2, cz - s / 2 - 0.001)
        ndl[f'{sisi}_depan'] = -L.z
        if sisi == 'kiri':
            sampel['kiri_+x'] = (cx + s / 2 + 0.001, y0 + s / 2, cz)
            ndl['kiri_+x'] = L.x
        else:
            sampel['kanan_-x'] = (cx - s / 2 - 0.001, y0 + s / 2, cz)
            ndl['kanan_-x'] = -L.x
        # Titik pelat: satu di tengah bayangan jatuhan kubus (kalau ada), satu
        # di samping yang pasti terbuka. Bayangan tengah-atas kubus jatuh di
        # alas + arah_xz * tinggi / -D.y.
        dxz = Vec3(sun_dir.x, 0, sun_dir.z)
        panjang = s * dxz.length() / max(0.05, -sun_dir.y)
        u = dxz.normalized() if dxz.length() > 1e-4 else Vec3(0, 0, -1)
        tegak = Vec3(-u.z, 0, u.x)
        jarak = min(s / 2 + panjang * 0.5, args.pelat / 2 - 0.15)
        teduh = Vec3(cx, y0, cz) + u * jarak
        # Titik terbuka: tegak lurus arah bayangan dari pusat kubus, di sisi
        # yang lebih dekat ke kamera (z lebih kecil) supaya tidak tertutup
        # kubusnya sendiri. Jaraknya s, di luar setengah-diagonal kubus
        # (0,71 s), jadi di luar bayangannya juga.
        if tegak.z > 0:
            tegak = -tegak
        buka = Vec3(cx, y0, cz) + tegak * s
        sampel[f'{sisi}_pelat_teduh'] = (teduh.x, y0 + 0.001, teduh.z)
        sampel[f'{sisi}_pelat_buka'] = (buka.x, y0 + 0.001, buka.z)

    # Bekukan task update: kubus dan kamera tidak boleh bergeser di antara dua
    # tangkapan yang dibandingkan.
    tugas = list(base.taskMgr.getTasksNamed('update'))
    for t in tugas:
        t.remove()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    tag = 'nopost' if os.environ.get('KARSA_NO_POST') else 'post'
    a = _tembak(base, out / f'cahaya_{args.scene}_{args.hour}_{tag}_benda.png')
    for e in benda:
        e.enabled = False
    b = _tembak(base, out / f'cahaya_{args.scene}_{args.hour}_{tag}_dunia.png')
    for e in benda:
        e.enabled = True
    for t in tugas:
        base.taskMgr.add(t)

    nilai, buang = {}, []
    for nama, w in sampel.items():
        xy = _proyeksi(base, w)
        if xy is None or not _berubah(a, b, xy):
            buang.append(nama)
            continue
        c = _rata(a, xy)
        nilai[nama] = {'xy': xy, 'rgb': [round(v, 1) for v in c],
                       'L': round(_lum(c), 1),
                       'B/G': round(c[2] / max(1.0, c[1]), 3)}

    def rasio(x, y):
        if x in nilai and y in nilai:
            return round(nilai[x]['L'] / max(1.0, nilai[y]['L']), 3)
        return None

    def geser(gelap, terang):
        if gelap in nilai and terang in nilai:
            return round(nilai[gelap]['B/G'] - nilai[terang]['B/G'], 3)
        return None

    # Sisi tegak terang dan gelap ditentukan dari ndl SEBENARNYA, bukan
    # dikarang: kalau arah matahari diubah, label ikut berubah.
    tegak_ = [k for k in ('kiri_+x', 'kanan_-x', 'kiri_depan', 'kanan_depan') if k in nilai]
    terang = max(tegak_, key=lambda k: ndl[k]) if tegak_ else None
    gelap = min(tegak_, key=lambda k: ndl[k]) if tegak_ else None
    teduh_buka = [rasio(f'{s_}_pelat_buka', f'{s_}_pelat_teduh') for s_ in ('kiri', 'kanan')]
    teduh_buka = [v for v in teduh_buka if v is not None]

    hasil = {
        'mode': tag, 'scene': args.scene, 'hour': args.hour,
        'frame_konvergen': n_konv,
        'sun_dir': [round(v, 3) for v in sun_dir],
        'sun_color': [round(g.sun.color[i], 3) for i in range(3)],
        'ambient': [round(g.ambient.color[i], 3) for i in range(3)],
        'ndl': {k: round(v, 3) for k, v in ndl.items()},
        'sampel': nilai, 'tertutup': buang,
        'terang': terang, 'gelap': gelap,
        'rasio_terang/gelap': rasio(terang, gelap) if terang and gelap else None,
        'geser_BG_gelap-terang': geser(gelap, terang) if terang and gelap else None,
        'rasio_atas/depan': rasio('kiri_atas', 'kiri_depan') or rasio('kanan_atas', 'kanan_depan'),
        'rasio_kanan/kiri(+x/-x)': rasio('kiri_+x', 'kanan_-x'),
        'geser_BG_depan-atas': geser('kiri_depan', 'kiri_atas') or geser('kanan_depan', 'kanan_atas'),
        'pelat_buka/teduh': round(sum(teduh_buka) / len(teduh_buka), 3) if teduh_buka else None,
        'geser_BG_pelat_teduh-buka': geser('kiri_pelat_teduh', 'kiri_pelat_buka'),
        'dunia': _statistik_dunia(b),
    }
    print('PROBE_JSON ' + json.dumps(hasil, ensure_ascii=False))
    sys.stdout.flush()
    save.unlink(missing_ok=True)
    os._exit(0)


def _ringkas(h):
    d = h['dunia']
    return (f"{h['mode']:7s} konv={h['frame_konvergen']:4d}  "
            f"terang/gelap={h['rasio_terang/gelap']}  B/G gelap-terang={h['geser_BG_gelap-terang']}  "
            f"atas/depan={h['rasio_atas/depan']}  +x/-x={h['rasio_kanan/kiri(+x/-x)']}  "
            f"pelat buka/teduh={h['pelat_buka/teduh']} (B/G {h['geser_BG_pelat_teduh-buka']})  "
            f"dunia p50={d['p50']} p95={d['p95']} p95/p5={d['p95/p5']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--scene', default='farm')
    ap.add_argument('--hour', type=float, default=10.0)
    ap.add_argument('--save', default='tools/fixtures/ladang_hari10_save.json')
    ap.add_argument('--scroll', type=int, default=4,
                    help='berapa kali roda mouse maju (farm_wide memakai 4)')
    ap.add_argument('--kubus', type=float, default=1.2)
    ap.add_argument('--pelat', type=float, default=3.2)
    ap.add_argument('--geser', type=float, default=3.6,
                    help='jarak lateral kubus dari pemain')
    ap.add_argument('--angkat', type=float, default=0.2,
                    help='tinggi permukaan pelat di atas tanah')
    ap.add_argument('--maju', type=float, default=0.0,
                    help='geser z kubus dari pemain (negatif = ke arah kamera)')
    ap.add_argument('--width', type=int, default=1280)
    ap.add_argument('--height', type=int, default=720)
    ap.add_argument('--out', default=str(ROOT / '_bench' / 'shots' / 'cahaya'))
    ap.add_argument('--mode', choices=('post', 'nopost'), default=None)
    ap.add_argument('--json', default=None, help='tulis hasil kedua mode ke sini')
    args, sisa = ap.parse_known_args()

    if args.mode:
        ukur(args)
        return

    hasil = []
    for mode in ('post', 'nopost'):
        env = dict(os.environ)
        env.pop('KARSA_NO_POST', None)
        if mode == 'nopost':
            env['KARSA_NO_POST'] = '1'
        r = subprocess.run([sys.executable, __file__, '--mode', mode] + sys.argv[1:],
                           cwd=ROOT, env=env, capture_output=True, text=True,
                           timeout=900)
        baris = [b for b in r.stdout.splitlines() if b.startswith('PROBE_JSON ')]
        if r.returncode != 0 or not baris:
            print(f'{mode}: GAGAL (kode {r.returncode})')
            print('\n'.join((r.stdout + r.stderr).strip().splitlines()[-12:]))
            sys.exit(1)
        hasil.append(json.loads(baris[-1][len('PROBE_JSON '):]))
    for h in hasil:
        print(_ringkas(h))
        if h['tertutup']:
            print(f"        sampel tertutup/di luar layar: {h['tertutup']}")
    if args.json:
        Path(args.json).write_text(json.dumps(hasil, ensure_ascii=False, indent=1),
                                   encoding='utf-8')


if __name__ == '__main__':
    main()
