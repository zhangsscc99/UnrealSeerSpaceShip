# -*- coding: utf-8 -*-
import sys
import time

sys.path.append(
    r"C:\Program Files\Epic Games\UE_5.8\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python"
)
from remote_execution import RemoteExecution, MODE_EXEC_FILE

SCRIPT = r'''
import unreal
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
editor_asset_lib = unreal.EditorAssetLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
utils = unreal.EditorLoadingAndSavingUtils
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

# 1) Recreate BP_FreeLookPawn as SpectatorPawn child (has camera that follows controller)
pawn_path = "/Game/Blueprints/BP_FreeLookPawn"
if editor_asset_lib.does_asset_exist(pawn_path):
    editor_asset_lib.delete_asset(pawn_path)

factory = unreal.BlueprintFactory()
factory.set_editor_property("parent_class", unreal.SpectatorPawn)
pawn_bp = asset_tools.create_asset("BP_FreeLookPawn", "/Game/Blueprints", unreal.Blueprint, factory)
unreal.BlueprintEditorLibrary.compile_blueprint(pawn_bp)
pawn_cdo = unreal.get_default_object(pawn_bp.generated_class())
pawn_cdo.set_editor_property("bUseControllerRotationYaw", True)
pawn_cdo.set_editor_property("bUseControllerRotationPitch", True)
pawn_cdo.set_editor_property("bAddDefaultMovementBindings", True)
unreal.BlueprintEditorLibrary.compile_blueprint(pawn_bp)
print("PAWN=SpectatorPawn")

# 2) GameMode uses this pawn + plain PlayerController (no custom camera manager)
gm_bp = unreal.load_asset("/Game/Blueprints/BP_KloseGameMode")
unreal.BlueprintEditorLibrary.compile_blueprint(gm_bp)
gm_cdo = unreal.get_default_object(gm_bp.generated_class())
gm_cdo.set_editor_property("DefaultPawnClass", pawn_bp.generated_class())
# Use default PlayerController - no custom CameraManager
gm_cdo.set_editor_property("PlayerControllerClass", unreal.PlayerController.static_class())
unreal.BlueprintEditorLibrary.compile_blueprint(gm_bp)
print("GM_PC=default")

# 3) World settings
ws = world.get_world_settings()
ws.set_editor_property("DefaultGameMode", gm_bp.generated_class())

# 4) Spawn point
for actor in eas.get_all_level_actors():
    if isinstance(actor, unreal.PlayerStart):
        actor.set_actor_location(unreal.Vector(0, -200, 600), False, True)
        actor.set_actor_rotation(unreal.Rotator(0, 0, 0), False)

editor_asset_lib.save_asset(pawn_path)
editor_asset_lib.save_asset("/Game/Blueprints/BP_KloseGameMode")
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
