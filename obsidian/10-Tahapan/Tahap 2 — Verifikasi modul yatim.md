---
judul: Tahap 2 — Verifikasi modul yatim
tipe: tahap
nomor: 2
status: selesai
ringkas: Tidak ada fitur baru sampai yang sudah ada terbukti jalan
commit: 2a0a26f
tags: [tahap, status/jalan]
---

# Tahap 2 — Verifikasi yang sudah terlanjur ada ✅

Beberapa modul mendarat di disk saat agennya mati kena limit sesi. **Belum ada
yang membuktikan isinya berfungsi.** Aturannya: tidak ada fitur baru sampai
yang ada terbukti jalan atau ditandai rusak dengan jujur. Sistem setengah jadi
yang diklaim selesai lebih berbahaya daripada sistem yang belum dibuat.

## Audit commit `2a0a26f`

| Modul | Baris | Vonis waktu itu |
|---|---:|---|
| `economy.py` | 388 | nyata, tersambung |
| `crops.py` | 633 | nyata, tersambung |
| `animal_models.py` | 337 | nyata, tersambung |
| `husbandry.py` | 434 | **yatim** — nol pemanggil |
| `tool_models.py` | 335 | **yatim** — nol pemanggil |
| `entity_style.py` | 598 | kerangka, 11 TODO |

Dua yatim itu disambungkan di commit yang sama:
`Player3D.refresh_held_tool()` memasang model alat ke bahu kanan
([[Objek dan Interaksi]]), dan `TimeController.advance_day()` memanggil
`husbandry.daily_tick()` ([[Ternak]]).

## Yatim terakhir: `entity_mesh.py` — ditutup 2026-10-03

Diperiksa ulang 2026-09-22 dan muncul yatim **baru**: `entity_mesh.py`, 458
baris, nol pemanggil, mendarat di
[[2026-08-27 — Tata letak, avatar native, tukang mesh]].

Aturan tahap ini memberi **dua** jalan keluar, dan yang kedua dipakai:

> *terbukti jalan **atau** ditandai rusak dengan jujur.*

Ia tidak disambungkan, dan itu keputusan sadar: docstringnya sendiri menyatakan
modul ini pustaka geometri generik (*"kalau dipakai untuk menggambar bendera,
dia akan menggambar bendera"*). Konsumennya bahasa rupa entitas, yaitu
[[Tahap 7 — Misteri dan entitas]] — yang sengaja ditaruh belakangan.
Menyambungkannya sekarang berarti melompati urutan yang justru jadi inti
`docs/TAHAPAN.md`.

Yang dilakukan: **membuktikan isinya berfungsi**, supaya statusnya bukan "tidak
jelas". `_bench/probes/probe_entity_mesh.py`, 16 pemeriksaan, semua lulus:

```
184 segitiga, 404 verteks, 404 warna per-verteks
dua Entity dari dua Mesh  ->  GeomNode 1 dan 1   (bukan 0)
style_entity unlit=True
resample: selisih jarak 8,3e-16
```

Lalu status itu ditulis di kepala modulnya sendiri, bukan cuma di vault —
pembaca kode melihatnya tanpa perlu tahu vault ini ada.

Catatan kecil yang layak diingat: **probe versi pertama saya GAGAL tiga kali,
dan ketiganya salah probe, bukan salah modul** — saya menebak API-nya
(`quad_bezier` mengembalikan n+1 titik, bukan n; `total_turning_deg` tidak
menganggap polyline tertutup; `PolyBuilder` tidak punya `.poly()`). Pelajaran
yang sama untuk ketiga kalinya di proyek ini: baca sumbernya dulu, jangan
menebak alat ukurnya → [[Pemeriksaan motif mengotori keadaan]].

## Tahap ini sekarang bersih

Tidak ada lagi modul berstatus tidak jelas: yang yatim sudah tersambung
(`husbandry`, `tool_models`, dan `choose_action` lewat [[Tahap 5 — Autonomi]])
atau terbukti-dan-ditandai (`entity_mesh`).

## Tautan

Sesi: [[2026-08-26 — Tahap 2 sambungkan modul yatim]] ·
Lanjut ke [[Tahap 3 — Performa]]
