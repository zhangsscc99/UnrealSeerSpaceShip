# -*- coding: utf-8 -*-
"""Build a large upright rock/canyon ring around the basin (no random shard piles)."""

from __future__ import annotations

import sys
import time

sys.path.append(
    r"C:\Program Files\Epic Games\UE_5.8\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python"
)
from remote_execution import RemoteExecution, MODE_EXEC_FILE

SCRIPT = r'''
import math
import unreal

LEVEL_PATH = "/Game/Maps/MeshyAIShowcase"
FOLDER = "RockRing"
CENTER_X = 0.0
CENTER_Y = -350.0

WALL = "/Game/MeshyAI/Meshy_AI_Rugged_Stone_Wall_0710144209_texture_fbx/Meshy_AI_Rugged_Stone_Wall_0710144209_texture"
STUMP = "/Game/MeshyAI/Meshy_AI_Stonebound_Stump_0710144219_texture_fbx/Meshy_AI_Stonebound_Stump_0710144219_texture"
ROCK = "/Game/Megascans/3D_Assets/Nordic_Beach_Rocks_vckqccbga_3d/Nordic_Beach_Rocks_LOD0_vckqccbga"

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
utils = unreal.EditorLoadingAndSavingUtils
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

wall = unreal.load_asset(WALL)
stump = unreal.load_asset(STUMP)
rock = unreal.load_asset(ROCK)
if not wall or not stump or not rock:
    raise RuntimeError("Missing ring mesh assets")


def folder(actor):
    try:
        actor.set_folder_path(FOLDER)
    except Exception:
        pass


def clear_old():
    removed = 0
    for actor in list(eas.get_all_level_actors()):
        if not isinstance(actor, unreal.StaticMeshActor):
            continue
        label = actor.get_actor_label()
        if label.startswith("Ring_") or label.startswith("Scatter_"):
            eas.destroy_actor(actor)
            removed += 1
    return removed


def place(mesh, label, x, y, z, yaw, sx, sy, sz, pitch=0.0, roll=0.0):
    actor = eas.spawn_actor_from_object(
        mesh,
        unreal.Vector(x, y, z),
        unreal.Rotator(pitch, yaw, roll),
    )
    actor.set_actor_label(label)
    actor.set_actor_scale3d(unreal.Vector(sx, sy, sz))
    folder(actor)
    return actor


removed = clear_old()
placed = []

# Outer canyon walls — larger ellipse, upright only, tangential yaw.
wall_count = 28
wall_a = 6000.0
wall_b = 4500.0
for i in range(wall_count):
    deg = i * (360.0 / wall_count)
    rad = math.radians(deg)
    wobble = 1.0 + 0.03 * math.sin(rad * 3.0)
    x = CENTER_X + math.cos(rad) * wall_a * wobble
    y = CENTER_Y + math.sin(rad) * wall_b * wobble
    yaw = deg + 90.0
    use_stump = (i % 5 == 2)
    mesh = stump if use_stump else wall
    sx = 4.4 if use_stump else 5.2
    sy = 4.0 if use_stump else 4.6
    sz = (4.6 if use_stump else 5.0) * (0.95 + 0.08 * abs(math.sin(rad * 2.0)))
    placed.append(place(mesh, "Ring_Wall_%02d" % i, x, y, -25.0, yaw, sx, sy, sz).get_actor_label())

# Inner base rubble — low and nearly flat, bridging wall to ground.
skirt_count = 36
skirt_a = 5200.0
skirt_b = 3900.0
for i in range(skirt_count):
    deg = i * (360.0 / skirt_count) + 5.0
    rad = math.radians(deg)
    x = CENTER_X + math.cos(rad) * skirt_a
    y = CENTER_Y + math.sin(rad) * skirt_b
    yaw = deg + 90.0
    scale = 1.1 + 0.25 * abs(math.sin(rad * 4.0))
    placed.append(
        place(
            rock,
            "Ring_Base_%02d" % i,
            x,
            y,
            -8.0,
            yaw,
            scale * 1.4,
            scale * 1.1,
            scale * 0.45,
            pitch=2.0,
        ).get_actor_label()
    )

utils.save_dirty_packages(True, True)
utils.save_map(world, LEVEL_PATH)
print("RING_REMOVED:%d" % removed)
print("RING_PLACED:%d" % len(placed))
print("RING_SAVED:%s" % LEVEL_PATH)
'''

remote = RemoteExecution()
remote.start()
try:
    for _ in range(30):
        if remote.remote_nodes:
            break
        time.sleep(0.5)
    if not remote.remote_nodes:
        raise RuntimeError("No Unreal Editor Python remote node found.")
    remote.open_command_connection(remote.remote_nodes[0]["node_id"])
    print(remote.run_command(SCRIPT, exec_mode=MODE_EXEC_FILE, raise_on_failure=True))
finally:
    remote.stop()
