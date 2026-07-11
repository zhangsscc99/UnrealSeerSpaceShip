import sys
sys.path.append(r"C:\Program Files\Epic Games\UE_5.8\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python")
from remote_execution import RemoteExecution, MODE_EXEC_FILE

SCRIPT = r"""
import unreal

utils = unreal.EditorLoadingAndSavingUtils
subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
world = subsystem.get_editor_world()
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# Remove previously placed showcase meshes
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    if isinstance(actor, unreal.StaticMeshActor):
        label = actor.get_actor_label()
        if any(k in label for k in ['Meshy', 'Amberleaf', 'Amethyst', 'Cotton', 'Emerald', 'Golden', 'Pile', 'Rugged', 'Stonebound', 'Verdant', 'Whispered', 'Green', '克洛斯', '绿色']):
            eas.destroy_actor(actor)

layout = [
    # 中央熔岩地面 - 主活动区
    ('/Game/MeshyAI/Meshy_AI_克洛斯星地面_0710144353_texture_fbx/Meshy_AI_克洛斯星地面_0710144353_texture', 'Klose_Ground', (0, 0, 0), (12, 12, 0.3), 0),
    # 左侧粉色触手植物
    ('/Game/MeshyAI/Meshy_AI_Amethyst_Tendril_0710144323_texture_fbx/Meshy_AI_Amethyst_Tendril_0710144323_texture', 'Klose_Tentacle_L1', (-1600, 300, 0), (3, 3, 3), 35),
    ('/Game/MeshyAI/Meshy_AI_Verdant_Tendrils_0710144230_texture_fbx/Meshy_AI_Verdant_Tendrils_0710144230_texture', 'Klose_Tentacle_L2', (-1500, -300, 0), (3.5, 3.5, 3), -25),
    # 水中黄色晶体
    ('/Game/MeshyAI/Meshy_AI_Pile_of_gold_0710144248_texture_fbx/Meshy_AI_Pile_of_gold_0710144248_texture', 'Klose_Crystal_1', (-700, 1300, 80), (2.5, 2.5, 2.5), 0),
    ('/Game/MeshyAI/Meshy_AI_Golden_Bar_and_Nugget_0710144257_texture_fbx/Meshy_AI_Golden_Bar_and_Nugget_0710144257_texture', 'Klose_Crystal_2', (-500, 1200, 100), (2, 2, 2), 45),
    # 左上蓝色小蘑菇/晶体
    ('/Game/MeshyAI/Meshy_AI_克洛斯星蓝色小_0710144151_texture_fbx/Meshy_AI_克洛斯星蓝色小_0710144151_texture', 'Klose_BlueRock_1', (-1100, 1700, 180), (2.5, 2.5, 2.5), 0),
    ('/Game/MeshyAI/Meshy_AI_克洛斯星蓝色小_0710144151_texture_fbx/Meshy_AI_克洛斯星蓝色小_0710144151_texture', 'Klose_BlueRock_2', (-900, 1900, 220), (2, 2, 2), 60),
    # 右上传送门区域
    ('/Game/MeshyAI/Meshy_AI_Amberleaf_Sentinel_0710144313_texture_fbx/Meshy_AI_Amberleaf_Sentinel_0710144313_texture', 'Klose_Portal', (1300, 1500, 120), (2.5, 2.5, 2.5), -30),
    ('/Game/MeshyAI/Meshy_AI_克洛斯星花_0710144344_texture_fbx/Meshy_AI_克洛斯星花_0710144344_texture', 'Klose_Flower_1', (1100, 1300, 40), (2, 2, 2), 0),
    ('/Game/MeshyAI/Meshy_AI_克洛斯星花_0710144344_texture_fbx/Meshy_AI_克洛斯星花_0710144344_texture', 'Klose_Flower_2', (1500, 1400, 40), (2, 2, 2), 90),
    ('/Game/MeshyAI/Meshy_AI_绿色小草_0710144133_texture_fbx/Meshy_AI_绿色小草_0710144133_texture', 'Klose_Grass_1', (1200, 1700, 20), (2.5, 2.5, 2), 0),
    ('/Game/MeshyAI/Meshy_AI_Emerald_Canopy_0710144238_texture_fbx/Meshy_AI_Emerald_Canopy_0710144238_texture', 'Klose_Grass_Canopy', (1000, 1800, 0), (2.5, 2.5, 2), 15),
    # 右侧多孔岩壁
    ('/Game/MeshyAI/Meshy_AI_Rugged_Stone_Wall_0710144209_texture_fbx/Meshy_AI_Rugged_Stone_Wall_0710144209_texture', 'Klose_Wall_R', (1900, 0, 0), (4, 4, 3), -90),
    ('/Game/MeshyAI/Meshy_AI_Rugged_Stone_Wall_0710144209_texture_fbx/Meshy_AI_Rugged_Stone_Wall_0710144209_texture', 'Klose_Wall_L', (-1900, 0, 0), (4, 4, 3), 90),
    # 后方岩壁/树桩
    ('/Game/MeshyAI/Meshy_AI_Stonebound_Stump_0710144219_texture_fbx/Meshy_AI_Stonebound_Stump_0710144219_texture', 'Klose_Cliff_Back', (0, -1700, 0), (3, 3, 2.5), 0),
    # 装饰
    ('/Game/MeshyAI/Meshy_AI_Whispered_Petals_0710144334_texture_fbx/Meshy_AI_Whispered_Petals_0710144334_texture', 'Klose_Petals', (-300, 900, 0), (2, 2, 2), 0),
    ('/Game/MeshyAI/Meshy_AI_Cotton_Candy_Pig_0710144305_texture_fbx/Meshy_AI_Cotton_Candy_Pig_0710144305_texture', 'Klose_Creature', (-1000, 1600, 200), (1.5, 1.5, 1.5), 0),
]

placed = []
for asset_path, label, loc, scale, yaw in layout:
    mesh = unreal.load_asset(asset_path)
    if not mesh:
        raise RuntimeError('Missing asset: ' + asset_path)
    actor = eas.spawn_actor_from_object(mesh, unreal.Vector(*loc), unreal.Rotator(0, yaw, 0))
    actor.set_actor_label(label)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    placed.append(label)

utils.save_dirty_packages(True, True)
utils.save_map(world, '/Game/Maps/MeshyAIShowcase')
print('LAYOUT:' + ','.join(placed))
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
        raise RuntimeError('No UE Python remote node')
    remote.open_command_connection(remote.remote_nodes[0]['node_id'])
    result = remote.run_command(SCRIPT, exec_mode=MODE_EXEC_FILE, raise_on_failure=True)
    print(result)
finally:
    remote.stop()
