@echo off
chcp 65001 >nul
title MAY CHU GMBOT AI CUC BO - CONTROL PLANE & MCP SERVER (PORT 8000)
cd /d "%~dp0"
echo ===================================================================
echo             MAY CHU GMBOT AI CUC BO DANG HOAT DONG
echo ===================================================================
echo   - Web Dashboard:     http://localhost:8000
echo   - Local Network API: http://127.0.0.1:8000
echo ===================================================================
start "" http://localhost:8000
python server.py
pause
