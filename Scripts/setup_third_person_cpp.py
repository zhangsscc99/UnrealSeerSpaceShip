# -*- coding: utf-8 -*-
"""Apply C++ third-person defaults: spawn point + world GameMode override."""
import sys
import time

sys.path.append(
    r"C:\Program Files\Epic Games\UE_5.8\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python"
)
from remote_execution import RemoteExecution, MODE_EXEC_FILE

SCRIPT = r'''
import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
utils = unreal.EditorLoadingAndSavingUtils
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

gm_class = unreal.load_class(None, "/Script/UnrealSeerSpaceShip.KloseGameMode")
if gm_class:
    ws = world.get_world_settings()
    ws.set_editor_property("DefaultGameMode", gm_class)
    print("GM=" + str(gm_class))
else:
    print("GM_CLASS_NOT_FOUND: compile C++ first")

for actor in eas.get_all_level_actors():
    if isinstance(actor, unreal.PlayerStart):
        actor.set_actor_location(unreal.Vector(0.0, -200.0, 120.0), False, True)
        actor.set_actor_rotation(unreal.Rotator(0.0, 0.0, 0.0), False)
        print("SPAWN:0,-200,120")

utils.save_dirty_packages(True, True)
utils.save_map(world, "/Game/Maps/MeshyAIShowcase")
print("OK")
'''

remote = RemoteExecution()
remote.start()
try:
    for _ in range(20):
        if remote.remote_nodes:
            break
        time.sleep(0.5)
    if not remote.remote_nodes:
        raise RuntimeError("No UE Python remote node")
    remote.open_command_connection(remote.remote_nodes[0]["node_id"])
    print(remote.run_command(SCRIPT, exec_mode=MODE_EXEC_FILE, raise_on_failure=True))
finally:
    remote.stop()
