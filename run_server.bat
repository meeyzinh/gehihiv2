@echo off
chcp 65001 >nul
title GMBOT AI SERVER & XIAOZHI CONTROL PLANE (LOCAL)

echo ======================================================================
echo    🤖 ĐANG KHỞI ĐỘNG GMBOT AI CONTROL PLANE & MCP SERVER...
echo    Chạy trực tiếp 100%% trên Máy tính cá nhân (Localhost:8000)
echo ======================================================================
echo.

cd /d "%~dp0"

:: Kiểm tra Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [LỖI] Không tìm thấy Python! Vui lòng cài đặt Python 3.10+ và thêm vào PATH.
    pause
    exit /b
)

:: Kiểm tra các gói thư viện
echo [1/3] Kiểm tra các thư viện cần thiết...
python -c "import fastapi, uvicorn, sqlalchemy, httpx, psutil, jinja2" >nul 2>&1
if %errorlevel% neq 0 (
    echo [THÔNG BÁO] Đang cài đặt thư viện từ requirements.txt...
    pip install -r requirements.txt
)

:: Tự động mở trình duyệt sau 2 giây
echo [2/3] Chuẩn bị mở Web Dashboard trên trình duyệt...
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://localhost:8000"

:: Khởi chạy server
echo [3/3] Khởi chạy máy chủ FastAPI & MCP Server...
echo.
python server.py

pause
