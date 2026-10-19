---
judul: "Majelis Batin hilang di merge 5683e79"
tipe: bug
status: selesai
ditemukan: "2026-10-18"
commit_perbaikan: (cabang bangun-B, "Pulihkan Majelis Batin yang hilang di merge 5683e79" + "Tata letak Majelis Batin")
dijaga_oleh: tools/probe_batin.py (baris 'majelis batin' di tools/regress.py)
tags: [bug, status/selesai, merge, batin, ui]
---

# 🐞 Majelis Batin hilang di merge 5683e79

Majelis Batin (empat suara batin gaya Disco Elysium: BARA/AKAR/SUKMA/LAPAR)
hilang sebagian saat `feature/3d-mobs` digabung. `game/batin.py` tetap ada,
enam pemanggil `say_batin_once` tetap ada, `_build_batin` tetap membangun
panel -- tapi tidak ada yang pernah menyalakannya. Tidak ada alat yang
menyadarinya, karena tidak ada yang memainkannya.

## Sebab (diukur pada objek git)

Merge 5683e79 mengambil `game/app.py` utuh dan blok HUD `panels.py` dari sisi
visual (`5683e79^1`), yang tidak pernah punya Batin. Hitungan
`def toggle_batin` / `def _build_batin` / `def open_pause` / `Batin(self.state)`:

| snapshot | hitungan |
|---|---|
| `5683e79^1` | 0/0/0/0 |
| `5683e79^2` (= cd92b0d) | 1/1/1/1 |
| `5683e79` | 0/1/0/0 |

Hanya pembangun yang terbawa. Ikut hilang tanpa konflik: empat suara di
`interaction_controller.py` (vonis "campur"; blok Siram dan Panen dari sisi
visual): `siram`, `panen`, `kirim_hint`, SUKMA mutu≥4. Arsip `_bench/port/`
yang dijanjikan `docs/INTEGRASI.md` tidak pernah ter-commit (`_bench/.gitignore`
berpola `*` saat merge) dan memang tidak memuat `panels.py`.

## Gejala (probe_batin sebelum pemulihan, 3132c89: 0/21 lulus)

- `game.batin = None`, `panels.batin = None`.
- Cangkul pertama tidak membuka PAGI PERTAMA; suara AKAR **menimpa flash**
  "Tanah dicangkul!" (`say_batin` versi flash 3 dtk). Di keenam titik panggil
  ia menimpa flash yang membawa informasi, mis. "Dapat X dari Y! Kirim ke Peti".
- Tidak ada tombol panel majelis (TAB sudah milik ringkasan motif).

## Kenapa salin-tempel verbatim tidak cukup (semua terukur)

1. `_pulihkan_mode_yatim` tidak mengenal `'batin'` → modal mati 1 frame
   setelah terbuka, dan [2] mengganti alat alih-alih memilih.
2. Jaring ESC global memanggil `close_all()` sebelum rute mode mana pun;
   `close_all` tidak membersihkan `_bc_ents` → 7 entity modal tertinggal.
3. Pemudar `_voice_sub_t` di dalam gerbang HUD → subtitle tidak padam selama
   modal terbuka.
4. Tata letak lama untuk HUD lama: panel kiri menimpa pelacak tutorial,
   prompt modal di bawah flash, subtitle dan "Tekan 1-N" sama-sama di
   y -0,30, subtitle jatuh di kotak dialog. `panel_chrome.png` hanya opak di
   49% tengah tiap sumbu (bbox alfa 130-382 dari 512).
5. `Batin._said` hanya di memori → PAGI PERTAMA muncul lagi tiap sesi.
6. F7 (tombol pilihan) ditangkap HotReloader Ursina selama development_mode
   menyala -- lihat [[F5 dan F9 dibajak HotReloader Ursina]].

## Perbaikan

- `app.py`: `Batin(self.state)` dibuat setelah UIManager; rute `'batin'`
  SETELAH jaring ESC; `_pulihkan_mode_yatim` mengenal `'batin'`; panel di **F7**.
- `panels.py`: toggle_batin, _refresh_batin, open_batin_check,
  batin_check_input, _pick_batin, _close_batin_check dari `5683e79^2`;
  `say_batin` kembali ke subtitle; pemudar di luar gerbang HUD; `close_all`
  membersihkan modal; tata letak baru + chrome dipangkas ke bbox alfanya.
- `GameState.batin_sekali: list` -- bendera sekali-ucap ikut save. Save lama
  tanpa field itu tetap dimuat (C3). `Batin.lines` sengaja tidak disimpan:
  log panel kosong lagi di sesi baru.
- Suara `siram`, `panen`, `kirim_hint` kembali. Baris SUKMA mutu≥4 **dibuang**:
  panen di HEAD tidak membaca mutu.
- Cabang skill-check/red `_pick_batin` (roll, pct, DIFF_NAME, batin_red) **tidak
  diport**: tak punya pemanggil produksi di HEAD maupun di cd92b0d (aturan #4).
- `tools/probe_lima_menit.py` menjawab modal dengan tombol yang tertulis di
  modal. Tanpa itu 5/8 (cangkul 0→1, tanam 0→0, panen 0→0); dengan itu 8/8.

## Bukti

`tools/probe_batin.py`, tiga subproses lewat `g.app.input`, HUD dicapai
dengan SPACE sampai `not g.sinema.aktif`: 0/21 (3132c89, sebelum pemulihan) → 22/22
(26/26 setelah cek tutup-sendiri dan fase D F9 ditambahkan, lihat di bawah).
Uji mutasi (bug dipasang kembali satu per satu; semuanya membuat probe merah):

| mutasi | probe_batin |
|---|---|
| `'batin'` dibuang dari `_pulihkan_mode_yatim` | 11/22 |
| pembersihan `_bc_ents` di `close_all` dibuang | 20/22 |
| pembuatan `Batin` di app.py dibuang | 1/22 |
| TAB kembali ke `toggle_batin` | 21/22 (cek motif) |
| `say_batin` kembali ke flash | 16/22 |
| pemudar `_voice_sub_t` dibuang | 21/22 (padam) |
| pemudar dikembalikan ke dalam gerbang HUD | 21/22 (padam) |
| `Batin.once` kembali ke list di memori | 20/22 (C1, C2) |
| `development_mode=True` (F7 milik HotReloader) | 19/22 |
| subtitle kembali ke y -0,30 | 20/22 (tata letak) |
| chrome tidak dipangkas | 20/22 (alfa latar 0,00) |
| rute input `'batin'` dibuang | 10/22 |
| panel majelis kembali ke kiri | 21/22 (menimpa pelacak tutorial) |

### Celah yang ditemukan verifikator (perbaikan-B)

Dua mutasi lolos dari probe 22/22 di atas. Keduanya kini punya cek
(probe_batin 26/26 di HEAD):

| mutasi | sebelum cek baru | sesudah |
|---|---|---|
| tutup-sendiri panel majelis di `UIManager.update()` dimatikan | 22/22 (lolos) | 25/26: `[I]` dengan panel terbuka → mode=panel open=True, 9 entity majelis tetap tergambar di atas inventaris |
| `Batin` menyimpan rujukan list `batin_sekali` pertama (basi setelah F9) | 22/22 (lolos) | 24/26: fase D, modal PAGI PERTAMA tidak terbuka lagi setelah F9 memuat save yang belum menjawabnya; F5 menyimpan `[]` |

Fase D baru: F5 tanpa bendera → jawab modal → F9 → cangkul lagi → modal
harus terbuka → jawab → F5 harus menyimpan `pagi_pertama`. Semua lewat
`g.app.input`.

## Yang belum beres

- ESC pada modal melewatkan pilihan untuk selamanya (bendera dikonsumsi
  sebelum modal dibuka) -- perilaku asli cd92b0d, dibiarkan.
- Stat batin hanya masuk ke `soil['quality']`; panen dan harga jual mengabaikan
  mutu, jadi pilihan PAGI PERTAMA praktis tanpa efek permainan.
- Menu Jeda hilang dengan pola yang sama dan **belum** dipulihkan.

## Pelajaran

Merge yang memilih "sisi kita" per berkas membuang pemakai yang tinggal di sisi
lain, dan pembangun yang tertinggal membuatnya tampak utuh. Cek
`grep "panels\.X("` vs `def X` menemukan pemanggil tanpa definisi, tapi tidak
menemukan *fitur tanpa pemanggil* -- itu hanya terlihat dengan memainkannya.
