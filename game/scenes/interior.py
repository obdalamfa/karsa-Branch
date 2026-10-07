"""interior.py — Isi ruangan dalam: perabot buatan Blender, dinding, jendela, karpet.

Semua bangunan yang bisa dimasuki (rumah, warung, klinik, studio, bengkel,
rumah kaca) memakai builder ini lewat nama builder `'interior'`.

## Dari mana bentuknya

Perabot dimodelkan di Blender oleh `tools/blender_interior.py` dan diekspor ke
`assets/models/interior/<nama>.obj` dengan satu tekstur palet bersama. Shader
game hanya membaca satu tekstur (bukan Kd .mtl, bukan warna vertex), jadi UV
tiap muka menunjuk ke kotak warnanya di `palette.png`.

Grid ubin TETAP sumber kebenaran untuk logika: ubin BD tetap kasur untuk
tidur, ST tetap kompor untuk memasak, dan semua ubin perabot tetap memblokir.
Modul ini hanya mengganti RUPA-nya. Kalau model hilang, ubin itu digambar
sebagai kubus sederhana -- degradasi yang tercatat, bukan crash.

## Arah hadap

Model dibuat menghadap +z (arah +ty). Perabot yang bersandar ke dinding
diputar supaya punggungnya menempel ke dinding itu dan digeser sampai
punggungnya benar-benar menyentuh muka dinding -- perabot yang melayang 40 cm
dari dinding adalah tanda paling jelas ruangan yang disusun asal.
"""
from __future__ import annotations

import logging
import math
from pathlib import Path

from game.config import (TILE_SIZE, GROUND_H, WALL_H, WL, DR, FL, D, BD, ST, TB,
                         CHR, TV, BS, MR, FP, CL, PP, CH, CT, SH, CAL,
                         KLK, WC, SWR)

TS = TILE_SIZE
_DIR = Path(__file__).resolve().parent.parent.parent / 'assets' / 'models' / 'interior'

# Ubin yang rupanya diambil alih modul ini. world.py melewatkan kubus
# bawaannya untuk ubin-ubin ini di scene ber-builder 'interior'.
TILES = (BD, ST, TB, CHR, TV, BS, MR, FP, CL, PP, CH, CT, SH, CAL, KLK, WC, SWR)

MODEL = {
    BD: 'kasur', ST: 'kompor', TB: 'meja', CHR: 'kursi', TV: 'tv',
    BS: 'rak_buku', MR: 'lemari_cermin', FP: 'tungku', CL: 'jam', PP: 'pot',
    CH: 'peti', CT: 'konter', SH: 'rak', CAL: 'meja_tulis',
    KLK: 'kulkas', WC: 'toilet', SWR: 'pancuran',
}

# Ubin yang sama, rupa berbeda per bangunan. Hanya RUPA: kasur klinik tetap
# ubin BD (bisa ditiduri), landasan tempa tetap ubin TB.
VARIAN = {
    'shop':       {CT: 'konter_warung'},
    'clinic':     {BD: 'kasur_klinik', SH: 'rak_obat'},
    'studio':     {TB: 'kuda_kuda'},
    'smith':      {FP: 'tungku_tempa', CT: 'meja_kerja', SH: 'rak_senjata',
                   CH: 'tong', TB: 'landasan'},
    'greenhouse': {SH: 'rak_bibit', TB: 'meja_pot', FP: 'pot'},
}

# Perabot yang berderet membentuk satu benda panjang. Arah deretan menentukan
# dinding mana yang boleh dijadikan sandaran (lihat `_arah`).
_DERET = (CT, SH, BS)

# Warna dinding per bangunan: tiap ruangan punya suasana sendiri.
WARNA_DINDING = {
    'house':      (184, 166, 138),
    'shop':       (190, 164, 112),
    'clinic':     (196, 202, 190),
    'studio':     (198, 188, 168),
    'smith':      (118, 108, 98),
    'greenhouse': (168, 192, 180),
}
_WARNA_DINDING_BAKU = (180, 168, 146)
_WARNA_LIS = (96, 66, 46)

# Karpet: (x0, y0, x1, y1, warna_tepi, warna_tengah) dalam koordinat ubin,
# inklusif. Murni hiasan, tidak memblokir.
KARPET = {
    'house': [(2, 2, 6, 3, (120, 52, 44), (168, 116, 70)),
              (5, 4, 7, 5, (62, 86, 96), (150, 140, 110))],
    # (pojok mandi sengaja tanpa karpet: alas keramik sudah bagian model)
    'shop':  [(1, 4, 7, 5, (120, 52, 44), (176, 140, 84))],
    'clinic': [(2, 3, 3, 5, (70, 104, 100), (176, 184, 170))],
    'studio': [(2, 2, 5, 5, (92, 72, 104), (182, 160, 120))],
    'greenhouse': [(6, 4, 8, 6, (96, 120, 70), (150, 156, 112))],
}

_PAL_TEX = None
_MESH = {}        # nama -> Mesh induk (dibagi lewat salinan, lihat _instans)
_BOUNDS = {}      # nama -> (min_x, max_x, min_z, max_z) dalam ruang berkas


def _palet():
    global _PAL_TEX
    if _PAL_TEX is None:
        from PIL import Image
        from ursina import Texture
        t = Texture(Image.open(_DIR / 'palette.png').convert('RGB'))
        t.filtering = False       # kotak warna tidak boleh saling luber
        _PAL_TEX = t
    return _PAL_TEX


def _baca_obj(nama):
    """Parse OBJ segitiga (v/vt/vn) jadi Mesh Ursina. None kalau gagal."""
    from ursina import Mesh
    p = _DIR / f'{nama}.obj'
    v, vt, vn = [], [], []
    verts, uvs, norms = [], [], []
    try:
        with open(p, encoding='utf-8') as f:
            for ln in f:
                if ln.startswith('v '):
                    v.append(tuple(float(a) for a in ln.split()[1:4]))
                elif ln.startswith('vt '):
                    vt.append(tuple(float(a) for a in ln.split()[1:3]))
                elif ln.startswith('vn '):
                    vn.append(tuple(float(a) for a in ln.split()[1:4]))
                elif ln.startswith('f '):
                    sudut = ln.split()[1:]
                    if len(sudut) != 3:
                        continue          # diekspor triangulated; jaga-jaga
                    for s in sudut:
                        i = s.split('/')
                        verts.append(v[int(i[0]) - 1])
                        uvs.append(vt[int(i[1]) - 1] if len(i) > 1 and i[1] else (0, 0))
                        norms.append(vn[int(i[2]) - 1] if len(i) > 2 and i[2] else (0, 1, 0))
    except (OSError, ValueError, IndexError) as e:
        logging.error("Interior: model '%s' gagal dibaca (%s)", nama, e)
        return None
    if not verts:
        return None
    xs = [a[0] for a in verts]
    zs = [a[2] for a in verts]
    _BOUNDS[nama] = (min(xs), max(xs), min(zs), max(zs))
    return Mesh(vertices=verts, triangles=list(range(len(verts))), uvs=uvs,
                normals=norms, static=True)


def _instans(nama):
    """Salinan mesh yang aman dipasang ke SATU entity.

    Mesh Ursina adalah NodePath dan hanya boleh punya satu parent -- membagi
    satu mesh ke banyak entity membuat semua kecuali yang terakhir kosong.
    """
    if nama not in _MESH:
        _MESH[nama] = _baca_obj(nama)
    from game.meshes import _instance
    return _instance(_MESH[nama])


def _pasang(world, nama, wx, wz, rot_y, y=GROUND_H):
    from game.world import _e
    from ursina import color
    m = _instans(nama)
    if m is None:
        return None
    e = _e(m, (wx, y, wz), (1, 1, 1), None, color.white, soft=False,
           tex_obj=_palet(), rotation=(0, rot_y, 0))
    world._obj_ents.append(e)
    return e


def _kotak(world, pos, scale, rgb, rot_y=0):
    from game.world import _e
    from ursina import color
    e = _e('cube', pos, scale, None, color.rgb(*rgb), soft=False,
           rotation=(0, rot_y, 0))
    world._obj_ents.append(e)
    return e


# ─── GEOMETRI GRID ───────────────────────────────────────────────────────────
def _tile(scene, x, y):
    if 0 <= x < scene.w and 0 <= y < scene.h:
        return scene.tiles[y][x]
    return WL


def _dinding(scene, x, y):
    return _tile(scene, x, y) in (WL, DR)


# Arah hadap -> (rotasi_y, arah dinding di belakang (dx, dy)).
# Rotasi Ursina: 0 = menghadap +z, 90 = menghadap +x.
_HADAP = {
    'selatan': (0, (0, -1)),     # punggung ke dinding utara
    'utara':   (180, (0, 1)),
    'timur':   (90, (-1, 0)),
    'barat':   (-90, (1, 0)),
}


def _arah(scene, x, y, tid):
    """Arah hadap perabot di (x, y) berdasarkan dinding di sekitarnya.

    Perabot berderet (konter, rak) hanya boleh bersandar ke dinding yang
    SEJAJAR dengan deretannya: konter yang berderet ke timur tidak boleh
    berbalik menghadap barat hanya karena ujungnya menyentuh dinding timur --
    deretannya akan patah jadi dua arah.
    """
    datar = tid in _DERET and (_tile(scene, x - 1, y) == tid or _tile(scene, x + 1, y) == tid)
    tegak = tid in _DERET and (_tile(scene, x, y - 1) == tid or _tile(scene, x, y + 1) == tid)
    calon = []
    if not tegak:
        calon += ['selatan', 'utara']
    if not datar:
        calon += ['timur', 'barat']
    for h in calon:
        dx, dy = _HADAP[h][1]
        if _dinding(scene, x + dx, y + dy):
            return h, True
    return ('timur' if tegak and not datar else 'selatan'), False


def _geser_ke_dinding(nama, hadap):
    """Jarak geser supaya punggung model menempel ke muka dalam dinding."""
    b = _BOUNDS.get(nama)
    if not b:
        return 0.0
    punggung = -b[2]                  # jarak pusat -> sisi belakang (min z)
    return max(0.0, TS / 2 - punggung - 0.03)


def _sudut_ke(x, y, tx, ty):
    """Rotasi_y supaya muka depan (+z) menghadap ubin (tx, ty)."""
    return math.degrees(math.atan2(tx - x, ty - y))


def _cari(scene, tids, x, y, radius):
    best = None
    for yy in range(max(0, y - radius), min(scene.h, y + radius + 1)):
        for xx in range(max(0, x - radius), min(scene.w, x + radius + 1)):
            if scene.tiles[yy][xx] in tids:
                d = math.hypot(xx - x, yy - y)
                if best is None or d < best[0]:
                    best = (d, xx, yy)
    return best


# ─── BUILDER ─────────────────────────────────────────────────────────────────
def build_interior(world, scene):
    varian = VARIAN.get(scene.name, {})
    selesai = set()

    for y in range(scene.h):
        for x in range(scene.w):
            tid = scene.tiles[y][x]
            if tid not in TILES or (x, y) in selesai:
                continue
            nama = varian.get(tid, MODEL[tid])
            wx, wz = x * TS, y * TS

            if tid == CHR:
                _kursi(world, scene, x, y)
                continue

            # Dua meja makan bersebelahan = SATU meja panjang di tengahnya.
            if nama == 'meja':
                if _tile(scene, x + 1, y) == TB and (x + 1, y) not in selesai:
                    _instans_cek('meja_panjang')
                    _pasang(world, 'meja_panjang', wx + TS / 2, wz, 0)
                    selesai.add((x + 1, y))
                    continue
                if _tile(scene, x, y + 1) == TB and (x, y + 1) not in selesai:
                    _pasang(world, 'meja_panjang', wx, wz + TS / 2, 90)
                    selesai.add((x, y + 1))
                    continue

            hadap, bersandar = _arah(scene, x, y, tid)
            rot, (dx, dy) = _HADAP[hadap]
            if _instans_cek(nama) is None:
                _cadangan(world, tid, wx, wz)
                continue
            if bersandar:
                g = _geser_ke_dinding(nama, hadap)
                wx += dx * g
                wz += dy * g
            _pasang(world, nama, wx, wz, rot)

    _dinding_dalam(world, scene)
    _karpet(world, scene)
    if scene.name == 'greenhouse':
        _bedeng(world, scene)


def _instans_cek(nama):
    """Muat mesh induk (untuk batas) tanpa membuat salinan."""
    if nama not in _MESH:
        _MESH[nama] = _baca_obj(nama)
    return _MESH[nama]


def _cadangan(world, tid, wx, wz):
    """Kubus polos kalau model tidak ada -- ubinnya tetap terbaca ada isinya."""
    from game.world import OBJ_COLORS
    c = OBJ_COLORS.get(tid)
    rgb = (int(c[0] * 255), int(c[1] * 255), int(c[2] * 255)) if c else (130, 110, 90)
    _kotak(world, (wx, GROUND_H + 0.45, wz), (TS * 0.8, 0.9, TS * 0.8), rgb)


def _kursi(world, scene, x, y):
    """Kursi menghadap meja di sebelahnya; kalau tidak ada, ke TV/perapian."""
    wx, wz = x * TS, y * TS
    for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        if _tile(scene, x + dx, y + dy) == TB:
            # Merapat ke meja: kursi di tengah ubin tertinggal hampir satu
            # meter dari tepi meja -- tidak ada yang duduk sejauh itu.
            _pasang(world, 'kursi', wx + dx * 0.42, wz + dy * 0.42,
                    _sudut_ke(x, y, x + dx, y + dy))
            return
    for tids, r in (((TV,), 5), ((FP,), 5)):
        hit = _cari(scene, tids, x, y, r)
        if hit:
            _pasang(world, 'kursi', wx, wz, _sudut_ke(x, y, hit[1], hit[2]))
            return
    hadap, bersandar = _arah(scene, x, y, CHR)
    rot, (dx, dy) = _HADAP[hadap]
    g = 0.5 if bersandar else 0.0
    _pasang(world, 'kursi', wx + dx * g, wz + dy * g, rot)


def _dinding_dalam(world, scene):
    """Warnai dinding, pasang lis kayu, jendela, dan kusen pintu.

    Hiasan dinding didaftarkan ke `world._wall_decor` per ubin dinding, supaya
    ikut menghilang saat dinding itu dipangkas cutaway. Tanpa itu, jendela dan
    lis akan melayang di udara di atas dinding yang sudah dipotong.
    """
    from ursina import color
    from game.world import _e
    rgb = WARNA_DINDING.get(scene.name, _WARNA_DINDING_BAKU)
    for rec in world._wall_ents:
        rec[0].color = color.rgb(*rgb)
        # Tutup gelap di puncak dinding, gaya potongan dinding The Sims.
        # Dinding setebal satu ubin (2 m) dilihat dari atas: tanpa tutup ini
        # bidang atasnya kena cahaya penuh dan terbaca sebagai pinggiran putih
        # menyilaukan di sekeliling ruangan. Jadi ANAK entity dinding supaya
        # ikut turun saat dinding dipangkas cutaway.
        tutup = _e('cube', (0, 0, 0), (1, 1, 1), None, color.rgb(58, 46, 40), soft=False)
        tutup.parent = rec[0]
        tutup.position = (0, 0.5, 0)
        # Tebal relatif terhadap tinggi dinding; ditahan >= 5 cm nyata supaya
        # tidak bertarung dengan bidang atas dinding di depth buffer.
        tutup.scale = (1.0, 0.1 / rec[1], 1.0)
        world._obj_ents.append(tutup)

    kaca = scene.name == 'greenhouse'
    for y in range(scene.h):
        for x in range(scene.w):
            t = scene.tiles[y][x]
            if t == DR:
                _pintu(world, scene, x, y)
                continue
            if t != WL:
                continue
            for h, (rot, (bx, by)) in _HADAP.items():
                # Muka dalam dinding ini menghadap ke ubin (x - bx, y - by).
                nx, ny = x - bx, y - by
                if not (0 <= nx < scene.w and 0 <= ny < scene.h):
                    continue
                isi = scene.tiles[ny][nx]
                if isi in (WL, DR):
                    continue
                # Titik muka dalam dinding.
                fx = x * TS - bx * TS / 2
                fz = y * TS - by * TS / 2
                hias = []
                # Lis bawah (wainscot) setinggi 0,95 m.
                lebar = TS
                tebal = 0.05
                sx, sz = (lebar, tebal) if bx == 0 else (tebal, lebar)
                hias.append(_kotak(world, (fx - bx * tebal / 2, GROUND_H + 0.475, fz - by * tebal / 2),
                                   (sx, 0.95, sz), _WARNA_LIS))
                hias.append(_kotak(world, (fx - bx * 0.035, GROUND_H + 0.97, fz - by * 0.035),
                                   (sx if bx == 0 else 0.07, 0.05, sz if bx != 0 else 0.07),
                                   (70, 48, 34)))
                if _perlu_jendela(scene, x, y, nx, ny, isi, kaca):
                    e = _pasang(world, 'jendela', fx, fz, rot, y=GROUND_H)
                    if e:
                        hias.append(e)
                world._wall_decor.setdefault((x, y), []).extend(hias)


_RENDAH = (FL, D, BD, TB, CHR, CT, CH, PP, ST, WC)


def _perlu_jendela(scene, x, y, nx, ny, isi, kaca):
    if kaca:
        return True
    if isi not in _RENDAH:
        return False                 # di belakang rak tinggi jendela tertutup
    # Jangan menempel pintu, dan beri jarak supaya dinding tidak bolong-bolong.
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if _tile(scene, x + dx, y + dy) == DR:
                return False
    pos = x if ny != y else y
    return pos % 3 == 2


def _pintu(world, scene, x, y):
    for h, (rot, (bx, by)) in _HADAP.items():
        # Pintu menghadap ke dalam: punggungnya ke arah luar peta.
        nx, ny = x - bx, y - by
        if 0 <= nx < scene.w and 0 <= ny < scene.h and scene.tiles[ny][nx] not in (WL, DR):
            e = _pasang(world, 'pintu', x * TS, y * TS, rot)
            if e:
                world._wall_decor.setdefault((x, y), []).append(e)
            return


def _karpet(world, scene):
    for x0, y0, x1, y1, tepi, tengah in KARPET.get(scene.name, ()):
        cx = (x0 + x1) / 2 * TS
        cz = (y0 + y1) / 2 * TS
        w = (x1 - x0 + 1) * TS - 0.5
        d = (y1 - y0 + 1) * TS - 0.5
        # SATU lapis: tengah + empat bingkai bersebelahan, tidak bertumpuk.
        # Versi bertumpuk (bingkai di bawah, tengah 2 cm di atasnya) tampil
        # belang-belang: dari jarak kamera, presisi depth buffer tidak cukup
        # untuk memisahkan dua bidang yang hanya terpaut 2 cm.
        t, h = 0.2, 0.05
        y = GROUND_H + h / 2
        _kotak(world, (cx, y, cz), (w - 2 * t, h, d - 2 * t), tengah)
        for sz in (-1, 1):
            _kotak(world, (cx, y, cz + sz * (d - t) / 2), (w, h, t), tepi)
        for sx in (-1, 1):
            _kotak(world, (cx + sx * (w - t) / 2, y, cz), (t, h, d - 2 * t), tepi)


def _bedeng(world, scene):
    """Bingkai papan di tepi bedeng tanah rumah kaca."""
    for y in range(scene.h):
        for x in range(scene.w):
            if scene.tiles[y][x] != D:
                continue
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                if _tile(scene, x + dx, y + dy) == D:
                    continue
                cx = x * TS + dx * (TS / 2 - 0.05)
                cz = y * TS + dy * (TS / 2 - 0.05)
                sc = (TS, 0.28, 0.1) if dx == 0 else (0.1, 0.28, TS)
                _kotak(world, (cx, GROUND_H + 0.14, cz), sc, (110, 78, 50))
