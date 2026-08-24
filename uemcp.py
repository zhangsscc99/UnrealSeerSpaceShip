import json, sys, urllib.request, urllib.error, re, os

BASE = "http://127.0.0.1:8000/mcp"
SESS = "mcp_session.txt"

def _post(payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(BASE, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json, text/event-stream")
    sid = None
    if os.path.exists(SESS):
        sid = open(SESS).read().strip()
        if sid:
            req.add_header("Mcp-Session-Id", sid)
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        h = resp.headers.get("Mcp-Session-Id")
        if h and sid != h:
            open(SESS, "w").write(h)
        raw = resp.read().decode()
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
    return _parse(raw)

def _parse(raw):
    # SSE stream: extract data: lines
    objs = []
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            js = line[5:].strip()
            try:
                objs.append(json.loads(js))
            except Exception:
                pass
    if objs:
        return objs[-1]
    # plain JSON fallback
    try:
        return json.loads(raw)
    except Exception:
        return {"raw": raw}

def rpc(method, params):
    global _uid
    _uid[0] += 1
    payload = {"jsonrpc":"2.0","id":_uid[0],"method":method,"params":params}
    return _post(payload)

def call(name, args=None, toolset=None):
    arguments = args or {}
    params = {"name": name, "arguments": arguments}
    if toolset:
        params["toolset_name"] = toolset
    return rpc("tools/call", params)

def list_toolsets():
    return call("list_toolsets")

def describe(name):
    return call("describe_toolset", {"toolset_name": name})

_uid = [100]

def text(result):
    content = result.get("result", {}).get("content", [])
    out = []
    for c in content:
        if isinstance(c, dict):
            if c.get("type") == "text":
                out.append(c.get("text",""))
            elif "text" in c:
                out.append(c.get("text",""))
    return "\n".join(out)

def main():
    if len(sys.argv) < 2:
        print("usage: uemcp list_toolsets | describe <ts> | call <tool> [jsonargs] [--toolset ts]")
        sys.exit(1)
    if sys.argv[1] == "list_toolsets":
        print(text(list_toolsets()))
    elif sys.argv[1] == "describe":
        print(text(describe(sys.argv[2])))
    elif sys.argv[1] == "call":
        tool = sys.argv[2]
        ts = None
        args = {}
        for i, a in enumerate(sys.argv[3:]):
            if a == "--toolset":
                ts = sys.argv[i+3]
        # parse json args (first non-flag arg)
        for a in sys.argv[3:]:
            if not a.startswith("--") and a != ts:
                args = json.loads(a)
        print(text(call(tool, args, ts)))

if __name__ == "__main__":
    main()
