"""anim_trace.py — Ubah jejak rekaman jadi angka yang bisa dibantah.

Kritik animasi biasanya berhenti di "kurang hidup". Itu tidak bisa ditindak
lanjuti dan tidak bisa dibantah. Modul ini mengukur enam sifat yang membedakan
gerakan yang dianimasikan dari gerakan yang cuma di-lerp, langsung dari
`*_trace.json` keluaran tools/record.py:

  rentang       berapa derajat sendi benar-benar bergerak
  antisipasi    gerakan BERLAWANAN arah sebelum ayunan utama, dalam derajat & ms
                (tanpa ini, aksi mulai dari nol — mata membacanya sebagai kaku)
  tahanan       berapa ms pose puncak bertahan di dalam 10% dari puncak
                (nol = pose puncak cuma disinggung, bukan dibaca)
  ikutan        overshoot: apakah lintasan lewat dari nilai diam lalu balik
  ease          rasio kecepatan puncak terhadap kecepatan rata-rata.
                Segitiga linier = 1,00. Manusia dan animator = 1,4-2,2.
  sekunder      jeda (ms) antara sendi penggerak dan sendi pengikut, dihitung
                dari korelasi silang. Nol berarti semua bagian badan bergerak
                di frame yang sama — tanda paling jelas rig yang mati.

Plus, untuk aksi berulang (menyikat, memerah):

  stroke        jumlah pembalikan arah — berapa kali sapuan benar-benar terjadi
  irama         simpangan baku jarak antar-sapuan (0 = metronom, mesin;
                sedikit variasi = tangan)

Pemakaian:
    python tools/anim_trace.py _bench/clips/gosok_trace.json
    python tools/anim_trace.py a_trace.json b_trace.json     # bandingkan
    python tools/anim_trace.py x_trace.json --json           # untuk skrip
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path


# ── utilitas deret ───────────────────────────────────────────────────────────
def _series(frames: list[dict], key: str) -> list[float]:
    return [float(f.get(key, 0.0) or 0.0) for f in frames]


def _deriv(xs: list[float], dt: float) -> list[float]:
    return [(xs[i + 1] - xs[i]) / dt for i in range(len(xs) - 1)] or [0.0]


def _active_window(xs: list[float], eps: float = 0.5) -> tuple[int, int]:
    """Bagian deret yang benar-benar bergerak, dipangkas dari kedua ujung."""
    rest = xs[0]
    lo = 0
    while lo < len(xs) - 1 and abs(xs[lo] - rest) < eps:
        lo += 1
    hi = len(xs) - 1
    tail = xs[-1]
    while hi > lo and abs(xs[hi] - tail) < eps:
        hi -= 1
    return lo, max(lo + 1, hi)


# ── ukuran per sendi ─────────────────────────────────────────────────────────
def measure(xs: list[float], fps: float) -> dict:
    dt = 1.0 / fps
    n = len(xs)
    if n < 4:
        return {'rentang': 0.0}

    rest = xs[0]
    rentang = max(xs) - min(xs)
    if rentang < 0.5:
        return {'rentang': round(rentang, 2), 'diam': True}

    lo, hi = _active_window(xs)
    seg = xs[lo:hi + 1]
    if len(seg) < 3:
        seg, lo, hi = xs, 0, n - 1

    # arah utama: ke ekstrem terjauh dari nilai diam
    i_pk = max(range(len(seg)), key=lambda i: abs(seg[i] - rest))
    puncak = seg[i_pk]
    arah = 1.0 if puncak > rest else -1.0

    # ── antisipasi: simpangan berlawanan arah SEBELUM puncak ────────────────
    ant_deg, ant_ms = 0.0, 0.0
    pre = seg[:i_pk + 1]
    if pre:
        lawan = [(rest - v) * arah for v in pre]      # positif = berlawanan
        ant_deg = max(0.0, max(lawan))
        ant_ms = sum(1 for v in lawan if v > 0.15 * max(1e-6, ant_deg)) * dt * 1000.0
        if ant_deg < 0.3:
            ant_deg, ant_ms = 0.0, 0.0

    # ── tahanan: frame di dalam 10% dari puncak ─────────────────────────────
    amp = abs(puncak - rest)
    dekat = [v for v in seg if abs(v - puncak) <= 0.10 * amp]
    tahan_ms = len(dekat) * dt * 1000.0

    # ── ikutan: melewati nilai akhir lalu balik ─────────────────────────────
    akhir = xs[-1]
    ekor = seg[i_pk:]
    over = 0.0
    if len(ekor) > 2:
        lewat = [(akhir - v) * arah for v in ekor]    # positif = lewat dari akhir
        over = max(0.0, max(lewat))
        if over < 0.3:
            over = 0.0

    # ── ease: kecepatan puncak / kecepatan rata-rata ────────────────────────
    v = [abs(x) for x in _deriv(seg, dt)]
    v_mean = statistics.fmean(v) if v else 0.0
    ease = (max(v) / v_mean) if v_mean > 1e-6 else 0.0

    # ── stroke: pembalikan arah yang berarti ────────────────────────────────
    dv = _deriv(seg, dt)
    amb = 0.06 * max(abs(x) for x in dv) if dv else 0.0
    tanda, balik, idx_balik = 0, 0, []
    for i, s in enumerate(dv):
        if abs(s) < amb:
            continue
        t = 1 if s > 0 else -1
        if tanda and t != tanda:
            balik += 1
            idx_balik.append(i)
        tanda = t
    irama = 0.0
    if len(idx_balik) >= 3:
        jarak = [(idx_balik[i + 1] - idx_balik[i]) * dt * 1000.0
                 for i in range(len(idx_balik) - 1)]
        irama = statistics.pstdev(jarak)

    return {
        'rentang': round(rentang, 2),
        'durasi_ms': round((hi - lo + 1) * dt * 1000.0, 1),
        'antisipasi_deg': round(ant_deg, 2),
        'antisipasi_ms': round(ant_ms, 1),
        'tahan_ms': round(tahan_ms, 1),
        'ikutan_deg': round(over, 2),
        'ease': round(ease, 3),
        'stroke': balik,
        'irama_sd_ms': round(irama, 1),
    }


def _lag_ms(a: list[float], b: list[float], fps: float, max_lag: int = 20) -> float:
    """Jeda sendi b terhadap a lewat korelasi silang. Positif = b terlambat."""
    def norm(xs):
        m = statistics.fmean(xs)
        s = statistics.pstdev(xs) or 1.0
        return [(x - m) / s for x in xs]
    if len(a) < 8 or len(b) < 8:
        return 0.0
    if (max(a) - min(a)) < 0.5 or (max(b) - min(b)) < 0.5:
        return 0.0
    A, B = norm(a), norm(b)
    best, best_lag = -9e9, 0
    for lag in range(-max_lag, max_lag + 1):
        acc, cnt = 0.0, 0
        for i in range(len(A)):
            j = i + lag
            if 0 <= j < len(B):
                acc += A[i] * B[j]
                cnt += 1
        if cnt >= 8:
            c = acc / cnt
            if c > best:
                best, best_lag = c, lag
    return round(best_lag * 1000.0 / fps, 1)


# ── laporan ──────────────────────────────────────────────────────────────────
PENTING = ('bahu_r.rotation_x', 'bahu_l.rotation_x', 'siku_r.rotation_x',
           'badan.rotation_x', 'badan.rotation_z', 'badan.y',
           'leher.rotation_x', 'leher.rotation_y',
           'lutut_r.rotation_x', 'lutut_l.rotation_x')


def analyse(path: Path) -> dict:
    data = json.loads(path.read_text(encoding='utf-8'))
    frames = data.get('frames', [])
    fps = float(data.get('fps', 30))
    keys = [k for k in PENTING if any(k in f for f in frames)]

    per: dict[str, dict] = {}
    for k in keys:
        m = measure(_series(frames, k), fps)
        if not m.get('diam'):
            per[k] = m

    # penggerak = sendi dengan rentang terbesar
    urut = sorted(per.items(), key=lambda kv: -kv[1]['rentang'])
    penggerak = urut[0][0] if urut else None
    jeda = {}
    if penggerak:
        a = _series(frames, penggerak)
        for k, _ in urut[1:]:
            jeda[k] = _lag_ms(a, _series(frames, k), fps)

    return {
        'berkas': path.name,
        'fps': fps,
        'n_frame': len(frames),
        'durasi_s': round(len(frames) / fps, 2) if fps else 0,
        'penggerak': penggerak,
        'sendi': per,
        'jeda_sekunder_ms': jeda,
        'marks': data.get('marks', {}),
    }


def cetak(rep: dict) -> None:
    print(f"\n── {rep['berkas']} · {rep['n_frame']} frame · "
          f"{rep['durasi_s']}s @ {rep['fps']}fps")
    if not rep['sendi']:
        print('   TIDAK ADA SENDI YANG BERGERAK. Aksi ini tidak dianimasikan.')
        return
    print(f"   penggerak: {rep['penggerak']}")
    hdr = (f"   {'sendi':22s} {'rentang':>8s} {'durasi':>7s} {'antisip':>8s} "
           f"{'tahan':>6s} {'ikutan':>7s} {'ease':>6s} {'strok':>6s} {'jeda':>6s}")
    print(hdr)
    print('   ' + '-' * (len(hdr) - 3))
    for k, m in sorted(rep['sendi'].items(), key=lambda kv: -kv[1]['rentang']):
        print(f"   {k:22s} {m['rentang']:8.1f} {m['durasi_ms']:6.0f}m "
              f"{m['antisipasi_deg']:5.1f}/{m['antisipasi_ms']:<3.0f} "
              f"{m['tahan_ms']:5.0f} {m['ikutan_deg']:7.1f} {m['ease']:6.2f} "
              f"{m['stroke']:6d} {rep['jeda_sekunder_ms'].get(k, 0.0):6.0f}")
    print('   (antisip = derajat/ms gerakan berlawanan sebelum ayunan; '
          'ease 1,00 = segitiga linier)')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('traces', nargs='+')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()

    reps = [analyse(Path(t)) for t in args.traces]
    if args.json:
        print(json.dumps(reps, ensure_ascii=False, indent=1))
        return
    for r in reps:
        cetak(r)
    if len(reps) == 2:
        a, b = reps
        print(f"\n── selisih {a['berkas']} -> {b['berkas']}")
        for k in sorted(set(a['sendi']) | set(b['sendi'])):
            ma, mb = a['sendi'].get(k, {}), b['sendi'].get(k, {})
            for f in ('rentang', 'antisipasi_deg', 'tahan_ms', 'ikutan_deg', 'ease'):
                va, vb = ma.get(f, 0.0), mb.get(f, 0.0)
                if abs(vb - va) > 0.25:
                    print(f"   {k:22s} {f:15s} {va:8.2f} -> {vb:8.2f}"
                          f"  ({vb - va:+.2f})")


if __name__ == '__main__':
    sys.exit(main())
