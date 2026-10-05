"""interior_check.py — Buktikan setiap bangunan bisa dimasuki, dijelajahi, dan ditinggalkan.

Tanpa jendela game: murni dari data scene, jadi cepat dan bisa dipakai di
skrip. Memeriksa, untuk setiap scene ber-builder 'interior':

  masuk      setiap portal di scene LUAR yang menuju ruangan ini mendaratkan
             pemain di ubin yang bisa dijalani (bukan di luar peta, bukan di
             dalam perabot) -- dulu semuanya mendarat di (7,9) pada ruangan
             setinggi 6 ubin.
  keluar     dari titik mendarat, pintu keluar bisa dicapai.
  lantai     SEMUA ubin lantai terjangkau dari titik mendarat -- tidak ada
             pojok yang terkurung perabot (konter warung dulu menutup satu
             baris penuh).
  perabot    setiap perabot punya setidaknya satu tetangga (4 arah) yang
             terjangkau, karena pemain memakai perabot sambil MENGHADAPnya.
  jadwal     posisi NPC di jadwal yang jatuh di ruangan ini bisa dijalani.
  balik      portal keluar mendaratkan pemain di ubin luar yang bisa dijalani
             dan tidak langsung memicu portal masuk lagi.

Pemakaian:  python tools/interior_check.py      (kode keluar 1 kalau gagal)
"""
from __future__ import annotations

import sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from game.config import WALKABLE, WL, DR, FL, D  # noqa: E402
from game.objects import is_interactive  # noqa: E402
from game.scenes import SCENES  # noqa: E402
from game.data import SCHEDULES  # noqa: E402


def jalan(sc, x, y):
    return 0 <= x < sc.w and 0 <= y < sc.h and sc.tiles[y][x] in WALKABLE


def jangkau(sc, x, y):
    seen = {(x, y)}
    q = deque([(x, y)])
    while q:
        cx, cy = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (cx + dx, cy + dy)
            if n not in seen and jalan(sc, *n):
                seen.add(n)
                q.append(n)
    return seen


_EMPAT = ((1, 0), (-1, 0), (0, 1), (0, -1))


def didekati(sc, r, x, y):
    """Perabot bisa dipakai kalau ada ubin terjangkau tepat di sebelahnya.

    Pengecualian: konter/rak/rak buku yang BERDERET adalah satu benda -- sudut
    konter siku di dapur cukup dicapai lewat anggota deretannya yang lain.
    """
    from game.config import CT, SH, BS
    t = sc.tiles[y][x]
    seen, q = {(x, y)}, [(x, y)]
    while q:
        cx, cy = q.pop()
        if any((cx + dx, cy + dy) in r for dx, dy in _EMPAT):
            return True
        if t not in (CT, SH, BS):
            return False
        for dx, dy in _EMPAT:
            n = (cx + dx, cy + dy)
            if n not in seen and 0 <= n[0] < sc.w and 0 <= n[1] < sc.h and sc.tiles[n[1]][n[0]] == t:
                seen.add(n)
                q.append(n)
    return False


def main():
    gagal = 0
    # Semua bangunan yang bisa dimasuki; gua & dungeon bukan bangunan.
    ruang = [n for n, s in SCENES.items() if s.indoor and n not in ('naga_cave', 'dungeon')]
    for nama in ruang:
        sc = SCENES[nama]
        masalah = []
        masuk = [(s, p) for s, o in SCENES.items() for p in o.portals if p[2] == nama]
        if not masuk:
            masalah.append('tidak ada portal masuk')
        titik = set()
        for s, (px, py, _, tx, ty) in masuk:
            if not jalan(sc, tx, ty):
                masalah.append(f'masuk dari {s}({px},{py}) mendarat di ({tx},{ty}) yang tak bisa dijalani')
            titik.add((tx, ty))
        for tx, ty in titik:
            r = jangkau(sc, tx, ty)
            for (px, py, tujuan, ox, oy) in sc.portals:
                if (px, py) not in r:
                    masalah.append(f'pintu keluar ({px},{py}) tak terjangkau dari ({tx},{ty})')
                luar = SCENES[tujuan]
                if not jalan(luar, ox, oy):
                    masalah.append(f'keluar ke {tujuan}({ox},{oy}) tak bisa dijalani')
                if any((q[0], q[1]) == (ox, oy) for q in luar.portals):
                    masalah.append(f'keluar ke {tujuan}({ox},{oy}) tepat di atas portal lain')
            for y in range(sc.h):
                for x in range(sc.w):
                    t = sc.tiles[y][x]
                    if t in (FL, D) and (x, y) not in r:
                        masalah.append(f'lantai ({x},{y}) terkurung')
                    if is_interactive(t) and t not in (FL, D) and not didekati(sc, r, x, y):
                        masalah.append(f'perabot ({x},{y}) tak bisa didekati')
            for npc, jadwal in SCHEDULES.items():
                for (_, x, y, s, _) in jadwal:
                    if s == nama and (x, y) not in r:
                        masalah.append(f'jadwal {npc} di ({x},{y}) tak terjangkau')
        status = 'LULUS' if not masalah else 'GAGAL'
        print(f'{nama:11s} {sc.w}x{sc.h}  {status}')
        for m in masalah:
            print('   -', m)
        gagal += bool(masalah)
    print(f'\n{len(ruang) - gagal}/{len(ruang)} ruangan lulus')
    sys.exit(1 if gagal else 0)


if __name__ == '__main__':
    main()
