# Ralph Development Instructions

## Context

You are Ralph, an autonomous agent working on the **UnrealSeerSpaceShip** Unreal
Engine 5.8 project. There is no code to compile — the work is **editing the live
`/Game/Maps/SuzhouGarden` level through the `unreal-mcp` editor tools**.

**Read `.ralph/AGENT.md` before your first tool call.** It documents the MCP
calling convention, the batching script toolset, the gotchas that silently waste a
whole loop, and how to save/revert/commit safely.

## Current Objectives

**The single task: enlarge the central Suzhou Garden so its ground area is 4×
larger than it is now.**

A larger map was previously attempted by scattering decorations far out to inflate
the bounding box. That is **not** what is wanted. What is wanted is the **central
walkable garden ground itself** — the terrain, the paving, the walls, the building
clusters, the pavilion spacing and the waterways — laid out 4× larger.

Target: **linear extent ×2 in X and Y ⇒ ground area ×4.** Measure the garden's
current X/Y extent first, and re-measure at the end; the numbers are the
acceptance test.

Work through `.ralph/fix_plan.md` one item per loop and keep it up to date — it is
your memory across loops.

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

Read `.ralph/fix_plan.md` and implement the most important unfinished item. Start
by measuring the garden's current extent if that has not been recorded yet.
