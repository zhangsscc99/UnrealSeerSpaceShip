"""Minimal client for the MCP-for-Blender addon socket.

Lets Blender be driven without the MCP tools being loaded in the session:
the addon listens on 127.0.0.1:9876 and speaks one JSON object per request,
one JSON object back (no trailing newline).

Usage:
    python blender_bridge.py ping
    python blender_bridge.py scene
    python blender_bridge.py exec "import bpy; print(len(bpy.data.objects))"
    python blender_bridge.py exec -f some_script.py
    python blender_bridge.py shot out.png [--size 1200]
"""

import argparse
import json
import pathlib
import socket
import sys

HOST, PORT = "127.0.0.1", 9876


def call(payload, timeout=180):
    with socket.create_connection((HOST, PORT), timeout=timeout) as s:
        s.sendall(json.dumps(payload).encode("utf-8"))
        buf = b""
        while True:
            chunk = s.recv(65536)
            if not chunk:
                raise SystemExit("connection closed before a full response")
            buf += chunk
            try:
                return json.loads(buf.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("ping")
    sub.add_parser("scene")
    sub.add_parser("addon")

    ex = sub.add_parser("exec")
    ex.add_argument("code", nargs="?")
    ex.add_argument("-f", "--file")

    sh = sub.add_parser("shot")
    sh.add_argument("path")
    sh.add_argument("--size", type=int, default=1200)

    shots = sub.add_parser("world")
    shots.add_argument("--objects", type=int, default=0)

    a = p.parse_args()

    if a.cmd == "ping":
        payload = {"type": "ping"}
    elif a.cmd == "scene":
        payload = {"type": "get_scene_info", "params": {}}
    elif a.cmd == "addon":
        payload = {"type": "get_addon_info", "params": {}}
    elif a.cmd == "world":
        payload = {"type": "get_world_state_snapshot", "params": {}}
    elif a.cmd == "exec":
        if a.file:
            code = pathlib.Path(a.file).read_text(encoding="utf-8")
        elif a.code:
            code = a.code
        else:
            code = sys.stdin.read()
        payload = {"type": "execute_code", "params": {"code": code}}
    else:  # shot
        payload = {
            "type": "get_viewport_screenshot",
            "params": {"filepath": str(pathlib.Path(a.path).resolve()), "max_size": a.size},
        }

    resp = call(payload)
    if a.cmd == "shot":
        print(json.dumps(resp, ensure_ascii=False))
        return
    print(json.dumps(resp, ensure_ascii=False, indent=2)[:4000])
    if resp.get("status") == "error":
        sys.exit(1)


if __name__ == "__main__":
    main()
