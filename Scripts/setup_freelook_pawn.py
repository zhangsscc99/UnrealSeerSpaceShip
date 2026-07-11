# -*- coding: utf-8 -*-
import sys
sys.path.append(r"C:\Program Files\Epic Games\UE_5.8\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python")
from remote_execution import RemoteExecution, MODE_EXEC_FILE

SCRIPT = r'''
import unreal

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
editor_asset_lib = unreal.EditorAssetLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
utils = unreal.EditorLoadingAndSavingUtils
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

if not editor_asset_lib.does_directory_exist("/Game/Blueprints"):
    editor_asset_lib.make_directory("/Game/Blueprints")

def ensure_bp(asset_path, parent_class, name):
    if editor_asset_lib.does_asset_exist(asset_path):
        return unreal.load_asset(asset_path)
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", parent_class)
    return asset_tools.create_asset(name, "/Game/Blueprints", unreal.Blueprint, factory)

pawn_bp = ensure_bp("/Game/Blueprints/BP_FreeLookPawn", unreal.DefaultPawn, "BP_FreeLookPawn")
gm_bp = ensure_bp("/Game/Blueprints/BP_KloseGameMode", unreal.GameModeBase, "BP_KloseGameMode")

unreal.BlueprintEditorLibrary.compile_blueprint(pawn_bp)
pawn_cdo = unreal.get_default_object(pawn_bp.generated_class())
pawn_cdo.set_editor_property("bAddDefaultMovementBindings", True)

try:
    coll = pawn_cdo.get_editor_property("CollisionComponent")
    if coll:
        coll.set_sphere_radius(1.0, True)
        coll.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
except Exception as e:
    print("COLL_ERR:" + str(e))

try:
    mv = pawn_cdo.get_editor_property("MovementComponent")
    if mv:
        mv.set_editor_property("MaxSpeed", 2000.0)
        mv.set_editor_property("Acceleration", 8000.0)
        mv.set_editor_property("Deceleration", 8000.0)
except Exception as e:
    print("MOVE_ERR:" + str(e))

unreal.BlueprintEditorLibrary.compile_blueprint(pawn_bp)

unreal.BlueprintEditorLibrary.compile_blueprint(gm_bp)
gm_cdo = unreal.get_default_object(gm_bp.generated_class())
gm_cdo.set_editor_property("DefaultPawnClass", pawn_bp.generated_class())
pc_bp = unreal.load_asset("/Game/Blueprints/BP_KlosePlayerController") if editor_asset_lib.does_asset_exist("/Game/Blueprints/BP_KlosePlayerController") else None
if pc_bp:
    gm_cdo.set_editor_property("PlayerControllerClass", pc_bp.generated_class())
else:
    gm_cdo.set_editor_property("PlayerControllerClass", unreal.PlayerController.static_class())
unreal.BlueprintEditorLibrary.compile_blueprint(gm_bp)

ws = world.get_world_settings()
ws.set_editor_property("DefaultGameMode", gm_bp.generated_class())

for actor in eas.get_all_level_actors():
    if isinstance(actor, unreal.PlayerStart):
        actor.set_actor_location(unreal.Vector(0.0, -200.0, 600.0), False, True)
        actor.set_actor_rotation(unreal.Rotator(0.0, 0.0, 0.0), False)
        print("SPAWN:0,-200,600")

# Free-fly: disable collision on all scene meshes so camera never jams
for actor in eas.get_all_level_actors():
    if not isinstance(actor, unreal.StaticMeshActor):
        continue
    label = actor.get_actor_label()
    smc = actor.static_mesh_component
    if not smc:
        continue
    if label.startswith("Klose_"):
        smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        print("NOCOLL:" + label)

# Shrink oversized ground slightly and ensure spawn clear
for actor in eas.get_all_level_actors():
    if isinstance(actor, unreal.StaticMeshActor) and actor.get_actor_label() == "Klose_Ground":
        actor.set_actor_scale3d(unreal.Vector(10.0, 8.0, 0.2))
        actor.set_actor_location(unreal.Vector(0.0, -200.0, -20.0), False, True)
        print("GROUND resized")

editor_asset_lib.save_asset("/Game/Blueprints/BP_FreeLookPawn")
editor_asset_lib.save_asset("/Game/Blueprints/BP_KloseGameMode")
if pc_bp:
    editor_asset_lib.save_asset("/Game/Blueprints/BP_KlosePlayerController")
utils.save_dirty_packages(True, True)
utils.save_map(world, "/Game/Maps/MeshyAIShowcase")
print("OK")
print("PawnClass=" + str(gm_cdo.get_editor_property("DefaultPawnClass")))
print("GameMode=" + str(ws.get_editor_property("DefaultGameMode")))
'''

remote = RemoteExecution()
remote.start()
try:
    import time
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
