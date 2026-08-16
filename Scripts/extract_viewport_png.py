# Extract CaptureViewport base64 PNG from MCP agent-tools dump.
import base64
import re
import sys
from pathlib import Path

src = Path(sys.argv[1])
out = Path(sys.argv[2])
text = src.read_text(encoding="utf-8", errors="ignore")
out.parent.mkdir(parents=True, exist_ok=True)
m = re.search(r'"data"\s*:\s*"([A-Za-z0-9+/=]+)"', text)
if not m:
    raise SystemExit("no image data found")
raw = base64.b64decode(m.group(1))
out.write_bytes(raw)
print(f"wrote {out} ({len(raw)} bytes)")
