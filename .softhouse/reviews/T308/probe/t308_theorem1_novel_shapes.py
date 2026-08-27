#!/usr/bin/env python3
"""T308 session-2 -- THEOREM 1, the shapes the brief named that NOBODY HAS TRIED.

Pass 1 attacked Theorem 1 with four operations (CE1 list-wrap, CE2 object-wrap, CE3 P-key-wrap,
CTRL root-promotion) and found three not invariant.  The brief then named six MORE shapes.  This
file drives every one of them and says, for each, whether it moved the WITNESS COUNT -- and where
the shape is not expressible at all, it says so, because "not found" must be a statement about
the search.

  S1  a key that is itself a container
  S2  a bool leaf under a non-string key
  S3  a document that is a bare `true`
  S4  deeply-nested empty containers
  S5  a JSON object with duplicate keys at DIFFERENT depths
  S6  anchors / aliases, if the loader admits them
  S7  (mine) top-level JSON array   -- re-run of a T291 attack
  S8  (mine) list-of-lists to depth 4 -- re-run of a T291 attack

BASE is a legitimate one-witness document.  A shape PASSES the theorem iff witness count and the
multiset of (key,value) pairs are unchanged.  Exit 0 means the run completed and every row is
reported; the VERDICT COLUMN, not the exit code, carries the finding.
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
REG = T256 / "boolean-key-register.json"
ACK = T256 / "acknowledged.json"

BASE = {"cells": [{"P1_principalAmortizesToZero": True, "verdict": "AS PREDICTED"}]}


def run_raw(text, tmp, name):
    p = tmp / (name + ".json")
    p.write_text(text, encoding="utf-8")
    r = subprocess.run([sys.executable, str(RULE), "--register", str(REG),
                        "--acknowledgements", str(ACK), str(p)],
                       capture_output=True, text=True, timeout=60)
    probe = None
    for ln in r.stdout.splitlines():
        if ln.startswith("T259-VPA:"):
            probe = ln
    return r.returncode, probe


def f(probe, name):
    if not probe:
        return None
    for t in probe.split():
        if t.startswith(name + "="):
            return t.split("=", 1)[1]
    return None


def main():
    tmp = Path(tempfile.mkdtemp(prefix=".t308-shapes-",
                                dir=str(ROOT / ".softhouse" / "reviews" / "T308")))
    rows = []
    try:
        b_rc, b_p = run_raw(json.dumps(BASE, indent=1), tmp, "base")
        b_w, b_d = f(b_p, "witness"), f(b_p, "coverageDigest")
        print("T308 -- THEOREM 1 AGAINST THE SHAPES THE BRIEF NAMED")
        print("=" * 108)
        print("BASE  %s" % json.dumps(BASE))
        print("      rc=%s witness=%s coverageDigest=%s" % (b_rc, b_w, b_d))
        print()

        def shape(tag, desc, text, expressible=True, note=""):
            if not expressible:
                rows.append((tag, desc, "N/A", "N/A", "NOT EXPRESSIBLE", note))
                return
            rc, p = run_raw(text, tmp, tag)
            w, d = f(p, "witness"), f(p, "coverageDigest")
            if p is None:
                v = "NO PROBE (rc=%s)" % rc
            elif w == b_w and d == b_d:
                v = "INVARIANT"
            else:
                v = "*** NOT INVARIANT ***"
            rows.append((tag, desc, "rc=%s" % rc, "witness=%s" % w, v, note))

        # S1 -- a key that is itself a container.
        shape("S1", "a key that is itself a container", "", expressible=False,
              note="RFC 8259: a JSON member name MUST be a string. json.dumps refuses a dict key; "
                   "json.loads cannot produce one. The shape does not exist in this loader's "
                   "input language, so it cannot move anything. Checked, not assumed.")

        # S2 -- a bool leaf under a non-string key.
        shape("S2", "a bool leaf under a non-string key", "", expressible=False,
              note="Same reason as S1. The nearest expressible thing is the STRING \"true\" as a "
                   "key, which is S2b.")
        shape("S2b", "the string \"true\" used as an object KEY",
              json.dumps({"cells": [{"true": True, "P1_principalAmortizesToZero": True,
                                     "verdict": "AS PREDICTED"}]}, indent=1),
              note="`true` as a key is an affirmative WORD in key position -- T286's guard #10 "
                   "territory -- but it is not a PREDICATE key, so it must not buy coverage.")

        # S3 -- a document that is a bare `true`.
        shape("S3", "the whole document is the bare literal `true`", "true",
              note="Must REFUSE through nil coverage; it grades nothing.")

        # S4 -- deeply-nested empty containers.
        deep = BASE
        for i in range(12):
            deep = {"_e%d" % i: deep, "_empty%d" % i: {}, "_arr%d" % i: []}
        shape("S4", "12 levels of nesting, each adding an empty {} and an empty []",
              json.dumps(deep, indent=1),
              note="Pure container insertion. The theorem's own operation class.")

        # S5 -- duplicate keys at DIFFERENT depths (legal JSON; G7 only refuses same-level dupes).
        shape("S5", "the same key name reused at three DIFFERENT depths",
              json.dumps({"cells": [{"P1_principalAmortizesToZero": True,
                                     "verdict": "AS PREDICTED"}],
                          "outer": {"cells": {"cells": {}}}}, indent=1),
              note="Legal JSON. G7 refuses duplicates at the SAME level only; different depths "
                   "are not duplicates.")
        shape("S5b", "the same PREDICATE key at two different depths (both true)",
              json.dumps({"cells": [{"P1_principalAmortizesToZero": True,
                                     "verdict": "AS PREDICTED"}],
                          "outer": {"P1_principalAmortizesToZero": True,
                                    "verdict": "AS PREDICTED"}}, indent=1),
              note="NOT a container-only rewriting -- it ADDS an assertion. Included as the "
                   "CONTROL that proves the witness counter can move at all on this population.")

        # S6 -- anchors / aliases.
        shape("S6", "YAML anchors / aliases", "", expressible=False,
              note="The loader is `json.loads(..., parse_float=Decimal, "
                   "object_pairs_hook=<dupe-refusing>)` [read at source]. There is no YAML path "
                   "and no `yaml` import in the file. Anchors are not admitted, so they cannot "
                   "move coverage. Checked by reading the loader, not by assuming.")

        # S7 -- top-level JSON array (T291 attack, re-run).
        shape("S7", "the whole document promoted into a top-level ARRAY",
              json.dumps([BASE], indent=1), note="T291 attack, re-run.")

        # S8 -- list-of-lists to depth 4 (T291 attack, re-run).
        nest = BASE
        for _ in range(4):
            nest = [nest]
        shape("S8", "list-of-lists, depth 4", json.dumps(nest, indent=1),
              note="T291 attack, re-run.")

        w = (6, 62, 8, 12, 24)
        print("%-*s%-*s%-*s%-*s%-*s" % (w[0], "shape", w[1], "operation", w[2], "exit",
                                        w[3], "coverage", w[4], "verdict"))
        print("-" * 108)
        for tag, desc, rc, wit, v, note in rows:
            print("%-*s%-*s%-*s%-*s%-*s" % (w[0], tag, w[1], desc[:w[1] - 2], w[2], rc,
                                            w[3], wit, w[4], v))
        print()
        print("NOTES, so that 'not found' is a statement about the search:")
        for tag, desc, _, _, _, note in rows:
            if note:
                print("  %-5s %s" % (tag, note))
        print()
        moved = [t for t, _, _, _, v, _ in rows if v.startswith("***")]
        na = [t for t, _, _, _, v, _ in rows if v == "NOT EXPRESSIBLE"]
        print("SUMMARY: %d shapes driven, %d not expressible in this loader's input language (%s),"
              % (len(rows) - len(na), len(na), ", ".join(na)))
        print("         %d moved coverage: %s" % (len(moved), ", ".join(moved) or "none"))
        print()
        print("EXIT 0   (the VERDICT COLUMN carries the finding, not the exit code)")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
