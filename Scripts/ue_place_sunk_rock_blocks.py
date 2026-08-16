# -*- coding: utf-8 -*-
"""Place already-imported volumetric RockBlocks, deeply sunk into ground, then SAVE.

Run inside UE Output Log / Cmd:
  py "exec(open(r'C:/Users/admin/Desktop/UnrealSeerSpaceShip/Scripts/ue_place_sunk_rock_blocks.py', encoding='utf-8').read())"
"""
import math
import unreal

LEVEL = "/Game/Maps/MeshyAIShowcase"
FOLDER = "RockBlocks"
CENTER_X = 0.0
CENTER_Y = -350.0
ROOT = "/Game/ThirdParty/RockBlocks"

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
utils = unreal.EditorLoadingAndSavingUtils
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
registry = unreal.AssetRegistryHelpers.get_asset_registry()


def folder(actor):
    try:
        actor.set_folder_path(FOLDER)
    except Exception:
        pass


def collect_meshes():
    meshes = []
    # Prefer mesh assets that look volumetric (skip materials/textures by class filter).
    assets = registry.get_assets_by_path(ROOT, recursive=True)
    skip_bits = (
        "_diff_",
        "_nor_",
        "_rough_",
        "_mask",
        "defaultmat",
        "dirt",
        "grass",
        "flat",
    )
    for data in assets:
        if str(data.asset_class_path.asset_name) != "StaticMesh":
            continue
        name = str(data.asset_name)
        lower = name.lower()
        path = data.package_name
        full = "%s.%s" % (path, name)
        if any(b in lower for b in skip_bits):
            continue
        # Prefer named mesh packages over accidental material wrappers.
        mesh = unreal.load_asset(full)
        if not isinstance(mesh, unreal.StaticMesh):
            continue
        meshes.append(mesh)

    # Stable preference: Poly Haven boulders first, then Kenney large/tall.
    def rank(m):
        p = m.get_path_name().lower()
        n = m.get_name().lower()
        score = 0
        if "boulder" in n or "boulder" in p:
            score += 100
        if "moss_set" in n or "stones" in n or "stone_01" in n:
            score += 80
        if "rock_0" in n:
            score += 70
        if "/kenney/" in p or n.startswith("rock_large"):
            score += 50
        if "rock_tall" in n:
            score += 40
        if "rock_small" in n:
            score += 10
        return -score

    meshes = sorted(set(meshes), key=rank)
    if not meshes:
        raise RuntimeError("No RockBlocks StaticMeshes found under " + ROOT)
    unreal.log("PLACE_MESHES:%d" % len(meshes))
    for m in meshes[:12]:
        unreal.log("  mesh: " + m.get_path_name())
    return meshes


def clear_junk():
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
        "Ring_BlockInner",
        "Ring_BlockOuter",
        "Scatter_",
        "RockBlock_",
    )
    for actor in list(eas.get_all_level_actors()):
        if not isinstance(actor, unreal.StaticMeshActor):
            continue
        label = actor.get_actor_label()
        if any(label.startswith(p) for p in prefixes):
            eas.destroy_actor(actor)
            removed += 1
    return removed


def place_sunk(mesh, label, x, y, yaw, sx, sy, sz, bury_ratio):
    actor = eas.spawn_actor_from_object(
        mesh, unreal.Vector(x, y, 1200.0), unreal.Rotator(0.0, yaw, 0.0)
    )
    actor.set_actor_label(label)
    actor.set_actor_scale3d(unreal.Vector(sx, sy, sz))
    folder(actor)
    origin, extent = actor.get_actor_bounds(False)
    height = max(float(extent.z) * 2.0, 80.0)
    # Sink so a large fraction sits underground; contact reads natural.
    z = -height * bury_ratio
    actor.set_actor_location(unreal.Vector(x, y, z), False, True)
    return actor


removed = clear_junk()
meshes = collect_meshes()
placed = []

# Outer rim — large sunk blocks
count = 56
a = 5600.0
b = 4100.0
for i in range(count):
    deg = i * (360.0 / count)
    rad = math.radians(deg)
    wobble = 1.0 + 0.05 * math.sin(rad * 2.5 + i * 0.1)
    x = CENTER_X + math.cos(rad) * a * wobble
    y = CENTER_Y + math.sin(rad) * b * wobble
    yaw = deg + 90.0 + ((i * 17) % 9 - 4) * 7.0
    mesh = meshes[i % len(meshes)]
    path = mesh.get_path_name().lower()
    name = mesh.get_name().lower()
    if "kenney" in path or name.startswith("rock_"):
        s = 22.0 + (i % 6) * 3.5
        if "small" in name:
            s *= 0.45
        elif "tall" in name:
            s *= 1.2
        elif "large" in name:
            s *= 1.05
    else:
        # Photogrammetry rocks: keep chunky, bury deep
        s = 2.6 + (i % 5) * 0.55
    bury = 0.42 + (i % 4) * 0.06
    sx = s * (0.95 + (i % 3) * 0.04)
    sy = s * (0.9 + (i % 4) * 0.04)
    sz = s * (0.85 + (i % 3) * 0.05)
    placed.append(
        place_sunk(mesh, "Ring_Block_%02d" % i, x, y, yaw, sx, sy, sz, bury).get_actor_label()
    )

# Inner denser rubble — smaller, more buried
inner = 72
for i in range(inner):
    deg = i * (360.0 / inner) + 2.5
    rad = math.radians(deg)
    x = CENTER_X + math.cos(rad) * (4700.0 + (i % 5) * 40.0)
    y = CENTER_Y + math.sin(rad) * (3450.0 + (i % 5) * 30.0)
    yaw = deg + 55.0 + (i % 7) * 5.0
    mesh = meshes[(i * 3 + 1) % len(meshes)]
    path = mesh.get_path_name().lower()
    name = mesh.get_name().lower()
    if "kenney" in path or name.startswith("rock_"):
        s = 9.0 + (i % 5) * 1.8
        if "small" in name:
            s *= 0.55
    else:
        s = 1.2 + (i % 6) * 0.28
    bury = 0.52 + (i % 3) * 0.05
    placed.append(
        place_sunk(
            mesh, "Ring_BlockInner_%02d" % i, x, y, yaw, s, s * 0.95, s * 0.88, bury
        ).get_actor_label()
    )

# Outer spill
outer = 28
for i in range(outer):
    deg = i * (360.0 / outer) + 6.0
    rad = math.radians(deg)
    x = CENTER_X + math.cos(rad) * 6700.0
    y = CENTER_Y + math.sin(rad) * 5000.0
    yaw = deg + 90.0
    mesh = meshes[(i * 5 + 2) % len(meshes)]
    path = mesh.get_path_name().lower()
    s = 14.0 if ("kenney" in path or mesh.get_name().lower().startswith("rock_")) else 1.8
    placed.append(
        place_sunk(
            mesh, "Ring_BlockOuter_%02d" % i, x, y, yaw, s, s * 0.92, s * 0.9, 0.48
        ).get_actor_label()
    )

# Explicit SAVE so progress is not lost
utils.save_dirty_packages(True, True)
saved = utils.save_map(world, LEVEL)

unreal.log("PLACE_REMOVED:%d" % removed)
unreal.log("PLACE_COUNT:%d" % len(placed))
unreal.log("PLACE_SAVED:%s ok=%s" % (LEVEL, saved))
print("PLACE_REMOVED:%d" % removed)
print("PLACE_COUNT:%d" % len(placed))
print("PLACE_SAVED:%s ok=%s" % (LEVEL, saved))
