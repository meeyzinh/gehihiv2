@echo off
set IDF_TOOLS_PATH=C:\Espressif
call C:\esp\v6.1\esp-idf\export.bat
cd /d "C:\Robot AI\Gmbot_server\xiaozhi-esp32-main\build"
C:\Espressif\tools\ninja\1.12.1\ninja.exe
