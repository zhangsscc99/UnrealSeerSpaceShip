# SeerCorridor ↔ SeerLab 无缝连通方案记录

日期：2026-11-01
当前安全回退点：`6db85e7` + tag `checkpoint/seer-corridor-portal-20261101`
（此版本门后是静态实验室截图 + 双向传送，作为保底方案）

## 目标

- 打开走廊起点门后看到**真实的 SeerLab 几何**，而不是贴图
- 两个区域在同一个世界里按需流送：靠近才加载、离开卸载（参考 WoW 大世界）
- 最终可以直接走过门进入实验室；阈值传送保留为兜底

## 已实测确认（UE 5.8.4）

在 SeerCorridor（非 World Partition）中创建 `ALevelInstance`，把
`world_asset` 指向 `/Game/SeerLab.SeerLab`，调用 `load_level_instance()`：

- 引擎把 SeerLab 加载为同一世界中的流送关卡
  （`/Temp/Game/SeerLab_LevelInstance_<hash>_0.SeerLab`）
- 实例的位移会应用到实验室 actor：
  实例放在 `(0, -30000, 0)` 时，`LabDoor` 出现在 `(400, -29331, 0)`，
  `LabShell` 出现在 `(0, -30000, 0)`
- 视口中能看到真实的实验室内部（椅子、控制台、舷窗），**不是贴图**

结论：两个场景可以同时存在于同一个世界，通过 Level Instance + 流送控制，
而不是"两个场景不可能同时加载"。

可用 API：

- `unreal.LevelInstance`：`set_world_asset` / `load_level_instance` /
  `unload_level_instance` / `get_loaded_level` / `level_transform`
- `unreal.EditorLevelUtils`：`create_new_streaming_level` /
  `move_actors_to_level` / `add_level_to_world_with_transform`
- `unreal.WorldPartitionSubsystem`

## 待实施

1. 在走廊起点门（y=80）后方放置 SeerLab 的 Level Instance，按门洞对齐
2. 在走廊 V5 后墙和实验室北墙开出真正可走通的门口
3. 流送控制：靠近起点门时加载实验室，离开后卸载
   （流送体积 / 距离流送 / World Partition，按调研结论选型）
4. 移除静态贴图背景、`OpenLevel` 传送和 SeerLab 侧反向触发；保留门滑开动画
5. 性能：流送距离、HLOD/LOD、遮挡与距离裁剪、灯光/阴影、纹理流送

## 回退

- 回到保底版本：`git checkout 6db85e7`
- 或回到 tag：`checkpoint/seer-corridor-portal-20261101`
- `Config/DefaultEngine.ini.bak_zen` 是本地备份文件，未提交

## 状态

- 调研工作流运行中：UE5.8 Level Instance / World Partition 流送细节，
  以及 WoW 无缝世界的具体做法
