# -*- coding: utf-8 -*-
"""Import Kenney rock FBX into /Game/ThirdParty/Rocks/Kenney for richer rock variety."""

from __future__ import annotations

import os
import sys
import time

sys.path.append(
    r"C:\Program Files\Epic Games\UE_5.8\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python"
)
from remote_execution import RemoteExecution, MODE_EXEC_FILE

SCRIPT = r'''
import os
import unreal

content = unreal.Paths.project_content_dir()
kenney_fbx = os.path.join(content, "ThirdParty", "KenneyNatureKit", "FBX")
dest = "/Game/ThirdParty/Rocks/Kenney"
imported = []

if not os.path.isdir(kenney_fbx):
    raise RuntimeError("Missing Kenney FBX folder: " + kenney_fbx)

files = sorted(
    f for f in os.listdir(kenney_fbx)
    if f.lower().endswith(".fbx") and ("rock" in f.lower() or "cliff" in f.lower())
)

for fname in files:
    asset_name = os.path.splitext(fname)[0]
    dest_path = dest + "/" + asset_name
    if unreal.EditorAssetLibrary.does_asset_exist(dest_path):
        imported.append(dest_path)
        continue
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
    options.static_mesh_import_data.auto_generate_collision = True
    task = unreal.AssetImportTask()
    task.filename = os.path.join(kenney_fbx, fname).replace("\\", "/")
    task.destination_path = dest
    task.destination_name = asset_name
    task.replace_existing = False
    task.automated = True
    task.save = True
    task.factory = unreal.FbxFactory()
    task.options = options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    for path in task.get_editor_property("imported_object_paths"):
        imported.append(str(path))

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
print("KENNEY_IMPORTED:%d" % len(imported))
'''

remote = RemoteExecution()
remote.start()
try:
    for _ in range(20):
        if remote.remote_nodes:
            break
        time.sleep(0.5)
    if not remote.remote_nodes:
        raise RuntimeError("NO_REMOTE")
    remote.open_command_connection(remote.remote_nodes[0]["node_id"])
    print(remote.run_command(SCRIPT, exec_mode=MODE_EXEC_FILE, raise_on_failure=True))
finally:
    remote.stop()
