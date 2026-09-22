---
judul: Utang Teknis
tipe: peta
diperbarui: 2026-09-22
tags: [moc, utang, status/terbuka]
---

# Utang Teknis

Daftar hal yang diketahui berutang. Setiap butir punya bukti, bukan firasat.

## 🟠 `entity_mesh.py` yatim — 458 baris tanpa pemanggil

Ditambahkan di [[2026-08-27 — Tata letak, avatar native, tukang mesh]] sebagai
"tukang mesh untuk kosakata rupa entitas". Diperiksa 2026-09-22:

```
grep -rn "entity_mesh" --include=*.py .   → hanya file itu sendiri
```

Ia sendiri memakai `entity_style.py`, tapi tidak ada satu pun modul yang
memakainya. Efeknya di game: **nol**. Ini pola yang persis sama dengan yang
ditangani [[Tahap 2 — Verifikasi modul yatim]] — modul mendarat lengkap saat
agennya kehabisan sesi, tepat sebelum disambungkan.

Pilihannya dua, dan keduanya jujur: sambungkan ke jalur render entitas, atau
tandai eksplisit sebagai belum dipakai. Yang tidak boleh: membiarkannya
terlihat seolah sudah bekerja.

## 🟠 Autonomi sudah jadi tapi tidak dipanggil

`motives.choose_action()` (`motives.py:295`) dan `objects.autonomy_candidates()`
(`objects.py:148`) ada dan teruji, tapi `grep` 2026-09-22 menemukan **nol**
pemanggil di luar definisinya. Ini persis yang dicatat [[Tahap 5 — Autonomi]]:
termurah, dampak paling besar, tinggal disambung.

## 🟡 92 file `.pyc` ikut ter-commit — separuh lunas

`git ls-files | grep -c '\.pyc$'` → **92**, bytecode `cpython-314` yang tidak
relevan dan bikin diff berisik.

**Sudah:** `.gitignore` di root (2026-09-22). Pemicunya langsung: satu larian
regresi di sesi itu menaburkan **70+ berkas `.pyc` baru** ke `git status`,
plus mengubah cache biner `game/vitaboy/.vitaboy_index.pkl`. Tanpa ignore,
semuanya berisiko ikut ter-commit hanya karena seseorang mengetik `git add -A`.

**Belum:** 92 berkas yang sudah terlanjur dilacak tetap dilacak — `.gitignore`
tidak berlaku surut. Melepasnya butuh `git rm -r --cached` sekali, dan karena
itu menyentuh 92 berkas ia pantas jadi commit tersendiri, bukan disisipkan ke
commit lain.

## 🟡 `PLAY.md` sudah melenceng dari kode

Diperiksa 2026-09-22:

| Klaim di `PLAY.md` | Kenyataan |
|---|---|
| "Edit `game/entities.py:736` → `_USE_VITABOY_HUMANS = True`" | Flag itu **tidak ada lagi** di mana pun; `entities.py` cuma 603 baris. Vitaboy sekarang selalu aktif dengan gagal-lunak → [[Avatar Vitaboy]] |
| "Fixed di `player.py:610` — portal cooldown 0.8s" | Baris 610 sekarang berisi perbaikan [[Terjepit permanen]], bukan portal |

Rujukan baris di dokumen memang selalu membusuk. Yang layak diperbaiki minimal
klaim yang **menyesatkan pemain**, yaitu instruksi Vitaboy.

## 🟡 Workflow CI belum pernah jalan di GitHub

`.github/workflows/regresi.yml` (2026-09-22) terbukti lewat perintah yang
**identik** di mesin lokal — 14/14 lulus di atas Xvfb + Mesa. Yang belum
terbukti: nama paket apt di runner `ubuntu-latest`, dan apakah `actions/*`
versi yang dipakai tersedia. Larian pertamanya di PR adalah buktinya.

## ✅ Lunas 2026-09-22

| Utang | Sebelumnya | Sekarang |
|---|---|---|
| `requirements.txt` hanya `ursina` | `import pygame` gagal → game tidak bisa di-import di mesin bersih | `pygame` + `pillow` tercantum, masing-masing dengan alasannya |
| font HUD tidak ketemu | game mati di baris pertama HUD di mesin tanpa Montserrat | [[Font HUD tidak ketemu di mesin bersih]] |
| `regress.py`/`capture.py` menunjuk `ROOT/'fonts'` | folder itu tidak ada | diarahkan ke `assets/fonts` |
| `motif_waras` mengotori keadaannya | scene ke-14 apa pun gagal palsu | [[Pemeriksaan motif mengotori keadaan]] |
| regresi hanya jalan kalau diingat | jaring digantung tapi tidak dipasang | jalan otomatis di CI |

## 🔴 Dua utang besar yang sudah punya rumah sendiri

- [[Arah WASD belum terverifikasi]] — jangan ubah tanda sebelum ada probe kokoh.
- [[Tahap 3 — Performa]] — 4–29 FPS, belum pernah diprofil.
