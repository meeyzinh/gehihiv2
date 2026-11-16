"""
WebSocket MCP Client Bridge cho Render & xiaozhi.me
Hệ thống Đa Robot (Multi-Robot MCP Connection Pool / MCPConnectionManager)
- Duy trì đồng thời nhiều kết nối wss://api.xiaozhi.me/mcp/?token=... trên 1 tiến trình AsyncIO (~50KB RAM/robot)
- Quản lý background tasks: {device_id: asyncio.Task}
- Hỗ trợ biến môi trường XIAOZHI_MCP_WSS_LIST và XIAOZHI_MCP_WSS_URL
- Cách ly bộ nhớ và nhiệm vụ theo device_id / agent_id
- Tự động reconnect sau 3s, ping keep-alive 20s, giao thức MCP JSON-RPC 2.0 chuẩn 2024-11-05
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

from .tools_engine import (
    execute_tool,
    get_tool_schemas,
    get_tool_schemas_for_device,
    TOTAL_TOOLS_COUNT
)

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
    """Đại diện cho một kết nối WebSocket Client tới xiaozhi.me cho một Robot ESP32"""
    def __init__(
        self,
        device_id: str,
        device_name: str,
        websocket_url: str,
        agent_id: Optional[str] = None
    ):
        self.device_id = str(device_id).strip()
        self.device_name = (device_name or "Robot").strip()
        self.agent_id = str(agent_id or self.device_id).strip()
        self.websocket_url = websocket_url.strip()
        self.is_connected = False
        self.is_paused = False
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
            return "Chưa kết nối" if not self.is_paused else "Tạm dừng"
        elapsed = int(time.time() - self.connected_at)
        hours = elapsed // 3600
        minutes = (elapsed % 3600) // 60
        seconds = elapsed % 60
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        return f"{minutes}m {seconds}s"

    def start(self, manager: "MCPConnectionManager"):
        if not self.websocket_url:
            return
        self.stop_event.clear()
        self.is_paused = False
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()
        
        # Nếu task cũ còn chạy, hủy trước khi tạo mới
        if self.task and not self.task.done():
            self.task.cancel()

        self.task = loop.create_task(self._run_loop(manager))
        manager.connection_tasks[self.device_id] = self.task

    def pause(self, manager: "MCPConnectionManager"):
        self.is_paused = True
        self.is_connected = False
        manager.add_log("WARN", f"⏸️ Tạm dừng kết nối MCP cho Robot [{self.device_name}] (ID: {self.device_id})")

    def resume(self, manager: "MCPConnectionManager"):
        self.is_paused = False
        manager.add_log("INFO", f"▶️ Tiếp tục kết nối MCP cho Robot [{self.device_name}] (ID: {self.device_id})")
        if not self.task or self.task.done():
            self.start(manager)

    def stop(self):
        self.stop_event.set()
        if self.task and not self.task.done():
            self.task.cancel()
        self.is_connected = False

    async def _run_loop(self, manager: "MCPConnectionManager"):
        target_url = self.format_url(self.websocket_url)
        manager.add_log("INFO", f"🔌 Khởi động kết nối MCP cho Robot [{self.device_name}] (Agent: {self.agent_id}): {target_url[:45]}...")

        while not self.stop_event.is_set():
            if self.is_paused:
                await asyncio.sleep(1)
                continue

            try:
                # Kết nối WebSocket Client tới xiaozhi.me duy trì liên tục
                async with websockets.connect(
                    target_url,
                    ping_interval=20,
                    ping_timeout=20,
                    close_timeout=5
                ) as ws:
                    self.is_connected = True
                    self.connected_at = time.time()
                    manager.add_log("SUCCESS", f"🟢 ĐÃ KẾT NỐI VỚI XIAOZHI.ME cho Robot [{self.device_name}] (Agent: {self.agent_id})!")

                    while not self.stop_event.is_set() and not self.is_paused:
                        msg_text = await ws.recv()
                        try:
                            req = json.loads(msg_text)
                            req_id = req.get("id")
                            method = req.get("method")
                            params = req.get("params", {})

                            # 1. Bắt tay Initialize giao thức MCP JSON-RPC 2.0
                            if method == "initialize":
                                resp = {
                                    "jsonrpc": "2.0",
                                    "id": req_id,
                                    "result": {
                                        "protocolVersion": "2024-11-05",
                                        "capabilities": {"tools": {}},
                                        "serverInfo": {
                                            "name": f"Gehihi-VN-MCP-Portal-{self.device_name}",
                                            "version": "2.0.0"
                                        }
                                    }
                                }
                                await ws.send(json.dumps(resp))
                                manager.add_log("DEBUG", f"🤝 [{self.device_name}] Initialize MCP thành công (ID: {req_id})")

                            # 2. Thông báo đã sẵn sàng
                            elif method in ["notifications/initialized", "initialized"]:
                                self.is_connected = True
                                manager.add_log("INFO", f"✨ [{self.device_name}] chuyển sang trạng thái: Online Ready")

                            # 3. Trả về danh sách công cụ lọc theo phân quyền của Robot này
                            elif method == "tools/list":
                                active_schemas = get_tool_schemas_for_device(self.device_id)
                                resp = {
                                    "jsonrpc": "2.0",
                                    "id": req_id,
                                    "result": {
                                        "tools": active_schemas
                                    }
                                }
                                await ws.send(json.dumps(resp))
                                manager.add_log("SUCCESS", f"📋 [{self.device_name}] Đã gửi danh sách {len(active_schemas)} công cụ MCP")

                            # 4. Thực thi công cụ khi Robot gọi (Cách ly bộ nhớ theo device_id & agent_id)
                            elif method == "tools/call":
                                t_name = params.get("name", "")
                                t_args = params.get("arguments", {})
                                self.call_count += 1
                                self.last_call_tool = t_name
                                self.last_call_time = time.time()
                                manager.add_log("CALL", f"🚀 [{self.device_name}] Gọi công cụ: [{t_name}] - Tham số: {t_args}")

                                # Thực thi dưới 3 giây, truyền đúng device_id và agent_id
                                try:
                                    res_str = await asyncio.wait_for(
                                        execute_tool(t_name, t_args, device_id=self.device_id, agent_id=self.agent_id),
                                        timeout=3.0
                                    )
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
                                manager.add_log("SUCCESS", f"✓ [{self.device_name}] Trả lời '{t_name}' xong ({len(res_str)} ký tự)")

                            # 5. Phản hồi Ping Keep-Alive
                            elif method == "ping":
                                await ws.send(json.dumps({"jsonrpc": "2.0", "id": req_id, "result": {}}))

                        except Exception as msg_err:
                            manager.add_log("ERROR", f"[{self.device_name}] Lỗi xử lý bản tin JSON-RPC: {msg_err}")

            except asyncio.CancelledError:
                manager.add_log("INFO", f"⏹️ Đã dừng kết nối MCP cho Robot [{self.device_name}].")
                break
            except Exception as e:
                self.is_connected = False
                if self.is_paused or self.stop_event.is_set():
                    break
                self.reconnect_count += 1
                manager.add_log("WARN", f"⚠️ [{self.device_name}] Mất kết nối tới xiaozhi.me ({e}). Tự động kết nối lại sau 3 giây (Lần {self.reconnect_count})...")
                await asyncio.sleep(3)


class MCPConnectionManager:
    """
    Bộ quản lý Đa kết nối WebSocket MCP (MCPConnectionPool / MCPConnectionManager)
    Quản lý đồng thời hàng chục kết nối WebSocket của nhiều Robot trên cùng tiến trình AsyncIO
    """
    def __init__(self):
        self.devices: Dict[str, McpClientConnection] = {}
        self.connection_tasks: Dict[str, asyncio.Task] = {}
        self.logs: deque = deque(maxlen=200)
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
                    agent_id TEXT,
                    websocket_url TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    is_paused INTEGER DEFAULT 0,
                    created_at TEXT
                )
            """)
            # Kiểm tra và bổ sung cột agent_id, is_paused nếu nâng cấp từ bản cũ
            try:
                cur.execute("ALTER TABLE mcp_portal_devices ADD COLUMN agent_id TEXT")
            except Exception:
                pass
            try:
                cur.execute("ALTER TABLE mcp_portal_devices ADD COLUMN is_paused INTEGER DEFAULT 0")
            except Exception:
                pass
            conn.commit()
            conn.close()
        except Exception as e:
            self.add_log("ERROR", f"Khởi tạo bảng SQLite mcp_portal_devices thất bại: {e}")

    def add_log(self, level: str, message: str):
        entry = McpLogEntry(level, message)
        self.logs.append(entry.to_dict())
        print(f"[MCP POOL {level}] {message}")

    def get_logs(self, limit: int = 50) -> List[Dict[str, str]]:
        return list(self.logs)[-limit:]

    def parse_mcp_wss_list(self, raw_env: str) -> List[Dict[str, str]]:
        """
        Phân tích biến môi trường XIAOZHI_MCP_WSS_LIST
        Hỗ trợ định dạng JSON: [{"name": "Robot_1", "agent_id": "2567180", "wss": "wss://..."}, ...]
        Hoặc danh sách URL cách nhau bằng dấu phẩy: wss://...token=1, wss://...token=2
        """
        results = []
        raw_env = (raw_env or "").strip()
        if not raw_env:
            return results

        # Thử parse JSON
        if raw_env.startswith("[") and raw_env.endswith("]"):
            try:
                parsed = json.loads(raw_env)
                if isinstance(parsed, list):
                    for idx, item in enumerate(parsed):
                        if isinstance(item, dict):
                            wss_url = item.get("wss") or item.get("url") or item.get("websocket_url", "")
                            if wss_url:
                                name = item.get("name") or f"Robot_{idx+1}"
                                agt_id = str(item.get("agent_id") or item.get("id") or f"agent_{idx+1}")
                                dev_id = str(item.get("device_id") or agt_id)
                                results.append({
                                    "id": dev_id,
                                    "name": name,
                                    "agent_id": agt_id,
                                    "websocket_url": wss_url
                                })
                    if results:
                        return results
            except Exception as e:
                self.add_log("WARN", f"Lỗi phân tích cú pháp JSON XIAOZHI_MCP_WSS_LIST: {e}")

        # Fallback: Phân tách bằng dấu phẩy
        parts = [p.strip() for p in raw_env.split(",") if p.strip()]
        for idx, part in enumerate(parts):
            dev_id = f"robot_env_{idx+1}"
            results.append({
                "id": dev_id,
                "name": f"Robot {idx+1}",
                "agent_id": dev_id,
                "websocket_url": part
            })
        return results

    def load_devices_from_storage(self):
        """Nạp cấu hình Đa Robot từ SQLite và Biến Môi Trường Render (Chống mất cấu hình)"""
        # 1. Đọc từ SQLite mcp_portal_devices
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT id, name, agent_id, websocket_url, is_active, is_paused FROM mcp_portal_devices WHERE is_active = 1")
            rows = cur.fetchall()
            conn.close()
            for r in rows:
                dev_id, dev_name, agt_id, ws_url, is_act, is_p = r
                if dev_id not in self.devices:
                    conn_obj = McpClientConnection(dev_id, dev_name, ws_url, agent_id=agt_id or dev_id)
                    conn_obj.is_paused = bool(is_p)
                    self.devices[dev_id] = conn_obj
        except Exception as e:
            self.add_log("ERROR", f"Đọc SQLite mcp_portal_devices lỗi: {e}")

        # 2. Đọc danh sách Đa Robot từ biến môi trường XIAOZHI_MCP_WSS_LIST
        env_list_raw = os.getenv("XIAOZHI_MCP_WSS_LIST", "").strip()
        if env_list_raw:
            items = self.parse_mcp_wss_list(env_list_raw)
            for itm in items:
                d_id = itm["id"]
                if d_id not in self.devices:
                    conn_obj = McpClientConnection(d_id, itm["name"], itm["websocket_url"], agent_id=itm["agent_id"])
                    self.devices[d_id] = conn_obj
                    self.save_device_to_db(d_id, itm["name"], itm["websocket_url"], agent_id=itm["agent_id"])
                    self.add_log("INFO", f"✓ Đã tự động nạp Robot từ XIAOZHI_MCP_WSS_LIST: [{itm['name']}]")

        # 3. Đọc biến đơn lẻ XIAOZHI_MCP_WSS_URL
        env_url = (os.getenv("XIAOZHI_MCP_WSS_URL", "").strip() or 
                   os.getenv("XIAOZHI_MCP_ENDPOINT", "").strip() or
                   os.getenv("UPSTREAM_AUTH_TOKEN", "").strip())
        env_name = os.getenv("DEVICE_NAME", "330730").strip() or "330730"

        if env_url:
            default_id = "330730"
            if default_id not in self.devices:
                conn_obj = McpClientConnection(default_id, env_name, env_url, agent_id=default_id)
                self.devices[default_id] = conn_obj
                self.save_device_to_db(default_id, env_name, env_url, agent_id=default_id)
                self.add_log("INFO", f"✓ Đã tự động nạp Robot mặc định từ XIAOZHI_MCP_WSS_URL: [{env_name}]")

    def save_device_to_db(
        self,
        device_id: str,
        device_name: str,
        websocket_url: str,
        agent_id: Optional[str] = None,
        is_paused: bool = False
    ):
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO mcp_portal_devices (id, name, agent_id, websocket_url, is_active, is_paused, created_at)
                VALUES (?, ?, ?, ?, 1, ?, ?)
            """, (
                device_id,
                device_name,
                agent_id or device_id,
                websocket_url,
                1 if is_paused else 0,
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
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

    def find_device(self, identifier: str) -> Optional[McpClientConnection]:
        """Tìm thiết bị theo device_id hoặc agent_id"""
        if identifier in self.devices:
            return self.devices[identifier]
        for dev in self.devices.values():
            if dev.agent_id == identifier or dev.device_id == identifier:
                return dev
        return None

    def add_device(
        self,
        device_name: str,
        websocket_url: str,
        agent_id: Optional[str] = None,
        device_id: Optional[str] = None
    ) -> McpClientConnection:
        dev_name = device_name.strip() or "330730"
        dev_id = device_id.strip() if device_id else (agent_id.strip() if agent_id else f"dev_{int(time.time()*1000)}")
        agt_id = agent_id.strip() if agent_id else dev_id

        # Nếu đã có connection này, dừng task cũ
        if dev_id in self.devices:
            self.devices[dev_id].stop()

        conn_obj = McpClientConnection(dev_id, dev_name, websocket_url, agent_id=agt_id)
        self.devices[dev_id] = conn_obj
        self.save_device_to_db(dev_id, dev_name, websocket_url, agent_id=agt_id)

        if self.is_started:
            conn_obj.start(self)
        self.add_log("SUCCESS", f"➕ Đã thêm kết nối Robot mới: [{dev_name}] (ID: {dev_id})")
        return conn_obj

    def remove_device(self, device_id: str) -> bool:
        dev = self.find_device(device_id)
        if dev:
            d_id = dev.device_id
            self.devices.pop(d_id, None)
            dev.stop()
            if d_id in self.connection_tasks:
                task = self.connection_tasks.pop(d_id)
                if not task.done():
                    task.cancel()
            self.delete_device_from_db(d_id)
            self.add_log("INFO", f"➖ Đã xóa kết nối Robot: [{dev.device_name}]")
            return True
        return False

    def pause_device(self, device_id: str) -> bool:
        """Tạm dừng một robot mà không làm gián đoạn các robot khác"""
        dev = self.find_device(device_id)
        if dev:
            dev.pause(self)
            self.save_device_to_db(dev.device_id, dev.device_name, dev.websocket_url, agent_id=dev.agent_id, is_paused=True)
            return True
        return False

    def resume_device(self, device_id: str) -> bool:
        """Tiếp tục kết nối lại cho một robot cụ thể"""
        dev = self.find_device(device_id)
        if dev:
            dev.resume(self)
            self.save_device_to_db(dev.device_id, dev.device_name, dev.websocket_url, agent_id=dev.agent_id, is_paused=False)
            return True
        return False

    def start_all(self):
        """Khởi động toàn bộ dàn Robot khi Server khởi động"""
        self.is_started = True
        self.load_devices_from_storage()
        for dev in self.devices.values():
            if not dev.is_paused:
                dev.start(self)
        self.add_log("INFO", f"🚀 MCPConnectionPool đã khởi chạy với {len(self.devices)} Robot song song.")

    def stop_all(self):
        """Dừng sạch các background tasks khi tắt server"""
        for dev in self.devices.values():
            dev.stop()
        self.connection_tasks.clear()
        self.is_started = False
        self.add_log("INFO", "🛑 Đã dừng toàn bộ kết nối trong MCPConnectionPool.")

    def get_status_summary(self) -> Dict[str, Any]:
        """Tổng hợp trạng thái realtime của toàn bộ dàn Robot phục vụ Web UI"""
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
                "agent_id": dev.agent_id,
                "websocket_url": dev.websocket_url,
                "is_connected": dev.is_connected,
                "is_paused": dev.is_paused,
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


# Aliases & Singleton Instance
MCPConnectionPool = MCPConnectionManager
McpDeviceManager = MCPConnectionManager
mcp_device_manager = MCPConnectionManager()
