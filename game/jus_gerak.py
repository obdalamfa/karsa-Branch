"""jus_gerak.py — lapisan gerak di atas klip kerja pemain: ancang-ancang,
hentakan, dan ikut-gerak.

Kenapa ini ada. Rig pemain (assets/models/actors/player.glb) punya tiga klip
kerja -- hoe, swing, water -- dan semuanya diputar dengan potongan keras:
bobot jalan/diam dibanting ke nol, klip kerja ke satu, lalu dibanting balik
saat klip habis. Tidak ada momen "angkat", tidak ada momen "kena", dan
tubuhnya tidak pernah ikut bergerak bersama alatnya. Itu yang terbaca kaku.
Aksi tanpa klip (bend untuk panen/petik, gosok, bicara) lebih parah: tokohnya
berdiri diam sementara permainan bilang ia sedang memanen.

Prinsip animasi yang dipakai, semuanya murah dan prosedural:

  ancang-ancang  sebelum hentakan tubuh condong ke BELAKANG dan sedikit
                 memanjang -- mata membaca energi yang dikumpulkan
  hentakan       condong ke depan, gepeng sesaat (squash), dan kamera
                 "terdorong" sedikit di frame yang sama
  ikut-gerak     kembali ke tegak dengan sedikit lewat (overshoot), bukan
                 berhenti mendadak

Semua dipasang pada SATU NodePath poros di antara entity pemain dan Actor
rig (CharActor.poros), jadi tidak ada tulang yang disentuh dan klip aslinya
tetap utuh. Kurva dihitung dari kemajuan aksi p in [0,1], bukan dari waktu
dinding, sehingga hasilnya sama di 60 fps dan 8 fps.
"""
from __future__ import annotations

import math

# Kemajuan saat alat "kena" per mode. Hoe 0,93 dtk dan swing 0,70 dtk: puncak
# ayunan klipnya jatuh sedikit sebelum tengah.
_HENTAK = {'hoe': 0.42, 'down': 0.42, 'mine': 0.45, 'swing': 0.40,
           'water': 0.30, 'bend': 0.45, 'gosok': 0.5, 'bicara': 0.5,
           'kena': 0.0}


def _mulus(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


def _lentur(x):
    """0 -> 1 dengan sedikit lewat (back-out): ikut-gerak, bukan rem mendadak."""
    x = max(0.0, min(1.0, x))
    s = 1.70158
    x -= 1.0
    return x * x * ((s + 1) * x + s) + 1.0


def kurva(mode: str, p: float):
    """(pitch, roll, yaw, dy, gepeng) untuk mode pada kemajuan p.

    pitch positif = condong ke depan; gepeng < 1 = memendek (squash), dengan
    lebar dikompensasi supaya volume terasa tetap.
    """
    h = _HENTAK.get(mode, 0.45)
    if mode in ('hoe', 'down', 'mine'):
        kuat = 1.35 if mode == 'mine' else 1.0
        if p < h:                                   # angkat: condong ke belakang
            k = _mulus(p / h)
            return (-9 * k * kuat, 0.0, 0.0, 0.05 * k, 1.0 + 0.05 * k)
        k = (p - h) / (1 - h)
        if k < 0.18:                                # hentakan
            q = k / 0.18
            return (-9 * kuat + 25 * kuat * _mulus(q), 0.0, 0.0,
                    0.05 - 0.13 * q, 1.05 - 0.15 * q)
        q = (k - 0.18) / 0.82                       # pulih dengan lewat
        b = 1.0 - _lentur(q)
        return (16 * kuat * b, 0.0, 0.0, -0.08 * b, 1.0 - 0.10 * b)
    if mode == 'swing':
        if p < h:
            k = _mulus(p / h)
            return (-5 * k, 0.0, -22 * k, 0.03 * k, 1.0 + 0.03 * k)
        k = (p - h) / (1 - h)
        if k < 0.2:
            q = _mulus(k / 0.2)
            return (-5 + 15 * q, 0.0, -22 + 50 * q, 0.03 - 0.08 * q, 1.03 - 0.10 * q)
        q = (k - 0.2) / 0.8
        b = 1.0 - _lentur(q)
        return (10 * b, 0.0, 28 * b, -0.05 * b, 1.0 - 0.07 * b)
    if mode == 'water':
        # Menuang: condong dan miring pelan, napas naik-turun ringan.
        k = math.sin(math.pi * min(1.0, p))
        return (9 * k, 7 * k, 0.0, -0.03 * k + 0.02 * math.sin(p * math.pi * 4) * k,
                1.0 - 0.03 * k)
    if mode == 'bend':
        # Jongkok memetik: badan condong dari pinggang dan tubuh memendek
        # (lutut "menekuk" lewat gepeng), lalu bangkit dengan loncatan kecil.
        if p < h:
            k = _mulus(p / h)
            return (22 * k, 0.0, 0.0, 0.0, 1.0 - 0.24 * k)
        k = (p - h) / (1 - h)
        b = 1.0 - _lentur(k)
        lompat = 0.05 * math.sin(math.pi * min(1.0, k * 1.4))
        return (22 * b, 0.0, 0.0, lompat, 1.0 - 0.24 * b)
    if mode == 'gosok':
        k = math.sin(math.pi * min(1.0, p))
        return (13 * k, 6 * math.sin(p * math.pi * 6) * k, 0.0, -0.06 * k, 1.0 - 0.04 * k)
    if mode == 'kena':
        # Dipukul mob: tersentak ke belakang dalam ~60 ms, badan memendek,
        # lalu pulih dengan sedikit lewat. Tanpa ancang-ancang: pukulan
        # datang dari luar, bukan dari niat tokoh.
        if p < 0.15:
            q = _mulus(p / 0.15)
            return (-16 * q, 7 * q, 0.0, -0.05 * q, 1.0 - 0.10 * q)
        b = 1.0 - _lentur((p - 0.15) / 0.85)
        return (-16 * b, 7 * b, 0.0, -0.05 * b, 1.0 - 0.10 * b)
    if mode == 'bicara':
        k = math.sin(math.pi * min(1.0, p))
        return (4 * math.sin(p * math.pi * 4) * k, 2 * k, 0.0, 0.0, 1.0)
    return (0.0, 0.0, 0.0, 0.0, 1.0)


class JusGerak:
    """Pemutar lapisan untuk satu pemain. Dipanggil tiap frame dari Player."""

    def __init__(self, player):
        self.p = player
        self.mode = None
        self._dur = 0.35
        self._t = 0.0
        self._kena = False
        self._punch = 0.0          # sisa dorongan kamera (unit dunia)

    def mulai(self, mode: str, detik: float):
        self.mode = mode
        self._dur = max(0.2, float(detik))
        self._t = 0.0
        self._kena = False

    def aktif(self) -> bool:
        return self.mode is not None

    def tick(self, dt: float):
        char = getattr(self.p, '_char', None)
        poros = getattr(char, 'poros', None) if char is not None else None
        if self.mode is None:
            if poros is not None:
                getattr(char, 'pinggang', poros).setHpr(0, 0, 0)
                poros.setPos(0, 0, 0)
                poros.setScale(1)
            self._redam_kamera(dt)
            return
        self._t += dt
        p = min(1.0, self._t / self._dur)
        pitch, roll, yaw, dy, gepeng = kurva(self.mode, p)
        if poros is not None:
            # Dua simpul: poros (telapak) memegang turun-naik dan gepeng;
            # pinggang memegang condong/putar, supaya badan yang condong,
            # bukan seluruh tokoh yang miring dari telapak.
            # Panda: H = yaw, P = pitch, R = roll. Rig menghadap -Z lalu
            # diputar 180 di dalam, jadi "condong ke depan" = P negatif.
            pinggang = getattr(char, 'pinggang', poros)
            pinggang.setHpr(yaw, -pitch, roll)
            poros.setPos(0, dy, 0)
            lebar = 1.0 / math.sqrt(max(0.5, gepeng))
            poros.setScale(lebar, gepeng, lebar)
        if not self._kena and p >= _HENTAK.get(self.mode, 0.45):
            self._kena = True
            self._saat_kena()
        if p >= 1.0:
            self.mode = None
        self._redam_kamera(dt)

    # ── efek di momen hentakan ─────────────────────────────────────────
    def _saat_kena(self):
        m = self.mode
        if m in ('hoe', 'down', 'mine', 'swing'):
            self._punch = 0.10 if m == 'mine' else (0.07 if m == 'swing' else 0.06)
            self._debu(m)
        elif m == 'kena':
            self._punch = 0.12

    def _debu(self, m):
        try:
            from ursina import color
            fx, fy = self.p._facing_tile()
            from .config import TILE_SIZE as TS, GROUND_H
            warna = {'hoe': color.rgb(120, 86, 56), 'down': color.rgb(120, 86, 56),
                     'mine': color.rgb(150, 150, 150), 'swing': color.rgb(170, 130, 80)}[m]
            self.p._fx_burst(fx * TS, GROUND_H + 0.15, fy * TS, warna,
                             n=6, spread=0.35, dur=0.30)
        except Exception:
            pass

    def _redam_kamera(self, dt):
        """Dorongan kamera singkat: kamera turun lalu kembali dalam ~0,15 dtk.
        Dipasang lewat camera.y sesudah pengikut kamera app menaruhnya, jadi
        tidak menumpuk dari frame ke frame."""
        if self._punch <= 0.0:
            return
        try:
            from ursina import camera
            camera.y -= self._punch
        except Exception:
            pass
        self._punch = max(0.0, self._punch - dt * 0.6)
