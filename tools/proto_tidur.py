"""proto_tidur.py — PROTOTIPE SEKALI PAKAI. Bukan bagian dari game.

Menjawab satu pertanyaan dari tiket #10 "Tidur tidak melakukan apa pun pada
mesin motif": kalau cabang `asleep` DIHIDUPKAN, berapa permintaan sehari
yang sebenarnya, dan berapa jam tidur yang membuat energi impas?

CATATAN METODE — versi pertama prototipe ini salah, dan cara salahnya layak
ditulis. Ia menjalankan sehari peluruhan lalu membaca keadaan akhir. Semua
motif mentok di −100 karena clamp `MOTIVE_MIN`, jadi tiap jam tidur dari 4
sampai 6,25 menghasilkan angka yang sama persis: −100. Sapuan yang setiap
barisnya identik terlihat seperti data, padahal itu clamp yang sedang bicara,
bukan mesinnya. Yang diukur sekarang laju yang DIINTEGRASIKAN pada tingkat
motif yang ditahan tetap — tidak ada keadaan akhir, jadi tidak ada yang bisa
mentok.

Kenapa "permintaan" harus disebut bersama tingkatnya: `lapar` non-linear
(turun cepat saat kenyang, melambat saat lapar) dan `kandung` terkopel
padanya lewat satu-satunya kopling antar-motif di mesin ini. Jadi "poin per
hari" tidak punya satu nilai. Menyebut satu angka tanpa menyebut tingkatnya
adalah angka yang tidak bisa diperiksa ulang.

Tidak menyentuh renderer: mesin motif berdiri sendiri, jadi tidak ada Game3D
dan tidak ada xvfb. Hasilnya persis dan berulang.

Yang TIDAK dijawab, dan itu disengaja: apa yang terjadi kalau sim juga
mengerjakan interaksi. Ini lantai permintaannya, bukan simulasi hari lengkap.

Dibuang setelah #10 ditutup.

    python tools/proto_tidur.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from game.motives import (  # noqa: E402
    MOTIVES, LABELS, Motives, SIM_MINUTES_PER_TICK,
    ENERGY_AWAKE, ENERGY_SLEEP_GAIN,
)

TICK_SEHARI = 1440.0 / SIM_MINUTES_PER_TICK        # 720


def permintaan(level: float, jam_tidur: float, *, asleep_hidup: bool) -> dict:
    """Poin/hari yang harus ditutup interaksi, tiap motif ditahan di `level`.

    Menahan tingkatnya tetap adalah intinya: itu membuat pertanyaannya
    "berapa yang harus dipasok untuk MEMPERTAHANKAN keadaan ini", yang punya
    jawaban tunggal — alih-alih "di mana ia berakhir", yang jawabannya selalu
    lantai.
    """
    mv = Motives()
    for m in MOTIVES:
        setattr(mv, m, level)

    t_tidur = jam_tidur * 60.0 / SIM_MINUTES_PER_TICK
    t_bangun = TICK_SEHARI - t_tidur

    out = {}
    for m in MOTIVES:
        mv.asleep = asleep_hidup
        laju_tidur = mv._decay_rate(m)
        mv.asleep = False
        laju_bangun = mv._decay_rate(m)
        out[m] = laju_tidur * t_tidur + laju_bangun * t_bangun
    return out


def jam_impas_energi() -> float:
    """Jam tidur yang membuat energi impas. Analitik — lajunya tidak
    bergantung keadaan, jadi simulasi tidak menambah apa pun."""
    # ENERGY_SLEEP_GAIN * (S*30 tick) == ENERGY_AWAKE * ((24-S)*30 tick)
    return 24.0 * ENERGY_AWAKE / (ENERGY_SLEEP_GAIN + ENERGY_AWAKE)


def main():
    JAM = 6.0
    print()
    print(f'Tidur {JAM:.0f} jam — angka yang sudah diputuskan di #4.')
    print(f'Jam impas energi (analitik): {jam_impas_energi():.2f} jam')
    print()

    for level, sebut in ((0.0, 'netral (semua motif 0)'),
                         (50.0, 'terpelihara (semua motif +50)')):
        print(f'PERMINTAAN SEHARI pada tingkat {sebut}')
        print(f'  {"motif":12s} {"asleep MATI":>12s} {"asleep HIDUP":>13s} '
              f'{"selisih":>9s}')
        print('  ' + '-' * 50)
        mati = permintaan(level, JAM, asleep_hidup=False)
        hidup = permintaan(level, JAM, asleep_hidup=True)
        tot_m = tot_h = 0.0
        for m in MOTIVES:
            a, b = mati[m], hidup[m]
            tot_m += max(a, 0.0)
            tot_h += max(b, 0.0)
            tanda = ''
            if b <= 0.0 < a:
                tanda = '  <-- tidak lagi menuntut'
            print(f'  {LABELS[m]:12s} {a:12.1f} {b:13.1f} {b - a:+9.1f}{tanda}')
        print('  ' + '-' * 50)
        print(f'  {"TOTAL":12s} {tot_m:12.1f} {tot_h:13.1f} '
              f'{tot_h - tot_m:+9.1f}')
        print()

    # Laju yang dibutuhkan, memakai kelonggaran 30% yang diputuskan di #4.
    menit_bangun = (24.0 - JAM) * 60.0
    menit_andal = menit_bangun * 0.70
    for level in (0.0, 50.0):
        for sebut, d in (('asleep MATI ', permintaan(level, JAM, asleep_hidup=False)),
                         ('asleep HIDUP', permintaan(level, JAM, asleep_hidup=True))):
            tot = sum(v for v in d.values() if v > 0)
            print(f'  tingkat {level:+5.0f}  {sebut}  permintaan {tot:7.1f} '
                  f'poin/hari  ->  {tot / menit_andal:.2f} poin/menit '
                  f'(median katalog 0,78)')
    print()


if __name__ == '__main__':
    main()
