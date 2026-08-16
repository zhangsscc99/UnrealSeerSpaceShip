# -*- coding: utf-8 -*-
"""Import Kenney + Poly Haven rocks and scatter a natural boulder field in MeshyAIShowcase."""

from __future__ import annotations

import sys
import time

sys.path.append(
    r"C:\Program Files\Epic Games\UE_5.8\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python"
)
from remote_execution import RemoteExecution, MODE_EXEC_FILE

SCRIPT = r'''
import glob
import math
import os
import random
import unreal

LEVEL_PATH = "/Game/Maps/MeshyAIShowcase"
FOLDER = "RockScatter"
PROJECT_CONTENT = unreal.Paths.project_content_dir()

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
utils = unreal.EditorLoadingAndSavingUtils
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()

RNG = random.Random(42)


def folder(actor):
    try:
        actor.set_folder_path(FOLDER)
    except Exception:
        pass


def import_fbx(source_file, content_folder, asset_name):
    dest_asset = f"{content_folder}/{asset_name}"
    existing = unreal.load_asset(dest_asset)
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
    options.static_mesh_import_data.combine_meshes = False
    options.static_mesh_import_data.generate_lightmap_u_vs = True
    options.static_mesh_import_data.auto_generate_collision = True

    task = unreal.AssetImportTask()
    task.filename = source_file.replace("\\", "/")
    task.destination_path = content_folder
    task.destination_name = asset_name
    task.replace_existing = True
    task.automated = True
    task.save = False
    task.factory = unreal.FbxFactory()
    task.options = options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    imported = []
    for path in task.get_editor_property("imported_object_paths"):
        obj = unreal.load_asset(str(path))
        if obj:
            imported.append(obj)
    if not imported:
        raise RuntimeError("Import failed: " + source_file)
    return imported[0] if len(imported) == 1 else imported


def collect_fbx_files(root_rel, name_filter=None):
    root_abs = os.path.join(PROJECT_CONTENT, root_rel.replace("/Game/", "").replace("Game/", ""))
    pattern = os.path.join(root_abs, "**", "*.fbx")
    files = []
    for path in glob.glob(pattern, recursive=True):
        base = os.path.basename(path)
        if name_filter and name_filter(base) is False:
            continue
        files.append(path)
    return sorted(set(files))


def ensure_rock_meshes():
    content_root = "/Game/ThirdParty/Rocks"
    meshes = []

    kenney_root = os.path.join(PROJECT_CONTENT, "ThirdParty", "KenneyNatureKit", "FBX")
    if os.path.isdir(kenney_root):
        for fname in sorted(os.listdir(kenney_root)):
            lower = fname.lower()
            if not lower.endswith(".fbx"):
                continue
            if "rock" not in lower and "cliff" not in lower:
                continue
            asset_name = os.path.splitext(fname)[0]
            mesh = import_fbx(
                os.path.join(kenney_root, fname),
                f"{content_root}/Kenney",
                asset_name,
            )
            if isinstance(mesh, list):
                meshes.extend(mesh)
            else:
                meshes.append(mesh)

    poly_root = os.path.join(PROJECT_CONTENT, "ThirdParty", "PolyHaven", "Rocks")
    if os.path.isdir(poly_root):
        for asset_dir in sorted(os.listdir(poly_root)):
            dir_abs = os.path.join(poly_root, asset_dir)
            if not os.path.isdir(dir_abs):
                continue
            for fname in sorted(os.listdir(dir_abs)):
                if not fname.lower().endswith(".fbx"):
                    continue
                asset_name = os.path.splitext(fname)[0]
                mesh = import_fbx(
                    os.path.join(dir_abs, fname),
                    f"{content_root}/PolyHaven/{asset_dir}",
                    asset_name,
                )
                if isinstance(mesh, list):
                    meshes.extend(mesh)
                else:
                    meshes.append(mesh)

    filter_obj = unreal.ARFilter(
        class_names=["StaticMesh"],
        package_paths=["/Game/Megascans"],
        recursive_paths=True,
    )
    for data in asset_registry.get_assets(filter_obj):
        path = str(data.package_name)
        if "Rock" in path or "rock" in path:
            obj = unreal.load_asset(path)
            if obj:
                meshes.append(obj)

    unique = []
    seen = set()
    for mesh in meshes:
        name = mesh.get_name()
        if name in seen:
            continue
        seen.add(name)
        unique.append(mesh)
    if not unique:
        raise RuntimeError("No rock meshes found to scatter.")
    return unique


def mesh_weight(mesh_name):
    lower = mesh_name.lower()
    if any(k in lower for k in ("small", "flat", "stone", "pebble")):
        return ("small", 0.45, 1.15, 0.08)
    if any(k in lower for k in ("tall", "large", "boulder", "cliff")):
        return ("large", 1.2, 2.8, 0.18)
    if "moss_set" in lower or "namaqualand" in lower or "set" in lower:
        return ("cluster", 0.9, 1.8, 0.14)
    return ("medium", 0.7, 1.6, 0.12)


def clear_old_rocks():
    removed = 0
    kill_labels = (
        "Wall", "Stump", "Cliff", "Rock_", "Scene_Side_Wall",
        "Scene_Back_Cliff", "Scene_Back_Buttress", "Klose_Wall", "Klose_Cliff",
    )
    for actor in list(eas.get_all_level_actors()):
        if not isinstance(actor, unreal.StaticMeshActor):
            continue
        label = actor.get_actor_label()
        if label.startswith("Scatter_"):
            eas.destroy_actor(actor)
            removed += 1
            continue
        if any(token in label for token in kill_labels):
            eas.destroy_actor(actor)
            removed += 1
    return removed


def sample_point(min_x, max_x, min_y, max_y):
    return RNG.uniform(min_x, max_x), RNG.uniform(min_y, max_y)


def too_close(x, y, placed, min_dist):
    for px, py, _ in placed:
        dx = x - px
        dy = y - py
        if dx * dx + dy * dy < min_dist * min_dist:
            return True
    return False


def scatter_field(meshes):
    zones = [
        {"name": "NorthField", "x": (-1200, 1200), "y": (400, 1700), "count": 42, "min_dist": 110},
        {"name": "WestSlope", "x": (-2100, -700), "y": (-400, 1200), "count": 28, "min_dist": 95},
        {"name": "EastSlope", "x": (700, 2100), "y": (-500, 1100), "count": 28, "min_dist": 95},
        {"name": "SouthForeground", "x": (-900, 900), "y": (-1400, -500), "count": 34, "min_dist": 85},
        {"name": "GateFlanks", "x": (-500, 500), "y": (900, 1400), "count": 18, "min_dist": 70},
    ]

    placed = []
    actors = []

    for zone in zones:
        attempts = 0
        max_attempts = zone["count"] * 40
        while len([p for p in placed if p[2] == zone["name"]]) < zone["count"] and attempts < max_attempts:
            attempts += 1
            mesh = RNG.choice(meshes)
            category, s_min, s_max, sink = mesh_weight(mesh.get_name())
            x, y = sample_point(zone["x"][0], zone["x"][1], zone["y"][0], zone["y"][1])

            # denser clusters near zone center
            cx = (zone["x"][0] + zone["x"][1]) * 0.5
            cy = (zone["y"][0] + zone["y"][1]) * 0.5
            if RNG.random() < 0.35:
                x = cx + RNG.uniform(-0.25, 0.25) * (zone["x"][1] - zone["x"][0])
                y = cy + RNG.uniform(-0.25, 0.25) * (zone["y"][1] - zone["y"][0])

            if too_close(x, y, placed, zone["min_dist"]):
                continue

            scale = RNG.uniform(s_min, s_max)
            if category == "small":
                z = RNG.uniform(-8, 18)
            elif category == "large":
                z = RNG.uniform(-20, 35)
            else:
                z = RNG.uniform(-12, 24)
            z -= sink * scale * 100.0

            yaw = RNG.uniform(0.0, 360.0)
            pitch = RNG.uniform(-8.0, 8.0)
            roll = RNG.uniform(-12.0, 12.0)
            sx = scale * RNG.uniform(0.85, 1.15)
            sy = scale * RNG.uniform(0.85, 1.15)
            sz = scale * RNG.uniform(0.75, 1.05)

            actor = eas.spawn_actor_from_object(
                mesh,
                unreal.Vector(x, y, z),
                unreal.Rotator(pitch, yaw, roll),
            )
            label = "Scatter_%s_%02d" % (zone["name"], len(actors))
            actor.set_actor_label(label)
            actor.set_actor_scale3d(unreal.Vector(sx, sy, sz))
            folder(actor)
            placed.append((x, y, zone["name"]))
            actors.append(actor)

    return actors


removed = clear_old_rocks()
meshes = ensure_rock_meshes()
placed = scatter_field(meshes)

utils.save_dirty_packages(True, True)
utils.save_map(world, LEVEL_PATH)
print("ROCKS_REMOVED:%d" % removed)
print("ROCKS_MESHES:%d" % len(meshes))
print("ROCKS_PLACED:%d" % len(placed))
print("ROCKS_SAVED:%s" % LEVEL_PATH)
'''

remote = RemoteExecution()
remote.start()
try:
    for _ in range(30):
        if remote.remote_nodes:
            break
        time.sleep(0.5)
    if not remote.remote_nodes:
        raise RuntimeError(
            "No Unreal Editor Python remote node found. Open the project in UE and enable remote execution."
        )

    remote.open_command_connection(remote.remote_nodes[0]["node_id"])
    result = remote.run_command(SCRIPT, exec_mode=MODE_EXEC_FILE, raise_on_failure=True)
    print(result)
finally:
    remote.stop()
