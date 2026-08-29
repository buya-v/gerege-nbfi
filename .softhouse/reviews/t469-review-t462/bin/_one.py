#!/usr/bin/env python3
"""Drive ONE (variant, host, case) cell and print JSON.

Fresh interpreter per cell, so every module-level cache (_MAINTREE, _REF_INDEX,
_IDPAT, DEADLINE) starts cold.  Nothing in the module under test is monkeypatched
except `repo` (via its own public set_repo) and `GIT` (pointed at the host wrapper) --
the predicate's bytes are exactly the staged variant's.
"""
import importlib.util
import json
import os
import sys
import time

mod_path, fixture, branch, tid, git_path, deadline = sys.argv[1:7]

spec = importlib.util.spec_from_file_location("rt_under_test", mod_path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

m.set_repo(fixture)
m.GIT = git_path
if float(deadline) > 0:
    m.set_deadline(float(deadline))

t0 = time.monotonic()
kind, note = m.branch_wip(branch if branch != "-" else "", tid)
wall = time.monotonic() - t0
action = m.reconcile_action(kind)
print(json.dumps({
    "kind": kind,
    "polarity": "REFUSE" if action.startswith("REFUSE") else "demote",
    "action": action[:60],
    "wall": round(wall, 2),
    "note_tail": note[-400:],
    "MIN": getattr(m, "MIN_REFS_ALWAYS_PROBED", None),
    "MAX": m.MAX_REFS_PROBED,
    "CEIL": getattr(m, "REF_PROBE_SECONDS", None),
}))
