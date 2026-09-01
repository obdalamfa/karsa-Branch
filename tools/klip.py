"""klip.py — patokan untuk GERAK, bukan untuk gambar diam.

Kenapa alat ini ada
===================

`bar_gate.py` menjaga delapan frame diam, dan itu cukup untuk menilai bentuk
karakter, warna tanah, dan letak HUD. Ia tidak cukup untuk menilai apa pun yang
bergerak. Animasi panen yang hidup dan pose panen yang BEKU menghasilkan
tangkapan layar yang sama persis — kritikus yang cuma melihat satu frame akan
meluluskan keduanya, dan yang beku akan lolos.

Jadi patokan gerak disimpan sebagai STRIP: N frame berjarak tetap disusun jadi
satu gambar. Kritikus melihat waktu di dalam satu gambar, dan strip beku
langsung ketahuan karena semua ubinnya identik.

Strip kita dibuat `tools/capture.py --strip`. Strip patokan dibuat di sini.
Keduanya harus punya JUMLAH UBIN DAN UKURAN UBIN YANG SAMA — kalau tidak,
kritikus bisa menebak mana yang mana dari bentuknya saja, dan "buta" batal.
Itulah kenapa `--ubin` dan `--n` ada di kedua sisi dan default-nya sama.

Pemakaian
=========

    # 1. Cari dulu detik ke berapa gerakannya terjadi. Jangan menebak.
    python tools/klip.py pindai _bench/refs/_video/awl_x.mp4 --tiap 10

    # 2. Ambil strip pada detik yang sudah dilihat sendiri.
    python tools/klip.py ambil _bench/refs/_video/awl_x.mp4 \\
        --mulai 137 --n 6 --jeda 0.30 --slug gerak_panen

    # 3. Periksa semua strip gerak yang sudah ada.
    python tools/klip.py status

`pindai` menulis satu contact sheet berlabel detik. Itu bukan kemewahan: memilih
timestamp tanpa melihat videonya sama saja dengan mengarang patokan, yang
persis lubang yang `bar_gate.py` dibuat untuk menutup.

BERKASNYA TIDAK BOLEH DI-COMMIT. Sama seperti frame diam: repo ini publik dan
isinya karya orang lain. `_bench/.gitignore` menjaganya dan `bar_gate.py check`
menolak jalan kalau ada yang bocor.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REFS = ROOT / '_bench' / 'refs'
VIDEO = REFS / '_video'
PINDAI = REFS / '_pindai'
MANIFEST = REFS / 'MANIFEST.json'

# Default ini HARUS sama dengan default `tools/capture.py --strip`, karena
# strip kita dan strip patokan dibandingkan berdampingan. Ubin 960x540 adalah
# 16:9 — rasio yang sama dengan jendela permainan — jadi tidak ada yang
# ter-crop dan tidak ada yang teregang.
UBIN_W, UBIN_H = 960, 540
N_DEFAULT = 6


def _ffmpeg() -> str:
    exe = shutil.which('ffmpeg')
    if not exe:
        sys.exit('Butuh `ffmpeg` di PATH.')
    return exe


def _durasi(video: Path) -> float:
    """Durasi video dalam detik, dibaca ffprobe kalau ada, kalau tidak ffmpeg."""
    probe = shutil.which('ffprobe')
    if probe:
        out = subprocess.run(
            [probe, '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=nw=1:nk=1', str(video)],
            capture_output=True, text=True)
        try:
            return float(out.stdout.strip())
        except ValueError:
            pass
    out = subprocess.run([_ffmpeg(), '-i', str(video)],
                         capture_output=True, text=True)
    for baris in out.stderr.splitlines():
        if 'Duration:' in baris:
            jam = baris.split('Duration:')[1].split(',')[0].strip()
            h, m, d = jam.split(':')
            return int(h) * 3600 + int(m) * 60 + float(d)
    sys.exit(f'tidak bisa membaca durasi: {video}')


def _ambil_frame(video: Path, detik: float, tujuan: Path) -> bool:
    tujuan.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        [_ffmpeg(), '-y', '-loglevel', 'error', '-ss', f'{detik:.3f}',
         '-i', str(video), '-frames:v', '1', str(tujuan)],
        capture_output=True, text=True)
    return r.returncode == 0 and tujuan.exists() and tujuan.stat().st_size > 0


# ─── pindai ───────────────────────────────────────────────

def perintah_pindai(args):
    """Contact sheet berlabel detik, supaya timestamp dipilih dengan MELIHAT."""
    from PIL import Image, ImageDraw
    video = Path(args.video)
    if not video.exists():
        sys.exit(f'video tidak ada: {video}')
    total = _durasi(video)
    mulai = args.mulai
    akhir = args.akhir if args.akhir is not None else total
    detik_list = []
    t = mulai
    while t < akhir and len(detik_list) < args.maks:
        detik_list.append(t)
        t += args.tiap
    print(f'{video.name}: durasi {total:.0f}s, {len(detik_list)} sampel '
          f'tiap {args.tiap}s dari {mulai:.0f}s')

    PINDAI.mkdir(parents=True, exist_ok=True)
    tmp = PINDAI / f'_tmp_{video.stem}'
    tmp.mkdir(parents=True, exist_ok=True)
    ims, label = [], []
    for d in detik_list:
        fp = tmp / f'{int(d):06d}.png'
        if _ambil_frame(video, d, fp):
            ims.append(Image.open(fp).convert('RGB'))
            label.append(f'{int(d)//60:d}:{int(d)%60:02d}  ({int(d)}s)')
    if not ims:
        sys.exit('tidak ada frame yang berhasil diambil')

    TW, TH, BAR = 400, 225, 20
    cols = args.kolom
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * TW, rows * (TH + BAR)), (16, 16, 18))
    d_ = ImageDraw.Draw(sheet)
    for i, (im, lb) in enumerate(zip(ims, label)):
        x, y = (i % cols) * TW, (i // cols) * (TH + BAR)
        sheet.paste(im.resize((TW, TH), Image.LANCZOS), (x, y + BAR))
        d_.text((x + 6, y + 5), lb, fill=(255, 226, 120))
    out = Path(args.out) if args.out else PINDAI / f'{video.stem}_pindai.png'
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f'sheet: {out}  ({sheet.size[0]}x{sheet.size[1]})')
    return 0


# ─── ambil ────────────────────────────────────────────────

def perintah_ambil(args):
    """Susun strip patokan: N ubin, jarak tetap, ukuran ubin dikunci."""
    from PIL import Image
    video = Path(args.video)
    if not video.exists():
        sys.exit(f'video tidak ada: {video}')

    tmp = REFS / '_tmp_klip'
    tmp.mkdir(parents=True, exist_ok=True)
    ims = []
    for i in range(args.n):
        d = args.mulai + i * args.jeda
        fp = tmp / f'{i:02d}.png'
        if not _ambil_frame(video, d, fp):
            shutil.rmtree(tmp, ignore_errors=True)
            sys.exit(f'gagal mengambil frame pada detik {d:.2f}')
        ims.append(Image.open(fp).convert('RGB').resize(
            (args.ubin_w, args.ubin_h), Image.LANCZOS))

    strip = Image.new('RGB', (args.ubin_w * len(ims), args.ubin_h), (0, 0, 0))
    for i, im in enumerate(ims):
        strip.paste(im, (i * args.ubin_w, 0))

    out = Path(args.out) if args.out else REFS / f'{args.slug}.png'
    out.parent.mkdir(parents=True, exist_ok=True)
    strip.save(out)

    gif = out.with_suffix('.gif')
    kecil = [im.resize((args.ubin_w // 2, args.ubin_h // 2), Image.LANCZOS)
             for im in ims]
    kecil[0].save(gif, save_all=True, append_images=kecil[1:],
                  duration=int(args.jeda * 1000), loop=0, optimize=True)
    shutil.rmtree(tmp, ignore_errors=True)

    # Strip yang semua ubinnya identik bukan patokan gerak — ia patokan diam
    # yang diulang. Diukur, bukan dipercaya: kalau ini lolos tanpa peringatan,
    # kritikus akan membandingkan gerak kita dengan kebekuan.
    beda = _keragaman(ims)
    print(f'strip : {out}  {len(ims)} ubin {args.ubin_w}x{args.ubin_h}')
    print(f'gif   : {gif}')
    print(f'gerak : {beda:.1%} piksel berubah antar ubin berturutan')
    if beda < 0.02:
        print('PERINGATAN: ubin nyaris identik — ini bukan potongan yang bergerak.')
        return 1
    return 0


def _keragaman(ims) -> float:
    """Rata-rata pecahan piksel yang berubah antara ubin berturutan."""
    import itertools
    kecil = [im.resize((96, 54)) for im in ims]
    total, n = 0.0, 0
    for a, b in itertools.pairwise(kecil):
        pa, pb = list(a.getdata()), list(b.getdata())
        beda = sum(1 for x, y in zip(pa, pb)
                   if abs(x[0]-y[0]) + abs(x[1]-y[1]) + abs(x[2]-y[2]) > 24)
        total += beda / len(pa)
        n += 1
    return total / max(1, n)


# ─── status ───────────────────────────────────────────────

def perintah_status(_args):
    if not MANIFEST.exists():
        sys.exit(f'MANIFEST tidak ada: {MANIFEST}')
    data = json.loads(MANIFEST.read_text(encoding='utf-8'))
    klip = data.get('klip') or []
    if not klip:
        print('MANIFEST belum punya daftar `klip`.')
        return 1
    from PIL import Image
    siap = 0
    for it in klip:
        slug = it['slug']
        p = REFS / f'{slug}.png'
        if not p.exists():
            print(f'  KOSONG  {slug:<20} {it.get("catatan","")[:60]}')
            continue
        with Image.open(p) as im:
            w, h = im.size
        n = w // max(1, h * 16 // 9) if h else 0
        print(f'  SIAP    {slug:<20} {w}x{h}  ~{n} ubin')
        siap += 1
    print(f'\n{siap}/{len(klip)} klip patokan siap.')
    return 0 if siap == len(klip) else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='perintah', required=True)

    p = sub.add_parser('pindai', help='contact sheet berlabel detik')
    p.add_argument('video')
    p.add_argument('--tiap', type=float, default=10.0)
    p.add_argument('--mulai', type=float, default=0.0)
    p.add_argument('--akhir', type=float, default=None)
    p.add_argument('--maks', type=int, default=60)
    p.add_argument('--kolom', type=int, default=6)
    p.add_argument('--out', default=None)

    a = sub.add_parser('ambil', help='susun strip patokan dari video')
    a.add_argument('video')
    a.add_argument('--mulai', type=float, required=True)
    a.add_argument('--n', type=int, default=N_DEFAULT)
    a.add_argument('--jeda', type=float, default=0.30)
    a.add_argument('--slug', default=None)
    a.add_argument('--out', default=None)
    a.add_argument('--ubin-w', type=int, default=UBIN_W)
    a.add_argument('--ubin-h', type=int, default=UBIN_H)

    sub.add_parser('status', help='daftar klip patokan yang sudah ada')

    args = ap.parse_args()
    if args.perintah == 'ambil' and not (args.slug or args.out):
        ap.error('butuh --slug atau --out')
    return {'pindai': perintah_pindai,
            'ambil': perintah_ambil,
            'status': perintah_status}[args.perintah](args)


if __name__ == '__main__':
    sys.exit(main())
