#!/usr/bin/env python3
"""T449 -- PASSES 3 and 4 of the state-space enumeration.

PASS 3 restricts to states where git ANSWERED cleanly, so any surviving split in
polarity is the RULE's and not the instrument's.
PASS 4 asks, for each branch state, whether the verdict is sensitive to the REF
evidence at all.
"""
import importlib.util, itertools, sys, collections

MOD = sys.argv[1] if len(sys.argv) > 1 else "/tmp/t449/mods/rt_t350.py"
spec = importlib.util.spec_from_file_location("rt", MOD)
rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)
print("module: %s   branch_sweep imported: %s" % (MOD, rt.branch_sweep is not None))

BRANCH_STATES = {
    "absent":                     (1, "",       None, None),
    "rev-parse-failed":           (None, "",    None, None),
    "rev-parse-rc2":              (2, "",       None, None),
    "exists-ahead":               (0, "a" * 40, "3",  None),
    "exists-0ahead-ancestor":     (0, "a" * 40, "0",  0),
    "exists-0ahead-not-ancestor": (0, "a" * 40, "0",  1),
    "exists-0ahead-mb-unanswer":  (0, "a" * 40, "0",  128),
    "exists-count-unreadable":    (0, "a" * 40, None, None),
}
MAIN_CONTENT = {
    "found":      (["commit deadbeef on main"], True),
    "found_part": (["commit deadbeef on main"], False),
    "none":       ([], True),
    "unrun":      ([], False),
}
REF_STATES = {
    "refindex-failed":   (None, None, None),
    "no-ref-names-id":   ([], [], []),
    "name-only":         ([], ["refs/heads/softhouse/rescued-tx-1"], []),
    "carrier":           ([("refs/heads/softhouse/tx-alt", ["path p"])], [], []),
    "carrier+nameonly":  ([("refs/heads/softhouse/tx-alt", ["path p"])],
                          ["refs/heads/softhouse/r"], []),
    "carrier+unprobed":  ([("refs/heads/softhouse/tx-alt", ["path p"])], [],
                          ["refs/heads/softhouse/u"]),
    "unprobed-only":     ([], [], ["refs/heads/softhouse/u"]),
    "nameonly+unprobed": ([], ["refs/heads/softhouse/r"], ["refs/heads/softhouse/u"]),
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
        raise AssertionError("unexpected git call: %r" % (argv,))

    rt._run = fake_run
    rt.landed_evidence = lambda tid: (MAIN_CONTENT[mc][0], MAIN_CONTENT[mc][1], "stub")
    rt.refs_carrying_content = lambda tid, excl: REF_STATES[rs] + ("stub",)
    rt.case_variants = lambda b: (set(), "stub")


rows, bad = [], []
for bs, mc, rs in itertools.product(BRANCH_STATES, MAIN_CONTENT, REF_STATES):
    install(bs, mc, rs)
    try:
        kind, _ = rt._branch_wip_core("softhouse/TX-b", "TX")
    except Exception as exc:
        bad.append((bs, mc, rs, repr(exc)))
        continue
    act = rt.reconcile_action(kind)
    pol = "REFUSE" if act.startswith("REFUSE") else (
        "demote" if act.startswith("demote") else "NEITHER:" + act[:40])
    if pol.startswith("NEITHER"):
        bad.append((bs, mc, rs, pol))
    rows.append((bs, mc, rs, kind, pol))

print("states enumerated: %d ; states with NO usable verdict: %d"
      % (len(rows) + len(bad), len(bad)))
for b in bad:
    print("   !!", b)
print("\n--- kind x polarity ---")
for (k, p), n in sorted(collections.Counter((r[3], r[4]) for r in rows).items()):
    print("  %-20s %-7s %4d" % (k, p, n))


def carries(rs):
    return bool(REF_STATES[rs][0])


def onmain(mc):
    return bool(MAIN_CONTENT[mc][0])


print()
print("=" * 92)
print("PASS 3 -- ONLY STATES WHERE GIT ANSWERED CLEANLY")
print("=" * 92)
CLEAN = {"absent", "exists-ahead", "exists-0ahead-ancestor", "exists-0ahead-not-ancestor"}
g2, d2 = collections.defaultdict(set), collections.defaultdict(list)
for bs, mc, rs, kind, pol in rows:
    if bs not in CLEAN:
        continue
    g2[(onmain(mc), carries(rs))].add(pol)
    d2[(onmain(mc), carries(rs))].append((bs, mc, rs, kind, pol))
n = 0
for key in sorted(g2):
    tag = "content-on-main=%-5s ref-carries-content=%s" % key
    if len(g2[key]) > 1:
        n += 1
        print("\n  !! SPLIT: %s -> %s" % (tag, sorted(g2[key])))
        seen = set()
        for bs, mc, rs, kind, pol in d2[key]:
            if (bs, mc, pol) in seen:
                continue
            seen.add((bs, mc, pol))
            print("       %-28s %-11s %-19s -> %-18s %s" % (bs, mc, rs, kind, pol))
    else:
        print("  ok  %s -> %s" % (tag, sorted(g2[key])[0]))
print("\nRULE-LEVEL splits: %d" % n)

print()
print("=" * 92)
print("PASS 4 -- IS THE REF EVIDENCE CONSULTED AT ALL WHEN THE BRANCH EXISTS?")
print("=" * 92)
for bs in ("absent", "exists-ahead", "exists-0ahead-ancestor",
           "exists-0ahead-not-ancestor"):
    for mc in MAIN_CONTENT:
        kinds = sorted({(r[3], r[4]) for r in rows if r[0] == bs and r[1] == mc})
        print("  %-28s main=%-11s verdicts over ALL 8 ref states: %s" % (bs, mc, kinds))
