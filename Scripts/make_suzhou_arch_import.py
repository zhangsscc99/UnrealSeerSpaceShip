# -*- coding: utf-8 -*-
import json
from pathlib import Path

root = Path(r"C:/Users/admin/Desktop/UnrealSeerSpaceShip")
arch = root / "Content/ThirdParty/ChineseGarden/Architecture"
files = []
pav = arch / "Pavilion/ChinesePavilion.fbx"
if pav.exists():
    files.append(str(pav).replace("\\", "/"))
for f in sorted((arch / "StructureSet/FBXs").glob("*.fbx")):
    files.append(str(f).replace("\\", "/"))
# potted plants
for name in ("potted_plant_01", "potted_plant_02"):
    for f in (root / "Content/ThirdParty/ChineseGarden/Models" / name).glob("*.fbx"):
        files.append(str(f).replace("\\", "/"))

print("count", len(files))
cfg = {
    "ImportGroups": [
        {
            "FileNames": files,
            "bReplaceExisting": True,
            "DestinationPath": "/Game/SuzhouGarden/Architecture",
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
out = root / "Saved/import_suzhou_arch.json"
out.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
print("wrote", out)
for f in files:
    print(" ", Path(f).name)
