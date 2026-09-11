"""progress_page.py — Bangun halaman progres langsung dari bukti di _bench/.

Membaca:
  _bench/slices.json      daftar slice (kalau sudah ada)
  _bench/progress.jsonl   satu event JSON per baris
  _bench/sheets/*.png     lembar perbandingan A/B
  _bench/shots/*.png      tangkapan layar mentah

Menulis:
  _bench/progress.html    halaman mandiri (gambar di-embed base64)

Dipakai orkestrator: python tools/progress_page.py, lalu publish sebagai Artifact.
"""
from __future__ import annotations

import base64
import html
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
BENCH = ROOT / '_bench'
THUMB_W = 760
THUMB_Q = 70


# ── data ────────────────────────────────────────────────────────────────

def load_slices() -> list[dict]:
    p = BENCH / 'slices.json'
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        return []
    return data if isinstance(data, list) else data.get('slices', [])


def load_events() -> list[dict]:
    p = BENCH / 'progress.jsonl'
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding='utf-8', errors='replace').splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except Exception:
            continue
        if isinstance(ev, dict):
            out.append(ev)
    return out


def thumb(path: Path, width: int = THUMB_W) -> str | None:
    """Kecilkan gambar jadi data URI JPEG. None kalau gagal."""
    try:
        im = Image.open(path)
    except Exception:
        return None
    im = im.convert('RGB')
    if im.width > width:
        im = im.resize((width, max(1, round(im.height * width / im.width))),
                       Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, 'JPEG', quality=THUMB_Q, optimize=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()


def clip_uri(path: Path, budget_mb: float = 3.0) -> str | None:
    """Sisipkan mp4 sebagai data URI. None kalau terlalu besar atau gagal.

    Halaman ini untuk DITONTON — animasi tidak bisa dinilai dari gambar diam,
    dan itu berlaku juga untuk pemiliknya, bukan cuma untuk juri."""
    try:
        raw = path.read_bytes()
    except Exception:
        return None
    if len(raw) > budget_mb * 1024 * 1024:
        return None
    return 'data:video/mp4;base64,' + base64.b64encode(raw).decode()


def newest(pattern: str) -> Path | None:
    hits = sorted(BENCH.glob(pattern), key=lambda p: p.stat().st_mtime)
    return hits[-1] if hits else None


# ── model ───────────────────────────────────────────────────────────────

def build_model():
    slices = load_slices()
    events = load_events()

    by_slice: dict[str, list[dict]] = {}
    for ev in events:
        by_slice.setdefault(str(ev.get('slice', '?')), []).append(ev)

    # Slice yang punya event tapi tidak terdaftar tetap ditampilkan.
    known = {str(s.get('id')) for s in slices}
    for sid in by_slice:
        if sid not in known and sid != '?':
            slices.append({'id': sid, 'title': sid, 'goal': '', 'kind': ''})

    rows = []
    for s in slices:
        sid = str(s.get('id', '?'))
        evs = by_slice.get(sid, [])
        verdicts = [e for e in evs if e.get('role') == 'judge'
                    and e.get('verdict') in ('ours', 'bar')]
        rounds = []
        for e in verdicts:
            rounds.append({
                'round': e.get('round'),
                'won': e.get('verdict') == 'ours',
                'gap': e.get('gap') or '',
            })
        won = bool(rounds) and rounds[-1]['won']
        sheet = newest(f'sheets/{sid}*.png') or newest(f'sheets/{sid}*.jpg')
        shot = newest(f'shots/{sid}*.png')
        clip = newest(f'clips/{sid}.mp4') or newest(f'clips/{sid}_*.mp4')
        strip = newest(f'clips/{sid}_strip.png') or newest(f'clips/{sid}_*_strip.png')
        rows.append({
            'id': sid,
            'title': s.get('title') or sid,
            'goal': s.get('goal') or '',
            'kind': (s.get('kind') or '').lower(),
            'bar': s.get('bar_image') or '',
            'question': s.get('judge_question') or '',
            'rounds': rounds,
            'won': won,
            'open_gap': '' if won else (rounds[-1]['gap'] if rounds else ''),
            'sheet': thumb(sheet) if sheet else None,
            'sheet_name': sheet.name if sheet else '',
            'clip': clip_uri(clip) if clip else None,
            'clip_name': clip.name if clip else '',
            'strip': thumb(strip) if strip else None,
            'strip_name': strip.name if strip else '',
            'shot': thumb(shot, 560) if (shot and not sheet) else None,
            'events': len(evs),
        })

    notes = [e for e in events if e.get('role') == 'note' or e.get('note')]
    return rows, notes[-14:], events


# ── render ──────────────────────────────────────────────────────────────

CSS = """
:root{
  --void:#FBF7E8; --surface:#F2EBD6; --edge:#D8C89B;
  --ink:#12251F; --ink-soft:#4A6459; --ink-faint:#7C9086;
  --bronze:#8A6428; --bronze-hi:#C79B45;
  --teal:#0E6B4F; --teal-hi:#12867A;
  --pink:#C4536F;
  --shadow:0 1px 0 rgba(18,37,31,.06);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --void:#07120F; --surface:#0D1E19; --edge:#1E3A31;
    --ink:#E9F1EA; --ink-soft:#8FAFA4; --ink-faint:#5C7A72;
    --bronze:#C79B45; --bronze-hi:#EBD08A;
    --teal:#3FB3A0; --teal-hi:#6FD8C4;
    --pink:#E77E9A;
    --shadow:0 1px 0 rgba(0,0,0,.4);
  }
}
:root[data-theme="dark"]{
  --void:#07120F; --surface:#0D1E19; --edge:#1E3A31;
  --ink:#E9F1EA; --ink-soft:#8FAFA4; --ink-faint:#5C7A72;
  --bronze:#C79B45; --bronze-hi:#EBD08A;
  --teal:#3FB3A0; --teal-hi:#6FD8C4;
  --pink:#E77E9A;
  --shadow:0 1px 0 rgba(0,0,0,.4);
}

figure video{width:100%;border:1px solid var(--edge);border-radius:3px;display:block;background:#000}
.banner{
  border:1px solid var(--bronze); border-left-width:4px; border-radius:3px;
  background:var(--surface); padding:14px 16px; margin:26px 0 8px;
}
.banner .k{
  display:block; font-family:"IBM Plex Mono",ui-monospace,monospace;
  font-size:10px; letter-spacing:.15em; text-transform:uppercase;
  color:var(--bronze); margin-bottom:4px;
}
.banner b{display:block;margin-bottom:5px}
.banner p{margin:0;color:var(--ink-soft);max-width:74ch}

*{box-sizing:border-box}
body{
  margin:0; background:var(--void); color:var(--ink);
  font-family:"IBM Plex Sans","Segoe UI",system-ui,sans-serif;
  font-size:15px; line-height:1.55;
  -webkit-font-smoothing:antialiased;
}
.wrap{max-width:1080px;margin:0 auto;padding:48px 28px 96px}

/* ── masthead ─────────────────────────────────────── */
.mast{display:flex;gap:28px;align-items:flex-start;margin-bottom:8px}
.seal{flex:0 0 96px;width:96px;height:96px}
.mast h1{
  font-family:"Bodoni Moda",Didot,"Times New Roman",serif;
  font-weight:600; font-size:clamp(30px,4.6vw,46px); line-height:1.04;
  margin:2px 0 6px; text-wrap:balance; letter-spacing:-.01em;
}
.mast .sub{color:var(--ink-soft);max-width:60ch;margin:0}
.stamp{
  display:inline-block;margin-top:12px;
  font-family:"IBM Plex Mono",ui-monospace,monospace;
  font-size:11px;letter-spacing:.14em;text-transform:uppercase;
  color:var(--bronze);border:1px solid var(--edge);
  padding:4px 9px;border-radius:2px;
}

/* ── console strip ────────────────────────────────── */
.console{
  display:grid;grid-template-columns:repeat(auto-fit,minmax(132px,1fr));
  gap:1px;background:var(--edge);border:1px solid var(--edge);
  border-radius:3px;overflow:hidden;margin:34px 0 8px;
}
.cell{background:var(--surface);padding:13px 15px}
.cell .k{
  font-family:"IBM Plex Mono",ui-monospace,monospace;
  font-size:10px;letter-spacing:.15em;text-transform:uppercase;
  color:var(--ink-faint);display:block;margin-bottom:3px;
}
.cell .v{
  font-family:"IBM Plex Mono",ui-monospace,monospace;
  font-size:26px;font-variant-numeric:tabular-nums;line-height:1.1;
  color:var(--ink);
}
.cell .v.ours{color:var(--teal)}
.cell .v.open{color:var(--bronze)}

.legend{
  font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:11px;
  color:var(--ink-faint);letter-spacing:.04em;margin:0 0 40px;
}
.legend b{color:var(--teal);font-weight:500}
.legend i{color:var(--bronze);font-style:normal}

/* ── slice ladder ─────────────────────────────────── */
h2.sec{
  font-family:"IBM Plex Mono",ui-monospace,monospace;
  font-size:11px;letter-spacing:.2em;text-transform:uppercase;
  color:var(--ink-faint);font-weight:500;
  border-top:1px solid var(--edge);padding-top:12px;margin:0 0 20px;
}
.slice{
  border:1px solid var(--edge);border-radius:3px;background:var(--surface);
  margin-bottom:14px;box-shadow:var(--shadow);overflow:hidden;
}
.slice.won{border-color:color-mix(in srgb,var(--teal) 45%,var(--edge))}
.head{display:flex;gap:16px;align-items:baseline;padding:16px 18px 12px;flex-wrap:wrap}
.sid{
  font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:12px;
  color:var(--bronze);letter-spacing:.08em;flex:0 0 auto;
}
.stitle{
  font-family:"Bodoni Moda",Didot,serif;font-weight:600;
  font-size:19px;line-height:1.2;flex:1 1 260px;margin:0;
}
.chip{
  font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:10px;
  letter-spacing:.12em;text-transform:uppercase;
  border:1px solid var(--edge);padding:2px 7px;border-radius:2px;
  color:var(--ink-faint);flex:0 0 auto;
}
.pill{
  font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:10px;
  letter-spacing:.12em;text-transform:uppercase;padding:3px 9px;
  border-radius:2px;flex:0 0 auto;font-weight:500;
}
.pill.ours{background:var(--teal);color:var(--void)}
.pill.bar{background:transparent;color:var(--bronze);border:1px solid var(--bronze)}
.pill.idle{color:var(--ink-faint);border:1px solid var(--edge)}

.body{padding:0 18px 18px}
.goal{color:var(--ink-soft);margin:0 0 12px;max-width:68ch}
.qn{
  font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:12px;
  color:var(--ink-faint);border-left:2px solid var(--edge);
  padding-left:12px;margin:0 0 14px;max-width:70ch;
}
.dots{display:flex;gap:6px;align-items:center;margin:0 0 12px;flex-wrap:wrap}
.dot{
  width:22px;height:22px;border-radius:50%;display:grid;place-items:center;
  font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:10px;
  border:1px solid var(--bronze);color:var(--bronze);
}
.dot.won{background:var(--teal);border-color:var(--teal);color:var(--void)}
.dots .lbl{
  font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:10px;
  letter-spacing:.14em;text-transform:uppercase;color:var(--ink-faint);
  margin-right:4px;
}
.gap{
  border-left:2px solid var(--pink);padding:2px 0 2px 12px;
  color:var(--ink);margin:0 0 14px;max-width:70ch;
}
.gap .k{
  font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:10px;
  letter-spacing:.14em;text-transform:uppercase;color:var(--pink);
  display:block;
}
figure{margin:0}
figure img{width:100%;height:auto;display:block;border:1px solid var(--edge);border-radius:2px}
figcaption{
  font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:10px;
  color:var(--ink-faint);letter-spacing:.08em;margin-top:6px;
}
.empty{
  color:var(--ink-faint);font-family:"IBM Plex Mono",ui-monospace,monospace;
  font-size:12px;border:1px dashed var(--edge);border-radius:3px;
  padding:22px;text-align:center;
}
.log{
  font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:12px;
  border:1px solid var(--edge);border-radius:3px;background:var(--surface);
  padding:14px 16px;overflow-x:auto;
}
.log div{white-space:nowrap;color:var(--ink-soft);padding:1px 0}
.log b{color:var(--bronze);font-weight:400}
footer{
  margin-top:44px;border-top:1px solid var(--edge);padding-top:14px;
  font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:11px;
  color:var(--ink-faint);
}
@media (prefers-reduced-motion:no-preference){
  .seal .ring{transform-origin:50% 50%;animation:turn 64s linear infinite}
  @keyframes turn{to{transform:rotate(360deg)}}
}
"""

SEAL = """
<svg class="seal" viewBox="0 0 100 100" role="img" aria-label="Segel entitas">
  <g class="ring" fill="none" stroke="var(--bronze)" stroke-width="1.6">
    <circle cx="50" cy="50" r="40"/>
    <circle cx="50" cy="50" r="31" stroke-width="1"/>
    {teeth}
  </g>
  <g fill="none" stroke="var(--teal)" stroke-width="1.8" stroke-linecap="square">
    <path d="M50 78 V44"/><path d="M50 68 H36 V60"/><path d="M50 60 H64 V52"/>
    <path d="M50 52 H40 V46"/>
  </g>
  <ellipse cx="50" cy="34" rx="7" ry="12" fill="none" stroke="var(--teal)" stroke-width="1.6"/>
  <circle cx="50" cy="32" r="4.2" fill="none" stroke="var(--teal-hi)" stroke-width="1.4"/>
  <circle cx="50" cy="32" r="1.5" fill="var(--ink)"/>
</svg>
"""


def seal_svg(done: int, total: int) -> str:
    import math
    n = 24
    lit = 0 if total <= 0 else round(n * done / total)
    parts = []
    for i in range(n):
        a = 2 * math.pi * i / n - math.pi / 2
        x1, y1 = 50 + 40 * math.cos(a), 50 + 40 * math.sin(a)
        x2, y2 = 50 + 46 * math.cos(a), 50 + 46 * math.sin(a)
        col = 'var(--teal)' if i < lit else 'var(--bronze)'
        w = 3.2 if i < lit else 1.6
        parts.append(f'<path d="M{x1:.1f} {y1:.1f} L{x2:.1f} {y2:.1f}" '
                     f'stroke="{col}" stroke-width="{w}"/>')
    return SEAL.replace('{teeth}', ''.join(parts))


def render() -> str:
    rows, notes, events = build_model()
    total = len(rows)
    won = sum(1 for r in rows if r['won'])
    open_ = total - won
    attempts = sum(len(r['rounds']) for r in rows)
    stamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    out = [f'<title>Karsa Bench</title>',
           '<link rel="preconnect" href="https://fonts.googleapis.com">',
           '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
           '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
           'family=Bodoni+Moda:opsz,wght@6..96,500;6..96,600&'
           'family=IBM+Plex+Mono:wght@400;500&'
           'family=IBM+Plex+Sans:wght@400;500&display=swap">',
           f'<style>{CSS}</style>',
           '<div class="wrap">']

    out.append('<header class="mast">')
    out.append(seal_svg(won, max(total, 1)))
    out.append('<div>')
    out.append('<h1>Karsa Bench — Ternak &amp; Animasi</h1>')
    out.append('<p class="sub">Memelihara ternak di Lembah Karsa 3D: beri minum, '
               'gosok, panen, bicara. Patokannya <i>Story of Seasons: A '
               'Wonderful Life</i> (remake 2023). Tiap bagian direkam sebagai '
               'klip dari game yang benar-benar jalan — bukan mockup — lalu '
               'dinilai. Bagian selesai hanya kalau juri yang tidak tahu mana '
               'milik kita tetap memilih milik kita.</p>')
    out.append(f'<span class="stamp">diperbarui {stamp}</span>')
    out.append('</div></header>')

    out.append('<div class="console">')
    for k, v, cls in (('Bagian', total, ''),
                      ('Menang buta', won, 'ours'),
                      ('Masih kalah', open_, 'open'),
                      ('Ronde dinilai', attempts, ''),
                      ('Peristiwa', len(events), '')):
        out.append(f'<div class="cell"><span class="k">{k}</span>'
                   f'<span class="v {cls}">{v}</span></div>')
    out.append('</div>')
    out.append('<p class="legend">Titik ronde: <b>hijau</b> = juri buta '
               'memilih milik kita &nbsp;·&nbsp; <i>perunggu</i> = juri memilih '
               'tangkapan layar aslinya, bagian dikembalikan ke pembangun.</p>')

    st = BENCH / 'bar' / 'STATUS.md'
    if st.exists():
        teks = st.read_text(encoding='utf-8', errors='replace').strip()
        judul, _, isi = teks.partition('\n')
        out.append('<div class="banner"><span class="k">Status patokan</span>'
                   f'<b>{html.escape(judul.lstrip("# ").strip())}</b>'
                   f'<p>{html.escape(isi.strip())}</p></div>')

    out.append('<h2 class="sec">Bagian</h2>')
    if not rows:
        out.append('<div class="empty">Pemetaan bagian belum selesai. '
                   'Agen recon masih membaca kode, logo, dan kedua rujukan.</div>')
    for r in rows:
        cls = 'slice won' if r['won'] else 'slice'
        out.append(f'<article class="{cls}">')
        out.append('<div class="head">')
        out.append(f'<span class="sid">{html.escape(r["id"])}</span>')
        out.append(f'<h3 class="stitle">{html.escape(r["title"])}</h3>')
        if r['kind']:
            out.append(f'<span class="chip">{html.escape(r["kind"])}</span>')
        if r['won']:
            out.append('<span class="pill ours">menang buta</span>')
        elif r['rounds']:
            out.append('<span class="pill bar">masih kalah</span>')
        else:
            out.append('<span class="pill idle">belum dinilai</span>')
        out.append('</div><div class="body">')
        if r['goal']:
            out.append(f'<p class="goal">{html.escape(r["goal"])}</p>')
        if r['question']:
            out.append(f'<p class="qn">Pertanyaan juri — {html.escape(r["question"])}</p>')
        if r['rounds']:
            out.append('<div class="dots"><span class="lbl">Ronde</span>')
            for i, rd in enumerate(r['rounds'], 1):
                c = 'dot won' if rd['won'] else 'dot'
                out.append(f'<span class="{c}" title="ronde {rd["round"] or i}">{i}</span>')
            out.append('</div>')
        if r['open_gap']:
            out.append('<p class="gap"><span class="k">Celah terbesar</span>'
                       f'{html.escape(r["open_gap"])}</p>')
        if r['clip']:
            out.append(f'<figure><video src="{r["clip"]}" controls loop muted '
                       'playsinline preload="metadata"></video>'
                       f'<figcaption>klip dari game yang benar-benar jalan · '
                       f'{html.escape(r["clip_name"])}</figcaption></figure>')
        if r['strip']:
            out.append(f'<figure><img src="{r["strip"]}" alt="Filmstrip '
                       f'{html.escape(r["id"])}"><figcaption>filmstrip, tiap '
                       f'petak berlabel ms · {html.escape(r["strip_name"])}'
                       '</figcaption></figure>')
        img = r['sheet'] or r['shot']
        if img:
            cap = (f'lembar banding buta · {html.escape(r["sheet_name"])}'
                   if r['sheet'] else 'tangkapan mentah dari game')
            out.append(f'<figure><img src="{img}" alt="Perbandingan {html.escape(r["id"])}">'
                       f'<figcaption>{cap}</figcaption></figure>')
        out.append('</div></article>')

    if events:
        out.append('<h2 class="sec">Catatan terakhir</h2><div class="log">')
        for ev in events[-18:]:
            sid = html.escape(str(ev.get('slice', '—')))
            role = html.escape(str(ev.get('role', '')))
            note = html.escape(str(ev.get('note') or ev.get('gap') or ''))[:160]
            out.append(f'<div><b>{sid}</b> · {role} · {note}</div>')
        out.append('</div>')

    out.append('<footer>Bukti mentah ada di <code>_bench/</code> — klip dari '
               'game yang benar-benar jalan, jejak angka per frame '
               '(<code>*_trace.json</code>), lembar banding buta, dan '
               '<code>progress.jsonl</code>. Klip patokan hanya dipakai untuk '
               'pembandingan internal.</footer>')
    out.append('</div>')
    return '\n'.join(out)


if __name__ == '__main__':
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else BENCH / 'progress.html'
    dest.write_text(render(), encoding='utf-8')
    print(f'WROTE {dest} ({dest.stat().st_size/1024:.0f} KB)')
