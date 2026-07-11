import sys
sys.path.append(r"C:\Program Files\Epic Games\UE_5.8\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python")
from remote_execution import RemoteExecution, MODE_EXEC_FILE

IMPORT_SCRIPT = r"""
import os
import unreal

project_content = os.path.join(unreal.Paths.project_content_dir(), 'MeshyAI')
utils = unreal.EditorLoadingAndSavingUtils
subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
world = subsystem.get_editor_world()

def import_fbx(folder_name):
    folder_abs = os.path.join(project_content, folder_name)
    fbx_files = [f for f in os.listdir(folder_abs) if f.lower().endswith('.fbx')]
    if not fbx_files:
        raise RuntimeError(f'No fbx in {folder_abs}')
    fbx_name = fbx_files[0]
    asset_name = os.path.splitext(fbx_name)[0]
    source_file = os.path.join(folder_abs, fbx_name)
    content_folder = f'/Game/MeshyAI/{folder_name}'
    if unreal.EditorAssetLibrary.does_directory_exist(f'{content_folder}/{asset_name}'):
        return unreal.load_asset(f'{content_folder}/{asset_name}')
    options = unreal.FbxImportUI()
    options.automated_import_should_detect_type = False
    options.import_mesh = True
    options.import_as_skeletal = False
    options.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
    options.original_import_type = unreal.FBXImportType.FBXIT_STATIC_MESH
    options.import_materials = True
    options.import_textures = True
    options.import_animations = False
    options.static_mesh_import_data.combine_meshes = True
    task = unreal.AssetImportTask()
    task.filename = source_file
    task.destination_path = content_folder
    task.destination_name = asset_name
    task.replace_existing = False
    task.automated = True
    task.save = False
    task.factory = unreal.FbxFactory()
    task.options = options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    paths = list(task.get_editor_property('imported_object_paths'))
    if not paths:
        raise RuntimeError(f'Import failed: {source_file}')
    return unreal.load_asset(paths[0])

folders = sorted([d for d in os.listdir(project_content) if d.endswith('_texture_fbx') and any(x in d for x in ['0710144353','0710144344','0710144151'])])
placed = []
spacing = 400.0
start_x = 800.0
start_y = 800.0
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for i, folder_name in enumerate(folders):
    mesh = import_fbx(folder_name)
    loc = unreal.Vector(start_x + (i * spacing), start_y, 0)
    actor = eas.spawn_actor_from_object(mesh, loc, unreal.Rotator(0, 0, 0))
    actor.set_actor_label(os.path.basename(folder_name))
    placed.append(folder_name)

utils.save_dirty_packages(True, True)
utils.save_map(world, '/Game/Maps/MeshyAIShowcase')
print('IMPORTED:' + ','.join(placed))
"""

remote = RemoteExecution()
remote.start()
try:
    import time
    for _ in range(20):
        if remote.remote_nodes:
            break
        time.sleep(0.5)
    if not remote.remote_nodes:
        raise RuntimeError('No UE Python remote node found')
    remote.open_command_connection(remote.remote_nodes[0]['node_id'])
    result = remote.run_command(IMPORT_SCRIPT, exec_mode=MODE_EXEC_FILE, raise_on_failure=True)
    print(result)
finally:
    remote.stop()
