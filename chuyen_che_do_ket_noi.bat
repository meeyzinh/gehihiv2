@echo off
chcp 65001 >nul
echo =======================================================================
echo       CÔNG CỤ CHUYỂN ĐỔI CHẾ ĐỘ KẾT NỐI CHO ROBOT ESP32-S3
echo =======================================================================
echo.
echo [1] CHẾ ĐỘ 1: KẾT NỐI TRỰC TIẾP XIAOZHI.ME GỐC (api.tenclass.net)
echo     - Ưu điểm: Phản hồi siêu nhanh (Ping ~30ms), mượt mà 100%% như robot Xiaozhi thương mại.
echo     - MCP Tools: Vẫn gọi các công cụ MCP trên Render bình thường.
echo     - WiFi mặc định: A Meey Zinh / 12345678
echo.
echo [2] CHẾ ĐỘ 2: KẾT NỐI QUA SERVER RIÊNG (gehihiv2.onrender.com)
echo     - Ưu điểm: Hỗ trợ giám sát sóng âm mic trực tiếp trên Web Dashboard, bài học tiếng Anh.
echo     - Đã sửa triệt để: Truyền trực tiếp 0ms, không ngắt mic, tự tắt lắng nghe sau 10s.
echo     - WiFi mặc định: A Meey Zinh / 12345678
echo =======================================================================
echo.

set /p OPTION="Hãy chọn chế độ bạn muốn nạp (1 hoặc 2): "

if "%OPTION%"=="1" (
    set BIN_FILE=nvs_direct_xiaozhi.bin
    set MODE_NAME=KẾT NỐI TRỰC TIẾP XIAOZHI.ME GỐC
) else if "%OPTION%"=="2" (
    set BIN_FILE=nvs.bin
    set MODE_NAME=KẾT NỐI QUA SERVER RIÊNG RENDER
) else (
    echo [LỖI] Lựa chọn không hợp lệ!
    pause
    exit /b
)

set /p COMPORT="Nhập cổng COM của Robot (mặc định COM8): "
if "%COMPORT%"=="" set COMPORT=COM8

echo.
echo Đang nạp cấu hình [%MODE_NAME%] vào cổng %COMPORT%...
echo.

set ESPTOOL_CMD=python -m esptool
if exist "C:\Espressif\tools\python\v6.1\venv\Scripts\python.exe" (
    set ESPTOOL_CMD="C:\Espressif\tools\python\v6.1\venv\Scripts\python.exe" -m esptool
)

%ESPTOOL_CMD% --chip esp32s3 -p %COMPORT% -b 460800 --before default-reset --after hard-reset write-flash 0x9000 %BIN_FILE%

if %errorlevel% equ 0 (
    echo.
    echo =======================================================================
    echo [THÀNH CÔNG] Đã nạp thành công [%MODE_NAME%] vào Robot!
    echo Robot đang tự khởi động lại và kết nối WiFi 'A Meey Zinh'...
    echo =======================================================================
) else (
    echo.
    echo [THẤT BẠI] Lỗi kết nối cổng %COMPORT%. Vui lòng kiểm tra lại dây cáp!
)
pause
