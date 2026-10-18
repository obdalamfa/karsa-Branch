"""bayangan.py — Menempelkan bayangan kontak ke PERMUKAAN TANAH.

Kenapa ini butuh modul sendiri, padahal isinya satu fungsi: menaruh quad
bayangan pada ketinggian yang benar ternyata tidak bisa dilakukan dengan
menulis angka di konstruktor, dan dua cara yang tampak benar keduanya salah.

Terukur, permukaan rumput ada di `GROUND_H + 0,04 = 0,24`:

  * Bayangan warga dipasang di y LOKAL 0,02 mendarat di y dunia 0,0137 —
    terkubur 23 cm di bawah tanah. Yang terlihat cuma serpihan di tempat
    tanahnya kebetulan cekung: 149 piksel dari frame 900x900.
  * Bayangan pemain dipasang dengan angka yang sama mendarat di y dunia
    0,92 — MELAYANG 68 cm di atas rumput, cakram gelap setinggi lutut. Ia
    sudah begitu sejak lama.

Dua sebabnya berbeda dan keduanya tidak terlihat dari kode di tempatnya:
node actor warga BERSKALA (manekin dikecilkan 2,35/3,42 = 0,687), jadi
0,245 lokal jadi 0,168 dunia; sedangkan pemain punya titik asal di y 0,90.

Dan `Entity.world_y = ...` milik Ursina tidak menolong — ia menulis ke y
LOKAL, jadi bayangan pemain justru naik ke 1,145. Yang dipakai di sini
transform Panda3D langsung (`set_pos(render, ...)`), yang memang menghitung
skala dan induk.
"""
from ursina import Vec3

from .config import GROUND_H

# Sedikit di atas tutup rumput (GROUND_H + 0,04) supaya tidak berkedip
# melawannya (z-fighting).
TINGGI_TANAH = GROUND_H + 0.045


def pin_ke_tanah(bayangan) -> None:
    """Kunci ketinggian `bayangan` ke permukaan tanah, x dan z tidak diubah."""
    if bayangan is None:
        return
    try:
        from direct.showbase.ShowBaseGlobal import base
        # setPos/getPos NodePath MENTAH, bukan set_position/get_position milik
        # Ursina: yang terakhir punya tanda tangan sendiri dan tidak menerima
        # node acuan, jadi memanggilnya dengan (render, Vec3) diam-diam
        # mendaratkan bayangan di tempat lain — terukur 0,0407 dan bukan 0,245.
        w = bayangan.getPos(base.render)
        bayangan.setPos(base.render, w[0], TINGGI_TANAH, w[2])
    except Exception:
        pass


# ─── Cakram bayangan kontak ──────────────────────────────────────────────
# Dulu bayangan pemain dan warga berupa QUAD PERSEGI ber-alpha rata 120:
# di tangkapan farm_wide ia terbaca sebagai ubin hitam bertepi keras di bawah
# kaki, bukan bayangan. Penjaga gua (guardian_models._contact_shadow) sudah
# memakai cakram yang memudar ke tepi; resepnya ditarik ke sini supaya
# pemain, warga, dan benda statis memakai satu bentuk.
#
# Profil alpha (jari-jari dinormalkan 0..1): inti pekat lalu memudar ke nol di
# tepi. Dua cincin tengah membuat pudarnya melengkung, bukan kerucut lurus.
_PROFIL = ((0.0, 1.0), (0.55, 0.92), (0.80, 0.50), (1.0, 0.0))
_SEGMEN = 28


def _titik_superelips(t, n):
    """Arah satuan pada superelips berpangkat `n` (2 = lingkaran, 4 = kotak
    bersudut bulat) di sudut `t`."""
    import math
    c, s = math.cos(t), math.sin(t)
    e = 2.0 / n
    return (math.copysign(abs(c) ** e, c), math.copysign(abs(s) ** e, s))


def _tambah_cakram(v, cl, tri, cx, cy, cz, rx, rz, alpha, warna, pangkat=2.0,
                   inti=None):
    """Tambahkan satu cakram berbulu ke daftar vertex/warna/segitiga.

    `inti` (hx, hz) opsional: setengah ukuran bidang pekat di tengah. Dipakai
    rok bangunan supaya bagian di bawah dinding tetap pekat penuh dan cuma
    tepi luarnya yang memudar.
    """
    import math
    r, g, b = warna
    pusat = len(v)
    v.append((cx, cy, cz))
    cl.append((r, g, b, alpha))
    cincin = []
    for jr, ja in _PROFIL[1:]:
        awal = len(v)
        for j in range(_SEGMEN):
            ux, uz = _titik_superelips(j * math.tau / _SEGMEN, pangkat)
            if inti is not None:
                # Cincin pertama menempel di tepi inti; berikutnya melebar
                # menuju tepi luar (rx, rz).
                f = (jr - _PROFIL[1][0]) / (1.0 - _PROFIL[1][0])
                ex = inti[0] + (rx - inti[0]) * f
                ez = inti[1] + (rz - inti[1]) * f
            else:
                ex, ez = rx * jr, rz * jr
            v.append((cx + ux * ex, cy, cz + uz * ez))
            cl.append((r, g, b, alpha * ja))
        cincin.append(awal)
    a0 = cincin[0]
    for j in range(_SEGMEN):
        k = (j + 1) % _SEGMEN
        tri.append((pusat, a0 + k, a0 + j))
    for a, b_ in zip(cincin, cincin[1:]):
        for j in range(_SEGMEN):
            k = (j + 1) % _SEGMEN
            tri.append((a + j, a + k, b_ + k))
            tri.append((a + j, b_ + k, b_ + j))


def _entity_cakram(parent, verts, cols, tris, **kw):
    """Entity tak-bercahaya untuk mesh cakram. Mesh BARU per panggilan
    (aturan #3 CLAUDE.md: Mesh Ursina tidak boleh dibagi antar-Entity)."""
    from ursina import Entity, Mesh, color
    from panda3d.core import TransparencyAttrib
    e = Entity(parent=parent, model=Mesh(vertices=verts, triangles=tris,
                                         colors=cols, static=True),
               color=color.white, shader=None, double_sided=True, **kw)
    # JANGAN biarkan shader=None di pipeline GL. Tanpa shader, cakram
    # digambar fixed-function tanpa TextureAttrib dan mencicip tekstur yang
    # terakhir terikat: di tangkapan capture.py kaki pemain berdiri di lajur
    # papan kayu dan pangkal pohon jadi kotak rumput hijau (terukur +14
    # per kanal; _bench/probes/probe_cakram_capture.py). unlit_shader Ursina
    # mengalikan warna vertex dengan tekstur putih bawaan Panda. D3D9 tidak
    # punya GLSL: di sana teksturnya dimatikan eksplisit.
    try:
        from .smooth_shader import _is_opengl_pipeline
        gl = _is_opengl_pipeline()
    except Exception:
        gl = False
    if gl:
        from ursina.shaders import unlit_shader
        e.shader = unlit_shader
    else:
        e.setTextureOff(1)
    e.setTransparency(TransparencyAttrib.M_alpha)
    # Tidak menulis kedalaman: cakram yang bertumpuk (pohon berdempetan)
    # saling menggelapkan, bukan saling memotong dengan tepi tajam.
    e.setDepthWrite(False)
    e.setLightOff()
    sembunyikan_dari_kamera_bayangan(e)
    return e


# Bit kamera yang dipakai kamera bayangan matahari (app._pasang_shadow_map).
# Benda yang disembunyikan dari bit ini tidak menjatuhkan bayangan di
# shadow map -- cakram kontak tidak boleh ikut menjadi kaster.
BIT_KAMERA_BAYANGAN = 1 << 3


def sembunyikan_dari_kamera_bayangan(np_):
    try:
        from panda3d.core import BitMask32
        np_.hide(BitMask32(BIT_KAMERA_BAYANGAN))
    except Exception:
        pass


def cakram_kontak(parent, lebar, dalam, alpha=0.47, **kw):
    """Cakram bayangan kontak berbulu, bidang XZ lokal di y=0, jari-jari
    lebar/2 x dalam/2. Tetap dikunci ke tanah oleh pemanggil (pin_ke_tanah)."""
    v, cl, tri = [], [], []
    _tambah_cakram(v, cl, tri, 0.0, 0.0, 0.0, lebar / 2, dalam / 2, alpha,
                   (0.02, 0.03, 0.06))
    return _entity_cakram(parent, v, cl, tri, **kw)


def bangun_bayangan_statis(world):
    """Satu mesh cakram/rok bayangan di kaki semua benda statis berdiri.

    Pohon, tiang, pagar, lentera, rumah: dulu tidak satu pun punya bayangan,
    jadi semuanya terbaca seperti ditempel di atas rumput. SATU Entity untuk
    seluruh scene (bukan satu per benda): farm punya ratusan benda, dan tiap
    Entity adalah draw call plus kunjungan loop update Ursina.

    Benda dikumpulkan per UBIN pusatnya, supaya batang dan tajuk pohon (dua
    Entity terpisah) memberi satu bayangan selebar tajuk. Cuma kelompok yang
    punya anggota menapak tanah yang diberi bayangan -- lampion gantung dan
    awan tidak. Dinding (`_wall_ents`) dilewati: ia ikut cutaway kamera,
    bayangannya tidak.

    Dipanggil SEBELUM `_satukan_ubin()` (yang menyembunyikan ubin), dan
    hasilnya masuk `_obj_ents` supaya `_clear()` menghancurkannya.
    """
    from direct.showbase.ShowBaseGlobal import base
    from ursina import scene
    from .config import TILE_SIZE as TS

    dinding = {id(r[0]) for r in getattr(world, '_wall_ents', [])}
    kelompok = {}
    for e in list(getattr(world, '_obj_ents', [])) + list(getattr(world, '_tile_ents', [])):
        if id(e) in dinding or not getattr(e, 'enabled', True):
            continue
        if getattr(e, 'model', None) is None:
            continue
        try:
            if e.is_hidden():
                continue
            b = e.getTightBounds(base.render)
        except Exception:
            continue
        if not b:
            continue
        lo, hi = b
        tinggi = hi[1] - lo[1]
        lx, lz = hi[0] - lo[0], hi[2] - lo[2]
        # Ubin tanah (tinggi <= 0,25) dan bidang raksasa (horizon) bukan benda.
        if tinggi < 0.30 or max(lx, lz) > TS * 6:
            continue
        cx, cz = (lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2
        kunci = (int(round(cx / TS)), int(round(cz / TS)))
        menapak = lo[1] <= GROUND_H + 0.30
        kelompok.setdefault(kunci, []).append((lo, hi, menapak))

    v, cl, tri = [], [], []
    n = 0
    for (tx, ty), isi in kelompok.items():
        tapak = [(lo, hi) for lo, hi, m in isi if m]
        if not tapak:
            continue
        # Tapak = gabungan benda yang menapak; tajuk = gabungan semuanya.
        x0 = min(lo[0] for lo, _ in tapak); x1 = max(hi[0] for _, hi in tapak)
        z0 = min(lo[2] for lo, _ in tapak); z1 = max(hi[2] for _, hi in tapak)
        X0 = min(lo[0] for lo, _, _ in isi); X1 = max(hi[0] for _, hi, _ in isi)
        Z0 = min(lo[2] for lo, _, _ in isi); Z1 = max(hi[2] for _, hi, _ in isi)
        hx, hz = (x1 - x0) / 2, (z1 - z0) / 2
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        y = TINGGI_TANAH + world.get_surface_height(tx, ty)
        if max(hx, hz) >= TS * 0.6:
            # Bangunan dan perabot lebar: ROK -- inti pekat persis di bawah
            # tapak, memudar 0,45 ke luar. Superelips pangkat 5: kotak
            # bersudut bulat, mengikuti dinding, bukan oval di bawah rumah.
            _tambah_cakram(v, cl, tri, cx, y, cz, hx + 0.45, hz + 0.45, 0.42,
                           (0.02, 0.03, 0.06), pangkat=5.0, inti=(hx, hz))
        else:
            # Batang, tiang, lentera: cakram selebar 70% tajuk (atau tapak
            # ditambah tepi kalau tajuknya tidak lebih lebar).
            rx = max(hx + 0.22, (X1 - X0) / 2 * 0.70)
            rz = max(hz + 0.22, (Z1 - Z0) / 2 * 0.70)
            _tambah_cakram(v, cl, tri, cx, y, cz, rx, rz, 0.40,
                           (0.02, 0.03, 0.06))
        n += 1
    if not n:
        return None
    e = _entity_cakram(scene, v, cl, tri)
    e.jumlah_cakram = n
    return e
