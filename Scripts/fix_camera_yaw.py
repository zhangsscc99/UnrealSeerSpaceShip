# -*- coding: utf-8 -*-
import sys
import time

sys.path.append(
    r"C:\Program Files\Epic Games\UE_5.8\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python"
)
from remote_execution import RemoteExecution, MODE_EXEC_FILE

SCRIPT = r'''
import unreal
editor_asset_lib = unreal.EditorAssetLibrary
utils = unreal.EditorLoadingAndSavingUtils

# 1) Fix CameraManager: yaw -180..180 (span exactly 360 => engine skips limiting)
cm = unreal.load_asset("/Game/Blueprints/BP_KloseCameraManager")
unreal.BlueprintEditorLibrary.compile_blueprint(cm)
cm_cdo = unreal.get_default_object(cm.generated_class())
cm_cdo.set_editor_property("ViewYawMin", -180.0)
cm_cdo.set_editor_property("ViewYawMax", 180.0)
cm_cdo.set_editor_property("ViewPitchMin", -89.9)
cm_cdo.set_editor_property("ViewPitchMax", 89.9)
unreal.BlueprintEditorLibrary.compile_blueprint(cm)
print("CM_Yaw=" + str(cm_cdo.get_editor_property("ViewYawMin")) + ".." + str(cm_cdo.get_editor_property("ViewYawMax")))

# 2) Fix Pawn: follow controller yaw so camera actually rotates with mouse
pawn = unreal.load_asset("/Game/Blueprints/BP_FreeLookPawn")
unreal.BlueprintEditorLibrary.compile_blueprint(pawn)
pawn_cdo = unreal.get_default_object(pawn.generated_class())
pawn_cdo.set_editor_property("bUseControllerRotationYaw", True)
pawn_cdo.set_editor_property("bUseControllerRotationPitch", True)
pawn_cdo.set_editor_property("bUseControllerRotationRoll", False)
pawn_cdo.set_editor_property("bAddDefaultMovementBindings", True)
unreal.BlueprintEditorLibrary.compile_blueprint(pawn)
print("Pawn_UseCtrlYaw=" + str(pawn_cdo.get_editor_property("bUseControllerRotationYaw")))

# 3) Save
editor_asset_lib.save_asset("/Game/Blueprints/BP_KloseCameraManager")
editor_asset_lib.save_asset("/Game/Blueprints/BP_FreeLookPawn")
editor_asset_lib.save_asset("/Game/Blueprints/BP_KlosePlayerController")
utils.save_dirty_packages(True, True)
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
