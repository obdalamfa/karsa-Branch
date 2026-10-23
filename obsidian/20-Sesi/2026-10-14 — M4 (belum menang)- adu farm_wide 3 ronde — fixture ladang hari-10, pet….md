---
judul: "M4 (belum menang): adu farm_wide 3 ronde — fixture ladang hari-10, petak garapan hangat bergundukan"
tipe: sesi
tanggal: 2026-10-14
commit: 9727df9
skala: 6 file sumber, +1389 / −8 baris
tags: [sesi]
---

# 2026-10-14 — M4 (belum menang): adu farm_wide 3 ronde — fixture ladang hari-10, petak garapan hangat bergundukan

## Pesan commit

r1: patokan memotret ladang yang digarap, kita memotret hari pertama. Fixture
ladang_hari10_save.json dibuat dengan plant_payload() asli (70 petak, tahap
tumbuh tersebar); capture.py dapat --save (menolak menimpa save pemain).
r2: "tanah di atas tanah" -- petak garapan kini cokelat hangat, lebih tinggi
dan sempit seperti bedengan (luminans petak 46->36 terhadap tanah 66->70).
r3 masih kalah: kamera jauh/tinggi, cahaya datar, tidak ada kehidupan.
Regresi 14/14.

## Berkas yang berubah

| Berkas | + | − |
|---|---:|---:|
| `game/world.py` | +10 | −5 |
| `obsidian/10-Tahapan/Gauntlet Oktober 2026 — 10 Milestone.md` | +1 | −1 |
| `tools/capture.py` | +11 | −1 |
| `tools/fixtures/buat_save_ladang.py` | +61 | −0 |
| `tools/fixtures/ladang_hari10_save.json` | +1303 | −0 |
| `tools/gauntlet_capture.py` | +3 | −1 |

## Bukti

Kritikus segar tiap ronde, buta (`bar_gate.py pair`/`reveal`), bar AWL `farm_wide`:

| Ronde | Vonis | Celah terbesar menurut kritikus |
|---|---|---|
| r1 | patokan menang | ladang kita satu bidang tanah datar tanpa petak; ternyata yang dipotret ladang hari pertama yang belum dicangkul |
| r2 | patokan menang | "tanah di atas tanah": petak gelap kusam di atas zona cokelat, dipisah jalan cokelat |
| r3 | patokan menang | kamera terlalu jauh/tinggi, cahaya datar tanpa bayangan, tidak ada kehidupan |

- Luminans petak garapan 46 → 36, tanah di sekitarnya ±66 (diukur di tangkapan r2/r3).
- Percobaan mengganti dasar zona ladang ke `sand_ground` hanya mengubah luminans 66 → 70, jadi **dikembalikan** dan tidak ikut di-commit.
- Regresi penuh setelah perubahan petak: 14/14.

## Yang belum beres

- M4 belum menang. Celah r3 yang tersisa: (1) sudut/jarak kamera `farm_wide`, (2) cahaya matahari terarah dan bayangan, (3) kehidupan di sekitar ladang (hewan, properti), (4) HUD yang menutupi layar.
- Cat zona ladang (`Zone(... TANAH_LADANG)`) nyaris tidak berpengaruh pada piksel. Kemungkinan ubin `D` digambar di atasnya, tapi **belum terverifikasi**.
- Fixture memperlihatkan teks tutorial "Baca surat" di hari 10, karena quest_stage masih 0. Ini artefak fixture, bukan bug game.

## Tautan

[[Status Sekarang]] · [[Peta Progres]]
