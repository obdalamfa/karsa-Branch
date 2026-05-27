import sys
import os
import logging

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
