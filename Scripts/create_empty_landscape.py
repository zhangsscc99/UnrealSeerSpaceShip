# -*- coding: utf-8 -*-
"""Replace Klose_Ground static mesh with a flat empty Landscape in MeshyAIShowcase."""
import sys
import time

sys.path.append(
    r"C:\Program Files\Epic Games\UE_5.8\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python"
)
from remote_execution import RemoteExecution, MODE_EXEC_FILE

SCRIPT = r'''
import unreal

MAP_PATH = "/Game/Maps/MeshyAIShowcase"
utils = unreal.EditorLoadingAndSavingUtils
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not utils.load_map(MAP_PATH):
    raise RuntimeError("Failed to load map: " + MAP_PATH)

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

removed = []
for actor in list(eas.get_all_level_actors()):
    label = actor.get_actor_label()
    if label == "Klose_Ground":
        eas.destroy_actor(actor)
        removed.append(label)

# Default flat landscape: 4x4 components, 63 quads/section, 1 section/component
component_count_x = 4
component_count_y = 4
quads_per_section = 63
sections_per_component = 1
quads_per_component = quads_per_section * sections_per_component
size_x = component_count_x * quads_per_component + 1
size_y = component_count_y * quads_per_component + 1
flat_height = 32768
height_data = [flat_height] * (size_x * size_y)

landscape_location = unreal.Vector(-12600.0, -13800.0, 0.0)
landscape_rotation = unreal.Rotator(0.0, 0.0, 0.0)
landscape_scale = unreal.Vector(100.0, 100.0, 100.0)

landscape = eas.spawn_actor_from_class(unreal.Landscape.static_class(), landscape_location, landscape_rotation)
landscape.set_actor_label("Klose_Landscape")
landscape.set_actor_scale3d(landscape_scale)

layer_guid = unreal.Guid.new_guid()
heightmap_per_layer = {layer_guid: height_data}
material_layers = {layer_guid: []}

landscape.import(
    layer_guid,
    0,
    0,
    size_x - 1,
    size_y - 1,
    sections_per_component,
    quads_per_section,
    heightmap_per_layer,
    "",
    material_layers,
    unreal.LandscapeImportAlphamapType.LAYER_DEFINITION,
    [],
)

landscape.set_actor_location(unreal.Vector(-12600.0, -13800.0, 0.0), False, False)
landscape.register_all_components()

# Try Sensei landscape material if present
material_candidates = [
    "/Game/Landscape/Materials/M_Landscape",
    "/Game/Landscape/M_Landscape",
    "/Game/Landscape/Materials/MI_Landscape",
]
for mat_path in material_candidates:
    mat = unreal.load_asset(mat_path)
    if mat:
        landscape.set_editor_property("landscape_material", mat)
        break

utils.save_dirty_packages(True, True)
utils.save_map(world, MAP_PATH)

print("REMOVED:" + ",".join(removed))
print("LANDSCAPE:" + landscape.get_actor_label())
print("SIZE:" + str(size_x) + "x" + str(size_y))
print("LOCATION:" + str(landscape.get_actor_location()))
'''

remote = RemoteExecution()
remote.start()
try:
    for _ in range(120):
        if remote.remote_nodes:
            break
        time.sleep(1.0)
    if not remote.remote_nodes:
        raise RuntimeError(
            "No UE Python remote node. Open Unreal Editor with this project and enable Python remote execution."
        )
    remote.open_command_connection(remote.remote_nodes[0]["node_id"])
    result = remote.run_command(SCRIPT, exec_mode=MODE_EXEC_FILE, raise_on_failure=True)
    print(result)
finally:
    remote.stop()
