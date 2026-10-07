"""perjalanan.py — Warga berpindah scene dengan BERJALAN, bukan teleport.

Sebelum ini jadwal yang menunjuk scene lain langsung menyetel posisi warga di
scene tujuan: Sari lenyap dari warung pukul 18:00 dan pada detik yang sama
sudah berdiri di alun-alun. Di sini rute dicari di graf portal (portal yang
sama yang dipakai pemain), lalu warga berjalan ke pintu keluar, menyeberang,
dan muncul di pintu masuk scene berikutnya.

Dua cara bergerak, tergantung apakah pemain bisa melihatnya:
  - di scene pemain: aktornya berjalan sungguhan lewat pathfinding ke pintu;
  - di scene lain  : posisinya maju lurus dengan kecepatan jalan yang sama,
    jadi waktu tempuhnya masuk akal dan ia tiba pada saat yang benar.
"""
from __future__ import annotations

import math
from collections import deque
from functools import lru_cache

from .config import NPC_SPEED, TILE_SIZE

# NPC_SPEED dalam satuan dunia per detik; posisi jadwal dalam PETAK.
LAJU_PETAK = NPC_SPEED / TILE_SIZE

# Scene yang tidak ikut graf: dungeon dibangkitkan prosedural, 'hidden' adalah
# tempat warga "tidak ada" (mis. peronda tidur di rumahnya).
_LUAR_GRAF = ('dungeon', 'hidden')
JARAK_TIBA = 0.7          # petak; cukup dekat dengan pintu untuk menyeberang


def _portal(scene: str):
    from .scenes import SCENES
    sc = SCENES.get(scene)
    return list(getattr(sc, 'portals', None) or []) if sc else []


@lru_cache(maxsize=512)
def rute(dari: str, ke: str):
    """Daftar lompatan (px, py, scene_berikut, tiba_x, tiba_y) atau None.

    BFS: jumlah pintu paling sedikit. Scene dalam ruang hanya punya satu
    pintu, jadi rute dari warung ke danau otomatis lewat alun-alun.
    """
    if dari == ke:
        return ()
    if dari in _LUAR_GRAF or ke in _LUAR_GRAF:
        return None
    asal = {dari: None}
    q = deque([dari])
    while q:
        cur = q.popleft()
        if cur == ke:
            break
        for (px, py, nxt, ax, ay) in _portal(cur):
            if nxt in asal or nxt in _LUAR_GRAF:
                continue
            asal[nxt] = (cur, (px, py, nxt, ax, ay))
            q.append(nxt)
    if ke not in asal:
        return None
    hops = []
    cur = ke
    while asal[cur] is not None:
        prev, hop = asal[cur]
        hops.append(hop)
        cur = prev
    return tuple(reversed(hops))


def lompatan_berikut(pos: dict):
    """Lompatan pertama dari scene warga sekarang ke scene tujuannya."""
    tujuan = pos.get('tujuan')
    if not tujuan:
        return None
    r = rute(pos.get('scene', ''), tujuan[0])
    return r[0] if r else None


def maju_lurus(pos: dict, gx: float, gy: float, dt: float, laju: float = LAJU_PETAK) -> bool:
    """Gerakkan posisi abstrak menuju (gx, gy). True kalau sudah tiba."""
    dx, dy = gx - pos['x'], gy - pos['y']
    d = math.hypot(dx, dy)
    langkah = laju * dt
    if d <= max(langkah, 1e-6):
        pos['x'], pos['y'] = float(gx), float(gy)
        return True
    pos['x'] += dx / d * langkah
    pos['y'] += dy / d * langkah
    return d - langkah <= JARAK_TIBA
