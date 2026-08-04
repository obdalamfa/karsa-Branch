"""sims_action_controller.py — Eksekusi OBJEK-BERAKSI ala The Sims (S2).

Alur satu aksi (persis pola The Sims / FreeSO):
    ANTRE → JALAN ke objek (pathfinding) → LAKUKAN (animasi + isi motif
    bertahap selama durasi) → SELESAI

Memakai ulang yang sudah ada:
- game/pathfinder.py PathMover  (player.mover) untuk berjalan ke objek
- game/player.py _play_tool_anim / anim state untuk pose
- game/sims_objects.py katalog + skor iklan
- game/panels.py flash_msg & emote untuk umpan balik

Motif diisi BERTAHAP (per detik) supaya aksi bisa dibatalkan di tengah dan
pemain tetap dapat sebagian manfaat — seperti Sims sungguhan.
"""
from ..config import NEED_MAX
from ..sims_objects import SIMS_OBJECTS
from ..sound import play as sound_play


class SimsActionController:
    """Menjalankan satu aksi-objek untuk Sim yang dikendalikan pemain."""

    # Jarak (tile) dianggap sudah sampai di objek
    REACH = 1.6

    def __init__(self, player):
        self.player = player
        self.state = player.state
        self.current = None      # dict aksi berjalan
        self._last_msg = None

    # ── API publik ────────────────────────────────────────────────
    @property
    def busy(self) -> bool:
        return self.current is not None

    def label(self) -> str:
        """Teks status untuk HUD ('Tidur… 62%') atau '' bila senggang."""
        c = self.current
        if not c:
            return ''
        if c['phase'] == 'walk':
            return f"Menuju {c['obj']['label']}…"
        pct = int((1.0 - c['left'] / c['dur']) * 100)
        return f"{c['obj']['action']}… {pct}%"

    def start(self, tile_id: int, tx: int, ty: int, panels=None) -> bool:
        """Antre & mulai aksi pada objek di tile (tx,ty). False bila tak valid."""
        obj = SIMS_OBJECTS.get(tile_id)
        if not obj:
            return False
        self.cancel(panels=None)             # satu aksi pada satu waktu
        self.current = {
            'tid': tile_id, 'tx': int(tx), 'ty': int(ty), 'obj': obj,
            'dur': float(obj['dur']), 'left': float(obj['dur']),
            'phase': 'walk',
        }
        # Jalan ke objek memakai PathMover yang sudah ada (klik-untuk-jalan).
        self._walk_to(tx, ty)
        if panels:
            panels.flash_msg(f"{obj['action']} — {obj['label']}", 1.4)
        return True

    def cancel(self, panels=None):
        c = self.current
        self.current = None
        if c and panels:
            panels.flash_msg(f"{c['obj']['action']} dibatalkan.", 1.0)

    def tick(self, dt: float, panels=None):
        """Dipanggil tiap frame dari Player3D.tick()."""
        c = self.current
        if not c:
            return

        if c['phase'] == 'walk':
            if self._near(c['tx'], c['ty']):
                c['phase'] = 'do'
                self._face(c['tx'], c['ty'])
                self._play_anim(c['obj'].get('anim'))
                try:
                    sound_play('menu_select', 0.6)
                except Exception:
                    pass
            elif not self._walking():
                # Tak bisa mencapai objek (terhalang) — batalkan dgn jujur.
                self.current = None
                if panels:
                    panels.flash_msg(f"Tak bisa mencapai {c['obj']['label']}.", 1.6)
            return

        # ── Fase melakukan: isi motif bertahap ──
        step = min(dt, c['left'])
        frac = step / c['dur'] if c['dur'] > 0 else 1.0
        for field, total in c['obj']['motives'].items():
            self._add_motive(field, total * frac)
        c['left'] -= step

        if c['left'] <= 0.0:
            obj = c['obj']
            self.current = None
            if panels:
                gains = ', '.join(
                    f"{self._motive_label(f)} +{int(v)}" for f, v in obj['motives'].items())
                panels.flash_msg(f"Selesai {obj['action'].lower()} ({gains})", 1.8)
                try:
                    panels.emote('v', None, 1.0)
                except Exception:
                    pass
            try:
                sound_play('harvest', 0.6)
            except Exception:
                pass

    # ── Internal ──────────────────────────────────────────────────
    _LABELS = {'lapar': 'Lapar', 'sosial': 'Sosial', 'senang': 'Senang',
               'kandung': 'Kandung', 'bersih': 'Bersih', 'energy': 'Energi'}

    def _motive_label(self, field):
        return self._LABELS.get(field, field)

    def _add_motive(self, field: str, delta: float):
        s = self.state
        if field == 'energy':
            s.energy = max(0.0, min(s.max_energy, s.energy + delta))
        else:
            cur = float(getattr(s, field, NEED_MAX))
            setattr(s, field, max(0.0, min(NEED_MAX, cur + delta)))

    def _tile_pos(self):
        """Posisi tile Sim saat ini (pecahan). Pakai posisi LIVE entitas —
        state.player_x baru disinkronkan belakangan, jadi bisa basi."""
        try:
            return self.player.get_float_tile()
        except Exception:
            return float(self.state.player_x), float(self.state.player_y)

    def _near(self, tx, ty) -> bool:
        px, py = self._tile_pos()
        return abs(px - tx) <= self.REACH and abs(py - ty) <= self.REACH

    def _walking(self) -> bool:
        mv = getattr(self.player, 'mover', None)
        return bool(mv and getattr(mv, 'is_moving', False))

    def _walk_to(self, tx, ty):
        """Jalan ke tile TERDEKAT yang bisa dipijak di sebelah objek (objek
        sendiri BLOCKING, jadi tak bisa diinjak)."""
        from ..config import TILE_SIZE, WALKABLE
        world = getattr(self.player, 'world', None)
        px, py = self._tile_pos()
        best = None
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nx, ny = tx + dx, ty + dy
            try:
                if world and world.get_tile(nx, ny) not in WALKABLE:
                    continue
            except Exception:
                pass
            d = abs(px - nx) + abs(py - ny)
            if best is None or d < best[0]:
                best = (d, nx, ny)
        if best is None:
            return
        _, nx, ny = best
        try:
            self.player.move_to_world(nx * TILE_SIZE, ny * TILE_SIZE)
        except Exception:
            pass

    def _face(self, tx, ty):
        import math
        px, py = self._tile_pos()
        dx, dy = tx - px, ty - py
        try:
            self.player.target_rotation_y = math.degrees(math.atan2(dx, dy))
        except Exception:
            pass

    def _play_anim(self, anim):
        if not anim:
            return
        try:
            self.player._play_tool_anim(anim if anim in ('bend', 'down') else 'down')
        except Exception:
            pass
