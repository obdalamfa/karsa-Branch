"""karsa_scene.py — Jembatan ke format scene game Lembah Karsa.

Editor ini lahir sebagai editor Ursina generik: ia memanipulasi daftar entity
bebas (posisi, rotasi, skala). Game Lembah Karsa TIDAK bekerja begitu -- dunianya
adalah grid ubin yang dirender `world.py`, dan pathfinder membaca grid itu, bukan
entity. Dua model ini tidak bisa disatukan begitu saja; menyamakannya adalah
pekerjaan tersendiri (lapisan objek terpasang, Fase 5).

Modul ini adalah jembatan tingkat DATA: membaca dan menulis scene game memakai
implementasi format milik game itu sendiri (`game.scenes.scene_io`).

Kenapa memakai implementasi game, bukan menulis ulang di sini: kalau editor
punya pembaca dan penulis sendiri, dua implementasi itu akan berbeda diam-diam,
dan perbedaannya muncul sebagai diff raksasa di berkas scene setiap kali editor
menyimpan -- padahal isinya tidak berubah. Satu implementasi, dipakai dua alat.

Modul ini sengaja TIDAK mengimpor ursina, sehingga bisa diuji tanpa membuka
jendela. Konversi grid ubin menjadi entity yang bisa diklik di viewport adalah
pekerjaan terpisah dan tinggal di modul lain.
"""
import sys
from pathlib import Path

# Editor bisa dijalankan dari mana saja (`python -m ursina_editor.main`), jadi
# akar repo dicari dari letak berkas ini, bukan dari CWD.
_DIR_EDITOR = Path(__file__).resolve().parent
_ROOT_REPO = _DIR_EDITOR.parent
if str(_ROOT_REPO) not in sys.path:
    sys.path.insert(0, str(_ROOT_REPO))

from game.scenes import SCENE_BUILDERS, SCENES          # noqa: E402
from game.scenes.scene_io import baca_scene, tulis_scene  # noqa: E402

DIR_SCENE = _ROOT_REPO / 'game' / 'scenes'


def jalur(nama: str) -> Path:
    """Berkas data sebuah scene game."""
    return DIR_SCENE / f'{nama}.json'


def scene_tersedia() -> list:
    """Nama semua scene game, terurut.

    Diambil dari `SCENE_BUILDERS`, bukan `SCENES`: kamus itu berisi seluruh
    scene yang bisa dibangun KODE, jadi scene yang berkas datanya belum ada pun
    tetap muncul dan tetap bisa disunting.
    """
    return sorted(SCENE_BUILDERS)


def muat(nama: str):
    """Muat scene game sebagai objek `Scene` milik game.

    Membaca berkas datanya; kalau berkasnya tidak ada, jatuh ke versi kode --
    sama persis dengan yang dilakukan game saat dijalankan, supaya yang
    disunting editor adalah peta yang benar-benar dipakai pemain.

    Mengembalikan `(scene, sumber)` dengan sumber 'data' atau 'kode'.
    """
    if nama not in SCENE_BUILDERS:
        raise KeyError(f"scene '{nama}' tidak dikenal; "
                       f"yang ada: {', '.join(scene_tersedia())}")
    p = jalur(nama)
    if p.exists():
        return baca_scene(p), 'data'
    return SCENE_BUILDERS[nama](), 'kode'


def simpan(scene, nama: str = None) -> Path:
    """Tulis scene kembali ke berkas data game.

    Ini SATU-SATUNYA tempat editor menulis berkas scene, dan game tidak pernah
    memanggilnya -- game hanya membaca.
    """
    nama = nama or scene.name
    p = jalur(nama)
    tulis_scene(scene, p)
    return p


def ringkas(scene) -> dict:
    """Ringkasan scene untuk ditampilkan di UI editor."""
    sebaran = {}
    for baris in scene.tiles:
        for tid in baris:
            sebaran[tid] = sebaran.get(tid, 0) + 1
    return {
        'nama': scene.name,
        'judul': scene.display,
        'ukuran': (scene.w, scene.h),
        'ubin': scene.w * scene.h,
        'jenis_ubin': len(sebaran),
        'zona': len(scene.paint),
        'portal': len(scene.portals),
        'indoor': scene.indoor,
        'builder': scene.builder_name,
    }
