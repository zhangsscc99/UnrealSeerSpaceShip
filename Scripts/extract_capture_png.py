# -*- coding: utf-8 -*-
import json
import base64
import re
from pathlib import Path

src = Path(r"C:\Users\admin\.cursor\projects\c-Users-admin-Desktop-UnrealSeerSpaceShip\agent-tools\dd29131e-f2dd-4593-b3c5-bd0c6650b3dc.txt")
out = Path(r"c:\Users\admin\Desktop\UnrealSeerSpaceShip\Saved\suzhou_viewport_1.png")
raw = src.read_text(encoding="utf-8", errors="ignore")
data = None
try:
    j = json.loads(raw)
    data = j.get("returnValue", j).get("image", {}).get("data")
except Exception:
    m = re.search(r'"data"\s*:\s*"([^"]+)"', raw)
    if m:
        data = m.group(1)
if not data:
    raise SystemExit("no image data")
out.write_bytes(base64.b64decode(data))
print("wrote", out, out.stat().st_size)
