"""
smooth_shader.py — Shader lit + smooth untuk Lembah Karsa 3D.

Diadaptasi dari LightingCommon.fx (FreeSO) ke GLSL Panda3D/Ursina.
Tujuan: ganti tampilan voxel-flat menjadi soft-shaded ala Animal Crossing / TSO
tanpa mengubah geometri entity.

Fitur:
  - Half-Lambert diffuse (lebih lembut dari Lambert biasa)
  - Soft rim light (tepi mesh sedikit terang — efek "painterly")
  - Fake ambient occlusion: gradien gelap di bagian bawah world Y
  - Saturation lift ringan untuk warna pop ala cartoon

Pemakaian:
    from .smooth_shader import get_smooth_shader, apply_smooth
    e = Entity(model='cube', ...)
    apply_smooth(e)
"""
from ursina import Shader, Vec3


_VERT = """
#version 140
// v6 2026-08-27
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelMatrix;
uniform mat3 p3d_NormalMatrix;
in vec4 p3d_Vertex;
in vec3 p3d_Normal;
in vec2 p3d_MultiTexCoord0;
// Warna per-vertex. Kalau geometri tidak punya kolom warna, Panda mengikat
// ini ke putih, jadi entity lama tidak berubah sedikit pun. Yang dibuka:
// satu mesh boleh punya banyak warna tanpa dipecah jadi banyak Entity —
// dan itu satu-satunya cara mewarnai kulit, baju, dan celana pada humanoid
// tanpa menambah tiga entity per warga desa.
in vec4 p3d_Color;

out vec3 v_world_pos;
out vec3 v_world_normal;
out vec2 v_uv;
out vec4 v_color;

void main() {
    vec4 world = p3d_ModelMatrix * p3d_Vertex;
    v_world_pos = world.xyz;
    v_world_normal = normalize(mat3(p3d_ModelMatrix) * p3d_Normal);
    v_uv = p3d_MultiTexCoord0;
    v_color = p3d_Color;
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
}
"""

_FRAG = """
#version 140
// v6 2026-08-27
uniform sampler2D p3d_Texture0;
uniform vec4 p3d_ColorScale;
uniform mat4 p3d_ViewMatrixInverse;
uniform int sm_has_tex;
uniform vec3 sm_sun_dir;
uniform vec3 sm_sun_color;
uniform vec3 sm_ambient;
uniform float sm_rim_strength;
uniform float sm_ao_strength;
uniform float sm_ao_height;
uniform float sm_saturation;

in vec3 v_world_pos;
in vec3 v_world_normal;
in vec2 v_uv;
in vec4 v_color;

out vec4 fragColor;

vec3 lift_saturation(vec3 c, float s) {
    float luma = dot(c, vec3(0.299, 0.587, 0.114));
    return mix(vec3(luma), c, s);
}

void main() {
    // Base color dari p3d_ColorScale — Ursina menyimpan entity.color di sini via setColorScale()
    vec4 base = p3d_ColorScale * v_color;
    if (sm_has_tex == 1) {
        base *= texture(p3d_Texture0, v_uv);
    }
    if (base.a < 0.01) discard;

    vec3 N = normalize(v_world_normal);
    vec3 L = normalize(-sm_sun_dir);  // dari permukaan ke sumber cahaya

    // Toon / Cel-Shading (Cartoon effect)
    float ndl = dot(N, L);
    float diff;
    if (ndl > 0.3) {
        diff = 1.0;          // Bagian yang kena sinar matahari (Terang)
    } else if (ndl > -0.1) {
        diff = 0.6;          // Batas bayangan (Sedang)
    } else {
        diff = 0.3;          // Bagian yang tidak kena cahaya (Gelap)
    }

    vec3 cam_pos = p3d_ViewMatrixInverse[3].xyz;
    vec3 V = normalize(cam_pos - v_world_pos);
    float ndv = max(0.0, dot(N, V));
    // Outline subtract: tepi gelap tapi tidak memakan warna terang
    float edge = 1.0 - smoothstep(0.0, 0.18, ndv);  // 1 di tepi, 0 di tengah
    float outline_darken = 1.0 - edge * 0.55;        // max gelap 55% di tepi

    // Fake AO berdasarkan world Y — entity yang rendah lebih gelap di bawah
    float ao = mix(1.0 - sm_ao_strength * 0.5, 1.0,
                   clamp(v_world_pos.y / max(sm_ao_height, 0.01), 0.0, 1.0));

    vec3 lit = base.rgb * (sm_ambient + sm_sun_color * diff) * ao;

    lit *= outline_darken; // Tepi sedikit gelap, tidak full hitam
    lit = lift_saturation(lit, sm_saturation * 1.08); // Saturasi ringan — tidak neon

    fragColor = vec4(lit, base.a);
}
"""

_smooth_shader = None
_shader_failed  = False
_pipeline_checked = False

def reset_shader_cache():
    """Paksa re-compile shader berikutnya (panggil setelah hot-reload)."""
    global _smooth_shader, _shader_failed, _pipeline_checked
    _smooth_shader    = None
    _shader_failed    = False
    _pipeline_checked = False


def _is_opengl_pipeline() -> bool:
    """Deteksi apakah Panda3D pakai pipeline OpenGL (support GLSL).
    Direct3D 9 tidak support GLSL → harus skip shader supaya tidak ada error draw."""
    try:
        from direct.showbase.ShowBaseGlobal import base
        pname = base.pipe.get_type().get_name().lower()
        return 'gl' in pname  # wglGraphicsPipe, glxGraphicsPipe, cocoaGLGraphicsPipe
    except Exception:
        return True  # Asumsi optimis kalau gagal cek


def get_smooth_shader():
    """Return shader, atau None kalau GLSL tidak tersedia di pipeline aktif."""
    global _smooth_shader, _shader_failed, _pipeline_checked
    if _shader_failed:
        return None
    if not _pipeline_checked:
        _pipeline_checked = True
        if not _is_opengl_pipeline():
            import logging
            logging.warning("Pipeline non-OpenGL terdeteksi — smooth_shader di-skip.")
            _shader_failed = True
            return None
    if _smooth_shader is None:
        try:
            _smooth_shader = Shader(vertex=_VERT, fragment=_FRAG,
                                    language=Shader.GLSL,
                                    default_input={
                                        # HANYA yang tidak pernah berubah.
                                        #
                                        # Ursina memasang tiap default_input ke
                                        # ENTITY (entity.py:692), dan input di
                                        # entity MENIMPA input di induknya. Jadi
                                        # menaruh sm_sun_color / sm_ambient /
                                        # sm_sun_dir di sini berarti tiap entity
                                        # membawa salinan bekunya sendiri, dan
                                        # app.py._sync_shader_globals() yang
                                        # memasangnya di `scene` tidak berefek
                                        # apa pun. Diukur: mengubah sm_ambient
                                        # di scene menggeser 0,00% piksel;
                                        # mengubahnya di entity menggeser 91,9%.
                                        # Selama itu, siang-malam tidak pernah
                                        # sampai ke permukaan mana pun — yang
                                        # berubah malam hari cuma warna langit
                                        # dan kabut.
                                        'sm_has_tex': 0,
                                        'sm_rim_strength': 0.55,
                                        'sm_ao_strength': 0.28,
                                        'sm_ao_height': 1.6,
                                        'sm_saturation': 1.0,
                                    })
        except Exception as e:
            import logging
            logging.warning(f"smooth_shader gagal compile (GLSL tidak tersedia di pipeline ini): {e}")
            _shader_failed = True
            return None
        pasang_uniform_global()
    return _smooth_shader


_UNIFORM_GLOBAL_AWAL = {
    'sm_sun_dir':   Vec3(-0.5, -0.8, -0.4),
    'sm_sun_color': Vec3(1.05, 1.02, 0.92),
    'sm_ambient':   Vec3(0.45, 0.46, 0.50),
}


def pasang_uniform_global(sun_dir=None, sun_color=None, ambient=None):
    """Pasang uniform siang-malam di `scene`, satu kali per nilai.

    Ini menggantikan `default_input` untuk ketiga uniform ini. Karena tidak
    ada lagi salinan di entity yang menimpanya, nilai di `scene` benar-benar
    turun ke semua keturunan — dan mengubah waktu hari jadi TIGA panggilan,
    bukan tiga panggilan dikali dua ribu entity.

    Dipanggil sekali saat shader dibuat supaya uniform-nya dijamin ADA
    sebelum frame pertama: shader GLSL Panda melempar "Shader input ... is
    not present" kalau uniform-nya kosong, dan itu menghentikan game, bukan
    sekadar membuatnya jelek.
    """
    try:
        from ursina import scene
        scene.set_shader_input('sm_sun_dir', sun_dir or _UNIFORM_GLOBAL_AWAL['sm_sun_dir'])
        scene.set_shader_input('sm_sun_color', sun_color or _UNIFORM_GLOBAL_AWAL['sm_sun_color'])
        scene.set_shader_input('sm_ambient', ambient or _UNIFORM_GLOBAL_AWAL['sm_ambient'])
        return True
    except Exception:
        return False


def apply_smooth(entity, has_texture: bool = False):
    """Pasang smooth shader ke satu entity. Fallback graceful kalau GLSL tidak ada."""
    sh = get_smooth_shader()
    if sh is None:
        # Bypass pencahayaan Panda3D agar objek tidak hitam total di mode Direct3D 9
        try: entity.setLightOff()
        except AttributeError: entity.unlit = True
        return
    try:
        entity.shader = sh
        entity.set_shader_input('sm_has_tex', 1 if has_texture else 0)
    except Exception:
        try: entity.setLightOff()
        except AttributeError: entity.unlit = True


def update_globals(entities, sun_dir, sun_color, ambient):
    """Sinkronisasi uniform siang/malam.

    `entities` diabaikan dan itu disengaja. Versi lamanya melintasi seluruh
    daftar dan memasang tiga input ke TIAP entity — di mountain 2.177 x 3 —
    padahal ketiganya bernilai sama untuk semua orang. Sekarang dipasang di
    `scene` dan diwariskan. Parameternya dipertahankan supaya pemanggil lama
    tidak perlu diubah.

    (Fungsi ini sendiri tidak pernah dipanggil siapa pun sampai sekarang;
    yang dipakai app.py._sync_shader_globals(). Dibiarkan hidup dan BENAR
    supaya pemanggil berikutnya tidak menghidupkan kembali pola per-entity.)
    """
    return pasang_uniform_global(sun_dir, sun_color, ambient)
