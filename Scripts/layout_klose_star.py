# -*- coding: utf-8 -*-
import sys
sys.path.append(r"C:\Program Files\Epic Games\UE_5.8\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python")
from remote_execution import RemoteExecution, MODE_EXEC_FILE

SCRIPT = r'''
import unreal

utils = unreal.EditorLoadingAndSavingUtils
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# 1) Clear ALL StaticMeshActors for a clean redo
destroyed = 0
for actor in list(eas.get_all_level_actors()):
    if isinstance(actor, unreal.StaticMeshActor):
        eas.destroy_actor(actor)
        destroyed += 1

# 2) Resolve assets by unique id in path (avoid encoding issues)
asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
filter = unreal.ARFilter(
    class_names=["StaticMesh"],
    package_paths=["/Game/MeshyAI"],
    recursive_paths=True)
assets = asset_registry.get_assets(filter)

def find_mesh(token):
    for a in assets:
        path = str(a.package_name)
        if token in path:
            obj = unreal.load_asset(path)
            if obj:
                return obj
    raise RuntimeError("Missing StaticMesh for token: " + token)

ground     = find_mesh("0710144353")  # 克洛斯星地面
flower     = find_mesh("0710144344")  # 克洛斯星花
blue_rock  = find_mesh("0710144151")  # 克洛斯星蓝色小
tendril_p  = find_mesh("0710144323")  # Amethyst Tendril 粉色触手
tendril_g  = find_mesh("0710144230")  # Verdant Tendrils
gold_pile  = find_mesh("0710144248")  # Pile of gold 黄色晶体
gold_bar   = find_mesh("0710144257")  # Golden Bar
portal     = find_mesh("0710144313")  # Amberleaf Sentinel ~传送门
grass      = find_mesh("0710144133")  # 绿色小草
canopy     = find_mesh("0710144238")  # Emerald Canopy
wall       = find_mesh("0710144209")  # Rugged Stone Wall 多孔岩壁
stump      = find_mesh("0710144219")  # Stonebound Stump
petals     = find_mesh("0710144334")  # Whispered Petals

def place(mesh, label, x, y, z, sx, sy, sz, yaw=0):
    actor = eas.spawn_actor_from_object(mesh, unreal.Vector(x, y, z), unreal.Rotator(0, yaw, 0))
    actor.set_actor_label(label)
    actor.set_actor_scale3d(unreal.Vector(sx, sy, sz))
    return label

placed = []

# === 按参考图布局 (X:左负右正, Y:北正南负, Z:高度) ===

# A. 中央主活动区：橙色熔岩地面（大面积铺在中心偏南）
placed.append(place(ground, "Klose_Ground", 0, -200, 0, 18, 14, 0.25, 0))

# B. 左侧粉色触手（从左岩壁伸出到地面）
placed.append(place(tendril_p, "Klose_Tentacle_1", -1400, 100, 0, 4.5, 4.5, 4.5, 40))
placed.append(place(tendril_g, "Klose_Tentacle_2", -1200, -500, 0, 4, 4, 4, -20))
placed.append(place(tendril_p, "Klose_Tentacle_3", -1600, -200, 50, 3.5, 3.5, 3.5, 80))

# C. 北侧河带上的黄色浮晶（左上中）
placed.append(place(gold_pile, "Klose_Crystal_1", -600, 1100, 60, 3, 3, 3, 0))
placed.append(place(gold_bar,  "Klose_Crystal_2", -350, 1250, 80, 2.5, 2.5, 2.5, 35))
placed.append(place(gold_pile, "Klose_Crystal_3", -800, 1300, 40, 2.2, 2.2, 2.2, 70))

# D. 左上粉色山坡上的蓝色蘑菇/晶体
placed.append(place(blue_rock, "Klose_Blue_1", -1500, 1600, 200, 3, 3, 3, 0))
placed.append(place(blue_rock, "Klose_Blue_2", -1200, 1800, 250, 2.5, 2.5, 2.5, 45))
placed.append(place(blue_rock, "Klose_Blue_3", -1750, 1500, 180, 2, 2, 2, 90))

# E. 右上草地平台 + 传送门 + 食人花
placed.append(place(canopy, "Klose_GrassPad", 1200, 1600, -20, 5, 4, 0.8, 0))
placed.append(place(grass,  "Klose_Grass_1", 1000, 1500, 10, 3, 3, 2.5, 0))
placed.append(place(grass,  "Klose_Grass_2", 1450, 1750, 10, 2.5, 2.5, 2, 30))
placed.append(place(portal, "Klose_Portal", 1300, 1550, 80, 3, 3, 3, -25))
placed.append(place(flower, "Klose_Flower_1", 1050, 1350, 30, 2.5, 2.5, 2.5, 0))
placed.append(place(flower, "Klose_Flower_2", 1550, 1400, 30, 2.5, 2.5, 2.5, 90))
placed.append(place(flower, "Klose_Flower_3", 1200, 1800, 30, 2, 2, 2, 180))

# F. 右侧多孔岩壁
placed.append(place(wall, "Klose_Wall_R1", 2000, 200, 0, 5, 5, 4, -90))
placed.append(place(wall, "Klose_Wall_R2", 1900, -600, 0, 4.5, 4.5, 3.5, -80))

# G. 左侧岩壁/树桩
placed.append(place(stump, "Klose_Cliff_L", -2000, 0, 0, 4, 4, 3.5, 90))
placed.append(place(wall,  "Klose_Wall_L", -2100, 800, 0, 4, 4, 3.5, 90))

# H. 南侧后方悬崖
placed.append(place(stump, "Klose_Cliff_S", 200, -1600, 0, 4, 4, 3, 0))
placed.append(place(wall,  "Klose_Wall_S", -600, -1700, 0, 4, 4, 3, 10))

# I. 地面装饰花瓣
placed.append(place(petals, "Klose_Petals_1", -200, 600, 5, 2.5, 2.5, 2.5, 0))
placed.append(place(petals, "Klose_Petals_2", 400, -800, 5, 2, 2, 2, 50))

utils.save_dirty_packages(True, True)
utils.save_map(world, "/Game/Maps/MeshyAIShowcase")
print("DESTROYED:" + str(destroyed))
print("PLACED:" + str(len(placed)))
print("LABELS:" + ",".join(placed))
'''

remote = RemoteExecution()
remote.start()
try:
    import time
    for _ in range(20):
        if remote.remote_nodes:
            break
        time.sleep(0.5)
    if not remote.remote_nodes:
        raise RuntimeError("No UE Python remote node")
    remote.open_command_connection(remote.remote_nodes[0]["node_id"])
    result = remote.run_command(SCRIPT, exec_mode=MODE_EXEC_FILE, raise_on_failure=True)
    print(result)
finally:
    remote.stop()
