import sys
import os
import logging

# On Windows, ensure thread is attached to the interactive 'Default' desktop
# so window renders directly onto the user screen when launched
if sys.platform == 'win32':
    try:
        import ctypes
        user32 = ctypes.windll.user32
        hdesk_default = user32.OpenDesktopW('Default', 0, False, 0x01FF)
        if hdesk_default:
            user32.SetThreadDesktop(hdesk_default)
    except Exception as e:
        pass

# Paksa OpenGL pipeline SEBELUM Ursina/Panda3D di-import — Direct3D9 tidak
# support GLSL shader yang dipakai smooth_shader / grass_shader / sky.
# `gl-version` tidak dipaksa supaya driver lawas tetap kompatibel.
from panda3d.core import loadPrcFileData
loadPrcFileData('', 'load-display pandagl')
loadPrcFileData('', 'aux-display pandadx9')

from game.app import run

# Setup logging dasar
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    logging.info("Memulai Lembah Karsa 3D...")
    
    # Pastikan folder assets ada sebelum menjalankan game
    assets_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
    if not os.path.exists(assets_path):
        logging.warning("Folder assets tidak ditemukan. Menjalankan make_assets.py...")
        import make_assets
        make_assets.main()

    try:
        run()
    except Exception as e:
        logging.error(f"Game crash! Terjadi kesalahan fatal: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
