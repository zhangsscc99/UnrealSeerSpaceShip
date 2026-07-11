# -*- coding: utf-8 -*-
import sys
import time

sys.path.append(
    r"C:\Program Files\Epic Games\UE_5.8\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python"
)
from remote_execution import RemoteExecution, MODE_EXEC_FILE

SCRIPT = r'''
import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
utils = unreal.EditorLoadingAndSavingUtils
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
FOLDER = "HybridLighting"

def find_existing(actor_class, label):
    for actor in eas.get_all_level_actors():
        if isinstance(actor, actor_class):
            return actor
        if actor.get_actor_label() == label:
            return actor
    return None

def ensure_actor(actor_class, label, location, rotation):
    existing = find_existing(actor_class, label)
    if existing:
        print("SKIP:" + label)
        return existing
    actor = eas.spawn_actor_from_class(actor_class.static_class(), location, rotation)
    actor.set_actor_label(label)
    try:
        actor.set_folder_path(FOLDER)
    except Exception:
        pass
    print("CREATE:" + label)
    return actor

sun = ensure_actor(unreal.DirectionalLight, "Klose_Sun", unreal.Vector(0, 0, 5000), unreal.Rotator(-45, 45, 0))
sky = ensure_actor(unreal.SkyLight, "Klose_SkyLight", unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
ensure_actor(unreal.SkyAtmosphere, "Klose_SkyAtmosphere", unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
cloud = ensure_actor(unreal.VolumetricCloud, "Klose_VolumetricCloud", unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
fog = ensure_actor(unreal.ExponentialHeightFog, "Klose_HeightFog", unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))

try:
    sc = sun.light_component
    if sc:
        sc.set_editor_property("Intensity", 10.0)
        sc.set_editor_property("LightColor", unreal.Color(255, 244, 214, 255))
        sc.set_editor_property("bAtmosphereSunLight", True)
        sc.set_editor_property("AtmosphereSunLightIndex", 0)
        sc.set_editor_property("CastShadows", True)
        sc.set_editor_property("Mobility", unreal.ComponentMobility.MOVABLE)
except Exception as e:
    print("SUN_ERR:" + str(e))

try:
    slc = sky.light_component
    if slc:
        slc.set_editor_property("Intensity", 1.0)
        slc.set_editor_property("Mobility", unreal.ComponentMobility.MOVABLE)
        slc.set_editor_property("bRealTimeCapture", True)
        slc.set_editor_property("SourceType", unreal.SkyLightSourceType.SLS_CAPTURED_SCENE)
        slc.recapture_sky()
except Exception as e:
    print("SKY_ERR:" + str(e))

try:
    fc = fog.component
    if fc:
        fc.set_editor_property("FogDensity", 0.02)
        fc.set_editor_property("FogHeightFalloff", 0.2)
        fc.set_editor_property("bEnableVolumetricFog", True)
        fc.set_editor_property("VolumetricFogScatteringDistribution", 0.5)
        fc.set_editor_property("VolumetricFogExtinctionScale", 1.0)
        fc.set_editor_property("VolumetricFogAlbedo", unreal.Color(230, 242, 230, 255))
except Exception as e:
    print("FOG_ERR:" + str(e))

try:
    cc = cloud.get_component_by_class(unreal.VolumetricCloudComponent)
    if cc:
        cc.set_editor_property("LayerBottomAltitude", 5.0)
        cc.set_editor_property("LayerHeight", 15.0)
except Exception as e:
    print("CLOUD_ERR:" + str(e))

utils.save_dirty_packages(True, True)
utils.save_map(world, "/Game/Maps/MeshyAIShowcase")
print("OK")
'''

remote = RemoteExecution()
remote.start()
try:
    for _ in range(20):
        if remote.remote_nodes:
            break
        time.sleep(0.5)
    if not remote.remote_nodes:
        raise RuntimeError("No UE Python remote node")
    remote.open_command_connection(remote.remote_nodes[0]["node_id"])
    print(remote.run_command(SCRIPT, exec_mode=MODE_EXEC_FILE, raise_on_failure=True))
finally:
    remote.stop()
