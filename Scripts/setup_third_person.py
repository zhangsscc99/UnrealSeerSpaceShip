# -*- coding: utf-8 -*-
"""Configure third-person Character (BP_KloseExplorer) + GameMode + spawn."""
import sys
import time

sys.path.append(
    r"C:\Program Files\Epic Games\UE_5.8\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python"
)
from remote_execution import RemoteExecution, MODE_EXEC_FILE

SCRIPT = r'''
import unreal

editor_asset_lib = unreal.EditorAssetLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
utils = unreal.EditorLoadingAndSavingUtils
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

char_path = "/Game/Blueprints/BP_KloseExplorer"
gm_path = "/Game/Blueprints/BP_KloseGameMode"
pc_path = "/Game/Blueprints/BP_KlosePlayerController"

char_bp = unreal.load_asset(char_path)
gm_bp = unreal.load_asset(gm_path)
pc_bp = unreal.load_asset(pc_path) if editor_asset_lib.does_asset_exist(pc_path) else None

unreal.BlueprintEditorLibrary.compile_blueprint(char_bp)
char_cdo = unreal.get_default_object(char_bp.generated_class())

# Third-person rotation: body follows movement, camera follows controller
char_cdo.set_editor_property("bUseControllerRotationYaw", False)
char_cdo.set_editor_property("bUseControllerRotationPitch", False)
char_cdo.set_editor_property("bUseControllerRotationRoll", False)

move = char_cdo.get_editor_property("CharacterMovement")
if move:
    move.set_editor_property("bOrientRotationToMovement", True)
    move.set_editor_property("RotationRate", unreal.Rotator(0.0, 540.0, 0.0))
    move.set_editor_property("MaxWalkSpeed", 600.0)
    move.set_editor_property("JumpZVelocity", 600.0)
    move.set_editor_property("AirControl", 0.35)
    move.set_editor_property("GravityScale", 1.0)
    move.set_editor_property("MaxAcceleration", 2048.0)
    move.set_editor_property("BrakingDecelerationWalking", 2048.0)

capsule = char_cdo.get_editor_property("CapsuleComponent")
if capsule:
    capsule.set_editor_property("CapsuleHalfHeight", 88.0)
    capsule.set_editor_property("CapsuleRadius", 42.0)

unreal.BlueprintEditorLibrary.compile_blueprint(char_bp)

# GameMode -> third-person character
unreal.BlueprintEditorLibrary.compile_blueprint(gm_bp)
gm_cdo = unreal.get_default_object(gm_bp.generated_class())
gm_cdo.set_editor_property("DefaultPawnClass", char_bp.generated_class())
if pc_bp:
    gm_cdo.set_editor_property("PlayerControllerClass", pc_bp.generated_class())
unreal.BlueprintEditorLibrary.compile_blueprint(gm_bp)

ws = world.get_world_settings()
ws.set_editor_property("DefaultGameMode", gm_bp.generated_class())

# Spawn on ground center (Klose_Ground is near y=-200, z=-20)
for actor in eas.get_all_level_actors():
    if isinstance(actor, unreal.PlayerStart):
        actor.set_actor_location(unreal.Vector(0.0, -200.0, 120.0), False, True)
        actor.set_actor_rotation(unreal.Rotator(0.0, 0.0, 0.0), False)
        print("SPAWN:0,-200,120")

editor_asset_lib.save_asset(char_path)
editor_asset_lib.save_asset(gm_path)
if pc_bp:
    editor_asset_lib.save_asset(pc_path)
utils.save_dirty_packages(True, True)
utils.save_map(world, "/Game/Maps/MeshyAIShowcase")

print("OK")
print("PawnClass=" + str(gm_cdo.get_editor_property("DefaultPawnClass")))
'''

remote = RemoteExecution()
remote.start()
try:
    for _ in range(20):
        if remote.remote_nodes:
            break
        time.sleep(0.5)
    if not remote.remote_nodes:
        raise RuntimeError("No UE Python remote node. Enable Remote Execution in UE editor.")
    remote.open_command_connection(remote.remote_nodes[0]["node_id"])
    print(remote.run_command(SCRIPT, exec_mode=MODE_EXEC_FILE, raise_on_failure=True))
finally:
    remote.stop()
