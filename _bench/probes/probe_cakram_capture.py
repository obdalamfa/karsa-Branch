"""probe_cakram_capture.py — Cakram bayangan kontak harus MENGGELAPKAN tanah
di tangkapan tools/capture.py, bukan menggambar tekstur lain.

Lahir dari bug nyata (ed063dc): cakram dibuat `shader=None`, jadi digambar
pipeline fixed-function tanpa TextureAttrib. Di jalur capture.py, tekstur
yang terakhir terikat di GL ikut tercicip: di bawah kaki pemain muncul
lajur papan kayu dan di pangkal pohon kotak rumput hijau. probe_bayangan_
kontak (jalur probe_cahaya) tidak melihatnya -- urutan gambarnya lain, dan
di sana cakram kebetulan gelap. Karena itu probe ini menempuh capture.py
apa adanya (subproses, argumen yang sama dengan gauntlet), dua kali:

  A  tangkapan biasa;
  B  sama, tetapi setiap cakram dari game/bayangan.py disembunyikan.

Di dua wilayah tetap (kaki pemain di tengah layar; pangkal pohon kanan),
A - B harus gelap: jumlah RGB turun, dan tidak ada kanal yang NAIK lebih
dari 3. Bug lama: kaki +17 per kanal (papan), pangkal pohon G +15 (rumput).

    xvfb-run -a -s "-screen 0 1024x768x24" python _bench/probes/probe_cakram_capture.py
Keluar 1 kalau gagal.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

_TANPA_CAKRAM = r'''
import runpy, sys
sys.path.insert(0, '.')
import game.bayangan as b
_asli = b._entity_cakram
def _sembunyi(*a, **k):
    e = _asli(*a, **k)
    e.hide()
    return e
b._entity_cakram = _sembunyi
sys.argv = ['tools/capture.py'] + sys.argv[1:]
runpy.run_path('tools/capture.py', run_name='__main__')
'''

# (x0, y0, x1, y1) pada 1280x720, fixture ladang_hari10, --hour 10.
WILAYAH = {
    'kaki_pemain': (600, 375, 680, 420),
    'pangkal_pohon': (1150, 375, 1260, 425),
}


def _tangkap(out: Path, tanpa: bool):
    argv = ['--scene', 'farm', '--hour', '10',
            '--save', 'tools/fixtures/ladang_hari10_save.json',
            '--width', '1280', '--height', '720', '--out', str(out)]
    cmd = ([sys.executable, '-c', _TANPA_CAKRAM] if tanpa
           else [sys.executable, 'tools/capture.py']) + argv
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                       timeout=600, env=dict(os.environ))
    if 'CAPTURE_OK' not in r.stdout:
        print((r.stdout + r.stderr)[-2000:])
        sys.exit(2)


def _rerata(p: Path, box):
    from PIL import Image
    im = Image.open(p).convert('RGB').crop(box)
    w, h = im.size
    tot = [0, 0, 0]
    for y in range(h):
        for x in range(w):
            c = im.getpixel((x, y))
            for i in range(3):
                tot[i] += c[i]
    n = max(1, w * h)
    return tuple(t / n for t in tot)


def main():
    tmp = Path(tempfile.mkdtemp(prefix='probe_cakram_'))
    a, b = tmp / 'a.png', tmp / 'b_tanpa_cakram.png'
    _tangkap(a, False)
    _tangkap(b, True)
    gagal = []
    for nama, box in WILAYAH.items():
        ra, rb = _rerata(a, box), _rerata(b, box)
        d = tuple(x - y for x, y in zip(ra, rb))
        print(f'{nama:14s} dengan={tuple(round(v, 1) for v in ra)} '
              f'tanpa={tuple(round(v, 1) for v in rb)} '
              f'selisih={tuple(round(v, 1) for v in d)}')
        if max(d) > 3.0:
            gagal.append(f'{nama}: cakram MENERANGKAN/mewarnai tanah '
                         f'(kanal naik {max(d):.1f})')
    if sum(_rerata(a, WILAYAH['kaki_pemain'])) - \
            sum(_rerata(b, WILAYAH['kaki_pemain'])) > -4.0:
        gagal.append('kaki_pemain: cakram tidak menggelapkan tanah')
    print(f'tangkapan: {a} {b}')
    if gagal:
        print('GAGAL: ' + '; '.join(gagal))
        sys.exit(1)
    print('LULUS')


if __name__ == '__main__':
    main()
