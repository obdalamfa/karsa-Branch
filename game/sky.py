"""
sky.py — SkyDome prosedural untuk Lembah Karsa 3D.
Diadaptasi dari FreeSO SkyDomeComponent.cs + AbstractSkyDome.

FreeSO pola:
  - OutsideTime (0–24) → interpolasi warna zenith/horizon/matahari
  - Weather → modifikasi saturasi dan intensitas
  - SunVector → arah matahari untuk glow

Implementasi Ursina:
  - Sphere besar dibalik (scale negatif) sebagai kubah langit
  - GLSL shader gradien zenith→horizon + sun glow
  - update() dipanggil tiap frame dari app.py
"""
from ursina import Entity, Vec3, color, Shader

# ─── GLSL SKY SHADER (port dari AbstractSkyDome pattern FreeSO) ──────────────
_SKY_VERT = """
#version 140
uniform mat4 p3d_ModelViewProjectionMatrix;
in vec4 p3d_Vertex;
out vec3 vDir;
void main() {
    vDir = p3d_Vertex.xyz;
    // Skybox trick: pastikan sky selalu di belakang semua objek
    vec4 pos = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    gl_Position = pos.xyww;
}
"""

_SKY_FRAG = """
#version 140
in vec3 vDir;
uniform vec3 sky_zenith;
uniform vec3 sky_horizon;
uniform vec3 sky_sun_glow;
uniform vec3 sky_sun_dir;
out vec4 fragColor;
void main() {
    vec3 d = normalize(vDir);
    // Gradient: t=0 (horizon), t=1 (zenith)
    float t = clamp(d.y * 1.8 + 0.05, 0.0, 1.0);
    vec3 col = mix(sky_horizon, sky_zenith, pow(t, 0.55));
    // Sun glow (FreeSO SunVector pattern)
    float s = max(0.0, dot(d, normalize(sky_sun_dir)));
    col += sky_sun_glow * pow(s, 52.0) * 1.4;
    // Soft haze at horizon
    float haze = pow(1.0 - abs(d.y), 3.5) * 0.18;
    col += sky_horizon * haze;
    fragColor = vec4(col, 1.0);
}
"""

_sky_shader = None
_sky_failed = False
_sky_pipeline_checked = False


def _is_opengl_pipeline() -> bool:
    try:
        from direct.showbase.ShowBaseGlobal import base
        return 'gl' in base.pipe.get_type().get_name().lower()
    except Exception:
        return True


def _get_sky_shader():
    global _sky_shader, _sky_failed, _sky_pipeline_checked
    if _sky_failed:
        return None
    if not _sky_pipeline_checked:
        _sky_pipeline_checked = True
        if not _is_opengl_pipeline():
            _sky_failed = True
            return None
    if _sky_shader is None:
        try:
            _sky_shader = Shader(vertex=_SKY_VERT, fragment=_SKY_FRAG,
                                 language=Shader.GLSL)
        except Exception:
            _sky_failed = True
            return None
    return _sky_shader


# ─── Palet warna langit per kondisi (port FreeSO OutsideTime interpolation) ───
# Format: (zenith_rgb, horizon_rgb, sun_glow_rgb, sun_dir_xyz)
# Format tiap baris: (zenith, cakrawala, pendar matahari, arah matahari).
#
# Tabel sebelumnya tidak punya SATU PUN warna langit yang masuk akal. Diukur
# dari frame yang benar-benar dirender di scene farm:
#
#     jam     zenith            cakrawala
#     09:00   158,198,211       154,188,191
#     12:00   253,131,210 MERAH MUDA   201,136,188 MERAH MUDA
#     15:00   253,131,210 MERAH MUDA   201,136,188 MERAH MUDA
#     22:00    26,210,253 sian          48,187,198 sian
#
# Dua hal yang tidak bisa dibela sebagai gaya: sepanjang siang langitnya merah
# muda menyala, dan pukul 22:00 langitnya LEBIH TERANG daripada pukul 09:00.
# Di tabel lamanya magenta (1,00 0,20 0,80) dipakai di EMPAT slot berbeda —
# sebagai pendar malam, cakrawala fajar, pendar pagi, dan pendar petang
# sekaligus. Itu bukan palet, itu warna tempelan yang tidak pernah diganti.
#
# Tabel ini gaya, bukan fotoreal: birunya lebih pekat dan jingganya lebih
# hangat daripada langit sungguhan, mengikuti bahasa game kehidupan Jepang yang
# sudah dipakai di seluruh rupa karakter. Tapi tiga hal fisis dijaga —
# zenith selalu lebih GELAP daripada cakrawala di siang hari (itu yang membuat
# langit terbaca sebagai kubah, bukan sebagai dinding), malam benar-benar
# gelap, dan pendar matahari hangat, tidak pernah magenta.
_SKY_NIGHT   = ((0.05, 0.07, 0.16), (0.10, 0.12, 0.24), (0.30, 0.36, 0.58), ( 0.0,  1.0,  0.0))
_SKY_DAWN    = ((0.30, 0.36, 0.64), (0.98, 0.66, 0.52), (1.00, 0.72, 0.45), ( 0.7,  0.2, -0.1))
_SKY_MORNING = ((0.34, 0.58, 0.89), (0.82, 0.89, 0.96), (1.00, 0.93, 0.78), ( 0.5,  0.5, -0.4))
_SKY_DAY     = ((0.25, 0.51, 0.90), (0.72, 0.86, 0.97), (1.00, 0.97, 0.88), ( 0.0,  1.0, -0.4))
_SKY_DUSK    = ((0.32, 0.34, 0.62), (1.00, 0.60, 0.42), (1.00, 0.64, 0.38), (-0.7,  0.2, -0.1))
_SKY_EVENING = ((0.09, 0.11, 0.28), (0.22, 0.20, 0.40), (0.52, 0.42, 0.58), (-0.9, -0.1,  0.0))

# Modifikasi cuaca — mengurangi saturasi (FreeSO Weather pattern)
_WEATHER_MUL = {
    'Cerah':    1.00,
    'Mendung':  0.60,
    'Hujan':    0.50,
    'Badai':    0.40,
    'Berangin': 0.75,
}

def _lerp3(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))

def _sky_palette(hour: float, weather: str):
    """Interpolasi palet langit berdasarkan jam (0–24) dan cuaca."""
    # Peta jam → palet
    # Pemetaan jam. Versi lama memulai peralihan ke fajar dari jam 00:00
    # (`hour / 5.0`), jadi pukul 03:00 langitnya sudah 60% fajar — terukur
    # kejinggaan di tengah malam. Malam sekarang DITAHAN sampai 04:12, dan
    # tidak ada malam kedua yang dimulai dari nol: sesudah 21:00 langit sudah
    # malam penuh dan tinggal diam di situ.
    if hour < 4.2:
        pal = _SKY_NIGHT
    elif hour < 6.0:
        pal = _lerp_pal(_SKY_NIGHT, _SKY_DAWN, (hour - 4.2) / 1.8)
    elif hour < 7.5:
        pal = _lerp_pal(_SKY_DAWN, _SKY_MORNING, (hour - 6.0) / 1.5)
    elif hour < 10.0:
        pal = _lerp_pal(_SKY_MORNING, _SKY_DAY, (hour - 7.5) / 2.5)
    elif hour < 16.0:
        pal = _SKY_DAY
    elif hour < 18.0:
        pal = _lerp_pal(_SKY_DAY, _SKY_DUSK, (hour - 16.0) / 2.0)
    elif hour < 19.3:
        pal = _lerp_pal(_SKY_DUSK, _SKY_EVENING, (hour - 18.0) / 1.3)
    elif hour < 21.0:
        pal = _lerp_pal(_SKY_EVENING, _SKY_NIGHT, (hour - 19.3) / 1.7)
    else:
        pal = _SKY_NIGHT

    mul = _WEATHER_MUL.get(weather, 1.0)
    zenith  = tuple(c * mul for c in pal[0])
    horizon = tuple(c * mul for c in pal[1])
    sun_gl  = tuple(c * mul for c in pal[2])
    return zenith, horizon, sun_gl, pal[3]

def _lerp_pal(a, b, t):
    t = max(0.0, min(1.0, t))
    return (
        _lerp3(a[0], b[0], t),
        _lerp3(a[1], b[1], t),
        _lerp3(a[2], b[2], t),
        _lerp3(a[3], b[3], t),
    )


class SkyDome:
    """Kubah langit prosedural ala FreeSO SkyDomeComponent.

    Dibuat sebagai sphere terbalik besar — selalu mengelilingi kamera.
    Shader GLSL menghitung gradien zenith/horizon + sun glow.
    """

    def __init__(self):
        sky_sh = _get_sky_shader()
        self._has_shader = sky_sh is not None
        if not self._has_shader:
            # Fallback: tidak ada sky dome — langit pakai window.color sebagai background polos.
            # Ini mencegah sphere -500 render hitam menutupi seluruh scene.
            self._sphere = None
            self._apply(6.5, 'Cerah')
            return
        self._sphere = Entity(
            model='sphere',
            scale=(-500, -500, -500),   # dibalik (skala negatif = render inside)
            shader=sky_sh,
            unlit=True,
        )
        # Depth test: langit tidak memblok objek apapun
        from panda3d.core import DepthTestAttrib, DepthWriteAttrib
        self._sphere.node().setAttrib(DepthTestAttrib.make(DepthTestAttrib.MLessEqual))
        self._sphere.node().setAttrib(DepthWriteAttrib.make(False))

        # Inisialisasi dengan warna siang
        self._apply(6.5, 'Cerah')

    def update(self, hour: float, weather: str, is_indoor: bool):
        """Dipanggil tiap frame dari app.py update()."""
        if self._sphere is None:
            # Tanpa shader: cukup update window.color via _apply ke horizon palette
            if not is_indoor:
                self._apply(hour, weather)
            return
        self._sphere.enabled = not is_indoor
        if not is_indoor:
            self._apply(hour, weather)

    def _apply(self, hour: float, weather: str):
        zenith, horizon, sun_glow, sun_dir = _sky_palette(hour, weather)
        if self._sphere is None:
            # Fallback: set window background ke horizon color
            try:
                from ursina import window, color
                window.color = color.rgb(int(horizon[0]*255), int(horizon[1]*255), int(horizon[2]*255))
            except Exception:
                pass
            return
        sp = self._sphere
        sp.set_shader_input('sky_zenith',   Vec3(*zenith))
        sp.set_shader_input('sky_horizon',  Vec3(*horizon))
        sp.set_shader_input('sky_sun_glow', Vec3(*sun_glow))
        sp.set_shader_input('sky_sun_dir',  Vec3(*sun_dir))
