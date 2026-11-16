"""
WebSocket MCP Client Bridge cho Render & xiaozhi.me
Hỗ trợ Multi-Device, Auto-Reconnect 24/7 (3s), Ping Keep-Alive (20s)
Giao thức MCP JSON-RPC 2.0 chuẩn 2024-11-05
"""

import os
import json
import time
import sqlite3
import asyncio
import datetime
from collections import deque
from typing import Dict, Any, List, Optional
import websockets

from .tools_engine import execute_tool, get_tool_schemas, TOTAL_TOOLS_COUNT

DB_PATH = os.path.abspath("database.db")


class McpLogEntry:
    def __init__(self, level: str, message: str):
        self.timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.level = level
        self.message = message

    def to_dict(self) -> Dict[str, str]:
        return {
            "time": self.timestamp,
            "level": self.level,
            "message": self.message
        }


class McpClientConnection:
    """Đại diện cho một kết nối WebSocket Client tới xiaozhi.me cho một thiết bị"""
    def __init__(self, device_id: str, device_name: str, websocket_url: str):
        self.device_id = device_id
        self.device_name = device_name
        self.websocket_url = websocket_url.strip()
        self.is_connected = False
        self.connected_at: Optional[float] = None
        self.call_count = 0
        self.last_call_tool: str = ""
        self.last_call_time: Optional[float] = None
        self.reconnect_count = 0
        self.task: Optional[asyncio.Task] = None
        self.stop_event = asyncio.Event()

    def format_url(self, raw_url: str) -> str:
        raw_url = raw_url.strip()
        if raw_url.startswith("wss://") or raw_url.startswith("ws://"):
            return raw_url
        if raw_url.startswith("token="):
            return f"wss://api.xiaozhi.me/mcp/?{raw_url}"
        return f"wss://api.xiaozhi.me/mcp/?token={raw_url}"

    def get_uptime_str(self) -> str:
        if not self.is_connected or not self.connected_at:
            return "Chưa kết nối"
        elapsed = int(time.time() - self.connected_at)
        hours = elapsed // 3600
        minutes = (elapsed % 3600) // 60
        seconds = elapsed % 60
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        return f"{minutes}m {seconds}s"

    def start(self, manager: "McpDeviceManager"):
        if not self.websocket_url:
            return
        self.stop_event.clear()
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()
        self.task = loop.create_task(self._run_loop(manager))

    def stop(self):
        self.stop_event.set()
        if self.task and not self.task.done():
            self.task.cancel()
        self.is_connected = False

    async def _run_loop(self, manager: "McpDeviceManager"):
        target_url = self.format_url(self.websocket_url)
        manager.add_log("INFO", f"🔌 Khởi động kết nối MCP cho thiết bị [{self.device_name}]: {target_url[:45]}...")

        while not self.stop_event.is_set():
            try:
                # Kết nối WebSocket Client tới xiaozhi.me
                async with websockets.connect(
                    target_url,
                    ping_interval=20,
                    ping_timeout=20,
                    close_timeout=5
                ) as ws:
                    self.is_connected = True
                    self.connected_at = time.time()
                    manager.add_log("SUCCESS", f"🟢 ĐÃ KẾT NỐI VỚI XIAOZHI.ME cho thiết bị [{self.device_name}]!")

                    while not self.stop_event.is_set():
                        msg_text = await ws.recv()
                        try:
                            req = json.loads(msg_text)
                            req_id = req.get("id")
                            method = req.get("method")
                            params = req.get("params", {})

                            # 1. Khởi tạo bắt tay giao thức MCP
                            if method == "initialize":
                                resp = {
                                    "jsonrpc": "2.0",
                                    "id": req_id,
                                    "result": {
                                        "protocolVersion": "2024-11-05",
                                        "capabilities": {"tools": {}},
                                        "serverInfo": {
                                            "name": "Gehihi-VN-MCP-Portal",
                                            "version": "2.0.0"
                                        }
                                    }
                                }
                                await ws.send(json.dumps(resp))
                                manager.add_log("DEBUG", f"🤝 Bắt tay Initialize thành công với xiaozhi.me (ID: {req_id})")

                            # 2. Thông báo đã sẵn sàng
                            elif method in ["notifications/initialized", "initialized"]:
                                self.is_connected = True
                                manager.add_log("INFO", f"✨ Thiết bị [{self.device_name}] chuyển sang trạng thái: Online Ready")

                            # 3. Liệt kê 78 công cụ MCP
                            elif method == "tools/list":
                                active_schemas = get_tool_schemas()
                                resp = {
                                    "jsonrpc": "2.0",
                                    "id": req_id,
                                    "result": {
                                        "tools": active_schemas
                                    }
                                }
                                await ws.send(json.dumps(resp))
                                manager.add_log("SUCCESS", f"📋 Đã gửi danh sách {len(active_schemas)} công cụ MCP cho xiaozhi.me")

                            # 4. Thực thi công cụ khi Robot gọi
                            elif method == "tools/call":
                                t_name = params.get("name", "")
                                t_args = params.get("arguments", {})
                                self.call_count += 1
                                self.last_call_tool = t_name
                                self.last_call_time = time.time()
                                manager.add_log("CALL", f"🚀 Robot gọi công cụ: [{t_name}] - Tham số: {t_args}")

                                # Thực thi dưới 3 giây
                                try:
                                    res_str = await asyncio.wait_for(execute_tool(t_name, t_args), timeout=3.0)
                                except asyncio.TimeoutError:
                                    res_str = f"Thời gian thực thi công cụ '{t_name}' vượt quá 3 giây."
                                except Exception as exec_err:
                                    res_str = f"Lỗi thực thi: {str(exec_err)}"

                                resp = {
                                    "jsonrpc": "2.0",
                                    "id": req_id,
                                    "result": {
                                        "content": [{"type": "text", "text": res_str}],
                                        "isError": False
                                    }
                                }
                                await ws.send(json.dumps(resp))
                                manager.add_log("SUCCESS", f"✓ Trả lời '{t_name}' xong ({len(res_str)} ký tự)")

                            # 5. Phản hồi Ping Keep-Alive
                            elif method == "ping":
                                await ws.send(json.dumps({"jsonrpc": "2.0", "id": req_id, "result": {}}))

                        except Exception as msg_err:
                            manager.add_log("ERROR", f"Lỗi xử lý bản tin JSON-RPC: {msg_err}")

            except asyncio.CancelledError:
                manager.add_log("INFO", f"⏹️ Đã dừng kết nối MCP cho thiết bị [{self.device_name}].")
                break
            except Exception as e:
                self.is_connected = False
                self.reconnect_count += 1
                manager.add_log("WARN", f"⚠️ Mất kết nối tới xiaozhi.me ({e}). Tự động kết nối lại sau 3 giây (Lần {self.reconnect_count})...")
                await asyncio.sleep(3)


class McpDeviceManager:
    """Quản lý toàn bộ danh sách thiết bị MCP, tự khởi động và lưu trữ vào SQLite"""
    def __init__(self):
        self.devices: Dict[str, McpClientConnection] = {}
        self.logs: deque = deque(maxlen=150)
        self.is_started = False
        self._init_db()

    def _init_db(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS mcp_portal_devices (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    websocket_url TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            self.add_log("ERROR", f"Khởi tạo bảng SQLite mcp_portal_devices thất bại: {e}")

    def add_log(self, level: str, message: str):
        entry = McpLogEntry(level, message)
        self.logs.append(entry.to_dict())
        # Đồng thời in ra stdout của server Render
        print(f"[MCP PORTAL {level}] {message}")

    def get_logs(self, limit: int = 50) -> List[Dict[str, str]]:
        return list(self.logs)[-limit:]

    def load_devices_from_storage(self):
        """Đọc cấu hình thiết bị từ SQLite và Biến môi trường Render (Chống reset disk)"""
        # 1. Đọc từ SQLite
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT id, name, websocket_url, is_active FROM mcp_portal_devices WHERE is_active = 1")
            rows = cur.fetchall()
            conn.close()
            for r in rows:
                dev_id, dev_name, ws_url, is_act = r
                if dev_id not in self.devices:
                    self.devices[dev_id] = McpClientConnection(dev_id, dev_name, ws_url)
        except Exception as e:
            self.add_log("ERROR", f"Đọc SQLite mcp_portal_devices lỗi: {e}")

        # 2. Đọc từ Biến Môi Trường Render (XIAOZHI_MCP_WSS_URL hoặc XIAOZHI_MCP_ENDPOINT)
        env_url = (os.getenv("XIAOZHI_MCP_WSS_URL", "").strip() or 
                   os.getenv("XIAOZHI_MCP_ENDPOINT", "").strip() or
                   os.getenv("UPSTREAM_AUTH_TOKEN", "").strip())
        env_name = os.getenv("DEVICE_NAME", "330730").strip() or "330730"

        if env_url:
            default_id = "default_device"
            if default_id not in self.devices:
                conn_obj = McpClientConnection(default_id, env_name, env_url)
                self.devices[default_id] = conn_obj
                self.save_device_to_db(default_id, env_name, env_url)
                self.add_log("INFO", f"✓ Đã tự động nạp thiết bị mặc định từ Biến Môi Trường Render: [{env_name}]")

    def save_device_to_db(self, device_id: str, device_name: str, websocket_url: str):
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO mcp_portal_devices (id, name, websocket_url, is_active, created_at)
                VALUES (?, ?, ?, 1, ?)
            """, (device_id, device_name, websocket_url, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()
        except Exception as e:
            self.add_log("ERROR", f"Lưu thiết bị vào SQLite thất bại: {e}")

    def delete_device_from_db(self, device_id: str):
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("DELETE FROM mcp_portal_devices WHERE id = ?", (device_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            self.add_log("ERROR", f"Xóa thiết bị khỏi SQLite thất bại: {e}")

    def add_device(self, device_name: str, websocket_url: str) -> McpClientConnection:
        dev_name = device_name.strip() or "330730"
        dev_id = f"dev_{int(time.time()*1000)}"
        conn_obj = McpClientConnection(dev_id, dev_name, websocket_url)
        self.devices[dev_id] = conn_obj
        self.save_device_to_db(dev_id, dev_name, websocket_url)
        if self.is_started:
            conn_obj.start(self)
        self.add_log("SUCCESS", f"➕ Đã thêm thiết bị mới: [{dev_name}]")
        return conn_obj

    def remove_device(self, device_id: str) -> bool:
        if device_id in self.devices:
            dev = self.devices.pop(device_id)
            dev.stop()
            self.delete_device_from_db(device_id)
            self.add_log("INFO", f"➖ Đã xóa thiết bị: [{dev.device_name}]")
            return True
        return False

    def start_all(self):
        """Khởi động toàn bộ các kết nối thiết bị khi Server khởi động"""
        self.is_started = True
        self.load_devices_from_storage()
        for dev in self.devices.values():
            dev.start(self)
        self.add_log("INFO", f"🚀 MCP Portal Manager đã sẵn sàng với {len(self.devices)} thiết bị.")

    def stop_all(self):
        """Dừng sạch các background tasks khi tắt server"""
        for dev in self.devices.values():
            dev.stop()
        self.is_started = False
        self.add_log("INFO", "🛑 Đã dừng toàn bộ kết nối MCP Portal.")

    def get_status_summary(self) -> Dict[str, Any]:
        """Tổng hợp trạng thái realtime phục vụ Web Dashboard"""
        device_list = []
        any_connected = False
        total_calls = 0

        for d_id, dev in self.devices.items():
            if dev.is_connected:
                any_connected = True
            total_calls += dev.call_count
            device_list.append({
                "id": d_id,
                "name": dev.device_name,
                "websocket_url": dev.websocket_url,
                "is_connected": dev.is_connected,
                "uptime": dev.get_uptime_str(),
                "call_count": dev.call_count,
                "last_call_tool": dev.last_call_tool,
                "reconnect_count": dev.reconnect_count
            })

        return {
            "status": "online" if any_connected else "disconnected",
            "is_connected": any_connected,
            "total_devices": len(self.devices),
            "total_tools": TOTAL_TOOLS_COUNT,
            "total_calls": total_calls,
            "devices": device_list
        }


# Singleton Instance
mcp_device_manager = McpDeviceManager()
