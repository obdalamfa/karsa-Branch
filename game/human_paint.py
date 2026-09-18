"""human_paint.py — mewarnai mesh humanoid tanpa memecahnya jadi banyak entity.

Kenapa ini ada. Di mesin tanpa instalasi TSO, `build_vitaboy_human_npc()`
gagal dan warga desa jatuh ke `assets/models/humanoid.obj`. Mesh-nya sendiri
baik-baik saja — siluetnya benar, normalnya benar — tapi satu mesh hanya punya
satu `entity.color`, dan warna itu tidak pernah diisi. Jadi setiap warga desa
sampai ke layar sebagai gumpalan PUTIH POLOS: bukan karena avatarnya hilang,
tapi karena tidak ada yang pernah memberitahu warnanya.

Kenapa per-vertex, bukan dipecah jadi beberapa Entity. Memecah humanoid jadi
sepatu/celana/baju/kulit berarti lima Entity per warga desa. Di scene town
sudah ada 1.884 entity dan ms/frame sudah jadi masalah yang belum disentuh
(Tahap 3); menambah puluhan entity hanya demi warna adalah ongkos yang
dibayar di tempat yang paling tidak mampu membayarnya. Satu kolom warna di
vertex data memberi hasil yang sama dengan nol entity tambahan.

Yang membuat ini bisa: `smooth_shader.py` sekarang mengalikan `p3d_Color` ke
warna dasar. Geometri tanpa kolom warna diikat Panda ke putih, jadi entity
lama tidak berubah sedikit pun.

Pembagian bagian TIDAK ditebak dari tinggi vertex. `humanoid.obj` lahir dari
`tools/gen_humanoid_obj.py` sebagai tiga objek terpisah — `part_0` badan
(lathe), `part_1` dan `part_2` lengan (kapsul) — dan Panda mempertahankan
ketiganya sebagai GeomNode bernama. Menebak lengan lewat `abs(x) > 0.36` akan
salah di sisi DALAM lengan, yang jangkauan x-nya (0,29–0,55) bertumpang tindih
dengan bahu badan (maksimum 0,34). Namanya sudah ada; tidak perlu menebak.
"""
from __future__ import annotations

# Ambang tinggi diambil langsung dari _PROFILE di tools/gen_humanoid_obj.py.
# Kalau profilnya berubah, angka-angka ini ikut berubah — itu sebabnya
# labelnya ditulis, supaya bisa dicocokkan baris per baris.
_Y_SEPATU  = 0.11   # foot_apex .. ankle
_Y_CELANA  = 1.58   # shin .. hip
_Y_BAJU    = 2.27   # pelvis_top .. shoulder_top
_Y_KULIT   = 2.82   # neck_bot .. forehead
#              di atas itu: crown → rambut

_Y_SIKU    = 1.55   # di lengan: di atas ini lengan baju, di bawah ini kulit

# Palet warga desa. Bukan acak: tiap baris satu orang yang bisa dibedakan dari
# jauh, karena dari jauh warna baju adalah SATU-SATUNYA yang membedakan mereka.
_BAJU = (
    (196,  82,  74), (74, 128, 196), (232, 176,  70), (108, 168, 104),
    (168,  96, 176), (222, 128,  86), (86, 172, 168), (204, 204, 212),
    (146, 110,  84), (120, 132, 200),
)
_CELANA = (
    (72,  78,  96), (94,  74,  58), (54,  62,  74), (108,  96,  76),
    (66,  66,  72), (86,  70,  90),
)
_KULIT = (
    (238, 198, 158), (222, 176, 132), (196, 146, 104),
    (162, 114,  78), (124,  84,  58),
)
_RAMBUT = (
    (48,  38,  34), (72,  50,  36), (110,  76,  46), (156, 120,  70),
    (36,  34,  40), (94,  62,  52),
)
_SEPATU = (52, 44, 40)


def _bilang(actor_id: str) -> int:
    """Angka stabil dari id.

    `sum(map(ord, ...))`, BUKAN `hash()`: hash() Python di-randomisasi per
    proses, jadi warna warga desa akan berubah tiap kali game dijalankan —
    dan tangkapan layar regresi ikut berubah tanpa ada yang diubah. Pola yang
    sama sudah dipakai di entities.py untuk rotasi hewan, dengan alasan yang
    persis sama.
    """
    return sum(map(ord, actor_id or 'x'))


def palet_untuk(actor_id: str) -> dict:
    """Palet deterministik per warga desa."""
    n = _bilang(actor_id)
    return {
        'baju':   _BAJU[n % len(_BAJU)],
        'celana': _CELANA[(n // 3) % len(_CELANA)],
        'kulit':  _KULIT[(n // 7) % len(_KULIT)],
        'rambut': _RAMBUT[(n // 11) % len(_RAMBUT)],
        'sepatu': _SEPATU,
    }


def _warna_badan(y: float, pal: dict):
    if y < _Y_SEPATU:
        return pal['sepatu']
    if y < _Y_CELANA:
        return pal['celana']
    if y < _Y_BAJU:
        return pal['baju']
    if y < _Y_KULIT:
        return pal['kulit']
    return pal['rambut']


def _warna_lengan(y: float, pal: dict):
    return pal['baju'] if y > _Y_SIKU else pal['kulit']


def paint_humanoid(np_, pal: dict) -> bool:
    """Tulis kolom warna per-vertex ke model humanoid yang sudah dimuat.

    `np_` adalah NodePath hasil `load_model_file('humanoid')` — sudah berupa
    salinan lepas per-actor (lihat `_model_instance`), jadi mewarnai satu
    actor tidak ikut mewarnai actor lain. `modifyVertexData()` memicu
    copy-on-write Panda, yang memutus perkongsian vertex data dari salinan.

    Mengembalikan True kalau ada yang benar-benar diwarnai.
    """
    try:
        from panda3d.core import (Geom, GeomVertexArrayFormat, GeomVertexFormat,
                                  GeomVertexReader, GeomVertexWriter,
                                  InternalName, ColorAttrib)
    except Exception:
        return False
    if np_ is None:
        return False

    warna_int = InternalName.getColor()
    diwarnai = 0

    for gn in np_.findAllMatches('**/+GeomNode'):
        nama = gn.getName()
        # part_0 = badan (lathe), part_1/part_2 = lengan (kapsul). Lihat
        # tools/gen_humanoid_obj.py:main().
        pilih = _warna_badan if nama.endswith('part_0') else _warna_lengan
        node = gn.node()
        for i in range(node.getNumGeoms()):
            try:
                geom = node.modifyGeom(i)
                vdata = geom.modifyVertexData()
                if not vdata.hasColumn(warna_int):
                    fmt = GeomVertexFormat(vdata.getFormat())
                    arr = GeomVertexArrayFormat()
                    arr.addColumn(warna_int, 4, Geom.NTFloat32, Geom.CColor)
                    fmt.addArray(arr)
                    vdata.setFormat(GeomVertexFormat.registerFormat(fmt))

                baca = GeomVertexReader(vdata, 'vertex')
                tulis = GeomVertexWriter(vdata, warna_int)
                while not baca.isAtEnd():
                    v = baca.getData3()
                    r, g, b = pilih(v[1], pal)
                    tulis.setData4(r / 255.0, g / 255.0, b / 255.0, 1.0)
                diwarnai += 1
            except Exception:
                continue

    if diwarnai:
        try:
            # Tanpa ini Panda boleh mengabaikan kolom warnanya. Ursina memakai
            # setColorScale untuk entity.color, jadi tidak bentrok: yang satu
            # dikalikan ke yang lain.
            np_.setAttrib(ColorAttrib.makeVertex())
        except Exception:
            pass
    return diwarnai > 0
