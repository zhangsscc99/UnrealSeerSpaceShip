# -*- coding: utf-8 -*-
"""Project Python startup: watch for Saved/run_rock_blocks.flag and execute import/sink."""

from __future__ import annotations

import os
import unreal


def _project_root():
    # Content/../ 
    return os.path.normpath(os.path.join(unreal.Paths.project_content_dir(), ".."))


FLAG = os.path.join(_project_root(), "Saved", "run_rock_blocks.flag")
SCRIPT = os.path.join(_project_root(), "Scripts", "ue_sink_rock_blocks_body.py")
_handle = None


def _tick(delta_time):
    global _handle
    if not os.path.isfile(FLAG):
        return True
    try:
        os.remove(FLAG)
    except OSError:
        return True
    unreal.log("RockBlocks: flag detected, running sink script...")
    if not os.path.isfile(SCRIPT):
        unreal.log_error("RockBlocks: missing " + SCRIPT)
        return True
    with open(SCRIPT, "r", encoding="utf-8") as f:
        code = f.read()
    try:
        exec(compile(code, SCRIPT, "exec"), {"__name__": "__rock_blocks__"})
        unreal.log("RockBlocks: finished")
    except Exception as exc:
        unreal.log_error("RockBlocks failed: %s" % exc)
    return True


def _register():
    global _handle
    _handle = unreal.register_slate_post_tick_callback(_tick)
    unreal.log("RockBlocks: watching for " + FLAG)


_register()
