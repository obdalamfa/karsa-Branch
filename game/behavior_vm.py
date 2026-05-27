"""
behavior_vm.py — Sistem Perilaku NPC untuk Lembah Karsa 3D
Diadaptasi dari SimAntics VM (FreeSO / The Sims Online, C#) ke Python/Ursina.

KONSEP UTAMA:
- Setiap NPC/entitas punya satu BehaviorThread
- Thread menyimpan action queue (antrian interaksi)
- Setiap action dijalankan sebagai pohon behavior node
- Node return TRUE / FALSE / RUNNING
- Sistem ini sepenuhnya terpisah dari rendering — bisa dipakai tanpa Ursina

CONTOH PEMAKAIAN:
    from behavior_vm import BehaviorVM, BehaviorEntity, action, condition

    vm = BehaviorVM()
    npc = BehaviorEntity("Sari", motives={"energy": 80, "social": 60, "hunger": 40})
    vm.add_entity(npc)

    # Daftarkan aksi "tidur"
    @action("tidur", motive_changes={"energy": +40})
    def tidur(entity, ctx):
        print(f"{entity.name} mulai tidur...")
        entity.set_animation("sleep")
        return NodeResult.SUCCESS

    npc.queue_action("tidur")
    vm.tick()  # panggil tiap frame
"""

from __future__ import annotations
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Any
import time


# ---------------------------------------------------------------------------
# Hasil eksekusi sebuah node (sama dengan VMPrimitiveExitCode di FreeSO)
# ---------------------------------------------------------------------------
class NodeResult(Enum):
    SUCCESS   = auto()   # TRUE  — lanjut ke cabang sukses
    FAILURE   = auto()   # FALSE — lanjut ke cabang gagal
    RUNNING   = auto()   # CONTINUE — masih dieksekusi, panggil lagi next tick


# ---------------------------------------------------------------------------
# Sebuah node dalam behavior tree (satu "primitive" di SimAntics)
# ---------------------------------------------------------------------------
@dataclass
class BehaviorNode:
    """
    Satu instruksi dalam behavior tree.
    fn(entity, context) -> NodeResult
    """
    name: str
    fn: Callable[["BehaviorEntity", "BehaviorContext"], NodeResult]
    on_success: Optional["BehaviorNode"] = None   # cabang jika TRUE
    on_failure: Optional["BehaviorNode"] = None   # cabang jika FALSE
    metadata: Dict[str, Any] = field(default_factory=dict)

    def run(self, entity: "BehaviorEntity", ctx: "BehaviorContext") -> NodeResult:
        try:
            return self.fn(entity, ctx)
        except Exception as e:
            print(f"[BehaviorVM] ERROR di node '{self.name}' pada '{entity.name}': {e}")
            return NodeResult.FAILURE


# ---------------------------------------------------------------------------
# Stack frame — satu level dalam call stack (seperti VMStackFrame di FreeSO)
# ---------------------------------------------------------------------------
@dataclass
class BehaviorFrame:
    node: BehaviorNode
    caller: Optional["BehaviorEntity"]   # siapa yang memicu aksi ini
    callee: "BehaviorEntity"             # siapa yang menjalankan
    temps: List[float] = field(default_factory=lambda: [0.0] * 20)  # 20 register temp


# ---------------------------------------------------------------------------
# Satu aksi yang antri (seperti VMQueuedAction di FreeSO)
# ---------------------------------------------------------------------------
@dataclass
class QueuedAction:
    name: str
    root_node: BehaviorNode
    priority: int = 0           # semakin tinggi = lebih urgent
    caller: Optional["BehaviorEntity"] = None
    uid: int = field(default_factory=lambda: int(time.time() * 1000) % 100000)
    motive_changes: Dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Thread satu entitas (seperti VMThread di FreeSO)
# ---------------------------------------------------------------------------
class BehaviorThread:
    MAX_TICKS_PER_FRAME = 200  # batas loop per frame (anti-hang)

    def __init__(self, entity: "BehaviorEntity"):
        self.entity = entity
        self.queue: List[QueuedAction] = []
        self.stack: List[BehaviorFrame] = []
        self.active_action: Optional[QueuedAction] = None
        self.blocking: bool = False          # sedang menunggu async (animasi, dll)
        self.block_timer: float = 0.0        # sisa waktu blocking
        self.queue_dirty: bool = False

    # -- Antrian --
    def push_action(self, action: QueuedAction):
        self.queue.append(action)
        self.queue.sort(key=lambda a: -a.priority)
        self.queue_dirty = True

    def cancel_action(self, name: str):
        self.queue = [a for a in self.queue if a.name != name]
        if self.active_action and self.active_action.name == name:
            self.stack.clear()
            self.active_action = None

    # -- Eksekusi satu frame --
    def tick(self, ctx: "BehaviorContext", dt: float):
        # Tangani blocking (menunggu animasi / async)
        if self.blocking:
            self.block_timer -= dt
            if self.block_timer <= 0:
                self.blocking = False
            else:
                return

        # Ambil aksi dari queue kalau stack kosong
        if not self.stack and self.queue:
            self.active_action = self.queue.pop(0)
            frame = BehaviorFrame(
                node=self.active_action.root_node,
                caller=self.active_action.caller,
                callee=self.entity
            )
            self.stack.append(frame)

        if not self.stack:
            return

        # Eksekusi node di top of stack
        ticks = 0
        while self.stack and not self.blocking and ticks < self.MAX_TICKS_PER_FRAME:
            ticks += 1
            frame = self.stack[-1]
            result = frame.node.run(self.entity, ctx)

            if result == NodeResult.RUNNING:
                break  # akan dilanjutkan next tick

            self.stack.pop()

            if result == NodeResult.SUCCESS:
                next_node = frame.node.on_success
            else:
                next_node = frame.node.on_failure

            if next_node:
                self.stack.append(BehaviorFrame(
                    node=next_node,
                    caller=frame.caller,
                    callee=frame.callee,
                    temps=frame.temps
                ))
            else:
                # Selesai — terapkan perubahan motif
                if self.active_action:
                    for motive, delta in self.active_action.motive_changes.items():
                        self.entity.change_motive(motive, delta)
                self.active_action = None

    def block_for(self, seconds: float):
        """Blokir thread selama N detik (misal: durasi animasi)."""
        self.blocking = True
        self.block_timer = seconds


# ---------------------------------------------------------------------------
# Entitas (NPC atau pemain) di dalam VM
# ---------------------------------------------------------------------------
class BehaviorEntity:
    def __init__(self, name: str, motives: Optional[Dict[str, float]] = None):
        self.name = name
        self.motives: Dict[str, float] = motives or {
            "hunger":  80.0,
            "energy":  80.0,
            "social":  80.0,
            "fun":     80.0,
            "hygiene": 80.0,
        }
        self.attributes: Dict[str, Any] = {}
        self.thread = BehaviorThread(self)
        self._animation: str = "idle"
        self._on_animation_change: Optional[Callable] = None

    # -- Motif --
    def change_motive(self, key: str, delta: float):
        if key in self.motives:
            self.motives[key] = max(0.0, min(100.0, self.motives[key] + delta))

    def get_motive(self, key: str) -> float:
        return self.motives.get(key, 0.0)

    # -- Animasi (hook ke Ursina/Panda3D) --
    def set_animation(self, anim_name: str):
        self._animation = anim_name
        if self._on_animation_change:
            self._on_animation_change(anim_name)

    def on_animation_change(self, callback: Callable):
        """Daftarkan callback untuk sinkronisasi animasi ke Ursina."""
        self._on_animation_change = callback

    # -- Antrian aksi --
    def queue_action(self, action_name: str, priority: int = 0,
                     caller: Optional["BehaviorEntity"] = None):
        # Registry is module-global (defined below in this module)
        if action_name not in _ACTION_REGISTRY:
            print(f"[BehaviorVM] Aksi '{action_name}' tidak ditemukan!")
            return
        reg = _ACTION_REGISTRY[action_name]
        self.thread.push_action(QueuedAction(
            name=action_name,
            root_node=reg["node"],
            priority=priority,
            caller=caller,
            motive_changes=reg.get("motive_changes", {})
        ))

    def cancel_action(self, action_name: str):
        self.thread.cancel_action(action_name)

    def block_for(self, seconds: float):
        self.thread.block_for(seconds)


# ---------------------------------------------------------------------------
# Registry aksi global (seperti VMPrimitiveRegistration di FreeSO)
# ---------------------------------------------------------------------------
_ACTION_REGISTRY: Dict[str, Dict] = {}


def action(name: str, motive_changes: Optional[Dict[str, float]] = None,
           on_success: Optional[BehaviorNode] = None,
           on_failure: Optional[BehaviorNode] = None):
    """
    Decorator untuk mendaftarkan sebuah aksi ke VM.

    @action("tidur", motive_changes={"energy": +40})
    def tidur(entity, ctx):
        entity.set_animation("sleep")
        entity.block_for(3.0)
        return NodeResult.SUCCESS
    """
    def decorator(fn: Callable):
        node = BehaviorNode(
            name=name,
            fn=fn,
            on_success=on_success,
            on_failure=on_failure
        )
        _ACTION_REGISTRY[name] = {
            "node": node,
            "motive_changes": motive_changes or {}
        }
        return fn
    return decorator


def condition(name: str):
    """
    Decorator untuk node kondisi (tidak mengubah state, hanya return SUCCESS/FAILURE).

    @condition("lapar")
    def lapar(entity, ctx):
        return NodeResult.SUCCESS if entity.get_motive("hunger") < 30 else NodeResult.FAILURE
    """
    def decorator(fn: Callable):
        node = BehaviorNode(name=name, fn=fn)
        _ACTION_REGISTRY[name] = {"node": node, "motive_changes": {}}
        return fn
    return decorator


# ---------------------------------------------------------------------------
# Context global VM (seperti VMContext di FreeSO)
# ---------------------------------------------------------------------------
class BehaviorContext:
    def __init__(self):
        self.entities: Dict[str, BehaviorEntity] = {}
        self.world_time: float = 0.0        # jam game (0.0 - 24.0)
        self.globals: Dict[str, Any] = {}   # variabel global dunia


# ---------------------------------------------------------------------------
# VM utama — scheduler untuk semua entitas
# ---------------------------------------------------------------------------
class BehaviorVM:
    """
    Scheduler utama. Panggil vm.tick(dt) tiap frame.

    Contoh integrasi Ursina:
        vm = BehaviorVM()
        def update():
            vm.tick(time.dt)
    """
    def __init__(self):
        self.context = BehaviorContext()
        self._entities: List[BehaviorEntity] = []

    def add_entity(self, entity: BehaviorEntity):
        self._entities.append(entity)
        self.context.entities[entity.name] = entity

    def remove_entity(self, entity: BehaviorEntity):
        self._entities = [e for e in self._entities if e is not entity]
        self.context.entities.pop(entity.name, None)

    def tick(self, dt: float = 0.016):
        """Panggil ini tiap frame (atau tiap game tick)."""
        self.context.world_time = (self.context.world_time + dt / 60.0) % 24.0
        for entity in self._entities:
            entity.thread.tick(self.context, dt)

    def get_entity(self, name: str) -> Optional[BehaviorEntity]:
        return self.context.entities.get(name)


# ---------------------------------------------------------------------------
# Aksi-aksi bawaan untuk Lembah Karsa
# ---------------------------------------------------------------------------

@action("idle")
def _idle(entity: BehaviorEntity, ctx: BehaviorContext) -> NodeResult:
    entity.set_animation("idle")
    return NodeResult.SUCCESS


@action("tidur", motive_changes={"energy": 40.0})
def _tidur(entity: BehaviorEntity, ctx: BehaviorContext) -> NodeResult:
    entity.set_animation("sleep")
    entity.block_for(5.0)
    return NodeResult.SUCCESS


@action("makan", motive_changes={"hunger": 35.0, "fun": 5.0})
def _makan(entity: BehaviorEntity, ctx: BehaviorContext) -> NodeResult:
    entity.set_animation("eat")
    entity.block_for(3.0)
    return NodeResult.SUCCESS


@action("bicara", motive_changes={"social": 20.0, "fun": 10.0})
def _bicara(entity: BehaviorEntity, ctx: BehaviorContext) -> NodeResult:
    entity.set_animation("talk")
    entity.block_for(2.0)
    return NodeResult.SUCCESS


@action("bertani", motive_changes={"hunger": -5.0, "energy": -10.0, "fun": 5.0})
def _bertani(entity: BehaviorEntity, ctx: BehaviorContext) -> NodeResult:
    entity.set_animation("farm")
    entity.block_for(4.0)
    return NodeResult.SUCCESS


@condition("butuh_makan")
def _butuh_makan(entity: BehaviorEntity, ctx: BehaviorContext) -> NodeResult:
    return NodeResult.SUCCESS if entity.get_motive("hunger") < 30 else NodeResult.FAILURE


@condition("butuh_tidur")
def _butuh_tidur(entity: BehaviorEntity, ctx: BehaviorContext) -> NodeResult:
    return NodeResult.SUCCESS if entity.get_motive("energy") < 20 else NodeResult.FAILURE


@condition("malam_hari")
def _malam_hari(entity: BehaviorEntity, ctx: BehaviorContext) -> NodeResult:
    return NodeResult.SUCCESS if ctx.world_time >= 20.0 or ctx.world_time < 5.0 else NodeResult.FAILURE


# ---------------------------------------------------------------------------
# NPC sederhana dengan AI otomatis (pakai BehaviorVM)
# ---------------------------------------------------------------------------
class AutoNPC:
    """
    NPC yang secara otomatis memilih aksi berdasarkan kebutuhan motif.
    Tinggal panggil npc.update(dt) tiap frame.
    """
    NEED_THRESHOLDS = {
        "hunger":  ("makan",  30.0),
        "energy":  ("tidur",  20.0),
        "social":  ("bicara", 25.0),
    }

    def __init__(self, name: str, vm: BehaviorVM):
        self.entity = BehaviorEntity(name)
        self.vm = vm
        vm.add_entity(self.entity)
        self._last_auto_tick = 0.0

    def update(self, dt: float):
        self._last_auto_tick += dt
        if self._last_auto_tick < 1.0:
            return  # cek kebutuhan tiap 1 detik
        self._last_auto_tick = 0.0

        # Kalau tidak ada aksi dalam queue, pilih berdasarkan motif terendah
        if not self.entity.thread.queue and not self.entity.thread.stack:
            worst_motive = min(self.entity.motives, key=lambda k: self.entity.motives[k])
            if worst_motive in self.NEED_THRESHOLDS:
                action_name, threshold = self.NEED_THRESHOLDS[worst_motive]
                if self.entity.get_motive(worst_motive) < threshold:
                    self.entity.queue_action(action_name)
                    return
            self.entity.queue_action("idle")


# ---------------------------------------------------------------------------
# TEST / DEMO
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== Demo BehaviorVM Lembah Karsa ===\n")

    vm = BehaviorVM()
    npc = BehaviorEntity("Sari", motives={
        "hunger": 25.0,  # lapar!
        "energy": 60.0,
        "social": 80.0,
        "fun":    70.0,
        "hygiene": 75.0,
    })
    vm.add_entity(npc)

    # Hook animasi ke print (nanti ganti ke Ursina actor.play_animation)
    npc.on_animation_change(lambda anim: print(f"  [{npc.name}] Animasi: {anim}"))

    # Antri beberapa aksi
    npc.queue_action("makan", priority=10)   # tinggi karena lapar
    npc.queue_action("bicara", priority=5)
    npc.queue_action("bertani", priority=3)
    npc.queue_action("tidur", priority=1)

    print(f"Motif awal: {npc.motives}\n")

    # Simulasi 30 tick (tiap tick ~0.1 detik)
    for i in range(30):
        vm.tick(dt=0.5)

    print(f"\nMotif akhir: {npc.motives}")
    print("\nDemo AutoNPC:")
    auto = AutoNPC("Budi", vm)
    auto.entity.motives["energy"] = 10.0  # sangat mengantuk
    for _ in range(10):
        auto.update(dt=1.0)
        vm.tick(dt=1.0)
    print(f"Motif Budi setelah auto: {auto.entity.motives}")
