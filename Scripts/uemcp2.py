# -*- coding: utf-8 -*-
"""Minimal unreal-mcp client that shells out to curl (urllib gets empty bodies
from this server's SSE transport).

    import uemcp2 as u
    u.init()
    print(u.call("get_actors_in_folder", {"folder_path": "06_Pavilion"}, "editor_toolset.toolsets.scene.SceneTools"))
"""
import json
import subprocess

BASE = "http://127.0.0.1:8000/mcp"
_sid = [None]
_uid = [0]


def _post(body):
    cmd = ["curl", "-s", "-X", "POST", BASE,
           "-H", "Content-Type: application/json",
           "-H", "Accept: application/json, text/event-stream"]
    if _sid[0]:
        cmd += ["-H", "Mcp-Session-Id: %s" % _sid[0]]
    cmd += ["-d", json.dumps(body)]
    raw = subprocess.run(cmd, capture_output=True, text=True, timeout=300).stdout
    for line in raw.splitlines():
        if line.startswith("data:"):
            return json.loads(line[5:].strip())
    return {}


def init():
    cmd = ["curl", "-s", "-D", "-", "-o", "/dev/null", "-X", "POST", BASE,
           "-H", "Content-Type: application/json",
           "-H", "Accept: application/json, text/event-stream",
           "-d", json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize",
                             "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                                        "clientInfo": {"name": "claude-code", "version": "1.0"}}})]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=60).stdout
    for line in out.splitlines():
        if line.lower().startswith("mcp-session-id:"):
            _sid[0] = line.split(":", 1)[1].strip()
    _post({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
    return _sid[0]


def call(tool, args=None, toolset=None):
    if not _sid[0]:
        init()
    _uid[0] += 1
    inner = {"tool_name": tool, "arguments": args or {}}
    if toolset:
        inner["toolset_name"] = toolset
    resp = _post({"jsonrpc": "2.0", "id": _uid[0], "method": "tools/call",
                  "params": {"name": "call_tool", "arguments": inner}})
    if "error" in resp:
        raise RuntimeError(json.dumps(resp["error"])[:400])
    return json.loads(resp["result"]["content"][0]["text"])


def scalar(tool, args=None, toolset=None):
    return call(tool, args, toolset)["returnValue"]
