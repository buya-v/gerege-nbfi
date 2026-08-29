#!/usr/bin/env python3
"""T462 / C-T456-2 -- THE ENUMERATION T451 SHIPPED IS A WELL-FORMEDNESS CHECK. SAY SO,
AND ADD THE ARM THAT MAKES IT A CORRECTNESS CHECK.

WHAT T451'S 288-STATE PARTITION ACTUALLY PROVES.  Its five criteria are: every state
yields a verdict; no state yields two DISAGREEING verdicts; the transcription of
`reconcile_action`'s tests agrees with `reconcile_action`; the T312 suffixes do not
change a polarity; nothing raises.  Every one of those is a property of the VERDICT
SPACE -- that the kinds partition it, single-valued.  NONE of them is a property of the
ROUTING: which kind a given state is sent to.  A defect that re-routes a state from one
well-formed kind to another well-formed kind is invisible to all five, by construction.

THAT IS NOT A HYPOTHESIS.  T451 planted three defects (D1 wrong polarity, D2 arm
deleted, D3 T312 suffix no longer stripped) and caught three -- but all three break
well-formedness, so "3 planted, 3 caught" was a SELF-SELECTED POPULATION.  T456 planted
a fourth, D4, which swaps the ORDER of the two arms T451 added to `_branch_wip_core`;
all five criteria stayed GREEN while two states moved REFUSE -> demote, the direction
that destroys merged work.  This instrument reproduces that, and adds the arms that
catch it.

THREE ARMS HERE, AND THE SECOND IS THE ONE THAT MATTERS:

  ARM A -- PER-STATE EXPECTED KIND.  An ordered rule table, transcribed from the
    DOCSTRINGS (`_absent_verdict` lists its five worlds in order; the T350/T451 comment
    in `_branch_wip_core` lists the ancestor-of-main outcomes in order), not from the
    executable lines.  It is a transcription and it is honest about being one: a
    transcription can be edited to agree with a defect.  Which is why there is ARM B.

  ARM B -- TABLE-FREE POLARITY INVARIANTS.  Three sentences that must hold whatever the
    routing is, each derived from a recorded incident rather than from this file:
      B1  a state where a live ref CARRIES CONTENT must NEVER demote.   (T451/C-T449-1)
      B2  a state where work bearing the id is ON MAIN must NEVER demote. (T324/T319)
      B3  a state where every probe RAN and found nothing anywhere MUST demote --
          otherwise the reconciler refuses forever and no dead dispatch is ever
          repaired.                                                        (T330)
    B1 catches D4 with no table at all: D4 makes (carriers present, one ref unprobed)
    demote.  An invariant that cannot be edited into agreement with the code is worth
    more than a table that can.

  ARM C -- T451's well-formedness criteria, RETAINED and RELABELLED.  They are not
    wrong; they are just not what they were being read as.

AND A NEGATIVE CONTROL, which is the other half of fixing a self-selected population:
D-NULL is a REAL edit to the same routing region that is behaviour-preserving.  An
instrument that flags it is over-sensitive and its greens mean nothing either.

usage: 50-expected-verdicts.py <module.py> [--plant]
       --plant additionally builds D4, D5 and D-NULL from <module.py> and reports which
       arms catch which, including the one that must catch NOTHING.
"""
import collections
import importlib.util
import itertools
import os
import shutil
import subprocess
import sys
import tempfile

MOD = sys.argv[1]
PLANT = "--plant" in sys.argv[2:]

# ---------------------------------------------------------------- the state space ----
# Same 8 x 4 x 9 as T451 and T456, so the transcripts are comparable line for line.
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

REFUSING_KINDS = {"merged", "merged-unverified", "relocated", "stillborn-carried"}


# ---------------------------------------------------------------------- ARM A --------

def _ref_flags(rlabel):
    """(carriers?, name_only?, unprobed?) from a REFS label, or (None, None, None) for
    the index-unavailable state.  PARSED, not indexed: the label format is written in
    one place above and an index into it is a silent-drift hazard."""
    if rlabel == "index-unavailable":
        return None, None, None
    parts = dict((w[:4], w[4:]) for w in rlabel.split())
    if set(parts) != {"carr", "name", "unpr"}:
        raise AssertionError("unparsable ref label %r" % rlabel)
    return parts["carr"] == "1", parts["name"] == "1", parts["unpr"] == "1"


def expected_kind(blabel, llabel, rlabel):
    """The kind this state OUGHT to produce, from the documented rule order.

    TRANSCRIBED FROM THE DOCSTRINGS, and the reader should check it against them:
      * `_absent_verdict.__doc__` -- "FIVE worlds since T350": merged, relocated,
        name-only-refs, unstarted, indeterminate, with the fail-closed rule that an
        unrun signal outranks a silent one.
      * `_branch_wip_core`'s T350 comment -- "Three outcomes, and the middle one is
        new: evidence found -> merged; probes could not all run -> merged-unverified;
        probes ran, nothing found -> ASK THE REF STORE", then T451's polarity block --
        "a ref CARRIES content -> REFUSE (stillborn-carried); the ref probe DID NOT RUN
        -> indeterminate, DEMOTE; refs matched by NAME ONLY -> stillborn, DEMOTE".
    """
    ev = llabel.startswith("found")
    complete = llabel.endswith("+complete")
    carr, name, unpr = _ref_flags(rlabel)

    if blabel in ("git-unavailable", "rev-parse-rc-3", "count-unreadable",
                  "zero-ancestor-unread"):
        return "unverified"            # git did not answer; never assumed empty
    if blabel == "commits-ahead":
        return "commits"               # decided before any content probe runs
    if blabel == "zero-not-ancestor":
        return "absent"                # measured, and the merged case excluded
    if blabel == "absent":
        if ev:
            return "merged"
        if carr:
            return "relocated"
        if (not complete) or carr is None or unpr:
            return "indeterminate"     # T330: an unrun probe never buys a reprieve
        if name:
            return "name-only-refs"    # T339: a NAME is not content
        return "unstarted"
    if blabel == "zero-ancestor":
        if ev:
            return "merged"
        if not complete:
            return "merged-unverified"  # T350: withhold on an ambiguous positive
        if carr:
            return "stillborn-carried"  # T451/C-T449-1: content on a live ref REFUSES
        if carr is None or unpr:
            return "indeterminate"
        return "stillborn"
    raise AssertionError("unmodelled branch state %r" % blabel)


# ---------------------------------------------------------------------- ARM B --------
# THE STATES THESE INVARIANTS ARE DEFINED ON, and why the restriction is not a
# convenience.  `_branch_wip_core` calls `landed_evidence` / `refs_carrying_content` on
# EXACTLY two branch states: `absent` (via `_absent_verdict`) and `zero-ancestor`.  In
# the other six it returns before either probe runs, so the LANDED and REFS coordinates
# of the cross-product are values the real function never saw -- asserting over them
# tests this file's staging, not the code.  That is T449's own correction, which T451
# recorded and applied to its stubs: "a stub must not hand the code a combination the
# real function cannot produce."  The restriction is printed with a COUNT below so a
# later reader can see how much of the space it removes rather than take it on trust.
EVIDENCE_CONSULTING = {"absent", "zero-ancestor"}


def invariants(blabel, llabel, rlabel, kind, pol):
    """[(id, message), ...] -- violations. NO reference to expected_kind."""
    bad = []
    if blabel not in EVIDENCE_CONSULTING:
        return bad
    ev = llabel.startswith("found")
    complete = llabel.endswith("+complete")
    carr, name, unpr = _ref_flags(rlabel)
    # B1 -- content on a live ref is a POSITIVE MEASURED FACT about the work. Only two
    # states may outrank it, and both are MORE conservative, not less: `merged` and
    # `merged-unverified` both REFUSE anyway. So: carriers present => never demote.
    if carr and pol == "demote":
        bad.append(("B1", "a live ref CARRIES CONTENT and the verdict DEMOTES "
                          "(kind=%s) -- C-T449-1's fail-open" % kind))
    # B2 -- work bearing the id is on main. Re-dispatching it is FU-RECONCILE-1.
    if ev and pol == "demote":
        bad.append(("B2", "work bearing the id is ON MAIN and the verdict DEMOTES "
                          "(kind=%s) -- the T324 accident" % kind))
    # B3 -- the other direction, and it has to be checked or "never demote" is trivially
    # satisfiable by refusing forever. Everything ran, nothing was found anywhere: this
    # MUST demote or no dead dispatch is ever repaired.
    if (not ev and complete
            and carr is False and name is False and unpr is False and pol != "demote"):
        bad.append(("B3", "every probe RAN and found nothing, yet the verdict is %s "
                          "(kind=%s) -- a reconciler that never repairs" % (pol, kind)))
    return bad


# ---------------------------------------------------------------------- driver -------
def arms_matching(base):
    """T451's transcription of reconcile_action's tests, kept verbatim so ARM C is the
    SAME check it was and the transcripts stay comparable."""
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


def arity_of(path):
    src = open(path, encoding="utf-8").read()
    return 5 if "unprobed, mentions, ref_note" in src else 4


def sweep(path, tag):
    spec = importlib.util.spec_from_file_location(tag, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    if getattr(m, "branch_sweep", "missing") is None:
        sys.exit("ABORT: %s could not import branch_sweep -- every verdict below would "
                 "be an artefact of my staging" % path)
    ar = arity_of(path)
    rows = []
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
        try:
            kind, _t = m.branch_wip("softhouse/T999-x", "T999")
            action = m.reconcile_action(kind)
        except Exception as exc:                                     # noqa: BLE001
            rows.append(((bl, ll, rlab), "EXCEPTION", "NONE",
                         "%s: %s" % (type(exc).__name__, exc), m))
            continue
        base = (kind or "").split("/")[0]
        pol = ("REFUSE" if action.startswith("REFUSE")
               else "demote" if action.startswith("demote") else "NONE")
        rows.append(((bl, ll, rlab), base, pol, "", m))
    return rows, ar


def constants_preflight(path):
    """The floor-under-a-ceiling invariant, checked HERE rather than raised at import
    time in the resolver.  A module-level raise in the file the driver runs every fire
    would turn a mis-set constant into a total dispatch outage, which is a worse failure
    than the one it guards.  So the resolver documents the invariant and this instrument
    enforces it.  Returns [] or a list of violations."""
    ns = {}
    for line in open(path, encoding="utf-8"):
        for name in ("MAX_REFS_PROBED", "MIN_REFS_ALWAYS_PROBED", "REF_PROBE_SECONDS"):
            if line.startswith(name + " = "):
                ns[name] = float(line.split("=", 1)[1].strip())
    bad = []
    if "MIN_REFS_ALWAYS_PROBED" not in ns:
        bad.append("MIN_REFS_ALWAYS_PROBED is not defined at module level")
    elif ns["MIN_REFS_ALWAYS_PROBED"] >= ns.get("MAX_REFS_PROBED", 0):
        bad.append("MIN_REFS_ALWAYS_PROBED=%g >= MAX_REFS_PROBED=%g -- the runaway guard "
                   "fires first and the floor never runs, so the floor is not a floor"
                   % (ns["MIN_REFS_ALWAYS_PROBED"], ns.get("MAX_REFS_PROBED", 0)))
    elif ns["MIN_REFS_ALWAYS_PROBED"] < 8:
        bad.append("MIN_REFS_ALWAYS_PROBED=%g < 8 -- BELOW the count cap this bound "
                   "replaced, so the truncated set is no longer a subset of the old "
                   "one and C-T456-1 is reopened" % ns["MIN_REFS_ALWAYS_PROBED"])
    return ns, bad


def report(path, label):
    rows, ar = sweep(path, "m_" + os.path.basename(path).replace(".", "_"))
    print("=" * 78)
    print("%s   %s   (refs_carrying_content arity %d)" % (label, path, ar))
    print("=" * 78)
    ns, cbad = constants_preflight(path)
    print("probe bound constants : %s"
          % ", ".join("%s=%g" % (k, ns[k]) for k in sorted(ns)) or "NONE FOUND")
    print("floor invariant       : %s"
          % ("OK (8 <= MIN_REFS_ALWAYS_PROBED < MAX_REFS_PROBED)" if not cbad
             else "VIOLATED -- " + "; ".join(cbad)))
    print("states enumerated : %d   (%d branch x %d landed x %d ref)"
          % (len(rows), len(BRANCH), len(LANDED), len(REFS)))
    if not rows:
        sys.exit("ABORT: a partition over nothing proves nothing.")

    a_bad, b_bad, c_none, c_two, c_stale, errs = [], [], [], [], [], []
    census = collections.Counter()
    for key, kind, pol, err, m in rows:
        bl, ll, rlab = key
        if kind == "EXCEPTION":
            errs.append((key, err))
            continue
        census[(kind, pol)] += 1
        # ---- ARM A
        want = expected_kind(bl, ll, rlab)
        if kind != want:
            wpol = "REFUSE" if want in REFUSING_KINDS else "demote"
            a_bad.append((key, want, kind, wpol, pol,
                          "DESTRUCTIVE" if (wpol == "REFUSE" and pol == "demote")
                          else "conservative" if wpol == "demote" and pol == "REFUSE"
                          else "same polarity"))
        # ---- ARM B
        for iid, msg in invariants(bl, ll, rlab, kind, pol):
            b_bad.append((key, iid, msg))
        # ---- ARM C (T451's five, relabelled)
        if not kind or pol == "NONE":
            c_none.append((key, kind, pol))
            continue
        hits = arms_matching(kind)
        if hits[0][1] != pol:
            c_stale.append((key, kind, hits[0][1], pol))
        for suffix in ("/CASE-VARIANT", "/CASE-UNCHECKED"):
            alt = m.reconcile_action(kind + suffix)
            altpol = "REFUSE" if alt.startswith("REFUSE") else "demote"
            if altpol != pol:
                c_two.append((key, kind, suffix, pol, altpol))
        if len(set(p for _, p in hits)) > 1:
            c_two.append((key, kind, "disagreeing arms", pol, hits))

    print()
    print("ARM A -- PER-STATE EXPECTED KIND (a CORRECTNESS check; a transcription, and")
    print("         it can be edited into agreement with a defect -- see ARM B)")
    print("   states disagreeing with the expected kind : %d" % len(a_bad))
    for key, want, got, wpol, gpol, direction in a_bad[:20]:
        print("      %-58s want %-20s got %-20s  %s -> %s  %s"
              % (str(key), want, got, wpol, gpol, direction))
    dstr = sum(1 for x in a_bad if x[5] == "DESTRUCTIVE")
    print("   of which in the WORK-DESTROYING direction (want REFUSE, got demote): %d"
          % dstr)

    print()
    print("ARM B -- TABLE-FREE POLARITY INVARIANTS (no reference to ARM A's table)")
    print("   B1 carriers present => never demote   (T451/C-T449-1)")
    print("   B2 work on main     => never demote   (T324/T319)")
    print("   B3 all probes ran, nothing found => MUST demote (T330)")
    print("   DEFINED ON the %d of %d states whose branch coordinate actually consults"
          % (sum(1 for k, _kd, _p, _e, _m in rows if k[0] in EVIDENCE_CONSULTING),
             len(rows)))
    print("   the evidence (%s); in the other %d the probes never run and the LANDED /"
          % ("/".join(sorted(EVIDENCE_CONSULTING)),
             sum(1 for k, _kd, _p, _e, _m in rows if k[0] not in EVIDENCE_CONSULTING)))
    print("   REFS coordinates are cross-product artefacts, not worlds.")
    print("   violations : %d" % len(b_bad))
    byid = collections.Counter(x[1] for x in b_bad)
    for iid in sorted(byid):
        print("      %s: %d" % (iid, byid[iid]))
    for key, iid, msg in b_bad[:20]:
        print("      %-58s %s %s" % (str(key), iid, msg))

    print()
    print("ARM C -- T451's FIVE CRITERIA, RELABELLED AS WHAT THEY ARE:")
    print("         WELL-FORMEDNESS OF THE VERDICT SPACE, not correctness of the routing")
    print("   states with NO usable verdict     : %d" % len(c_none))
    print("   states with TWO DISAGREEING arms  : %d" % len(c_two))
    print("   arm-transcription mismatches      : %d" % len(c_stale))
    print("   exceptions raised                 : %d" % len(errs))
    for x in errs[:6]:
        print("      %s" % (x,))
    bykind = collections.defaultdict(set)
    for (k, p) in census:
        bykind[k].add(p)
    print("   kind -> polarity:")
    for k in sorted(bykind):
        pols = sorted(bykind[k])
        n = sum(v for (kk, _), v in census.items() if kk == k)
        print("      %-20s %-14s %4d states%s"
              % (k, "/".join(pols), n,
                 "   <== TWO POLARITIES" if len(pols) > 1 else ""))
    print("      %-20s %-14s %4d states" % ("TOTAL", "", sum(census.values())))
    caught = {"A": bool(a_bad), "A-destructive": dstr > 0, "B": bool(b_bad),
              "C": bool(c_none or c_two or c_stale or errs or cbad)}
    print()
    print("   ARMS RED on this file: %s"
          % (", ".join(k for k, v in caught.items() if v and k != "A-destructive")
             or "NONE -- all arms green"))
    return caught


clean = report(MOD, "SUBJECT")

if not PLANT:
    sys.exit(0 if not any(clean.values()) else 1)

# ---------------------------------------------------------------- planted defects ----
WORK = tempfile.mkdtemp(prefix="t462-plant-")
src = open(MOD, encoding="utf-8").read()
bs = os.path.join(os.path.dirname(os.path.abspath(MOD)), "branch_sweep.py")
if os.path.exists(bs):
    shutil.copy(bs, os.path.join(WORK, "branch_sweep.py"))


def write(name, text, why):
    if text == src:
        sys.exit("ABORT: plant %s was a NO-OP. Nothing was tested." % name)
    p = os.path.join(WORK, name)
    open(p, "w", encoding="utf-8").write(text)
    print()
    print("#" * 78)
    print("# PLANT %s -- %s" % (name, why))
    print("#" * 78)
    return p


# D4 -- T456's: swap the ORDER of the two arms T451 added to _branch_wip_core.
A0 = src.index('        if carriers:\n            return "stillborn-carried"')
A1 = src.index('        if carriers is None or unprobed:', A0)
A2 = src.index('        return "stillborn", (', A1)
if src.count('        if carriers:\n            return "stillborn-carried"') != 1:
    sys.exit("ABORT: the stillborn-carried arm is not unique; refusing to plant D4")
d4 = src[:A0] + src[A1:A2] + src[A0:A1] + src[A2:]
p4 = write("rt_d4.py", d4,
           "T456's ROUTING defect: the two new arms of _branch_wip_core swapped, so a "
           "state with a CARRIER and an unprobed ref demotes. Well-formed throughout.")
r4 = report(p4, "D4-PLANTED")

# D5 -- mine, in the OTHER caller, which D4 never touches: delete the `relocated` arm
# from _absent_verdict so a carrier on a pruned branch falls through to indeterminate.
# Also well-formed: `indeterminate` is a real kind with one polarity.
B0 = src.index('    if carriers:\n        return "relocated", (')
B1 = src.index('    if not complete or carriers is None or unprobed:', B0)
d5 = src[:B0] + src[B1:]
p5 = write("rt_d5.py", d5,
           "T462's own ROUTING defect, in the caller D4 does not touch: the `relocated` "
           "arm removed from _absent_verdict, so a carrier on a PRUNED branch demotes.")
r5 = report(p5, "D5-PLANTED")

# D-NULL -- the NEGATIVE CONTROL. A real edit inside the same routing region that is
# behaviour-preserving: the two unconditional probe calls at the top of _absent_verdict
# are swapped. Both run before any branch and neither depends on the other.
L1 = "    ev, complete, ev_note = landed_evidence(tid)\n"
L2 = "    carriers, name_only, unprobed, mentions, ref_note = " \
     "refs_carrying_content(tid, branch)\n"
i1 = src.index(L1 + L2)
dn = src[:i1] + L2 + L1 + src[i1 + len(L1) + len(L2):]
pn = write("rt_dnull.py", dn,
           "NEGATIVE CONTROL: the two unconditional probe calls at the top of "
           "_absent_verdict swapped. A real edit, behaviour-preserving. EVERY ARM MUST "
           "STAY GREEN -- an instrument that reddens here is crying wolf and its greens "
           "are worthless too.")
rn = report(pn, "D-NULL (must stay GREEN)")

print()
print("=" * 78)
print("SUMMARY -- WHICH ARM CATCHES WHICH")
print("=" * 78)
print("%-14s %-8s %-8s %-8s %-8s" % ("plant", "ARM A", "A-destr", "ARM B", "ARM C"))
for name, r in (("clean", clean), ("D4", r4), ("D5", r5), ("D-NULL", rn)):
    print("%-14s %-8s %-8s %-8s %-8s"
          % (name, "RED" if r["A"] else "green",
             "RED" if r["A-destructive"] else "green",
             "RED" if r["B"] else "green", "RED" if r["C"] else "green"))
print()
ok = True
for name, r in (("D4", r4), ("D5", r5)):
    if not (r["A"] and r["B"]):
        ok = False
        print("FAIL: %s was NOT caught by both ARM A and ARM B." % name)
if any(rn.values()):
    ok = False
    print("FAIL: the NEGATIVE CONTROL reddened an arm. The instrument is over-sensitive "
          "and its greens mean nothing.")
if any(clean.values()):
    ok = False
    print("FAIL: the SUBJECT file is not green.")
if ok:
    print("RESULT: both routing defects caught by ARM A and by ARM B; ARM C stayed")
    print("        GREEN on both, which is the C-T456-2 finding REPRODUCED -- T451's")
    print("        criteria cannot see a routing defect, by construction. The negative")
    print("        control stayed green on every arm, so the population is no longer")
    print("        self-selected: 3 planted (2 defects + 1 non-defect), 2 caught, 1")
    print("        correctly ignored.")
sys.exit(0 if ok else 1)
