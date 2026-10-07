"""uji_langit.py — Jaga supaya kubah langit tidak pernah lagi keluar magenta.

Terikat pada kegagalan NYATA: scene `town` jam 13:00 merender pita langit
#FF00FF-an di sepanjang tepi atas layar. Dilaporkan sebagai "warna placeholder
tekstur hilang", padahal `_SKY_FRAG` di sky.py tidak punya sampler2D sama
sekali — tidak ada tekstur yang bisa gagal dimuat. Yang salah adalah DATA-nya:
tabel `_SKY_*` berisi warna placeholder norak untuk SETIAP waktu, dan jam 13
jatuh di `_SKY_DAY` yang horizon-nya (1.00, 0.50, 0.80) merah jambu pekat.
Suku haze di shader (`col += sky_horizon * haze`) menambah 18% warna itu lagi,
jadi kanal merah mentok 255 dan pitanya terbaca magenta.

Jam 7 lolos dari mata cuma karena kebetulan: ia jatuh di `_SKY_MORNING` yang
horizon-nya (0.20, 1.00, 0.80) — sama norak, tapi condong ke sian, dan sian
masih terbaca sebagai "langit" sekilas. Terukur: (81, 255, 255).

Patokan yang dipakai di sini bukan selera, tapi sifat langit sungguhan:

    HIJAU SELALU DI ANTARA MERAH DAN BIRU.

Langit apa pun — biru siang, jingga senja, kelabu mendung, nila malam —
adalah landaian mulus sepanjang spektrum. Hijau ada di tengah spektrum, jadi
nilainya selalu terjepit di antara merah dan biru. Warna yang melanggar ini
cuma bisa datang dari data yang dikarang:

  * hijau JATUH di bawah keduanya  -> magenta / merah jambu  (bug jam 13)
  * hijau NAIK di atas keduanya    -> sian / hijau neon      (bug jam 7)

Pemakaian:
    python tools/uji_langit.py

Keluar dengan kode 1 kalau ada yang GAGAL, supaya bisa dipakai di skrip.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from game import sky  # noqa: E402

# Kelonggaran satu kanal. Cukup untuk membiarkan langit malam yang sedikit
# nila (hijau boleh sedikit di bawah merah) tapi tidak cukup untuk
# meloloskan merah jambu 0.30 atau sian 0.80.
TOLERANSI = 0.06

# Diperiksa tiap setengah jam: cacat bisa bersembunyi di tengah interpolasi,
# bukan cuma di titik-titik palet yang ditulis tangan.
JAM_UJI = [h * 0.5 for h in range(48)]

CUACA = ('Cerah', 'Mendung', 'Hujan', 'Badai', 'Berangin')

NAMA_KANAL = ('zenith', 'horizon', 'sun_glow')


def _cek_warna(nama, jam, cuaca, rgb):
    """Kembalikan pesan kegagalan, atau None kalau warnanya masuk akal."""
    r, g, b = rgb
    gagal = []

    lantai = min(r, b) - TOLERANSI
    langit_langit = max(r, b) + TOLERANSI
    if g < lantai:
        gagal.append(
            f'hijau {g:.2f} JATUH di bawah merah {r:.2f} dan biru {b:.2f} '
            f'-> condong magenta')
    elif g > langit_langit:
        gagal.append(
            f'hijau {g:.2f} NAIK di atas merah {r:.2f} dan biru {b:.2f} '
            f'-> condong sian/hijau')

    for kanal, nilai in zip('rgb', rgb):
        if not (0.0 <= nilai <= 1.0):
            gagal.append(f'kanal {kanal} {nilai:.2f} di luar 0..1')

    if not gagal:
        return None
    return (f'{nama} jam {jam:04.1f} cuaca {cuaca}: '
            f'({r:.2f}, {g:.2f}, {b:.2f}) — ' + '; '.join(gagal))


def main() -> int:
    kegagalan = []
    for cuaca in CUACA:
        for jam in JAM_UJI:
            palet = sky._sky_palette(jam, cuaca)
            for nama, rgb in zip(NAMA_KANAL, palet[:3]):
                pesan = _cek_warna(nama, jam, cuaca, rgb)
                if pesan:
                    kegagalan.append(pesan)

    diperiksa = len(CUACA) * len(JAM_UJI) * len(NAMA_KANAL)
    if kegagalan:
        print(f'GAGAL — {len(kegagalan)} dari {diperiksa} warna langit '
              f'tidak mungkin ada di langit sungguhan:\n')
        for pesan in kegagalan[:20]:
            print(f'  {pesan}')
        if len(kegagalan) > 20:
            print(f'  ... dan {len(kegagalan) - 20} lagi')
        return 1

    print(f'LULUS — {diperiksa} warna langit diperiksa, semuanya masuk akal '
          f'(hijau selalu di antara merah dan biru).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
