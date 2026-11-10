@echo off
chcp 65001 >nul
title KHOI CHAY GMBOT AI & CLOUDFLARE TUNNEL (ONLINE)

cd /d "%~dp0"

echo ======================================================================
echo    🤖 GMBOT AI CONTROL PLANE + CLOUDFLARE TUNNEL (PUBLIC ONLINE)
echo ======================================================================
echo.

:: 1. Chạy Server ở cửa sổ riêng
start "GMbot AI Server" cmd /k "python server.py"

:: 2. Đợi 2 giây cho Server sẵn sàng
timeout /t 2 /nobreak >nul

:: 3. Chạy Cloudflare Tunnel
echo Đang mở Cloudflare Tunnel đưa hệ thống ra Internet...
start "Cloudflare Tunnel (Public URL)" cmd /k "run_tunnel.bat"

echo.
echo [XONG] Cả Server và Cloudflare Tunnel đang chạy trong các cửa sổ riêng biệt!
pause
