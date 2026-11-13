---
judul: "Interaksi di lapangan terbuka melempar TypeError"
tipe: bug
status: selesai
ditemukan: "2026-10-22"
commit_perbaikan: (sesi kamera Q/E, 2026-10-22)
dijaga_oleh: tools/probe_kamera_qe.py (baris "kamera Q/E" di regress.py)
tags: [bug, status/selesai, input]
---

# 🐞 Interaksi di lapangan terbuka melempar TypeError

## Gejala

Tombol interaksi (dulu [E], kini [F]) ditekan di petak yang tidak punya
NPC, perabot, surat, Peti Kirim, atau petak garapan di dekatnya:

```
TypeError: EntitiesManager.try_capture_wild() got an unexpected keyword argument 'kinds'
```

Exception itu naik lewat `app.input` Ursina, jadi game berhenti. Pemain tidak
perlu berbuat aneh untuk memicunya: cukup menekan tombol aksi di tengah ladang.

## Sebab

`interaction_controller._try_harvest_wild` memanggil
`try_capture_wild(..., kinds=HARVESTABLE)`, tapi parameter `kinds` tidak ada
lagi di tanda tangan `game/entities.py`. Pola yang sama dengan
[[Majelis Batin hilang di merge 5683e79]]: pemanggil selamat, definisinya
tidak. Tidak ada probe yang pernah menekan tombol aksi di lapangan kosong,
jadi tidak ada yang tahu.

## Perbaikan

`try_capture_wild(self, tx, ty, state, kinds=None)`. Kalau `kinds` diisi,
jenis lain dilewati, sehingga interaksi hanya memetik herba/beri/jamur/mandrake.
Kunang-kunang tetap lewat tangkap ([Shift]+[F]).

## Bukti

- Ditemukan oleh `tools/probe_kamera_qe.py` yang baru: langkah "[F] saja
  memanggil interaksi" di ladang (15,15) meledak dengan TypeError di atas.
- Sesudah perbaikan: 11/11 lulus.
- Mutasi (parameter `kinds` dicabut lagi) → "probe meledak: TypeError", 10/11.
