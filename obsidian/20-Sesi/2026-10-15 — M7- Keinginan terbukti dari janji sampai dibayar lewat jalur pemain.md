---
judul: "M7: Keinginan terbukti dari janji sampai dibayar lewat jalur pemain"
tipe: sesi
tanggal: 2026-10-15
commit: e879ea5
skala: 4 file sumber, +107 / −4 baris
tags: [sesi]
---

# 2026-10-15 — M7: Keinginan terbukti dari janji sampai dibayar lewat jalur pemain

## Pesan commit

Mesin wishes (e72577b) sudah tersambung, tapi bukti terakhirnya basi:
probe_wishes.py macet di mode sinema sejak adegan pembuka ditambahkan
(5/11). Kini menandai adegan sudah ditonton seperti regress.py, dan
ditambah uji ujung-ke-ujung: tombol p+angka menjanjikan 'Panen 5 hasil
kebun', tombol 4 memilih Panen, space memanen 5 lobak, loop Game3D.update
membayar +60 Kebahagiaan tanpa panel dibuka. 17/17; pembayaran di app.py
dimatikan -> GAGAL. Regresi 14/14.

## Berkas yang berubah

| Berkas | + | − |
|---|---:|---:|
| `_bench/progress.jsonl` | +1 | −0 |
| `obsidian/10-Tahapan/Gauntlet Oktober 2026 — 10 Milestone.md` | +1 | −1 |
| `obsidian/10-Tahapan/Tahap 4 — Wishes.md` | +11 | −3 |
| `tools/probe_wishes.py` | +94 | −0 |

## Bukti

- `tools/uji_wishes.py`: 41/41 (mesin murni).
- `tools/probe_wishes.py` sebelum diperbaiki: **5/11**. Enam gagal dengan `mode=sinema` karena adegan pembuka menelan tombol `p`.
- Sesudah: **17/17**, termasuk lima pemeriksaan baru ujung-ke-ujung: tawaran memuat "Panen 5 hasil kebun apa pun" → janji lewat tombol → tombol `4` memilih Panen → `space` memanen 5/5 lobak → loop update membayar +60 Kebahagiaan, dengan janji kosong dan mode tetap `hud`.
- Mutasi: `self.panels._bayar_keinginan()` di `app.py` diganti `pass` → 16/17, dan yang GAGAL "loop update membayar tanpa panel dibuka". Berkasnya dipulihkan, diff kosong.
- Regresi penuh 14/14.

## Yang belum beres

- DoD menyebut "lahir dari motif/hubungan". Yang terbukti: tawaran lahir dari konteks (benih, alat, gua) dan hubungan ("Capai 4 hati dengan Pak Joko"). **Belum ada wish yang lahir dari motif**, misalnya lapar mendorong wish memasak.
- Bias sifat di `_bobot()` masih kait kosong, menunggu Tahap 6.
- Cek `panel wishes` di regresi masih 12 pemeriksaan; uji ujung-ke-ujung baru hanya ada di probe dan belum masuk regresi.

## Tautan

[[Status Sekarang]] · [[Peta Progres]]
