#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CẦU NỐI SERIAL COM8 -> RENDER CLOUD (GEHIHIV2.ONRENDER.COM)
Cho phép máy tính cục bộ kết nối cổng USB COM8 của Robot ESP32 với máy chủ Render Cloud.
Tất cả nhật ký console, trạng thái thiết bị và lệnh điều khiển (D-Pad, OLED, Loa)
sẽ được đồng bộ song công (Full-Duplex) theo thời gian thực qua WebSocket.
"""

import sys
import os
import time
import json
import asyncio
import threading
import argparse

# Tự động kiểm tra và cài đặt thư viện cần thiết
try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("[CÀI ĐẶT] Đang cài đặt thư viện pyserial...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyserial"])
    import serial
    import serial.tools.list_ports

try:
    import websockets
except ImportError:
    print("[CÀI ĐẶT] Đang cài đặt thư viện websockets...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
    import websockets


class SerialRenderBridge:
    def __init__(self, port: str = "COM8", baudrate: int = 115200, server_url: str = "https://gehihiv2.onrender.com"):
        self.port = port
        self.baudrate = baudrate
        clean_url = server_url.rstrip("/")
        if clean_url.startswith("https://"):
            self.ws_url = clean_url.replace("https://", "wss://") + "/ws/serial-bridge"
        elif clean_url.startswith("http://"):
            self.ws_url = clean_url.replace("http://", "ws://") + "/ws/serial-bridge"
        else:
            self.ws_url = clean_url + "/ws/serial-bridge"

        self.ser: serial.Serial | None = None
        self.ws = None
        self.is_running = True
        self.last_mic_diag_time = 0.0
        self.hw_info = {
            "chip": "ESP32-S3 (v0.2)",
            "mac": "14:C1:9F:C4:EE:D0",
            "sku": "robot-mini-s3",
            "display": "SSD1306 (128x64 OLED)",
            "ip": "10.26.1.173",
            "wifi_ssid": "A Meey Zinh",
            "firmware": "Xiaozhi v2.5.3"
        }
        self.loop: asyncio.AbstractEventLoop | None = None

    def log(self, prefix: str, msg: str):
        now = time.strftime("%H:%M:%S")
        print(f"[{now}] {prefix} {msg}")

    def open_serial(self) -> bool:
        try:
            if self.ser and self.ser.is_open:
                try:
                    self.ser.close()
                except Exception:
                    pass

            self.ser = serial.Serial()
            self.ser.port = self.port
            self.ser.baudrate = self.baudrate
            self.ser.timeout = 0.1
            self.ser.write_timeout = 0.5
            # Giữ DTR và RTS ở mức FALSE để không gây Reset chập chờn cho ESP32 khi kết nối
            self.ser.dsrdtr = False
            self.ser.rtscts = False
            self.ser.dtr = False
            self.ser.rts = False
            self.ser.open()
            self.log("🔌 [SERIAL]", f"✓ Đã mở thành công cổng {self.port} (Baudrate: {self.baudrate})")
            return True
        except Exception as e:
            self.log("⚠ [SERIAL]", f"Không thể mở cổng {self.port}: {e}")
            self.ser = None
            return False

    def reset_chip(self):
        """Khởi động lại ESP32-S3 bằng cách nháy chân RTS"""
        if not self.ser or not self.ser.is_open:
            return
        try:
            self.log("🔄 [RESET]", "Đang gửi tín hiệu Hard Reset tới ESP32 qua chân RTS...")
            self.ser.dtr = False
            self.ser.rts = True
            time.sleep(0.12)
            self.ser.rts = False
            time.sleep(0.05)
            self.log("🔄 [RESET]", "✓ Đã khởi động lại chip ESP32 thành công!")
        except Exception as e:
            self.log("⚠ [RESET]", f"Lỗi reset: {e}")

    def serial_read_loop(self):
        """Đọc liên tục nhật ký từ cổng COM8 và chuyển tiếp lên Server qua WebSocket"""
        while self.is_running:
            if not self.ser or not self.ser.is_open:
                time.sleep(1.0)
                self.open_serial()
                continue

            try:
                if self.ser.in_waiting:
                    raw = self.ser.readline()
                    line = raw.decode("utf-8", errors="ignore").strip()
                    if line:
                        # Lọc bớt log MIC Diagnostic lặp đi lặp lại để tránh nghẽn mạng (chỉ gửi 1 lần mỗi 5 giây)
                        if "MIC Diagnostic" in line:
                            now = time.time()
                            if now - self.last_mic_diag_time < 5.0:
                                continue
                            self.last_mic_diag_time = now

                        # Trích xuất thông tin phần cứng tự động
                        if "SKU=" in line:
                            try:
                                self.hw_info["sku"] = line.split("SKU=")[-1].strip()
                            except Exception: pass
                        elif "sta ip:" in line:
                            try:
                                self.hw_info["ip"] = line.split("sta ip:")[-1].split(",")[0].strip()
                            except Exception: pass
                        elif "sta (" in line:
                            try:
                                self.hw_info["mac"] = line.split("sta (")[-1].split(")")[0].strip().upper()
                            except Exception: pass

                        # In ra terminal
                        print(f"  [ROBOT COM8] {line}")

                        # Gửi lên WebSocket Render
                        if self.ws and self.loop and self.loop.is_running():
                            payload = json.dumps({"type": "log", "text": line})
                            asyncio.run_coroutine_threadsafe(self.safe_send(payload), self.loop)
                else:
                    time.sleep(0.015)
            except Exception as e:
                self.log("⚠ [SERIAL]", f"Lỗi đọc COM: {e}. Đang thử mở lại sau 2s...")
                try:
                    if self.ser:
                        self.ser.close()
                except Exception:
                    pass
                self.ser = None
                time.sleep(2.0)

    async def safe_send(self, payload: str):
        if self.ws:
            try:
                await self.ws.send(payload)
            except Exception:
                pass

    async def run_ws_client(self):
        """Duy trì kết nối WebSocket Client tới Cloud Server Render"""
        self.loop = asyncio.get_running_loop()
        retry_delay = 2

        while self.is_running:
            self.log("🌐 [CLOUD]", f"Đang kết nối tới máy chủ Render: {self.ws_url} ...")
            try:
                async with websockets.connect(
                    self.ws_url,
                    ping_interval=15,
                    ping_timeout=15,
                    close_timeout=5
                ) as ws:
                    self.ws = ws
                    retry_delay = 2
                    self.log("🟢 [CLOUD]", f"✓ ĐÃ KẾT NỐI THÀNH CÔNG VỚI RENDER CLOUD! Robot trên {self.port} đã online!")
                    
                    # Gửi bản tin chào ban đầu kèm thông tin phần cứng
                    init_msg = json.dumps({
                        "type": "hw_info",
                        "port": self.port,
                        "baudrate": self.baudrate,
                        "hw_info": self.hw_info
                    })
                    await ws.send(init_msg)

                    # Lắng nghe lệnh từ Web Render gửi xuống
                    async for message in ws:
                        try:
                            data = json.loads(message)
                            mtype = data.get("type")
                            if mtype == "command":
                                cmd = data.get("command", "")
                                if cmd and self.ser and self.ser.is_open:
                                    self.log("📥 [LỆNH WEB]", f">> {cmd}")
                                    line_to_write = cmd.strip() + "\r\n"
                                    self.ser.write(line_to_write.encode("utf-8"))
                            elif mtype == "reset":
                                self.reset_chip()
                            elif mtype == "pong":
                                pass
                        except Exception as ex:
                            self.log("⚠ [XỬ LÝ LỆNH]", f"Lỗi: {ex}")

            except (websockets.ConnectionClosed, ConnectionResetError) as e:
                self.ws = None
                self.log("🔴 [CLOUD]", f"Mất kết nối với Render ({e}). Thử lại sau {retry_delay}s...")
            except Exception as e:
                self.ws = None
                self.log("🔴 [CLOUD]", f"Không thể kết nối Render ({e}). Thử lại sau {retry_delay}s...")

            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 1.5, 10)

    def start(self):
        print("=" * 68)
        print("   🤖 CẦU NỐI SERIAL USB COM8 -> CLOUD RENDER (GMBOT AI) 🤖   ")
        print(f"   - Cổng Serial phần cứng: {self.port} (Baudrate: {self.baudrate})")
        print(f"   - Máy chủ Cloud Render:  {self.ws_url}")
        print("=" * 68)
        print("Đang khởi động tiến trình...")

        # 1. Mở cổng Serial
        self.open_serial()

        # 2. Khởi chạy luồng đọc Serial
        read_thread = threading.Thread(target=self.serial_read_loop, daemon=True)
        read_thread.start()

        # 3. Chạy WebSocket Loop
        try:
            asyncio.run(self.run_ws_client())
        except KeyboardInterrupt:
            self.log("🛑 [HỆ THỐNG]", "Đang dừng chương trình...")
            self.is_running = False
            if self.ser:
                try:
                    self.ser.close()
                except Exception:
                    pass
            print("Đã thoát an toàn.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cầu nối Serial USB COM8 lên Cloud Render")
    parser.add_argument("--port", default="COM8", help="Tên cổng Serial (mặc định: COM8)")
    parser.add_argument("--baud", type=int, default=115200, help="Baudrate (mặc định: 115200)")
    parser.add_argument("--server", default="https://gehihiv2.onrender.com", help="Địa chỉ server Render")
    args = parser.parse_args()

    bridge = SerialRenderBridge(port=args.port, baudrate=args.baud, server_url=args.server)
    bridge.start()
