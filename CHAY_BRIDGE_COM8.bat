@echo off
chcp 65001 >nul
title CẦU NỐI SERIAL COM8 -> RENDER CLOUD (gehihiv2.onrender.com)
cd /d "%~dp0"
echo ===================================================================
echo       🌐 CẦU NỐI SERIAL USB COM8 -> RENDER CLOUD GMBOT AI
echo ===================================================================
echo   - Cổng Robot:    COM8 (ESP32-S3 Mạch Tím)
echo   - Server Cloud:  https://gehihiv2.onrender.com
echo   - Tác vụ:        Truyền nhật ký console, nhận lệnh D-Pad, OLED, Loa
echo ===================================================================
echo.
python scripts\bridge_com8.py --port COM8 --server https://gehihiv2.onrender.com
if %errorlevel% neq 0 (
    echo.
    echo [LỖI] Không thể chạy python. Vui lòng kiểm tra Python trên máy tính.
)
pause
