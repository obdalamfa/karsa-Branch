"""ab_sheet.py — Lembar banding BUTA: punya kita vs klip patokan, label dicopot.

Kritikus tidak boleh tahu mana yang mana. Kalau ia tahu, ia menilai reputasi,
bukan gambar. Jadi alat ini:

  1. mengambil N frame dari KEDUA klip pada waktu ternormalisasi yang sama
  2. menyusunnya jadi dua baris berlabel cuma "A" dan "B"
  3. mengacak urutan A/B dengan benih acak
  4. menulis kuncinya ke berkas TERPISAH yang tidak ikut ke kritikus

Kritikus melihat lembarnya, memilih baris yang lebih baik, lalu menyebut satu
celah terbesar. Orkestrator baru membuka kuncinya SESUDAH putusan masuk.

Klip patokan harus disediakan sendiri di `_bench/bar/`. Alat ini TIDAK akan
mengarang pembanding: kalau klip patokannya tidak ada ia berhenti dengan kode
keluar 3 dan mengatakan apa yang kurang. Perbandingan buta melawan ingatan
bukan perbandingan buta — itu justru hal yang mau dihindari.

Pemakaian:
    python tools/ab_sheet.py --slice gosok --round 1 \\
        --ours _bench/clips/gosok.mp4 --bar _bench/bar/awl_brush.mp4 \\
        --frames 8 --seed 7

    python tools/ab_sheet.py --reveal _bench/sheets/gosok_r1.png
"""
from __future__ import annotations

import argparse
import json
import math
import random
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BENCH = ROOT / '_bench'
SHEETS = BENCH / 'sheets'
BAR = BENCH / 'bar'


def ffmpeg() -> str:
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def probe_duration(path: Path) -> float:
    r = subprocess.run([ffmpeg(), '-i', str(path)], capture_output=True, text=True)
    for line in r.stderr.splitlines():
        if 'Duration:' in line:
            t = line.split('Duration:')[1].split(',')[0].strip()
            h, m, s = t.split(':')
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 0.0


def grab(path: Path, times: list[float], outdir: Path, tag: str) -> list[Path]:
    out = []
    for i, t in enumerate(times):
        p = outdir / f'{tag}{i:03d}.png'
        r = subprocess.run(
            [ffmpeg(), '-y', '-loglevel', 'error', '-ss', f'{t:.3f}',
             '-i', str(path), '-frames:v', '1', str(p)],
            capture_output=True, text=True)
        if r.returncode != 0 or not p.exists():
            raise SystemExit(f'gagal mengambil frame {t:.2f}s dari {path}: '
                             f'{r.stderr[-300:]}')
        out.append(p)
    return out


def build(args) -> int:
    from PIL import Image, ImageDraw

    ours = Path(args.ours)
    bar = Path(args.bar) if args.bar else None

    if not ours.exists():
        print(f'AB_FAIL: klip kita tidak ada: {ours}', file=sys.stderr)
        return 2

    if bar is None or not bar.exists():
        BAR.mkdir(parents=True, exist_ok=True)
        ada = sorted(p.name for p in BAR.glob('*.mp4'))
        print('AB_FAIL: tidak ada klip patokan — perbandingan buta tidak bisa '
              'dijalankan.', file=sys.stderr)
        print(f'  dicari di : {BAR}', file=sys.stderr)
        print(f'  isi folder: {ada or "(kosong)"}', file=sys.stderr)
        print('  Taruh klip gameplay patokan di sana lalu ulangi. Alat ini '
              'sengaja TIDAK menilai lawan ingatan.', file=sys.stderr)
        return 3

    SHEETS.mkdir(parents=True, exist_ok=True)
    n = args.frames
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        d_ours = probe_duration(ours)
        d_bar = probe_duration(bar)
        if d_ours <= 0 or d_bar <= 0:
            print('AB_FAIL: durasi klip tidak terbaca', file=sys.stderr)
            return 2
        # Waktu ternormalisasi sama untuk keduanya: aksi yang sama, panjang
        # berbeda, harus dibandingkan pada FASE yang sama, bukan detik yang sama.
        fr = [(i + 0.5) / n for i in range(n)]
        po = grab(ours, [f * d_ours for f in fr], td, 'o')
        pb = grab(bar, [f * d_bar for f in fr], td, 'b')

        rng = random.Random(args.seed)
        atas_kita = rng.random() < 0.5
        baris = [(po, 'A') if atas_kita else (pb, 'A'),
                 (pb, 'B') if atas_kita else (po, 'B')]

        TW = 260
        ims = [[Image.open(p).convert('RGB') for p in r[0]] for r in baris]
        TH = max(1, round(ims[0][0].height * TW / ims[0][0].width))
        LAB = 26
        W = TW * n + 34
        H = (TH + LAB) * 2 + 14
        sheet = Image.new('RGB', (W, H), (14, 16, 18))
        d = ImageDraw.Draw(sheet)
        for ri, row in enumerate(ims):
            y = 8 + ri * (TH + LAB)
            d.text((8, y + TH // 2), baris[ri][1], fill=(240, 232, 200))
            for ci, im in enumerate(row):
                x = 30 + ci * TW
                sheet.paste(im.resize((TW, TH), Image.LANCZOS), (x, y))
                d.text((x + 4, y + TH + 5), f'fase {fr[ci]*100:.0f}%',
                       fill=(150, 160, 165))
        out = SHEETS / f'{args.slice}_r{args.round}.png'
        sheet.save(out)

    key = SHEETS / f'.{args.slice}_r{args.round}.key.json'
    key.write_text(json.dumps({
        'A': 'ours' if atas_kita else 'bar',
        'B': 'bar' if atas_kita else 'ours',
        'ours': str(ours), 'bar': str(bar), 'seed': args.seed,
    }, indent=1), encoding='utf-8')

    print(f'AB_OK {out}')
    print(f'  kunci (JANGAN dibaca kritikus): {key}')
    return 0


def reveal(path: Path) -> int:
    key = path.parent / f'.{path.stem}.key.json'
    if not key.exists():
        print(f'tidak ada kunci untuk {path}', file=sys.stderr)
        return 2
    print(key.read_text(encoding='utf-8'))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--reveal', default=None)
    ap.add_argument('--slice', default='x')
    ap.add_argument('--round', type=int, default=1)
    ap.add_argument('--ours', default='')
    ap.add_argument('--bar', default='')
    ap.add_argument('--frames', type=int, default=8)
    ap.add_argument('--seed', type=int, default=0)
    args = ap.parse_args()
    if args.reveal:
        return reveal(Path(args.reveal))
    if not args.seed:
        args.seed = random.randrange(1, 10**6)
    return build(args)


if __name__ == '__main__':
    sys.exit(main())
