#!/usr/bin/env python3
"""T449 -- STATE-SPACE ENUMERATION OF T350's VERDICT LATTICE.

The brief asks whether the rule PARTITIONS: every state must yield exactly one
verdict, and no two states that carry the same evidence may yield two verdicts.
This RUNS the predicates over the cross product rather than reading them.

Dimensions (the brief's, made executable):
  branch_state   : absent | exists-0-ahead-ancestor | exists-0-ahead-not-ancestor
                 | exists-ahead | exists-ancestor-unanswerable | rev-parse-failed
  main_content   : the (evidence, complete) pair landed_evidence() can return
                     found      -> (["x"], True)
                     found_part -> (["x"], False)     evidence found, a source failed
                     none       -> ([],    True)      every source ran, all empty
                     unrun      -> ([],    False)     a source did not run
  ref_state      : the (carriers, name_only, unprobed) triple refs_carrying_content()
                   can return -- enumerated for REACHABILITY in pass 2 below.

`_branch_wip_core` is the single entry point; `reconcile_action` is the single place
a kind becomes an action.  Both are called for real; only the two leaf probes are
stubbed, so every branch of the real control flow is exercised.
"""
import importlib.util, itertools, sys, collections

MOD = sys.argv[1] if len(sys.argv) > 1 else "/tmp/t449/mods/rt_t350.py"
spec = importlib.util.spec_from_file_location("rt", MOD)
rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)

# ---------------------------------------------------------------- git stubbing -----
BRANCH_STATES = {
    #                       rev-parse rc, sha, ahead-count, merge-base rc
    "absent":                     (1, "",          None, None),
    "rev-parse-failed":           (None, "",       None, None),
    "rev-parse-rc2":              (2, "",          None, None),
    "exists-ahead":               (0, "a" * 40,    "3",  None),
    "exists-0ahead-ancestor":     (0, "a" * 40,    "0",  0),
    "exists-0ahead-not-ancestor": (0, "a" * 40,    "0",  1),
    "exists-0ahead-mb-unanswer":  (0, "a" * 40,    "0",  128),
    "exists-count-unreadable":    (0, "a" * 40,    None, None),
}

MAIN_CONTENT = {
    "found":      (["commit deadbeef on main"], True),
    "found_part": (["commit deadbeef on main"], False),
    "none":       ([], True),
    "unrun":      ([], False),
}

# (carriers, name_only, unprobed) -- reachability is checked in PASS 2.
REF_STATES = {
    "refindex-failed":     (None, None, None),
    "no-ref-names-id":     ([], [], []),
    "name-only":           ([], ["softhouse/rescued-tX-20260828"], []),
    "carrier":             ([("softhouse/tX-alt", ["path p"])], [], []),
    "carrier+nameonly":    ([("softhouse/tX-alt", ["path p"])], ["softhouse/r"], []),
    "carrier+unprobed":    ([("softhouse/tX-alt", ["path p"])], [], ["softhouse/u"]),
    "unprobed-only":       ([], [], ["softhouse/u"]),
    "nameonly+unprobed":   ([], ["softhouse/r"], ["softhouse/u"]),
}


def install(bs, mc, rs):
    rc, sha, ahead, mbrc = BRANCH_STATES[bs]

    def fake_run(argv, timeout=20):
        a = argv[1:]
        if a[:1] == ["rev-parse"]:
            return (rc, sha, "stub")
        if a[:1] == ["rev-list"]:
            return (0, ahead, "") if ahead is not None else (None, "", "stub failure")
        if a[:2] == ["merge-base", "--is-ancestor"]:
            return (mbrc, "", "stub") if mbrc is not None else (None, "", "stub")
        raise AssertionError("unexpected git call in enumeration: %r" % (argv,))

    rt._run = fake_run
    rt.landed_evidence = lambda tid: (MAIN_CONTENT[mc][0], MAIN_CONTENT[mc][1], "stub")
    rt.refs_carrying_content = lambda tid, excl: REF_STATES[rs] + ("stub",)
    # T312's case-variant suffix probe also shells out; neutralise it.
    rt.case_variants = lambda b: (set(), "stub")


print("=" * 96)
print("PASS 1 -- FULL CROSS PRODUCT  branch_state x main_content x ref_state")
print("=" * 96)
rows = []
noverdict = []
for bs, mc, rs in itertools.product(BRANCH_STATES, MAIN_CONTENT, REF_STATES):
    install(bs, mc, rs)
    try:
        kind, text = rt._branch_wip_core("softhouse/TX-b", "TX")
    except Exception as exc:                                   # a state with NO verdict
        noverdict.append((bs, mc, rs, "EXCEPTION %r" % (exc,)))
        continue
    if kind is None or kind == "":
        noverdict.append((bs, mc, rs, "EMPTY KIND"))
        continue
    act = rt.reconcile_action(kind)
    pol = "REFUSE" if act.startswith("REFUSE") else ("demote" if act.startswith("demote")
                                                    else "??? " + act[:30])
    if pol.startswith("???"):
        noverdict.append((bs, mc, rs, "ACTION IS NEITHER REFUSE NOR demote: %r" % act))
    rows.append((bs, mc, rs, kind, pol))

print("states enumerated: %d" % (len(rows) + len(noverdict)))
print("states with NO verdict / an un-actionable verdict: %d" % len(noverdict))
for r in noverdict:
    print("   !!", r)

print("\n--- kind x polarity table ---")
for (k, p), n in sorted(collections.Counter((r[3], r[4]) for r in rows).items()):
    print("  %-20s %-7s %4d" % (k, p, n))

print("\n--- FULL TABLE (branch_state, main_content, ref_state) -> kind / action ---")
for r in rows:
    print("  %-28s %-11s %-19s -> %-18s %s" % r)

# ------------------------------------------------------------------------------------
print()
print("=" * 96)
print("PASS 2 -- DOES THE SAME EVIDENCE EVER GET TWO ANSWERS?")
print("=" * 96)
print("The evidence a reader has in hand is: is there content bearing this id ON MAIN,")
print("and is there a live ref CARRYING content for it.  Group the enumerated states by")
print("that pair alone and report every group that contains BOTH polarities.")


def carries(rs):
    return bool(REF_STATES[rs][0])


def onmain(mc):
    return bool(MAIN_CONTENT[mc][0])


groups = collections.defaultdict(set)
detail = collections.defaultdict(list)
for bs, mc, rs, kind, pol in rows:
    key = (onmain(mc), carries(rs))
    groups[key].add(pol)
    detail[key].append((bs, mc, rs, kind, pol))

split = 0
for key in sorted(groups):
    tag = "content-on-main=%s ref-carries-content=%s" % key
    if len(groups[key]) > 1:
        split += 1
        print("\n  !! SPLIT VERDICT: %s -> %s" % (tag, sorted(groups[key])))
        seen = set()
        for bs, mc, rs, kind, pol in detail[key]:
            if (bs, pol) in seen:
                continue
            seen.add((bs, pol))
            print("       %-28s %-11s %-19s -> %-18s %s" % (bs, mc, rs, kind, pol))
    else:
        print("  ok  %-52s -> %s" % (tag, sorted(groups[key])[0]))
print("\ngroups whose polarity depends on something OTHER than the evidence: %d" % split)
