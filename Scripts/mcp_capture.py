# -*- coding: utf-8 -*-
"""Capture the UE level viewport to a PNG file via the unreal-mcp HTTP endpoint.

Usage:
  py Scripts/mcp_capture.py out.png
  py Scripts/mcp_capture.py out.png X Y Z PITCH YAW
"""
import base64
import json
import os
import sys
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000/mcp"
SESS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mcp_session.txt")
_sid = [None]
_uid = [0]


def _parse(raw):
    """Parse an SSE stream (or a plain JSON body) and return the last message."""
    if not raw.strip():
        return {}
    events, buf = [], []
    for line in raw.splitlines():
        if line.startswith("data:"):
            buf.append(line[5:].lstrip())
        elif not line.strip() and buf:
            events.append("\n".join(buf))
            buf = []
    if buf:
        events.append("\n".join(buf))
    for ev in reversed(events):
        try:
            return json.loads(ev)
        except Exception:
            continue
    return json.loads(raw)


def _post(payload, sid=None, want_sid=False):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(BASE, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json, text/event-stream")
    if sid:
        req.add_header("Mcp-Session-Id", sid)
    try:
        resp = urllib.request.urlopen(req, timeout=180)
        h = resp.headers.get("Mcp-Session-Id")
        raw = resp.read().decode()
    except urllib.error.HTTPError as e:
        h = e.headers.get("Mcp-Session-Id")
        raw = e.read().decode()
    body = _parse(raw)
    return (body, h) if want_sid else body


def _initialize():
    body, h = _post(
        {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "mcp_capture", "version": "1.0"},
            },
        },
        want_sid=True,
    )
    if not h:
        raise SystemExit("initialize failed: %s" % json.dumps(body)[:400])
    _sid[0] = h
    _post({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}, h)
    return h


def call(name, args, toolset=None):
    if _sid[0] is None:
        _initialize()
    _uid[0] += 1
    inner = {"tool_name": name, "arguments": args}
    if toolset:
        inner["toolset_name"] = toolset
    params = {"name": "call_tool", "arguments": inner}
    resp = _post({"jsonrpc": "2.0", "id": _uid[0], "method": "tools/call", "params": params}, _sid[0])
    if "error" in resp:
        raise SystemExit("tool error: %s" % json.dumps(resp["error"])[:400])
    return resp


def result_value(resp):
    res = resp["result"]
    if "structuredContent" in res:
        return res["structuredContent"]["returnValue"]
    return json.loads(res["content"][0]["text"])


def main():
    out = sys.argv[1]
    if len(sys.argv) >= 7:
        x, y, z, pitch, yaw = (float(v) for v in sys.argv[2:7])
        call("SetCameraTransform",
             {"transform": {"location": {"x": x, "y": y, "z": z},
                            "rotation": {"pitch": pitch, "yaw": yaw, "roll": 0.0}}},
             "EditorToolset.EditorAppToolset")
    cap = result_value(call("CaptureViewport", {"bShowUI": False},
                            "EditorToolset.EditorAppToolset"))
    with open(out, "wb") as f:
        f.write(base64.b64decode(cap["image"]["data"]))
    print("wrote", out, os.path.getsize(out), "bytes")
    print("camera", cap["cameraLocation"], cap["cameraRotation"])


if __name__ == "__main__":
    main()
