#!/usr/bin/env python3
"""
icon_contact.py — Susun semua ikon target jadi satu montase grid berlabel.

Membaca assets/textures/<id>.png, menempatkan tiap ikon dalam sel ~96px
dengan latar abu netral + label id, lalu simpan ke tools/icon_contact.png.

Jalankan dari root repo:  python tools/icon_contact.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

# Root repo = parent dari folder tools/
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_DIR = os.path.join(ROOT, "assets", "textures")
OUT_PATH = os.path.join(ROOT, "tools", "icon_contact.png")

IDS = [
    "sword_kayu", "sword_besi", "sword_emas", "sword_mithril",
    "jala", "obor", "perahu", "peti_kayu", "pagar_kayu",
    "mithril", "mutiara", "ikan_laut", "ikan_legendaris",
    "mandrake", "running_mushroom", "firefly", "wild_herb", "wild_berry",
    "fragmen_prasasti_1", "fragmen_prasasti_2", "fragmen_prasasti_3",
    "buku_paman_arsa", "peta_mimpi_maya", "surat_paman_arsa_2",
]

# Bandingkan juga gaya dengan ikon lama (referensi konsistensi)
REF_IDS = ["lobak", "kayu", "susu"]

ICON_PX = 96            # area gambar per sel
LABEL_H = 18            # tinggi strip label
PAD = 6                 # padding dalam sel
CELL_W = ICON_PX + PAD * 2
CELL_H = ICON_PX + PAD * 2 + LABEL_H
COLS = 6

BG = (96, 96, 100)            # latar montase abu netral gelap
CELL_BG = (130, 130, 134)     # latar sel abu netral
CHECK_A = (122, 122, 126)     # papan catur agar transparansi ikon kelihatan
CHECK_B = (138, 138, 142)
LABEL_BG = (40, 40, 44)
LABEL_FG = (235, 235, 235)
MISSING_FG = (220, 70, 70)


def load_font(size):
    for name in ("arial.ttf", "DejaVuSans.ttf", "segoeui.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def checker(w, h, sq=8):
    """Papan catur abu agar piksel transparan ikon terbaca."""
    img = Image.new("RGB", (w, h), CHECK_A)
    px = img.load()
    for y in range(h):
        for x in range(w):
            if ((x // sq) + (y // sq)) % 2 == 0:
                px[x, y] = CHECK_A
            else:
                px[x, y] = CHECK_B
    return img


def render_cell(icon_id, font, ref=False):
    cell = Image.new("RGB", (CELL_W, CELL_H), CELL_BG)
    draw = ImageDraw.Draw(cell)

    # area ikon dengan papan catur
    chk = checker(ICON_PX, ICON_PX)
    cell.paste(chk, (PAD, PAD))

    path = os.path.join(TEX_DIR, icon_id + ".png")
    status = "ok"
    if os.path.isfile(path):
        try:
            im = Image.open(path).convert("RGBA")
            # scale ke ICON_PX menjaga aspek
            im.thumbnail((ICON_PX, ICON_PX), Image.NEAREST)
            ox = PAD + (ICON_PX - im.width) // 2
            oy = PAD + (ICON_PX - im.height) // 2
            cell.paste(im, (ox, oy), im)
        except Exception as e:
            status = "err"
            draw.text((PAD + 4, PAD + 4), "ERR", fill=MISSING_FG, font=font)
    else:
        status = "missing"
        draw.line([(PAD, PAD), (PAD + ICON_PX, PAD + ICON_PX)], fill=MISSING_FG, width=2)
        draw.line([(PAD + ICON_PX, PAD), (PAD, PAD + ICON_PX)], fill=MISSING_FG, width=2)
        draw.text((PAD + 4, PAD + 4), "MISSING", fill=MISSING_FG, font=font)

    # label strip
    ly = PAD + ICON_PX
    draw.rectangle([0, ly, CELL_W, CELL_H], fill=(60, 60, 66) if ref else LABEL_BG)
    label = ("REF: " + icon_id) if ref else icon_id
    # truncate kalau kepanjangan
    max_w = CELL_W - 6
    while draw.textlength(label, font=font) > max_w and len(label) > 4:
        label = label[:-2]
    draw.text((3, ly + 2), label, fill=LABEL_FG, font=font)
    return cell, status


def main():
    font = load_font(11)
    title_font = load_font(16)

    all_ids = IDS + REF_IDS
    n = len(all_ids)
    rows = (n + COLS - 1) // COLS

    title_h = 30
    grid_w = COLS * CELL_W
    grid_h = rows * CELL_H
    sheet = Image.new("RGB", (grid_w, grid_h + title_h), BG)
    draw = ImageDraw.Draw(sheet)
    draw.text((8, 6), "Lembah Karsa — Icon Contact Sheet (target + REF lama)",
              fill=(240, 240, 240), font=title_font)

    statuses = {}
    for i, icon_id in enumerate(all_ids):
        r, c = divmod(i, COLS)
        is_ref = icon_id in REF_IDS
        cell, status = render_cell(icon_id, font, ref=is_ref)
        sheet.paste(cell, (c * CELL_W, title_h + r * CELL_H))
        statuses[icon_id] = status

    sheet.save(OUT_PATH)
    print("Saved:", OUT_PATH, sheet.size)
    for k, v in statuses.items():
        if v != "ok":
            print("  !", k, "->", v)
    print("Total icons:", n, "| target:", len(IDS), "| ref:", len(REF_IDS))


if __name__ == "__main__":
    main()
