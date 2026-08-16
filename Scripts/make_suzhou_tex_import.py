# -*- coding: utf-8 -*-
"""Import Chinese garden textures via ImportAssets commandlet JSON."""
import json
from pathlib import Path

root = Path(r"C:/Users/admin/Desktop/UnrealSeerSpaceShip")
tex_root = root / "Content/ThirdParty/ChineseGarden/Textures"
files = []
for d in sorted(tex_root.iterdir()):
    if not d.is_dir():
        continue
    for f in d.glob("*.jpg"):
        files.append(str(f).replace("\\", "/"))
    for f in d.glob("*.png"):
        files.append(str(f).replace("\\", "/"))

# also potted plants already downloaded as fbx
models = root / "Content/ThirdParty/ChineseGarden/Models"
extra_fbx = []
for name in ("potted_plant_01", "potted_plant_02"):
    for f in (models / name).glob("*.fbx"):
        if f.stat().st_size < 40_000_000:
            extra_fbx.append(str(f).replace("\\", "/"))

print("textures", len(files), "fbx", len(extra_fbx))

tex_cfg = {
    "ImportGroups": [
        {
            "FileNames": files,
            "bReplaceExisting": True,
            "DestinationPath": "/Game/SuzhouGarden/Textures",
            "FactoryName": "TextureFactory",
            "ImportSettings": {},
        }
    ]
}
(root / "Saved/import_suzhou_textures.json").write_text(
    json.dumps(tex_cfg, indent=2), encoding="utf-8"
)

mesh_cfg = {
    "ImportGroups": [
        {
            "FileNames": extra_fbx,
            "bReplaceExisting": True,
            "DestinationPath": "/Game/SuzhouGarden/Meshes",
            "FactoryName": "FbxFactory",
            "ImportSettings": {
                "bImportMesh": 1,
                "bImportAsSkeletal": 0,
                "bImportAnimations": 0,
                "bImportMaterials": 1,
                "bImportTextures": 1,
                "MeshTypeToImport": 0,
                "OriginalImportType": 0,
                "AutomatedImportShouldDetectType": 0,
                "StaticMeshImportData": {
                    "bCombineMeshes": 1,
                    "bAutoGenerateCollision": 1,
                    "bRemoveDegenerates": 1,
                },
            },
        }
    ]
}
(root / "Saved/import_suzhou_plants.json").write_text(
    json.dumps(mesh_cfg, indent=2), encoding="utf-8"
)
print("wrote jsons")
