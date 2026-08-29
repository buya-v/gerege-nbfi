#!/usr/bin/env python3
"""Two tasks reconciled IN ONE PROCESS under ONE --deadline-secs budget.

This is the shape the driver actually runs: `ready-tasks.py --reconcile --deadline-secs N`
installs the budget ONCE (set_deadline is a module global) and then walks every
in_progress task.  `refs_carrying_content`'s subset guarantee is stated per-probe; the
budget is not per-probe.

argv: <module> <fixture> <sink-branch> <sink-tid> <victim-branch> <victim-tid> <git> <deadline>
"""
import importlib.util
import json
import sys
import time

mod_path, fixture, sb, stid, vb, vtid, git_path, deadline = sys.argv[1:9]

spec = importlib.util.spec_from_file_location("rt_under_test", mod_path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
m.set_repo(fixture)
m.GIT = git_path
m.set_deadline(float(deadline))

t0 = time.monotonic()
skind, snote = m.branch_wip(sb, stid)          # the BUDGET SINK, reconciled first
t1 = time.monotonic()
vkind, vnote = m.branch_wip(vb, vtid)          # the VICTIM
t2 = time.monotonic()

va = m.reconcile_action(vkind)
print(json.dumps({
    "sink_kind": skind, "sink_wall": round(t1 - t0, 2),
    "victim_kind": vkind,
    "victim_polarity": "REFUSE" if va.startswith("REFUSE") else "demote",
    "victim_wall": round(t2 - t1, 2),
    "budget_note": getattr(m, "BUDGET_NOTE", None),
    "victim_note_tail": vnote[-300:],
    "MAX": m.MAX_REFS_PROBED,
    "MIN": getattr(m, "MIN_REFS_ALWAYS_PROBED", None),
}))
