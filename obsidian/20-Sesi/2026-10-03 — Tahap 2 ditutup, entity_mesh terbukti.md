---
judul: Tahap 2 ditutup — entity_mesh terbukti jalan dan ditandai
tipe: sesi
tanggal: 2026-10-03
commit: e1340fd
tags: [sesi, audit, bukti]
---

# 2026-10-03 — Tahap 2 ditutup

Satu yatim terakhir menahan [[Tahap 2 — Verifikasi modul yatim]], dan ia tidak
ditutup dengan menyambungkannya.

## `entity_mesh.py`: dibuktikan, bukan disambungkan

Aturan Tahap 2 memberi dua jalan keluar — *"terbukti jalan **atau** ditandai
rusak dengan jujur"* — dan yang dipakai jalan kedua, dengan alasan yang bisa
dibaca dari modulnya sendiri: ia **pustaka geometri generik**, bukan fitur.
Docstringnya menyatakan *"Tidak tahu apa-apa soal entitas; kalau dipakai untuk
menggambar bendera, dia akan menggambar bendera."*

Konsumennya bahasa rupa entitas = [[Tahap 7 — Misteri dan entitas]], yang
**sengaja** ditaruh belakangan (horor butuh kehidupan biasa di sekelilingnya).
Menyambungkannya sekarang berarti melompati urutan yang justru jadi inti
`docs/TAHAPAN.md`.

Jadi yang dikerjakan: menghapus ketidakjelasannya.
`_bench/probes/probe_entity_mesh.py` — 16 pemeriksaan, semua lulus:

```
quad/cubic bezier          17 titik (16 segmen + 1), ujung tepat di kontrol
catmull_rom                25 titik dari 4 kontrol
resample jarak seragam     selisih 8,3e-16
polyline_rails lebar       0,5000 .. 0,5000
total_turning_deg          kotak 270 derajat, garis lurus 0
PolyBuilder                184 segitiga, 404 verteks, 404 warna per-verteks
dua Entity, dua Mesh       GeomNode 1 dan 1   <- bukan 0
style_entity               unlit=True
```

Dua yang terakhir penting: GeomNode ≥ 1 membuktikan
[[Mesh NodePath dipakai bersama]] tidak kambuh di jalur ini, dan `unlit=True`
membuktikan warna per-verteks tidak dimatikan shader.

Statusnya lalu ditulis di **kepala modulnya**, bukan hanya di vault — pembaca
kode melihatnya tanpa perlu tahu vault ini ada.

## Probe saya sendiri gagal tiga kali — dan ketiganya salah probe

Versi pertama probe ini melaporkan tiga GAGAL. Ketiganya ekspektasi saya yang
salah, bukan cacat modul:

| Yang saya tebak | Yang sebenarnya |
|---|---|
| `quad_bezier(…, 16)` → 16 titik | → **17**; `n` adalah jumlah segmen, ujung inklusif |
| `total_turning_deg` kotak → 360° | → **270°**; ia tidak menganggap polyline tertutup |
| `PolyBuilder.poly()` ada | tidak ada — API-nya `add_tri/add_quad/add_band/add_disc/add_ring/add_ribbon`, lalu `.mesh()` |

Ini kali **keempat** proyek ini tertipu alat ukurnya sendiri
([[Pemeriksaan motif mengotori keadaan]] punya daftarnya). Bedanya kali ini
ketahuan dalam satu menit karena probe-nya ada. Aturannya: baca sumbernya dulu.

## Dua utang yang ternyata sudah lunas

Diperiksa terhadap repo, bukan terhadap catatan sebelumnya:

- **92 `.pyc`** → `git ls-files | grep -c '\.pyc$'` = **0**. Base branch sudah melepasnya. Vault mencatatnya sebagai utang terbuka beberapa jam setelah ia lunas.
- **Workflow CI** → sudah terbukti hijau, dicatat di [[2026-09-22 — Merge base, CI terbukti hijau]].

## Bukti

- `probe_entity_mesh.py` → 16/16 lulus, keluar kode 0.
- `git ls-files | grep -c '.pyc$'` → 0.
- `py_compile game/entity_mesh.py` → bersih.

## Yang belum beres

- [[Arah WASD basis sumbu salah]] — satu-satunya 🔴 yang bisa dikerjakan tanpa GPU, dan probe arahnya **hilang** bersama 14 probe lain → [[2026-10-03 — Probe pertama yang bisa diperiksa]]. Ini pekerjaan berikutnya.
- [[Tahap 3 — Performa]] butuh mesin ber-GPU; tidak bisa dari sini.

## Tautan

[[Tahap 2 — Verifikasi modul yatim]] · [[Status Sekarang]] · [[Utang Teknis]]
