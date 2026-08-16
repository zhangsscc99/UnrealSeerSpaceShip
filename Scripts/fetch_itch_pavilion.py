# -*- coding: utf-8 -*-
import re
import urllib.request
import zipfile
from pathlib import Path

HEADERS = {"User-Agent": "Mozilla/5.0"}
OUT = Path("Content/ThirdParty/ChineseGarden/Architecture")
OUT.mkdir(parents=True, exist_ok=True)

url = (
    "https://vvaytoyek.itch.io/chinese-four-corner-pavilion-free/download/"
    "eyJpZCI6NDQ0NDA5NywiZXhwaXJlcyI6MTc4NTMzNjA0Mn0%3d.TDj1WJE6JRc4ggkOYC1wxHPSz2M%3d"
)
html = urllib.request.urlopen(
    urllib.request.Request(url, headers=HEADERS), timeout=60
).read().decode("utf-8", "ignore")
Path("Saved/itch_pavilion.html").write_text(html, encoding="utf-8")
print("html", len(html))

patterns = [
    r'https://[^"\']+\.(?:zip|fbx|obj|glb)',
    r'data-upload_id="(\d+)"',
    r'data-url="([^"]+)"',
    r'href="([^"]*download[^"]*)"',
]
for pat in patterns:
    found = re.findall(pat, html, re.I)
    print(pat, "->", found[:10])

# itch file CDN often looks like:
# https://cdn.example... or //itch.itch.zone/uploads/...
cdn = re.findall(r'(https://[a-z0-9.-]*itch\.zone/[^"\']+)', html)
print("itch.zone", cdn[:10])
uploads = re.findall(r'(//[^"\']+/uploads/[^"\']+)', html)
print("uploads", uploads[:10])

# If we can find a direct zip button file name
files = re.findall(r'([\w\- ]+\.zip)', html, re.I)
print("zip names", files[:10])
