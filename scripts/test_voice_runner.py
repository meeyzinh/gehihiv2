import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import asyncio
import sqlite3
from server import handle_robot_voice_command

async def test():
    print("--- TEST 1: CANCEL ---")
    await handle_robot_voice_command("Sophia ơi hủy học tiếng anh cho mình", "14:c1:9f:c4:ee:d0")
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    char1 = c.execute("SELECT character FROM agents LIMIT 1").fetchone()[0]
    print("Character after cancel:", char1[:60])
    
    print("\n--- TEST 2: START ANIMALS ---")
    await handle_robot_voice_command("bắt đầu học tiếng anh bài con vật", "14:c1:9f:c4:ee:d0")
    char2 = c.execute("SELECT character FROM agents LIMIT 1").fetchone()[0]
    print("Character after start:", char2[:60])
    
    print("\n--- TEST 3: CANCEL AGAIN ---")
    await handle_robot_voice_command("dừng bài học tiếng anh", "14:c1:9f:c4:ee:d0")
    char3 = c.execute("SELECT character FROM agents LIMIT 1").fetchone()[0]
    print("Character after cancel again:", char3[:60])
    conn.close()

if __name__ == "__main__":
    asyncio.run(test())
