"""potret.py — Render potret wajah tiap warga dari GLB-nya untuk kotak dialog.

Kotak percakapan ala Harvest Moon butuh wajah si pembicara. Potretnya diambil
dari model yang SAMA dengan yang berjalan di desa (assets/models/actors/*.glb),
jadi seragam, warna kulit, dan rambut di potret selalu cocok dengan sosoknya.

    python tools/potret.py              # semua aktor
    python tools/potret.py npc_sari     # satu

Hasil: assets/textures/potret/<id>.png (256x256, latar transparan).
"""
import os
import sys
from pathlib import Path

from panda3d.core import loadPrcFileData

ROOT = Path(__file__).resolve().parent.parent
ACTORS = ROOT / 'assets' / 'models' / 'actors'
OUT = ROOT / 'assets' / 'textures' / 'potret'

# Sistem koordinat SAMA dengan game (ursina/window.py): tanpa ini topi OBJ
# dimuat tegak ke Z sementara rig GLB tegak ke Y, dan topi terlihat rebah.
loadPrcFileData('', 'coordinate-system y-up-left')
loadPrcFileData('', 'window-type offscreen')
loadPrcFileData('', 'win-size 256 256')
loadPrcFileData('', 'framebuffer-alpha 1')
loadPrcFileData('', 'audio-library-name null')
loadPrcFileData('', 'model-cache-dir')

from direct.showbase.ShowBase import ShowBase              # noqa: E402
from direct.actor.Actor import Actor                       # noqa: E402
from panda3d.core import (AmbientLight, DirectionalLight, Filename,  # noqa: E402
                          LVector3, NodePath, PNMImage, Vec4, AntialiasAttrib)

sys.path.insert(0, str(ROOT))
import game  # noqa: E402  (Assimp untuk OBJ topi)
from game.char_actor import _warnai_material_polos           # noqa: E402


def main(nama):
    base = ShowBase()
    base.win.setClearColor(Vec4(0, 0, 0, 0))
    base.render.setAntialias(AntialiasAttrib.MMultisample)
    amb = AmbientLight('amb'); amb.setColor(Vec4(0.78, 0.76, 0.74, 1))
    sun = DirectionalLight('sun'); sun.setColor(Vec4(0.75, 0.72, 0.66, 1))
    base.render.setLight(base.render.attachNewNode(amb))
    sn = base.render.attachNewNode(sun); sn.setHpr(25, -30, 0)
    base.render.setLight(sn)
    # lampu isi dari depan-bawah: wajah tidak boleh tenggelam di bayangan topi
    isi = DirectionalLight('isi'); isi.setColor(Vec4(0.45, 0.44, 0.42, 1))
    ni = base.render.attachNewNode(isi); ni.setHpr(-160, 10, 0)
    base.render.setLight(ni)
    base.camLens.setFov(22)
    base.camLens.setNear(0.05)       # bawaan 1 m memotong kepala dari jarak potret
    OUT.mkdir(parents=True, exist_ok=True)
    for n in nama:
        p = ACTORS / f'{n}.glb'
        if not p.exists():
            print('LEWAT', n)
            continue
        a = Actor(Filename.fromOsSpecific(str(p)).getFullpath())
        a.reparentTo(base.render)
        _warnai_material_polos(a)
        anim = a.getAnimNames()
        if 'idle' in anim:
            a.pose('idle', 0)
        a.update()
        base.graphicsEngine.renderFrame()   # sendi harus sudah berpose sebelum topi ditempel
        # Wajah chibi, warna kulit suku, dan topi -- sama persis dengan sosok
        # yang berjalan di desa (game/rupa_pemain.py).
        if n == 'player':
            # topi bawaan GLB disembunyikan; topi pemain dipilih di chargen
            from game.rupa_pemain import pasang_aksesori

            class _CP:
                pass
            cp = _CP(); cp.actor = a
            pasang_aksesori(cp, None)
        if n.startswith('npc_'):
            try:
                from game.rupa_pemain import terapkan_npc

                class _CA:
                    pass
                ca = _CA(); ca.actor = a
                terapkan_npc(ca, n[4:])
            except Exception as e:
                print('rupa gagal', n, e)
        # sayap bidadari menutup latar potret dengan bidang putih
        for g in a.findAllMatches('**/sayap*'):
            g.hide()
        kar = a.find('**/+Character')
        sendi = a.exposeJoint(kar.attachNewNode('kepala'), 'modelRoot', 'HEAD')
        base.graphicsEngine.renderFrame()
        kp = sendi.getPos(base.render)
        # glTF Y-atas: tinggi di Y Panda? Ambil sumbu tegak dari kotak batas.
        lo, hi = a.getTightBounds()
        tegak_z = (hi.z - lo.z) >= (hi.y - lo.y)
        if tegak_z:
            pusat = LVector3(kp.x, kp.y, kp.z + 0.09)
            base.cam.setPos(pusat + LVector3(0.2, -1.0, 0.04))
        else:
            pusat = LVector3(kp.x, kp.y + 0.09, kp.z)
            base.cam.setPos(pusat + LVector3(0.2, 0.04, -1.0))
        base.cam.lookAt(pusat)
        for _ in range(2):
            base.graphicsEngine.renderFrame()
        img = PNMImage()
        base.win.getScreenshot(img)
        img.write(Filename.fromOsSpecific(str(OUT / f'{n[4:] if n.startswith("npc_") else n}.png')))
        print('POTRET', n)
        a.cleanup(); a.removeNode()
    base.destroy()


if __name__ == '__main__':
    daftar = sys.argv[1:] or sorted(p.stem for p in ACTORS.glob('*.glb'))
    main(daftar)
