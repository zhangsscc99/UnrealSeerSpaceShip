# -*- coding: utf-8 -*-
import sys
sys.path.append(r"C:\Program Files\Epic Games\UE_5.8\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python")
from remote_execution import RemoteExecution, MODE_EXEC_FILE

SCRIPT = r'''
import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
rows = []
for actor in eas.get_all_level_actors():
    label = actor.get_actor_label()
    cls = actor.get_class().get_name()
    loc = actor.get_actor_location()
    try:
        origin, extent = actor.get_actor_bounds(False)
        minz = origin.z - extent.z
        maxz = origin.z + extent.z
        sx = extent.x * 2
        sy = extent.y * 2
        sz = extent.z * 2
    except Exception:
        minz = maxz = sx = sy = sz = 0.0
    rows.append((label, cls, loc.x, loc.y, loc.z, minz, maxz, sx, sy, sz))

rows.sort(key=lambda r: r[0])
print("LABEL|CLASS|LX|LY|LZ|MINZ|MAXZ|SIZEX|SIZEY|SIZEZ")
for r in rows:
    print("%s|%s|%.0f|%.0f|%.0f|%.0f|%.0f|%.0f|%.0f|%.0f" % r)
print("TOTAL_ACTORS:%d" % len(rows))
'''

remote = RemoteExecution()
remote.start()
try:
    import time
    for _ in range(30):
        if remote.remote_nodes:
            break
        time.sleep(0.5)
    if not remote.remote_nodes:
        raise RuntimeError("No UE Python remote node")
    remote.open_command_connection(remote.remote_nodes[0]["node_id"])
    result = remote.run_command(SCRIPT, exec_mode=MODE_EXEC_FILE, raise_on_failure=True)
    out = result.get("output", []) if isinstance(result, dict) else []
    for line in out:
        print(line.get("output", "") if isinstance(line, dict) else line)
finally:
    remote.stop()
