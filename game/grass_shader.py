"""
grass_shader.py — Animasi rumput melambai angin.
Diadaptasi dari FreeSO GrassShader.fx (teknik DrawBlades + wind sway).

FreeSO pola:
  - Posisi tiap vertex di-offset berdasarkan sin(worldPos.x + Time * speed)
  - Hanya vertex bagian atas yang bergerak (h = max(0, pos.y - ground))
  - Dua frekuensi sinus digabung agar terlihat natural

Ursina: shader GLSL, uniform `time` di-update tiap frame dari app.py.
"""
from ursina import Shader

_GRASS_VERT = """
#version 140
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelMatrix;
uniform mat4 p3d_TextureMatrix;
in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;
uniform float grs_time;
uniform float grs_wind;
out vec2 uv;

void main() {
    vec4 world = p3d_ModelMatrix * p3d_Vertex;

    // Sway hanya pada bagian atas tile (y > permukaan tanah ~0.2)
    float h = max(0.0, world.y - 0.15);

    // Dua gelombang sinus (frekuensi beda) → gerakan alami (FreeSO blade pattern)
    float wave1 = sin(world.x * 0.55 + grs_time * 2.2) *
                  cos(world.z * 0.45 + grs_time * 1.7);
    float wave2 = sin(world.x * 0.90 + grs_time * 3.1 + 1.0) * 0.35;

    vec4 pos = p3d_Vertex;
    pos.x += (wave1 + wave2) * h * grs_wind;
    pos.z += cos(world.x * 0.38 + grs_time * 1.4) * h * grs_wind * 0.5;

    gl_Position = p3d_ModelViewProjectionMatrix * pos;
    uv = p3d_MultiTexCoord0;
}
"""

_GRASS_FRAG = """
#version 140
uniform sampler2D p3d_Texture0;
in vec2 uv;
out vec4 fragColor;
void main() {
    fragColor = texture(p3d_Texture0, uv);
}
"""

_grass_shader = None
_grass_failed = False
_grass_pipeline_checked = False


def _is_opengl_pipeline() -> bool:
    try:
        from direct.showbase.ShowBaseGlobal import base
        return 'gl' in base.pipe.get_type().get_name().lower()
    except Exception:
        return True


def get_grass_shader():
    global _grass_shader, _grass_failed, _grass_pipeline_checked
    if _grass_failed:
        return None
    if not _grass_pipeline_checked:
        _grass_pipeline_checked = True
        if not _is_opengl_pipeline():
            _grass_failed = True
            return None
    if _grass_shader is None:
        try:
            _grass_shader = Shader(vertex=_GRASS_VERT, fragment=_GRASS_FRAG,
                                   language=Shader.GLSL)
        except Exception:
            _grass_failed = True
            return None
    return _grass_shader


# Uniform `grs_time`/`grs_wind` didorong SEKALI ke `ursina.scene`, bukan ke tiap
# entity rumput. Panda3D mewariskan shader input ke seluruh anak NodePath, jadi
# satu panggilan menjangkau semua tutup rumput sekaligus.
#
# Kenapa diubah: tools/profil.py menunjuk update_time sebagai 3,12 ms dari
# 7,78 ms LOGIKA di scene mountain -- 40% seluruh waktu Python game, habis di
# 461 entity x 2 uniform = 922 panggilan set_shader_input tiap frame.
# tools/probe_rumput.py mengukur keduanya berdampingan di scene farm:
#
#   per-entity  0,590 ms/frame, 65.870 piksel berubah (maks kanal 147)
#   scene       0,004 ms/frame, 66.008 piksel berubah (maks kanal 147)
#
# Jadi animasinya BUKAN dibuang -- jumlah piksel yang bergerak praktis sama,
# dan itu yang membuktikan uniform-nya memang sampai ke shader. Yang hilang
# cuma 147x biayanya.
#
# SATU SYARAT yang harus dijaga: input per-entity MENINDIH input induk. Begitu
# ada kode lain yang memanggil `e.set_shader_input('grs_time', ...)` pada entity
# rumput, entity itu berhenti membaca nilai dari `scene` dan rumputnya membeku
# di nilai terakhirnya. Jangan lakukan itu; regress menjaganya lewat uji_rumput.
_wind_terakhir = None


def _dorong(time: float, wind: float):
    """Dorong kedua uniform ke scene. True kalau berhasil."""
    global _wind_terakhir
    try:
        from ursina import scene as _scene
        _scene.set_shader_input('grs_time', time)
        if wind != _wind_terakhir:
            _scene.set_shader_input('grs_wind', wind)
            _wind_terakhir = wind
        return True
    except Exception:
        return False


def apply_to_entities(entities: list, time: float = 0.0, wind: float = 0.06):
    """Terapkan grass shader ke list entity rumput.

    entities : list Entity yang sudah dibuat di world.py
    time     : nilai waktu animasi (detik real)
    wind     : kekuatan angin (0 = tidak ada, 0.1 = sepoi, 0.3 = kencang)

    Shader-nya tetap dipasang per entity -- itu memang milik tiap NodePath.
    Yang pindah ke `scene` cuma nilai uniform-nya.
    """
    sh = get_grass_shader()
    if sh is None:
        return
    for e in entities:
        try:
            e.shader = sh
        except Exception:
            pass
    global _wind_terakhir
    _wind_terakhir = None   # scene baru: paksa wind terdorong sekali
    _dorong(time, wind)


def update_time(entities: list, time: float, wind: float = 0.06):
    """Update uniform `grs_time` dan `grs_wind` tiap frame.

    `entities` cuma dipakai untuk tahu scene ini punya rumput atau tidak;
    nilainya didorong ke `scene`, bukan ke tiap anggota list.
    """
    if _grass_failed or not entities:
        return
    _dorong(time, wind)
