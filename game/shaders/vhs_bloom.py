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
uniform sampler2D tex;
uniform float time;
in vec2 uv;
out vec4 fragColor;

const int SAMPLES = 3;
const float SPREAD = 0.0035;
const float LUM_THRESHOLD = 0.65;

vec3 getBloom(vec2 coord) {
    vec3 bloom = vec3(0.0);
    float count = 0.0;
    for(int i = -SAMPLES; i <= SAMPLES; i++) {
        for(int j = -SAMPLES; j <= SAMPLES; j++) {
            vec2 offset = vec2(float(i), float(j)) * SPREAD;
            vec3 c = texture(tex, coord + offset).rgb;
            float lum = dot(c, vec3(0.299, 0.587, 0.114));
            if (lum > LUM_THRESHOLD) {
                // boost the bright parts slightly
                bloom += c * (c * 1.2);
            }
            count += 1.0;
        }
    }
    return bloom / count;
}

void main() {
    // 1. CRT Barrel Distortion (extremely subtle, virtually flat for clear visibility)
    vec2 crt_uv = uv - 0.5;
    float dist = dot(crt_uv, crt_uv);
    crt_uv = crt_uv * (1.0 + dist * 0.015); // warp factor reduced from 0.15
    crt_uv += 0.5;
    
    // Check screen bounds for black borders
    if (crt_uv.x < 0.0 || crt_uv.x > 1.0 || crt_uv.y < 0.0 || crt_uv.y > 1.0) {
        fragColor = vec4(0.0, 0.0, 0.0, 1.0);
        return;
    }

    // 2. Glitch Sine Wave / Tearing (highly subtle, no hard jumps to prevent visual fatigue)
    float glitch = sin(crt_uv.y * 20.0 + time * 4.0) * 0.0002;
    float jump = 0.0;
    vec2 fetch_uv = crt_uv + vec2(glitch + jump, 0.0);

    // 3. Chromatic Aberration (highly reduced from 0.0025 to 0.0004 for super crisp colors)
    float r = texture(tex, fetch_uv + vec2(0.0004, 0.0)).r;
    float g = texture(tex, fetch_uv).g;
    float b = texture(tex, fetch_uv - vec2(0.0004, 0.0)).b;
    vec3 base_color = vec3(r, g, b);

    // 4. Pseudo-Bloom (softened from 1.8 to 0.45 for an elegant glow instead of color blinding)
    vec3 bloom_color = getBloom(fetch_uv);
    vec3 final_color = base_color + bloom_color * 0.45;

    // 5. Scanlines (extremely faint and soft)
    float scanline = sin(crt_uv.y * 800.0 + time * 5.0) * 0.015;
    final_color -= scanline;

    // 6. Vignette (very soft edge shading, no dark corners)
    float vignette = length(uv - 0.5);
    final_color *= smoothstep(0.9, 0.48, vignette);

    fragColor = vec4(final_color, 1.0);
}
'''

vhs_bloom_shader = Shader(
    language=Shader.GLSL,
    vertex=_VERT,
    fragment=_FRAG
)
