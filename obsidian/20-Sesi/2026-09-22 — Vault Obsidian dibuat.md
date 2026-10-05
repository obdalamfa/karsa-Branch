---
judul: Vault Obsidian dibuat — pencatatan progres pindah ke sini
tipe: sesi
tanggal: 2026-09-22
commit: 03d61bb
branch: claude/tender-allen-614l6y
tags: [sesi, meta, dokumentasi]
---

# 2026-09-22 — Vault Obsidian dibuat

Permintaan pemilik: *"pakai obsidian untuk mencatat semua progres mu di dalam
program game ini"*. Sesi ini tidak mengubah satu baris pun kode game — yang
dibangun adalah tempat mencatatnya.

## Yang dibangun

- **Vault `obsidian/`** dengan konfigurasi ikut ter-commit (`.obsidian/`): tema, graph berwarna per folder, plugin inti, folder templat.
- **41 nota**: beranda + 5 peta (`00-Peta/`), 9 tahap (`10-Tahapan/`), jurnal 7 sesi
  (`20-Sesi/`), 10 sistem (`30-Sistem/`), 6 bug (`40-Bug/`), 3 templat (`50-Templat/`).
- **`tools/catat_obsidian.py`** — menulis kerangka nota sesi langsung dari git,
  supaya mencatat lebih murah daripada tidak mencatat → [[Aturan Pencatatan]].
- **`CLAUDE.md`** — lima aturan yang lahir dari kegagalan nyata di repo ini,
  plus perintah mencatat, supaya sesi berikutnya tidak mengulanginya.
- Bagian **Catatan Progres** di `README.md` supaya vault ini ketemu tanpa perlu diberi tahu.

Sejarah enam commit (2026-05-27 → 2026-08-27) direkonstruksi dari pesan commit,
`--numstat`, dan `docs/TAHAPAN.md`.

## Temuan baru dari audit ulang

Bukan menyalin dokumen lama — tiga hal berikut ditemukan dengan memeriksa
kode hari ini:

| Temuan | Cara memeriksanya |
|---|---|
| `entity_mesh.py` (458 baris) **nol pemanggil** — yatim baru | `grep -rn "entity_mesh" --include=*.py .` |
| `choose_action()` / `autonomy_candidates()` masih **nol pemanggil** | `grep -rn "autonomy_candidates\|choose_action"` |
| `PLAY.md` menyuruh mengedit `_USE_VITABOY_HUMANS` yang **sudah tidak ada** | `grep -rn "USE_VITABOY"` → kosong |
| 92 file `.pyc` ter-commit, tidak ada `.gitignore` root | `git ls-files \| grep -c '\.pyc$'` |

Semuanya masuk [[Utang Teknis]].

## Batas kejujuran sesi ini

Mesin sesi ini **tidak punya `ursina`/`panda3d`**, jadi `tools/regress.py`
tidak bisa dijalankan ulang. Status "5/5 lulus" di seluruh vault adalah warisan
commit `7ed8d59`, bukan larian baru — dan itu ditulis eksplisit di
[[Status Sekarang]] supaya tidak ada yang salah kira.

Yang **bisa** diverifikasi tanpa GPU sudah diverifikasi: pembacaan kode, `grep`
pemanggil, hitungan baris, isi git.

> [!note] Kenapa hash-nya butuh commit kedua
> Nota ini ada **di dalam** commit `03d61bb`, jadi ia tidak mungkin memuat
> hash-nya sendiri. Hash-nya distempel di satu commit susulan yang tidak
> mengubah apa pun selain baris `commit:` di frontmatter ini.

## Tautan

[[Beranda]] · [[Aturan Pencatatan]] · [[Status Sekarang]]
