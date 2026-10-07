"""ambil_patokan.py — kumpulkan delapan frame patokan AWL di mesin Anda.

DIJALANKAN DI MESIN ANDA, bukan di sesi web. Egress sesi web ditolak
kebijakan jaringan — terukur: `403 to CONNECT (policy denial)` untuk
`images.ctfassets.net`, `store.steampowered.com`, `youtube.com`, dan
`google.com`. Skrip ini tidak akan pernah berhasil dari sana, dan itu bukan
sesuatu yang bisa diakali dari dalam.

Kenapa tidak menulis URL langsung di dalam kode: URL gambar Steam memuat hash
40 heksadesimal per tangkapan layar yang tidak bisa ditebak, dan appid yang
salah menghasilkan 404 atau — lebih buruk — gambar game lain. Jadi appid
dicari lewat API, dan daftar tangkapan layarnya diminta dari API, bukan
diketik. Tidak ada satu pun URL gambar yang ditulis tangan di berkas ini.

YANG SENGAJA TIDAK DILAKUKAN SKRIP INI: menentukan sendiri tangkapan layar
mana yang jadi `barn_interior` dan mana yang jadi `evening_light`. Ia tidak
tahu, dan menebaknya berarti mengisi gerbang dengan frame yang salah lalu
menyerahkan perbandingan yang tercemar ke kritikus. Pemetaannya penilaian
Anda; skrip cuma mengunduh, memeriksa, dan memasang apa yang Anda tunjuk.

    python tools/ambil_patokan.py cari                  # temukan appid-nya
    python tools/ambil_patokan.py steam --appid 1953910 # unduh semua kandidat
    python tools/ambil_patokan.py video <url|berkas> --detik 90 240 615
    python tools/ambil_patokan.py daftar                # lihat kandidat
    python tools/ambil_patokan.py pasang steam_04 barn_interior
    python tools/ambil_patokan.py status                # 8 slug, mana yang siap

Butuh `requests` dan `Pillow` (keduanya sudah dipakai repo ini). Mode `video`
tambahan butuh `yt-dlp` dan `ffmpeg` di PATH — hanya kalau dipakai.

BERKASNYA TIDAK BOLEH DI-COMMIT. `_bench/.gitignore` sudah menjaganya dan
`bar_gate.py check` menolak jalan kalau ada yang bocor. Repo ini publik;
menyimpan frame lokal untuk pembandingan internal sah, meng-commitnya tidak.
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
KANDIDAT = REFS / '_kandidat'
MANIFEST = REFS / 'MANIFEST.json'

# Sama persis dengan tools/bar_gate.py — gerbang yang sama, syarat yang sama.
MIN_BYTES = 20_000
MIN_SISI_GERBANG = 480
# MANIFEST menuntut lebih ketat daripada gerbang: 1280x720.
MIN_LEBAR, MIN_TINGGI = 1280, 720

EKSTENSI = ('.png', '.jpg', '.jpeg', '.webp')
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/124.0 Safari/537.36')


# ─── bantu ────────────────────────────────────────────────

def _slug_manifest() -> list[dict]:
    if not MANIFEST.exists():
        sys.exit(f'MANIFEST tidak ada: {MANIFEST}')
    return json.loads(MANIFEST.read_text(encoding='utf-8'))['frames']


def _periksa_gambar(p: Path) -> tuple[bool, str]:
    """Syarat yang sama dengan bar_gate, plus 1280x720 dari MANIFEST."""
    n = p.stat().st_size
    if n < MIN_BYTES:
        return False, f'cuma {n} B — placeholder, bukan patokan'
    try:
        from PIL import Image
        with Image.open(p) as im:
            w, h = im.size
            fmt = im.format
    except Exception as e:
        return False, f'bukan gambar yang bisa dibuka ({e})'
    if min(w, h) < MIN_SISI_GERBANG:
        return False, f'{w}x{h} terlalu kecil untuk dibandingkan'
    if w < MIN_LEBAR or h < MIN_TINGGI:
        return True, (f'{fmt} {w}x{h}, {n // 1024} KiB — LOLOS gerbang tapi '
                      f'di bawah 1280x720 yang diminta MANIFEST')
    return True, f'{fmt} {w}x{h}, {n // 1024} KiB'


def _sesi():
    try:
        import requests
    except ImportError:
        sys.exit('Butuh `requests`. Pasang: pip install requests')
    s = requests.Session()
    s.headers.update({'User-Agent': UA})
    return s


def _unduh(sesi, url: str, tujuan: Path) -> tuple[bool, str]:
    try:
        r = sesi.get(url, timeout=30)
    except Exception as e:
        return False, f'{type(e).__name__}: {e}'
    if r.status_code != 200:
        return False, f'HTTP {r.status_code}'
    if not r.content:
        return False, 'balasan kosong'
    tujuan.parent.mkdir(parents=True, exist_ok=True)
    tujuan.write_bytes(r.content)
    ok, catatan = _periksa_gambar(tujuan)
    if not ok:
        tujuan.unlink(missing_ok=True)
        return False, catatan
    return True, catatan


# ─── perintah ─────────────────────────────────────────────

def perintah_cari(args):
    """Cari appid lewat API pencarian toko Steam."""
    sesi = _sesi()
    url = 'https://store.steampowered.com/api/storesearch/'
    try:
        r = sesi.get(url, params={'term': args.istilah, 'cc': 'us', 'l': 'en'},
                     timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        sys.exit(f'Pencarian gagal: {type(e).__name__}: {e}\n'
                 f'Kalau ini ProxyError, Anda menjalankannya di sesi web — '
                 f'jalankan di mesin sendiri.')
    hasil = data.get('items') or []
    if not hasil:
        sys.exit(f'Tidak ada hasil untuk "{args.istilah}".')
    print(f'\nHasil untuk "{args.istilah}":\n')
    for it in hasil[:10]:
        print(f'  appid {it.get("id"):>8}  {it.get("name")}')
    print(f'\nLalu:  python tools/ambil_patokan.py steam --appid '
          f'{hasil[0].get("id")}\n')


def perintah_steam(args):
    """Unduh semua tangkapan layar resmi satu appid sebagai kandidat."""
    sesi = _sesi()
    try:
        r = sesi.get('https://store.steampowered.com/api/appdetails',
                     params={'appids': str(args.appid), 'l': 'en'}, timeout=30)
        r.raise_for_status()
        data = r.json()[str(args.appid)]
    except Exception as e:
        sys.exit(f'Gagal mengambil detail app: {type(e).__name__}: {e}\n'
                 f'Kalau ini ProxyError, jalankan di mesin sendiri.')
    if not data.get('success'):
        sys.exit(f'appid {args.appid} tidak dikenal Steam.')
    d = data['data']
    tembakan = d.get('screenshots') or []
    if not tembakan:
        sys.exit(f'"{d.get("name")}" tidak punya tangkapan layar di Steam.')

    print(f'\n{d.get("name")}  (appid {args.appid})')
    print(f'{len(tembakan)} tangkapan layar. Mengunduh ke {KANDIDAT}/\n')
    KANDIDAT.mkdir(parents=True, exist_ok=True)
    berhasil = 0
    for i, t in enumerate(tembakan, 1):
        url = t.get('path_full') or t.get('path_thumbnail')
        if not url:
            continue
        ext = Path(url.split('?')[0]).suffix or '.jpg'
        tujuan = KANDIDAT / f'steam_{i:02d}{ext}'
        ok, catatan = _unduh(sesi, url, tujuan)
        tanda = 'OK  ' if ok else 'GAGAL'
        print(f'  [{tanda}] steam_{i:02d}  {catatan}')
        berhasil += ok
    print(f'\n{berhasil}/{len(tembakan)} terunduh dan lolos pemeriksaan.')
    print('Lihat berkasnya, lalu pasang yang cocok:\n'
          '  python tools/ambil_patokan.py pasang steam_04 barn_interior\n')


def perintah_video(args):
    """Ambil frame dari video gameplay, pada detik yang Anda tunjuk.

    Frame video sah menurut MANIFEST — itu tetap game yang merender dirinya.
    Yang ditolak art resmi, render, still cutscene, dan frame trailer, jadi
    pilih video gameplay biasa, bukan trailer.
    """
    if not shutil.which('ffmpeg'):
        sys.exit('Butuh `ffmpeg` di PATH.')
    KANDIDAT.mkdir(parents=True, exist_ok=True)

    sumber = args.sumber
    sementara = None
    if sumber.startswith(('http://', 'https://')):
        if not shutil.which('yt-dlp'):
            sys.exit('Sumber berupa URL butuh `yt-dlp` di PATH.\n'
                     'Pasang: pip install yt-dlp')
        sementara = KANDIDAT / '_sumber.mp4'
        print(f'Mengunduh video ke {sementara} ...')
        p = subprocess.run(
            ['yt-dlp', '-f', 'bestvideo[height>=720]/best', '--no-playlist',
             '-o', str(sementara), sumber])
        if p.returncode != 0 or not sementara.exists():
            sys.exit('yt-dlp gagal.')
        sumber = str(sementara)
    elif not Path(sumber).exists():
        sys.exit(f'Berkas tidak ada: {sumber}')

    print()
    for detik in args.detik:
        tujuan = KANDIDAT / f'video_{int(detik):06d}.png'
        p = subprocess.run(
            ['ffmpeg', '-y', '-loglevel', 'error', '-ss', str(detik),
             '-i', sumber, '-frames:v', '1', str(tujuan)])
        if p.returncode != 0 or not tujuan.exists():
            print(f'  [GAGAL] detik {detik}')
            continue
        ok, catatan = _periksa_gambar(tujuan)
        if not ok:
            tujuan.unlink(missing_ok=True)
            print(f'  [GAGAL] detik {detik}: {catatan}')
        else:
            print(f'  [OK  ] video_{int(detik):06d}  {catatan}')
    print(f'\nKandidat di {KANDIDAT}/. Pasang yang cocok dengan `pasang`.\n')


def perintah_daftar(_args):
    if not KANDIDAT.exists():
        sys.exit(f'Belum ada kandidat. Jalankan `steam` atau `video` dulu.')
    berkas = sorted(p for p in KANDIDAT.iterdir()
                    if p.suffix.lower() in EKSTENSI)
    if not berkas:
        sys.exit('Folder kandidat kosong.')
    print(f'\n{len(berkas)} kandidat di {KANDIDAT}/\n')
    for p in berkas:
        ok, catatan = _periksa_gambar(p)
        print(f'  {"OK" if ok else "TOLAK":6s} {p.stem:22s} {catatan}')
    print()


def perintah_pasang(args):
    """Salin satu kandidat jadi slug patokan, setelah diperiksa."""
    slugs = {f['slug'] for f in _slug_manifest()}
    if args.slug not in slugs:
        sys.exit(f'"{args.slug}" bukan slug MANIFEST.\n'
                 f'Yang sah: {", ".join(sorted(slugs))}')

    cocok = [p for p in KANDIDAT.glob(args.kandidat + '.*')
             if p.suffix.lower() in EKSTENSI] if KANDIDAT.exists() else []
    if not cocok:
        sys.exit(f'Kandidat "{args.kandidat}" tidak ada di {KANDIDAT}/')
    sumber = cocok[0]

    ok, catatan = _periksa_gambar(sumber)
    if not ok:
        sys.exit(f'Ditolak: {catatan}')

    tujuan = REFS / f'{args.slug}{sumber.suffix}'
    lama = [REFS / f'{args.slug}{e}' for e in EKSTENSI]
    ada = [p for p in lama if p.exists()]
    if ada and not args.timpa:
        sys.exit(f'{ada[0].name} sudah ada. Tambahkan --timpa untuk mengganti.')
    for p in ada:
        p.unlink()
    shutil.copy2(sumber, tujuan)
    print(f'{sumber.name} -> {tujuan.name}   {catatan}')


def perintah_status(_args):
    frames = _slug_manifest()
    print()
    siap = 0
    for f in frames:
        slug = f['slug']
        ada = [REFS / f'{slug}{e}' for e in EKSTENSI]
        ada = [p for p in ada if p.exists()]
        if not ada:
            print(f'  {"KOSONG":7s} {slug:20s} {f["catatan"][:52]}')
            continue
        ok, catatan = _periksa_gambar(ada[0])
        print(f'  {"SIAP" if ok else "TOLAK":7s} {slug:20s} {catatan}')
        siap += ok
    print(f'\n{siap}/{len(frames)} siap.')
    if siap == len(frames):
        print('Gerbangnya mestinya terbuka. Pastikan:\n'
              '  python tools/bar_gate.py check\n')
    else:
        print('Gerbang masih tertutup sampai kedelapan terisi.\n')


def main():
    ap = argparse.ArgumentParser(
        description='Kumpulkan delapan frame patokan AWL (jalankan di mesin '
                    'sendiri — egress sesi web ditolak kebijakan jaringan).')
    sub = ap.add_subparsers(dest='perintah', required=True)

    p = sub.add_parser('cari', help='cari appid Steam berdasarkan nama')
    p.add_argument('istilah', nargs='?',
                   default='Story of Seasons A Wonderful Life')
    p.set_defaults(fn=perintah_cari)

    p = sub.add_parser('steam', help='unduh semua tangkapan layar satu appid')
    p.add_argument('--appid', type=int, required=True)
    p.set_defaults(fn=perintah_steam)

    p = sub.add_parser('video', help='ambil frame dari video gameplay')
    p.add_argument('sumber', help='URL video atau berkas lokal')
    p.add_argument('--detik', type=float, nargs='+', required=True)
    p.set_defaults(fn=perintah_video)

    p = sub.add_parser('daftar', help='lihat kandidat yang sudah ada')
    p.set_defaults(fn=perintah_daftar)

    p = sub.add_parser('pasang', help='pasang satu kandidat jadi slug patokan')
    p.add_argument('kandidat')
    p.add_argument('slug')
    p.add_argument('--timpa', action='store_true')
    p.set_defaults(fn=perintah_pasang)

    p = sub.add_parser('status', help='delapan slug — mana yang sudah siap')
    p.set_defaults(fn=perintah_status)

    args = ap.parse_args()
    args.fn(args)


if __name__ == '__main__':
    main()
