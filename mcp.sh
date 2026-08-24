#!/bin/bash
BASE="http://127.0.0.1:8000/mcp"
SESS="mcp_session.txt"

mcp_post() {
  local body="$1"; local out="${TMP:-/tmp}/mcp_out_$$.json"
  if [ -s "$SESS" ]; then
    curl -s -X POST "$BASE" -H "Content-Type: application/json" \
      -H "Accept: application/json, text/event-stream" \
      -H "Mcp-Session-Id: $(cat "$SESS")" \
      -d "$body" -o "$out"
  else
    curl -s -D "$out.hdr" -X POST "$BASE" -H "Content-Type: application/json" \
      -H "Accept: application/json, text/event-stream" \
      -d "$body" -o "$out"
    local sid; sid=$(grep -i '^Mcp-Session-Id:' "$out.hdr" | tr -d '\r' | awk '{print $2}')
    if [ -n "$sid" ] && [ "$sid" != "-" ]; then echo "$sid" > "$SESS"; fi
  fi
  cat "$out"; rm -f "$out" "$out.hdr"
}

mcp_init() {
  [ -s "$SESS" ] && return 0
  mcp_post '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"claude-code","version":"1.0"}}}' >/dev/null
  mcp_post '{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}' >/dev/null
}

mcp_toolsets() {
  mcp_post '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"list_toolsets","arguments":{}}}'
}

mcp_describe() {
  local ts="$1"
  local arg=$(py -c "import json,sys;print(json.dumps({'toolset_name':sys.argv[1]}))" "$ts")
  mcp_post "{\"jsonrpc\":\"2.0\",\"id\":3,\"method\":\"tools/call\",\"params\":{\"name\":\"describe_toolset\",\"arguments\":$arg}}"
}

mcp_call() {
  local tool="$1"; local ts="$2"; local args="${3:-{}}"
  local argjson
  if [ -n "$ts" ]; then
    argjson=$(py -c "import json,sys;d=json.loads(sys.argv[1]);d['toolset_name']=sys.argv[2];print(json.dumps(d))" "$args" "$ts")
  else
    argjson="$args"
  fi
  mcp_post "{\"jsonrpc\":\"2.0\",\"id\":4,\"method\":\"tools/call\",\"params\":{\"name\":\"$tool\",\"arguments\":$argjson}}"
}
