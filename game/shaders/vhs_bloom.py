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

const int SAMPLES = 3;
const float SPREAD = 0.0035;
// Ambang dinaikkan 0,65 -> 0,80. Kulit yang tersinari punya luminans 0,85,
// jadi dengan ambang lama WAJAH IKUT MEKAR — dan mekar itu menambahkannya
// kembali ke atas 1,0 sehingga terpotong jadi putih, persis pemotongan yang
// sudah ditutup di smooth_shader.py. Bloom seharusnya menangkap sumber
// cahaya dan sorotan, bukan kulit orang.
const float LUM_THRESHOLD = 0.80;

vec3 getBloom(vec2 coord) {
    vec3 bloom = vec3(0.0);
    float count = 0.0;
    for(int i = -SAMPLES; i <= SAMPLES; i++) {
        for(int j = -SAMPLES; j <= SAMPLES; j++) {
            vec2 offset = vec2(float(i), float(j)) * SPREAD;
            vec3 c = texture(tex, coord + offset).rgb;
            float lum = dot(c, vec3(0.299, 0.587, 0.114));
            // Lutut LUNAK, bukan saklar. Versi lama memakai `if (lum > ambang)`
            // lalu menambahkan seluruh c*c*1.2: satu piksel yang kebetulan
            // melewati ambang menyumbang sebanyak piksel yang jauh lebih
            // terang. Sekarang yang mekar hanya KELEBIHAN terang di atas
            // ambang, dan besarnya sebanding dengan kuadrat kelebihan itu,
            // jadi tepian mekar melunak alih-alih membentuk batas keras.
            float lebih = max(lum - LUM_THRESHOLD, 0.0)
                        / max(1.0 - LUM_THRESHOLD, 1e-3);
            bloom += c * (lebih * lebih);
            count += 1.0;
        }
    }
    return bloom / count;
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

    // Jaga RONA, sama seperti di smooth_shader.py. Bloom menambahkan cahaya
    // di ATAS warna yang sudah ada, jadi tanpa ini ia mengembalikan persis
    // pemotongan per-kanal yang baru saja ditutup di sana: kulit hangat
    // dijadikan putih lagi oleh mekarnya sendiri. Kanal tertinggi didudukkan
    // di 1,0 dan sisanya ikut turun dengan rasio yang sama.
    float puncak = max(final_color.r, max(final_color.g, final_color.b));
    if (puncak > 1.0) {
        final_color /= puncak;
    }

    fragColor = vec4(final_color, 1.0);
}
'''

vhs_bloom_shader = Shader(
    language=Shader.GLSL,
    vertex=_VERT,
    fragment=_FRAG
)
