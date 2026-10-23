"""buat_save_ladang.py — tulis ulang `ladang_hari10_save.json` dari save regresi.

Patokan `farm_wide` memotret ladang yang SEDANG DIGARAP: petak dicangkul,
ditanami, sebagian disiram. Save regresi adalah hari pertama, jadi ladangnya
tanah kosong. Membandingkan hari pertama kita dengan pertengahan musim
mereka bukan adu yang adil, dan kritikus akan (dengan benar) menghukum
"ladang terbaca sebagai lantai kosong" padahal yang dipotret memang belum
pernah dicangkul.

Isinya keadaan yang bisa dicapai pemain: tanaman musim Semi, dibuat lewat
`plant_payload()` yang juga dipakai saat menanam di game, dengan umur
berbeda-beda supaya tiap tahap tumbuh terlihat. Tidak ada medan yang
mustahil di game asli.

    python tools/fixtures/buat_save_ladang.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from game.crops import plant_payload, spec  # noqa: E402

SUMBER = ROOT / 'tools' / 'fixtures' / 'regress_save.json'
TUJUAN = ROOT / 'tools' / 'fixtures' / 'ladang_hari10_save.json'

# Ladang farm: x 8..23, y 11..18 (lihat game/scenes/farm.py). Petak ditanam
# per baris berselang supaya ada jalan setapak di antaranya, seperti cara
# pemain menanam supaya bisa lewat untuk menyiram.
BARIS = {
    12: 'padi', 13: 'lobak',
    14: 'stroberi', 16: 'wortel',
    17: 'stroberi', 18: 'kacang_panjang',
}
X_MULAI, X_SELESAI = 9, 21


def main():
    d = json.loads(SUMBER.read_text(encoding='utf-8'))
    soil = {}
    for y, cid in BARIS.items():
        hari = spec(cid).get('days', 3)
        for x in range(X_MULAI, X_SELESAI + 1):
            p = plant_payload(cid)
            # Umur menyebar dari setengah jalan sampai siap panen di sepanjang
            # baris: hari ke-10 musim, kebanyakan tanaman sudah besar, dan satu
            # tangkapan tetap memperlihatkan beberapa tahap.
            p['age'] = round(hari * (0.5 + 0.5 * (x - X_MULAI) / (X_SELESAI - X_MULAI)), 2)
            p['watered'] = (x % 3) != 0
            soil[f'{x},{y},farm'] = p
        # Satu petak di ujung baris dicangkul tapi belum ditanami.
        soil[f'{X_SELESAI + 1},{y},farm'] = {'tilled': True, 'kering': 0}
    d['soil'] = soil
    d['day'] = d['day_in_season'] = 10
    d['player_x'], d['player_y'] = 15.0, 15.0   # di lorong tengah ladang
    TUJUAN.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(soil)} petak -> {TUJUAN.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
