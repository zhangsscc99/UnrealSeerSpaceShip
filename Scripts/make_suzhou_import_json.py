# -*- coding: utf-8 -*-
import json
from pathlib import Path

root = Path(r"C:/Users/admin/Desktop/UnrealSeerSpaceShip")
models = root / "Content/ThirdParty/ChineseGarden/Models"
files = []
# Prefer smaller assets first; skip giant trees for now if > 40MB
for d in sorted(models.iterdir()):
    if not d.is_dir():
        continue
    for f in d.glob("*.fbx"):
        size = f.stat().st_size
        if size > 40_000_000:
            print("skip large", f.name, size)
            continue
        files.append(str(f).replace("\\", "/"))

# Also include Kenney stones already on disk for rockery variety
kenney = root / "Content/ThirdParty/KenneyNatureKit/FBX"
for pat in ("rock_large*.fbx", "stone_large*.fbx", "cliff_*.fbx"):
    for f in kenney.glob(pat):
        files.append(str(f).replace("\\", "/"))

print("file count", len(files))
cfg = {
    "ImportGroups": [
        {
            "FileNames": files,
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
out = root / "Saved/import_suzhou_meshes.json"
out.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
print("wrote", out)
for f in files[:15]:
    print(" ", f)
