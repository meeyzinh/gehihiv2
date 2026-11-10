import urllib.request
import json
import time

BASE_URL = "http://localhost:8000"

def test_endpoint(name, method, path, payload=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            elapsed = int((time.time() - start) * 1000)
            status = resp.status
            body = resp.read().decode()
            try:
                body_json = json.loads(body)
                preview = str(body_json)[:100]
            except Exception:
                preview = body[:100]
            return {"name": name, "ok": True, "status": status, "ms": elapsed, "preview": preview}
    except urllib.error.HTTPError as e:
        elapsed = int((time.time() - start) * 1000)
        return {"name": name, "ok": False, "status": e.code, "ms": elapsed, "error": str(e)}
    except Exception as e:
        return {"name": name, "ok": False, "status": 0, "ms": 0, "error": str(e)}

def run_all_tests():
    tests = [
        # 1. Trạng thái kết nối Robot & Upstream
        ("1. Robot Status", "GET", "/api/robot/status", None),
        ("2. Serial Logs COM8", "GET", "/api/serial/logs", None),
        
        # 2. D-Pad & Kỹ năng phần cứng
        ("3. D-Pad Forward", "POST", "/api/robot/control", {"action": "forward"}),
        ("4. D-Pad Stop", "POST", "/api/robot/control", {"action": "stop"}),
        ("5. Kỹ năng Wiggle", "POST", "/api/robot/control", {"action": "wiggle"}),
        ("6. Kỹ năng Dance", "POST", "/api/robot/control", {"action": "dance"}),
        ("7. Bật/Tắt Đèn LED (GPIO 21)", "POST", "/api/robot/control", {"action": "led_toggle"}),
        
        # 3. Màn hình OLED & Biểu cảm
        ("8. OLED Biểu cảm (happy)", "POST", "/api/robot/display", {"emotion": "happy"}),
        ("9. OLED Biểu cảm (loving)", "POST", "/api/robot/display", {"emotion": "loving"}),
        ("10. Gửi chữ lên OLED (Speak)", "POST", "/api/robot/speak", {"text": "GMbot AI Online!", "emotion": "cool"}),
        
        # 4. Học Tiếng Anh
        ("11. Danh sách bài học Tiếng Anh", "GET", "/api/presets?category=english", None),
        ("12. Áp dụng bài học Tiếng Anh", "POST", "/api/apply-curriculum", {
            "curriculum_id": "12",
            "name": "Daily Routine - Bài 1: My day",
            "content": "Bạn là gia sư tiếng Anh hướng dẫn bài Daily Routine..."
        }),
        ("13. Hủy bài học Tiếng Anh", "POST", "/api/english-tutor/deactivate", {}),
        
        # 5. Vai trò GMbot AI
        ("14. Danh sách Vai trò", "GET", "/api/presets?category=role", None),
        ("15. Áp dụng Vai trò Sophia", "POST", "/api/apply-preset/1", {}),
        
        # 6. Cấu hình GMbot AI
        ("16. Lấy cấu hình Agent", "GET", "/api/agent/config", None),
        ("17. Reset Prompt về mặc định", "POST", "/api/reset-default-ai-prompt", {}),
        
        # 7. Bộ nhớ & Ghi chú
        ("18. Lấy danh sách Ghi chú", "GET", "/api/notes", None),
        ("19. Tạo Ghi chú mới", "POST", "/api/notes", {"title": "Test Ghi chú MCP", "content": "Kiểm tra tự động toàn diện"}),
        
        # 8. MCP Server (JSON-RPC 2.0)
        ("20. Danh sách công cụ MCP", "GET", "/api/mcp/tools", None),
        ("21. Gọi MCP: get_current_time", "POST", "/mcp", {
            "jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": "get_current_time", "arguments": {}}
        }),
        ("22. Gọi MCP: get_pc_system_info", "POST", "/mcp", {
            "jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {"name": "get_pc_system_info", "arguments": {}}
        }),
        
        # 9. Quản lý Thiết bị
        ("23. Danh sách Thiết bị (Devices)", "GET", "/api/devices", None),
        
        # 10. Phát nhạc YouTube Online trên Robot & Web
        ("24. Trạng thái nhạc YouTube", "GET", "/api/music/status", None),
        ("25. Tìm kiếm bài hát YouTube", "GET", "/api/music/search?q=Baby%20Shark", None),
        ("26. Stream bài hát tới Robot", "POST", "/api/music/play", {"url": "BwN3NiZt-PU", "title": "Bống Bống Bang Bang"}),
        ("27. Dừng phát nhạc", "POST", "/api/music/stop", {}),
        ("28. Lấy stream link nghe Web", "GET", "/api/music/info?id=BwN3NiZt-PU", None)
    ]

    print("=" * 70)
    print("   KIỂM TRA TỰ ĐỘNG TOÀN BỘ TÍNH NĂNG SERVER GMBOT & ROBOT")
    print("=" * 70)
    passed = 0
    for t in tests:
        res = test_endpoint(t[0], t[1], t[2], t[3])
        if res["ok"]:
            passed += 1
            print(f"[PASS] {res['name']:<35} ({res['ms']:>3}ms) -> {res['preview']}")
        else:
            print(f"[FAIL] {res['name']:<35} -> Lỗi HTTP {res['status']}: {res.get('error')}")
    
    print("-" * 70)
    print(f"Tổng kết: Đạt {passed}/{len(tests)} tính năng ({int(passed/len(tests)*100)}%)!")
    print("=" * 70)

if __name__ == "__main__":
    run_all_tests()
