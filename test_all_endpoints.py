import urllib.request
import json

base_url = "http://localhost:8000"

endpoints = [
    ("/", "HTML Dashboard"),
    ("/api/my-xiaozhi-options", "Options (Models, Languages, Voices)"),
    ("/api/my-xiaozhi-config", "Current Config & User"),
    ("/api/devices", "Devices list"),
    ("/api/curriculums", "20 Curriculums"),
    ("/api/presets?category=english", "English Presets"),
    ("/api/presets?category=role", "Role Presets"),
    ("/api/memories", "Memories list"),
    ("/api/tasks", "Tasks list"),
    ("/api/notes", "Notes list"),
    ("/api/robot/status", "Robot WebSocket Status"),
    ("/api/serial/logs", "Serial logs COM8"),
]

print("=== KIỂM TRA TẤT CẢ ENDPOINTS ===")
for path, desc in endpoints:
    url = base_url + path
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as res:
            status = res.status
            content = res.read()
            if path == "/":
                html = content.decode('utf-8')
                has_tutor = 'id="tabEnglishTutor"' in html
                has_curr = 'id="tabCurriculums"' in html
                has_roles = 'id="tabAiRoleSelect"' in html
                has_mem = 'id="tabMemory"' in html
                has_tasks = 'id="tabTasksMcp"' in html
                has_devs = 'id="tabDevicesManager"' in html
                all_tabs = has_tutor and has_curr and has_roles and has_mem and has_tasks and has_devs
                print(f"[OK] {status} {desc}: All 6 missing tabs present? {all_tabs}")
            else:
                data = json.loads(content.decode('utf-8'))
                count = len(data) if isinstance(data, (list, dict)) else 1
                print(f"[OK] {status} {desc}: Success (item/field count: {count})")
    except Exception as e:
        print(f"[FAIL] {desc} ({url}): {e}")
