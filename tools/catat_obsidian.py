"""catat_obsidian.py — Tulis kerangka catatan sesi ke vault Obsidian dari git.

Kenapa alat ini ada
───────────────────
Vault `obsidian/` hanya berguna kalau isinya mengikuti kerja yang benar-benar
terjadi. Mencatat manual selalu kalah dari mengerjakan: yang tercatat jadi
sesi-sesi awal saja, lalu berhenti. Skrip ini membuat mencatat lebih murah
daripada tidak mencatat — kerangkanya dibangun dari git, manusia tinggal
mengisi bukti.

Yang DIAMBIL dari git (fakta): hash, tanggal, judul, badan pesan commit,
daftar file yang berubah, dan jumlah baris.

Yang DIBIARKAN KOSONG (bukan fakta): bagian `## Bukti` dan
`## Yang belum beres`. Skrip tidak tahu apakah regresi lulus, dan menebaknya
akan persis mengulang kesalahan yang melahirkan `tools/regress.py` — klaim
selesai tanpa pengukuran. Lihat `obsidian/00-Peta/Aturan Pencatatan.md`.

Pemakaian
─────────
    python tools/catat_obsidian.py --status      commit mana yang belum tercatat
    python tools/catat_obsidian.py               buat nota untuk HEAD
    python tools/catat_obsidian.py --commit d8da814
    python tools/catat_obsidian.py --semua       semua commit yang belum tercatat

Nota yang sudah ada tidak pernah ditimpa.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SESI = ROOT / 'obsidian' / '20-Sesi'

# Karakter yang tidak boleh masuk nama file di Windows/macOS/Linux.
TERLARANG = r'[\\/:*?"<>|]'


def git(*args: str) -> str:
    # core.quotepath=false: tanpa ini git menulis nama berkas non-ASCII sebagai
    # oktal di dalam tanda kutip ("obsidian/... \342\200\224 ..."), dan nama
    # nota di vault ini memang memakai em dash. Akibatnya path tidak lagi
    # diawali "obsidian/" dan setiap pemeriksaan berbasis awalan meleset.
    hasil = subprocess.run(('git', '-c', 'core.quotepath=false', *args),
                           cwd=ROOT, capture_output=True,
                           text=True, encoding='utf-8', errors='replace')
    if hasil.returncode != 0:
        sys.exit(f'git {" ".join(args)} gagal:\n{hasil.stderr.strip()}')
    return hasil.stdout


def hanya_vault(sha: str) -> bool:
    """True kalau commit ini cuma menyentuh isi vault.

    Commit semacam itu adalah pembukuan tentang kerja, bukan kerjanya sendiri,
    jadi ia tidak menuntut notanya sendiri — kalau tidak, tiap nota melahirkan
    commit yang menuntut nota baru, tanpa akhir.
    """
    berkas = [path for _, _, path in berkas_berubah(sha)]
    return bool(berkas) and all(p.startswith('obsidian/') for p in berkas)


def daftar_commit() -> list[tuple[str, str, str]]:
    """(hash pendek, tanggal YYYY-MM-DD, judul) — terlama dulu."""
    keluaran = git('log', '--reverse', '--pretty=format:%h\x1f%ad\x1f%s',
                   '--date=format:%Y-%m-%d')
    out = []
    for baris in keluaran.splitlines():
        if baris.strip():
            h, tgl, judul = baris.split('\x1f', 2)
            out.append((h, tgl, judul))
    return out


def sudah_tercatat() -> dict[str, Path]:
    """Peta hash commit → berkas nota, dibaca dari frontmatter `commit:`."""
    peta: dict[str, Path] = {}
    if not SESI.is_dir():
        return peta
    for nota in SESI.glob('*.md'):
        isi = nota.read_text(encoding='utf-8', errors='replace')[:800]
        cocok = re.search(r'^commit:\s*(\S+)', isi, re.MULTILINE)
        if cocok:
            peta[cocok.group(1).strip()] = nota
    return peta


def nama_berkas(tanggal: str, judul: str) -> str:
    bersih = re.sub(TERLARANG, '-', judul).strip()
    if len(bersih) > 70:
        bersih = bersih[:70].rstrip() + '…'
    return f'{tanggal} — {bersih}.md'


def berkas_berubah(sha: str) -> list[tuple[str, str, str]]:
    """(tambah, hapus, path) untuk file sumber; .pyc dibuang karena berisik."""
    out = []
    for baris in git('show', '--numstat', '--format=', sha).splitlines():
        bagian = baris.split('\t')
        if len(bagian) != 3:
            continue
        tambah, hapus, path = bagian
        # Sisa pengutipan tetap dilucuti: git masih mengutip nama yang memuat
        # tanda kutip atau karakter kendali, apa pun nilai core.quotepath.
        if len(path) > 1 and path.startswith('"') and path.endswith('"'):
            path = path[1:-1]
        if path.endswith('.pyc') or '__pycache__' in path:
            continue
        out.append((tambah, hapus, path))
    return out


def bangun_nota(sha: str, tanggal: str, judul: str) -> str:
    badan = git('show', '-s', '--format=%b', sha).strip()
    # Baris atribusi commit bukan isi catatan.
    badan = '\n'.join(b for b in badan.splitlines()
                      if not b.startswith(('Co-Authored-By:', 'Claude-Session:')))
    badan = badan.strip()

    berkas = berkas_berubah(sha)
    tambah = sum(int(a) for a, _, _ in berkas if a.isdigit())
    hapus = sum(int(h) for _, h, _ in berkas if h.isdigit())

    baris_tabel = '\n'.join(
        f'| `{path}` | +{a} | −{h} |' for a, h, path in berkas[:30]) or \
        '| *(tidak ada file sumber yang berubah)* | | |'
    lebih = (f'\n\n*…dan {len(berkas) - 30} file lain.*'
             if len(berkas) > 30 else '')

    judul_aman = judul.replace('"', "'")
    return f"""---
judul: "{judul_aman}"
tipe: sesi
tanggal: {tanggal}
commit: {sha}
skala: {len(berkas)} file sumber, +{tambah} / −{hapus} baris
tags: [sesi]
---

# {tanggal} — {judul}

## Pesan commit

{badan if badan else '*(commit tanpa badan pesan)*'}

## Berkas yang berubah

| Berkas | + | − |
|---|---:|---:|
{baris_tabel}{lebih}

## Bukti

<!-- ISI MANUAL. Angka, larian regresi, atau probe — skrip sengaja tidak
     menebak bagian ini. Lihat [[Aturan Pencatatan]]. -->

- Regresi: `python tools/regress.py` → ?/? scene lulus

## Yang belum beres

<!-- ISI MANUAL. Ditulis apa adanya, termasuk yang alat ukurnya belum bisa
     dipercaya. -->

## Tautan

[[Status Sekarang]] · [[Peta Progres]]
"""


def tulis(sha: str, tanggal: str, judul: str, tercatat: dict[str, Path]) -> bool:
    if sha in tercatat:
        print(f'  lewati {sha}  sudah ada → {tercatat[sha].name}')
        return False
    SESI.mkdir(parents=True, exist_ok=True)
    tujuan = SESI / nama_berkas(tanggal, judul)
    if tujuan.exists():
        print(f'  lewati {sha}  berkas senama sudah ada → {tujuan.name}')
        return False
    tujuan.write_text(bangun_nota(sha, tanggal, judul), encoding='utf-8')
    print(f'  tulis  {sha}  → {tujuan.relative_to(ROOT)}')
    return True


def main() -> int:
    p = argparse.ArgumentParser(
        description='Tulis kerangka catatan sesi ke vault Obsidian dari git.')
    p.add_argument('--commit', help='hash commit tertentu (default: HEAD)')
    p.add_argument('--semua', action='store_true',
                   help='tulis nota untuk semua commit yang belum tercatat')
    p.add_argument('--status', action='store_true',
                   help='hanya laporkan commit mana yang belum punya nota')
    arg = p.parse_args()

    commits = daftar_commit()
    tercatat = sudah_tercatat()

    if arg.status:
        cocok = sum(1 for s, _, _ in commits if s in tercatat)
        print(f'{len(commits)} commit, {cocok} punya nota\n')
        print(f'{"commit":9s} {"tanggal":11s} {"nota":6s} judul')
        print('-' * 72)
        for sha, tgl, judul in commits:
            if sha in tercatat:
                tanda = 'ada'
            elif hanya_vault(sha):
                tanda = 'vault'
            else:
                tanda = '—'
            print(f'{sha:9s} {tgl:11s} {tanda:6s} {judul[:42]}')
        belum = [s for s, _, _ in commits
                 if s not in tercatat and not hanya_vault(s)]
        print('-' * 72)
        print(f'{len(belum)} commit belum tercatat'
              + (f': {", ".join(belum)}' if belum else ''))
        return 0

    if arg.semua:
        n = sum(tulis(s, t, j, tercatat) for s, t, j in commits
                if not hanya_vault(s))
        print(f'\n{n} nota baru ditulis.')
        return 0

    sha_minta = git('rev-parse', '--short', arg.commit or 'HEAD').strip()
    for sha, tgl, judul in commits:
        if sha.startswith(sha_minta) or sha_minta.startswith(sha):
            tulis(sha, tgl, judul, tercatat)
            return 0
    sys.exit(f'commit {sha_minta} tidak ada di riwayat branch ini')


if __name__ == '__main__':
    raise SystemExit(main())
