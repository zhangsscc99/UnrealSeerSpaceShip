# -*- coding: utf-8 -*-
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
FOLDER = "SceneCraft"

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
utils = unreal.EditorLoadingAndSavingUtils
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()

def safe_set(obj, prop, value):
    try:
        obj.set_editor_property(prop, value)
        return True
    except Exception:
        return False

def folder(actor):
    try:
        actor.set_folder_path(FOLDER)
    except Exception:
        pass

def clear_scene():
    removed = 0
    classes = (
        unreal.StaticMeshActor,
        unreal.PointLight,
        unreal.RectLight,
        unreal.SpotLight,
        unreal.DirectionalLight,
        unreal.SkyLight,
        unreal.SkyAtmosphere,
        unreal.ExponentialHeightFog,
        unreal.VolumetricCloud,
        unreal.PostProcessVolume,
        unreal.CineCameraActor,
    )
    for actor in list(eas.get_all_level_actors()):
        label = actor.get_actor_label()
        if isinstance(actor, unreal.StaticMeshActor) or label.startswith("Klose_") or label.startswith("Scene_"):
            if isinstance(actor, classes):
                eas.destroy_actor(actor)
                removed += 1
    return removed

assets = asset_registry.get_assets(unreal.ARFilter(
    class_names=["StaticMesh"],
    package_paths=["/Game/MeshyAI"],
    recursive_paths=True,
))

def find_mesh(token):
    for data in assets:
        path = str(data.package_name)
        if token in path:
            mesh = unreal.load_asset(path)
            if mesh:
                return mesh
    raise RuntimeError("Missing StaticMesh token: " + token)

mesh = {
    "ground": find_mesh("0710144353"),
    "flower": find_mesh("0710144344"),
    "blue": find_mesh("0710144151"),
    "amethyst": find_mesh("0710144323"),
    "tendril": find_mesh("0710144230"),
    "gold_pile": find_mesh("0710144248"),
    "gold_bar": find_mesh("0710144257"),
    "portal": find_mesh("0710144313"),
    "grass": find_mesh("0710144133"),
    "canopy": find_mesh("0710144238"),
    "wall": find_mesh("0710144209"),
    "stump": find_mesh("0710144219"),
    "petals": find_mesh("0710144334"),
}

def place(key, label, loc, scale, yaw=0, pitch=0, roll=0):
    actor = eas.spawn_actor_from_object(
        mesh[key],
        unreal.Vector(loc[0], loc[1], loc[2]),
        unreal.Rotator(pitch, yaw, roll),
    )
    actor.set_actor_label(label)
    actor.set_actor_scale3d(unreal.Vector(scale[0], scale[1], scale[2]))
    folder(actor)
    return actor

def light(actor_class, label, loc, rot=(0, 0, 0), intensity=None, color=None, radius=None):
    actor = eas.spawn_actor_from_class(
        actor_class.static_class(),
        unreal.Vector(loc[0], loc[1], loc[2]),
        unreal.Rotator(rot[0], rot[1], rot[2]),
    )
    actor.set_actor_label(label)
    folder(actor)
    comp = getattr(actor, "light_component", None)
    if comp:
        if intensity is not None:
            safe_set(comp, "Intensity", intensity)
        if color is not None:
            safe_set(comp, "LightColor", color)
        if radius is not None:
            safe_set(comp, "AttenuationRadius", radius)
        safe_set(comp, "Mobility", unreal.ComponentMobility.MOVABLE)
    return actor

removed = clear_scene()
placed = []

# Broad stepped ground plates: overlapping scales give the playable area real mass.
placed.append(place("ground", "Scene_Central_Basin", (0, -260, -12), (20.0, 15.5, 0.22), 0))
placed.append(place("ground", "Scene_North_Terrace", (120, 940, -4), (12.0, 7.0, 0.18), 7))
placed.append(place("ground", "Scene_South_Foreground", (-120, -1460, -18), (11.0, 5.2, 0.16), -5))

# Main portal silhouette at the back, framed by cliffs and living tendrils.
placed.append(place("portal", "Scene_Amberleaf_Gate", (110, 1530, 120), (4.8, 4.8, 4.8), 180))
for i, x in enumerate([-720, 780]):
    placed.append(place("wall", "Scene_Back_Cliff_%02d" % i, (x, 1580, 40), (5.0, 4.2, 4.8), 180 + (18 if x < 0 else -18)))
    placed.append(place("stump", "Scene_Back_Buttress_%02d" % i, (x * 1.18, 1130, 20), (3.4, 3.4, 4.2), 150 if x < 0 else -150))

for i, data in enumerate([
    ("amethyst", (-1500, 480, 55), (4.5, 4.5, 4.8), 42),
    ("tendril", (-1270, -280, 20), (4.4, 4.4, 4.6), -18),
    ("amethyst", (-1730, -820, 40), (3.7, 3.7, 4.1), 74),
    ("tendril", (1450, 320, 15), (3.9, 3.9, 4.0), -142),
    ("amethyst", (1710, -520, 45), (3.4, 3.4, 3.9), -92),
]):
    placed.append(place(data[0], "Scene_Living_Tendril_%02d" % i, data[1], data[2], data[3]))

# Curved approach path: repeated petals and crystals lead the eye from spawn to the gate.
for i in range(13):
    t = i / 12.0
    y = -1320 + t * 2380
    x = math.sin(t * math.pi * 1.15) * 260
    yaw = -12 + 24 * math.sin(t * math.pi)
    scale = 1.2 + 0.55 * (1.0 - t)
    key = "petals" if i % 2 == 0 else "grass"
    placed.append(place(key, "Scene_Path_Marker_%02d" % i, (x, y, 12), (scale, scale, scale * 0.75), yaw))

for i, data in enumerate([
    ("gold_pile", (-470, 1030, 70), (2.7, 2.7, 2.7), 18),
    ("gold_bar", (-250, 1190, 96), (2.2, 2.2, 2.2), -35),
    ("gold_pile", (460, 1070, 72), (2.4, 2.4, 2.4), -24),
    ("blue", (-1010, 1320, 165), (2.4, 2.4, 2.4), 26),
    ("blue", (1050, 1260, 145), (2.2, 2.2, 2.2), -44),
    ("blue", (80, 1260, 130), (1.8, 1.8, 1.8), 0),
]):
    placed.append(place(data[0], "Scene_Gate_Crystal_%02d" % i, data[1], data[2], data[3]))

# Foreground and side ecology, denser near the camera and thinner toward the gate.
for i, data in enumerate([
    ("canopy", (-930, -1040, 0), (3.6, 3.0, 0.8), 20),
    ("canopy", (980, -820, -5), (3.2, 2.8, 0.75), -28),
    ("flower", (-620, -820, 30), (2.2, 2.2, 2.2), 12),
    ("flower", (560, -660, 30), (2.0, 2.0, 2.0), -36),
    ("flower", (-980, 180, 34), (1.8, 1.8, 1.8), 50),
    ("flower", (900, 300, 34), (1.9, 1.9, 1.9), -58),
    ("grass", (-1250, -560, 18), (2.4, 2.4, 1.9), 0),
    ("grass", (1220, -420, 18), (2.3, 2.3, 1.8), 36),
]):
    placed.append(place(data[0], "Scene_Ecology_%02d" % i, data[1], data[2], data[3]))

for i, data in enumerate([
    ("wall", (-2150, 240, 0), (4.8, 4.3, 4.1), 86),
    ("wall", (2160, 120, 0), (4.8, 4.3, 4.1), -86),
    ("stump", (-1900, -1020, -5), (3.8, 3.8, 3.5), 64),
    ("stump", (1880, -940, -5), (3.6, 3.6, 3.5), -70),
]):
    placed.append(place(data[0], "Scene_Side_Wall_%02d" % i, data[1], data[2], data[3]))

# Atmosphere and cinematic lighting.
sun = light(unreal.DirectionalLight, "Scene_Low_Sun", (0, 0, 5000), (-34, 42, 0), 7.5, unreal.Color(255, 226, 190, 255))
if getattr(sun, "light_component", None):
    safe_set(sun.light_component, "bAtmosphereSunLight", True)
    safe_set(sun.light_component, "AtmosphereSunLightIndex", 0)

sky = light(unreal.SkyLight, "Scene_SkyLight", (0, 0, 0), (0, 0, 0), 0.85, unreal.Color(190, 215, 255, 255))
if getattr(sky, "light_component", None):
    safe_set(sky.light_component, "bRealTimeCapture", True)
    safe_set(sky.light_component, "SourceType", unreal.SkyLightSourceType.SLS_CAPTURED_SCENE)
    try:
        sky.light_component.recapture_sky()
    except Exception:
        pass

for cls, label in [
    (unreal.SkyAtmosphere, "Scene_SkyAtmosphere"),
    (unreal.VolumetricCloud, "Scene_VolumetricCloud"),
    (unreal.ExponentialHeightFog, "Scene_HeightFog"),
]:
    actor = eas.spawn_actor_from_class(cls.static_class(), unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    actor.set_actor_label(label)
    folder(actor)
    if isinstance(actor, unreal.ExponentialHeightFog):
        comp = actor.component
        safe_set(comp, "FogDensity", 0.032)
        safe_set(comp, "FogHeightFalloff", 0.18)
        safe_set(comp, "FogInscatteringColor", unreal.LinearColor(0.62, 0.86, 0.84, 1.0))
        safe_set(comp, "bEnableVolumetricFog", True)
        safe_set(comp, "VolumetricFogScatteringDistribution", 0.58)
        safe_set(comp, "VolumetricFogExtinctionScale", 0.75)

light(unreal.PointLight, "Scene_Gate_Aura", (120, 1370, 360), (0, 0, 0), 5800, unreal.Color(255, 166, 80, 255), 1450)
light(unreal.PointLight, "Scene_Left_Crystal_Glow", (-630, 1020, 260), (0, 0, 0), 2200, unreal.Color(255, 214, 85, 255), 900)
light(unreal.PointLight, "Scene_Right_Blue_Glow", (940, 1100, 240), (0, 0, 0), 1800, unreal.Color(89, 164, 255, 255), 850)
light(unreal.RectLight, "Scene_Foreground_Rim", (0, -1180, 520), (-28, 180, 0), 1200, unreal.Color(180, 230, 255, 255), 1200)

pp = eas.spawn_actor_from_class(unreal.PostProcessVolume.static_class(), unreal.Vector(0, 0, 120), unreal.Rotator(0, 0, 0))
pp.set_actor_label("Scene_PostProcess")
folder(pp)
safe_set(pp, "bUnbound", True)
settings = pp.get_editor_property("settings")
safe_set(settings, "bOverride_AutoExposureMinBrightness", True)
safe_set(settings, "bOverride_AutoExposureMaxBrightness", True)
safe_set(settings, "AutoExposureMinBrightness", 0.9)
safe_set(settings, "AutoExposureMaxBrightness", 1.25)
safe_set(settings, "bOverride_BloomIntensity", True)
safe_set(settings, "BloomIntensity", 0.35)
safe_set(settings, "bOverride_VignetteIntensity", True)
safe_set(settings, "VignetteIntensity", 0.28)
safe_set(settings, "bOverride_ColorSaturation", True)
safe_set(settings, "ColorSaturation", unreal.Vector4(1.05, 1.08, 1.12, 1.0))

camera = eas.spawn_actor_from_class(unreal.CineCameraActor.static_class(), unreal.Vector(0, -2740, 760), unreal.Rotator(-10, 0, 0))
camera.set_actor_label("Scene_Composition_Camera")
folder(camera)
cam_comp = camera.get_cine_camera_component()
safe_set(cam_comp, "CurrentFocalLength", 24.0)
safe_set(cam_comp, "CurrentAperture", 5.6)
safe_set(cam_comp, "FocusSettings", unreal.CameraFocusSettings(focus_method=unreal.CameraFocusMethod.DISABLE))
try:
    unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(
        unreal.Vector(0, -2740, 760),
        unreal.Rotator(-10, 0, 0),
    )
except Exception:
    pass

utils.save_dirty_packages(True, True)
utils.save_map(world, LEVEL_PATH)
print("SCENECRAFT_REMOVED:%d" % removed)
print("SCENECRAFT_PLACED:%d" % len(placed))
print("SCENECRAFT_SAVED:%s" % LEVEL_PATH)
'''

remote = RemoteExecution()
remote.start()
try:
    for _ in range(30):
        if remote.remote_nodes:
            break
        time.sleep(0.5)
    if not remote.remote_nodes:
        raise RuntimeError("No Unreal Editor Python remote node found. Enable Python remote execution in Editor Preferences.")

    remote.open_command_connection(remote.remote_nodes[0]["node_id"])
    result = remote.run_command(SCRIPT, exec_mode=MODE_EXEC_FILE, raise_on_failure=True)
    print(result)
finally:
    remote.stop()
