import re

with open("templates/index.html", "r", encoding="utf-8") as f:
    text = f.read()

ids = set(re.findall(r'document\.getElementById\(["\']([a-zA-Z0-9_\-]+)["\']\)', text))
missing = []
for i in ids:
    if f'id="{i}"' not in text and f"id='{i}'" not in text:
        missing.append(i)

print("Missing IDs count:", len(missing))
for m in sorted(missing):
    print(" - Missing:", m)
