# Run inside Unreal Editor via -ExecutePythonScript
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

component_count_x = 4
component_count_y = 4
quads_per_section = 63
sections_per_component = 1
quads_per_component = quads_per_section * sections_per_component
size_x = component_count_x * quads_per_component + 1
size_y = component_count_y * quads_per_component + 1
height_data = [32768] * (size_x * size_y)

landscape = eas.spawn_actor_from_class(
    unreal.Landscape.static_class(),
    unreal.Vector(-12600.0, -13800.0, 0.0),
    unreal.Rotator(0.0, 0.0, 0.0),
)
landscape.set_actor_label("Klose_Landscape")
landscape.set_actor_scale3d(unreal.Vector(100.0, 100.0, 100.0))

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

landscape.register_all_components()

for mat_path in (
    "/Game/Landscape/Materials/M_Landscape",
    "/Game/Landscape/M_Landscape",
):
    mat = unreal.load_asset(mat_path)
    if mat:
        landscape.set_editor_property("landscape_material", mat)
        break

utils.save_dirty_packages(True, True)
utils.save_map(world, MAP_PATH)

unreal.log("REMOVED=" + ",".join(removed))
unreal.log("LANDSCAPE=" + landscape.get_actor_label())
unreal.log("SIZE=" + str(size_x) + "x" + str(size_y))
