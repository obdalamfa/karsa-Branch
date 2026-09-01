"""bar_gate.py — gerbang patokan: kritikus tidak boleh bisa mengarang bandingan.

Kenapa alat ini ada
===================

Gauntlet loop hanya menghasilkan mutu kalau benda yang dibandingkan itu NYATA.
Skill-nya sendiri menyebut satu kegagalan sebagai yang paling sering terjadi:

    "A vague bar. The critic invents a comparison and approves everything.
     Most common failure by far."

Dan di repo ini kegagalan itu bukan kemungkinan, tapi sudah pernah terjadi
setengahnya: patokan AWL yang sudah diambil hilang bersama container-nya, dan
tidak bisa diambil ulang karena egress sesi web cuma mengizinkan GitHub.
Diukur:

    https://store.steampowered.com -> 000  ditolak
    https://en.wikipedia.org       -> 000  ditolak
    https://api.github.com         -> 200

Kritikus yang dijalankan dalam keadaan itu tidak akan berkata "aku tidak punya
patokan". Ia akan menulis perbandingan yang terdengar masuk akal dari ingatan
tentang AWL, lalu meluluskan apa pun. Loopnya berhenti di ronde satu dan semua
orang mengira menang.

Alat ini menutup dua celah, dan sengaja dua-duanya:

  check   Menolak jalan kalau frame patokan yang diminta MANIFEST tidak ada.
          Bukan peringatan — keluar dengan kode 1, supaya loopnya berhenti,
          bukan melanjutkan tanpa patokan. Juga menolak jalan kalau patokan
          justru MASUK git: repo ini publik, dan meng-commit tangkapan layar
          orang lain adalah redistribusi. Termasuk lewat pintu belakang —
          progress.html meng-embed lembar perbandingan sebagai data URI.

  pair    Menyusun lembar A/B dengan label DICOPOT dan urutan diacak, lalu
          menulis kuncinya ke berkas TERPISAH. Kritikus melihat lembarnya;
          kritikus tidak melihat kuncinya. Tanpa ini "buta" cuma janji: agen
          yang tahu gambar kiri buatan sendiri akan memilih gambar kiri.

Pemakaian
=========

    python tools/bar_gate.py check
    python tools/bar_gate.py pair --ours shot.png --ref farm_wide \\
        --out _bench/sheet.png --key _bench/key.json
    python tools/bar_gate.py reveal --key _bench/key.json --pilih A

`reveal` dijalankan SETELAH kritikus menjawab, oleh pemanggilnya, bukan oleh
kritikusnya.
"""
from __future__ import annotations

import argparse
import json
import hashlib
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REFS = ROOT / '_bench' / 'refs'
MANIFEST = REFS / 'MANIFEST.json'

# Ukuran minimum supaya berkas kosong atau placeholder 1x1 tidak lolos sebagai
# "patokan ada". Tanpa ambang ini, `touch farm_wide.png` cukup untuk membuka
# gerbangnya — dan itu persis lubang yang alat ini dibuat untuk menutup.
MIN_BYTES = 20_000
MIN_SISI = 480


def _ter_track_git(paths) -> list:
    """Berkas mana dari `paths` yang dilacak git."""
    import subprocess
    ada = [str(x) for x in paths if x.exists()]
    if not ada:
        return []
    try:
        out = subprocess.run(['git', 'ls-files', '--error-unmatch', '--'] + ada,
                             cwd=str(ROOT), capture_output=True, text=True)
    except Exception:
        return []
    return [b.strip() for b in out.stdout.splitlines() if b.strip()]


def _periksa_kebocoran() -> list:
    """Patokan dan lembar perbandingan TIDAK BOLEH masuk git.

    Repo ini publik. Tangkapan layar Story of Seasons boleh disimpan lokal
    untuk pembandingan internal — itu yang ditulis MANIFEST-nya sendiri — tapi
    meng-commit-nya ke repo publik adalah redistribusi karya orang lain.

    Dijaga di sini, bukan dengan komentar di .gitignore, karena komentar yang
    meminta orang mengingat bukan jaring pengaman. Dan ada satu pintu belakang
    yang tidak terlihat dari nama berkasnya: progress_page.py meng-embed
    _bench/sheets/*.png sebagai data URI, jadi meng-commit progress.html
    menyelundupkan frame patokan ke dalam repo tanpa satu pun berkas gambar
    ikut ter-stage.
    """
    from itertools import chain
    kandidat = list(chain(
        (p for p in REFS.glob('*') if p.suffix.lower() in
         ('.png', '.jpg', '.jpeg', '.webp')),
        (ROOT / '_bench' / 'sheets').glob('*') if (ROOT / '_bench' / 'sheets').exists() else [],
        [ROOT / '_bench' / 'progress.html'],
    ))
    return _ter_track_git(kandidat)


def _muat_manifest():
    if not MANIFEST.exists():
        return None, (f'MANIFEST tidak ada di {MANIFEST.relative_to(ROOT)}. '
                      f'Tanpa daftar patokan, tidak ada yang bisa diperiksa.')
    try:
        data = json.loads(MANIFEST.read_text(encoding='utf-8'))
    except Exception as e:
        return None, f'MANIFEST tidak bisa dibaca: {e}'
    frames = data.get('frames')
    if not isinstance(frames, list) or not frames:
        return None, 'MANIFEST tidak memuat daftar `frames` yang berisi.'
    return data, None


def _periksa_satu(item):
    """Kembalikan (ok, catatan) untuk satu entri patokan."""
    slug = item.get('slug')
    if not slug:
        return False, 'entri tanpa `slug`'
    kandidat = [REFS / f'{slug}{ext}' for ext in ('.png', '.jpg', '.jpeg', '.webp')]
    ada = [p for p in kandidat if p.exists()]
    if not ada:
        return False, f'{slug}: berkas tidak ada'
    p = ada[0]
    n = p.stat().st_size
    if n < MIN_BYTES:
        return False, f'{slug}: cuma {n} B — placeholder, bukan patokan'
    try:
        from PIL import Image
        with Image.open(p) as im:
            w, h = im.size
    except Exception as e:
        return False, f'{slug}: bukan gambar yang bisa dibuka ({e})'
    if min(w, h) < MIN_SISI:
        return False, f'{slug}: {w}x{h} terlalu kecil untuk dibandingkan'
    return True, f'{slug}: {w}x{h}, {n // 1024} KiB'


def perintah_check(_args):
    data, galat = _muat_manifest()
    if galat:
        print('GERBANG TERTUTUP\n')
        print(f'  {galat}\n')
        print('  Kritikus TIDAK boleh dijalankan tanpa patokan. Tanpa frame')
        print('  asli ia akan mengarang perbandingan dari ingatan lalu')
        print('  meluluskan semuanya — kegagalan nomor satu gauntlet loop.')
        return 1

    # Patokan ter-track TIDAK otomatis salah. Yang salah adalah patokan ter-track
    # di repo PUBLIK. Sejak repo ini dipindahkan ke privat, pemilik memilih agar
    # patokannya ikut ter-commit supaya tidak hilang lagi — dan keputusan itu
    # dicatat di MANIFEST, bukan diingat. Kalau repo dikembalikan jadi publik,
    # `repo_privat` harus disetel false dan gerbang ini akan menutup lagi.
    bocor = [] if data.get('repo_privat') else _periksa_kebocoran()
    if bocor:
        print('GERBANG TERTUTUP — patokan bocor ke git\n')
        for b in bocor[:8]:
            print(f'  ter-track: {b}')
        print()
        print('  Repo ini publik. Frame patokan dan lembar perbandingan boleh')
        print('  ada di disk, tapi tidak boleh ter-commit — itu redistribusi')
        print('  karya orang lain. Keluarkan dulu:')
        print()
        print('      git rm --cached <berkas>')
        print()
        print('  progress.html termasuk: ia meng-embed lembar perbandingan')
        print('  sebagai data URI, jadi ia membawa frame patokan ikut serta.')
        return 1

    if data.get('repo_privat'):
        print('repo    : PRIVAT — patokan boleh ter-commit.')
        print('          Kalau repo ini dikembalikan jadi publik: setel')
        print('          repo_privat=false di MANIFEST DAN keluarkan patokannya')
        print('          dari git (`git rm --cached`). Gerbang ini akan menutup lagi.')
    print(f"patokan : {data.get('bar', '(tidak disebut)')}")
    print(f"sumber  : {data.get('source', '(tidak disebut)')}\n")
    import textwrap
    hasil = [(_periksa_satu(it), it) for it in data['frames']]
    kurang = 0
    for (ok, catatan), it in hasil:
        if ok:
            print(f'  ADA    {catatan}')
            continue
        kurang += 1
        print(f'  HILANG {catatan}')
        if it.get('catatan'):
            for baris in textwrap.wrap(it['catatan'], 64):
                print(f'         {baris}')

    print()
    if kurang:
        print(f'GERBANG TERTUTUP — {kurang}/{len(hasil)} patokan tidak ada.\n')
        print('  Taruh frame yang kurang di _bench/refs/ lalu jalankan ini')
        print('  lagi. JANGAN di-commit: repo ini publik, dan berkasnya karya')
        print('  orang lain. Karena itu ia hilang tiap container ditarik, dan')
        print('  karena itu loop ini hanya bisa jalan di mesin yang punya')
        print('  berkasnya — bukan di sesi web.')
        return 1
    print(f'GERBANG TERBUKA — {len(hasil)}/{len(hasil)} patokan ada.')
    return 0


def perintah_pair(args):
    """Susun lembar A/B buta: label dicopot, urutan diacak, kunci dipisah."""
    try:
        from PIL import Image
    except Exception as e:
        print(f'butuh Pillow: {e}')
        return 1

    ours = Path(args.ours)
    if not ours.exists():
        print(f'tangkapan layar kita tidak ada: {ours}')
        return 1
    kandidat = [REFS / f'{args.ref}{ext}' for ext in ('.png', '.jpg', '.jpeg', '.webp')]
    ada = [p for p in kandidat if p.exists()]
    if not ada:
        print(f'patokan `{args.ref}` tidak ada di {REFS.relative_to(ROOT)}.')
        print('Jalankan `python tools/bar_gate.py check` dulu.')
        return 1
    ref = ada[0]

    a_img = Image.open(ours).convert('RGB')
    b_img = Image.open(ref).convert('RGB')

    # Samakan tinggi supaya beda ukuran tidak jadi petunjuk mana yang mana.
    h = min(a_img.height, b_img.height, 720)
    if args.tegak:
        # Strip: tingginya satu ubin, bukan satu layar. Menjepitnya ke 720
        # tidak masuk akal dan malah membuang resolusi.
        h = min(a_img.height, b_img.height)
    def _skala(im):
        w = max(1, round(im.width * h / im.height))
        return im.resize((w, h), Image.LANCZOS)
    a_img, b_img = _skala(a_img), _skala(b_img)

    # Urutan diacak. Ini bagian yang membuat "buta" berarti sesuatu: kritikus
    # yang tahu gambar kiri buatan sendiri akan memilih gambar kiri.
    rnd = random.Random(args.seed) if args.seed is not None else random.Random()
    kiri_kita = rnd.random() < 0.5
    kiri, kanan = (a_img, b_img) if kiri_kita else (b_img, a_img)

    JEDA = 24
    if args.tegak:
        # Strip gerak berdampingan jadi 15.000 px lebar; diperkecil agar muat,
        # tiap frame-nya tinggal beberapa puluh piksel dan gerakan yang justru
        # sedang dinilai hilang. Ditumpuk tegak, tiap strip tetap satu baris
        # penuh. Lebar disamakan juga supaya beda ukuran tidak jadi petunjuk.
        w = min(kiri.width, kanan.width)
        def _lebar(im):
            hh = max(1, round(im.height * w / im.width))
            return im.resize((w, hh), Image.LANCZOS)
        kiri, kanan = _lebar(kiri), _lebar(kanan)
        lembar = Image.new('RGB', (w, kiri.height + JEDA + kanan.height), (18, 18, 20))
        lembar.paste(kiri, (0, 0))
        lembar.paste(kanan, (0, kiri.height + JEDA))
    else:
        lembar = Image.new('RGB', (kiri.width + JEDA + kanan.width, h), (18, 18, 20))
        lembar.paste(kiri, (0, 0))
        lembar.paste(kanan, (kiri.width + JEDA, 0))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    lembar.save(out)

    kunci = {
        'lembar': str(out),
        'susun': 'tegak' if args.tegak else 'datar',
        'ref_slug': args.ref,
        'A': 'kita' if kiri_kita else 'patokan',
        'B': 'patokan' if kiri_kita else 'kita',
        'sidik_kita': hashlib.sha256(ours.read_bytes()).hexdigest()[:16],
        'sidik_patokan': hashlib.sha256(ref.read_bytes()).hexdigest()[:16],
    }
    kp = Path(args.key)
    kp.parent.mkdir(parents=True, exist_ok=True)
    kp.write_text(json.dumps(kunci, ensure_ascii=False, indent=2), encoding='utf-8')

    posisi = 'A = atas, B = bawah' if args.tegak else 'A = kiri, B = kanan'
    print(f'lembar : {out}   ({posisi})')
    print(f'kunci  : {kp}')
    print('Berikan HANYA lembarnya ke kritikus. Kuncinya jangan.')
    return 0


def perintah_reveal(args):
    kp = Path(args.key)
    if not kp.exists():
        print(f'kunci tidak ada: {kp}')
        return 1
    kunci = json.loads(kp.read_text(encoding='utf-8'))
    pilih = args.pilih.strip().upper()
    if pilih not in ('A', 'B'):
        print('--pilih harus A atau B')
        return 1
    siapa = kunci.get(pilih)
    print(f'kritikus memilih {pilih} = {siapa}')
    if siapa == 'kita':
        print('MENANG — potongan ini boleh keluar dari loop.')
        return 0
    print('BELUM MENANG — kembalikan ke pembangun dengan celah yang disebut kritikus.')
    return 2


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='perintah', required=True)

    sub.add_parser('check', help='tolak jalan kalau patokan tidak ada')

    p = sub.add_parser('pair', help='susun lembar A/B buta')
    p.add_argument('--ours', required=True, help='tangkapan layar dari tools/capture.py')
    p.add_argument('--ref', required=True, help='slug patokan di _bench/refs/')
    p.add_argument('--out', default='_bench/sheet.png')
    p.add_argument('--key', default='_bench/key.json')
    p.add_argument('--tegak', action='store_true',
                   help='tumpuk A di atas B, bukan berdampingan — untuk strip gerak')
    p.add_argument('--seed', type=int, default=None,
                   help='hanya untuk uji — biarkan kosong saat dipakai sungguhan')

    r = sub.add_parser('reveal', help='buka kunci SETELAH kritikus menjawab')
    r.add_argument('--key', default='_bench/key.json')
    r.add_argument('--pilih', required=True, help='A atau B')

    args = ap.parse_args()
    return {'check': perintah_check,
            'pair': perintah_pair,
            'reveal': perintah_reveal}[args.perintah](args)


if __name__ == '__main__':
    sys.exit(main())
