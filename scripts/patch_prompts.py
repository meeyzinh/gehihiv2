import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()
rows = c.execute("SELECT id, system_prompt FROM presets WHERE category LIKE '%english%'").fetchall()
updated = 0
rule = (
    "\n\n[QUY TẮC ĐIỀU KHIỂN & HỦY BÀI HỌC]\n"
    "Nếu người dùng nói bằng tiếng Việt yêu cầu dừng học, hủy học, thoát bài học hoặc quay về trợ lý Sophia "
    "(ví dụ: 'hủy học tiếng anh', 'dừng bài học', 'thoát', 'quay lại sophia', 'stop english'), "
    "bạn PHẢI vui vẻ chào tạm biệt bằng tiếng Việt và xác nhận đã kết thúc bài học để trở về trợ lý Sophia."
)

for rid, sp in rows:
    sp = sp or ""
    if "[QUY TẮC ĐIỀU KHIỂN & HỦY BÀI HỌC]" not in sp:
        c.execute("UPDATE presets SET system_prompt = ? WHERE id = ?", (sp + rule, rid))
        updated += 1

conn.commit()
print(f"Updated {updated} presets successfully!")
conn.close()
