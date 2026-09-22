---
judul: Tahap 2 — sambungkan modul yatim (alat di tangan, akibat merawat ternak)
tipe: sesi
tanggal: 2026-08-26
commit: 2a0a26f
skala: player.py +43, time_controller.py +12
tags: [sesi, audit, gameplay]
---

# 2026-08-26 — Dua modul yatim disambungkan

Commit `2a0a26f`. Audit modul yang mendarat saat agennya mati kena limit sesi.

## Hasil audit

| Modul | Baris | Vonis |
|---|---:|---|
| `economy.py` | 388 | nyata, tersambung |
| `crops.py` | 633 | nyata, tersambung |
| `animal_models.py` | 337 | nyata, tersambung |
| `husbandry.py` | 434 | **yatim** — nol pemanggil |
| `tool_models.py` | 335 | **yatim** — nol pemanggil |
| `entity_style.py` | 598 | kerangka, 11 TODO |

Dua modul lengkap tanpa satu pun pemanggil: kodenya ada, **efeknya di game
nol**. Agennya mati tepat sebelum menyambungkan.

## Yang disambungkan

**`Player3D.refresh_held_tool()`** memasang model alat ke bahu kanan dan
menggantinya saat pemain ganti alat. Sebelumnya HUD cuma menulis kata "Cangkul"
sementara tangan karakter kosong.

`build_tool()` sengaja **tanpa cache**: Mesh Ursina adalah NodePath Panda3D
yang hanya boleh punya satu parent, dan berbagi mesh sudah dua kali membuat
entity kehilangan geometri di proyek ini → [[Mesh NodePath dipakai bersama]].

**`TimeController.advance_day()`** memanggil `husbandry.daily_tick()` →
[[Ternak]]. Diuji lima hari: hari 1 dua ternak siap dipanen, lalu lapar, hari 4
semua jatuh sakit karena dilalaikan. Sebelum ini merawat hewan tidak berakibat
apa pun.

## Bukti

Regresi **5/5 lulus**.

## Yang belum beres

[[Tahap 2 — Verifikasi modul yatim]] ternyata belum bisa ditutup: commit
berikutnya melahirkan yatim baru, `entity_mesh.py` → [[Utang Teknis]].

## Tautan

Berikutnya: [[2026-08-27 — Tata letak, avatar native, tukang mesh]]
