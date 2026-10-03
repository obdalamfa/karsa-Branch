"""Kontroler gameplay: waktu, quest, dan interaksi.

Paket ini sebelumnya tidak punya `__init__.py`. Ia berjalan di Python 3.14
sebagai namespace package implisit, tapi itu tidak dijamin di semua perkakas:
PyInstaller dan gaya `setup.py`/`find_packages()` melewatkan paket tanpa
`__init__.py`, dan game hasil build akan kehilangan seluruh modul di sini.
"""
