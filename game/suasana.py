"""Cahaya dan langit per scene.

app.py hanya membedakan indoor/outdoor menurut jam, sehingga gua naga mendapat
lampu rumah yang terang dan Swarga mendapat siang desa biasa. Di sini tiap
tempat yang punya watak sendiri menimpa (matahari, ambient, langit) itu.
Semua warna dalam skala 0-255, sama dengan color.rgb milik game.
"""

_PRESET = {
    # Gelap kebiruan: terang di gua datang dari kristal dan obor, bukan langit.
    'naga_cave': dict(sun=(70, 92, 126), amb=(52, 64, 90), sky=(5, 7, 12)),
    # Kahyangan: senja keemasan abadi, tidak ikut jam desa.
    'swarga': dict(sun=(255, 210, 150), amb=(126, 104, 116), sky=(232, 164, 120)),
}

# (zenith, horizon, sun_glow, sun_dir) untuk SkyDome, skala 0-1.
_LANGIT = {
    'swarga': ((0.34, 0.30, 0.56), (0.98, 0.66, 0.42), (1.00, 0.80, 0.48),
               (-0.55, 0.22, -0.4)),
}

_HAZE_GUNUNG = (196, 212, 226)


def atur(scene_name, sun, amb, sky):
    """(sun, amb, sky) default untuk jam ini -> versi milik scene."""
    p = _PRESET.get(scene_name)
    if p is not None:
        return p['sun'], p['amb'], p['sky']
    if scene_name == 'mountain':
        # Udara tipis: matahari lebih putih, bayangan kebiruan, langit berkabut.
        sun = (sun[0] * 0.94, sun[1] * 0.97, min(255.0, sun[2] * 1.06))
        amb = (amb[0] * 0.90, amb[1] * 0.98, min(255.0, amb[2] * 1.20))
        sky = tuple(s * 0.65 + h * 0.35 for s, h in zip(sky, _HAZE_GUNUNG))
    return sun, amb, sky


def palet_langit(scene_name):
    return _LANGIT.get(scene_name)
