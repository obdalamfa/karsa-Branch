"""scenes/__init__.py — Bangun SCENES dari berkas DATA kalau ada, dari kode kalau tidak.

Sejak Fase 3, `<nama>.json` di folder ini adalah yang DIPAKAI. Kode `build_*()`
tetap ada dan tetap jadi jalur cadangan, dan `tools/scene_export.py --check`
menjaga keduanya tidak pernah berbeda diam-diam.

## Siapa yang menulis apa

Game **tidak pernah** menulis berkas scene. Yang menulis adalah editor peta,
atau `tools/scene_export.py` yang menurunkannya dari kode.

Mutasi saat bermain -- menebang pohon (`interaction_controller.py:131`),
menambang ore (`:166`), memperbaiki mercusuar (`:407`) -- menyentuh SALINAN di
memori saja, karena `SCENES` dibangun sekali saat impor dan tidak pernah
ditulis ulang. Perubahan itu bertahan sepanjang sesi lalu hilang saat program
ditutup. Itu perilaku yang sudah ada sebelum Fase 3 dan sengaja tidak diubah:
Fase 3 murni soal bentuk data. Membuat pohon yang ditebang bertahan permanen
adalah pekerjaan tersendiri yang menyentuh `state.py` dan save.
"""
import json
import logging
from pathlib import Path

from .farm import build_farm
from .town import build_town
from .mountain import build_mountain
from .lake import build_lake
from .cemetery import build_cemetery
from .beach import build_beach
from .house import build_house
from .shop import build_shop
from .clinic import build_clinic
from .studio import build_studio
from .smith import build_smith
from .greenhouse import build_greenhouse
from .naga_cave import build_naga_cave
from .dungeon import build_dungeon_placeholder
from .swarga import build_swarga
from .lawang import build_lawang
from .scene_base import Scene

_DIR = Path(__file__).resolve().parent

# Versi KODE tiap scene. Sengaja dipisahkan dari `SCENES`, karena `SCENES` bisa
# berisi hasil BACAAN berkas data -- membandingkan `SCENES` dengan berkasnya
# sendiri akan selalu setuju dan tidak membuktikan apa pun.
# `tools/scene_export.py --check` memakai kamus ini untuk mengadu kode melawan
# data, dan itulah yang membuat penyimpangan di antara keduanya ketahuan.
SCENE_BUILDERS = {
    'farm': build_farm,
    'town': build_town,
    'mountain': build_mountain,
    'lake': build_lake,
    'cemetery': build_cemetery,
    'beach': build_beach,
    'house': build_house,
    'shop': build_shop,
    'clinic': build_clinic,
    'studio': build_studio,
    'smith': build_smith,
    'greenhouse': build_greenhouse,
    'naga_cave': build_naga_cave,
    'dungeon': build_dungeon_placeholder,
    'swarga': build_swarga,
    'lawang': build_lawang,      # Dukuh Lawang, Cerita Dua Desa
}


def _muat(nama: str, bangun):
    """Data kalau ada dan sehat; kode kalau tidak.

    Berkas data yang rusak TIDAK boleh membuat game tidak bisa dibuka. Ia
    dilaporkan sebagai error lalu dilewati -- pola yang sama dengan kegagalan
    Vitaboy di `entities.py`, dan sejalan dengan sikap proyek ini bahwa
    degradasi yang tercatat lebih baik daripada crash yang senyap.
    """
    p = _DIR / f'{nama}.json'
    if p.exists():
        try:
            # `utf-8-sig` menerima berkas dengan maupun tanpa BOM. Notepad
            # Windows menuliskan BOM, dan tanpa ini berkas yang disunting
            # dengan Notepad akan ditolak -- scenenya kembali ke kode dan
            # perubahan penyuntingnya diam-diam tidak berpengaruh.
            return Scene.from_dict(
                json.loads(p.read_text(encoding='utf-8-sig')))
        except Exception as e:
            logging.error(
                "Scene '%s': %s rusak (%s: %s) -- jatuh ke kode. "
                "Jalankan tools/scene_export.py untuk menulis ulang berkasnya.",
                nama, p.name, type(e).__name__, e)
    return bangun()


SCENES = {nama: _muat(nama, bangun) for nama, bangun in SCENE_BUILDERS.items()}


def sesuaikan_scene(nama: str, scene, state) -> None:
    """Setel ubin & portal yang bergantung pada kemajuan cerita.

    Cerita Dua Desa babak 2 membuka jalan lama Lawang <-> Gua Sang Hyang.
    SCENES dibangun sekali saat impor, jadi peta yang bisa berubah harus disetel
    ulang TIAP kali dimuat, dua arah (buka maupun tutup) — supaya memuat save
    lama sesudah save baru tidak mewarisi ubin yang sudah dibuka.

    Kaitnya dikunci NAMA scene di sini, bukan ditempel di objek Scene: sebagian
    besar SCENES hasil bacaan berkas JSON, dan fungsi Python tidak bisa ikut
    tersimpan di sana — alasan yang sama dengan BUILDER_NAMES di scene_base.py.
    World3D.load_scene() memanggilnya sebelum ubin dibangun.
    """
    sebelum = list(scene.portals)
    if nama == 'lawang':
        from .lawang import sesuaikan_lawang
        sesuaikan_lawang(scene, state)
    elif nama == 'naga_cave':
        from .naga_cave import sesuaikan_naga_cave
        sesuaikan_naga_cave(scene, state)
    if list(scene.portals) != sebelum:
        # Graf portal berubah. perjalanan.rute di-cache (lru_cache), jadi tanpa
        # ini warga yang rutenya dihitung saat jalan lama terbuka tetap menuju
        # pintu (4,1) sesudah save lama menutupnya lagi.
        from ..perjalanan import rute
        rute.cache_clear()
