# -*- coding: utf-8 -*-
from pathlib import Path
import re
html = Path("Saved/itch_pavilion.html").read_text(encoding="utf-8", errors="ignore")
# find upload ids and buttons near zip
for m in re.finditer(r".{0,120}Chinese Four-corner Pavilion\.zip.{0,400}", html):
    print("---")
    print(m.group(0)[:500])
print("UPLOAD IDS", re.findall(r"upload(?:_id|s)/(\d+)", html))
print("BUTTONS", re.findall(r"<button[^>]+>", html)[:20])
print("FORMS", re.findall(r"<form[^>]+>", html)[:20])
