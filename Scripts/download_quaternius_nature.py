# -*- coding: utf-8 -*-
import re
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Content" / "ThirdParty" / "ChineseGarden"
HEADERS = {"User-Agent": "Mozilla/5.0"}

OUT.mkdir(parents=True, exist_ok=True)

# OpenGameArt Quaternius Ultimate Nature Pack
html = urllib.request.urlopen(
    urllib.request.Request(
        "https://opengameart.org/content/low-poly-nature-pack-1", headers=HEADERS
    ),
    timeout=60,
).read().decode("utf-8", "ignore")
zips = re.findall(r'href="(/sites/default/files/[^"]+\.zip)"', html)
print("found zips:", zips)
if not zips:
    raise SystemExit("no zip link")
url = "https://opengameart.org" + zips[0]
dest = OUT / "ultimate_nature_pack_by_quaternius.zip"
print("download", url)
if not dest.exists() or dest.stat().st_size < 1000:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=300) as resp, open(dest, "wb") as out:
        while True:
            chunk = resp.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
print("zip size", dest.stat().st_size)
extract = OUT / "QuaterniusNature"
if not extract.exists():
    with zipfile.ZipFile(dest, "r") as zf:
        zf.extractall(extract)
print("extracted to", extract)
# list some fbx
fbx = list(extract.rglob("*.fbx")) + list(extract.rglob("*.FBX"))
print("fbx count", len(fbx))
for p in fbx[:20]:
    print(" ", p.relative_to(extract))
