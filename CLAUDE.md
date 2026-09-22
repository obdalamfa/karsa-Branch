# Lembah Karsa 3D — catatan untuk agen

## Catat progres di vault Obsidian

Semua progres dicatat di vault `obsidian/`. Setelah menyelesaikan kerja yang
layak di-commit:

```bash
python tools/catat_obsidian.py            # kerangka nota sesi untuk HEAD
python tools/catat_obsidian.py --status   # commit mana yang belum tercatat
```

Lalu isi bagian `## Bukti` dan `## Yang belum beres` — skrip sengaja tidak
menebaknya. Perbarui juga `obsidian/00-Peta/Status Sekarang.md` kalau status
proyek berubah, dan tambahkan nota di `40-Bug/` untuk tiap bug yang **pernah
nyata**.

Aturan lengkap: `obsidian/00-Peta/Aturan Pencatatan.md`.

## Aturan yang lahir dari kegagalan nyata di repo ini

1. **Klaim tanpa bukti tidak ditulis sebagai fakta.** Verifikasi manual sudah
   gagal dua kali di sini. "Selesai" butuh larian `tools/regress.py`, probe di
   `_bench/`, atau angka. Kalau belum terbukti, tulis "belum terverifikasi"
   apa adanya.
2. **Probe harus menempuh jalur asli.** Tiga probe gagal menemukan bug pembeku
   pemain karena memanggil `player.tick()` langsung, melewati gerbang mode di
   `app.py`. Alat ukur yang salah mengukur dunia yang tidak ada.
3. **Jangan berbagi Mesh Ursina antar-Entity.** Mesh adalah NodePath Panda3D
   dan hanya boleh punya satu parent; berbagi mesh sudah dua kali membuat
   entity kehilangan geometri.
4. **Modul tanpa pemanggil = efeknya nol.** Sudah terjadi tiga kali: modul
   lengkap mendarat di disk saat agennya kehabisan sesi, tepat sebelum
   disambungkan. Periksa dengan `grep -rn "nama_modul" --include=*.py .`.
5. **Jangan ubah tanda arah WASD** sebelum ada probe arah yang kokoh — lihat
   `obsidian/40-Bug/Arah WASD belum terverifikasi.md`.

## Uji sebelum commit

```bash
python tools/regress.py          # semua scene; keluar 1 kalau ada yang gagal
python tools/regress.py farm     # satu scene
```

Butuh `ursina` + `panda3d` (`pip install -r requirements.txt`).
