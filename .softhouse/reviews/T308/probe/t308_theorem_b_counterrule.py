#!/usr/bin/env python3
"""T308 -- ATTACK THEOREM 2: "guard #10's ambition is a MEASURED IMPOSSIBILITY".

T292's claim, verbatim from the rule docstring:

    "This rule does not restore that claim, because the claim is unachievable by any
     container-blind rule ... Separating X5 from classify-t229.json requires an EXTERNAL
     declaration of which containers hold graded records; that changes
     boolean-key-register.json's contract, which is outside T292's files_hint."

"Impossible" is a strong word, so this probe tries to BUILD the separator rather than agree
that none exists.  It CONSTRUCTS one -- with no register change, no external declaration,
and no new input of any kind -- and measures it over the whole corpus.

THE COUNTER-RULE (G10-SIBLING).  For every affirmative word (as a value OR as a mapping key)
whose IMMEDIATELY OWNING object contributed no witness:

    let C be the container that directly holds that owning object.
    PERMIT  iff C directly holds at least one object that DID contribute a witness.
    REFUSE  otherwise.

i.e. "an affirmative verdict may stand without grading anything only where the graded records
themselves live."  Nothing external is consulted; the discriminator is the sibling relation,
which is CONTAINER STRUCTURE.

WHY THAT IS NOT A REFUTATION OF T292'S LITERAL SENTENCE, AND IS STILL A FINDING.  T292's
impossibility is proved for the class of CONTAINER-BLIND rules.  Guard #10 is a DETECTION
guard, and T292's own central thesis is that DETECTION is entitled to be container-aware --
walk_objects is total and deliberately so ("the DETECTION side, generous, as it should be").
So the impossibility is proved about a rule class guard #10 never needed to belong to.  The
honest statement is "not achievable WITHOUT READING CONTAINER STRUCTURE, which detection is
already permitted to do" -- a design choice that was not made, not a theorem.
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent.parent
CAP = ROOT / ".softhouse" / "capture" / "t286-t268-retry"
T256 = ROOT / ".softhouse" / "capture" / "t256-verdict-predicate"
T291FIX = ROOT / ".softhouse" / "reviews" / "t291-review-t286" / "probe" / "fixtures"
REAL_229 = ROOT / ".softhouse" / "capture" / "t229-g8-site3" / "out" / "classify-t229.json"
REAL_219 = ROOT / ".softhouse" / "capture" / "t219-g8-residual" / "out" / "classify-t219.json"

AFFIRMATIVE = {"AS PREDICTED", "AS_PREDICTED", "AS-PREDICTED", "PASS", "PASSED", "OK",
               "CONFIRMED", "REPRODUCED", "GREEN", "HELD", "AGREES", "MATCHED"}


def load_register():
    return json.loads((T256 / "boolean-key-register.json").read_text(encoding="utf-8"))


def key_class(reg, key):
    if key.startswith("P") and "_" in key:
        head = key.split("_", 1)[0]
        if len(head) > 1 and head[1:].isdigit():
            return "PREDICATE"
    ent = reg.get("keys", {}).get(key)
    if ent is None:
        return "UNCLASSIFIED"
    return ent.get("class")


def walk_objects(v, path="$"):
    if isinstance(v, dict):
        yield path, v
        for k, x in v.items():
            yield from walk_objects(x, path + "." + k)
    elif isinstance(v, list):
        for i, x in enumerate(v):
            yield from walk_objects(x, path + "[%d]" % i)


def walk_strings(v, path="$"):
    if isinstance(v, dict):
        for k, x in v.items():
            yield path + ".<key>" + k, "key", k
            yield from walk_strings(x, path + "." + k)
    elif isinstance(v, list):
        for i, x in enumerate(v):
            yield from walk_strings(x, path + "[%d]" % i)
    elif isinstance(v, str):
        yield path, "value", v


def parent_container(opath):
    """The container that DIRECTLY holds the object at `opath`. '$' has none."""
    if opath == "$":
        return None
    if opath.endswith("]"):
        return opath[:opath.rindex("[")]
    return opath[:opath.rindex(".")]


def witnessed_objects(doc, reg):
    out = set()
    for opath, obj in walk_objects(doc):
        for k, v in obj.items():
            if isinstance(v, bool) and key_class(reg, k) == "PREDICATE":
                out.add(opath)
                break
    return out


def g10_census(doc, reg):
    """T292's SHIPPED counter: affirmative word whose owning object graded nothing."""
    wit = witnessed_objects(doc, reg)
    hits = []
    for spath, kind, s in walk_strings(doc):
        if str(s).strip().upper() not in AFFIRMATIVE:
            continue
        owner = spath.split(".<key>")[0] if kind == "key" else spath.rsplit(".", 1)[0]
        if owner not in wit:
            hits.append((spath, kind, s, owner))
    return hits


def g10_sibling(doc, reg):
    """THE COUNTER-RULE. Same candidates, then keep only those with NO witnessing sibling."""
    wit = witnessed_objects(doc, reg)
    by_container = {}
    for w in wit:
        by_container.setdefault(parent_container(w), set()).add(w)
    hits = []
    for spath, kind, s, owner in g10_census(doc, reg):
        c = parent_container(owner)
        if c is not None and by_container.get(c):
            continue                      # a sibling of genuinely graded records: PERMIT
        hits.append((spath, kind, s, owner, c))
    return hits


CORPUS = {}


def load_corpus():
    for p in sorted(T291FIX.glob("*.json")):
        CORPUS["T291/" + p.stem] = json.loads(p.read_text(encoding="utf-8"))
    if REAL_229.exists():
        CORPUS["REAL/classify-t229"] = json.loads(REAL_229.read_text(encoding="utf-8"))
    if REAL_219.exists():
        CORPUS["REAL/classify-t219"] = json.loads(REAL_219.read_text(encoding="utf-8"))
    CORPUS["A7-affirmation-as-a-mapping-key"] = {
        "AS PREDICTED": {"note": "header"},
        "cells": [{"id": "c1", "P2_x": False, "verdict": "REFUTED"}]}
    CORPUS["A9-CONTROL-genuine-green"] = {
        "cells": [{"id": "c1", "P2_x": True, "verdict": "AS PREDICTED"}]}
    CORPUS["A10-CONTROL-unacknowledged-disagreement"] = {
        "cells": [{"id": "c1", "P2_x": False, "verdict": "AS PREDICTED"}]}
    CORPUS["EVASION-header-moved-INSIDE-the-records-list"] = {
        "cells": [{"verdict": "AS PREDICTED"},
                  {"id": "c1", "P2_x": False, "verdict": "REFUTED"}]}


# What a correct guard #10 MUST do, stated before the numbers are read.
WANT_REFUSE = {
    "T291/X5-affirmation-in-list-over-refuted-record",
    "T291/X5b-affirmation-as-mapping-key-over-refuted-record",
    "A7-affirmation-as-a-mapping-key",
}
WANT_PERMIT = {
    "REAL/classify-t229",          # COMMITTED, CORRECT evidence. Turning this red is the veto.
    "REAL/classify-t219",
    "A9-CONTROL-genuine-green",
    "A10-CONTROL-unacknowledged-disagreement",
}


def main():
    reg = load_register()
    load_corpus()
    tmp = Path(tempfile.mkdtemp(prefix=".t308-thmB-", dir=str(CAP)))
    try:
        print("T308 -- IS GUARD #10 IMPOSSIBLE, OR MERELY UNACHIEVED?")
        print("=" * 100)
        print("  %-56s %8s %8s" % ("document", "CENSUS", "SIBLING"))
        print("  %-56s %8s %8s" % ("", "(T292)", "(T308)"))
        print("  " + "-" * 74)
        cens_bad, sib_bad = [], []
        for name in sorted(CORPUS):
            doc = CORPUS[name]
            c = g10_census(doc, reg)
            s = g10_sibling(doc, reg)
            print("  %-56s %8d %8d" % (name, len(c), len(s)))
            for h in s:
                print("        SIBLING REFUSES: %s %s %r  (owner %s, container %s)"
                      % (h[1], h[0], h[2], h[3], h[4]))
            # grade both candidate guards against the stated requirement
            if name in WANT_REFUSE:
                if not c:
                    cens_bad.append((name, "should REFUSE, census sees 0"))
                if not s:
                    sib_bad.append((name, "should REFUSE, sibling sees 0"))
            if name in WANT_PERMIT:
                if c:
                    cens_bad.append((name, "should PERMIT, census sees %d" % len(c)))
                if s:
                    sib_bad.append((name, "should PERMIT, sibling sees %d" % len(s)))
        print()
        print("=" * 100)
        print("GRADED AGAINST GUARD #10's STATED AMBITION")
        print("  requirement REFUSE : %s" % ", ".join(sorted(WANT_REFUSE)))
        print("  requirement PERMIT : %s" % ", ".join(sorted(WANT_PERMIT)))
        print()
        print("  T292's SHIPPED CENSUS, promoted to a refusal : %d violations" % len(cens_bad))
        for n, why in cens_bad:
            print("      %-56s %s" % (n, why))
        print("  T308's SIBLING COUNTER-RULE                  : %d violations" % len(sib_bad))
        for n, why in sib_bad:
            print("      %-56s %s" % (n, why))
        print()
        if not sib_bad:
            print("RESULT: a separator EXISTS. It needs NO register change, NO external")
            print("  declaration and NO new input -- only the SIBLING RELATION, which is")
            print("  container structure. T292's 'unachievable by any container-blind rule' is")
            print("  therefore TRUE AS LITERALLY SCOPED and MISLEADING AS APPLIED: guard #10 is")
            print("  a DETECTION guard, and T292's own thesis grants detection the right to read")
            print("  containers. The impossibility was proved about the wrong rule class.")
        else:
            print("RESULT: the sibling counter-rule does NOT separate them. T292's claim stands")
            print("  on this construction.")
        print()
        print("HONEST LIMIT OF THE COUNTER-RULE, MEASURED, NOT ASSUMED: see the row")
        print("  EVASION-header-moved-INSIDE-the-records-list above. Moving the header into the")
        print("  records container defeats the sibling rule, exactly as P-91 predicts of any")
        print("  shape rule ('a guard phrased as a STRUCTURAL PATTERN over the shape of its")
        print("  input can always be re-nested one level out'). The finding is NOT that the")
        print("  sibling rule should ship. The finding is that 'IMPOSSIBLE' is the wrong word")
        print("  for something a 20-line predicate does on this corpus, and that the correct")
        print("  phrasing -- 'no CONTAINER-BLIND rule can, and we chose not to make guard #10")
        print("  container-aware' -- is a decision T292 did not record as one.")
        rc = 1 if sib_bad else 0
        print("EXIT %d" % rc)
        return rc
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
