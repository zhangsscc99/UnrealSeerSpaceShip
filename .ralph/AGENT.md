# Ralph Agent Configuration

## What this project is

An Unreal Engine 5.8 project (`UnrealSeerSpaceShip.uproject`). There is no code to
compile — "development" here means **editing a live level inside the running
Unreal Editor**, through an MCP server the editor exposes.

## Build Instructions

Nothing to build. Never run UBT, `msbuild`, or a compiler.

```
# n/a — assets are edited in the running editor
```

## Test Instructions

Verification is **numeric, through the MCP tools** — not a test suite. See
"Verifying your work" below. Never claim a change works without reading the
numbers back.

## Run Instructions

```
# The editor must already be running with the SuzhouGarden level loaded:
"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" \
  "C:/Users/admin/Desktop/UnrealSeerSpaceShip/UnrealSeerSpaceShip.uproject" \
  /Game/Maps/SuzhouGarden
```

## Talking to the editor (read this carefully)

The editor is reachable over MCP as the server `unreal-mcp` (HTTP at
`http://127.0.0.1:8000/mcp`). Two harness calls exist:

- `mcp__unreal-mcp__list_toolsets` — list toolsets.
- `mcp__unreal-mcp__describe_toolset` — list a toolset's tools and input schemas.
- `mcp__unreal-mcp__call_tool` — call one tool.

**Calling convention — get this right or every call fails:** `tool_name` takes the
**bare** tool name and `toolset_name` is a **separate** field. Passing the
fully-qualified name in `tool_name` fails with `Tool '<name>' not found`.

```
mcp__unreal-mcp__call_tool({
  tool_name:    "find_actors",
  toolset_name: "editor_toolset.toolsets.scene.SceneTools",
  arguments:    { name: "", tag: "", collision_channels: [] }
})
```

### Batching — use this for anything touching many actors

`editor_toolset.toolsets.programmatic.ProgrammaticToolset` runs a small sandboxed
Python script that glues tool calls together. Rules:

- Call `get_execution_environment` **once** before `execute_tool_script`.
- The script must define `run()` returning a `dict`.
- Call other tools with `execute_tool("<full.dotted.ToolName>", json.dumps({...}))`.
  Note: inside the script the **full dotted name IS correct** (the opposite of the
  harness convention above).
- Allowed imports only: `json`, `re`, `time`, `copy`, `math`, `datetime`.
  `unreal` is **blocked**. `collections` is **not** allowed.
- Define small helper functions at the top wrapping each `execute_tool` call.

This is the only sane way to move 1,500+ actors. A single script doing work over
a few thousand actors can take several minutes — that is expected, not a hang.

### Gotchas that will otherwise waste a whole loop

- `SceneTools.find_actors` needs `name`, `tag`, `collision_channels` (use `[]`).
  An empty `name` matches **all** actors. Matching is a case-insensitive
  **substring against the actor's label**. Returned actor names carry a
  `PersistentLevel.` prefix.
- A large `find_actors` result can exceed the response limit and get persisted to
  a file instead of returned. Batch or filter rather than dumping everything.
- `ObjectTools.set_properties` takes `values` as a **JSON string**; object refs are
  `{"refPath": "..."}`. `get_properties` raises if the actor lacks the property —
  always wrap it in `try/except BaseException`.
- `get_actor_bounds` lives in `ActorTools`, not `SceneTools`. On the Landscape it
  returns all zeros (useless) — measure the proxies instead.
- `find_actors` returns actor *names*, not file paths.

### Key actors in the level (measured, current state)

| What | Actor |
|---|---|
| Landscape (World Partition, 64 streaming proxies) | `Landscape_UAID_A85E45CFE404FBD100_1221515703` |
| Water zone | `WaterZone_UAID_00163E6E452288F802_1311752325` |
| Landscape water brush manager | `Landscape_WaterBrushManager_0` |
| Pigs (皮皮) | 30 actors, `BP_PigWander` instances |

Current level: 1,745 actors total, 1,569 of them static meshes, 64 landscape
proxies. Landscape actor transform is location `(-100800, -100800, 100)`,
scale `(100, 100, 100)`.

## Units

**1 Unreal unit = 1 cm.** Distances in this project are large — the garden already
spans kilometres (positions in the tens of thousands).

## Saving, reverting and committing

- **Nothing you do counts until you save.** Call `save_assets` (AssetTools) before
  verifying or committing. Unsaved editor state is invisible to git.
- A **running editor holds Windows file locks**. `git checkout` / `git restore` on
  a `.uasset` fails with `unable to unlink old '<path>': Invalid argument` while
  the editor is open. To revert assets on disk you must stop the editor first
  (`Stop-Process -Name UnrealEditor -Force`), revert, then relaunch it on
  `/Game/Maps/SuzhouGarden`. Save your work before doing this.
- Assets are **git-LFS** tracked. `git cat-file -p HEAD:<path>` shows only the LFS
  *pointer*, never the real content — do not grep it expecting asset internals.
  `git status` is reliable; a path that is not listed is byte-identical to HEAD.
- Commit **specific paths**. Never `git add -A` or `git add .` — the repo carries
  ~248 pre-existing untracked external-actor files that are not part of this task.

## Verifying your work

Read real numbers back from the editor after every change:

- Actor spread: collect positions and report min/max/centre per axis.
- Z sanity: every actor should sit on the terrain. Report any actor above z≈1200 —
  that means it is floating and the placement is wrong.
- Material checks: read the property back, do not assume the assignment took.

`CaptureViewport` returns base64 that is far too large to read into context —
verify numerically. A screenshot is a last resort, not evidence.

## Notes

- Editor startup map is pinned to `/Game/Maps/SuzhouGarden` in
  `Config/DefaultEngine.ini`, so a relaunch lands in the garden.
- The Claude CLI here talks to a DeepSeek proxy. The
  `[claude-code:unrecognized_model]` warning on every run is cosmetic — ignore it.
