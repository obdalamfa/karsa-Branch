"""bayangan_matahari.py — Shadow map Panda3D pada DirectionalLight `Game3D.sun`.

Sebelum modul ini tidak ada satu pun bayangan jatuhan di game: lampu dibuat
`DirectionalLight(shadows=False)`, `pl.shadows = True` di lampu dalam ruang
tidak berbuat apa-apa (PointLight Ursina tidak punya setter itu), dan tidak
ada shader yang membaca shadowMap. probe_cahaya mengukur tanah "teduh lawan
terbuka" 1,00 di mana pun -- tidak ada tempat teduh sama sekali.

Yang dikerjakan di sini, dan alasannya:

  * LENSA DISETEL SENDIRI. `DirectionalLight.shadows = True` milik Ursina
    memanggil `update_bounds(scene)`, yang mengukur SELURUH scene termasuk
    kubah langit r=500 dan quad horizon 1000 -- film ~1000 m di peta 1024
    texel = ~1 m per texel, bayangan jadi gumpalan. `look_at` Ursina pada
    lampu juga memanggilnya, jadi arah matahari diubah lewat
    `Entity.look_at` (game/cahaya.py).
  * Film persegi FILM m mengikuti pemain, posisinya DISNAP ke kisi texel di
    ruang lampu. Tanpa snap, tiap langkah pemain menggeser kisi sampling dan
    tepi bayangan berkedip ("berenang").
  * Kamera bayangan hanya melihat bit BIT_KAMERA_BAYANGAN. Langit, awan,
    hujan, ubin tanah (cukup jadi penerima), rumput, sebaran, air, dan
    cakram kontak disembunyikan dari bit itu: mereka tidak menjatuhkan
    bayangan yang berarti dan cuma memakan waktu render.
  * Initial state kamera bayangan memakai shader kedalaman sepele dengan
    override, supaya fragmen smooth_shader (cel, hemisfer, bahu sorot, PCF)
    tidak dijalankan untuk peta yang cuma butuh kedalaman.
  * Di dalam ruang caster dimatikan; fragmen tetap mencicip peta dummy Panda
    dan mendapat s = 1 (dibuktikan probe Panda murni sebelum dipasang).
  * Pass bayangan digambar tiap SELANG (2) frame lewat task sendiri, dan
    PCF-nya satu tap perangkat keras (lihat smooth_shader).
  * Saklar: MATI bawaan karena melewati anggaran ms/frame (angka di
    diminta()). KARSA_SHADOW=1 menyalakan; KARSA_NO_SHADOW=1 selalu
    mematikan. Dalam keadaan mati, blok shadow di fragmen tidak dikompilasi
    sama sekali, jadi ongkosnya nol. Pipeline non-GL (D3D9) tidak pernah
    menyalakannya: smooth_shader memang tidak dipakai di sana.
"""
from __future__ import annotations

import os

from .bayangan import BIT_KAMERA_BAYANGAN

RESOLUSI = 1024
FILM = 36.0       # meter, sisi film ortografis
JARAK = 60.0      # meter, mundur sepanjang arah sinar dari titik fokus
DEKAT, JAUH = 1.0, 130.0
SEL = 10.0        # meter, sel peleburan proksi kaster
SELANG = int(os.environ.get('KARSA_SHADOW_SELANG', '2') or 2)
                  # peta digambar ulang tiap SELANG frame (lihat ikuti())

_DEPTH_VERT = """
#version 140
uniform mat4 p3d_ModelViewProjectionMatrix;
in vec4 p3d_Vertex;
void main() { gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex; }
"""
_DEPTH_FRAG = """
#version 140
out vec4 o;
void main() { o = vec4(1.0); }
"""


def diminta() -> bool:
    """Apakah shadow map dinyalakan menurut saklar lingkungan.

    MATI bawaan; KARSA_SHADOW=1 menyalakan, KARSA_NO_SHADOW=1 selalu menang.
    Alasannya angka: regress.py farm A/B berurutan (mesin sesi, llvmpipe)
    memberi ms/frame 75,7/86,5/63,4 tanpa lawan 139,4/105,5/102,3 dengan
    shadow map -- +22..84%, melewati anggaran +25% walau pass bayangan sudah
    digambar tiap dua frame, kaster statis dilebur per sel, dan PCF tinggal
    satu tap perangkat keras."""
    if os.environ.get('KARSA_NO_SHADOW'):
        return False
    return bool(os.environ.get('KARSA_SHADOW'))


def _lampu_np(game):
    sun = getattr(game, 'sun', None)
    if sun is None:
        return None
    try:
        return sun.getChildren()[0]
    except Exception:
        return None


def pasang(game) -> bool:
    """Siapkan shadow map (sekali, saat boot). True kalau aktif."""
    game._bayangan_aktif = False
    if not diminta() or not getattr(game, '_use_unlit_sh', False):
        return False
    lnp = _lampu_np(game)
    if lnp is None:
        return False
    try:
        from panda3d.core import (BitMask32, OrthographicLens, RenderState,
                                  ShaderAttrib, Shader as PShader)
        node = lnp.node()
        lensa = OrthographicLens()
        lensa.setFilmSize(FILM, FILM)
        lensa.setNearFar(DEKAT, JAUH)
        node.setLens(lensa)
        node.setCameraMask(BitMask32(BIT_KAMERA_BAYANGAN))
        sh = PShader.make(PShader.SL_GLSL, _DEPTH_VERT, _DEPTH_FRAG)
        node.setInitialState(RenderState.make(ShaderAttrib.make(sh), 1000))
        # Matahari dulu di p3d_LightSource[0], bukan PointLight dalam ruang.
        node.setPriority(100)
        node.setShadowCaster(True, RESOLUSI, RESOLUSI)
        # Kamera utama berhenti melihat bit kamera bayangan. Benda biasa
        # tetap terlihat (bit lain masih terbuka), tapi proksi kaster yang
        # HANYA dibuka untuk bit itu (_bangun_proksi) jadi tak terlihat.
        from direct.showbase.ShowBaseGlobal import base
        m = base.cam.node().getCameraMask()
        base.cam.node().setCameraMask(m & ~BitMask32(BIT_KAMERA_BAYANGAN))
        # Kubah langit, awan, dan hujan milik app, bukan world: sekali saja.
        for e in [getattr(game, 'sky', None)] + list(getattr(game, 'clouds', [])) \
                + list(getattr(game, 'rain_drops', [])):
            _sembunyikan(e)
        sky = getattr(game, 'sky', None)
        for nama in ('_sphere', '_sun', '_bulan', '_moon'):
            _sembunyikan(getattr(sky, nama, None))
    except Exception as ex:
        print(f'[bayangan] shadow map gagal dipasang: {ex}')
        return False
    game._bayangan_aktif = True
    game._bayangan_snap = None
    game._bayangan_gambar = True
    if SELANG > 1:
        try:
            from direct.showbase.ShowBaseGlobal import base
            # Task sendiri, bukan bagian update(): sort -50 jalan sebelum
            # task 'update' Ursina (sort 0) di frame yang sama, dan tetap jalan
            # saat 'update' dicabut (_TanpaUpdate di regress, probe). Diukur:
            # waktu saklar ini ada di update(), probe yang mencabut update
            # membekukan buffer dalam keadaan MATI, dan kubus yang dipasang
            # sesudahnya tidak berbayang sama sekali (pelat buka/teduh 1,0).
            base.taskMgr.add(lambda t: _selang(game, t), 'bayangan_selang',
                             sort=-50)
        except Exception:
            pass
    return True


def _selang(game, task):
    """Pass bayangan cuma digambar tiap SELANG frame.

    Di llvmpipe ongkos pass ini per draw call dan per frame, bukan per piksel
    (resolusi 512 sama lambatnya dengan 1024); separuh frame berarti separuh
    ongkos. Bayangan benda bergerak tertinggal satu frame paling banyak."""
    try:
        from direct.showbase.ShowBaseGlobal import base
        lnp = _lampu_np(game)
        buf = lnp.node().getShadowBuffer(base.win.getGsg()) if lnp is not None else None
        game._bayangan_frame = getattr(game, '_bayangan_frame', -1) + 1
        gambar = game._bayangan_frame % SELANG == 0
        game._bayangan_gambar = gambar
        if buf is not None:
            buf.setActive(gambar)
    except Exception:
        game._bayangan_gambar = True
    return task.cont


def _sembunyikan(np_):
    if np_ is None:
        return
    try:
        from panda3d.core import BitMask32
        np_.hide(BitMask32(BIT_KAMERA_BAYANGAN))
    except Exception:
        pass


def atur_scene(game, indoor: bool) -> None:
    """Dipanggil tiap scene dimuat (`_init_env`): caster hidup/mati, dan
    benda bukan-kaster scene baru disembunyikan dari kamera bayangan."""
    if not getattr(game, '_bayangan_aktif', False):
        return
    lnp = _lampu_np(game)
    if lnp is None:
        return
    nyala = not indoor
    try:
        node = lnp.node()
        if node.isShadowCaster() != nyala:
            if nyala:
                node.setShadowCaster(True, RESOLUSI, RESOLUSI)
            else:
                node.setShadowCaster(False)
    except Exception:
        pass
    w = getattr(game, 'world', None)
    if w is None:
        return
    for daftar in (getattr(w, '_tile_ents', []), getattr(w, '_grass_ents', []),
                   getattr(w, '_water_ents', []), getattr(w, '_sebaran_ents', [])):
        for e in daftar:
            _sembunyikan(e)
    for e in getattr(w, '_soil_ents', {}).values():
        _sembunyikan(e)
    for ents in getattr(w, '_crop_ents', {}).values():
        for e in (ents if isinstance(ents, (list, tuple)) else [ents]):
            _sembunyikan(e)
    _sembunyikan(getattr(w, '_ubin_statis', None))
    _sembunyikan(getattr(w, '_bayangan_statis', None))
    _bangun_proksi(game, w, nyala)
    game._bayangan_snap = None


def _bangun_proksi(game, w, nyala):
    """Satu salinan lebur benda statis, HANYA untuk kamera bayangan.

    Terukur di farm (llvmpipe, mesin sesi): 831 GeomNode menjatuhkan
    bayangan dan pass bayangan menambah ~30-50 ms/frame -- ongkosnya per
    draw call, bukan per piksel (resolusi 512 dan PCF satu tap sama
    lambatnya). Untuk kamera bayangan cuma bentuk yang penting, jadi
    salinan geometri `_obj_ents` dilucuti state-nya dan dilebur
    `flattenStrong()` jadi segelintir Geom; aslinya disembunyikan dari bit
    kamera bayangan. Dinding (`_wall_ents`) dilewati karena ikut cutaway.
    Tanaman (`_crop_ents`) tidak menjatuhkan bayangan sama sekali: kecil,
    berubah tiap panen, dan cakram/bayangan pohon sudah membawa ladang.
    """
    lama = getattr(game, '_bayangan_proksi', None)
    if lama is not None:
        lama.removeNode()
    game._bayangan_proksi = None
    if not nyala:
        return
    try:
        from direct.showbase.ShowBaseGlobal import base
        from panda3d.core import BitMask32, RenderState
        bit = BitMask32(BIT_KAMERA_BAYANGAN)
        dinding = {id(r[0]) for r in getattr(w, '_wall_ents', [])}
        akar = base.render.attachNewNode('kaster_statis')
        # Dilebur PER SEL, bukan satu node: satu node selebar peta tidak
        # pernah lolos frustum culling, jadi seluruh geometri (farm: 144 ribu
        # vertex) digambar tiap frame walau film cuma 36 m. Per sel 10 m,
        # yang di luar film dibuang kamera bayangan.
        sel = {}
        n = 0
        for e in getattr(w, '_obj_ents', []):
            if id(e) in dinding or e is getattr(w, '_bayangan_statis', None):
                continue
            try:
                if not e.enabled or e.is_hidden():
                    continue
            except Exception:
                continue
            for gnp in e.findAllMatches('**/+GeomNode'):
                p = gnp.getPos(base.render)
                k = (int(p[0] // SEL), int(p[2] // SEL))
                if k not in sel:
                    sel[k] = akar.attachNewNode(f'sel_{k[0]}_{k[1]}')
                c = gnp.copyTo(sel[k])
                c.setState(RenderState.makeEmpty())
                c.setMat(gnp.getMat(base.render))
                n += 1
            _sembunyikan(e)
        for simpul in sel.values():
            simpul.flattenStrong()
        # Buka hanya untuk bit kamera bayangan.
        akar.hide(BitMask32.allOn() & ~bit)
        akar.show(bit)
        game._bayangan_proksi = akar
        game._bayangan_proksi_n = n
    except Exception as ex:
        print(f'[bayangan] proksi kaster gagal: {ex}')


def ikuti(game, fokus=None) -> None:
    """Geser lampu supaya film berpusat di `fokus` (bawaan: pemain), disnap
    ke kisi texel di ruang lampu. Murah: dua transformasi vektor."""
    if not getattr(game, '_bayangan_aktif', False):
        return
    lnp = _lampu_np(game)
    if lnp is None:
        return
    try:
        from direct.showbase.ShowBaseGlobal import base
        from panda3d.core import LVector3
        # Lensa HANYA digeser di frame yang menggambar peta (_selang):
        # menggeser lensa sementara petanya basi membuat bayangan meloncat
        # satu frame lalu kembali.
        if not getattr(game, '_bayangan_gambar', True):
            return
        if fokus is None:
            fokus = game.player.world_position
        # Koordinat fokus di ruang ROTASI lampu (tanpa translasi), supaya kisi
        # snap mutlak dan tidak ikut bergeser bersama lampu.
        f = lnp.getRelativeVector(base.render, LVector3(fokus[0], fokus[1], fokus[2]))
        kanan, atas, maju = LVector3.right(), LVector3.up(), LVector3.forward()
        texel = FILM / RESOLUSI
        x = round(f.dot(kanan) / texel) * texel
        y = round(f.dot(atas) / texel) * texel
        z = f.dot(maju) - JARAK
        kunci = (x, y, round(z, 1))
        if kunci == getattr(game, '_bayangan_snap', None):
            return
        game._bayangan_snap = kunci
        lokal = kanan * x + atas * y + maju * z
        dunia = base.render.getRelativeVector(lnp, lokal)
        # Yang dipindah Entity matahari (induk lampu); rotasinya tidak disentuh.
        game.sun.setPos(base.render, dunia)
    except Exception:
        pass
