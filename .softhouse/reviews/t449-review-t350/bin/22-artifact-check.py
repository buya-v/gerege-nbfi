#!/usr/bin/env python3
"""T449 -- prove the 7 AttributeError states in pass 1 were MY artifact, not a defect.

Pass 1 loaded the module from a directory with no branch_sweep.py beside it, so
`branch_sweep` was None while my stub still handed _absent_verdict a non-None
`carriers`/`name_only`.  In the REAL code that combination cannot occur: branch_sweep
None => ref_index None => refs_naming None => refs_carrying_content (None, None, None),
and `_absent_verdict` returns `indeterminate` on `carriers is None` BEFORE it ever calls
branch_sweep.short().  Measured, not reasoned.
"""
import importlib.util, sys

spec = importlib.util.spec_from_file_location("rt", "/tmp/t449/mods/rt_t350.py")
rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)
print("branch_sweep imported (with it beside the module): %s" % (rt.branch_sweep is not None))

# Force the failure mode the artifact simulated.
rt.branch_sweep = None
rt.BRANCH_SWEEP_ERR = "simulated ImportError"
rt._REF_INDEX = ("uncached", None)
idx, note = rt.ref_index()
print("ref_index()            -> %r" % (idx,))
print("  note: %s" % note[:120])
refs, note2 = rt.refs_naming("T339", None)
print("refs_naming('T339')    -> %r" % (refs,))
c, n, u, note3 = rt.refs_carrying_content("T339", None)
print("refs_carrying_content  -> carriers=%r name_only=%r unprobed=%r" % (c, n, u))

rt._run = lambda argv, timeout=20: (1, "", "stub")   # branch absent
rt.landed_evidence = lambda tid: ([], True, "stub")  # every main probe ran, empty
kind, text = rt._absent_verdict("softhouse/T339-x", "T339")
print("\n_absent_verdict with branch_sweep=None -> kind=%r" % kind)
print("action: %s" % rt.reconcile_action(kind)[:90])
print("\nNO AttributeError: the real code returns before branch_sweep.short() is reached.")
