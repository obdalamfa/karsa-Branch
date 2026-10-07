# build_release.ps1 — Bangun distribusi Lembah Karsa 3D (ROADMAP M7).
# Pakai: pwsh ./build_release.ps1   (jalankan dari root repo)
$ErrorActionPreference = 'Stop'

Write-Host '== Lembah Karsa 3D — Build Rilis ==' -ForegroundColor Cyan

# 1. Pastikan PyInstaller terpasang
$hasPI = python -c "import PyInstaller" 2>$null; if ($LASTEXITCODE -ne 0) {
    Write-Host 'Memasang PyInstaller...' -ForegroundColor Yellow
    python -m pip install pyinstaller
}

# 2. Smoke test dulu — jangan bundel build yang rusak
Write-Host 'Menjalankan smoke test...' -ForegroundColor Yellow
python tools/smoke_boot.py
if ($LASTEXITCODE -ne 0) { throw 'Smoke test GAGAL — build dibatalkan.' }

# 3. Bersihkan build lama & bundel
if (Test-Path build) { Remove-Item -Recurse -Force build }
if (Test-Path dist)  { Remove-Item -Recurse -Force dist }
Write-Host 'Membundel dengan PyInstaller (onedir)...' -ForegroundColor Yellow
pyinstaller lembah_karsa.spec --noconfirm
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller GAGAL.' }

# 4. Sertakan README pemain di folder dist
Copy-Item README_PEMAIN.md dist/LembahKarsa3D/ -Force

Write-Host ''
Write-Host 'SELESAI. Distribusi: dist/LembahKarsa3D/' -ForegroundColor Green
Write-Host 'Uji: jalankan dist/LembahKarsa3D/LembahKarsa3D.exe lalu zip folder itu untuk dikirim.' -ForegroundColor Green
