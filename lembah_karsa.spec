# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec — Lembah Karsa 3D (ROADMAP M7).

Build (dari root repo, venv dengan dependensi terpasang):
    pip install pyinstaller
    pyinstaller lembah_karsa.spec --noconfirm

Hasil: dist/LembahKarsa3D/  (onedir) — kirim seluruh folder ini ke pemain.
Mode onedir dipilih (bukan onefile) karena:
  - Path model game memakai assets/ relatif paket game/ → struktur folder
    harus utuh berdampingan (game/ dan assets/ di _internal/).
  - Boot jauh lebih cepat (tak ekstrak ulang ke temp tiap run).

Catatan: panda3d & ursina membawa data (shader/model/tekstur internal).
collect_all menyertakannya. Bila build error soal panda3d, pastikan versi
PyInstaller terbaru (hook panda3d sudah bawaan sejak PyInstaller 5).
"""
from PyInstaller.utils.hooks import collect_all, collect_data_files

datas = [
    ('assets', 'assets'),   # models, fonts, textures, sounds, audio, ui, vitaboy
]
binaries = []
hiddenimports = ['pygame', 'pygame.mixer']

# Sertakan data + submodul ursina, panda3d, direct (shader/model/tekstur internal)
for pkg in ('ursina', 'panda3d', 'direct'):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Kecualikan tool dev (Blender/render/build scripts) supaya bundel ramping.
    excludes=['matplotlib', 'tkinter', 'PIL.ImageQt', 'numpy.testing'],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LembahKarsa3D',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,                       # GUI app: tanpa jendela konsol
    disable_windowed_traceback=False,
    icon='assets/ui/icon.ico' if __import__('os').path.exists('assets/ui/icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LembahKarsa3D',
)
