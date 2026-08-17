"""sims_build.py — Mode BANGUN/BELI ala The Sims (milestone S7).

Pemain membeli objek dgn Simoleon lalu menaruhnya di petak kosong, atau
menjualnya kembali (dapat sebagian uang). Objek yang ditaruh MEMENUHI MOTIF
persis seperti objek bawaan — karena memakai katalog yang sama (S2).

PENTING soal ketahanan data:
Scene dibangun dari template global SCENES, jadi menulis langsung ke
scene.tiles saja akan HILANG saat game dimuat ulang. Karena itu setiap
penempatan dicatat di state.placed_objects, lalu di-OVERLAY kembali ke
scene.tiles setiap kali scene dimuat (World3D.load_scene).

    state.placed_objects = { 'house': { '4,6': <tile_id>, ... }, ... }
"""
from .config import WALKABLE, TILE_NAMES
from .sims_objects import SIMS_OBJECTS

# tile_id → harga beli (Simoleon). Hanya objek di katalog S2 yang bisa dibeli.
BUY_PRICES = {}


def _init_prices():
    from .config import BD, ST, TV, CHR, BS, FP, MR, TB, KLK, WC, SWR
    BUY_PRICES.update({
        CHR: 60,    # kursi
        TB: 90,     # meja makan
        BD: 220,    # ranjang
        WC: 180,    # toilet
        SWR: 260,   # pancuran
        KLK: 300,   # kulkas
        ST: 240,    # kompor
        TV: 350,    # televisi
        BS: 150,    # rak buku
        FP: 280,    # perapian
        MR: 110,    # cermin
    })


_init_prices()

# Dijual kembali dgn separuh harga (kerugian wajar, spt Sims)
SELL_RATIO = 0.5


def catalog():
    """[(tile_id, label, aksi, harga)] urut harga — untuk UI katalog."""
    out = []
    for tid, price in BUY_PRICES.items():
        obj = SIMS_OBJECTS.get(tid)
        if not obj:
            continue
        out.append((tid, obj['label'], obj['action'], price))
    out.sort(key=lambda r: r[3])
    return out


def sell_value(tile_id: int) -> int:
    return int(BUY_PRICES.get(tile_id, 0) * SELL_RATIO)


def _placed(state) -> dict:
    if getattr(state, 'placed_objects', None) is None:
        state.placed_objects = {}
    return state.placed_objects


def apply_placed(state, scene):
    """Overlay objek yang pernah dibeli ke grid scene. Dipanggil saat scene
    dimuat, SEBELUM tile dirender — supaya objek bertahan lintas save/muat."""
    if scene is None:
        return 0
    rec = _placed(state).get(getattr(scene, 'name', ''), {})
    n = 0
    for key, tid in list(rec.items()):
        try:
            tx, ty = (int(v) for v in key.split(','))
        except Exception:
            continue
        if 0 <= ty < scene.h and 0 <= tx < scene.w:
            scene.tiles[ty][tx] = int(tid)
            n += 1
    return n


def can_place(state, world, tx: int, ty: int):
    """(boleh, alasan_bila_tidak) — petak harus ada, kosong & bisa dipijak."""
    scene = getattr(world, 'scene_obj', None)
    if scene is None:
        return False, "Tak ada scene aktif."
    if not (0 <= ty < scene.h and 0 <= tx < scene.w):
        return False, "Di luar petak."
    tid = scene.tiles[ty][tx]
    if tid not in WALKABLE:
        return False, f"Petak terisi ({TILE_NAMES.get(tid, tid)})."
    return True, None


def place(state, world, tile_id: int, tx: int, ty: int):
    """Beli & taruh objek. Return (sukses, pesan)."""
    price = BUY_PRICES.get(tile_id)
    if price is None:
        return False, "Objek itu tak dijual."
    if state.gold < price:
        return False, f"Uang kurang (butuh {price}G, punya {state.gold}G)."
    ok, why = can_place(state, world, tx, ty)
    if not ok:
        return False, why
    scene = world.scene_obj
    scene.tiles[ty][tx] = tile_id
    _placed(state).setdefault(scene.name, {})[f"{tx},{ty}"] = tile_id
    state.gold -= price
    label = SIMS_OBJECTS.get(tile_id, {}).get('label', 'Objek')
    return True, f"{label} dibeli & dipasang (-{price}G)."


def sell(state, world, tx: int, ty: int):
    """Jual objek YANG PERNAH DIBELI di petak itu. Return (sukses, pesan).

    Objek bawaan scene tak bisa dijual — hanya yang dibeli pemain, supaya
    pemain tak bisa menjual isi rumah yang bukan miliknya.
    """
    scene = getattr(world, 'scene_obj', None)
    if scene is None:
        return False, "Tak ada scene aktif."
    rec = _placed(state).get(scene.name, {})
    key = f"{tx},{ty}"
    if key not in rec:
        return False, "Itu bukan barang yang kamu beli."
    tid = rec.pop(key)
    # Kembalikan petak jadi lantai yang bisa dipijak
    from .config import FL, G
    scene.tiles[ty][tx] = FL if getattr(scene, 'indoor', False) else G
    refund = sell_value(tid)
    state.gold += refund
    label = SIMS_OBJECTS.get(tid, {}).get('label', 'Objek')
    return True, f"{label} dijual (+{refund}G)."
