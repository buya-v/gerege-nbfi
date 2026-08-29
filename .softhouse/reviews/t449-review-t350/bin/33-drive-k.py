#!/usr/bin/env python3
"""T449 -- CASE K driven RED and GREEN."""
import importlib.util, sys

REPO = "/tmp/t449/fixture"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    m.set_repo(REPO)
    return m


M = load("rt_main", "/tmp/t449/mods/rt_main.py")
T = load("rt_t350", "/tmp/t449/mods/rt_t350.py")

for label, branch, tid in [
    ("K/  T945's genuine work is under T944's condition dir; sweep-rescued;"
     " recorded branch DELETED", "softhouse/T945-t944-conditions", "T945"),
    ("K2/ the SAME ref, but the commit subject names the id",
     "softhouse/T946-t944-conditions", "T946"),
]:
    km, tm = M.branch_wip(branch, tid)
    kt, tt = T.branch_wip(branch, tid)
    am = "REFUSE" if M.reconcile_action(km).startswith("REFUSE") else "DEMOTE"
    at = "REFUSE" if T.reconcile_action(kt).startswith("REFUSE") else "DEMOTE"
    print("\n%s\n  RED  %-16s %s\n  GREEN %-15s %s%s"
          % (label, km, am, kt, at, "   <== CHANGED" if am != at else ""))
    print("  GREEN text: %s" % tt[:900])

c, n, u, note = T.refs_carrying_content("T945", "softhouse/T945-t944-conditions")
print("\nrefs_carrying_content('T945'):")
print("  carriers = %s" % [r for r, _ in (c or [])])
print("  name_only= %s" % n)
print("  unprobed = %s" % u)
print("  note     = %s" % note)
