---
judul: Probe pertama yang bisa diperiksa
tipe: sesi
tanggal: 2026-10-03
commit:
tags: [sesi, bukti, dokumentasi]
---

# 2026-10-03 — Probe pertama yang bisa diperiksa

Kecil, tapi menutup lubang yang menyentuh seluruh cara proyek ini mengklaim
sesuatu terbukti.

## Yang berubah

`_bench/probes/probe_font.py` di-commit — probe yang membuktikan
[[Font HUD tidak ketemu di mesin bersih]].

Dulu ia tidak mungkin di-commit: `_bench/.gitignore` memakai pola `*` yang
menelan seluruh isi folder. Base branch sudah mengubahnya supaya **keluaran**
saja yang diabaikan (`*.png`, `shots/`, `regress/`, `progress.jsonl`),
sementara dokumen dan alat ukur bisa masuk. Alasan yang ditulis di sana persis
alasan yang penting di sini: komentar kode menyebut
"Diukur di `_bench/probes/probe_*.py`" sebagai dasar keputusan, dan tidak satu
pun bisa diperiksa pembaca.

## Temuan: 15 dari 16 probe yang dikutip tidak ada

```
grep -rhao "_bench/probes/probe_[a-z_]*\.py" --include=*.py game/ tools/ | sort -u
```

16 probe dikutip. Yang benar-benar ada di repo: **satu** — `probe_font.py`,
yang baru di-commit ini. Lima belas lainnya hilang bersama sesi yang
menulisnya.

Jadi angka-angka yang jadi dasar keputusan besar di proyek ini — 0,288 ms
lawan 6,387 ms per avatar ([[Avatar Vitaboy]]), "mode=dialog 0,00 unit MEMBEKU"
([[Pemain beku saat panel terbuka]]), "keempat arah menghasilkan perpindahan
0,00" ([[Terjepit permanen]]) — semuanya **tidak bisa dijalankan ulang oleh
siapa pun**. Angkanya masih dipercaya karena ditulis oleh yang mengukurnya,
tapi ia bukti yang tidak bisa diaudit.

Itu bukan alasan membuang angkanya. Itu alasan **tiap probe baru di-commit**,
mulai dari yang ini.

## Bukti

- `git check-ignore` → `probe_font.py` tidak lagi diabaikan.
- `ls _bench/probes/` → satu berkas; `grep` kutipan → 16 nama berbeda.

## Yang belum beres

Lima belas probe yang hilang tidak bisa dipulihkan — sesinya sudah lewat. Yang
bisa dilakukan: menulis ulang yang masih dibutuhkan saat klaimnya diuji ulang,
dan itu paling mendesak untuk [[Arah WASD belum terverifikasi]], yang justru
gagal **karena** alat ukurnya tidak bisa dipercaya.

## Tautan

[[2026-09-22 — Regresi jalan sungguhan, CI dipasang]] · [[Utang Teknis]] · [[Aturan Pencatatan]]
