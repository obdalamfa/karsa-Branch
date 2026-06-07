# Rencana Mencari Inspirasi — Repo Open-Source Ursina/Panda3D

Tujuan: belajar dari game open-source yang repository-nya lengkap (sesama Ursina/Panda3D),
lalu adaptasi ke Lembah Karsa 3D. **Belajar pola, bukan menyalin.**

---

## A. REPO REFERENSI (dipetakan ke 4 pilar)

### 🎨 GRAPHIC (visual, rendering, atmosfer)
| Repo | Yang dipelajari |
|------|-----------------|
| `kairess/minecraft-clone` (Ursina) | Render dunia tile/voxel, texture atlas, chunking, hotbar |
| `Raphi-2Code/Voxel-Engine-Ursina` | Voxel engine bekerja + terrain |
| `mandaw2014/Forest` (Ursina) | Lingkungan stylized atmosferik, kabut, mood |
| `hamedsheygh/DoomMaker` (Ursina) | Estetika Doom — **relevan untuk HUD Doom yang kamu mau** |
| `panda3d/Yorg` (Ya2, Panda3D) | Game lengkap & rapi: shader, lighting, post-process |

### 🕹️ GAMEPLAY (mekanik)
| Repo | Yang dipelajari |
|------|-----------------|
| `mandaw2014/sword_combat` (Ursina) | **Combat pedang 3D** — langsung relevan dgn sistem pedang kita |
| `KolenMG/3rd-PersonGame-Ursina` | Kontroler & kamera third-person |
| `mandaw2014/mandaw_openworld` | Open-world traversal + interaksi |
| `mandaw2014/Sandbox` | FPS cepat (mekanik tembak/hit) |

### 📖 STORY (narasi, quest, dialog)
| Repo | Yang dipelajari |
|------|-----------------|
| `Pirates-Online-Rewritten` (Panda3D) | Sistem quest, dialog, NPC schedule (skala MMO Disney) |
| Toontown Online (open source forks) | Quest/economy/NPC AI matang |
| `Lekksii/pito` (STALKER remake, Ursina) | Storytelling lingkungan atmosferik |
| `mandaw2014/Forest` | Narasi eksplorasi minimalis |

### ⚙️ SYSTEM (arsitektur kode, inventory, save, NPC)
| Repo | Yang dipelajari |
|------|-----------------|
| `cpbeto/PyAO` (Argentum Online, Ursina) | **Inventory + NPC + arsitektur RPG** |
| `Pirates-Online-Rewritten` / Toontown | Inventory, quest, save, ekonomi, AI NPC (referensi terlengkap) |
| `panda3d/Yorg` | Struktur proyek Panda3D bersih, build pipeline |
| `wezu/Avolition` | Struktur game aksi solid |

### Daftar kurasi (sumber lengkap)
- `ShivamKR12/awesome-ursina` — semua game Ursina
- `Moguri/awesome-panda3d` — semua resource Panda3D

---

## B. WORKFLOW MINING INSPIRASI (aku bisa clone & baca sendiri)

Aku punya Bash + git → bisa **clone repo & pelajari kodenya langsung**, lalu ekstrak pola.

**Per repo (loop kecil):**
1. `git clone --depth 1 <repo>` ke `tools/refs/<nama>/`
2. Baca `README` + struktur folder (peta sistem)
3. Identifikasi **1 hal kunci** untuk dipelajari (mis. cara sword_combat deteksi hit)
4. Tulis temuan + cara adaptasi ke `INSPIRATION.md` (bukan copy-paste, tapi pola)
5. (opsional) prototipe kecil di Lembah Karsa, verifikasi via workflow capture

**Prioritas (paling relevan dulu):**
1. `mandaw2014/sword_combat` → perbaiki combat kita
2. `kairess/minecraft-clone` → render tile lebih efisien + hotbar (→ inventory)
3. `hamedsheygh/DoomMaker` → referensi HUD Doom
4. `cpbeto/PyAO` → arsitektur inventory/NPC RPG
5. `mandaw2014/Forest` → mood/atmosfer (kabut, palet)
6. `Pirates-Online-Rewritten` → quest/dialog/story (deep-dive sistem)

---

## C. ETIKA & LISENSI
- Hanya **belajar pola & teknik**, tulis ulang sendiri. Jangan salin aset/kode berlisensi.
- Cek LICENSE tiap repo sebelum pakai potongan apa pun.
- Aset (Toontown/Pirates) milik Disney — jangan dipakai, hanya pelajari arsitektur.
