from ursina import Shader

_VERT = '''
#version 140
uniform mat4 p3d_ModelViewProjectionMatrix;
in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;
out vec2 uv;
void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    uv = p3d_MultiTexCoord0;
}
'''

_FRAG = '''
#version 140
// Color-grade Disco Elysium (mengganti VHS/CRT lama yang bentrok dengan mood painterly).
// Tanpa chromatic aberration / scanline / barrel distortion.
uniform sampler2D tex;
uniform float time;
in vec2 uv;
out vec4 fragColor;

// Resolusi piksel efektif — HALUS (butiran seperti pasir), gambar tetap jelas.
const vec2 PIXEL_RES = vec2(960.0, 540.0);

// Grain pseudo-acak per-piksel (tekstur "pasir" halus)
float grain(vec2 p) {
    return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

void main() {
    // 0. PIXELATION halus — kuantisasi UV ke grid rapat (sampel di tengah sel)
    vec2 puv = (floor(uv * PIXEL_RES) + 0.5) / PIXEL_RES;
    vec3 c = texture(tex, puv).rgb;

    // 0b. Butiran pasir (grit Zomboid — terlihat tapi tidak mengganggu)
    float g = grain(floor(uv * PIXEL_RES));
    c += (g - 0.5) * 0.030;

    // 1. Desaturasi Disco Elysium — dunia pudar kelelahan
    float luma = dot(c, vec3(0.299, 0.587, 0.114));
    c = mix(vec3(luma), c, 0.78);

    // 1b. Split-tone: bayangan ditarik ke teal dingin, merah turun di area gelap
    c -= vec3(0.022, 0.004, 0.012) * (1.0 - luma);

    // 2. Angkat black supaya tile gelap jadi abu (BUKAN hitam → tidak ada magenta)
    c = c * 0.90 + 0.07;

    // 3. Kontras sangat lembut (hampir netral) — tidak memperkuat noise gelap
    c = (c - 0.5) * 1.02 + 0.5;

    // 4. Vignette — bingkai suram menekan sudut layar
    float v = length(uv - 0.5);
    c *= smoothstep(1.15, 0.35, v) * 0.14 + 0.86;

    fragColor = vec4(clamp(c, 0.0, 1.0), 1.0);
}
'''

vhs_bloom_shader = Shader(
    language=Shader.GLSL,
    vertex=_VERT,
    fragment=_FRAG
)
