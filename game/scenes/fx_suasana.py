"""Efek suasana bersama: kolam cahaya, benda berpijar, partikel melayang.

Semua entity dimasukkan ke world._obj_ents supaya ikut dibuang saat scene
berganti. Efek ini sengaja TIDAK memakai smooth_shader: cahaya tidak boleh
diredupkan oleh cahaya scene, justru itulah yang membuatnya terbaca menyala.
"""
import math
import random


def _daftar(world, e):
    world._obj_ents.append(e)
    return e


def _aditif(e):
    from panda3d.core import ColorBlendAttrib, DepthWriteAttrib, TransparencyAttrib
    e.setTransparency(TransparencyAttrib.MAlpha)
    e.setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd,
                                      ColorBlendAttrib.OIncomingAlpha,
                                      ColorBlendAttrib.OOne))
    e.setAttrib(DepthWriteAttrib.make(DepthWriteAttrib.MOff))
    e.setLightOff()
    e.setBin('fixed', 10)


def kolam_cahaya(world, x, z, radius, rgb, kuat=0.55, y=0.23):
    """Genangan cahaya bergradasi di lantai: terang di tengah, pudar ke tepi."""
    from ursina import Entity, Mesh, color
    from ursina.shaders import unlit_shader
    n = 40
    verts, cols, tris = [(0, 0, 0)], [color.rgba(rgb[0], rgb[1], rgb[2], 255 * kuat)], []
    for i in range(n):
        a = i * math.tau / n
        verts.append((math.cos(a), 0, math.sin(a)))
        cols.append(color.rgba(rgb[0], rgb[1], rgb[2], 0))
    for i in range(n):
        tris.extend((0, 1 + (i + 1) % n, 1 + i))
    e = Entity(model=Mesh(vertices=verts, triangles=tris, colors=cols),
               position=(x, y, z), scale=(radius, 1, radius),
               shader=unlit_shader, double_sided=True)
    _aditif(e)
    return _daftar(world, e)


def pijar(world, model, pos, scale, rgb, **kw):
    """Benda yang memancarkan cahaya sendiri (tidak terkena bayangan scene)."""
    from ursina import Entity, color
    from ursina.shaders import unlit_shader
    e = Entity(model=model, position=pos, scale=scale, color=color.rgb(*rgb),
               shader=unlit_shader, **kw)
    e.setLightOff()
    return _daftar(world, e)


def halo(world, pos, ukuran, rgb, kuat=0.45):
    """Bintik cahaya menghadap kamera di sekitar sumber terang (obor, kristal)."""
    from ursina import Entity, Mesh, color
    from ursina.shaders import unlit_shader
    n = 24
    verts, cols, tris = [(0, 0, 0)], [color.rgba(rgb[0], rgb[1], rgb[2], 255 * kuat)], []
    for i in range(n):
        a = i * math.tau / n
        verts.append((math.cos(a), math.sin(a), 0))
        cols.append(color.rgba(rgb[0], rgb[1], rgb[2], 0))
    for i in range(n):
        tris.extend((0, 1 + i, 1 + (i + 1) % n))
    e = Entity(model=Mesh(vertices=verts, triangles=tris, colors=cols),
               position=pos, scale=ukuran, shader=unlit_shader,
               billboard=True, double_sided=True)
    _aditif(e)
    return _daftar(world, e)


class Partikel:
    """Butir cahaya kecil yang melayang pelan di dalam sebuah kotak dunia.

    Satu Entity induk dengan `update` -- bukan satu skrip per butir -- supaya
    ongkosnya satu panggilan Python per frame untuk seluruh kawanan.
    """

    def __init__(self, world, x0, x1, z0, z1, y0, y1, jumlah, rgb,
                 ukuran=0.06, naik=0.15, goyang=0.35, kedip=True, seed=7):
        from ursina import Entity
        from ursina.shaders import unlit_shader
        rng = random.Random(seed)
        self.batas = (x0, x1, y0, y1, z0, z1)
        self.naik, self.goyang, self.kedip = naik, goyang, kedip
        self.induk = _daftar(world, Entity())
        self.induk.update = self._update
        self.butir = []
        for _ in range(jumlah):
            # Titik bulat bergradasi, bukan quad: kotak putih bertepi tajam yang
            # berdenyut terbaca sebagai kilatan blitz, bukan debu cahaya.
            b = Entity(parent=self.induk, model=_titik_lembut(rgb), billboard=True,
                       shader=unlit_shader, scale=ukuran * 2.4 * rng.uniform(0.6, 1.4),
                       position=(rng.uniform(x0, x1), rng.uniform(y0, y1), rng.uniform(z0, z1)))
            _aditif(b)
            self.butir.append([b, rng.uniform(0, math.tau), rng.uniform(0.6, 1.4)])
        self.t = 0.0

    def _update(self):
        from ursina import time
        dt = min(time.dt, 0.1)
        self.t += dt
        x0, x1, y0, y1, z0, z1 = self.batas
        tinggi = max(1e-3, y1 - y0)
        for b, fase, laju in self.butir:
            b.y += self.naik * laju * dt
            b.x += math.sin(self.t * 0.7 * laju + fase) * self.goyang * dt
            b.z += math.cos(self.t * 0.5 * laju + fase) * self.goyang * dt
            if b.y > y1:
                b.y = y0
            elif b.y < y0:
                b.y = y1
            # Pudar di kedua ujung supaya lompatan balik ke bawah tak terlihat.
            a = math.sin(math.pi * (b.y - y0) / tinggi)
            if self.kedip:
                a *= 0.6 + 0.4 * (0.5 + 0.5 * math.sin(self.t * 0.6 * laju + fase))
            b.setAlphaScale(max(0.0, a))


def _titik_lembut(rgb, kuat=0.5):
    from ursina import Mesh, color
    n = 12
    verts, cols, tris = [(0, 0, 0)], [color.rgba(rgb[0], rgb[1], rgb[2], 255 * kuat)], []
    for i in range(n):
        a = i * math.tau / n
        verts.append((math.cos(a), math.sin(a), 0))
        cols.append(color.rgba(rgb[0], rgb[1], rgb[2], 0))
    for i in range(n):
        tris.extend((0, 1 + i, 1 + (i + 1) % n))
    return Mesh(vertices=verts, triangles=tris, colors=cols)
