#!/usr/bin/env python3
"""T456 -- FAILURE-DIRECTION check, PER STATE, not per aggregate.

T451 claims: "the change makes exactly two verdicts more conservative and none less --
every transition is demote->REFUSE; nothing that refused before demotes now."  The 288-
state partition transcript only prints COUNTS PER KIND, which cannot distinguish
"three states moved demote->REFUSE" from "four moved that way and one moved back".  This
instrument pairs the SAME state in RED and GREEN and reports every polarity transition
by direction.  REFUSE->demote is the direction that destroys merged work (T324/T330).

It fails LOUDLY rather than printing a zero it did not measure: if either leg raises, or
if the two legs do not enumerate the same state keys, it says so and exits non-zero.

usage: 50-direction.py <red.py> <green.py>
"""
import collections
import importlib.util
import itertools
import sys

BRANCH = [
    ("git-unavailable",      (None, "", "no git"),  None,            None),
    ("rev-parse-rc-3",       (3, "", "boom"),       None,            None),
    ("absent",               (1, "", ""),           None,            None),
    ("count-unreadable",     (0, "abc123def", ""),  (128, "", "e"),  None),
    ("commits-ahead",        (0, "abc123def", ""),  (0, "4", ""),    None),
    ("zero-ancestor",        (0, "abc123def", ""),  (0, "0", ""),    0),
    ("zero-not-ancestor",    (0, "abc123def", ""),  (0, "0", ""),    1),
    ("zero-ancestor-unread", (0, "abc123def", ""),  (0, "0", ""),    129),
]
LANDED = [
    ("found+complete",   (["ev"], True,  "n")),
    ("found+incomplete", (["ev"], False, "n")),
    ("none+complete",    ([],     True,  "n")),
    ("none+incomplete",  ([],     False, "n")),
]
REFS = [("index-unavailable", (None, None, None, None, "no ref index"))]
for c, n, u in itertools.product((0, 1), repeat=3):
    REFS.append(("carr%d name%d unpr%d" % (c, n, u),
                 ([("refs/heads/x", ["path p"])] if c else [],
                  ["refs/heads/y"] if n else [],
                  ["refs/heads/z"] if u else [],
                  [("refs/heads/y", ["a/t999-x/f"])] if n else [],
                  "ref note")))


def arity_of(path):
    src = open(path, encoding="utf-8").read()
    return 5 if "unprobed, mentions, ref_note" in src else 4


def sweep(path, tag):
    spec = importlib.util.spec_from_file_location(tag, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    if getattr(m, "branch_sweep", "missing") is None:
        raise SystemExit("ABORT: %s could not import branch_sweep -- every verdict below "
                         "would be an artefact of MY staging, not of the code. Put "
                         "branch_sweep.py beside %s." % (tag, path))
    ar = arity_of(path)
    res = {}
    for (bl, rp, rl, mb), (ll, lev), (rlab, rres) in itertools.product(
            BRANCH, LANDED, REFS):
        def fake_run(argv, timeout=20, _rp=rp, _rl=rl, _mb=mb):
            if "rev-parse" in argv:
                return _rp
            if "rev-list" in argv:
                return _rl if _rl is not None else (128, "", "unset")
            if "merge-base" in argv:
                return (_mb if _mb is not None else 128, "", "unset")
            return (0, "", "")
        m._run = fake_run
        m.landed_evidence = lambda tid, _e=lev: _e
        m.refs_carrying_content = (lambda tid, exclude, _r=rres: _r) if ar == 5 \
            else (lambda tid, exclude, _r=rres: (_r[0], _r[1], _r[2], _r[4]))
        m._case_clause = lambda branch: ("", "")
        key = (bl, ll, rlab)
        try:
            kind, _t = m.branch_wip("softhouse/T999-x", "T999")
            action = m.reconcile_action(kind)
        except Exception as exc:                                     # noqa: BLE001
            res[key] = ("EXCEPTION", "%s: %s" % (type(exc).__name__, exc))
            continue
        base = (kind or "").split("/")[0]
        pol = ("REFUSE" if action.startswith("REFUSE")
               else "demote" if action.startswith("demote") else "NONE")
        res[key] = (base, pol)
    return res, ar


red, ar_r = sweep(sys.argv[1], "m_red")
green, ar_g = sweep(sys.argv[2], "m_green")
print("RED   %s   (arity %d)  states=%d" % (sys.argv[1], ar_r, len(red)))
print("GREEN %s   (arity %d)  states=%d" % (sys.argv[2], ar_g, len(green)))
if set(red) != set(green):
    print("ABORT: the two legs did not enumerate the same states.")
    sys.exit(2)
if not red:
    print("ABORT: zero states enumerated. A partition over nothing proves nothing.")
    sys.exit(91)

bad = [k for k, v in list(red.items()) + list(green.items()) if v[0] == "EXCEPTION"]
print("states raising           : %d %s" % (len(bad), bad[:4]))
print("states with polarity NONE: %d"
      % sum(1 for v in list(red.values()) + list(green.values()) if v[1] == "NONE"))

trans = collections.Counter()
worse, better = [], []
for k in sorted(red):
    rk, rp = red[k]
    gk, gp = green[k]
    trans[(rp, gp)] += 1
    if rp == "REFUSE" and gp == "demote":
        worse.append((k, rk, gk))
    elif rp == "demote" and gp == "REFUSE":
        better.append((k, rk, gk))

print()
print("POLARITY TRANSITIONS over all %d states:" % len(red))
for (a, b), n in sorted(trans.items()):
    mark = ""
    if a == "REFUSE" and b == "demote":
        mark = "   <== THE DESTRUCTIVE DIRECTION (T324/T330)"
    if a == "demote" and b == "REFUSE":
        mark = "   <== more conservative"
    print("   %-8s -> %-8s : %3d%s" % (a, b, n, mark))

print()
print("REFUSE -> demote (work-destroying) : %d" % len(worse))
for k, rk, gk in worse:
    print("   %s   %s -> %s" % (k, rk, gk))
print("demote -> REFUSE (conservative)    : %d" % len(better))
for k, rk, gk in better:
    print("   %s   %s -> %s" % (k, rk, gk))

print()
print("KIND REDISTRIBUTION (same state, kind changed but polarity may not have):")
kt = collections.Counter()
for k in sorted(red):
    if red[k][0] != green[k][0]:
        kt[(red[k][0], green[k][0])] += 1
for (a, b), n in sorted(kt.items()):
    print("   %-20s -> %-20s : %3d" % (a, b, n))
print()
rc = collections.Counter(v[0] for v in red.values())
gc = collections.Counter(v[0] for v in green.values())
print("RED   kind census: %s  total=%d" % (dict(sorted(rc.items())), sum(rc.values())))
print("GREEN kind census: %s  total=%d" % (dict(sorted(gc.items())), sum(gc.values())))
sys.exit(1 if worse or bad else 0)
