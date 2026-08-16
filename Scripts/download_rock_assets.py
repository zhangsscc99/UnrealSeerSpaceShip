# -*- coding: utf-8 -*-
"""Download CC0 rock assets from Poly Haven into Content/ThirdParty/PolyHaven."""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = PROJECT_ROOT / "Content" / "ThirdParty" / "PolyHaven" / "Rocks"
RESOLUTION = "1k"

# Volumetric boulders / stone blocks (not thin rock sheets).
ASSETS = [
    "rock_moss_set_01",
    "rock_moss_set_02",
    "rock_07",
    "rock_09",
    "stone_01",
    "namaqualand_stones_01",
    "boulder_01",
    "namaqualand_boulder_02",
    "namaqualand_boulder_03",
    "namaqualand_boulder_04",
    "namaqualand_boulder_05",
    "namaqualand_boulders_01",
    # Extra volumetric blocks / clusters (no thin wall sheets)
    "rock_boulder_spires_02",
    "rock_collection_02",
    "rock_collection_03",
    "rock_04",
    "rock_05",
    "rock_08",
    "coast_sand_rocks_02",
]


HEADERS = {"User-Agent": "UnrealSeerSpaceShip-AssetDownloader/1.0"}


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def download_file(url: str, dest: Path, retries: int = 3) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  skip (exists): {dest.name}")
        return
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            print(f"  download: {dest.name} (attempt {attempt})")
            request = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(request, timeout=300) as response, open(dest, "wb") as out:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)
            if dest.stat().st_size > 0:
                return
        except Exception as exc:
            last_error = exc
            if dest.exists():
                dest.unlink(missing_ok=True)
    raise RuntimeError(f"Failed to download {url}: {last_error}")


def download_asset(asset_id: str) -> None:
    files = fetch_json(f"https://api.polyhaven.com/files/{asset_id}")
    fbx_entry = files.get("fbx", {}).get(RESOLUTION, {}).get("fbx")
    if not fbx_entry:
        raise RuntimeError(f"No FBX at {RESOLUTION} for {asset_id}")

    asset_dir = OUTPUT_ROOT / asset_id
    asset_dir.mkdir(parents=True, exist_ok=True)

    main_name = f"{asset_id}_{RESOLUTION}.fbx"
    download_file(fbx_entry["url"], asset_dir / main_name)

    for rel_path, info in fbx_entry.get("include", {}).items():
        download_file(info["url"], asset_dir / rel_path.replace("/", os.sep))

    print(f"ok: {asset_id} -> {asset_dir}")


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    for asset_id in ASSETS:
        print(f"\n[{asset_id}]")
        download_asset(asset_id)
    print(f"\nDone. Assets saved under {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
