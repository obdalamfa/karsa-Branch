"""mob_gerak.py — mob dungeon yang bergerak seperti makhluk, bukan patung.

Sebelum modul ini, mob adalah model .obj diam yang meluncur di lantai:
tidak bernapas, tidak melangkah, membelok dengan melompat ke empat arah,
dan wind-up serangannya (yang AI-nya sudah menghitung, `windup_ms`) tidak
terlihat sama sekali. Kilat kena pukul tidak pernah terlihat (kedua cabang
kodenya menyetel warna putih), dan mob yang mati lenyap dalam satu frame
walau `dying`/`death_ms` sudah disiapkan di mob.py.

Semua gerak di sini prosedural pada transform MODEL (bukan entity, yang
posisinya milik sync_visuals dan logikanya milik AI), jadi tidak ada aset
baru, dan tiap jenis mendapat watak geraknya sendiri:

  kelelawar   melayang, kepak cepat (naik-turun + guling)
  tikus_gua   lari kecil: lenggang cepat, rendah
  pocong      melompat-lompat dengan gepeng saat mendarat
  kuntilanak  melayang tinggi, berayun pelan
  genderuwo   langkah berat: goyang lebar, hentakan
  banaspati   api: denyut skala dan kedip
  leak        melayang, berputar pelan
  naga (boss) napas besar, kepala condong saat ancang-ancang

Fase bersama: diam (napas), jalan (lenggang + belok halus), ancang-ancang
(condong ke belakang, membesar, gemetar, kemerahan), terjang (maju sesaat),
kena pukul (kilat putih + mental ke belakang), mati (berputar, menyusut,
tenggelam 0,6 dtk sebelum dihapus).
"""
from __future__ import annotations

import math
import random

# Watak per jenis: (laju napas, amplitudo napas, lenggang derajat,
# laju langkah, melayang, lompat)
_WATAK = {
    'kelelawar':  dict(napas=9.0, amp=0.10, lenggang=14, langkah=16, melayang=True),
    'tikus_gua':  dict(napas=5.0, amp=0.02, lenggang=10, langkah=22),
    'pocong':     dict(napas=2.0, amp=0.02, lenggang=4, langkah=7, lompat=0.45),
    'kuntilanak': dict(napas=1.6, amp=0.12, lenggang=8, langkah=3, melayang=True),
    'genderuwo':  dict(napas=1.4, amp=0.03, lenggang=11, langkah=6),
    'banaspati':  dict(napas=7.0, amp=0.06, lenggang=6, langkah=8, api=True),
    'leak':       dict(napas=1.8, amp=0.10, lenggang=6, langkah=4, melayang=True),
    'naga':       dict(napas=1.1, amp=0.025, lenggang=4, langkah=4),
}
_BAKU = dict(napas=2.0, amp=0.03, lenggang=8, langkah=9)

DURASI_MATI = 0.6
DURASI_KENA = 0.22


def _pasang_awal(actor):
    m = getattr(actor, 'model', None)
    if m is None or getattr(actor, '_mg_awal', None) is not None:
        return
    try:
        actor._mg_awal = (m.getPos(), m.getHpr(), m.getScale())
    except Exception:
        actor._mg_awal = None
    actor._mg_t = random.uniform(0, 6.28)      # fase acak: kawanan tidak serempak
    actor._mg_yaw = actor.rotation_y
    actor._mg_kena = 0.0
    actor._mg_hp_lalu = getattr(actor, 'hp', 0)


def kena(actor):
    """Dipanggil saat mob menerima pukulan: kilat + mental."""
    actor._mg_kena = DURASI_KENA


def animasikan(actor, dt, pemain_xz=None):
    """Satu frame animasi mob. Dipanggil SESUDAH sync_visuals."""
    _pasang_awal(actor)
    awal = getattr(actor, '_mg_awal', None)
    m = getattr(actor, 'model', None)
    if awal is None or m is None:
        return
    pos0, hpr0, sc0 = awal
    jenis = 'naga' if getattr(actor, 'is_boss', False) else getattr(actor, 'kind', '')
    w = _WATAK.get(jenis, _BAKU)
    actor._mg_t += dt
    t = actor._mg_t

    # Kena pukul terdeteksi juga dari HP turun, supaya jalur serang mana pun
    # (pedang, ledakan, quest) memicunya tanpa harus ingat memanggil kena().
    hp = getattr(actor, 'hp', 0)
    if hp < getattr(actor, '_mg_hp_lalu', hp):
        actor._mg_kena = DURASI_KENA
    actor._mg_hp_lalu = hp

    dy = dh = dp = dr = 0.0
    sx = sy = 1.0

    # ── mati ──
    if getattr(actor, 'dying', False):
        k = min(1.0, actor.death_ms / (DURASI_MATI * 1000.0))
        dh = 540 * k * k
        dr = 25 * k
        dy = -0.6 * k * k
        s = max(0.02, 1.0 - k)
        m.setPos(pos0.x, pos0.y + dy, pos0.z)
        m.setHpr(hpr0.x + dh, hpr0.y, hpr0.z + dr)
        m.setScale(sc0.x * s, sc0.y * s * (1 + 0.3 * k), sc0.z * s)
        try:
            from ursina import color
            actor.color = color.rgba(255, 255, 255, int(255 * (1 - k)))
        except Exception:
            pass
        return

    bergerak = getattr(actor, 'is_moving', False)
    windup = getattr(actor, 'windup_ms', 0) or 0
    total = max(1, getattr(actor, 'windup_total', 1) or 1)

    # ── napas / idle ──
    napas = math.sin(t * w['napas'])
    sy *= 1.0 + w['amp'] * 0.5 * napas
    sx *= 1.0 - w['amp'] * 0.25 * napas
    if w.get('melayang'):
        dy += 0.18 * math.sin(t * w['napas'] * 0.5) + 0.12
        dr += 6 * math.sin(t * w['napas'] * 0.5 + 1.0)
    if w.get('api'):
        kedip = 1.0 + 0.08 * math.sin(t * 23.0) + 0.05 * math.sin(t * 37.0)
        sx *= kedip
        sy *= kedip

    # ── jalan ──
    if bergerak:
        fase = t * w['langkah']
        dr += w['lenggang'] * math.sin(fase)
        dp += 4 * math.sin(fase * 2)
        if w.get('lompat'):
            loncat = abs(math.sin(fase * 0.5))
            dy += w['lompat'] * loncat
            # gepeng saat menyentuh tanah
            if loncat < 0.25:
                sy *= 0.85
                sx *= 1.08
        elif not w.get('melayang'):
            dy += 0.05 * abs(math.sin(fase))

    # ── ancang-ancang & terjang ──
    if windup > 0:
        k = 1.0 - windup / total                  # 0 -> 1 menuju pukulan
        dp -= 18 * k                              # condong ke belakang
        tumbuh = 1.0 + 0.18 * k
        sx *= tumbuh
        sy *= tumbuh
        gemetar = 1.5 + 5 * k
        dh += random.uniform(-gemetar, gemetar)
        dr += random.uniform(-gemetar, gemetar) * 0.5
        if k > 0.85:                              # terjang di ujung wind-up
            dp += 40 * (k - 0.85) / 0.15
    cd = getattr(actor, 'attack_cooldown_ms', 0) or 0
    if cd > 850 and windup <= 0:                  # sesaat sesudah memukul
        q = (cd - 850) / 150.0
        dp += 22 * q

    # ── kena pukul ──
    if actor._mg_kena > 0:
        q = actor._mg_kena / DURASI_KENA
        dp -= 20 * q                              # mental ke belakang
        sy *= 1.0 - 0.15 * q
        sx *= 1.0 + 0.10 * q
        actor._mg_kena = max(0.0, actor._mg_kena - dt)

    # ── warna: merah saat ancang-ancang, putih menyala saat kena ──
    try:
        from ursina import color
        if actor._mg_kena > 0:
            actor.color = color.rgb(255, 255, 255)
            m.setColorScale(2.2, 2.2, 2.2, 1)
        elif windup > 0:
            k = 1.0 - windup / total
            m.setColorScale(1.0 + 0.9 * k, 1.0 - 0.45 * k, 1.0 - 0.45 * k, 1)
        else:
            m.setColorScale(1, 1, 1, 1)
    except Exception:
        pass

    # ── belok halus ke arah gerak / ke pemain saat menyerang ──
    tujuan = actor.rotation_y
    if pemain_xz is not None and (windup > 0 or getattr(actor, 'ai_state', None) is not None
                                  and getattr(actor.ai_state, 'name', '') in ('CHASE', 'ATTACK')):
        tujuan = math.degrees(math.atan2(pemain_xz[0] - actor.x, pemain_xz[1] - actor.z))
    beda = (tujuan - actor._mg_yaw + 180) % 360 - 180
    actor._mg_yaw += beda * min(1.0, dt * 8.0)
    actor.rotation_y = actor._mg_yaw

    m.setPos(pos0.x, pos0.y + dy, pos0.z)
    m.setHpr(hpr0.x + dh, hpr0.y + dp, hpr0.z + dr)
    m.setScale(sc0.x * sx, sc0.y * sy, sc0.z * sx)
