---
judul: "Kebal sesudah dipukul mob hilang dalam satu frame"
tipe: bug
status: selesai
ditemukan: "2026-10-23"
commit_perbaikan: (lihat nota sesi 2026-10-23, reaksi kena pukul)
dijaga_oleh: tools/probe_gerak.py (3 cek "kena", baris "animasi gerak" di regress.py)
tags: [bug, status/selesai, combat, animasi]
---

# 🐞 Kebal sesudah dipukul mob hilang dalam satu frame

## Gejala

Saat pemain dipukul mob, HP-nya turun tapi tubuhnya tidak bereaksi:
tidak berkedip dan tidak tersentak. Masa kebal 600 ms
(`INVULN_AFTER_HIT_MS`) juga tidak pernah bertahan, sehingga beberapa mob
bisa memukul beruntun tanpa jeda.

Terukur lewat jalur asli: genderuwo dipasang di sebelah pemain di dungeon
dan AI-nya dibiarkan menyerang.

```
frame pukulan   invuln_timer_ms 600   player._invuln 0
frame berikut   invuln_timer_ms   0   player._invuln 0
```

## Sebab

Ada dua penyebab:

1. `mob.py` menulis kebal ke `state.invuln_timer_ms`. `Player.tick` lalu
   menyalin ke arah sebaliknya, `s.invuln_timer_ms = self._invuln`.
   Karena `_invuln` tidak pernah diisi siapa pun, nilai yang ditulis mob
   tertimpa 0 di frame berikutnya.
2. Kedip merah mewarnai `self.body`. Pada rig CharActor, `self.body` hanya
   `Entity(parent=p)` kosong, jadi kedipnya tidak terlihat walaupun
   kebalnya ada.

Penulis lain, `combat_controller.receive_damage`, tidak punya pemanggil
(aturan #4), jadi ia tidak pernah menutupi bug ini.

## Perbaikan

- `Player.tick` mengambil kebal dari state lebih dulu. Jika nilainya naik
  dari 0, pukulan baru menyalakan lapisan `jus_gerak` mode `kena`: tersentak
  ke belakang sekitar 60 ms, tubuh memendek, kamera terdorong, lalu pulih
  dengan sedikit lewat.
- Kedip merah dipasang di `CharActor.poros` melalui `setColorScale`.

## Bukti

- `tools/probe_gerak.py` lulus 15/15. Kebal turun 548 → 495 → 434 → 376 ms
  per frame, P pinggang maksimum 14,6, dan kedip merah terlihat.
- Mutasi: sinkronisasi dimatikan, lalu 3 cek "kena" GAGAL (invuln
  `[0, 0, 0, 0]`).
