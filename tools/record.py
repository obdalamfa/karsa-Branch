"""record.py — Rekam gameplay SUNGGUHAN jadi klip, filmstrip, dan jejak angka.

Animasi tidak bisa dinilai dari gambar diam. Satu tangkapan layar tidak bisa
membedakan gerakan yang punya antisipasi, tahanan, dan ikutan dari gerakan yang
cuma segitiga linier naik-turun — keduanya terlihat sama persis di frame puncak.
Jadi alat ini mengeluarkan TIGA bentuk bukti dari satu jalan-jalan yang sama:

  <nama>.mp4          klip; untuk ditonton manusia dan ditempel ke halaman progres
  <nama>_strip.png    filmstrip: N frame berjarak sama, tiap petak berlabel ms
  <nama>_trace.json   jejak angka per frame (sudut sendi, posisi, penanda)

Yang ketiga itu yang membuat kritik bisa keras. Dari jejaknya, hal-hal yang
biasanya cuma "terasa" jadi terukur:

  antisipasi   apakah ada gerakan BERLAWANAN arah sebelum ayunan utama?
  tahanan      berapa lama pose puncak ditahan? (nol = kaku)
  ikutan       apakah gerakan lewat dari titik akhir lalu balik? (overshoot)
  pelambatan   apakah kecepatan sudut mengecil di ujung, atau berhenti mendadak?
  ikutan kedua apakah ada bagian lain (kepala, badan, alat) yang ikut telat?

Pemakaian:

    python tools/record.py --out _bench/clips/gosok.mp4 --scene farm \\
        --script "warp:19,7|face:sapi_betsy|wait:20|pie:sapi_betsy:gosok|wait:200"

Bahasa skrip (dipisah '|'), dijalankan berurutan; tiap langkah merekam frame:

    wait:N                  jalankan N frame
    key:K                   kirim satu tombol ke game.input (mis. key:e)
    warp:X,Y                pindahkan pemain ke tile X,Y
    face:NPC_ID             putar pemain menghadap NPC (juga mengunci kamera)
    pie:NPC_ID:AKSI         jalankan aksi pie menu langsung (tanpa navigasi)
    hour:H                  set jam dalam game
    care:ID|*:TAKARAN:NILAI setel takaran perawatan ternak (air/kenyang/bersih)
    pos:NPC_ID:X,Y          tempatkan hewan/NPC di ubin (menata panggung)
    sepi:ID,ID              sembunyikan hewan lain supaya tidak menutupi
    cam:DIST,PITCH,YAW      setel kamera
    lift:H                  naikkan titik fokus kamera (bingkai dada, bukan kaki)
    mark:NAMA               tandai frame ini di jejak (dipakai untuk mengukur)

Klok dipaksa non-real-time: tiap frame persis 1/fps detik, jadi dua rekaman
dari kode yang sama menghasilkan jejak yang sama. Tanpa itu, mengukur waktu
animasi di mesin yang berbeda-beda bebannya cuma bikin angka sampah.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from panda3d.core import loadPrcFileData  # noqa: E402
loadPrcFileData('', 'load-display pandagl')
loadPrcFileData('', 'aux-display pandadx9')
loadPrcFileData('', 'window-type onscreen')
loadPrcFileData('', 'sync-video false')
loadPrcFileData('', 'audio-library-name null')

import logging  # noqa: E402
logging.basicConfig(level=logging.ERROR)


# ── sendi yang dilacak ───────────────────────────────────────────────────────
# Nama pendek -> (atribut di player, sifat yang diambil). Sengaja sedikit:
# jejak yang terlalu lebar tidak terbaca, dan lima sendi ini yang menentukan
# apakah satu aksi terlihat hidup.
JOINTS = {
    'bahu_r':  ('_pivot_shoulder_r', ('rotation_x', 'rotation_y', 'rotation_z')),
    'bahu_l':  ('_pivot_shoulder_l', ('rotation_x', 'rotation_y', 'rotation_z')),
    'siku_r':  ('_pivot_elbow_r',    ('rotation_x',)),
    'siku_l':  ('_pivot_elbow_l',    ('rotation_x',)),
    'badan':   ('body',              ('rotation_x', 'rotation_y', 'rotation_z', 'y')),
    'leher':   ('_pivot_neck',       ('rotation_x', 'rotation_y', 'y')),
    'lutut_r': ('_pivot_knee_r',     ('rotation_x',)),
    'lutut_l': ('_pivot_knee_l',     ('rotation_x',)),
}


def _sample(g) -> dict:
    """Satu baris jejak: sudut sendi + keadaan aksi yang sedang jalan."""
    p = g.player
    row: dict = {}
    for nama, (attr, props) in JOINTS.items():
        ent = getattr(p, attr, None)
        if ent is None:
            continue
        for pr in props:
            v = getattr(ent, pr, None)
            if isinstance(v, (int, float)):
                row[f'{nama}.{pr}'] = round(float(v), 4)
    row['aksi_ms'] = round(float(getattr(p, '_attack_anim', 0.0)), 2)
    row['aksi_mode'] = getattr(p, '_anim_mode', '')
    row['pemain.rot_y'] = round(float(p.rotation_y), 3)
    row['pemain.y'] = round(float(p.y), 4)
    # Aksi perawatan berdurasi (dibangun di slice ternak) punya jam sendiri.
    kar = getattr(p, '_care_anim', None)
    if kar is not None:
        row['rawat_t'] = round(float(getattr(kar, 't', 0.0)), 4)
        row['rawat_fase'] = getattr(kar, 'fase', '')
        row['rawat_jenis'] = getattr(kar, 'jenis', '')
    return row


# ── skrip ────────────────────────────────────────────────────────────────────
def _face_npc(g, npc_id: str):
    pos = g.state.npc_positions.get(npc_id) or {}
    nx, ny = pos.get('x'), pos.get('y')
    if nx is None:
        return
    from game.config import TILE_SIZE as TS
    dx = nx - g.player.x / TS
    dy = ny - g.player.z / TS
    g.player.rotation_y = math.degrees(math.atan2(dx, dy))
    g.player.target_rotation_y = g.player.rotation_y


def run_step(g, base, step: str, frames: list, marks: dict, shoot) -> None:
    """Jalankan satu langkah skrip. `shoot()` merekam satu frame."""
    if ':' in step:
        op, arg = step.split(':', 1)
    else:
        op, arg = step, ''
    op = op.strip()

    if op == 'wait':
        for _ in range(int(arg or 1)):
            shoot()
    elif op == 'key':
        try:
            g.input(arg)
        except Exception:
            traceback.print_exc()
        shoot()
    elif op == 'warp':
        x, y = (float(v) for v in arg.split(','))
        g.state.player_x, g.state.player_y = x, y
        g.player.set_tile_pos(x, y)
        g._snap_camera_to_player()
        shoot()
    elif op == 'face':
        _face_npc(g, arg)
        shoot()
    elif op == 'pie':
        npc_id, aksi = arg.split(':', 1)
        g.player.execute_pie_action(npc_id, aksi, g.entities, g.panels)
        shoot()
    elif op == 'hour':
        # Jam permainan disimpan sebagai time_minutes; `state.hour` bukan
        # atribut yang dibaca siapa pun. Menulis ke sana diam-diam tidak
        # melakukan apa-apa — dan itu yang membuat semua rekaman terjebak di
        # jam 7 pagi, saat matahari terbit membakar seluruh bingkai jadi putih.
        g.state.time_minutes = float(arg) * 60.0
        shoot()
    elif op == 'cam':
        d, p, y = (float(v) for v in arg.split(','))
        g.camera_dist, g.camera_pitch, g.camera_yaw = d, p, y
        g._snap_camera_to_player()
        shoot()
    elif op == 'lift':
        # app.py melakukan `from .config import CAM_TARGET_LIFT`, jadi namanya
        # tinggal di namespace game.app — di situlah ia harus diganti supaya
        # bingkai rekaman bisa naik ke dada, bukan ke kaki.
        import game.app as _app
        _app.CAM_TARGET_LIFT = float(arg)
        g._snap_camera_to_player()
        shoot()
    elif op == 'care':
        # care:<id|*>:<takaran>:<nilai> — siapkan keadaan ternak sebelum
        # merekam. Aksi perawatan menolak jalan kalau tidak ada yang perlu
        # dikerjakan (palung penuh, hewan kenyang), jadi tanpa penyiapan ini
        # rekaman aksi perawatan selalu berisi penolakan, bukan aksi.
        siapa, takaran, nilai = arg.split(':')
        from game.data import ANIMAL_NPCS
        from game.husbandry import care_of, is_livestock
        from game.economy import animal_record
        ids = [a for a in ANIMAL_NPCS if is_livestock(a)] if siapa == '*' else [siapa]
        for aid in ids:
            if takaran == 'siap':
                # Siklus hasil tinggal di economy.animal_record, bukan di
                # takaran perawatan husbandry — dua buku yang berbeda isinya.
                animal_record(g.state, aid)['siap'] = int(float(nilai))
            else:
                care_of(g.state, aid)[takaran] = float(nilai)
        try:
            g.player.interaction_controller.sync_trough()
        except Exception:
            pass
        shoot()
    elif op == 'pos':
        # pos:<npc_id>:<x>,<y> — tempatkan hewan/NPC di ubin tertentu.
        # Kandang kebun berisi enam ekor di petak 9x5; pada kamera sedekat
        # yang dibutuhkan untuk MELIHAT animasi, selalu ada satu ekor yang
        # menutupi pemain. Ini menata panggung untuk pengambilan gambar,
        # bukan mengubah permainan.
        who, xy = arg.split(':', 1)
        x, y = (float(v) for v in xy.split(','))
        pos = g.state.npc_positions.setdefault(who, {})
        pos.update(scene=g.state.scene_name, x=x, y=y, target_x=x, target_y=y)
        act = g.entities.actors.get(who)
        if act is not None:
            from game.config import TILE_SIZE as _TS
            act.logical_x, act.logical_y = x, y
            act.target_x, act.target_y = x, y
            act.x, act.z = x * _TS, y * _TS
        shoot()
    elif op == 'sepi':
        # sepi:<id,id,...> — singkirkan hewan lain jauh dari panggung.
        buang = {a.strip() for a in arg.split(',') if a.strip()}
        from game.data import ANIMAL_NPCS
        for aid in ANIMAL_NPCS:
            if aid in buang:
                continue
            act = g.entities.actors.get(aid)
            if act is None:
                continue
            act.enabled = False
        shoot()
    elif op == 'mark':
        marks[arg] = len(frames)
    else:
        raise SystemExit(f'langkah skrip tidak dikenal: {step!r}')


# ── penggerak ────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True, help='berkas .mp4 tujuan')
    ap.add_argument('--scene', default='farm')
    ap.add_argument('--script', default='wait:60')
    ap.add_argument('--fps', type=int, default=30)
    ap.add_argument('--width', type=int, default=960)
    ap.add_argument('--height', type=int, default=540)
    ap.add_argument('--strip', type=int, default=12,
                    help='jumlah petak di filmstrip (0 = tanpa filmstrip)')
    ap.add_argument('--strip-from', default='',
                    help='ambil petak filmstrip mulai dari mark ini')
    ap.add_argument('--strip-frames', type=int, default=0,
                    help='panjang jendela filmstrip dalam frame (0 = seluruh klip)')
    ap.add_argument('--seed', type=int, default=1234)
    args = ap.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    import random
    random.seed(args.seed)

    from ursina import application
    application.asset_folder = ROOT
    application.fonts_folder = ROOT / 'fonts'
    from panda3d.core import getModelPath
    getModelPath().append_path(str(ROOT.resolve()))

    import game.config as cfg
    cfg.SCREEN_W, cfg.SCREEN_H = args.width, args.height

    from game.app import Game3D
    g = Game3D()

    from direct.showbase.ShowBaseGlobal import base
    from panda3d.core import ClockObject
    clock = ClockObject.getGlobalClock()
    clock.setMode(ClockObject.MNonRealTime)
    clock.setDt(1.0 / args.fps)

    for _ in range(10):
        base.taskMgr.step()

    g.state.scene_name = args.scene
    for _ in range(40):
        base.taskMgr.step()

    frames: list = []
    trace: list = []
    marks: dict = {}

    def shoot():
        base.taskMgr.step()
        img = base.win.getScreenshot()
        if img is not None:
            frames.append(img)
            trace.append(_sample(g))

    for step in [s for s in args.script.split('|') if s.strip()]:
        run_step(g, base, step.strip(), frames, marks, shoot)

    if not frames:
        print('RECORD_FAIL: nol frame', file=sys.stderr)
        sys.exit(2)

    # ── tulis mp4 ────────────────────────────────────────────────────────────
    from PIL import Image, ImageDraw

    # Panda menulis PNG jauh lebih cepat daripada mengambil piksel satu-satu.
    tmp = out.parent / f'.{out.stem}_frames'
    tmp.mkdir(parents=True, exist_ok=True)
    from panda3d.core import Filename
    paths = []
    for i, img in enumerate(frames):
        p = tmp / f'f{i:05d}.png'
        img.write(Filename.fromOsSpecific(str(p.resolve())))
        paths.append(p)

    import imageio_ffmpeg
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    import subprocess
    cmd = [exe, '-y', '-loglevel', 'error', '-framerate', str(args.fps),
           '-i', str(tmp / 'f%05d.png'),
           '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20',
           str(out.resolve())]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print('RECORD_WARN: ffmpeg gagal:', r.stderr[-400:], file=sys.stderr)

    # ── filmstrip ────────────────────────────────────────────────────────────
    strip_path = out.with_name(out.stem + '_strip.png')
    if args.strip > 0:
        lo = marks.get(args.strip_from, 0) if args.strip_from else 0
        hi = min(len(paths), lo + args.strip_frames) if args.strip_frames else len(paths)
        span = max(1, hi - lo)
        n = min(args.strip, span)
        idxs = [lo + round(i * (span - 1) / max(1, n - 1)) for i in range(n)]
        thumbs = [Image.open(paths[i]).convert('RGB') for i in idxs]
        tw = 300
        th = max(1, round(thumbs[0].height * tw / thumbs[0].width))
        cols = min(4, n)
        rows = math.ceil(n / cols)
        LAB = 20
        sheet = Image.new('RGB', (cols * tw, rows * (th + LAB)), (16, 18, 20))
        d = ImageDraw.Draw(sheet)
        for k, (i, im) in enumerate(zip(idxs, thumbs)):
            cx, cy = (k % cols) * tw, (k // cols) * (th + LAB)
            sheet.paste(im.resize((tw, th), Image.LANCZOS), (cx, cy + LAB))
            ms = (i - lo) * 1000.0 / args.fps
            d.text((cx + 5, cy + 5), f'#{i}  {ms:.0f} ms', fill=(235, 225, 190))
        sheet.save(strip_path)

    # ── jejak ────────────────────────────────────────────────────────────────
    trace_path = out.with_name(out.stem + '_trace.json')
    trace_path.write_text(json.dumps({
        'fps': args.fps,
        'scene': args.scene,
        'script': args.script,
        'marks': marks,
        'frames': trace,
    }, ensure_ascii=False, indent=1), encoding='utf-8')

    for p in paths:
        try:
            p.unlink()
        except OSError:
            pass
    try:
        tmp.rmdir()
    except OSError:
        pass

    print(f'RECORD_OK {out.resolve()}  {len(frames)} frame @ {args.fps}fps')
    print(f'  strip: {strip_path}')
    print(f'  trace: {trace_path}')
    sys.stdout.flush()
    os._exit(0)


if __name__ == '__main__':
    main()
