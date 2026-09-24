# Gauntlet

Jaring pemeriksaan render dan permainan nyata untuk Lembah Karsa 3D.

## Menjalankan

```
python gauntlet/check.py
```

Sembilan kelompok tes. Skrip memaksa `window-type offscreen` dengan pipeline
OpenGL, memuat aset asli, dan merender lewat mesin Ursina sungguhan — bukan
meniru keluarannya.

## Yang di-track dan yang tidak

**Di-track:**

- `check.py` — pemeriksaannya sendiri
- `baseline.png` — rujukan tetap "Sebelum". Tidak pernah ditulis ulang skrip,
  jadi ia memang milik repo.
- `results.json` — ditulis ulang tiap run, tapi isinya stabil selama sembilan
  tes lulus.
- `progress.html` — halaman progres yang memperbarui diri.

**Tidak di-track** (lihat `.gitignore`): lima screenshot kamera —
`cave-gameplay`, `cave-overview`, `guardians-front`, `mountain-entrance`,
`mountain-overview`.

Alasannya terukur, bukan selera. Rasterisasi GPU tidak deterministik pada
tingkat piksel: membandingkan hasil commit dengan hasil run berikutnya
menunjukkan 1 sampai 87 piksel dari 1.152.000 berbeda (0,000%–0,008%), dengan
selisih kanal 72–108 pada piksel tepi yang terisolasi. Gambarnya sama secara
visual; yang berubah hanya keputusan ambang di tepi poligon.

Menyimpannya berarti setiap kali verifikasi dijalankan, `git status` kembali
penuh "modified" yang menenggelamkan perubahan sungguhan. Itu persis masalah
yang baru saja disingkirkan untuk berkas `.pyc`.

`progress.html` menampilkan kelima gambar itu, jadi **jalankan check dulu di
klon baru** supaya gambarnya muncul.

## Membuktikan tes punya gigi

Tes yang tidak pernah gagal tidak membuktikan apa pun. Dua pemeriksaan sudah
diverifikasi dengan cara menyuntikkan kembali bug aslinya, memastikan gagal,
lalu memulihkan berkasnya:

| Bug disuntikkan | Hasil |
|---|---|
| panggilan ganda `update_guardian()` | `AssertionError: {'naga_bijak': 2, 'banaspati': 2}` |
| tint kristal pra-perbaikan | `AssertionError: puncak 1.253 > 1,0` |

## Yang belum dibuktikan

Dicatat apa adanya di `results.json`, bukan disembunyikan:

- `interactive_playthrough: false` — belum ada yang memainkan game ini dari
  awal sampai akhir secara otomatis. Yang diperiksa adalah konektivitas,
  transisi, save/load, dan perilaku penunggu — bukan satu sesi bermain utuh.
- Penilaian terhadap acuan Rune Factory 4 Special saat ini **bukan
  perbandingan buta**: kritikus mengetahui asal gambar.
