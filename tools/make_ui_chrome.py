"""make_ui_chrome.py — Tekstur panel 'chrome' ala TSO (ROADMAP M3 skin HUD-A).

Bingkai logam bergradien (bevel) + isi parchment gelap muted, dirancang
TAHAN-STRETCH (tanpa ornamen sudut yang distorsi saat diregang), supaya
bisa dipasang langsung sebagai texture latar panel apa pun.

Output: assets/ui/panel_chrome.png (256x256, RGBA)
Pakai: python tools/make_ui_chrome.py
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent.parent / 'assets' / 'ui'
OUT.mkdir(parents=True, exist_ok=True)
SS = 3
N = 256 * SS
B = 26 * SS          # tebal bingkai
R = 30 * SS          # radius sudut

# Palet TSO-ish: krom kuningan hangat -> isi parchment gelap (selaras Disco muted)
FRAME_HI = (214, 188, 140)   # sorotan logam atas-kiri
FRAME_LO = (120, 96, 60)     # bayangan logam bawah-kanan
INNER    = (34, 30, 26, 246) # isi panel gelap hangat
BEVEL    = (245, 224, 170)   # garis kilau di tepi-dalam bingkai


def _rrect(d, box, radius, fill):
    d.rounded_rectangle(box, radius=radius, fill=fill)


def main():
    img = Image.new('RGBA', (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # 1) Bingkai luar: gradien diagonal logam (hi -> lo) lewat banyak lapis rrect
    steps = B
    for i in range(steps):
        t = i / max(1, steps - 1)
        col = tuple(int(FRAME_HI[k] * (1 - t) + FRAME_LO[k] * t) for k in range(3))
        _rrect(d, [i, i, N - 1 - i, N - 1 - i], max(2, R - i), col + (255,))

    # 2) Garis kilau (bevel) tepat di tepi-dalam bingkai
    d.rounded_rectangle([B - 2*SS, B - 2*SS, N - B + 2*SS, N - B + 2*SS],
                        radius=max(2, R - B), outline=BEVEL + (210,), width=2*SS)

    # 3) Isi panel parchment gelap + vignette halus
    inner = Image.new('RGBA', (N, N), (0, 0, 0, 0))
    di = ImageDraw.Draw(inner)
    _rrect(di, [B, B, N - 1 - B, N - 1 - B], max(2, R - B), INNER)
    # vignette: gelapkan tepi-dalam sedikit
    vg = Image.new('RGBA', (N, N), (0, 0, 0, 0))
    dv = ImageDraw.Draw(vg)
    _rrect(dv, [B, B, N - 1 - B, N - 1 - B], max(2, R - B), (0, 0, 0, 60))
    _rrect(dv, [B + 10*SS, B + 10*SS, N - 1 - B - 10*SS, N - 1 - B - 10*SS],
           max(2, R - B), (0, 0, 0, 0))
    vg = vg.filter(ImageFilter.GaussianBlur(8 * SS))
    inner.alpha_composite(vg)
    img.alpha_composite(inner)

    img = img.resize((256, 256), Image.LANCZOS)
    img.save(OUT / 'panel_chrome.png')
    print(f"[make_ui_chrome] panel_chrome.png -> {OUT}")


if __name__ == '__main__':
    main()
