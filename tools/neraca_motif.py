"""neraca_motif.py — Neraca permintaan lawan suplai mesin motif.

Kenapa alat ini ada. Angka-angka di #6 ("permintaan 1.006 poin/hari", "median
suplai 0,78 poin/menit", "47,7% hidup di kasur") ditulis tangan sekali lalu
dikutip ulang di tiga tempat. Dua tiket sesudahnya membatalkannya — #9
menemukan motif tanpa suplai sama sekali, dan #10 menghidupkan cabang tidur
yang selama ini mati — dan tidak ada cara memeriksa mana yang masih benar
selain menurunkannya ulang dengan tangan lagi.

Alat ini membacanya dari KODE YANG JALAN: laju luruh dari `motives._decay_rate`,
suplai dari katalog `objects.OBJECT_INTERACTIONS`. Kalau salah satu berubah,
angkanya ikut berubah tanpa ada yang perlu ingat memperbaruinya.

    python tools/neraca_motif.py             # tidur 6 jam (pilihan #4)
    python tools/neraca_motif.py --tidur 8
"""
from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from game.motives import MOTIVES, Motives, SIM_MINUTES_PER_TICK   # noqa: E402
from game.objects import OBJECT_INTERACTIONS, OBJECT_NAMES        # noqa: E402

MENIT_SEHARI = 1440.0


def permintaan(jam_tidur: float, faktor: float = 1.0,
               nyaman_moodlet: bool = False) -> dict:
    """Poin per hari yang HILANG tiap motif, terjaga dan tidur dijumlahkan.

    Diukur pada motif = 0 (tengah rentang -100..+100). Itu penting untuk
    `lapar`, yang lajunya bergantung pada laparnya sendiri: di tengah rentang
    ia mewakili hari biasa, bukan kasus terbaik atau terburuk.

    Yang dihitung adalah luruh MENTAH, bukan yang benar-benar tercatat di
    motif — `add()` menjepit di -100, dan angka terjepit mengukur seberapa
    parah kekurangannya, bukan seberapa besar permintaannya.
    """
    menit_tidur = jam_tidur * 60.0
    menit_jaga = MENIT_SEHARI - menit_tidur

    out = {}
    for tidur, menit in ((False, menit_jaga), (True, menit_tidur)):
        mv = Motives()
        for m in MOTIVES:
            setattr(mv, m, 0.0)
        mv.asleep = tidur
        ticks = menit / SIM_MINUTES_PER_TICK
        for m in MOTIVES:
            out.setdefault(m, 0.0)
            laju = mv._decay_rate(m)
            if nyaman_moodlet and m == 'nyaman':
                laju = 0.0
            elif laju > 0:
                # Faktor hanya mengecilkan LURUH, bukan pemulihan: energi saat
                # tidur bertanda negatif di sini, dan mengalikannya berarti
                # "tidur jadi kurang memulihkan", yang bukan yang ditawarkan
                # knop B.
                laju *= faktor
            out[m] += laju * ticks
    return out


def suplai() -> dict:
    """Laju isi ulang terbaik per motif, poin per menit-sim.

    Satu interaksi memberi `delta` poin dalam `duration` menit, jadi laju
    efektifnya delta/duration. Yang dicatat: laju TERBAIK (pilihan optimal
    kalau perabotnya ada di dekat) dan seluruh daftarnya untuk median.
    """
    per_motif: dict[str, list] = {}
    for tile_id, daftar in OBJECT_INTERACTIONS.items():
        nama_obj = OBJECT_NAMES.get(tile_id, str(tile_id))
        for act in daftar:
            for ad in act.adverts:
                laju = ad.delta / max(1e-9, act.duration)
                per_motif.setdefault(ad.motive, []).append(
                    (laju, f'{act.name} ({nama_obj})', ad.delta, act.duration,
                     ad.minimum, act.autonomous))
    for v in per_motif.values():
        v.sort(key=lambda r: -r[0])
    return per_motif


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--tidur', type=float, default=6.0,
                    help='jam tidur per hari (pilihan #4: 6)')
    ap.add_argument('--luruh', type=float, default=1.0, metavar='FAKTOR',
                    help='kalikan SEMUA laju luruh (knop B di #6). '
                         '0.7 = luruh 30%% lebih lambat.')
    ap.add_argument('--nyaman-moodlet', action='store_true',
                    help='perlakukan Nyaman sebagai moodlet: tidak meluruh '
                         'sama sekali. objects.py sudah menyatakan ini niatnya '
                         '("Nyaman dan ruang ... akan menjadi moodlet") tapi '
                         'mesinnya masih meluruhkannya seperti kebutuhan, dan '
                         'itu permintaan TERBESAR di seluruh neraca.')
    args = ap.parse_args()

    dem = permintaan(args.tidur, args.luruh, args.nyaman_moodlet)
    sup = suplai()
    menit_jaga = MENIT_SEHARI - args.tidur * 60.0

    ubah = []
    if args.luruh != 1.0:
        ubah.append(f'luruh x{args.luruh:g}')
    if args.nyaman_moodlet:
        ubah.append('Nyaman = moodlet')
    print(f'Tidur {args.tidur:.1f} jam; terjaga {menit_jaga:.0f} menit-sim'
          + (f'; {", ".join(ubah)}.' if ubah else '.') + '\n')
    print(f'{"motif":>8} {"permintaan/hari":>16} {"suplai terbaik":>15} '
          f'{"menit/hari":>11}  sumber terbaik')
    print('-' * 86)

    total_dem = 0.0
    total_menit = 0.0
    tanpa_suplai = []
    for m in MOTIVES:
        d = dem[m]
        baris = sup.get(m) or []
        if d <= 0:
            # Motif yang NAIK sendiri (energi saat tidur masuk di sini kalau
            # tidurnya panjang) atau yang tidak meluruh sama sekali.
            print(f'{m:>8} {d:16.1f} {"—":>15} {"—":>11}  '
                  f'{"tidak meluruh" if d == 0 else "pulih sendiri"}')
            continue
        total_dem += d
        if not baris:
            tanpa_suplai.append(m)
            print(f'{m:>8} {d:16.1f} {"TIDAK ADA":>15} {"∞":>11}  '
                  f'nol interaksi mengiklankannya')
            continue
        laju, nama, delta, dur, mini, oto = baris[0]
        menit = d / laju
        total_menit += menit
        print(f'{m:>8} {d:16.1f} {laju:15.2f} {menit:11.0f}  '
              f'{nama} +{delta:g}/{dur:g}mnt')

    print('-' * 86)
    semua = [r[0] for v in sup.values() for r in v]
    print(f'permintaan total   : {total_dem:8.1f} poin/hari '
          f'(motif yang meluruh dan punya suplai)')
    print(f'laju yang dibutuhkan: {total_dem / menit_jaga:8.2f} poin/menit-sim '
          f'rata-rata sepanjang waktu bangun')
    print(f'median katalog     : {statistics.median(semua):8.2f} poin/menit-sim '
          f'({len(semua)} iklan di {len(OBJECT_INTERACTIONS)} perabot)')
    print(f'menit yang dibutuhkan: {total_menit:6.0f} dari {menit_jaga:.0f} '
          f'menit bangun = {100 * total_menit / menit_jaga:.1f}% hidup dipakai '
          f'mengurus motif')
    if tanpa_suplai:
        print(f'\nTANPA SUPLAI: {", ".join(tanpa_suplai)} — meluruh tiap hari '
              f'dan tidak ada satu pun interaksi yang mengiklankannya.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
