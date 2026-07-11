import sys
sys.path.append(r"C:\Program Files\Epic Games\UE_5.8\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python")
from remote_execution import RemoteExecution, MODE_EXEC_FILE

SAVE_SCRIPT = r"""
import unreal

editor_asset_lib = unreal.EditorAssetLibrary
utils = unreal.EditorLoadingAndSavingUtils
subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
world = subsystem.get_editor_world()
level_path = '/Game/Maps/MeshyAIShowcase'

if not editor_asset_lib.does_directory_exist('/Game/Maps'):
    editor_asset_lib.make_directory('/Game/Maps')

utils.save_map(world, level_path)
utils.save_dirty_packages(True, True)
print('SAVED:' + level_path)
"""

remote = RemoteExecution()
remote.start()
try:
    import time
    for _ in range(20):
        nodes = remote.remote_nodes
        if nodes:
            break
        time.sleep(0.5)
    if not nodes:
        raise RuntimeError('No Unreal Editor Python remote node found. Enable Python remote execution in editor settings.')
    remote.open_command_connection(nodes[0]['node_id'])
    result = remote.run_command(SAVE_SCRIPT, exec_mode=MODE_EXEC_FILE, raise_on_failure=True)
    print(result)
finally:
    remote.stop()
