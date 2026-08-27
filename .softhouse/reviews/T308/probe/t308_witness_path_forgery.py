#!/usr/bin/env python3
"""T308 session-2 -- ATTACK THE SECOND CLAUSE OF THEOREM 2: "a forgery is NAMED".

T292's declared floor is that coverage can only be raised by ASSERTING A FACT, and that this is
tolerable because EVERY WITNESS PATH IS PRINTED, so a forgery is NAMED and a reader can see it.
T308's first pass used that clause TWICE to downgrade severity -- CE3 ("not a security hole") and
F-T308-5 ("severity LOW ... the witness path is printed") -- and never tested the clause itself.

A floor that names forgeries is only as good as the naming.  The naming is this, verbatim:

    248  def walk_objects(v, path="$"):
    257          yield from walk_objects(x, path + "." + k)      # <- naive concatenation
    260              yield from walk_objects(x, path + "[%d]" % i)
    421      rep.witness.append(("%s.%s" % (opath, k), k, v))
    562  for wpath, wkey, wval in rep.witness:
    563      print("      %s = %s" % (wpath, "true" if wval else "false"))

The path is a STRING BUILT BY CONCATENATION FROM UNTRUSTED KEY NAMES, and it is printed with no
escaping, no quoting and no length cap.  Two attacks follow directly.

  A1  COLLISION.  A key literally named `cells[0]` renders as the same path as an object at index
      0 of a list named `cells`.  Two structurally different documents, ONE byte-identical
      printed witness line.  The forgery is printed -- under a legitimate document's name.

  A2  INJECTION.  A key containing a newline splits one witness line into several, and the
      attacker chooses what the extra lines say.  A forged document can print witness lines that
      it did not earn, formatted byte-identically to the ones it did.

  CTRL  the honest document, to prove the renderer is doing what I claim.

Exit 0 means every arm behaved as this file claims, INCLUDING the arms showing the forgery.
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


def run(target):
    r = subprocess.run([sys.executable, str(RULE), "--register", str(REG),
                        "--acknowledgements", str(ACK), str(target)],
                       capture_output=True, text=True, timeout=60)
    probe = None
    for ln in r.stdout.splitlines():
        if ln.startswith("T259-VPA:"):
            probe = ln
    return r.returncode, probe, r.stdout


def f(probe, name):
    if not probe:
        return None
    for t in probe.split():
        if t.startswith(name + "="):
            return t.split("=", 1)[1]
    return None


def witness_block(stdout):
    """The lines the rule prints as the witness listing -- the NAMING, verbatim."""
    out, grabbing = [], False
    for ln in stdout.splitlines():
        if ln.strip().startswith("WITNESS -- predicate reads"):
            grabbing = True
            continue
        if grabbing:
            if ln.strip().startswith("disagreements found"):
                break
            out.append(ln)
    return out


def main():
    print("T308 -- IS A FORGED WITNESS PATH DISTINGUISHABLE FROM A LEGITIMATE ONE?")
    print("=" * 96)
    print("THE NAMING, READ AT SOURCE (before any run):")
    src = RULE.read_text(encoding="utf-8").splitlines()
    for n in (257, 260, 421, 562, 563):
        print("      %d: %s" % (n, src[n - 1].rstrip()))
    print("      -> path is CONCATENATED from untrusted key names; printed unescaped, unquoted,")
    print("         uncapped.")
    print()

    tmp = Path(tempfile.mkdtemp(prefix=".t308-forge-",
                                dir=str(ROOT / ".softhouse" / "reviews" / "T308")))
    try:
        # ---------- CTRL: the legitimate document. ------------------------------------
        honest = {"cells": [{"P1_principalAmortizesToZero": True, "verdict": "AS PREDICTED"}]}
        ph = tmp / "ctrl-honest.json"
        ph.write_text(json.dumps(honest, indent=1), encoding="utf-8")
        rc_h, p_h, so_h = run(ph)
        wb_h = witness_block(so_h)
        print("CTRL  LEGITIMATE  {\"cells\": [ {\"P1_...\": true, \"verdict\": \"AS PREDICTED\"} ]}")
        print("      rc=%s witness=%s   naming printed:" % (rc_h, f(p_h, "witness")))
        for ln in wb_h:
            print("      | %s" % ln)
        print()

        # ---------- A1: COLLISION. A key literally named `cells[0]`. -------------------
        forged = {"cells[0]": {"P1_principalAmortizesToZero": True, "verdict": "AS PREDICTED"}}
        pf = tmp / "a1-collision.json"
        pf.write_text(json.dumps(forged, indent=1), encoding="utf-8")
        rc_f, p_f, so_f = run(pf)
        wb_f = witness_block(so_f)
        print("A1    FORGED      {\"cells[0]\": {\"P1_...\": true, \"verdict\": \"AS PREDICTED\"}}")
        print("      rc=%s witness=%s   naming printed:" % (rc_f, f(p_f, "witness")))
        for ln in wb_f:
            print("      | %s" % ln)
        collision = (wb_h == wb_f and rc_h == rc_f == 0)
        print("      DOCUMENTS DIFFER: %s"
              % (ph.read_bytes() != pf.read_bytes()))
        print("      PRINTED NAMING BYTE-IDENTICAL: %s"
              % ("YES -- the forgery is NOT distinguishable by its name" if collision else "no"))
        print("      coverageDigest honest=%s forged=%s  -> %s"
              % (f(p_h, "coverageDigest"), f(p_f, "coverageDigest"),
                 "ALSO IDENTICAL" if f(p_h, "coverageDigest") == f(p_f, "coverageDigest")
                 else "differs"))
        print()

        # ---------- A2: INJECTION. A key carrying a newline. ---------------------------
        inj_key = "z\n      $.cells[0].P7_reconciledAgainstOracle = true\n      x"
        injected = {inj_key: {"P1_principalAmortizesToZero": True, "verdict": "AS PREDICTED"}}
        pi = tmp / "a2-injection.json"
        pi.write_text(json.dumps(injected, indent=1), encoding="utf-8")
        rc_i, p_i, so_i = run(pi)
        wb_i = witness_block(so_i)
        print("A2    FORGED      a container key containing a NEWLINE and a fabricated witness line")
        print("      rc=%s witness=%s (the COUNT says %s)   naming printed:"
              % (rc_i, f(p_i, "witness"), f(p_i, "witness")))
        for ln in wb_i:
            print("      | %s" % ln)
        fabricated = "$.cells[0].P7_reconciledAgainstOracle = true"
        injected_line_present = any(ln.strip() == fabricated for ln in wb_i)
        lines_exceed_count = len([l for l in wb_i if l.strip()]) > int(f(p_i, "witness") or 0)
        print("      a line reading %r appears in the witness block: %s"
              % (fabricated, "YES" if injected_line_present else "no"))
        print("      printed witness LINES (%d) exceed the reported witness COUNT (%s): %s"
              % (len([l for l in wb_i if l.strip()]), f(p_i, "witness"),
                 "YES" if lines_exceed_count else "no"))
        print("      that fabricated line names a predicate `P7_reconciledAgainstOracle` the")
        print("      document never asserted and the register never classified -- a reader")
        print("      auditing the naming reads a fact that was never graded.")
        print()

        print("RESULT, STATED AS MEASURED AND NOT WIDER:")
        print("  THEOREM 2's second clause -- 'every witness path is printed so a forgery is")
        print("  NAMED' -- is TRUE that a line is printed and FALSE that the line identifies the")
        print("  forgery.  The name is not a name: it is an unescaped concatenation of")
        print("  attacker-chosen key strings, so it can be made to COLLIDE with a legitimate")
        print("  document's name (A1) or to CARRY EXTRA LINES OF ITS OWN CHOOSING (A2).")
        print()
        print("  CONSEQUENCE FOR THIS REVIEW: the clause was used to downgrade CE3 (F-T308-1)")
        print("  and F-T308-5 to 'not a security hole' / LOW.  Those downgrades rest on a naming")
        print("  that does not hold.  Both are re-stated in REVIEW.md; neither becomes a defect")
        print("  in the money, because the rule still has NO CALLER.")
        print()
        print("  FIX (mechanical): render the path as a JSON-escaped segment list --")
        print("  json.dumps(k) per segment -- so `cells[0]` prints as \"cells[0]\" and a newline")
        print("  prints as \\n.  One line at 257/260/421.  Then A1 and A2 both become visible.")
        ok = collision and injected_line_present and lines_exceed_count and rc_h == 0
        print()
        print("EXIT %d   (0 means every arm behaved as claimed, INCLUDING the arms showing the "
              "forgery)" % (0 if ok else 1))
        return 0 if ok else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
