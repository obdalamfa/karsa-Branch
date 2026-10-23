"""probe_kamera_qe.py — [Q]/[E] memutar kamera, [F] interaksi, [Shift]+[F] tangkap.

Sejak 22 Okt 2026 tata tombolnya:

  [Q] / [E]     kamera berputar 45 derajat ke kiri / kanan per tekan
  [F]           interaksi (dulu [E]): bicara, surat, Peti Kirim, ternak
  [Shift]+[F]   tangkap makhluk halus (dulu [F])
  [R]           ganti benih (dulu [Q]/[R]; [Q] benih-sebelumnya dilepas)

PANDUAN.md dan README_PEMAIN.md sudah lama menulis "Q/E Putar kamera"
padahal tidak ada kode yang melakukannya. Probe ini menjaga supaya janji
itu tidak membusuk lagi.

Semua tombol lewat dispatcher Ursina `g.app.input` (aturan #2 CLAUDE.md),
dari game baru, HUD dicapai lewat SPACE sampai sinema selesai. Save ditulis
ke direktori sementara.

    python tools/probe_kamera_qe.py
"""
from __future__ import annotations

import math
import os
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))

from probe_batin import boot, ke_hud, langkah, tekan, jalan  # noqa: E402

hasil: list[tuple[str, bool, str]] = []


def cek(nama, ok, ket=''):
    hasil.append((nama, bool(ok), str(ket)))


def beda_sudut(a, b):
    return abs((a - b + 180.0) % 360.0 - 180.0)


def tunggu_putar(g, maks=240):
    """Langkah sampai putaran [Q]/[E] tiba (tujuan dibuang saat sampai)."""
    for _ in range(maks):
        langkah(1)
        if getattr(g, '_yaw_tujuan', None) is None:
            return True
    return False


def arah_w(g):
    """Sudut antara gerak W dan 'atas layar' kamera, tabrakan dimatikan
    seperti cek arah_maju di regress.py. Berhenti di 3 satuan."""
    from ursina import held_keys, camera
    world = g.player.world
    world.is_walkable = lambda *a, **k: True
    try:
        for k in ('w', 'a', 's', 'd', 'shift'):
            held_keys[k] = 0
        g.player.velocity_x = g.player.velocity_z = 0.0
        langkah(3)
        x0, _, z0 = g.player.world_position
        cx, _, cz = camera.world_position
        ux, uz = g.camera_focus[0] - cx, g.camera_focus[2] - cz
        held_keys['w'] = 1
        for _ in range(60):
            langkah(1)
            px, _, pz = g.player.world_position
            if math.hypot(px - x0, pz - z0) >= 3.0:
                break
        held_keys['w'] = 0
        x1, _, z1 = g.player.world_position
        dx, dz = x1 - x0, z1 - z0
        j, nu = math.hypot(dx, dz), math.hypot(ux, uz)
        if j < 1.0 or nu < 1e-4:
            return None, j
        c = max(-1.0, min(1.0, (dx * ux + dz * uz) / (j * nu)))
        return math.degrees(math.acos(c)), j
    finally:
        del world.is_walkable
        g.player.velocity_x = g.player.velocity_z = 0.0


def uji(g):
    from ursina import held_keys
    s, p = g.state, g.panels

    if not ke_hud(g):
        cek('sampai HUD lewat SPACE', False, f'mode={p.mode}')
        return

    # Tengah ladang, jauh dari portal dan dinding.
    jalan(g, 15, 15, 'up')
    langkah(30)

    # 1. [Q] = +45, [E] = -45, halus lalu tiba persis.
    y0 = g.camera_yaw
    benih0 = s.seed_key
    tekan(g, 'q', 1)
    sedang = g.camera_yaw
    tiba = tunggu_putar(g)
    cek('[Q] memutar kamera +45 derajat',
        tiba and beda_sudut(g.camera_yaw, y0 + 45.0) < 0.6,
        f'{y0:.1f} -> {g.camera_yaw:.1f} (tiba={tiba})')
    cek('putaran halus, bukan lompat dalam satu frame',
        beda_sudut(sedang, y0 + 45.0) > 1.0,
        f'frame pertama {sedang:.1f}, tujuan {y0 + 45.0:.1f}')
    cek('[Q] tidak lagi mengganti benih', s.seed_key == benih0,
        f'{benih0} -> {s.seed_key}')

    y1 = g.camera_yaw
    tekan(g, 'e', 1)
    tekan(g, 'e', 1)                    # tekan cepat dua kali = 90, bukan 45
    tunggu_putar(g)
    cek('[E][E] cepat memutar -90 derajat',
        beda_sudut(g.camera_yaw, y1 - 90.0) < 0.6,
        f'{y1:.1f} -> {g.camera_yaw:.1f}')

    # 2. WASD tetap relatif kamera setelah diputar (aturan #5: tanda WASD
    #    tidak diubah; ini memastikan putaran tidak merusaknya).
    beda, jarak = arah_w(g)
    cek('W tetap "atas layar" setelah diputar',
        beda is not None and beda < 25.0,
        f'beda {beda if beda is None else round(beda, 1)} deg, {jarak:.1f}u')

    # 3. Di panel, Q/E milik panel, bukan kamera.
    tekan(g, 'i', 4)
    if p.mode != 'hud':
        y2 = g.camera_yaw
        tekan(g, 'q', 1)
        langkah(20)
        cek('[Q] di panel inventaris tidak memutar kamera',
            beda_sudut(g.camera_yaw, y2) < 0.01 and getattr(g, '_yaw_tujuan', None) is None,
            f'{y2:.1f} -> {g.camera_yaw:.1f}')
        tekan(g, 'escape', 4)
    else:
        cek('[I] membuka panel inventaris', False, f'mode={p.mode}')

    # 4. [E] menghadap kotak pos TIDAK membaca surat; [F] membacanya.
    from game.config import MB
    from game.scenes import SCENES
    mb = next((x, y) for y, r in enumerate(SCENES['farm'].tiles)
              for x, v in enumerate(r) if v == MB)
    jalan(g, mb[0], mb[1] - 1, 'up')
    tekan(g, 'e', 6)
    tunggu_putar(g)
    cek('[E] menghadap kotak pos tidak membaca surat', not s.mail_read and p.mode == 'hud',
        f'mail_read={s.mail_read} mode={p.mode}')
    jalan(g, mb[0], mb[1] - 1, 'up')
    tekan(g, 'f', 6)
    cek('[F] menghadap kotak pos membaca surat', s.mail_read,
        f'mail_read={s.mail_read}')
    if p.mode != 'hud':
        tekan(g, 'escape', 4)

    # 5. Petunjuk tutorial dan pelacak HUD menyebut [F], bukan [E].
    from game.tutorial import tracker_lines
    _, _, hint = tracker_lines(s)
    cek('petunjuk tutorial tidak menyuruh [E]', '[E]' not in (hint or ''), repr(hint))

    # 6. [Shift]+[F] menangkap, [F] saja tidak.
    ic = g.player.interaction_controller
    hitung = {'capture': 0, 'interact': 0}
    asli_c, asli_i = ic.capture, ic.interact
    ic.capture = lambda *a, **k: (hitung.__setitem__('capture', hitung['capture'] + 1), asli_c(*a, **k))[1]
    ic.interact = lambda *a, **k: (hitung.__setitem__('interact', hitung['interact'] + 1), asli_i(*a, **k))[1]
    try:
        jalan(g, 15, 15, 'up')
        held_keys['shift'] = 1
        tekan(g, 'f', 3)
        held_keys['shift'] = 0
        langkah(2)
        cek('[Shift]+[F] memanggil tangkap, bukan interaksi',
            hitung == {'capture': 1, 'interact': 0}, str(hitung))
        if p.mode != 'hud':
            tekan(g, 'escape', 4)
        tekan(g, 'f', 3)
        cek('[F] saja memanggil interaksi', hitung['interact'] == 1 and hitung['capture'] == 1,
            str(hitung))
        if p.mode != 'hud':
            tekan(g, 'escape', 4)
    finally:
        held_keys['shift'] = 0
        ic.capture, ic.interact = asli_c, asli_i


def main():
    kerja = Path(tempfile.mkdtemp(prefix='probe_kamera_qe_'))
    try:
        g = boot(kerja / 'save.json')
    except Exception:
        traceback.print_exc()
        os._exit(1)
    try:
        uji(g)
    except Exception as ex:
        traceback.print_exc()
        cek('probe meledak', False, f'{type(ex).__name__}: {ex}')

    print('\nKAMERA [Q]/[E] + INTERAKSI [F] — lewat app.input dari game baru')
    print('=' * 78)
    lebar = max(len(n) for n, _, _ in hasil)
    for nama, ok, ket in hasil:
        print(f"{'LULUS' if ok else 'GAGAL':>5s}  {nama:<{lebar}s}  {ket[:70]}")
    gagal = [n for n, ok, _ in hasil if not ok]
    print('-' * 78)
    print(f'{len(hasil) - len(gagal)}/{len(hasil)} lulus')
    sys.stdout.flush()
    os._exit(1 if gagal else 0)


if __name__ == '__main__':
    main()
