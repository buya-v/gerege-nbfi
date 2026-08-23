#!/usr/bin/env python3
"""T292 -- the adversary.  It does NOT enumerate shapes; it QUANTIFIES OVER THEM.

P-91: "a guard phrased as a STRUCTURAL PATTERN over the shape of its input can always be re-nested
one level out, so enumerating shapes that COUNT and refusing the unmatched is a losing method no
matter how carefully each shape is chosen."  A test that enumerates fixtures has the same defect as
a rule that enumerates shapes: it removes finitely many members of an infinite family.  So the
central instrument here is a GENERATOR over the container-rewriting group, and the central claim is
an INVARIANCE, checked over thousands of members.

FOUR PROPERTIES, all mechanical:

  PROP-A  CONTAINER INVARIANCE.  For every seed document D and every container-only rewriting T
          drawn from the generator: exit(T(D)) == exit(D) AND coverageDigest(T(D)) ==
          coverageDigest(D) AND witness(T(D)) == witness(D).
          A VIOLATION IS THE WHOLE LINEAGE'S DEFECT, in either direction.

  PROP-B  NO VACUOUS GREEN.  Over every document produced anywhere in this run:
          exit == 0  =>  probe line PRESENT and witness >= 1 and nilFiles == 0.

  PROP-C  LOST-REFUSAL LEDGER vs the PRE-T268 rule (pinned blob 86f4285).  For every document,
          if PRE refuses (exit 1 WITH a probe line) and NEW greens, NEW must name a non-empty
          WITNESS.  Witness empty => LOST REFUSAL => FAIL.  Witness non-empty => the widening is
          adjudicated as legitimate and the witness paths are PRINTED so a reader can check the
          claim in one line rather than trusting it.

  PROP-D  ERROR/VERDICT SEPARATION (P-81, P-84).  exit 0 => probe PRESENT & GREEN.
          exit 1 => probe PRESENT & REFUSED.  exit 2 => probe ABSENT.  No other exit code.

ARMS.  PRE is extracted from the PINNED BLOB `86f4285`, never `HEAD:<path>` -- T268's lesson: a
`HEAD:<path>` extraction silently becomes the FIXED file the moment the fix is committed.
NEW is the live rule; its `git hash-object` is printed into the transcript on every run.
"""
import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAP = HERE.parent
ROOT = CAP.parent.parent.parent          # repo root, = .../<worktree>
T256 = CAP.parent / "t256-verdict-predicate"
T291FIX = ROOT / ".softhouse" / "reviews" / "t291-review-t286" / "probe" / "fixtures"

PRE_BLOB = "86f4285"
PROBE = "T259-VPA:"
TIMEOUT = 20      # F-T291-7: a guard that never returns never reports. Every arm is timed.


# ------------------------------------------------------------------------------------------
# arms
# ------------------------------------------------------------------------------------------

def git(*a):
    return subprocess.run(["git", "-C", str(ROOT)] + list(a),
                          capture_output=True, text=True, timeout=60)


def extract_pre(dst: Path) -> str:
    """Unpack the PINNED PRE blob. NOTE THE DIRECTORY: PRE computes `repo_root()` by walking up
    from its OWN location and `raise SystemExit`s if it finds no `.git` ancestor -- so a PRE arm
    unpacked into /tmp exits 1 on EVERY input and the whole PRE column silently becomes a constant.
    The first draft of this file did exactly that and three legs went red with
    `ERROR: no .git ancestor`; recorded rather than tidied. T286 flagged the same hazard about its
    own default target. The PRE arm is therefore unpacked INSIDE the repo."""
    r = subprocess.run(["git", "-C", str(ROOT), "cat-file", "blob", PRE_BLOB],
                       capture_output=True, timeout=60)
    if r.returncode != 0:
        raise SystemExit("ERROR: cannot resolve pinned PRE blob %s; the PRE arm is ABSENT and "
                         "this run measures nothing. Refusing to continue." % PRE_BLOB)
    dst.write_bytes(r.stdout)
    sha = _hash_object(dst)
    if not sha.startswith(PRE_BLOB):
        raise SystemExit("ERROR: unpacked PRE hashes to %s, not %s" % (sha, PRE_BLOB))
    # Calibrate the arm on a KNOWN POSITIVE before trusting a single PRE column (P-72): PRE must
    # GREEN the real evidence. If it refuses, the arm is broken, not the corpus.
    if REAL_229.exists():
        rc, probe, _, err = run_rule(dst, [REAL_229])
        if rc != 0 or probe is None:
            raise SystemExit("ERROR: PRE arm fails its calibration -- it must exit 0 with a probe "
                             "line on classify-t229.json, got rc=%s probe=%s %s"
                             % (rc, probe is not None, err.strip()[:200]))
    return sha


def _hash_object(p: Path) -> str:
    r = subprocess.run(["git", "hash-object", str(p)], capture_output=True, text=True, timeout=60)
    return r.stdout.strip()


def run_rule(rule: Path, targets, env_extra=None, timeout=TIMEOUT):
    """Returns (rc, probe_line_or_None, stdout, stderr). rc == 'TIMEOUT' if it never returned."""
    env = dict(os.environ)
    env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    if env_extra:
        env.update(env_extra)
    cmd = [sys.executable, str(rule),
           "--register", str(T256 / "boolean-key-register.json"),
           "--acknowledgements", str(T256 / "acknowledged.json")] + [str(t) for t in targets]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return "TIMEOUT", None, "", ""
    probe = None
    for ln in p.stdout.splitlines():
        if ln.startswith(PROBE):
            probe = ln
    return p.returncode, probe, p.stdout, p.stderr


def probe_field(probe, name):
    if not probe:
        return None
    for tok in probe.split():
        if tok.startswith(name + "="):
            return tok.split("=", 1)[1]
    return None


# ------------------------------------------------------------------------------------------
# the container-rewriting generator -- THE point of this file
# ------------------------------------------------------------------------------------------
#
# A CONTAINER-ONLY rewriting inserts, removes or re-arranges CONTAINERS.  It never changes which
# object a key belongs to -- so it cannot change what a correct rule grades.  Every member of the
# family costs the attacker a couple of characters.  T291 found four members by hand (X2, X3, X4,
# X7).  This generates them and thousands of others.
#
# TWO DELIBERATE CHOICES, STATED SO THE COVERAGE CLAIM IS NOT READ AS WIDER THAN IT IS:
#
#  (1) Wrappers are inserted ONLY at positions already holding a dict or a list.  Wrapping a SCALAR
#      would detach a leaf from its object -- `{"verdict": "PASS"}` -> `{"verdict": ["PASS"]}` is a
#      real semantic change, not a re-nesting, and asserting invariance over it would be asserting
#      something false.  That evasion is a separate, NAMED fixture (A13) with its own expected
#      outcome, not a member of this family.
#  (2) `beside-a-decoy-*` ADDS a leaf, so the generator is slightly MORE permissive than the
#      theorem's hypothesis.  That is on purpose: adding decoys is exactly what an attacker does,
#      and the theorem only needs that no BOOLEAN UNDER A REGISTERED PREDICATE KEY is added.

def _container_sites(v, path=()):
    """Every position holding a dict or a list -- the only positions a container wrapper may be
    inserted at without detaching a key from its object."""
    if isinstance(v, (dict, list)):
        yield path
    if isinstance(v, dict):
        for k, x in v.items():
            yield from _container_sites(x, path + (("k", k),))
    elif isinstance(v, list):
        for i, x in enumerate(v):
            yield from _container_sites(x, path + (("i", i),))


def _get(v, path):
    for kind, k in path:
        v = v[k]
    return v


def _set(v, path, new):
    if not path:
        return new
    parent = _get(v, path[:-1])
    kind, k = path[-1]
    parent[k] = new
    return v


WRAPPERS = [
    ("wrap-in-list", lambda x, n: [x]),
    ("wrap-in-object", lambda x, n: {"_w%d" % n: x}),
    ("wrap-in-list-of-lists", lambda x, n: [[x]]),
    ("wrap-3-deep-lists", lambda x, n: [[[x]]]),
    ("wrap-object-then-list", lambda x, n: {"_h%d" % n: [x]}),
    ("wrap-list-then-object", lambda x, n: [{"_h%d" % n: x}]),
    ("beside-a-decoy-string", lambda x, n: [x, "AS PREDICTED"]),
    ("beside-a-decoy-object", lambda x, n: [x, {"note": "n%d" % n}]),
]


def _listify_object(o, n):
    """{k: v} -> {k: [v]} for one dict-or-list-valued key. Container-only."""
    cands = [k for k, v in o.items() if isinstance(v, (dict, list))]
    if not cands:
        return None
    k = cands[n % len(cands)]
    out = dict(o)
    out[k] = [out[k]]
    return out


def _objectify_list(lst, n):
    """[a, b] -> {"0": a, "1": b}. Container-only: the index keys are neither registered
    predicate keys nor verdict-named keys, and every element keeps its own key set."""
    return {str(i): x for i, x in enumerate(lst)}


def mutate(doc, rng, steps):
    """Apply `steps` container-only rewritings at random sites. Returns (doc', [names])."""
    cur = json.loads(json.dumps(doc))
    names = []
    for n in range(steps):
        sites = list(_container_sites(cur))
        if not sites:
            break
        site = rng.choice(sites)
        node = _get(cur, site)
        choice = rng.randrange(len(WRAPPERS) + 2)
        if choice < len(WRAPPERS):
            nm, fn = WRAPPERS[choice]
            cur = _set(cur, site, fn(node, n))
        elif choice == len(WRAPPERS) and isinstance(node, dict):
            new = _listify_object(node, n)
            if new is None:
                continue
            nm = "listify-a-key"
            cur = _set(cur, site, new)
        elif isinstance(node, list):
            nm = "objectify-a-list"
            cur = _set(cur, site, _objectify_list(node, n))
        else:
            continue
        names.append(nm)
    return cur, names


# ------------------------------------------------------------------------------------------
# corpus
# ------------------------------------------------------------------------------------------

REAL_229 = ROOT / ".softhouse" / "capture" / "t229-g8-site3" / "out" / "classify-t229.json"
REAL_219 = ROOT / ".softhouse" / "capture" / "t219-g8-residual" / "out" / "classify-t219.json"

# T292's own attacks. Each is a shape a reviewer would think of and none is a re-nesting of
# another -- the re-nestings are the generator's job, not a fixture's.
T292_ATTACKS = {
    # A1. The predicate is recorded as a STRING, not a boolean. PRE counts the row and greens;
    #     a witness-based rule reads no boolean and refuses. A gained refusal, not a lost one.
    "A1-predicate-as-a-string": {
        "cells": [{"id": "c1", "P2_totalInterestEqualsNEplusB": "false", "verdict": "AS PREDICTED"}]},
    # A2. COVERAGE LAUNDERING. The only boolean is one the REGISTER classifies DESCRIPTIVE, so it
    #     looks like evidence and grades nothing. The register is external and committed: this is
    #     the attack that shows coverage is constructed from R, not from the document.
    "A2-coverage-laundered-through-a-DESCRIPTIVE-key": {
        "cells": [{"id": "c1", "t223RulePredictedRescue": True, "verdict": "AS PREDICTED"}]},
    # A3. The verdict KEY is renamed so no verdict-named key exists, over a real false predicate.
    #     G6 -- a refuted record must state a disposition this rule can read.
    "A3-refutation-with-the-verdict-key-renamed": {
        "cells": [{"id": "c1", "P2_x": False, "conclusion": "everything is fine"}]},
    # A4. A near-miss on the auto pattern: `P_x` has no digits, so it is UNCLASSIFIED, not a
    #     predicate. Tests that the auto-classifier cannot be talked into coverage by a lookalike.
    "A4-auto-pattern-lookalike-key": {
        "cells": [{"id": "c1", "P_x": True, "verdict": "AS PREDICTED"}]},
    # A5. A predicate NESTED INSIDE the header the attacker built. If coverage were structural
    #     this would be the next evasion; under a witness it simply IS coverage, and the graded
    #     fact is printed with its path.
    "A5-real-predicate-buried-under-eight-containers": {
        "a": [{"b": [[{"c": {"cells": [{"id": "c1", "P2_x": False, "verdict": "AS PREDICTED"}]}}]]}]},
    # A6. Mongolian Cyrillic payload -- ovog / patronymic / given name, three fields (CLAUDE.md).
    #     Driven additionally under LC_ALL=C, where PRE's `read_text()` dies.
    "A6-cyrillic-mongolian-name-fields": {
        "cells": [{"id": "c1", "ovog": "Бат", "etsgiinNer": "Дорж",
                   "ner": "Сарантуяа",
                   "P2_x": True, "verdict": "AS PREDICTED"}]},
    # A7. An affirmative word as a MAPPING KEY over a refuted record (T286's guard #10 shape).
    "A7-affirmation-as-a-mapping-key": {
        "AS PREDICTED": {"note": "header"},
        "cells": [{"id": "c1", "P2_x": False, "verdict": "REFUTED"}]},
    # A8. Every boolean removed but the affirmative verdict kept, at the deepest reachable point.
    "A8-affirmation-only-at-depth": {"a": {"b": {"c": [[[{"verdict": "AS PREDICTED"}]]]}}},
    # A9. A genuine, fully-graded green -- the control. If this ever refuses the rule is useless.
    "A9-CONTROL-genuine-green": {
        "cells": [{"id": "c1", "P2_x": True, "verdict": "AS PREDICTED"}]},
    # A10. A genuine unacknowledged disagreement -- the control in the other direction.
    "A10-CONTROL-genuine-unacknowledged-disagreement": {
        "cells": [{"id": "c1", "P2_x": False, "verdict": "AS PREDICTED"}]},
    # A11. THE FORGERY FLOOR, PUT IN FRONT OF THE INSTRUMENT RATHER THAN REASONED ABOUT.
    #      A header that buys its coverage by ASSERTING a predicate. This GREENS, deliberately,
    #      and it is the sharpest thing a reviewer can aim at T292. The answer is in the rule's
    #      second theorem: to build this the attacker had to write `P1_ok: true` into a committed
    #      file -- a FABRICATED FACT, byte-identical as an input to a true one, and unreachable
    #      for ANY rule reading only (document, register). What T292 buys is that the transcript
    #      NAMES it: `$.meta.P1_ok = true`. Compare A12, which cannot even do that much.
    "A11-FLOOR-header-buys-coverage-by-asserting-a-predicate": {
        "meta": {"P1_ok": True, "verdict": "AS PREDICTED"}, "cells": []},
    # A12. The same attempt WITHOUT asserting a fact -- a header carrying a registered
    #      DESCRIPTIVE boolean and a plausible-looking count. Refuses. The floor is exactly at
    #      "assert a predicate", not at "look like a record".
    "A12-header-tries-to-buy-coverage-without-asserting-a-predicate": {
        "meta": {"t223RulePredictedRescue": True, "rowsChecked": 11,
                 "verdict": "AS PREDICTED"}, "cells": []},
    # A13. THE BRACKET AIMED AT DETECTION INSTEAD OF COVERAGE -- the obvious next move once
    #      coverage is container-blind. Wrap the VERDICT VALUE in `[ ]`: it is no longer a string
    #      value of its object, so the local disagreement check cannot see it. This is the same
    #      two-character evasion, re-nested one level out, on the other axis. It REFUSES -- not
    #      because a shape was enumerated, but because G6 demands that a record admitting a FALSE
    #      predicate carry a disposition the rule can READ. Hiding the disposition is not a pass.
    "A13-verdict-VALUE-wrapped-in-a-list-over-a-false-predicate": {
        "cells": [{"id": "c1", "P1_x": False, "verdict": ["AS PREDICTED"]}]},
}


def load_t291_fixtures():
    out = {}
    if not T291FIX.is_dir():
        return out
    for p in sorted(T291FIX.glob("*.json")):
        out["T291/" + p.stem] = json.loads(p.read_text(encoding="utf-8"))
    return out


# ------------------------------------------------------------------------------------------

class Ledger:
    def __init__(self):
        self.legs = []

    def add(self, prop, name, ok, detail, skipped=False):
        self.legs.append({"prop": prop, "name": name,
                          "ok": bool(ok), "skipped": bool(skipped), "detail": detail})

    @property
    def failed(self):
        return [l for l in self.legs if not l["ok"] and not l["skipped"]]

    @property
    def skipped(self):
        return [l for l in self.legs if l["skipped"]]


def write(tmp: Path, name: str, doc) -> Path:
    p = tmp / (name.replace("/", "__") + ".json")
    p.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


def measure(rule, path, env=None):
    rc, probe, out, err = run_rule(rule, [path], env)
    return {"rc": rc, "probe": probe,
            "witness": probe_field(probe, "witness"),
            "digest": probe_field(probe, "coverageDigest"),
            "state": probe.split()[1] if probe else None,
            "stderr": err[-400:]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rule", default=str(CAP / "check_verdict_predicate_agreement_t292.py"))
    ap.add_argument("--seeds", type=int, default=40)
    ap.add_argument("--depth", type=int, default=6)
    ap.add_argument("--seed", type=int, default=292)
    ap.add_argument("--legs-out", default=str(CAP / "out" / "t292-adversary-legs.json"))
    args = ap.parse_args()

    NEW = Path(args.rule).resolve()
    rng = random.Random(args.seed)
    L = Ledger()
    tmp = Path(tempfile.mkdtemp(prefix="t292-adv-"))
    # The PRE arm must live INSIDE the repo -- see extract_pre.
    prehome = Path(tempfile.mkdtemp(prefix=".t292-pre-arm-", dir=str(CAP)))
    try:
        pre = prehome / "PRE.py"
        pre_sha = extract_pre(pre)
        print("ARMS")
        print("  PRE  pinned blob %s -> git hash-object %s" % (PRE_BLOB, pre_sha))
        print("  NEW  %s -> git hash-object %s" % (NEW.name, _hash_object(NEW)))
        print("  python %s" % sys.version.split()[0])
        print("  rng seed %d, %d container mutations per seed doc, up to depth %d"
              % (args.seed, args.seeds, args.depth))
        print()

        corpus = {}
        corpus.update(load_t291_fixtures())
        corpus.update(T292_ATTACKS)
        if REAL_229.exists():
            corpus["REAL/classify-t229"] = json.loads(REAL_229.read_text(encoding="utf-8"))
        if REAL_219.exists():
            corpus["REAL/classify-t219"] = json.loads(REAL_219.read_text(encoding="utf-8"))
        if not corpus:
            raise SystemExit("ERROR: empty corpus; this run measures nothing")

        # ---------------- PROP-A / PROP-B / PROP-C over the generated family ----------------
        print("=" * 96)
        print("PROP-A  CONTAINER INVARIANCE  +  PROP-B NO VACUOUS GREEN  +  PROP-C LOST-REFUSAL "
              "LEDGER vs PRE")
        print("=" * 96)
        total_docs = 0
        lost_refusals = []
        widenings = []
        for name, doc in sorted(corpus.items()):
            base_p = write(tmp, "base__" + name, doc)
            base_new = measure(NEW, base_p)
            base_pre = measure(pre, base_p)
            total_docs += 1

            # PROP-B on the base
            ok_b = not (base_new["rc"] == 0 and
                        (base_new["probe"] is None or int(base_new["witness"] or 0) < 1))
            L.add("PROP-B", "base " + name, ok_b,
                  "rc=%s witness=%s" % (base_new["rc"], base_new["witness"]))

            # PROP-C on the base
            pre_refuses = (base_pre["rc"] == 1 and base_pre["probe"] is not None)
            if pre_refuses and base_new["rc"] == 0:
                if int(base_new["witness"] or 0) < 1:
                    lost_refusals.append((name, "base"))
                else:
                    widenings.append((name, base_new["witness"], base_new["digest"]))

            # PROP-A: the generated container family
            bad = []
            for s in range(args.seeds):
                steps = 1 + rng.randrange(args.depth)
                mdoc, names = mutate(doc, rng, steps)
                mp = write(tmp, "m__%s__%d" % (name, s), mdoc)
                m = measure(NEW, mp)
                total_docs += 1
                if (m["rc"] != base_new["rc"] or m["digest"] != base_new["digest"]
                        or m["witness"] != base_new["witness"]):
                    bad.append((s, names, m["rc"], m["witness"], m["digest"]))
                if m["rc"] == 0 and (m["probe"] is None or int(m["witness"] or 0) < 1):
                    L.add("PROP-B", "mutant %s#%d" % (name, s), False,
                          "VACUOUS GREEN rc=0 witness=%s via %s" % (m["witness"], names))
                mpre = measure(pre, mp)
                if mpre["rc"] == 1 and mpre["probe"] is not None and m["rc"] == 0:
                    if int(m["witness"] or 0) < 1:
                        lost_refusals.append((name + "#%d" % s, ",".join(names)))
                    else:
                        widenings.append((name + "#%d via %s" % (s, ",".join(names)),
                                          m["witness"], m["digest"]))
            L.add("PROP-A", name, not bad,
                  ("INVARIANT over %d container rewritings  rc=%s witness=%s digest=%s"
                   % (args.seeds, base_new["rc"], base_new["witness"], base_new["digest"]))
                  if not bad else
                  ("NOT INVARIANT: base rc=%s w=%s d=%s ; %d divergences, first: %r"
                   % (base_new["rc"], base_new["witness"], base_new["digest"], len(bad), bad[0])))
            mark = "ok " if not bad else "FAIL"
            print("  %s PROP-A %-58s rc=%-4s witness=%-4s digest=%s"
                  % (mark, name, base_new["rc"], base_new["witness"], base_new["digest"]))

        print()
        print("  documents driven through BOTH arms: %d" % total_docs)
        L.add("PROP-C", "no lost refusal vs PRE (pinned %s)" % PRE_BLOB, not lost_refusals,
              "lost=%d %r" % (len(lost_refusals), lost_refusals[:5]))
        print("  PROP-C  LOST REFUSALS (PRE refuses, NEW greens, witness EMPTY): %d %s"
              % (len(lost_refusals), "" if not lost_refusals else lost_refusals[:5]))
        print("  PROP-C  ADJUDICATED WIDENINGS (PRE refuses, NEW greens, witness NAMED): %d"
              % len(widenings))
        print("          A WIDENING IS NOT A LOST REFUSAL: PRE refused for want of a SHAPE it "
              "recognised,")
        print("          NEW greens because it GRADED named facts, and it prints them. Adjudicate "
              "by reading")
        print("          the witness, not by trusting the count.")
        for w in widenings[:12]:
            print("            %-58s witness=%s digest=%s" % w)
        if len(widenings) > 12:
            print("            ... and %d more, all in out/t292-adversary-legs.json"
                  % (len(widenings) - 12))
        print()

        # ---------------- PROP-D: error / verdict separation, and the repairs -------------
        print("=" * 96)
        print("PROP-D  ERROR vs MEASURED NEGATIVE, and the six repairs T291 measured")
        print("=" * 96)

        def leg(nm, targets, expect_rc, expect_probe, env=None, timeout=TIMEOUT, arm=None):
            rc, probe, out, err = run_rule(arm or NEW, targets, env, timeout)
            got_probe = probe is not None
            ok = (rc == expect_rc) and (got_probe == expect_probe)
            L.add("PROP-D", nm, ok, "rc=%s probe=%s (want rc=%s probe=%s) %s"
                  % (rc, got_probe, expect_rc, expect_probe, err.strip()[:160]))
            print("  %s %-62s rc=%-8s probe=%s" % ("ok " if ok else "FAIL", nm, rc,
                                                   "PRESENT" if got_probe else "ABSENT"))
            return rc, probe

        raw = tmp / "raw"
        raw.mkdir()

        def rawfile(nm, text, mode="w"):
            p = raw / nm
            if isinstance(text, bytes):
                p.write_bytes(text)
            else:
                p.write_text(text, encoding="utf-8")
            return p

        # F-T291-4 duplicate predicate keys -- MUST be exit 2, not a silent last-wins green
        dup = rawfile("duplicate-predicate-keys.json",
                      '{"cells":[{"id":"c1","P9_x":false,"P9_x":true,"verdict":"AS PREDICTED"}]}')
        leg("DUP  duplicate predicate keys (last-wins drops a false)", [dup], 2, False)
        leg("DUP  ... and the PRE arm greens it (the defect, driven)", [dup], 0, True, arm=pre)

        # F-T291-5 NaN / Infinity as FLOATS in a GREEN run -- money non-negotiable
        nan = rawfile("json-nan-infinity.json",
                      '{"cells":[{"id":"c1","P9_x":true,"verdict":"AS PREDICTED",'
                      '"v":NaN,"w":Infinity,"u":-Infinity}]}')
        leg("NaN  NaN/Infinity JSON constants", [nan], 2, False)
        leg("NaN  ... and the PRE arm greens them AS FLOATS (the defect, driven)",
            [nan], 0, True, arm=pre)
        big = rawfile("json-1e400.json",
                      '{"cells":[{"id":"c1","P9_x":true,"verdict":"AS PREDICTED","v":1e400}]}')
        leg("NaN  1e400 overflows float; Decimal keeps it exact", [big], 0, True)

        # F-T291-6 Cyrillic under LC_ALL=C -- Mongolian names, three fields
        cyr = write(tmp, "cyrillic", T292_ATTACKS["A6-cyrillic-mongolian-name-fields"])
        leg("CYR  Cyrillic ovog/patronymic/given name under LC_ALL=C", [cyr], 0, True,
            env={"LC_ALL": "C", "LANG": "C", "PYTHONUTF8": "0", "PYTHONCOERCECLOCALE": "0"})
        leg("CYR  ... and the PRE arm exits 2 on it (the defect, driven)", [cyr], 2, False,
            env={"LC_ALL": "C", "LANG": "C", "PYTHONUTF8": "0", "PYTHONCOERCECLOCALE": "0"},
            arm=pre)

        # F-T291-7 read-twice -- observable as an indefinite HANG on a FIFO
        fifo = raw / "target.fifo"
        try:
            os.mkfifo(fifo)
            feeder = subprocess.Popen(
                [sys.executable, "-c",
                 "import sys;open(sys.argv[1],'w').write('{\"cells\":[{\"id\":\"c1\",'"
                 "'\"P9_x\":true,\"verdict\":\"AS PREDICTED\"}]}')", str(fifo)])
            rc, probe, out, err = run_rule(NEW, [fifo], timeout=15)
            feeder.kill()
            ok = rc != "TIMEOUT"
            L.add("PROP-D", "FIFO read-once does not hang", ok, "rc=%s" % rc)
            print("  %s %-62s rc=%s" % ("ok " if ok else "FAIL",
                                        "FIFO read-once does not hang (F-T291-7)", rc))
        except (OSError, NotImplementedError) as exc:
            L.add("PROP-D", "FIFO read-once does not hang", False, "SKIPPED: %s" % exc,
                  skipped=True)
            print("  SKIP FIFO -- %s" % exc)

        # T286's fourth fail-open: --help -> SystemExit(0) -> exit 0 with NO probe line
        for flag in ("--help", "-h", "--not-a-flag", "--register"):
            r = subprocess.run([sys.executable, str(NEW), flag], capture_output=True, text=True,
                               timeout=TIMEOUT)
            ok = r.returncode == 2 and PROBE not in r.stdout
            L.add("PROP-D", "argv %s -> 2, no probe" % flag, ok, "rc=%d" % r.returncode)
            print("  %s argv %-56s rc=%d probe=%s" % ("ok " if ok else "FAIL", flag, r.returncode,
                                                      "PRESENT" if PROBE in r.stdout else "ABSENT"))
        r = subprocess.run([sys.executable, str(NEW)], capture_output=True, text=True,
                           timeout=TIMEOUT)
        ok = r.returncode == 2 and PROBE not in r.stdout
        L.add("PROP-D", "no targets -> 2 (no built-in default target)", ok, "rc=%d" % r.returncode)
        print("  %s %-62s rc=%d" % ("ok " if ok else "FAIL",
                                    "no targets -> 2 (no built-in default)", r.returncode))

        # ordinary error surface
        leg("ERR  missing file", [raw / "nope.json"], 2, False)
        leg("ERR  a directory as target", [raw], 2, False)
        leg("ERR  zero bytes", [rawfile("empty.json", "")], 2, False)
        leg("ERR  malformed json", [rawfile("bad.json", "{")], 2, False)
        leg("ERR  trailing garbage", [rawfile("tail.json", '{"a":1} xx')], 2, False)
        leg("ERR  invalid utf-8 bytes", [rawfile("badenc.json", b'{"a":"\xff\xfe"}')], 2, False)
        leg("ERR  recursion bomb (3000 brackets)",
            [rawfile("bomb.json", "[" * 3000 + "]" * 3000)], 2, False)
        # zero-row degenerates: a MEASURED negative, probe PRESENT
        for nm, txt in (("null", "null"), ("empty-array", "[]"), ("empty-object", "{}"),
                        ("bare-int", "7"), ("bare-string", '"x"'), ("bare-true", "true"),
                        ("list-of-scalars", "[1,2,3]"), ("list-of-nulls", "[null,null]")):
            leg("NEG  degenerate %-18s -> 1, probe PRESENT" % nm,
                [rawfile("deg-%s.json" % nm, txt)], 1, True)

        # PYTHONOPTIMIZE strips `assert`; the post-condition must not be an assert
        r = subprocess.run([sys.executable, str(NEW),
                            "--register", str(T256 / "boolean-key-register.json"),
                            "--acknowledgements", str(T256 / "acknowledged.json"),
                            str(write(tmp, "opt", load_t291_fixtures().get(
                                "T291/X2-header-in-nested-list", {"cells": []})))],
                           capture_output=True, text=True, timeout=TIMEOUT,
                           env={**os.environ, "PYTHONOPTIMIZE": "2"})
        ok = r.returncode == 1
        L.add("PROP-D", "PYTHONOPTIMIZE=2 still refuses X2", ok, "rc=%d" % r.returncode)
        print("  %s %-62s rc=%d" % ("ok " if ok else "FAIL", "PYTHONOPTIMIZE=2 still refuses X2",
                                    r.returncode))

        # T268's F-1 shape: an empty header file BATCHED with real evidence, both orders
        if REAL_229.exists():
            x2 = write(tmp, "x2batch", load_t291_fixtures().get(
                "T291/X2-header-in-nested-list", {"cells": []}))
            for order, ts in (("header-first", [x2, REAL_229]),
                              ("evidence-first", [REAL_229, x2])):
                rc, probe, out, err = run_rule(NEW, ts)
                ok = rc == 1 and probe is not None and probe_field(probe, "nilFiles") == "1"
                L.add("PROP-D", "BATCH %s refuses (T268 F-1)" % order, ok,
                      "rc=%s nilFiles=%s" % (rc, probe_field(probe, "nilFiles")))
                print("  %s BATCH %-56s rc=%s nilFiles=%s"
                      % ("ok " if ok else "FAIL", order, rc, probe_field(probe, "nilFiles")))

        # ---------------- report ----------------
        print()
        print("=" * 96)
        passed = [l for l in L.legs if l["ok"] and not l["skipped"]]
        print("T292 ADVERSARY: %d passed, %d failed, %d SKIPPED   over %d documents"
              % (len(passed), len(L.failed), len(L.skipped), total_docs))
        for l in L.failed:
            print("  FAILED  [%s] %s -- %s" % (l["prop"], l["name"], l["detail"]))
        for l in L.skipped:
            print("  SKIPPED [%s] %s -- %s" % (l["prop"], l["name"], l["detail"]))
        print("LOST REFUSALS: %d   (the criterion T281 used to reject T268)" % len(lost_refusals))
        # A SKIPPED LEG IS A FAILURE. P-91 corollary: a rig that can pass vacuously proves
        # nothing, and T286's battery returned 0 with nine legs dropped.
        rc = 1 if (L.failed or L.skipped or lost_refusals) else 0
        print("EXIT %d   (non-zero on ANY failure, ANY skip, or ANY lost refusal)" % rc)
        legs_out = Path(args.legs_out)
        legs_out.parent.mkdir(parents=True, exist_ok=True)
        legs_out.write_text(
            json.dumps({"pre_blob": PRE_BLOB, "pre_sha": pre_sha,
                        "new_sha": _hash_object(NEW), "docs": total_docs,
                        "lost_refusals": lost_refusals, "widenings": widenings,
                        "legs": L.legs}, indent=1), encoding="utf-8")
        return rc
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(prehome, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
