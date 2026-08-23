#!/usr/bin/env python3
"""T308 -- RE-DERIVE THEOREM 1 (container-blindness) BY CONSTRUCTION, NOT BY READING.

The theorem, verbatim from check_verdict_predicate_agreement_t292.py:

    Let T be any CONTAINER-ONLY rewriting of D: wrap a value in a list; wrap it in an object
    under a fresh key; re-nest to any depth; promote the root into a list; turn {k: v} into
    [{k: v}]; any composition of these.  T changes no leaf and adds or removes no registered
    predicate key.  Then W(T(D),R) and W(D,R) have the same cardinality and the same multiset
    of (key, value) pairs; only the `path` component differs.

    PROOF. W's membership test reads exactly two things: (a) is this value a `bool` LEAF, and
    (b) does R classify its key as PREDICATE.  Neither consults container structure. []

This probe applies the operations the theorem NAMES and prints the witness count on both sides.
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent.parent
CAP = ROOT / ".softhouse" / "capture" / "t286-t268-retry"
RULE = CAP / "check_verdict_predicate_agreement_t292.py"
T256 = ROOT / ".softhouse" / "capture" / "t256-verdict-predicate"


def run(doc, tmp, name):
    p = tmp / (name + ".json")
    p.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run([sys.executable, str(RULE),
                        "--register", str(T256 / "boolean-key-register.json"),
                        "--acknowledgements", str(T256 / "acknowledged.json"), str(p)],
                       capture_output=True, text=True, timeout=120)
    probe = None
    for ln in r.stdout.splitlines():
        if ln.startswith("T259-VPA:"):
            probe = ln
    w = d = st = None
    if probe:
        for tok in probe.split():
            if tok.startswith("witness="):
                w = tok.split("=", 1)[1]
            if tok.startswith("coverageDigest="):
                d = tok.split("=", 1)[1]
        st = probe.split()[1]
    return r.returncode, st, w, d


CASES = [
    ("CE1  wrap a BOOL LEAF in a list  ('wrap a value in a list')",
     {"cells": [{"id": "c1", "P2_x": True, "verdict": "AS PREDICTED"}]},
     {"cells": [{"id": "c1", "P2_x": [True], "verdict": "AS PREDICTED"}]}),

    ("CE2  wrap a BOOL LEAF in an object under a fresh NON-predicate key",
     {"cells": [{"id": "c1", "P2_x": True, "verdict": "AS PREDICTED"}]},
     {"cells": [{"id": "c1", "P2_x": {"_w0": True}, "verdict": "AS PREDICTED"}]}),

    ("CE3  wrap a DESCRIPTIVE bool leaf in an object under a fresh key matching the auto\n"
     "      predicate pattern -- 'wrap it in an object under a fresh key', verbatim",
     {"cells": [{"id": "c1", "t223RulePredictedRescue": True, "verdict": "AS PREDICTED"}]},
     {"cells": [{"id": "c1", "t223RulePredictedRescue": {"P9_z": True},
                 "verdict": "AS PREDICTED"}]}),

    ("CTRL  promote the root into a list (a rewriting the theorem DOES cover)",
     {"cells": [{"id": "c1", "P2_x": True, "verdict": "AS PREDICTED"}]},
     [{"cells": [{"id": "c1", "P2_x": True, "verdict": "AS PREDICTED"}]}]),
]


def main():
    tmp = Path(tempfile.mkdtemp(prefix=".t308-thmA-", dir=str(CAP)))
    bad = 0
    try:
        print("T308 -- THEOREM 1 (container-blindness) DRIVEN AGAINST THE OPERATIONS IT NAMES")
        print("=" * 96)
        print("  rule: %s" % RULE)
        print()
        for label, d, td in CASES:
            rc0, st0, w0, dg0 = run(d, tmp, "base")
            rc1, st1, w1, dg1 = run(td, tmp, "rewritten")
            same = (rc0 == rc1 and w0 == w1 and dg0 == dg1)
            print("  %s" % label)
            print("      D    : rc=%s %-8s witness=%-3s digest=%s" % (rc0, st0, w0, dg0))
            print("      T(D) : rc=%s %-8s witness=%-3s digest=%s" % (rc1, st1, w1, dg1))
            print("      -> %s" % ("INVARIANT (theorem holds on this operation)" if same
                                   else "*** NOT INVARIANT -- the theorem is FALSE on an "
                                        "operation it names ***"))
            print()
            if not same:
                bad += 1
        print("=" * 96)
        print("NON-INVARIANT OPERATIONS FOUND: %d of %d" % (bad, len(CASES)))
        print()
        print("READ THE DIRECTION, NOT ONLY THE COUNT:")
        print("  CE1/CE2 lose a witness -> GREEN becomes REFUSED. FAIL-CLOSED; harmless to")
        print("          safety, fatal to the theorem AS WRITTEN.")
        print("  CE3     GAINS a witness -> REFUSED becomes GREEN. This is the direction the")
        print("          corollary 'THE BRACKET IS POWERLESS' denies. It is rescued only by the")
        print("          theorem's SECOND hypothesis ('adds or removes no registered predicate")
        print("          key'), which the theorem's OWN operation list ('wrap it in an object")
        print("          under a fresh key') is able to violate. The operation set is not a")
        print("          subset of the hypothesis class.")
        print()
        print("SCOPE OF WHAT T292 ACTUALLY MEASURED: the adversary states that its generator")
        print("  inserts wrappers ONLY at positions already holding a dict or a list, and its")
        print("  object wrappers use keys _w<n> / _h<n>. So CE1, CE2 and CE3 are all OUTSIDE")
        print("  the generated family. The adversary is honest about that restriction; the")
        print("  RULE's docstring theorem is not scoped to match it.")
        print("EXIT %d" % (0 if bad == 0 else 1))
        return 0 if bad == 0 else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
