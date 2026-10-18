"""probe_buy_sinema.py — dua mode yang ditelan jaring di app.py, lewat app.input.

  S  ESC saat sinema intro. '[ESC] lewati' tertulis di layar, tapi jaring ESC
     global (app.py, `mode not in ('hud', 'chargen')`) menangkapnya lebih dulu:
     mode jadi 'hud', sinema.aktif tetap True, UI sinema tetap di layar.
  L  [L] membuka Bangun/Beli. `_pulihkan_mode_yatim` tidak mengenal 'buy', jadi
     mode kembali ke 'hud' satu frame kemudian dan panel tertinggal di layar.

Tiap fase subproses sendiri (Game3D sekali per proses, sinema intro sekali per
pemain). Alat jalur asli dipinjam dari tools/probe_batin.py.

    python _bench/probes/probe_buy_sinema.py      # keluar 1 kalau ada yang gagal
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT))


def fase(nama, save):
    import probe_batin as pb
    g = pb.boot(Path(save))
    p = g.panels
    hasil = []

    def cek(n, ok, ket=''):
        hasil.append([n, bool(ok), str(ket)])

    if nama == 'S':
        pb.tekan(g, 'enter', 5)                       # chargen -> sinema
        for _ in range(40):                           # sinema benar-benar berjalan
            pb.langkah(1)
        jalan = g.sinema.aktif and p.mode == 'sinema'
        if not jalan:                                 # prasyarat: hanya dilaporkan bila gagal
            cek('S prasyarat: sinema intro berjalan sebelum ESC', False,
                f'aktif={g.sinema.aktif} mode={p.mode}')
        nama_sinema = g.sinema.nama
        pb.tekan(g, 'escape', 5)
        sisa = pb.ui_sinema_hidup(g)
        cek('S ESC menyelesaikan sinema (aktif False, nol UI sinema)',
            jalan and not g.sinema.aktif and not sisa,
            f'aktif={g.sinema.aktif} ui_sinema={len(sisa)} mode={p.mode}')
        cek('S sinema tercatat selesai, mode hud',
            jalan and nama_sinema in g.state.sinema_selesai and p.mode == 'hud',
            f'{nama_sinema!r} in sinema_selesai={nama_sinema in g.state.sinema_selesai}')
    else:
        ok = pb.ke_hud(g)
        if not (ok and not g.sinema.aktif):           # prasyarat: hanya dilaporkan bila gagal
            cek('L prasyarat: HUD lewat SPACE', False, f'mode={p.mode}')
        pb.tekan(g, 'l', 3)
        hidup = [e for e in p._buy_ents if e.enabled]
        cek('L [L] membuka Bangun/Beli dan bertahan 3 frame',
            p.mode == 'buy' and hidup, f'mode={p.mode} ents_hidup={len(hidup)}')
        sel0 = p._buy_sel
        pb.tekan(g, 's', 2)
        cek('L [S] menggeser pilihan katalog', p.mode == 'buy' and p._buy_sel != sel0,
            f'_buy_sel {sel0}->{p._buy_sel} mode={p.mode}')
        pb.tekan(g, 'escape', 3)
        hidup = [e for e in p._buy_ents if e.enabled]
        cek('L ESC menutup panel: mode hud, nol entity panel tersisa',
            p.mode == 'hud' and not hidup, f'mode={p.mode} ents_hidup={len(hidup)}')
    for h in hasil:
        print('CEK ' + json.dumps(h, ensure_ascii=False))
    sys.stdout.flush()
    os._exit(0)


def main():
    if '--fase' in sys.argv:
        i = sys.argv.index('--fase')
        fase(sys.argv[i + 1], sys.argv[i + 2])
        return
    kerja = Path(tempfile.mkdtemp(prefix='probe_buy_sinema_'))
    semua = []
    for f in ('S', 'L'):
        r = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--fase', f,
                            str(kerja / f'{f}.json')], cwd=ROOT, capture_output=True,
                           text=True, timeout=600)
        (kerja / f'{f}.log').write_text(r.stdout + '\n' + r.stderr, encoding='utf-8')
        baris = [json.loads(b[4:]) for b in r.stdout.splitlines() if b.startswith('CEK ')]
        semua += baris or [[f'{f} subproses tanpa hasil', False,
                            (r.stderr.strip().splitlines() or ['?'])[-1][:100]]]
    print('\nBUY + ESC SINEMA — lewat app.input')
    print('=' * 78)
    for n, ok, ket in semua:
        print(f"{'LULUS' if ok else 'GAGAL':>5s}  {n:<58s}  {ket[:80]}")
    gagal = [n for n, ok, _ in semua if not ok]
    print('-' * 78)
    print(f'{len(semua) - len(gagal)}/{len(semua)} lulus  (log: {kerja})')
    sys.stdout.flush()
    os._exit(1 if gagal else 0)


if __name__ == '__main__':
    main()
