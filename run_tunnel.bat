@echo off
chcp 65001 >nul
title Cloudflare Tunnel - GMbot AI Online
echo ======================================================
echo    🌐 CLOUDFLARE TUNNEL - ĐƯA GMBOT AI RA INTERNET
echo ======================================================
echo.
echo Đang kết nối port 8000 ra Internet toàn cầu...
echo Sau khi khởi động, hãy sao chép đường link:
echo https://xxxx.trycloudflare.com
echo.
if exist ".\cloudflared.exe" (
    .\cloudflared.exe tunnel --url http://localhost:8000
) else (
    "C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel --url http://localhost:8000
)
pause
