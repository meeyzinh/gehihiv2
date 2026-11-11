@echo off
set IDF_TOOLS_PATH=C:\Espressif
call C:\esp\v6.1\esp-idf\export.bat
cd /d "c:\Robot AI\Gmbot_server\xiaozhi-esp32-main"
python scripts/build.py robot-mini-s3 --name robot-mini-s3 --language vi-VN
