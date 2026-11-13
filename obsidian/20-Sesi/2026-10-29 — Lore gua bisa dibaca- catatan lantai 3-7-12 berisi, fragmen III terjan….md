---
judul: "Lore gua bisa dibaca: catatan lantai 3/7/12 berisi, fragmen III terjangkau"
tipe: sesi
tanggal: 2026-10-29
commit: 06d5587
skala: 6 file sumber, +426 / −62 baris
tags: [sesi]
---

# 2026-10-29 — Lore gua bisa dibaca: catatan lantai 3/7/12 berisi, fragmen III terjangkau

## Pesan commit

Tiga cacat lama di lore gua, semuanya tanpa error. Diukur lewat tangga
sungguhan dengan probe baru tools/probe_lore_gua.py:

- Lantai 3/7/12 mencatat 'dungeon_3/7/12' tanpa entri LORE_ITEMS, jadi
  panel Catatan [N] menampilkan "[dungeon_3]" kosong. Kini entri
  LORE_ITEMS; id-nya dipertahankan karena save yang ada sudah menyimpannya.
- Fragmen prasasti III menunggu di lantai 14, padahal gua berhenti di 13.
  Pindah ke 13 (arena Bhutakala, danau legendaris).
- check_dungeon_lore membaca found_at saja; tabel FRAGMEN_GUA dihapus.
- Tangga memanggil check_dungeon_lore tanpa panels, jadi pesannya menunggu
  sampai tidur dan ditimpa lantai berikutnya. app.py kini menyampaikannya
  sesudah scene baru termuat: judul + isi, dibungkus 48 huruf.
- Panel [N] berhalaman (Q/R) tanpa membelah catatan, dibuka di halaman
  terbaru, dan menyingkirkan flash yang menutupinya. Koleksi lengkap kini
  39 baris; dulu dipotong mati di baris 28.

probe_lore_gua 18/18 (pada 630c805: 10/17). Regresi penuh 14/14 scene,
0 pemeriksaan gagal, termasuk baris baru 'lore gua'.

## Berkas yang berubah

| Berkas | + | − |
|---|---:|---:|
| `game/app.py` | +13 | −0 |
| `game/controllers/quest_controller.py` | +35 | −37 |
| `game/data.py` | +24 | −1 |
| `game/panels.py` | +57 | −24 |
| `tools/probe_lore_gua.py` | +264 | −0 |
| `tools/regress.py` | +33 | −0 |

## Bukti

> [!info] Permintaan pemilik: "masukan ke game terbaru yang ada di github".
> Perbaikan ini semula diminta untuk checkout lokal (Cerita Dua Desa), yang
> ternyata 289 commit di belakang branch utama GitHub. Ia dibangun ulang di
> atas kepala PR #15 (630c805), lalu di-push langsung ke branch PR itu atas
> pilihan pemilik.

- Garis dasar dibuat lebih dulu, lewat jalur asli. Harness tanpa jendela
  turun lantai 1→13 dengan berdiri di STAIRS_DOWN (app.update → player.tick
  → `_check_portals`), di 3877418 maupun 630c805: 35/47 di keduanya. Tidak
  ada crash di lantai mana pun (crash `lore_found` sudah hilang). Yang
  terukur:
  - lantai 3/7/12 memberi id tanpa entri LORE_ITEMS, dan panel [N]
    menampilkan `[dungeon_3]` tanpa isi (tangkapan layar);
  - tidak ada flash saat tiba: pesan menunggu tidur dan saling menimpa
    (pesan lantai 3 sudah tergantikan di lantai 5);
  - fragmen III di lantai 14, di luar `DUNGEON_MAX_LEVEL` 13.
- `tools/probe_lore_gua.py` di 630c805: 10/17, tujuh GAGAL yang masing-masing
  satu cacat. Sesudah 06d5587: 18/18.
- Flash catatan kini 3–4 baris dengan lebar 0,32–0,36 layar, diukur dari
  `_flash_ent.width / camera.aspect_ratio`.
- Panel [N] dengan koleksi lengkap: 2 halaman, maks 26 baris, tidak ada
  catatan yang terbelah, dibuka di halaman berisi catatan terbaru.
- Regresi penuh: 14/14 scene, 0 pemeriksaan gagal, baris "lore gua" 18/18
  (9 mnt 26 dtk).

## Yang belum beres

- `gauntlet/check.py` gagal di "cave crystals ... no clipped tint" (puncak
  1,500 > 1,0). Gagal sama persis di 630c805 sebelum perubahan ini, jadi
  bukan regresi dari sini. Belum diselidiki.
- Probe ini menemukan pantulan di lantai 13, diperbaiki di commit
  berikutnya → [[Pemain terpantul dari dasar gua]].
- Nama tiga catatan baru (Prasasti Kutukan, Buku Harian Penambang, Dinding
  Bercahaya) dipilih agen. Teksnya teks lama apa adanya.

## Tautan

[[Status Sekarang]] · [[Peta Progres]] · [[Catatan gua tanpa isi dan fragmen III di lantai 14]] · [[Regresi]]
