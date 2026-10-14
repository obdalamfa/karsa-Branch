"""gauntlet_capture.py — potret game asli per slug patokan, lalu pasangkan buta.

Satu perintah untuk satu ronde gauntlet visual. Tiap slug di
`_bench/refs/MANIFEST.json` (farm_wide, village_wide, evening_light, ...)
dipetakan ke satu pengambilan dari GAME ASLI lewat `tools/capture.py`. Alat
itu mem-boot `Game3D` dan melangkah lewat `app.py`, jadi yang dipotret
adalah dunia yang dimainkan, bukan panggung buatan (aturan #2 CLAUDE.md).
Hasilnya lalu dipasangkan dengan patokannya lewat `bar_gate.py pair`: label
dicopot, urutan diacak, dan kuncinya ditulis ke berkas terpisah yang tidak
boleh dilihat kritikus.

    python tools/gauntlet_capture.py                 # semua slug, ronde 1
    python tools/gauntlet_capture.py farm_wide --ronde 3
    python tools/gauntlet_capture.py --daftar        # slug -> pengambilan

Keluaran di `_bench/gauntlet/r<ronde>/`:
    <slug>_kita.png     tangkapan game (untuk builder; JANGAN ke kritikus)
    <slug>_ab.png       lembar A/B buta (ini yang diserahkan ke kritikus)
    <slug>_kunci.json   kunci A/B (dibuka `bar_gate.py reveal` SESUDAH vonis)

Pengambilan sengaja disimpan sebagai data di bawah, bukan argumen baris
perintah: tiap ronde harus memotret sudut yang SAMA. Kalau sudutnya digeser
diam-diam, "menang" di ronde lima bisa berarti cuma kameranya yang dipindah.
Mengubah sudut boleh, asal lewat diff yang terlihat.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REFS = ROOT / '_bench' / 'refs'
KELUAR = ROOT / '_bench' / 'gauntlet'

# slug patokan -> argumen tools/capture.py. Jam dipilih supaya cocok dengan
# cahaya di frame patokannya (siang untuk lapangan, senja untuk evening_light).
PENGAMBILAN: dict[str, list[str]] = {
    # Ladang yang sedang digarap, seperti di patokan -- bukan hari pertama.
    'farm_wide':         ['--scene', 'farm', '--hour', '10',
                          '--save', 'tools/fixtures/ladang_hari10_save.json'],
    'farm_closeup':      ['--scene', 'farm', '--hour', '10', '--dist', '5', '--pitch', '28'],
    'hud_default':       ['--scene', 'farm', '--hour', '11'],
    'character_midshot': ['--scene', 'town', '--hour', '10'],
    'character_closeup': ['--scene', 'town', '--hour', '10', '--dist', '4', '--pitch', '12'],
    'village_wide':      ['--scene', 'town', '--hour', '10', '--dist', '22', '--pitch', '35'],
    'barn_interior':     ['--scene', 'house', '--hour', '10'],
    'evening_light':     ['--scene', 'farm', '--hour', '17.6'],
    'gua_interior':      ['--scene', 'naga_cave', '--hour', '12'],
}


def _manifest_slugs() -> list[str]:
    data = json.loads((REFS / 'MANIFEST.json').read_text(encoding='utf-8'))
    return [f['slug'] for f in data['frames']]


def ambil(slug: str, out: Path) -> bool:
    cmd = [sys.executable, str(ROOT / 'tools' / 'capture.py'),
           '--out', str(out), '--frames', '120', *PENGAMBILAN[slug]]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0 or not out.exists():
        print(f'  GAGAL ambil {slug}: {r.stderr.strip().splitlines()[-1:]}')
        return False
    # capture.py tetap menulis PNG walau scene tak pernah berganti -- ia cuma
    # memperingatkan di stderr. Diam-diam meneruskannya berarti kritikus
    # menilai layar yang salah.
    if 'CAPTURE_WARN' in r.stderr:
        print(f'  GAGAL ambil {slug}: ' + r.stderr.split('CAPTURE_WARN', 1)[1].splitlines()[0])
        return False
    return True


def pasangkan(slug: str, kita: Path, ab: Path, kunci: Path) -> bool:
    cmd = [sys.executable, str(ROOT / 'tools' / 'bar_gate.py'), 'pair',
           '--ours', str(kita), '--ref', slug, '--out', str(ab), '--key', str(kunci)]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        print(f'  GAGAL pasang {slug}: {(r.stdout + r.stderr).strip()[-200:]}')
        return False
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('slug', nargs='*', help='slug patokan; kosong = semua')
    ap.add_argument('--ronde', type=int, default=1)
    ap.add_argument('--daftar', action='store_true')
    args = ap.parse_args()

    slugs_manifest = _manifest_slugs()
    tanpa_ambil = [s for s in slugs_manifest if s not in PENGAMBILAN]
    if tanpa_ambil:
        # Slug patokan tanpa pengambilan berarti bagian bar yang tak pernah
        # diadu. Lebih baik berhenti daripada diam-diam melewatinya.
        print(f'slug di MANIFEST tanpa pengambilan: {tanpa_ambil}')
        return 2

    if args.daftar:
        for s in slugs_manifest:
            print(f'{s:18s} {" ".join(PENGAMBILAN[s])}')
        return 0

    # Tanpa patokan tidak ada perbandingan buta -- bar_gate yang memutuskan.
    if subprocess.run([sys.executable, str(ROOT / 'tools' / 'bar_gate.py'), 'check'],
                      cwd=ROOT, capture_output=True).returncode != 0:
        print('bar_gate check menolak: patokan tidak lengkap. Berhenti.')
        return 3

    pilih = args.slug or slugs_manifest
    salah = [s for s in pilih if s not in PENGAMBILAN]
    if salah:
        print(f'slug tidak dikenal: {salah}')
        return 2

    d = KELUAR / f'r{args.ronde}'
    d.mkdir(parents=True, exist_ok=True)
    gagal = 0
    for s in pilih:
        kita, ab, kunci = d / f'{s}_kita.png', d / f'{s}_ab.png', d / f'{s}_kunci.json'
        print(f'{s} ...')
        if not (ambil(s, kita) and pasangkan(s, kita, ab, kunci)):
            gagal += 1
            continue
        print(f'  -> {ab.relative_to(ROOT)}')
    print(f'{len(pilih) - gagal}/{len(pilih)} slug siap diadu di {d.relative_to(ROOT)}')
    return 1 if gagal else 0


if __name__ == '__main__':
    sys.exit(main())
