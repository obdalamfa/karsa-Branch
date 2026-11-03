---
judul: "Kilat kena pukul mob tidak pernah terlihat, mob mati lenyap seketika"
tipe: bug
status: selesai
ditemukan: "2026-10-23"
commit_perbaikan: (lihat nota sesi 2026-10-23, animasi gerak)
dijaga_oleh: tools/probe_gerak.py (baris "animasi gerak" di regress.py)
tags: [bug, status/selesai, mob, animasi]
---

# 🐞 Kilat kena pukul mob tidak pernah terlihat, mob mati lenyap seketika

## Gejala

Mob dungeon yang dipukul tidak berkedip sama sekali. Mob yang HP-nya habis
lenyap di frame yang sama, tanpa jatuh, menyusut, atau memudar. Ini
terjadi walau `mob.py` sudah punya `dying`, `death_ms`, dan `dmg_flash_ms`.

## Sebab

Di `EntitiesManager.update` (`game/entities.py`), kedua cabang kilat
menyetel warna yang sama:

```python
if actor.dmg_flash_ms > 0:
    actor.color = color.white
else:
    actor.color = color.white # Revert to normal
```

Putih adalah warna dasar mob, jadi tidak ada yang berubah. Cabang kematian
memanggil `destroy(actor)` langsung saat `hp <= 0`, sehingga `dying` dan
`death_ms` tidak pernah dipakai. Ini kasus aturan #4: bahannya ada tapi
tidak punya pemanggil.

## Perbaikan

`game/mob_gerak.py` menganimasikan transform model tiap frame sesudah
`sync_visuals`:

- kilat memakai `setColorScale(2.2, …)` dan dipicu oleh HP yang turun lewat
  jalur serang mana pun
- mati: logikanya (s.mobs, bendera naga) tetap jalan di frame kematian,
  sedangkan model berputar, menyusut, dan tenggelam selama 0,6 dtk sebelum
  `destroy`

## Bukti

`tools/probe_gerak.py` lulus 12/12. Ada dua mutasi yang dipasang ulang:

- `animasikan` dijadikan no-op: probe gagal 4 cek (napas, ancang-ancang,
  kilat, animasi mati).
- `destroy` seketika: probe gagal di "mob mati tidak lenyap dalam satu
  frame".
