@echo off
chcp 65001 >nul
echo ========================================================
echo    GMbot Robot ESP32-S3 Firmware Flasher (Offset 0x0)
echo ========================================================
echo.

set PORT=COM8
set /p USER_PORT="Nhập cổng COM của robot (nhấn Enter để dùng %PORT%): "
if not "%USER_PORT%"=="" set PORT=%USER_PORT%

echo.
echo [*] Đang nạp firmware vào robot tại %PORT% (Địa chỉ 0x0)...
echo.

"C:\Users\Welcome\.espressif\python_env\idf6.1_py3.14_env\Scripts\python.exe" -m esptool --chip esp32s3 -p %PORT% -b 921600 --before default_reset --after hard_reset write_flash --flash_mode dio --flash_freq 80m --flash_size 16MB 0x0 "%~dp0firmware_robot_0x0.bin"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo  [OK] Nạp firmware thành công 100%! Robot đang khởi động.
    echo ========================================================
) else (
    echo.
    echo [!] Nạp thất bại. Vui lòng kiểm tra lại cáp kết nối hoặc nhấn giữ nút BOOT khi cắm cáp.
)
echo.
pause
