import re

with open("Web_templates/index.html", "r", encoding="utf-8") as f:
    text = f.read()

print("File size:", len(text))
menu_items = re.findall(r'<div[^>]*class=["\'][^"\']*menu-item[^"\']*["\'][^>]*>(.*?)</div>', text, re.IGNORECASE)
print("=== Menu Items ===")
for item in menu_items:
    clean = re.sub(r'<[^>]+>', '', item).strip()
    if clean:
        print(" -", clean)

print("\n=== Main Sections or Tab IDs ===")
sections = re.findall(r'<section[^>]*id=["\']([^"\']+)["\']', text, re.IGNORECASE)
for s in sections:
    print(" - Section:", s)

cards = re.findall(r'<div[^>]*class=["\'][^"\']*card[^"\']*["\'][^>]*id=["\']([^"\']+)["\']', text, re.IGNORECASE)
for c in cards:
    print(" - Card ID:", c)
