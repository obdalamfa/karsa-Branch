---
judul: Aturan Pencatatan
tipe: peta
diperbarui: 2026-09-22
tags: [moc, meta]
---

# Aturan Pencatatan

Vault ini hanya berguna kalau isinya bisa dipercaya. Empat aturan, dan alasan
tiap aturan diambil dari kegagalan nyata di proyek ini.

## 1. Satu commit = satu catatan sesi

Setiap commit dapat satu nota di `20-Sesi/`, dinamai
`YYYY-MM-DD — judul ringkas.md`, dengan `commit:` di frontmatter. Jurnalnya
kronologis, tidak pernah ditulis ulang — kalau kesimpulannya berubah, tulis
catatan baru yang menautkan yang lama.

## 2. Klaim tanpa bukti tidak ditulis sebagai fakta

Verifikasi manual di proyek ini sudah gagal dua kali: WASD dinyatakan beres
padahal belum, dan dua kali sebuah metode disisipkan di tengah fungsi sehingga
fungsi induknya mati total. Karena itu:

- **Selesai** hanya kalau ada larian `tools/regress.py`, probe di `_bench/`, atau angka.
- **Belum terverifikasi** ditulis apa adanya, lengkap dengan alasan kenapa alat ukurnya tidak bisa dipercaya — contoh: [[Arah WASD belum terverifikasi]].
- Kalau pemeriksaan tidak bisa dijalankan di mesin itu, catat **itu** juga, jangan diam-diam mewarisi status lama.

## 3. Status hidup di satu tempat

[[Status Sekarang]] adalah satu-satunya nota yang boleh ditimpa. Tahapan,
sistem, dan bug menyimpan status di frontmatter `status:` supaya bisa
di-`grep` dan di-query.

Nilai yang dipakai: `selesai` · `jalan` · `belum` · `terbuka` · `macet`.

## 4. Bug dapat nota sendiri kalau pernah nyata

Folder `40-Bug/` bukan daftar kemungkinan — isinya bug yang **pernah terjadi**,
tiap satu terikat pada satu pemeriksaan di [[Regresi]]. Itu yang membedakan
jaring pengaman dari ritual tes.

---

## Alat: `tools/catat_obsidian.py`

Menulis kerangka catatan sesi langsung dari git, supaya mencatat lebih murah
daripada tidak mencatat.

```bash
python3 tools/catat_obsidian.py --status     # commit mana yang belum punya nota
python3 tools/catat_obsidian.py              # buat nota untuk HEAD
python3 tools/catat_obsidian.py --commit d8da814
python3 tools/catat_obsidian.py --semua      # semua commit yang belum tercatat
```

Skrip ini **tidak** mengarang isi: ia menyalin pesan commit, daftar file, dan
angka baris, lalu meninggalkan bagian `## Bukti` dan `## Yang belum beres`
untuk diisi manusia atau agen yang mengerjakannya. Nota yang sudah ada tidak
pernah ditimpa.

## Templat

`50-Templat/` berisi [[Templat Sesi]], [[Templat Bug]], [[Templat Sistem]].
Plugin **Templates** sudah aktif dan menunjuk ke folder itu.

## Struktur folder

| Folder | Isi |
|---|---|
| `00-Peta/` | pintu masuk: status, progres, peta kode, utang |
| `10-Tahapan/` | satu nota per tahap dari `docs/TAHAPAN.md` |
| `20-Sesi/` | jurnal kronologis, satu per commit |
| `30-Sistem/` | sistem permainan yang berumur panjang |
| `40-Bug/` | bug yang pernah nyata + pemeriksaan yang menjaganya |
| `50-Templat/` | templat nota baru |
