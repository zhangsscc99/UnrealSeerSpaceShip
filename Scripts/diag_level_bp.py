# -*- coding: utf-8 -*-
import sys, time
sys.path.append(r"C:\Program Files\Epic Games\UE_5.8\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python")
from remote_execution import RemoteExecution, MODE_EXEC_FILE

SCRIPT = r'''
import unreal

out = []

# 1) Level blueprint of current map
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
try:
    levels = world.get_levels()
    for lvl in levels:
        lsb = None
        try:
            lsb = unreal.LevelStreaming.get_level_script_blueprint(lvl)
        except Exception:
            pass
        if lsb is None:
            continue
        graphs = unreal.BlueprintEditorLibrary.get_all_graphs(lsb) if hasattr(unreal.BlueprintEditorLibrary, "get_all_graphs") else []
        out.append("LSB:" + lsb.get_path_name() + " graphs=" + str(len(graphs)))
        for g in graphs:
            try:
                nodes = g.get_nodes() if hasattr(g, "get_nodes") else []
                out.append("  GRAPH:" + g.get_name() + " nodes=" + str(len(nodes)))
                for n in nodes[:60]:
                    out.append("    NODE:" + n.get_class().get_name() + " | " + n.get_name())
            except Exception as e:
                out.append("  GRAPH_ERR:" + str(e))
except Exception as e:
    out.append("LSB_ERR:" + str(e))

# 2) Check all project blueprints for input-mode / widget nodes
reg = unreal.AssetRegistryHelpers.get_asset_registry()
paths = ["/Game/Blueprints"]
assets = reg.get_assets_by_path(unreal.Name("/Game/Blueprints"), True)
for ad in assets:
    try:
        bp = ad.get_asset()
        if not isinstance(bp, unreal.Blueprint):
            continue
        graphs = bp.get_editor_property("ubergraph_pages") + bp.get_editor_property("function_graphs")
        for g in graphs:
            for n in g.get_nodes():
                cn = n.get_class().get_name()
                if "CallFunction" in cn:
                    try:
                        fn = n.get_editor_property("function_reference")
                        fname = ""
                        try:
                            fname = str(fn.get_editor_property("member_name"))
                        except Exception:
                            pass
                        if any(k in fname.lower() for k in ["inputmode", "input_mode", "widget", "ignore", "cursor", "showmouse"]):
                            out.append("BP_NODE:" + bp.get_path_name() + " -> " + fname)
                    except Exception:
                        pass
    except Exception as e:
        out.append("BP_ERR:" + str(e))

print("\n".join(out) if out else "NOTHING_FOUND")
'''

remote = RemoteExecution()
remote.start()
try:
    for _ in range(30):
        if remote.remote_nodes:
            break
        time.sleep(0.5)
    if not remote.remote_nodes:
        raise RuntimeError("No UE Python remote node")
    remote.open_command_connection(remote.remote_nodes[0]["node_id"])
    print(remote.run_command(SCRIPT, exec_mode=MODE_EXEC_FILE, raise_on_failure=True))
finally:
    remote.stop()
