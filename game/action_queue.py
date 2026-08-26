"""action_queue.py — Antrian aksi: bagaimana sebuah klik menjadi perbuatan.

Loop permainan yang sebenarnya ada di sini. Sebelum modul ini, motif hanya
turun dan tidak ada apa pun yang menaikkannya; permainan tidak punya loop.

Model mengikuti The Sims: aksi masuk ANTRIAN, bukan langsung dijalankan.
Pemain boleh menumpuk beberapa perintah dan sim mengerjakannya berurutan.
Aksi otonom masuk dengan prioritas rendah sehingga selalu kalah dari perintah
pemain — itu yang membuat sim terasa punya kehendak sendiri tanpa pernah
membangkang perintah langsung.

Motif diberikan SELAMA aksi berjalan, bukan sekaligus di akhir. Itu penting
untuk keterbacaan: pemain melihat termometer merangkak naik dan langsung paham
sebab-akibatnya. Hadiah yang muncul tiba-tiba di akhir tidak mengajarkan apa pun.
"""
from __future__ import annotations

from dataclasses import dataclass, field

PRIORITY_PLAYER = 50      # perintah langsung pemain
PRIORITY_AUTONOMOUS = 2   # pilihan sim sendiri
PRIORITY_IDLE = 0


@dataclass
class QueuedAction:
    """Satu aksi yang sedang atau akan dijalankan."""
    interaction: object          # motives.Interaction
    target: tuple                # (tx, ty, tile_id)
    priority: int = PRIORITY_PLAYER
    elapsed: float = 0.0         # menit-sim yang sudah berjalan

    @property
    def name(self) -> str:
        return getattr(self.interaction, 'name', '?')

    @property
    def duration(self) -> float:
        return max(1.0, getattr(self.interaction, 'duration', 60.0))

    @property
    def progress(self) -> float:
        return min(1.0, self.elapsed / self.duration)


class ActionQueue:
    """Antrian per-sim. Pemain dan NPC memakai kelas yang sama."""

    MAX = 8

    def __init__(self, motives):
        self.motives = motives
        self.items: list[QueuedAction] = []
        self.last_finished: str | None = None

    # ── query ──
    @property
    def current(self) -> QueuedAction | None:
        return self.items[0] if self.items else None

    @property
    def busy(self) -> bool:
        return bool(self.items)

    def top_priority(self) -> int:
        return max((a.priority for a in self.items), default=PRIORITY_IDLE)

    def labels(self) -> list[str]:
        return [a.name for a in self.items]

    # ── mutasi ──
    def enqueue(self, interaction, target, priority: int = PRIORITY_PLAYER) -> bool:
        if len(self.items) >= self.MAX:
            return False
        self.items.append(QueuedAction(interaction, target, priority))
        return True

    def cancel_current(self) -> None:
        if self.items:
            self.items.pop(0)

    def clear(self) -> None:
        """Batalkan semua. Dipakai saat pemain ganti scene atau pingsan."""
        self.items.clear()

    def drop_autonomous(self) -> None:
        """Buang aksi yang dipilih sim sendiri, sisakan perintah pemain.

        Dipakai saat pemain memberi perintah: keinginan pemain selalu menang,
        tapi aksi pemain yang sudah antri tidak ikut hilang.
        """
        self.items = [a for a in self.items if a.priority > PRIORITY_AUTONOMOUS]

    # ── eksekusi ──
    def tick(self, sim_minutes: float) -> str | None:
        """Jalankan aksi terdepan selama `sim_minutes`.

        Mengembalikan nama aksi yang baru saja selesai, atau None.
        """
        act = self.current
        if act is None or sim_minutes <= 0:
            return None

        step = min(sim_minutes, act.duration - act.elapsed)
        if step > 0:
            self._apply(act, step)
            act.elapsed += step

        if act.elapsed >= act.duration - 1e-6:
            self.items.pop(0)
            self.last_finished = act.name
            return act.name
        return None

    def _apply(self, act: QueuedAction, minutes: float) -> None:
        """Bagi rata efek motif sepanjang durasi aksi."""
        frac = minutes / act.duration
        for ad in getattr(act.interaction, 'adverts', ()):
            self.motives.add(ad.motive, ad.delta * frac)
