# -*- coding: utf-8 -*-
"""Download free CC0 assets for a Suzhou-style Chinese garden scene."""
from __future__ import annotations

import json
import os
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Content" / "ThirdParty" / "ChineseGarden"
HEADERS = {"User-Agent": "UnrealSeerSpaceShip-AssetDownloader/1.0"}
RES = "1k"

# Photogrammetry / nature models (Poly Haven CC0)
MODELS = [
    "fir_tree_01",
    "fir_sapling_medium",
    "island_tree_01",
    "island_tree_02",
    "fern_02",
    "grass_medium_01",
    "grass_bermuda_01",
    "boulder_01",
    "rock_moss_set_01",
    "rock_moss_set_02",
    "namaqualand_boulder_03",
    "namaqualand_boulder_05",
    "coast_rocks_02",
    "dead_tree_trunk",
]

# Garden-appropriate PBR textures (Poly Haven CC0)
TEXTURES = [
    "grey_plaster",
    "white_plaster_rough_01",
    "clay_roof_tiles",
    "clay_roof_tiles_02",
    "grey_roof_tiles",
    "cobblestone_floor_03",
    "monastery_stone_floor",
    "stony_dirt_path",
    "dark_wood",
    "wood_planks",
    "mossy_cobblestone",
    "park_dirt",
]

HDRIS = ["chinese_garden"]


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def download(url: str, dest: Path, retries: int = 3) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  skip {dest.name}")
        return
    last = None
    for i in range(1, retries + 1):
        try:
            print(f"  get {dest.name} ({i})")
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=300) as resp, open(dest, "wb") as out:
                while True:
                    chunk = resp.read(1024 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)
            if dest.stat().st_size > 0:
                return
        except Exception as exc:
            last = exc
            if dest.exists():
                dest.unlink(missing_ok=True)
    raise RuntimeError(f"Failed {url}: {last}")


def download_model(asset_id: str) -> None:
    files = fetch_json(f"https://api.polyhaven.com/files/{asset_id}")
    fbx = files.get("fbx", {}).get(RES, {}).get("fbx")
    if not fbx:
        # some plants only have blend/gltf
        gltf = files.get("gltf", {}).get(RES, {}).get("gltf")
        if not gltf:
            print(f"  no fbx/gltf for {asset_id}")
            return
        dest_dir = OUT / "Models" / asset_id
        download(gltf["url"], dest_dir / f"{asset_id}_{RES}.gltf")
        for rel, info in gltf.get("include", {}).items():
            download(info["url"], dest_dir / rel.replace("/", os.sep))
        print(f"ok gltf: {asset_id}")
        return
    dest_dir = OUT / "Models" / asset_id
    download(fbx["url"], dest_dir / f"{asset_id}_{RES}.fbx")
    for rel, info in fbx.get("include", {}).items():
        download(info["url"], dest_dir / rel.replace("/", os.sep))
    print(f"ok model: {asset_id}")


def download_texture(asset_id: str) -> None:
    files = fetch_json(f"https://api.polyhaven.com/files/{asset_id}")
    dest_dir = OUT / "Textures" / asset_id
    # Prefer jpg diffuse + nor_gl + rough
    for map_name in ("Diffuse", "nor_gl", "Rough", "AO", "arm"):
        entry = files.get(map_name, {}).get(RES)
        if not entry:
            continue
        # pick jpg/png/exr
        for ext in ("jpg", "png", "exr"):
            if ext in entry:
                download(entry[ext]["url"], dest_dir / f"{asset_id}_{map_name.lower()}_{RES}.{ext}")
                break
    print(f"ok tex: {asset_id}")


def download_hdri(asset_id: str) -> None:
    files = fetch_json(f"https://api.polyhaven.com/files/{asset_id}")
    dest_dir = OUT / "HDRI" / asset_id
    # 2k hdr for sky
    hdr = files.get("hdri", {}).get("2k", {}).get("hdr")
    if hdr:
        download(hdr["url"], dest_dir / f"{asset_id}_2k.hdr")
    tone = files.get("tonemapped", {})
    # tonemapped may be direct
    if isinstance(tone, dict):
        for key, info in tone.items():
            if isinstance(info, dict) and "url" in info:
                download(info["url"], dest_dir / f"{asset_id}_tonemapped.jpg")
                break
    print(f"ok hdri: {asset_id}")


def download_itch_pavilion() -> None:
    """Best-effort: itch CC0 pavilion via known CDN pattern; skip if blocked."""
    dest = OUT / "Architecture" / "FourCornerPavilion.zip"
    urls = [
        # itch often needs login; try direct github mirrors / alternatives below
    ]
    # Alternative CC0 lowpoly Asian pavilion from Poly Pizza CDN patterns are auth-gated.
    # Use a public GitHub raw if available later.
    print("itch pavilion: manual/auth often required; using Poly Haven + Kenney fallbacks")


def download_kenney_nature_extra() -> None:
    # Already on disk usually; ensure trees if nature kit zip exists online
    url = "https://kenney.nl/media/pages/assets/nature-kit/0a2bafead4-1677579506/kenney_nature-kit.zip"
    dest = OUT / "KenneyNatureKit.zip"
    try:
        download(url, dest)
        extract_to = OUT / "KenneyNature"
        if not extract_to.exists():
            with zipfile.ZipFile(dest, "r") as zf:
                zf.extractall(extract_to)
            print(f"ok kenney extract -> {extract_to}")
    except Exception as exc:
        print(f"kenney download skipped: {exc}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("=== HDRI ===")
    for a in HDRIS:
        try:
            download_hdri(a)
        except Exception as e:
            print(f"HDRI fail {a}: {e}")
    print("=== MODELS ===")
    for a in MODELS:
        try:
            download_model(a)
        except Exception as e:
            print(f"MODEL fail {a}: {e}")
    print("=== TEXTURES ===")
    for a in TEXTURES:
        try:
            download_texture(a)
        except Exception as e:
            print(f"TEX fail {a}: {e}")
    print("=== KENNEY ===")
    download_kenney_nature_extra()
    print("Done ->", OUT)


if __name__ == "__main__":
    main()
