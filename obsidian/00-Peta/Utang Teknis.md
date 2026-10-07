---
judul: Utang Teknis
tipe: peta
diperbarui: 2026-10-07
tags: [moc, utang, status/terbuka]
---

# Utang Teknis

Daftar hal yang diketahui berutang. Setiap butir punya bukti, bukan firasat.

## ✅ `entity_mesh.py` — terbukti jalan dan ditandai (2026-10-03)

458 baris tanpa pemanggil, dan statusnya sempat "tidak jelas". Sekarang jelas:
16 pemeriksaan di `_bench/probes/probe_entity_mesh.py` lulus semua, dan kepala
modulnya menyatakan terang bahwa ia menunggu [[Tahap 7 — Misteri dan entitas]].
Tidak disambungkan supaya tidak melompati urutan tahap →
[[Tahap 2 — Verifikasi modul yatim]].

## ✅ Autonomi — lunas, oleh branch sebelah

Dulu utang paling murah di daftar ini: dua fungsi matang tanpa pemanggil.
Sejak merge `342facf` ia dipanggil dari `game/npc.py:92` — kode game yang
hidup, bukan harness → [[Tahap 5 — Autonomi]].

## ✅ 92 file `.pyc` — lunas, oleh base branch

`git ls-files | grep -c '\.pyc$'` → **92**, bytecode `cpython-314` yang tidak
relevan dan bikin diff berisik.

**Sudah:** `.gitignore` di root (2026-09-22). Pemicunya langsung: satu larian
regresi di sesi itu menaburkan **70+ berkas `.pyc` baru** ke `git status`,
plus mengubah cache biner `game/vitaboy/.vitaboy_index.pkl`. Tanpa ignore,
semuanya berisiko ikut ter-commit hanya karena seseorang mengetik `git add -A`.

**Juga sudah, dan bukan oleh sesi ini:** base branch melepas 92 berkas yang
terlanjur dilacak. Diperiksa 2026-10-03:

```
git ls-files | grep -c '\.pyc$'   →  0
```

Nota ini sempat mencatatnya sebagai utang terbuka beberapa jam setelah ia
sebenarnya lunas — contoh kecil kenapa [[Status Sekarang]] harus diperiksa
ulang terhadap repo, bukan terhadap catatan sebelumnya.

## 🟡 `PLAY.md` sudah melenceng dari kode

Diperiksa 2026-09-22:

| Klaim di `PLAY.md` | Kenyataan |
|---|---|
| "Edit `game/entities.py:736` → `_USE_VITABOY_HUMANS = True`" | Flag itu **tidak ada lagi** di mana pun; `entities.py` cuma 603 baris. Vitaboy sekarang selalu aktif dengan gagal-lunak → [[Avatar Vitaboy]] |
| "Fixed di `player.py:610` — portal cooldown 0.8s" | Baris 610 sekarang berisi perbaikan [[Terjepit permanen]], bukan portal |

Rujukan baris di dokumen memang selalu membusuk. Yang layak diperbaiki minimal
klaim yang **menyesatkan pemain**, yaitu instruksi Vitaboy.

## ✅ Workflow CI — terbukti hijau di GitHub

Sudah tidak jadi utang. `.github/workflows/regresi.yml` berjalan **4 kali**
di GitHub Actions (push + pull_request untuk dua commit), semuanya `success`,
dengan artifact bukti 3,28 MB terunggah. Nama paket apt yang ditebak untuk
`ubuntu-latest` ternyata benar.

## ✅ Lunas 2026-09-22

| Utang | Sebelumnya | Sekarang |
|---|---|---|
| `requirements.txt` hanya `ursina` | `import pygame` gagal → game tidak bisa di-import di mesin bersih | `pygame` + `pillow` tercantum, masing-masing dengan alasannya |
| font HUD tidak ketemu | game mati di baris pertama HUD di mesin tanpa Montserrat | [[Font HUD tidak ketemu di mesin bersih]] |
| `regress.py`/`capture.py` menunjuk `ROOT/'fonts'` | folder itu tidak ada | diarahkan ke `assets/fonts` |
| `motif_waras` mengotori keadaannya | scene ke-14 apa pun gagal palsu | [[Pemeriksaan motif mengotori keadaan]] |
| regresi hanya jalan kalau diingat | jaring digantung tapi tidak dipasang | jalan otomatis di CI |

## ✅ Pemeriksaan `arah_maju` — lunas 2026-10-06

Dibuat 2026-10-04 dan sempat menuduh enam scene sehat, jadi diturunkan jadi
lapor-saja. Sekarang memvonis lagi, dan terbukti dua arah: 14/14 lulus dengan
perbaikan, 6/6 GAGAL (177–179°) dengan bug dipasang kembali.

Catatan yang layak disimpan: dugaan pertama tentang sebabnya — kontaminasi
antar-scene — **salah**, dan itu terukur (selisih posisi lokal lawan dunia
0,000 di keempat belas scene). Sebab sebenarnya: acuan diambil sesudah pemain
berjalan, dan jendela ukur terlalu panjang sehingga gesekan dinding menumpuk.
→ [[2026-10-06 — Penjaga arah jadi penjaga sungguhan]]

## 🟠 15 dari 16 probe yang dikutip kode tidak ada di repo

```
grep -rhao "_bench/probes/probe_[a-z_]*\.py" --include=*.py game/ tools/ | sort -u
```

16 nama probe dikutip komentar kode sebagai dasar keputusan. Yang benar-benar
ada: **satu**, `probe_font.py` (di-commit 2026-10-03). Sisanya hilang bersama
sesi yang menulisnya, karena `_bench/.gitignore` dulu memakai pola `*`.

Akibatnya angka-angka penting — 0,288 ms lawan 6,387 ms per avatar,
"mode=dialog 0,00 unit MEMBEKU", "keempat arah 0,00" — tidak bisa dijalankan
ulang siapa pun. Masih dipercaya, tapi tidak bisa diaudit.

Pola aturannya sudah diperbaiki base branch: sekarang hanya **keluaran** yang
diabaikan, alat ukurnya bisa di-commit. Yang tersisa: tiap probe baru harus
ikut masuk → [[2026-10-03 — Probe pertama yang bisa diperiksa]].

## 🟠 Konten yang lengkap tapi tidak tersambung (2026-10-07)

Lima temuan dari pemetaan sistem konten → [[Peta Sistem Konten]]. Semuanya
konten yang **sudah selesai ditulis** lalu berhenti sebelum ada yang
memakainya — pola yang sama dengan modul yatim di [[Tahap 2 — Verifikasi modul yatim]],
kali ini di lapisan data.

| Utang | Buktinya | Kenapa layak diperbaiki |
|---|---|---|
| 16 dari 24 benih tidak bisa dibeli | `grep -rn SEED_SHOP_ROWS` → nol pemanggil; `len(SHOP_ITEMS)` 10 lawan `len(CROPS)` 24 | Alasan yang ditulis `crops.py:335` (panel toko belum berhalaman) **sudah tidak berlaku** — `panels.py:861 _page_slice()` sudah berhalaman dan dipakai di `:879` dan `:950`. Syaratnya terpenuhi, pemasangannya belum |
| `SEASONAL_EVENTS` nol pemanggil | `grep -rn SEASONAL_EVENTS --include=*.py` → hanya `data.py:523` | Empat festival lengkap dengan hari dan scene-nya; tidak ada yang membacanya |
| 25 dari 33 model tanpa pemuat | `load_model_file()` hanya dipanggil dengan 5 nama dari `get_npc_model_name()` | 24 `au-*.glb` + `sari_idle.glb` menumpang di repo tanpa jalur pemakaian |
| `ORE_SPAWN_TABLE` baris 14–15 mati, dan `13` ditulis ulang sebagai angka | `DUNGEON_MAX_LEVEL = 13`; `interaction_controller.py:190` dan `:336` menulis `== 13` | Dua sumber kebenaran untuk lantai maksimum; mengubah satu akan meninggalkan yang lain |
| `random_stairs_chance()` nol pemanggil | `grep -rn random_stairs_chance` → hanya `dungeon.py:179` | |

## 🟡 Detektor penyimpangan scene tidak dijalankan siapa pun (2026-10-07)

`tools/scene_export.py --check` membandingkan kode scene dengan berkas
`game/scenes/*.json` dan keluar 1 kalau berbeda. Hari ini keduanya cocok
(**15/15**, dibuktikan dengan larian sungguhan), dan `scene_roundtrip.py` juga
hijau 15/15.

Yang berutang bukan keadaannya, tapi penjaganya: CI hanya menjalankan
`tools/regress.py`, dan `regress.py` tidak menyebut `scene_export`. Penjaga
yang digantung tapi tidak dipasang adalah persis utang yang dilunasi
2026-09-22 untuk regresi → [[Regresi]].

## 🟡 `docs/EKONOMI.md` dikutip tapi tidak ada (2026-10-07)

`data.py:11` dan `economy.py:20` menunjuk ke dokumen itu untuk perhitungan
harga per energi. Berkasnya tidak ada di `docs/`. Perhitungannya sendiri masih
terbaca di komentar `data.py`, jadi yang hilang adalah alamatnya, bukan isinya.

## 🔴 Dua utang besar yang sudah punya rumah sendiri

- [[Arah WASD basis sumbu salah]] — jangan ubah tanda sebelum ada probe kokoh.
- [[Tahap 3 — Performa]] — 4–29 FPS, belum pernah diprofil.
