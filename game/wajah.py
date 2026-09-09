"""wajah.py — Wajah dan rambut, satu bahasa rupa untuk pemain dan NPC.

Sebelum modul ini, kepala pemain adalah kotak kulit polos dan NPC adalah
manekin `humanoid.obj` PUTIH MURNI (Color 1,1,1,1) setinggi 3,42 unit —
1,45 kali pemain — tanpa wajah, tanpa rambut, tanpa baju. Diukur, bukan
dikira: lihat catatan di docs.

Bahasa rupa yang diikuti datang dari game kehidupan Jepang (Story of Seasons,
Rune Factory, Harvest Moon), dan urutannya penting karena tiap langkah
menyelesaikan masalah yang berbeda:

  1. RAMBUT DULU. Poni yang menjorok di atas dahi adalah satu hal yang paling
     cepat mengubah kepala polos jadi karakter, dan ia sekaligus memberi
     kepala ARAH DEPAN yang terbaca dari jauh. Tanpa rambut, kepala dari depan
     dan dari belakang sama saja.
  2. MATA adalah fiturnya, bukan salah satu fitur. Besar, gelap, bentuk
     sederhana, duduk sedikit DI BAWAH garis tengah wajah — mata yang
     diletakkan tepat di tengah membuat wajah terbaca dewasa dan dingin.
     Besarnya sekitar sepertiga tinggi wajah yang terlihat: percobaan pertama
     memakai hampir setengahnya dan hasilnya terbaca sebagai kacamata hitam.
  3. KILAU. Mata anime tidak pernah hitam rata. Satu titik putih kecil di
     sudut yang SAMA pada kedua mata (cahaya datang dari satu arah) adalah
     beda antara "melihat" dan "melotot". Kilau simetris cermin terbaca
     sebagai dua bola mata, bukan wajah.
  4. MULUT sekecil mungkin, dan warnanya diredam. Pada kotak sekecil ini,
     merah menyala terbaca sebagai luka.
  5. Rona pipi. Murah, dan ia yang membuat kulit terbaca hidup.

Semua ukuran diberikan sebagai PECAHAN dari setengah-lebar kepala, jadi satu
resep yang sama pas di kepala pemain (setengah-lebar 0,175) maupun di kepala
manekin NPC (0,36) tanpa dua tabel angka yang harus dijaga sinkron.
"""
from ursina import Entity, Vec3, color


MATA_WARNA  = (46, 36, 42)
# Mulut sengaja diredam: merah menyala pada bidang sekecil ini terbaca sebagai
# luka, bukan mulut.
MULUT_WARNA = (168, 108, 100)
PIPI_WARNA  = (243, 176, 172)


def _kotak(induk, pos, skala, warna):
    e = Entity(model='cube', position=Vec3(*pos), scale=skala,
               color=warna, parent=induk)
    from .smooth_shader import apply_smooth
    apply_smooth(e, has_texture=False)
    return e


def bangun_rambut(induk, hw: float, ht: float, warna, maju: float = 0.0):
    """Batok, poni, tuft sisi dan belakang kepala. Return daftar entity.

    `hw` setengah-lebar kepala, `ht` setengah-tinggi kepala, keduanya dalam
    satuan induk. `maju` menggeser seluruh rambut ke depan (dipakai saat
    kepala di bawahnya bukan kotak, melainkan bola yang lebih ramping).
    """
    out = []
    def r(pos, skala):
        out.append(_kotak(induk, pos, skala, warna))
    # Poni sengaja menonjol lebih maju daripada bidang muka supaya ia
    # MENGGANTUNG di atas dahi, bukan menempel rata seperti stiker.
    out_hw = hw * 1.06
    r((0.0,  ht * 0.67, -hw * 0.07 + maju), (out_hw * 2, ht * 0.85, out_hw * 2))
    r((0.0,  ht * 0.35,  hw * 0.86 + maju), (out_hw * 2, ht * 0.56, hw * 0.55))
    r((-hw * 1.03, ht * 0.04, -hw * 0.06 + maju), (hw * 0.28, ht * 1.33, hw * 1.97))
    r(( hw * 1.03, ht * 0.04, -hw * 0.06 + maju), (hw * 0.28, ht * 1.33, hw * 1.97))
    r((0.0, -ht * 0.09, -hw * 1.05 + maju), (hw * 1.94, ht * 1.47, hw * 0.29))
    return out


def bangun_wajah(induk, hw: float, ht: float, muka_z: float):
    """Mata, kilau, mulut dan rona pipi pada bidang muka.

    `muka_z` adalah jarak bidang muka dari pusat kepala, dalam satuan induk.
    Semua fitur ditempel sedikit di depannya supaya tidak berkedip melawan
    permukaan kepala (z-fighting).
    """
    out = []
    z = muka_z
    for sx in (-1, 1):
        out.append(_kotak(induk, (sx * hw * 0.41, -ht * 0.26, z),
                          (hw * 0.34, ht * 0.28, hw * 0.08),
                          color.rgb(*MATA_WARNA)))
        # Kilau di sudut yang SAMA pada kedua mata: satu arah cahaya.
        out.append(_kotak(induk, (sx * hw * 0.41 - hw * 0.09, -ht * 0.19, z + hw * 0.046),
                          (hw * 0.10, ht * 0.08, hw * 0.046),
                          color.rgb(255, 255, 255)))
    out.append(_kotak(induk, (0.0, -ht * 0.71, z),
                      (hw * 0.22, ht * 0.07, hw * 0.069),
                      color.rgb(*MULUT_WARNA)))
    for sx in (-1, 1):
        out.append(_kotak(induk, (sx * hw * 0.71, -ht * 0.50, z - hw * 0.023),
                          (hw * 0.30, ht * 0.12, hw * 0.046),
                          color.rgb(*PIPI_WARNA)))
    return out


def warna_rambut(state, indeks_default: int = 0):
    from .chargen import HAIR_PRESETS
    i = getattr(state, 'char_hair', indeks_default) or indeks_default
    rgb = HAIR_PRESETS[i][1] if i < len(HAIR_PRESETS) else HAIR_PRESETS[0][1]
    return color.rgb(*rgb)
