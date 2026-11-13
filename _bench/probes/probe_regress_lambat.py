"""probe_regress_lambat.py — jalankan tools/regress.py ASLI di "mesin lambat".

Lahir dari bug alat ukur 16 Okt 2026: di mesin sesi yang ~2x lebih lambat,
`arah_maju` menahan W 40 frame dengan tabrakan dimatikan, pemain farm menembus
petak portal greenhouse, dan sisa pemeriksaan scene mengukur greenhouse (689
entity, "W menyimpang 157 deg"). CI yang cepat tidak pernah melihatnya. Probe
ini membuat jendela lama-frame itu bisa diulang di mesin mana pun.

Yang dijalankan adalah `main()` regress.py apa adanya (jalur Game3D/app.py,
aturan #2). Probe hanya MEMBUNGKUS:
  - tiap fungsi `cek_*`  -> catat scene & jumlah entity sebelum/sesudah;
  - `Player3D.tick`       -> catat dt, dan jejak W selama `cek_arah_maju`;
  - `Player3D._check_portals` -> catat setiap portal yang terpicu.

Opsi:
  --lambat=MS      tambah time.sleep(MS) per frame lewat taskMgr (proksi mesin
                   lambat: dt-nya sama, sebaran beban CPU-nya tidak)
  --mutasi-basis   pasang DI MEMORI bug basis arah lama (komponen .y untuk .z)
                   di player.py; arah_maju harus GAGAL
  --sumber=PATH    regress.py lain (mis. salinan) sebagai yang diuji
  --no-lima        lewati subproses probe_lima_menit
Argumen lain diteruskan ke regress.py (mis. nama scene).

Keluaran: `_bench/regress/lambat/` (di-gitignore) -- laporan, PNG, dan log
jsonl. Berkas laporan regresi biasa di `_bench/regress/` tidak disentuh.

    xvfb-run -a -s "-screen 0 1024x768x24" python _bench/probes/probe_regress_lambat.py farm --lambat=50
    grep -c '"ev": "PORTAL"' _bench/regress/lambat/log_*.jsonl     # harus 0
"""
import builtins
import importlib.util
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KELUAR = ROOT / '_bench' / 'regress' / 'lambat'
KELUAR.mkdir(parents=True, exist_ok=True)
LOG = KELUAR / f'log_{int(time.time())}.jsonl'

no_lima = '--no-lima' in sys.argv
LAMBAT_MS = 0.0
MUTASI = False
SUMBER = ROOT / 'tools' / 'regress.py'
_sisa = []
for a in sys.argv[1:]:
    if a == '--no-lima':
        continue
    if a.startswith('--lambat='):
        LAMBAT_MS = float(a.split('=', 1)[1])
        continue
    if a == '--mutasi-basis':
        MUTASI = True
        continue
    if a.startswith('--sumber='):
        SUMBER = Path(a.split('=', 1)[1]).resolve()
        continue
    _sisa.append(a)
sys.argv = [str(ROOT / 'tools' / 'regress.py')] + _sisa
# regress.py meng-import probe_arah dari folder tools/ lewat __file__-nya.
sys.path.insert(0, str(ROOT / 'tools'))

spec = importlib.util.spec_from_file_location('regress', SUMBER)
R = importlib.util.module_from_spec(spec)
sys.modules['regress'] = R
spec.loader.exec_module(R)
R.OUT = KELUAR

_open = builtins.open


def _open_alih(p, *a, **k):
    if str(p).endswith('progress.jsonl'):
        p = KELUAR / 'progress.jsonl'
    return _open(p, *a, **k)


R.open = _open_alih

_fh = _open(LOG, 'w', encoding='utf-8')


def log(**kw):
    kw['t'] = round(time.time(), 3)
    _fh.write(json.dumps(kw, ensure_ascii=False) + '\n')
    _fh.flush()
    print('[PROBE]', json.dumps(kw, ensure_ascii=False), flush=True)


CTX = {'cek': None, 'scene_loop': None, 'dt_sum': 0.0, 'ticks': 0, 'dts': []}


def _ringkas(g):
    from ursina import scene as us
    try:
        return dict(state_scene=g.state.scene_name,
                    world_scene=g.world.scene_name,
                    n_children=len(us.children),
                    pos=[round(v, 2) for v in g.player.position],
                    tile=list(g.player.get_tile_pos()),
                    mode=getattr(g.panels, 'mode', '?'),
                    yaw=getattr(g, 'camera_yaw', None))
    except Exception as e:
        return dict(err=repr(e))


for nama in [n for n in dir(R) if n.startswith('cek_')]:
    asli = getattr(R, nama)

    def bungkus(*a, _asli=asli, _nama=nama, **k):
        g = a[0] if a and hasattr(a[0], 'state') else None
        if _nama == 'cek_geom_nol':
            CTX['scene_loop'] = a[0]
        sebelum = _ringkas(g) if g else None
        CTX.update(cek=_nama, dt_sum=0.0, ticks=0, dts=[])
        hasil = None
        try:
            hasil = _asli(*a, **k)
            return hasil
        finally:
            if g is not None:
                ent = dict(scene_loop=CTX['scene_loop'], cek=_nama,
                           ticks=CTX['ticks'], dt_sum=round(CTX['dt_sum'], 3),
                           dt_max=round(max(CTX['dts']), 3) if CTX['dts'] else None,
                           sebelum=sebelum, sesudah=_ringkas(g))
                if isinstance(hasil, tuple) and len(hasil) == 2 and isinstance(hasil[0], bool):
                    ent['hasil'] = list(hasil)
                log(**ent)
            CTX['cek'] = None

    setattr(R, nama, bungkus)

if MUTASI:
    # Bentuk bug "Arah WASD basis sumbu salah": basis gerak membaca komponen
    # tegak (.y) alih-alih (.z). Dipasang DI MEMORI; berkas repo tidak disentuh.
    import types
    import game
    _src = (ROOT / 'game' / 'player.py').read_text(encoding='utf-8')
    _A = '''                fwd_x, fwd_z = _wt.x - _w0.x, _wt.z - _w0.z
                right_x, right_z = _wr.x - _wt.x, _wr.z - _wt.z'''
    _B = '''                fwd_x, fwd_z = -(_wt.x - _w0.x), -(_wt.y - _w0.y)
                right_x, right_z = _wr.x - _wt.x, _wr.y - _wt.y'''
    assert _src.count(_A) == 1, 'pola mutasi tidak ketemu di player.py'
    _mod = types.ModuleType('game.player')
    _mod.__file__ = str(ROOT / 'game' / 'player.py')
    _mod.__package__ = 'game'
    sys.modules['game.player'] = _mod
    exec(compile(_src.replace(_A, _B), _mod.__file__, 'exec'), _mod.__dict__)
    game.player = _mod

import game.player as GP  # noqa: E402

_tick_asli = GP.Player3D.tick


def _tick(self, dt=None, panels=None):
    from ursina import time as utime
    d = dt if dt is not None else utime.dt
    CTX['dt_sum'] += d
    CTX['ticks'] += 1
    CTX['dts'].append(d)
    r = _tick_asli(self, dt, panels)
    if CTX['cek'] == 'cek_arah_maju':
        from ursina import held_keys
        if held_keys['w']:
            CTX.setdefault('jejak', []).append((d, self.x, self.z, self.state.scene_name))
        elif CTX.get('jejak'):
            j = CTX.pop('jejak')
            sdt = sum(t[0] for t in j)
            log(ev='SEGMEN_W', scene_loop=CTX['scene_loop'], n=len(j),
                dt_sum=round(sdt, 3), dt_rata=round(sdt / len(j), 4),
                x0=round(j[0][1], 2), z0=round(j[0][2], 2),
                x1=round(j[-1][1], 2), z1=round(j[-1][2], 2),
                scenes=sorted(set(t[3] for t in j)))
    return r


GP.Player3D.tick = _tick

_portal_asli = GP.Player3D._check_portals


def _portal(self, tx_i, ty_i):
    dari = self.state.scene_name
    r = _portal_asli(self, tx_i, ty_i)
    if r:
        log(ev='PORTAL', cek=CTX['cek'], scene_loop=CTX['scene_loop'],
            dari=dari, ke=self.state.scene_name, tile=[tx_i, ty_i],
            dt_sum_sejauh_ini=round(CTX['dt_sum'], 3), ticks=CTX['ticks'])
    return r


GP.Player3D._check_portals = _portal

if no_lima:
    import subprocess

    class _R:
        returncode = 0
        stdout = 'lima menit dilewati oleh probe: 0/0 lulus\n'
    subprocess.run = lambda *a, **k: _R()

if LAMBAT_MS > 0:
    import game.app as GA
    _init_asli = GA.Game3D.__init__

    def _init(self, *a, **k):
        _init_asli(self, *a, **k)
        from direct.showbase.ShowBaseGlobal import base

        def _tidur(task):
            time.sleep(LAMBAT_MS / 1000.0)
            return task.cont
        base.taskMgr.add(_tidur, 'probe_lambat')
    GA.Game3D.__init__ = _init

log(ev='MULAI', argv=sys.argv, log=str(LOG), lambat_ms=LAMBAT_MS,
    sumber=str(SUMBER), mutasi=MUTASI)
R.main()
