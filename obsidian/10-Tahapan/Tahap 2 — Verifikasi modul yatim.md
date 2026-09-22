---
judul: Tahap 2 — Verifikasi modul yatim
tipe: tahap
nomor: 2
status: jalan
ringkas: Tidak ada fitur baru sampai yang sudah ada terbukti jalan
commit: 2a0a26f
tags: [tahap, status/jalan]
---

# Tahap 2 — Verifikasi yang sudah terlanjur ada 🔨

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

## Kenapa tahap ini belum ditutup

Diperiksa ulang 2026-09-22: muncul yatim **baru**.

```
entity_mesh.py   458 baris   nol pemanggil
```

Pola yang sama persis — modul lengkap mendarat di [[2026-08-27 — Tata letak, avatar native, tukang mesh]],
tepat sebelum disambungkan. Rinciannya di [[Utang Teknis]].

Tahap 2 selesai kalau `entity_mesh.py` tersambung atau ditandai eksplisit
belum dipakai, dan tidak ada modul lain yang berstatus tidak jelas.

## Tautan

Sesi: [[2026-08-26 — Tahap 2 sambungkan modul yatim]] ·
Lanjut ke [[Tahap 3 — Performa]]
