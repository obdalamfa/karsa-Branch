"""
Preview 4 mob baru dalam satu gambar grid menggunakan Panda3D offscreen render.
Output: screenshots/mob_preview_new.png
"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from panda3d.core import (
    loadPrcFileData, Point3, Vec3, Vec4,
    AmbientLight, DirectionalLight, NodePath,
    GraphicsOutput, GraphicsPipe, FrameBufferProperties,
    WindowProperties, Filename, PNMImage,
    Texture, OrthographicLens, PerspectiveLens,
    AntialiasAttrib
)

loadPrcFileData('', 'load-display pandagl')
loadPrcFileData('', 'window-type offscreen')
loadPrcFileData('', 'win-size 1280 640')
loadPrcFileData('', 'audio-library-name null')
loadPrcFileData('', 'model-path .')

from direct.showbase.ShowBase import ShowBase

MOB_NAMES = ['mob_banaspati', 'mob_tikus_gua', 'mob_leak', 'mob_kuntilanak']
MOB_LABELS = ['Banaspati\n(Roh Api)', 'Tikus Gua', 'Leak\n(Leyak)', 'Kuntilanak']

# Per-mob: (scale, cam_dist, cam_height, cam_pitch)
MOB_CAM = {
    'mob_banaspati':  (1.8, 2.8,  0.7,  -10),
    'mob_tikus_gua':  (2.5, 2.5,  0.4,  -15),
    'mob_leak':       (1.4, 3.0,  1.0,  -10),
    'mob_kuntilanak': (1.0, 3.2,  1.0,   -8),
}


class MobViewer(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.setBackgroundColor(0.08, 0.07, 0.09, 1)  # latar gelap gaya dungeon

        # Lighting
        al = AmbientLight('amb')
        al.setColor((0.35, 0.32, 0.40, 1))
        self.render.setLight(self.render.attachNewNode(al))

        dl = DirectionalLight('dir')
        dl.setColor((0.9, 0.85, 0.75, 1))
        dlnp = self.render.attachNewNode(dl)
        dlnp.setHpr(45, -35, 0)
        self.render.setLight(dlnp)

        dl2 = DirectionalLight('rim')
        dl2.setColor((0.25, 0.30, 0.55, 1))
        dl2np = self.render.attachNewNode(dl2)
        dl2np.setHpr(220, -20, 0)
        self.render.setLight(dl2np)

        self.render.setAntialias(AntialiasAttrib.MMultisample, 4)

        self._load_and_render()

    def _load_and_render(self):
        # Posisi 4 mob berjajar horizontal
        x_positions = [-3.5, -1.1, 1.1, 3.5]

        # Warna material — gaya relic arkeologis (abu-perunggu)
        relic_colors = {
            'mob_banaspati':  (0.80, 0.58, 0.35, 1),
            'mob_tikus_gua':  (0.62, 0.60, 0.57, 1),
            'mob_leak':       (0.67, 0.64, 0.60, 1),
            'mob_kuntilanak': (0.70, 0.72, 0.76, 1),
        }

        target_height = 2.0  # semua mob dinormalisasi ke tinggi 2 unit

        for i, mob_name in enumerate(MOB_NAMES):
            path = f'assets/models/{mob_name}.obj'
            node = self.loader.loadModel(path)
            if not node:
                print(f'GAGAL load: {mob_name}')
                continue

            # Panda3D OBJ loader TIDAK konversi Y-up → Z-up.
            # Model OBJ Y (intended up) = Panda3D Y (forward).
            # Fix: setP(90) → local Y menjadi world Z (up).
            # Hitung bounds SEBELUM rotate, gunakan Y untuk tinggi.
            bounds = node.getTightBounds()
            if bounds:
                lo, hi = bounds
                foot_y  = lo.getY()                      # kaki di Y rendah
                height_y = hi.getY() - lo.getY()         # tinggi sepanjang Y
                scale_factor = target_height / max(height_y, 0.01)
                # Setelah setP(90): local Y → world Z.
                # kaki (foot_y local) menjadi foot_y*scale di world Z.
                # Agar kaki di world Z=0: setPos z = -foot_y * scale
                px = x_positions[i]
                py = 7.0
                pz = -foot_y * scale_factor
            else:
                px, py, pz = x_positions[i], 7.0, 0.0
                scale_factor = 1.0

            node.reparentTo(self.render)
            node.setPos(px, py, pz)
            node.setScale(scale_factor)
            node.setHpr(25, 90, 0)  # H=25° yaw, P=90° pitch: tegakkan model
            node.setColor(*relic_colors.get(mob_name, (0.65, 0.63, 0.60, 1)))

        # Kamera: lihat dari depan, semua model masuk frame
        self.cam.setPos(0, -2.5, 1.8)
        self.cam.lookAt(Point3(0, 7.0, 1.2))

        # Render 3 frame baru terasa stabil
        for _ in range(3):
            self.graphicsEngine.renderFrame()

        # Simpan screenshot
        out_dir = 'screenshots'
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, 'mob_preview_new.png')

        img = PNMImage()
        self.win.getScreenshot(img)
        img.write(Filename.fromOsSpecific(os.path.abspath(out_path)))
        print(f'Saved: {out_path}')

        sys.exit(0)


app = MobViewer()
app.run()
