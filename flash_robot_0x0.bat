@echo off
chcp 65001 >nul
echo ========================================================
echo       TOOL NẠP FIRMWARE ROBOT MINI ESP32-S3 (MẠCH TÍM)
echo   Server: https://gehihiv2.onrender.com (Tiếng Việt)
echo   Web Admin cấu hình GPIO: http://192.168.4.1:8080
echo ========================================================
echo.

set /p COMPORT="Nhập cổng COM của Robot (ví dụ: COM3, COM5, COM8): "
if "%COMPORT%"=="" (
    echo [LỖI] Không được để trống cổng COM!
    pause
    exit /b
)

echo.
echo Đang chuẩn bị nạp file: firmware_robot_0x0.bin vào %COMPORT% tại cổng 0x0...
echo Tốc độ nạp: 460800 baud
echo.

REM Tìm Python và esptool
set ESPTOOL_CMD=python -m esptool
%ESPTOOL_CMD% version >nul 2>&1
if %errorlevel% neq 0 (
    if exist "C:\Users\%USERNAME%\.espressif\python_env\idf6.1_py3.14_env\Scripts\python.exe" (
        set ESPTOOL_CMD="C:\Users\%USERNAME%\.espressif\python_env\idf6.1_py3.14_env\Scripts\python.exe" -m esptool
    ) else (
        if exist "C:\Users\Welcome\.espressif\python_env\idf6.1_py3.14_env\Scripts\python.exe" (
            set ESPTOOL_CMD="C:\Users\Welcome\.espressif\python_env\idf6.1_py3.14_env\Scripts\python.exe" -m esptool
        )
    )
)

echo Thực hiện nạp firmware toàn bộ tại địa chỉ 0x0...
%ESPTOOL_CMD% --chip esp32s3 -p %COMPORT% -b 460800 --before default-reset --after hard-reset write-flash --flash-mode dio --flash-size 16MB --flash-freq 80m 0x0 firmware_robot_0x0.bin

if %errorlevel% equ 0 (
    echo.
    echo ========================================================
    echo [THÀNH CÔNG] Đã nạp xong firmware cho Robot trên %COMPORT%!
    echo Robot đang khởi động lại...
    echo.
    echo CÁCH TRUY CẬP WEB ADMIN QUẢN TRỊ & ĐỔI CHÂN GPIO:
    echo 1. Kết nối vào sóng Wi-Fi do robot phát ra (Xiaozhi-xxxx / Megabot-xxxx)
    echo 2. Mở trình duyệt web truy cập:
    echo      http://192.168.4.1:8080
    echo    (Khi robot đã vào mạng nhà, có thể vào bằng: http://^<IP-CỦA-ROBOT^>:8080)
    echo.
    echo Mẹo an toàn: Giữ nút BOOT 3 giây khi vừa bật nguồn để xoá cấu hình chân, trở về mặc định!
    echo ========================================================
) else (
    echo.
    echo ========================================================
    echo [LỖI] Không thể nạp vào %COMPORT%. Vui lòng kiểm tra:
    echo 1. Đã cắm cáp USB kết nối ESP32-S3 với máy tính chưa?
    echo 2. Đã kiểm tra đúng cổng COM trong Device Manager chưa?
    echo 3. Giữ nút BOOT trên mạch rồi cắm cáp USB để vào chế độ nạp (Download Mode).
    echo ========================================================
)

echo.
pause
