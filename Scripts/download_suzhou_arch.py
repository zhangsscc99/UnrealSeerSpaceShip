# -*- coding: utf-8 -*-
"""Download free Chinese garden architecture packs."""
from __future__ import annotations

import os
import ssl
import urllib.request
import zipfile

ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "Content",
    "ThirdParty",
    "ChineseGarden",
)
ARCH = os.path.join(ROOT, "Architecture")
os.makedirs(ARCH, exist_ok=True)

CTX = ssl.create_default_context()
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def download(url: str, dest: str) -> None:
    if os.path.isfile(dest) and os.path.getsize(dest) > 1000:
        print("exists", dest, os.path.getsize(dest))
        return
    print("GET", url)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, context=CTX, timeout=180) as r, open(dest, "wb") as f:
        while True:
            chunk = r.read(1024 * 256)
            if not chunk:
                break
            f.write(chunk)
    print("OK", dest, os.path.getsize(dest))


def unzip(path: str, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    with zipfile.ZipFile(path, "r") as z:
        z.extractall(out_dir)
    print("unzipped", path, "->", out_dir)


def main() -> None:
    # OpenGameArt Structure set (CC0) — pavilions, walkways, tower
    oga = (
        "https://opengameart.org/sites/default/files/"
        "structureset_fbx_gltf_blend_textures.zip"
    )
    oga_zip = os.path.join(ARCH, "structureset_fbx_gltf_blend_textures.zip")
    try:
        download(oga, oga_zip)
        unzip(oga_zip, os.path.join(ARCH, "StructureSet"))
    except Exception as e:
        print("OGA fail", e)
        # alternate CDN mirrors sometimes differ
        try:
            download(
                "https://opengameart.org/sites/default/files/structureset_godot.zip",
                os.path.join(ARCH, "structureset_godot.zip"),
            )
            unzip(
                os.path.join(ARCH, "structureset_godot.zip"),
                os.path.join(ARCH, "StructureSetGodot"),
            )
        except Exception as e2:
            print("OGA godot fail", e2)

    # Poly Haven extra plants via API
    import json

    def api(url: str):
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, context=CTX, timeout=60) as r:
            return json.loads(r.read().decode("utf-8"))

    models_dir = os.path.join(ROOT, "Models")
    os.makedirs(models_dir, exist_ok=True)
    for mid in [
        "potted_plant_01",
        "potted_plant_02",
        "bamboo_medium_yh",
        "ivy_01",
        "bush_01",
        "plant_pot_01",
    ]:
        try:
            files = api(f"https://api.polyhaven.com/files/{mid}")
        except Exception as e:
            print(mid, "meta", e)
            continue
        fbx = files.get("fbx", {})
        picked = None
        for res in ("1k", "2k"):
            if res in fbx and "fbx" in fbx[res]:
                size = fbx[res]["fbx"].get("size", 0)
                if size and size < 45_000_000:
                    picked = (res, fbx[res]["fbx"]["url"], size)
                    break
        if not picked:
            print(mid, "no small fbx", list(fbx.keys()))
            continue
        res, url, size = picked
        dest_dir = os.path.join(models_dir, mid)
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, f"{mid}_{res}.fbx")
        print(mid, res, size)
        try:
            download(url, dest)
            # includes
            includes = fbx[res]["fbx"].get("include") or {}
            for rel, info in includes.items():
                out = os.path.join(dest_dir, rel.replace("/", os.sep))
                os.makedirs(os.path.dirname(out), exist_ok=True)
                download(info["url"], out)
        except Exception as e:
            print(mid, "dl fail", e)


if __name__ == "__main__":
    main()
