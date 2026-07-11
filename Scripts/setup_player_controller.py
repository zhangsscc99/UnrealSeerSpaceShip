# -*- coding: utf-8 -*-
import sys, time
sys.path.append(r"C:\Program Files\Epic Games\UE_5.8\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python")
from remote_execution import RemoteExecution, MODE_EXEC_FILE

SCRIPT = r'''
import unreal

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
editor_asset_lib = unreal.EditorAssetLibrary

pc_path = "/Game/Blueprints/BP_KlosePlayerController"
if not editor_asset_lib.does_asset_exist(pc_path):
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", unreal.PlayerController)
    asset_tools.create_asset("BP_KlosePlayerController", "/Game/Blueprints", unreal.Blueprint, factory)

pc_bp = unreal.load_asset(pc_path)
unreal.BlueprintEditorLibrary.compile_blueprint(pc_bp)
pc_cdo = unreal.get_default_object(pc_bp.generated_class())
pc_cdo.set_editor_property("bShowMouseCursor", False)
pc_cdo.set_editor_property("bEnableClickEvents", False)
pc_cdo.set_editor_property("bEnableMouseOverEvents", False)
unreal.BlueprintEditorLibrary.compile_blueprint(pc_bp)

gm_bp = unreal.load_asset("/Game/Blueprints/BP_KloseGameMode")
gm_cdo = unreal.get_default_object(gm_bp.generated_class())
gm_cdo.set_editor_property("PlayerControllerClass", pc_bp.generated_class())
unreal.BlueprintEditorLibrary.compile_blueprint(gm_bp)

editor_asset_lib.save_asset(pc_path)
editor_asset_lib.save_asset("/Game/Blueprints/BP_KloseGameMode")
print("PC_OK")
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
