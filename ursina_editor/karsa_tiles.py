"""karsa_tiles.py — Tampilkan grid ubin scene game sebagai entity di viewport.

Game menyimpan dunia sebagai GRID UBIN (`Scene.tiles[y][x]`), bukan sebagai
daftar entity, sedangkan editor ini bekerja dengan entity. Modul ini
menjembatani keduanya untuk TAMPILAN: satu Entity per ubin.

## Kenapa tekstur asli, bukan warna karangan

`world.py` sudah punya `TILE_TEX` dan `OBJ_TEX` yang memetakan tiap ubin ke
teksturnya. Memakai warna karangan akan membuat editor menampilkan peta yang
tidak mirip game sama sekali, dan penata letak kehilangan satu-satunya umpan
balik yang penting: apakah ladangnya benar-benar terbaca sebagai ladang.

## Kenapa jalur absolut, bukan `asset_folder`

`assets/textures/` berada di dalam paket game, bukan di folder editor. Menyetel
`application.asset_folder` ke sana akan ikut memindahkan tempat Ursina mencari
tekstur bawaannya, dan editor ini memakai beberapa di antaranya. Jadi tekstur
dimuat lewat jalur absolut dan di-cache.

## Ubin tanpa tekstur

Empat ubin -- PALM, TV, CHR, CAL -- tidak punya entri di `TILE_TEX` maupun
`OBJ_TEX`, dan juga tidak ada di `OBJ_COLORS`. Ketiganya mendapat warna netral
di `WARNA_CADANGAN` supaya tetap terlihat dan tetap bisa disunting, alih-alih
menghilang dari viewport tanpa penjelasan.
"""
import sys
from pathlib import Path

_DIR_EDITOR = Path(__file__).resolve().parent
_ROOT_REPO = _DIR_EDITOR.parent
if str(_ROOT_REPO) not in sys.path:
    sys.path.insert(0, str(_ROOT_REPO))

from ursina import Entity, Texture, Vec3, color, destroy   # noqa: E402

from game.config import GROUND_H, TILE_IDS, TILE_SIZE      # noqa: E402
from game.world import OBJ_COLORS, OBJ_TEX, TILE_TEX       # noqa: E402

DIR_TEKSTUR = _ROOT_REPO / 'assets' / 'textures'

# Ubin -> nama tekstur. Dua tabel milik world.py digabung; di sana keduanya
# dipisah karena ubin tanah dan ubin objek dibangun dengan cara berbeda, tapi
# bagi editor keduanya sama: sesuatu yang menempati satu ubin.
TEKSTUR = {**TILE_TEX, **OBJ_TEX}

_ID_KE_NAMA = {tid: nama for nama, tid in TILE_IDS.items()}

# Ubin yang tidak punya tekstur maupun warna di world.py.
WARNA_CADANGAN = {
    'PALM': (110, 150, 90),
    'TV':   (60, 60, 70),
    'CHR':  (130, 95, 60),
    'CAL':  (230, 230, 220),
}

_TEX_CACHE: dict = {}


def nama_ubin(tid: int) -> str:
    """Nama konstanta sebuah ubin, mis. 'FN'. Dipakai panel palet."""
    return _ID_KE_NAMA.get(tid, f'UNKNOWN_{tid}')


def tekstur_ubin(tid: int):
    """Nama tekstur game untuk ubin ini, atau None."""
    return TEKSTUR.get(tid)


def warna_ubin(tid: int):
    """Warna untuk ubin tanpa tekstur."""
    c = OBJ_COLORS.get(tid)
    if c is not None:
        return c
    cadangan = WARNA_CADANGAN.get(nama_ubin(tid))
    if cadangan:
        return color.rgb(*cadangan)
    return color.rgb(150, 150, 150)


def _tekstur(nama: str):
    """Texture game, di-cache.

    Kegagalan memuat tekstur TIDAK boleh menjatuhkan editor: ubinnya turun ke
    warna cadangan dan tetap bisa disunting. Perlu karena di lingkungan uji
    tertentu (harness gauntlet memakai VFS ramdisk) Panda3D tidak bisa membaca
    berkas fisik walaupun Python bisa -- persoalan lingkungan, bukan persoalan
    aset.
    """
    if nama in _TEX_CACHE:
        return _TEX_CACHE[nama]
    t = None
    p = DIR_TEKSTUR / f'{nama}.png'
    if p.exists():
        try:
            t = Texture(str(p))
        except Exception:
            t = None
    _TEX_CACHE[nama] = t
    return t


def palet() -> list:
    """Daftar (tid, nama, punya_tekstur) untuk panel palet editor."""
    return sorted(((tid, nama, tekstur_ubin(tid) is not None)
                   for nama, tid in TILE_IDS.items()),
                  key=lambda r: r[1])


class LayerUbin:
    """Satu Entity per ubin scene, plus jalan pulang untuk setiap perubahan.

    Perubahan ditulis ke `scene.tiles` DAN ke viewport dalam satu langkah.
    Kalau keduanya bisa berbeda, editor akan menampilkan peta yang tidak sama
    dengan yang akan disimpan -- dan itu jenis kebohongan yang paling mahal di
    alat penyunting.
    """

    def __init__(self, scene, parent=None, tinggi=None):
        self.scene = scene
        self.tinggi = GROUND_H if tinggi is None else tinggi
        self.root = Entity(parent=parent, name=f'karsa_{scene.name}')
        self.ubin: dict = {}          # (x, y) -> Entity
        self.bangun()

    def bangun(self):
        """Bangun ulang seluruh viewport dari `scene.tiles`."""
        for e in list(self.ubin.values()):
            destroy(e)
        self.ubin.clear()
        for y, baris in enumerate(self.scene.tiles):
            for x, tid in enumerate(baris):
                self.ubin[(x, y)] = self._entitas(x, y, tid)

    def _entitas(self, x: int, y: int, tid: int):
        nama = tekstur_ubin(tid)
        tex = _tekstur(nama) if nama else None
        e = Entity(
            parent=self.root,
            model='cube',
            position=Vec3(x * TILE_SIZE, self.tinggi, y * TILE_SIZE),
            scale=Vec3(TILE_SIZE, 0.04, TILE_SIZE),
            texture=tex,
            color=color.white if tex else warna_ubin(tid),
        )
        # Koordinat ubin disimpan di entity supaya klik di viewport bisa
        # diterjemahkan balik tanpa menghitungnya lagi dari posisi.
        e.ubin_x, e.ubin_y = x, y
        return e

    def koordinat(self, entity):
        """Koordinat ubin sebuah entity, atau None kalau bukan ubin layer ini."""
        x = getattr(entity, 'ubin_x', None)
        if x is None:
            return None
        return (x, getattr(entity, 'ubin_y'))

    def set(self, x: int, y: int, tid: int) -> bool:
        """Ubah satu ubin di scene DAN di viewport."""
        if not (0 <= y < self.scene.h and 0 <= x < self.scene.w):
            return False
        self.scene.tiles[y][x] = tid
        lama = self.ubin.get((x, y))
        if lama is not None:
            destroy(lama)
        self.ubin[(x, y)] = self._entitas(x, y, tid)
        return True

    def jumlah_entity(self) -> int:
        return len(self.ubin)


class LayerObjek:
    """Viewport untuk `Scene.objects` milik game, plus jalan pulangnya.

    Bergaya sama dengan `LayerUbin`: satu Entity per objek, dan tiap perubahan
    ditulis ke `scene.objects` DAN ke viewport dalam satu langkah. Kalau
    keduanya bisa berbeda, editor menampilkan peta yang tidak sama dengan yang
    akan disimpan -- dan itu kebohongan yang paling mahal di alat penyunting.

    Rumus posisinya milik `game.objects.posisi_dunia` / `dari_posisi_dunia`,
    bukan salinan di sini, supaya benda tidak melompat tiap kali disimpan dari
    editor lalu dimuat game.
    """

    def __init__(self, scene, parent=None):
        self.scene = scene
        self.root = Entity(parent=parent, name=f'karsa_obj_{scene.name}')
        self.entitas: list = []
        self.bangun()

    def bangun(self):
        for e in self.entitas:
            destroy(e)
        self.entitas = [self._entitas(o) for o in self.scene.objects]

    def _entitas(self, o):
        from game.objects import posisi_dunia, tile_dari_kind
        tid = tile_dari_kind(o['kind'])
        nama_tex = TEKSTUR.get(tid) if tid is not None else None
        tex = _tekstur(nama_tex) if nama_tex else None
        px, py, pz, tinggi = posisi_dunia(o, TILE_SIZE, GROUND_H)
        lebar = TILE_SIZE * 0.8 * o['scale']
        e = Entity(parent=self.root, model='cube',
                   position=Vec3(px, py, pz),
                   scale=Vec3(lebar, tinggi, lebar),
                   texture=tex,
                   color=color.white if tex else warna_ubin(tid),
                   rotation_y=o['rot_y'])
        # Ditandai supaya klik di viewport bisa dibedakan dari ubin dan dari
        # entity bebas milik editor generik.
        e.kind = o['kind']
        e.is_karsa_object = True
        return e

    def index_dari(self, entity):
        for i, e in enumerate(self.entitas):
            if e is entity:
                return i
        return None

    def sinkron(self, entity) -> bool:
        """Tulis posisi entity kembali ke `scene.objects`.

        Kebalikan dari `posisi_dunia`: `y` entity adalah ketinggian PUSAT kotak,
        jadi tinggi kotaknya dikurangi lagi supaya `h` kembali berarti
        "ketinggian alas di atas tanah".
        """
        i = self.index_dari(entity)
        if i is None:
            return False
        from game.objects import dari_posisi_dunia
        self.scene.objects[i] = dari_posisi_dunia(
            entity.kind, entity.x, entity.y, entity.z, entity.rotation_y,
            self.scene.objects[i]['scale'], TILE_SIZE, GROUND_H)
        # Setter `Scene.objects` memvalidasi ulang; kalau sampai ada entri yang
        # dibuang, daftar entity di sini jadi tidak sejajar lagi.
        if len(self.scene.objects) != len(self.entitas):
            self.bangun()
        return True

    def tambah(self, kind: str, x: float, y: float,
               h: float = 0.0, rot_y: float = 0.0):
        """Tambah objek di koordinat ubin. Mengembalikan entity barunya."""
        self.scene.objects = list(self.scene.objects) + [
            {'kind': kind, 'x': x, 'y': y, 'h': h, 'rot_y': rot_y, 'scale': 1.0}]
        self.bangun()
        return self.entitas[-1] if self.entitas else None

    def hapus(self, entity) -> bool:
        i = self.index_dari(entity)
        if i is None:
            return False
        self.scene.objects = [o for j, o in enumerate(self.scene.objects)
                              if j != i]
        self.bangun()
        return True

    def jumlah(self) -> int:
        return len(self.entitas)
