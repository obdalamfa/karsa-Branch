@echo off
title Lembah Karsa 3D - Three.js Web
echo ============================================================
echo   LEMBAH KARSA 3D — Versi Web (Three.js)
echo ============================================================
echo Menjalankan web server lokal dan membuka browser...
start "" "http://localhost:8000/web/index.html"
python -m http.server 8000
