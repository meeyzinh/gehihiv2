@echo off
chcp 65001 >nul
echo ========================================================
echo       TOOL CẬP NHẬT WI-FI CHO ROBOT ESP32-S3 (MẠCH TÍM)
echo   SSID: A Meey Zinh
echo   Password: 12345678
echo   Phân vùng NVS: 0x9000 (Chỉ mất 2 giây, không mất code)
echo ========================================================
echo.

set /p COMPORT="Nhập cổng COM của Robot (ví dụ: COM3, COM5, COM8): "
if "%COMPORT%"=="" (
    echo [LỖI] Không được để trống cổng COM!
    pause
    exit /b
)

echo.
echo Đang nạp cấu hình WiFi vào %COMPORT% tại địa chỉ 0x9000...
echo.

REM Tìm Python và esptool
set ESPTOOL_CMD=python -m esptool
if exist "C:\Espressif\tools\python\v6.1\venv\Scripts\python.exe" (
    set ESPTOOL_CMD="C:\Espressif\tools\python\v6.1\venv\Scripts\python.exe" -m esptool
) else (
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
)

%ESPTOOL_CMD% --chip esp32s3 -p %COMPORT% -b 460800 --before default-reset --after hard-reset write-flash 0x9000 nvs.bin

if %errorlevel% equ 0 (
    echo.
    echo ========================================================
    echo [THÀNH CÔNG] Đã lưu mặc định WiFi "A Meey Zinh" vào Robot!
    echo Robot đang tự khởi động lại và kết nối vào "A Meey Zinh"...
    echo ========================================================
) else (
    echo.
    echo [THẤT BẠI] Lỗi kết nối cổng %COMPORT%. Vui lòng kiểm tra lại dây cáp Type-C!
)
echo.
pause
