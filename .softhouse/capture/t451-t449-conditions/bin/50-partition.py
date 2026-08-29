#!/usr/bin/env python3
"""T451 -- re-run T449's partition property on the CHANGED predicate, by EXECUTING it.

THE PROPERTY.  Every reachable state of `_branch_wip_core` must yield exactly ONE kind,
and `reconcile_action` must map that kind to exactly ONE of {REFUSE, demote}.  A state
with NO verdict is a crash or a fall-through to nothing; a state with TWO is the
seven-arm-lock defect (F-B/T343), where arms overlap and which one fires depends on the
ORDER they are written in rather than on the evidence.  T449 enumerated 256 states on
T350's bytes: 0 with none, 0 with two.  T451 widened the ancestor-of-main leg to consult
the ref store, which makes far more of that space reachable -- so the property has to be
RE-ESTABLISHED, not assumed.

HOW.  The leaf probes are stubbed and the REAL `_branch_wip_core` and the REAL
`reconcile_action` are executed.  Nothing about the predicate is re-implemented here; if
it were, this would be checking a paraphrase of the thing under test.

    branch state    (8) : git-unavailable / rev-parse-rc-3 / absent / count-unreadable /
                          commits-ahead / zero+ancestor / zero+not-ancestor /
                          zero+ancestor-unreadable
    landed evidence (4) : found+complete / found+incomplete / none+complete /
                          none+incomplete
    ref outcome     (8) : index-unavailable, plus the 2^3 of (carriers, name_only,
                          unprobed) minus the all-zero... no: all 8 of the 2^3 are kept
                          and index-unavailable makes 9 -- see the printed cardinal.

T449's own correction is kept: a stub must not hand the code a combination the real
function cannot produce (a carrier beside a None index).  The index-unavailable state
returns all-None together, exactly as `refs_carrying_content` does.

usage: 50-partition.py <red.py> <green.py>
"""
import collections, importlib.util, itertools, sys

BRANCH = [
    # (label, rev-parse result, rev-list result, merge-base rc)
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


def arms_matching(base):
    """Every arm of reconcile_action whose TEST the base satisfies, transcribed from the
    function's own tests in the order it writes them, with the polarity each arm would
    return.  Two arms matching is only a DEFECT when they disagree: then the verdict is
    decided by which one is written first rather than by the evidence, which is the
    seven-arm-lock shape.  Two arms matching that AGREE is a redundant test -- worth
    printing, not worth failing on -- and this file already had one before T451
    (`merged-unverified` satisfies both `== "merged-unverified"` and
    `startswith("merged")`, and both return REFUSE)."""
    hits = []
    if base == "stillborn-carried":
        hits.append(("stillborn-carried (==)", "REFUSE"))
    if base == "merged-unverified":
        hits.append(("merged-unverified (==)", "REFUSE"))
    if base.startswith("merged"):
        hits.append(("merged* (startswith)", "REFUSE"))
    if base.startswith("relocated"):
        hits.append(("relocated* (startswith)", "REFUSE"))
    return hits or [("fall-through demote", "demote")]


def run(path, tag, arity):
    spec = importlib.util.spec_from_file_location(tag, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    census = collections.Counter()
    none_v, two_v, errs, overlap, stale = [], [], [], [], []
    total = 0
    for (bl, rp, rl, mb), (ll, lev), (rl_lab, rres) in itertools.product(
            BRANCH, LANDED, REFS):
        total += 1

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
        m.refs_carrying_content = (lambda tid, exclude, _r=rres: _r) if arity == 5 \
            else (lambda tid, exclude, _r=rres: (_r[0], _r[1], _r[2], _r[4]))
        m._case_clause = lambda branch: ("", "")
        try:
            kind, _text = m.branch_wip("softhouse/T999-x", "T999")
            action = m.reconcile_action(kind)
        except Exception as exc:                                     # noqa: BLE001
            errs.append((bl, ll, rl_lab, "%s: %s" % (type(exc).__name__, exc)))
            none_v.append((bl, ll, rl_lab, "EXCEPTION"))
            continue
        pol = ("REFUSE" if action.startswith("REFUSE")
               else "demote" if action.startswith("demote") else None)
        if not kind or pol is None:
            none_v.append((bl, ll, rl_lab, kind, action[:50]))
            continue
        base = kind.split("/")[0]
        hits = arms_matching(base)
        # THE TRANSCRIPTION MUST NOT ROT (P-80).  `arms_matching` is a transcription of
        # reconcile_action's tests, and a transcription that silently disagrees with the
        # code is worse than none because it is believed (P-22).  The FIRST matching arm
        # is the one that fires, so its predicted polarity must equal the polarity the
        # REAL function just returned.  Any mismatch fails this instrument LOUDLY -- it
        # is what drives RED when an arm is edited without editing this file.
        if hits[0][1] != pol:
            stale.append((bl, ll, rl_lab, base, "transcription says %s, code returned %s"
                          % (hits[0][1], pol)))
        # The suffixes T312 appends must not change the action either -- reconcile_action
        # strips them, and if it ever stopped, the same state would have two verdicts.
        for suffix in ("/CASE-VARIANT", "/CASE-UNCHECKED"):
            alt = m.reconcile_action(base + suffix)
            altpol = "REFUSE" if alt.startswith("REFUSE") else "demote"
            if altpol != pol:
                two_v.append((bl, ll, rl_lab, base,
                              "bare=%s but %s=%s" % (pol, suffix, altpol)))
        if len(set(p for _, p in hits)) > 1:
            two_v.append((bl, ll, rl_lab, base, hits))     # THE DEFECT: arms disagree
        elif len(hits) > 1:
            overlap.append((base, [h for h, _ in hits]))   # redundant, agreeing
        census[(base, pol)] += 1
    return total, census, none_v, two_v, errs, overlap, stale


def arity_of(path):
    src = open(path, encoding="utf-8").read()
    return 5 if "unprobed, mentions, ref_note = refs_carrying_content" in src \
        or "unprobed, mentions, ref_note = \\" in src else 4


for label, path in (("RED   (main's bytes)", sys.argv[1]),
                    ("GREEN (this tree)", sys.argv[2])):
    ar = arity_of(path)
    total, census, none_v, two_v, errs, overlap, stale = run(path, "m_" + label[:3], ar)
    print("=" * 78)
    print("%s   %s   (refs_carrying_content arity %d)" % (label, path, ar))
    print("=" * 78)
    print("states enumerated             : %d   (%d branch x %d landed x %d ref)"
          % (total, len(BRANCH), len(LANDED), len(REFS)))
    print("states with NO usable verdict : %d" % len(none_v))
    for x in none_v[:12]:
        print("      %s" % (x,))
    print("states with TWO verdicts      : %d   <- arms match AND DISAGREE (the defect)"
          % len(two_v))
    for x in two_v[:12]:
        print("      %s" % (x,))
    print("states w/ redundant agreeing arms: %d   (pre-existing; both return REFUSE)"
          % len(overlap))
    seen = set()
    for base, hits in overlap:
        if base not in seen:
            seen.add(base)
            print("      %-20s %s" % (base, " + ".join(hits)))
    print("arm-transcription MISMATCHES  : %d   <- this file disagrees with the code"
          % len(stale))
    for x in stale[:6]:
        print("      %s" % (x,))
    print("exceptions raised             : %d" % len(errs))
    for x in errs[:12]:
        print("      %s" % (x,))
    bykind = collections.defaultdict(set)
    for (k, p) in census:
        bykind[k].add(p)
    print("kind -> polarity (a kind with two polarities is the defect):")
    for k in sorted(bykind):
        pols = sorted(bykind[k])
        n = sum(v for (kk, _), v in census.items() if kk == k)
        print("      %-20s %-14s %4d states%s"
              % (k, "/".join(pols), n,
                 "   <== TWO POLARITIES" if len(pols) > 1 else ""))
    print("      %-20s %-14s %4d states"
          % ("TOTAL", "", sum(census.values())))
    print()
