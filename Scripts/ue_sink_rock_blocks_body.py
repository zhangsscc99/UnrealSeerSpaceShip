# Body executed inside Unreal Editor Python (via init_unreal flag watcher).
import math
import os
import unreal

LEVEL = "/Game/Maps/MeshyAIShowcase"
FOLDER = "RockBlocks"
CENTER_X = 0.0
CENTER_Y = -350.0
CONTENT = unreal.Paths.project_content_dir()
DEST_ROOT = "/Game/ThirdParty/RockBlocks"

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
utils = unreal.EditorLoadingAndSavingUtils
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()


def folder(actor):
    try:
        actor.set_folder_path(FOLDER)
    except Exception:
        pass


def import_fbx(source_file, dest_folder, asset_name):
    dest_path = dest_folder + "/" + asset_name
    existing = unreal.load_asset(dest_path)
    if existing:
        return existing
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
    task.filename = source_file.replace("\\", "/")
    task.destination_path = dest_folder
    task.destination_name = asset_name
    task.replace_existing = True
    task.automated = True
    task.save = True
    task.factory = unreal.FbxFactory()
    task.options = options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    paths = list(task.get_editor_property("imported_object_paths") or [])
    for p in paths:
        obj = unreal.load_asset(str(p))
        if isinstance(obj, unreal.StaticMesh):
            return obj
    return unreal.load_asset(dest_path)


def collect_block_meshes():
    meshes = []
    poly_root = os.path.join(CONTENT, "ThirdParty", "PolyHaven", "Rocks")
    if os.path.isdir(poly_root):
        for asset_dir in sorted(os.listdir(poly_root)):
            dir_abs = os.path.join(poly_root, asset_dir)
            if not os.path.isdir(dir_abs):
                continue
            for fname in sorted(os.listdir(dir_abs)):
                if not fname.lower().endswith(".fbx"):
                    continue
                lower = fname.lower()
                if "face" in lower or "cliff" in lower:
                    continue
                mesh = import_fbx(
                    os.path.join(dir_abs, fname),
                    DEST_ROOT + "/PolyHaven/" + asset_dir,
                    os.path.splitext(fname)[0],
                )
                if mesh:
                    meshes.append(mesh)

    kenney = os.path.join(CONTENT, "ThirdParty", "KenneyNatureKit", "FBX")
    if os.path.isdir(kenney):
        for fname in sorted(os.listdir(kenney)):
            lower = fname.lower()
            if not lower.endswith(".fbx"):
                continue
            if not (
                lower.startswith("rock_large")
                or lower.startswith("rock_tall")
                or lower.startswith("rock_small")
            ):
                continue
            mesh = import_fbx(
                os.path.join(kenney, fname),
                DEST_ROOT + "/Kenney",
                os.path.splitext(fname)[0],
            )
            if mesh:
                meshes.append(mesh)

    unique = []
    seen = set()
    for m in meshes:
        name = m.get_path_name()
        if name in seen:
            continue
        seen.add(name)
        unique.append(m)
    if not unique:
        raise RuntimeError("No volumetric rock meshes imported")
    return unique


def clear_sheet_junk():
    removed = 0
    prefixes = (
        "Ring_Wall",
        "Ring_WallThick",
        "Ring_Base",
        "Ring_Blend",
        "Ring_Berm",
        "Ring_Debris",
        "Ring_Scatter",
        "Ring_Block",
        "Scatter_",
    )
    for actor in list(eas.get_all_level_actors()):
        if not isinstance(actor, unreal.StaticMeshActor):
            continue
        label = actor.get_actor_label()
        if any(label.startswith(p) for p in prefixes):
            eas.destroy_actor(actor)
            removed += 1
    return removed


def place_sunk(mesh, label, x, y, yaw, scale, bury_ratio=0.35):
    actor = eas.spawn_actor_from_object(
        mesh, unreal.Vector(x, y, 800.0), unreal.Rotator(0, yaw, 0)
    )
    actor.set_actor_label(label)
    actor.set_actor_scale3d(unreal.Vector(scale, scale * 0.95, scale * 0.9))
    folder(actor)
    origin, extent = actor.get_actor_bounds(False)
    height = max(extent.z * 2.0, 50.0)
    z = -height * bury_ratio
    actor.set_actor_location(unreal.Vector(x, y, z), False, True)
    return actor


removed = clear_sheet_junk()
meshes = collect_block_meshes()
placed = []

count = 48
a = 5800.0
b = 4300.0
for i in range(count):
    deg = i * (360.0 / count)
    rad = math.radians(deg)
    wobble = 1.0 + 0.04 * math.sin(rad * 3.0)
    x = CENTER_X + math.cos(rad) * a * wobble
    y = CENTER_Y + math.sin(rad) * b * wobble
    yaw = deg + 90.0 + (i % 5 - 2) * 8.0
    mesh = meshes[i % len(meshes)]
    path = mesh.get_path_name().lower()
    name = mesh.get_name().lower()
    if "kenney" in path:
        scale = 18.0 + (i % 5) * 3.0
        if "small" in name:
            scale *= 0.55
        elif "tall" in name:
            scale *= 1.15
    else:
        scale = 2.2 + (i % 4) * 0.45
    bury = 0.40 + (i % 3) * 0.05
    placed.append(
        place_sunk(mesh, "Ring_Block_%02d" % i, x, y, yaw, scale, bury).get_actor_label()
    )

inner = 60
for i in range(inner):
    deg = i * (360.0 / inner) + 3.0
    rad = math.radians(deg)
    x = CENTER_X + math.cos(rad) * 4900.0
    y = CENTER_Y + math.sin(rad) * 3600.0
    yaw = deg + 70.0
    mesh = meshes[(i * 3) % len(meshes)]
    path = mesh.get_path_name().lower()
    scale = 8.0 + (i % 4) * 1.5 if "kenney" in path else 1.1 + (i % 5) * 0.25
    placed.append(
        place_sunk(mesh, "Ring_BlockInner_%02d" % i, x, y, yaw, scale, 0.5).get_actor_label()
    )

outer = 24
for i in range(outer):
    deg = i * (360.0 / outer) + 7.0
    rad = math.radians(deg)
    x = CENTER_X + math.cos(rad) * 6800.0
    y = CENTER_Y + math.sin(rad) * 5100.0
    yaw = deg + 90.0
    mesh = meshes[(i * 5) % len(meshes)]
    path = mesh.get_path_name().lower()
    scale = 12.0 if "kenney" in path else 1.6
    placed.append(
        place_sunk(mesh, "Ring_BlockOuter_%02d" % i, x, y, yaw, scale, 0.45).get_actor_label()
    )

utils.save_dirty_packages(True, True)
utils.save_map(world, LEVEL)
unreal.log("BLOCK_REMOVED:%d" % removed)
unreal.log("BLOCK_MESHES:%d" % len(meshes))
unreal.log("BLOCK_PLACED:%d" % len(placed))
