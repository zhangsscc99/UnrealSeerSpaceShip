#!/bin/bash
# Capture the UE level viewport to a PNG.
# usage: Scripts/mcp_cap.sh out.png [X Y Z PITCH YAW]
set -e
BASE="http://127.0.0.1:8000/mcp"
OUT="$1"; shift || true
RAW="${OUT%.png}.sse"

SID=$(curl -s -D - -o /dev/null -X POST "$BASE" \
  -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"claude-code","version":"1.0"}}}' \
  | grep -i '^Mcp-Session-Id:' | tr -d '\r' | awk '{print $2}')

call() {
  curl -s -X POST "$BASE" -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" -H "Mcp-Session-Id: $SID" -d "$1"
}

call '{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}' >/dev/null

if [ $# -ge 5 ]; then
  call "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/call\",\"params\":{\"name\":\"call_tool\",\"arguments\":{\"tool_name\":\"SetCameraTransform\",\"toolset_name\":\"EditorToolset.EditorAppToolset\",\"arguments\":{\"transform\":{\"location\":{\"x\":$1,\"y\":$2,\"z\":$3},\"rotation\":{\"pitch\":$4,\"yaw\":$5,\"roll\":0}}}}}}" >/dev/null
  SID=$(curl -s -D - -o /dev/null -X POST "$BASE" \
    -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
    -d '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"claude-code","version":"1.0"}}}' \
    | grep -i '^Mcp-Session-Id:' | tr -d '\r' | awk '{print $2}')
  call '{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}' >/dev/null
fi

call '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"call_tool","arguments":{"tool_name":"CaptureViewport","toolset_name":"EditorToolset.EditorAppToolset","arguments":{"bShowUI":false,"captureTransform":null,"annotations":null}}}}' > "$RAW"

py - "$RAW" "$OUT" <<'PY'
import base64, json, re, sys
raw = open(sys.argv[1], encoding="utf-8", errors="ignore").read()
m = re.search(r'^data: (.*)$', raw, re.M)
if not m:
    sys.exit("no data line in %s (head: %r)" % (sys.argv[1], raw[:200]))
msg = json.loads(m.group(1))
val = json.loads(msg["result"]["content"][0]["text"])["returnValue"]
open(sys.argv[2], "wb").write(base64.b64decode(val["image"]["data"]))
print("wrote", sys.argv[2], "camera", val["cameraLocation"])
PY
