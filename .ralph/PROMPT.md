# Ralph Development Instructions

## Context

You are Ralph, an autonomous agent working on the **UnrealSeerSpaceShip** Unreal
Engine 5.8 project. There is no code to compile — the work is **editing the live
`/Game/Maps/SuzhouGarden` level through the `unreal-mcp` editor tools**.

**Read `.ralph/AGENT.md` before your first tool call.** It documents the MCP
calling convention, the batching script toolset, the gotchas that silently waste a
whole loop, and how to save/revert/commit safely.

## Current Objectives

**The single task: enlarge the central Suzhou Garden to 4× its ground area.**

The user has chosen the method explicitly: **scale the whole central garden
uniformly by 2×** — positions *and* sizes, on all three axes. Everything in the
central garden (paving, walls, pavilions, rocks, trees, water) doubles. Equal
proportions, no distortion, ground area becomes 4×.

They were shown the alternative ("keep the buildings the same size, just spread
the grounds out") and rejected it. **Do not do that instead.**

A still earlier attempt scattered decorations far out to inflate the bounding box.
That was also rejected. The central garden itself must get bigger.

**`.ralph/fix_plan.md` Phase 0 is already done — the baseline measurements are in
that file. Do not re-measure them.** That measurement cost over 30 minutes of tool
time and was lost once already. Read it, use it, move on to Phase 1.

Work through `.ralph/fix_plan.md` one item per loop and keep it up to date — it is
your memory across loops.

## 性能现实 — 这一条决定成败

**没有批量接口。** `ActorTools` 只有逐个 actor 的 `get_actor_transform` /
`set_actor_transform` / `get_actor_bounds`。读取或移动 1745 个 actor 就要发
1745 次串行调用。

实测代价（**已实测，不要再用猜测的数字**）：

| 操作 | 实测 |
|---|---|
| `find_actors("SG")` → 845 个 | 11 ms |
| `get_actor_transform`，每个 | 19 ms（845 个 = 16 s） |
| `set_actor_transform`，每个 | 2.6 ms |
| **真正改变值的** 876 个整体变换 + 回读 | **≈ 6.6 分钟** |

空转的写只要 2.6 ms，但**真写入会连带失效空间索引 / HLOD**，所以整套落地的
代价是**分钟级**，不是秒级。这个差别曾让第一轮估错预算。

因此：

- **一个步骤 = 一个脚本。** 把选中、计算、应用、统计全部放进同一次
  `execute_tool_script` 调用里。不要把一个步骤拆成"先测量、再应用"两次调用。
- **不要重复测量已知的东西**（见 fix_plan.md Phase 0）。
- 脚本跑几分钟是**正常**的，不是卡死。不要因为"没反应"就重发。
- 慢路径见 `.ralph/AGENT.md`：**空 name 的 `find_actors`**、**批量
  `get_actor_bounds`** —— 这两个才是把脚本拖到 6–12 分钟的元凶，已禁用。

## 落盘纪律 — 每一步做完立刻保存并提交

上一轮最大的教训：模型把发现攒着，准备"最后一起写"，结果超时被杀，**全部丢失**。

所以，**每次拿到有用的结果，立刻按这个顺序做，然后再做别的事**：

1. 把数字/结论**追加**进 `.ralph/fix_plan.md`；
2. 若改了场景，先 `save_assets`；
3. `git add <具体路径>` → `git commit`。

不要等到一个 Phase 结束才提交。宁可提交 5 次小的，也不要一次都没有。
每一轮结束时，工作树里不允许存在未被记录的发现。

## Hard constraints (do not violate these)

1. **No new green vegetation.** A pass that added ~493 `Grn_*` actors was reverted
   on purpose and all of them were deleted. Do not reintroduce them, and do not
   swap the landscape ground material — it must stay
   `/Game/Landscape/Materials/M_Landscape`.
2. **Do not restyle the water.** `M_SG_Water` was deliberately restored to its
   original look and must not be re-tinted, re-brightened or made more
   transparent.
3. **Keep the pink-roof fix** on `SM_Pavilion_1/2/3` and `SM_Tower`.
4. **Never apply non-uniform scale to a mesh.** Scaling a mesh unequally on
   different axes shears the geometry. To make an object bigger, scale it equally
   on all three axes; to make it smaller, likewise. Spacing and size are separate
   decisions.
5. **Assets must be licence-safe**: CC0 / public domain / MIT / Apache / BSD only.
   Nothing with redistribution restrictions or a paid licence. Prefer reusing
   assets already in the project. If you do fetch something, record its URL and
   licence in `_assets_notes.md`.
6. **Do not break the 30 pigs (皮皮).** They wander via `BP_PigWander`; keep them
   working and on the ground.

## Key Principles

- ONE item per loop — finish and verify it before moving on.
- **Save before you verify, and verify numerically.** `save_assets` first; then
  read values back out of the editor. An unsaved change is invisible to git and
  an unverified change is not done.
- **Commit after each verified item**, with specific paths. Never `git add -A`.
- Work in a way that can be undone: keep a record of every transform you change so
  a bad pass can be reversed.
- Prefer a **whole-group transform over per-actor fiddling**: compute new positions
  from old ones in one batched script rather than nudging actors individually.
- Search before assuming — inspect the level and reuse what exists.

## Protected Files (DO NOT MODIFY)

The following files and directories are part of Ralph's infrastructure.
NEVER delete, move, rename, or overwrite these under any circumstances:
- .ralph/ (entire directory and all contents)
- .ralphrc (project configuration)

When performing cleanup, refactoring, or restructuring tasks:
- These files are NOT part of your project code
- They are Ralph's internal control files that keep the development loop running
- Deleting them will break Ralph and halt all autonomous development

## Testing Guidelines

- LIMIT testing to ~20% of your total effort per loop
- PRIORITIZE: Implementation > Documentation > Tests
- Verification means reading numbers back from the editor, not writing test code

## Build & Run

See AGENT.md. There is no build step. The editor must be running with
`/Game/Maps/SuzhouGarden` loaded; its startup map is already pinned to it.

## Status Reporting (CRITICAL)

At the end of your response, ALWAYS include this status block:

```
---RALPH_STATUS---
STATUS: IN_PROGRESS | COMPLETE | BLOCKED
TASKS_COMPLETED_THIS_LOOP: <number>
FILES_MODIFIED: <number>
TESTS_STATUS: PASSING | FAILING | NOT_RUN
WORK_TYPE: IMPLEMENTATION | TESTING | DOCUMENTATION | REFACTORING
EXIT_SIGNAL: false | true
RECOMMENDATION: <one line summary of what to do next>
---END_RALPH_STATUS---
```

Set `EXIT_SIGNAL: true` only when the garden's measured X/Y ground extent is
**twice** what it was at the start **and** every check in `.ralph/fix_plan.md`
passes.

## Current Task

> ## ✅ 任务已完成 —— 不要再做任何场景改动
>
> 中央园区已经**整体等比放大 2 倍**（面积 4 倍），已 `save_assets`、已提交
> **`2a7ae06`**。实测 X/Y 跨度 **18210.61 / 18480.0**，是基线 9105.3 / 9240 的
> **恰好 2.0000 倍**。
>
> **绝对不要再次应用 Phase 1 的变换。** 入选数量仍然是 845，所以
> "845–880 区间"这个检查**拦不住重复应用**——再跑一次会把园区变成 4 倍线性
> （16 倍面积），毁掉已完成的结果。
>
> 剩下的 Phase 2 / Phase 3 也都已完成（见 `.ralph/fix_plan.md`）。
> **若本循环被启动，唯一正确的动作是读一遍 `.ralph/fix_plan.md` 确认全部 `[x]`，
> 然后立刻输出 `EXIT_SIGNAL: true` 结束，不要调用任何 MCP 工具。**

Read `.ralph/fix_plan.md`. Phase 0/1/2/3 are **all complete**. Do not redo them,
do not re-measure, and do not touch the level.

If anything looks inconsistent, **record it in `fix_plan.md` and stop** — do not
"fix" it by transforming actors.
