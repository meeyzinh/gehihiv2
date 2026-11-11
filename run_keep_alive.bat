@echo off
title GMbot Render 24/7 Keep-Alive
chcp 65001 >nul
echo ========================================================
echo   GMBOT RENDER 24/7 KEEP-ALIVE SCRIPT
echo   Dang gui ping dinh ky 10 phut/lan toi gehihiv2.onrender.com
echo ========================================================
echo.

python "%~dp0keep_alive.py"

pause
