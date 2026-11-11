@echo off
title MAY CHU GMBOT AI CUC BO (PORT 8000)
cd /d "C:\Robot AI\Gmbot_server"
echo ===================================================================
echo             MAY CHU GMBOT AI CUC BO DANG HOAT DONG
echo ===================================================================
echo   - Web Dashboard:     http://localhost:8000
echo   - Local Network API: http://127.0.0.1:8000
echo ===================================================================
C:\Espressif\tools\python\v6.1\venv\Scripts\python.exe server.py
pause
