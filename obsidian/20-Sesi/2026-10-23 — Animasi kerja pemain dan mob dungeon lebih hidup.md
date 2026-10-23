---
judul: "Animasi kerja pemain dan mob dungeon lebih hidup"
tipe: sesi
tanggal: 2026-10-23
commit: b2a9151
skala: 8 file sumber, +750 / −27 baris
tags: [sesi]
---

# 2026-10-23 — Animasi kerja pemain dan mob dungeon lebih hidup

## Pesan commit

- char_actor: klip kerja dibaur masuk 0,07 dtk / keluar 0,22 dtk (dulu
  bobot dibanting 0->1->0), poros + pinggang untuk lapisan prosedural
- jus_gerak: ancang-ancang, hentakan (gepeng, dorongan kamera, debu),
  ikut-gerak; juga untuk aksi tanpa klip (bend, gosok, bicara)
- mob_gerak: napas, lenggang/lompat per jenis, ancang-ancang kemerahan,
  kilat kena pukul, mati berputar-menyusut 0,6 dtk sebelum dihapus
- entities: kilat no-op dibuang, kematian logis di frame itu, model
  dihapus sesudah animasi
- tools/probe_gerak.py (12 cek, 4 mutasi tertangkap) + baris regresi

## Berkas yang berubah

| Berkas | + | − |
|---|---:|---:|
| `game/char_actor.py` | +56 | −16 |
| `game/entities.py` | +24 | −9 |
| `game/jus_gerak.py` | +185 | −0 |
| `game/mob_gerak.py` | +191 | −0 |
| `game/player.py` | +19 | −2 |
| `obsidian/40-Bug/Kilat kena pukul mob tidak pernah terlihat.md` | +54 | −0 |
| `tools/probe_gerak.py` | +194 | −0 |
| `tools/regress.py` | +27 | −0 |

## Bukti

<!-- ISI MANUAL. Angka, larian regresi, atau probe — skrip sengaja tidak
     menebak bagian ini. Lihat [[Aturan Pencatatan]]. -->

- `tools/probe_gerak.py`: 12/12 lulus. Pinggang condong P −15,4..+9,0
  selama cangkul, bobot klip dibaur `[0.0, 0.43, 1.0, 0.45, 0.05]`, bend
  |P| 15,6 dengan sy 0,83, kilat mob colorScale 2,2, dan ancang-ancang
  (1,28; 0,86; 0,86).
- Mutasi, masing-masing tertangkap:
  - bobot dibanting → 11/12
  - jus dimatikan → 9/12
  - `animasikan` no-op → 8/12
  - destroy seketika → 11/12
- Regresi lokal: 14/14 scene lulus, juga baris otonomi dan sims. Baris
  global sisanya sedang berjalan saat nota ini ditulis.
- CI di b2a9151 tidak melaporkan suite yang gagal.
- Tangkapan visual sudah dilihat: cangkul (badan condong ke belakang
  dengan alat terangkat), jongkok, dan mob (pocong, genderuwo, kelelawar)
  yang memerah saat ancang-ancang.

## Yang belum beres

<!-- ISI MANUAL. Ditulis apa adanya, termasuk yang alat ukurnya belum bisa
     dipercaya. -->

- Rasa geraknya belum dinilai pemilik di mesin sendiri. Semua tangkapan
  dibuat dengan render CPU, sekitar 100 ms/frame.
- Dorongan kamera (`camera.y -= punch`) tidak punya cek probe.
- Animasi kematian dinilai dari skala model saja, belum dari tampilannya.
- Mob memakai model .obj statis, jadi gerak anggota tubuh (sayap, kaki)
  belum bisa dibuat tanpa rig.
- Keputusan tebing mulut gua di mountain masih menunggu pemilik.

## Tautan

[[Status Sekarang]] · [[Peta Progres]]
