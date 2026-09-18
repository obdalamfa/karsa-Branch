"""
grass_shader.py — Animasi rumput melambai angin.
Diadaptasi dari FreeSO GrassShader.fx (teknik DrawBlades + wind sway).

FreeSO pola:
  - Posisi tiap vertex di-offset berdasarkan sin(worldPos.x + Time * speed)
  - Hanya vertex bagian atas yang bergerak (h = max(0, pos.y - ground))
  - Dua frekuensi sinus digabung agar terlihat natural

Ursina: shader GLSL, uniform `time` di-update tiap frame dari app.py.

Fragmennya DIPINJAM dari smooth_shader, dan itu perbaikan bug, bukan
kerapian. Fragmen lamanya satu baris:

    fragColor = texture(p3d_Texture0, uv);

yang berarti tutup rumput membuang SEMUANYA — warna tint per ubin, cahaya
matahari, gelap-terang siang-malam, bayangan toon, AO. Rumput adalah
satu-satunya permukaan di dunia ini yang terang benderang sama saja di tengah
malam, dan satu-satunya yang tidak ikut berubah warna saat musim atau cuaca
berganti. Tint yang dihitung `world._cb()` untuk tiap ubin rumput dipasang ke
entity-nya dengan rapi lalu dibuang di baris itu.

Karena fragmennya sekarang sama persis dengan milik smooth_shader, rumput
menerima pencahayaan yang sama dengan tanah di bawahnya — dan tetap melambai,
karena yang berbeda cuma vertex shader-nya.
"""
from ursina import Shader, Vec3

# Varying-nya sengaja sama persis dengan milik smooth_shader (v_world_pos,
# v_world_normal, v_uv, v_color), karena fragmennya memang fragmen itu.
_GRASS_VERT = """
#version 140
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelMatrix;
uniform mat3 p3d_NormalMatrix;
in vec4 p3d_Vertex;
in vec3 p3d_Normal;
in vec2 p3d_MultiTexCoord0;
in vec4 p3d_Color;
uniform float grs_time;
uniform float grs_wind;

out vec3 v_world_pos;
out vec3 v_world_normal;
out vec2 v_uv;
out vec4 v_color;

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

    // Posisi dunia diambil SETELAH digeser. Kalau diambil sebelum, AO dan rim
    // light dihitung untuk tempat yang tidak lagi ditempati vertex-nya, dan
    // rumput yang melambai kencang akan terlihat berkedip terang-gelap.
    vec4 world_sway = p3d_ModelMatrix * pos;
    v_world_pos = world_sway.xyz;
    v_world_normal = normalize(mat3(p3d_ModelMatrix) * p3d_Normal);
    v_uv = p3d_MultiTexCoord0;
    v_color = p3d_Color;

    gl_Position = p3d_ModelViewProjectionMatrix * pos;
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
            # Fragmen dipinjam UTUH dari smooth_shader — lihat docstring modul.
            # Diimpor, bukan disalin: dua salinan GLSL yang harus tetap sama
            # adalah dua salinan yang akan berbeda pada perubahan berikutnya.
            from .smooth_shader import _FRAG as _SMOOTH_FRAG, pasang_uniform_global
            # Uniform siang-malam harus sudah ADA di scene sebelum frame
            # pertama: GLSL Panda melempar "Shader input ... is not present"
            # dan game berhenti, bukan cuma jadi jelek.
            pasang_uniform_global()
            _grass_shader = Shader(vertex=_GRASS_VERT, fragment=_SMOOTH_FRAG,
                                   language=Shader.GLSL,
                                   default_input={
                                       # HANYA yang tidak pernah berubah.
                                       # Ursina memasang default_input ke
                                       # ENTITY, dan input entity menimpa
                                       # induknya — jadi grs_time di sini akan
                                       # membekukan setiap rumput di nilai
                                       # awalnya, dan sm_sun_color di sini akan
                                       # memutus rumput dari siang-malam.
                                       # Dua-duanya sudah terjadi sekali dan
                                       # ditangkap `rumput_lambai`.
                                       'sm_has_tex': 1,
                                       'sm_rim_strength': 0.55,
                                       'sm_ao_strength': 0.28,
                                       'sm_ao_height': 1.6,
                                       'sm_saturation': 1.0,
                                   })
        except Exception as e:
            import logging
            logging.warning(f'grass_shader gagal compile: {e}')
            _grass_failed = True
            return None
    return _grass_shader


def _induk_uniform():
    """Node tempat uniform rumput dipasang SEKALI, bukan per entity.

    Shader input di Panda3D diwariskan ke seluruh keturunan node. Jadi satu
    assignment di `scene` sampai ke semua rumput di bawahnya, dan tidak ada
    alasan menyentuh tiap entity satu per satu.
    """
    from ursina import scene
    return scene


def apply_to_entities(entities: list, time: float = 0.0, wind: float = 0.06):
    """Terapkan grass shader ke list entity rumput.

    entities : list Entity yang sudah dibuat di world.py
    time     : nilai waktu animasi (detik real)
    wind     : kekuatan angin (0 = tidak ada, 0.1 = sepoi, 0.3 = kencang)

    Shader-nya dipasang per entity — memang harus, itu yang menentukan entity
    mana yang melambai. Tapi NILAI uniform-nya tidak: itu sama untuk semua
    rumput dan dipasang sekali di induknya (lihat update_time).
    """
    sh = get_grass_shader()
    if sh is None:
        return
    for e in entities:
        try:
            e.shader = sh
            # Uniform SENGAJA tidak dipasang di sini. Input yang dipasang di
            # entity MENIMPA input dari induknya, jadi satu saja yang
            # tertinggal di sini sudah cukup membuat rumput itu membeku
            # sementara yang lain melambai.
        except Exception:
            pass
    update_time(entities, time, wind)


def update_time(entities: list, time: float, wind: float = 0.06):
    """Update uniform `grs_time` dan `grs_wind`. Dipanggil tiap frame.

    Dulu ini melintasi seluruh daftar rumput dan memanggil set_shader_input
    dua kali per entity. Di scene `mountain` itu 488 entity x 2 = 976
    panggilan PER FRAME, dan cProfile menunjukkannya sebagai satu-satunya
    biaya Python terbesar di luar render: 39.320 panggilan dalam 40 frame,
    ~12,5 ms per frame — untuk memasang dua angka yang sama ke semua orang.

    Sekarang dua panggilan, titik. Shader input diwariskan ke keturunan, dan
    tiap rumput ada di bawah `scene`.

    `entities` dipertahankan di tanda tangan supaya pemanggil lama tidak
    perlu diubah, dan supaya nol-rumput tetap berarti nol kerja.
    """
    if _grass_failed or not entities:
        return
    try:
        induk = _induk_uniform()
        induk.set_shader_input('grs_time', time)
        induk.set_shader_input('grs_wind', wind)
    except Exception:
        pass
