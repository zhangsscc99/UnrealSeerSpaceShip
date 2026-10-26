"""Call Unreal MCP tools over HTTP when the MCP client in the session is disconnected.

The editor exposes a streamable-HTTP MCP endpoint at 127.0.0.1:8000/mcp.
This client does the initialize handshake, caches the session id, and calls one tool.

Usage:
    python uemcp_http.py list_toolsets
    python uemcp_http.py <tool_name> '<json arguments>'
    python uemcp_http.py --raw <tool_name> '<json arguments>'   # print the raw JSON-RPC envelope
"""

import http.client
import json
import pathlib
import sys

URL = "http://127.0.0.1:8000/mcp"
SESSION_FILE = pathlib.Path(__file__).with_name(".uemcp_session")
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}


def _post(payload, session=None):
    """POST directly via http.client: urllib honours HTTP_PROXY, which breaks loopback."""
    data = json.dumps(payload).encode("utf-8")
    headers = dict(HEADERS)
    if session:
        headers["Mcp-Session-Id"] = session
    conn = http.client.HTTPConnection("127.0.0.1", 8000, timeout=600)
    try:
        conn.request("POST", "/mcp", body=data, headers=headers)
        resp = conn.getresponse()
        body = resp.read().decode("utf-8", "replace")
        return resp.getheader("Mcp-Session-Id") or session, body
    finally:
        conn.close()


def _parse(body):
    body = body.strip()
    if not body:
        return None
    if body.startswith("event:") or body.startswith("data:"):
        for line in body.splitlines():
            if line.startswith("data:"):
                return json.loads(line[5:].strip())
        return None
    return json.loads(body)


def open_session():
    sid, body = _post({
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                   "clientInfo": {"name": "uemcp-http", "version": "0"}},
    })
    SESSION_FILE.write_text(sid or "")
    _post({"jsonrpc": "2.0", "method": "notifications/initialized"}, sid)
    return sid


def session():
    if SESSION_FILE.exists():
        sid = SESSION_FILE.read_text().strip()
        if sid:
            return sid
    return open_session()


def call(tool, arguments=None):
    """`<toolset>.<tool_name>` is routed through the call_tool dispatcher."""
    if "." in tool:
        toolset, tool_name = tool.rsplit(".", 1)
        tool = "call_tool"
        arguments = {"toolset_name": toolset, "tool_name": tool_name,
                     "arguments": arguments or {}}
    payload = {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
               "params": {"name": tool, "arguments": arguments or {}}}
    sid = session()
    _, body = _post(payload, sid)
    msg = _parse(body)
    if msg is None:
        sid = open_session()
        _, body = _post(payload, sid)
        msg = _parse(body)
    if "error" in msg:
        raise RuntimeError(msg["error"])
    return msg.get("result", {})


def main():
    argv = sys.argv[1:]
    raw = False
    if argv and argv[0] == "--raw":
        raw = True
        argv = argv[1:]
    if not argv:
        print(__doc__)
        return
    tool = argv[0]
    args = json.loads(argv[1]) if len(argv) > 1 else {}
    result = call(tool, args)
    print(json.dumps(result if raw else result.get("content", result), ensure_ascii=False)[:6000])


if __name__ == "__main__":
    main()
