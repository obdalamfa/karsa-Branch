"""probe_lonjakan_scene.py — Cahaya harus sudah di targetnya sejak frame
pertama sesudah ganti scene.

Menjaga bug yang terukur 18 Okt 2026: `_init_env()` (snap saat ganti scene)
memakai tabel warna sendiri yang 33% lebih terang dari target lerp di
`update()`, dan lerp memakai dt tanpa jepit. Frame yang dirender tepat
sesudah scene dimuat membawa sun+amb merah 1,33 (p50 dunia 93,8 lawan 74,4
setelah tenang, +26%); di mesin sesi frame berikutnya membawa dt > 1 detik,
jadi lerp MELEWATI target ke 0,91 (target 1,00, p50 68,8) lalu merangkak
naik ~30 frame. Di mesin cepat yang terlihat lonjakan terang yang meredup.

Jalur asli: Game3D lewat probe_cahaya._boot (fixture, scene lewat
state.scene_name), lalu ganti scene LAGI lewat state.scene_name.

    xvfb-run -a -s "-screen 0 1024x768x24" python _bench/probes/probe_lonjakan_scene.py
    ... probe_lonjakan_scene.py --mutasi    # pasang lagi angka _init_env lama: harus GAGAL

Keluar 0 kalau lulus, 1 kalau gagal.
"""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / '_bench' / 'probes'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dari', default='farm')
    ap.add_argument('--ke', default='town')
    ap.add_argument('--hour', type=float, default=10.0)
    ap.add_argument('--mutasi', action='store_true',
                    help='pasang di memori angka snap _init_env lama (255,248,215 / 95,90,78)')
    a = ap.parse_args()

    import probe_cahaya as pc
    args = argparse.Namespace(scene=a.dari, hour=a.hour,
                              save='tools/fixtures/ladang_hari10_save.json',
                              scroll=0, width=640, height=360)
    g, base, save = pc._boot(args)
    if a.mutasi:
        from ursina import Vec4
        asli = type(g)._init_env

        def _init_env_lama(self):
            asli(self)
            if not self.world.scene_obj.indoor:
                self.sun.color = Vec4(255 / 255, 248 / 255, 215 / 255, 1)
                self.ambient.color = Vec4(95 / 255, 90 / 255, 78 / 255, 1)
                self._sync_smooth_lighting()
        type(g)._init_env = _init_env_lama
        print('MUTASI: angka snap _init_env lama dipasang')

    for _ in range(60):
        pc._tahan_jam(g, a.hour)
        base.taskMgr.step()
    out = ROOT / '_bench' / 'shots' / 'lonjakan'
    out.mkdir(parents=True, exist_ok=True)
    g.state.scene_name = a.ke
    rec = []
    for i in range(45):
        pc._tahan_jam(g, a.hour)
        base.taskMgr.step()
        if g.world.scene_name != a.ke:
            continue
        s, m = g.sun.color, g.ambient.color
        r = {'f': i, 'sun+amb': [round(s[k] + m[k], 3) for k in range(3)]}
        # Frame PERTAMA tempat scene baru sudah dimuat ikut diukur: itu frame
        # yang dirender dengan warna snap _init_env, sebelum lerp mana pun.
        # Tanpa frame itu, jepitan dt di mesin lambat menutupi tabel snap
        # yang salah (lerp dengan k=1 langsung mendarat di target).
        if not rec or i in (2, 4, 44):
            r['p50'] = pc._statistik_dunia(pc._tembak(base, out / f'f{i:02d}.png'))['p50']
        rec.append(r)
    for r in rec:
        if 'p50' in r:
            print(json.dumps(r))
    awal = [r for r in rec if 'p50' in r][0]
    akhir = rec[-1]
    beda_lampu = max(abs(x - y) for x, y in zip(awal['sun+amb'], akhir['sun+amb']))
    beda_p50 = abs(awal['p50'] - akhir['p50']) / max(1.0, akhir['p50'])
    ok = beda_lampu < 0.01 and beda_p50 < 0.02
    print(f"{'LULUS' if ok else 'GAGAL'}: frame {awal['f']} sesudah ganti scene "
          f"sun+amb {awal['sun+amb']} lawan tenang {akhir['sun+amb']} "
          f"(beda {beda_lampu:.3f}); p50 dunia {awal['p50']} lawan {akhir['p50']} "
          f"({beda_p50:.1%})")
    sys.stdout.flush()
    save.unlink(missing_ok=True)
    os._exit(0 if ok else 1)


if __name__ == '__main__':
    main()
