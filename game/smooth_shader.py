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
// v5 2026-05-17
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelMatrix;
uniform mat3 p3d_NormalMatrix;
in vec4 p3d_Vertex;
in vec3 p3d_Normal;
in vec2 p3d_MultiTexCoord0;

out vec3 v_world_pos;
out vec3 v_world_normal;
out vec2 v_uv;

void main() {
    vec4 world = p3d_ModelMatrix * p3d_Vertex;
    v_world_pos = world.xyz;
    v_world_normal = normalize(mat3(p3d_ModelMatrix) * p3d_Normal);
    v_uv = p3d_MultiTexCoord0;
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
}
"""

_FRAG = """
#version 140
// v5 2026-05-17
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

out vec4 fragColor;

vec3 lift_saturation(vec3 c, float s) {
    float luma = dot(c, vec3(0.299, 0.587, 0.114));
    return mix(vec3(luma), c, s);
}

void main() {
    // Base color dari p3d_ColorScale — Ursina menyimpan entity.color di sini via setColorScale()
    vec4 base = p3d_ColorScale;
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
                                        'sm_has_tex': 0,
                                        'sm_sun_dir': Vec3(-0.5, -0.8, -0.4),
                                        'sm_sun_color': Vec3(1.05, 1.02, 0.92),
                                        'sm_ambient': Vec3(0.45, 0.46, 0.50),
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
    return _smooth_shader


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
    """Sinkronisasi uniform global (dipanggil saat transisi siang/malam).

    Camera position diambil langsung dari p3d_ViewMatrixInverse di shader,
    jadi tidak perlu di-update per frame.
    """
    for e in entities:
        try:
            e.set_shader_input('sm_sun_dir', sun_dir)
            e.set_shader_input('sm_sun_color', sun_color)
            e.set_shader_input('sm_ambient', ambient)
        except Exception:
            pass
