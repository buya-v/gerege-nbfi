#!/usr/bin/env python3
"""T27 re-check probe — MUTATION TESTING of the two invariant checkers T25 repaired.

=======================================================================
NOT RUN AGAINST A LIVE ORACLE. No Fineract instance and no PostgreSQL is
reachable in this sandbox. This script makes NO oracle observation and
synthesizes NO oracle value. It takes an ALREADY-COMMITTED capture
artifact, deliberately CORRUPTS one money literal by ONE MINOR UNIT by
SURGICAL TEXT EDIT of the raw bytes, and asserts that the repaired
checker REPORTS A FAILURE. Its only purpose is to prove the repaired
checks are genuinely failable rather than hard-coded to PASS.
=======================================================================

No floating-point is ever constructed: mutation is a byte-level string
substitution and the arithmetic is `decimal.Decimal` in minor units.
The mutated files live in a temp dir and are never committed.

Usage:
  python3 t27_mutate.py            # both suites
  python3 t27_mutate.py pathb      # Path B checker only
  python3 t27_mutate.py passa      # Path A checker only

Targets under test:
  .softhouse/capture/pathb/t22-probe/invariants.py   (T22 P1-13: I5 was
      `verdict("I5", True, ...)` -> could never fail)
  .softhouse/capture/out/t21-probe-invariants.py     (T21 P1-5: X2 was a
      naive roll-forward, invalid for P-03's pre-disbursement snapshot row;
      replaced by the audit's position-aware A3)
"""
import os
import re
import subprocess
import sys
import tempfile
from decimal import Decimal

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
TMP = tempfile.mkdtemp(prefix="t27-mut-")


def run(script, *args):
    p = subprocess.run([sys.executable, script, *args], capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def bump_literal(text, pattern, occurrence, delta_minor):
    """Add delta_minor minor units to the `occurrence`-th (1-based) money literal
    matched by `pattern` (one capture group = the numeric literal). Exact decimal,
    scale preserved, no float anywhere."""
    hits = list(re.finditer(pattern, text))
    if len(hits) < occurrence:
        raise AssertionError("only %d matches for %r" % (len(hits), pattern))
    m = hits[occurrence - 1]
    lit = m.group(1)
    scale = len(lit.split(".")[1]) if "." in lit else 0
    new = Decimal(lit) + Decimal(delta_minor).scaleb(-scale if scale else 0)
    new_lit = format(new.quantize(Decimal(1).scaleb(-scale)), "f")
    return text[:m.start(1)] + new_lit + text[m.end(1):], lit, new_lit


def write(name, text):
    p = os.path.join(TMP, name)
    with open(p, "w") as fh:
        fh.write(text)
    return p


# --------------------------------------------------------------- Path B
def pathb():
    src = os.path.join(ROOT, ".softhouse/capture/pathb/out/B-01-baseline-raw.json")
    chk = os.path.join(ROOT, ".softhouse/capture/pathb/t22-probe/invariants.py")
    base = open(src).read()
    ok = {}

    print("### control: unmutated B-01 through the repaired checker")
    rc, out = run(chk, src + "::B-01-CONTROL")
    print("   rc=%d  %s" % (rc, [l for l in out.splitlines() if l.startswith("OVERALL")][0]))
    assert rc == 0, "control must PASS"

    # Mutation 1 -- break I5 (per-period principal+interest+fee+penalty == total).
    txt, old, new = bump_literal(base, r'"interestDue":([0-9]+\.[0-9]+)', 2, 1)
    p1 = write("mut-i5.json", txt)
    print("\n### mutation 1: 2nd interestDue %s -> %s  (must break I5)" % (old, new))
    rc, out = run(chk, p1 + "::B-01-MUT-I5")
    for l in out.splitlines():
        if l.strip().startswith("I5"):
            print("   " + l.strip())
    ok["I5-pathB"] = rc != 0 and any("**FAIL**" in l for l in out.splitlines()
                                     if l.strip().startswith("I5"))

    # Mutation 2 -- break S2 (running balance tie).
    txt, old, new = bump_literal(
        base, r'"principalLoanBalanceOutstanding":([0-9]+\.[0-9]+)', 4, 1)
    p2 = write("mut-s2.json", txt)
    print("\n### mutation 2: 4th principalLoanBalanceOutstanding %s -> %s (must break S2)"
          % (old, new))
    rc, out = run(chk, p2 + "::B-01-MUT-S2")
    for l in out.splitlines():
        if l.strip().startswith("S2"):
            print("   " + l.strip())
    ok["S2-pathB"] = rc != 0 and any("**FAIL**" in l for l in out.splitlines()
                                     if l.strip().startswith("S2"))

    print("\n   >>> " + "  ".join("%s=%s" % (k, "FAILABLE" if v else "STILL-FAKE")
                                  for k, v in ok.items()))
    return all(ok.values())


# --------------------------------------------------------------- Path A
def cap_slice(text, cid):
    """Byte range of one capture object in capture-prod-raw.json, located by id."""
    i = text.index('"id": "%s"' % cid)
    nxt = text.find('"id": "', i + 10)
    return i, (nxt if nxt != -1 else len(text))


def passa():
    src = os.path.join(ROOT, ".softhouse/capture/out/capture-prod-raw.json")
    chk = os.path.join(ROOT, ".softhouse/capture/out/t21-probe-invariants.py")
    base = open(src).read()
    ok = {}

    print("### control: unmutated capture-prod-raw.json through the repaired checker")
    rc, out = run(chk, src)
    print("   rc=%d  %s" % (rc, out.strip().splitlines()[-1]))
    assert rc == 0, "control must PASS"

    def mutate_in(cid, pattern, occ, delta, name):
        lo, hi = cap_slice(base, cid)
        seg = base[lo:hi]
        seg2, old, new = bump_literal(seg, pattern, occ, delta)
        return write(name, base[:lo] + seg2 + base[hi:]), old, new

    def col(line, idx):
        return line.split()[idx]

    # A -- break the CORRECTED X2 on a normal capture (P-01): nudge one
    #      REPAYMENT row's emitted `balance`.
    p, old, new = mutate_in("P-01", r'"balance": "([0-9]+\.[0-9]+)"', 4, 1, "mut-x2-p01.json")
    print("\n### mutation A: P-01 4th repayment balance %s -> %s (must break X2)" % (old, new))
    rc, out = run(chk, p)
    line = [l for l in out.splitlines() if l.startswith("P-01")][0]
    print("   " + line + "    rc=%d" % rc)
    ok["X2-normal"] = rc != 0 and col(line, 8) == "!!"

    # B -- break the CORRECTED X2 on P-03, the capture whose pre-disbursement
    #      snapshot row made the OLD X2 report a spurious failure. If the new X2
    #      were merely disabled for P-03, this mutation would slip through.
    p, old, new = mutate_in("P-03", r'"principal": "([0-9]+\.[0-9]+)"', 2, 1, "mut-x2-p03.json")
    print("\n### mutation B: P-03 DISBURSEMENT principal %s -> %s (must break X1 and X2)"
          % (old, new))
    rc, out = run(chk, p)
    line = [l for l in out.splitlines() if l.startswith("P-03")][0]
    print("   " + line + "    rc=%d" % rc)
    ok["X2-p03"] = rc != 0 and col(line, 8) == "!!"

    # C -- break I5 in the Path A checker.
    p, old, new = mutate_in("P-MNT-5M", r'"total": "([0-9]+\.[0-9]+)"', 1, 1, "mut-i5-a.json")
    print("\n### mutation C: P-MNT-5M 1st repayment total %s -> %s (must break I5)"
          % (old, new))
    rc, out = run(chk, p)
    line = [l for l in out.splitlines() if l.startswith("P-MNT-5M")][0]
    print("   " + line + "    rc=%d" % rc)
    ok["I5-pathA"] = rc != 0 and col(line, 5) == "!!"

    # D -- control: the RETRACTED naive X2 formulation, re-implemented here, must
    #      still report the known spurious failure on the UNMUTATED P-03. This is
    #      what shows the repair changed the formulation and not merely the data.
    import json
    d = json.load(open(src))
    cap = [c for c in d["captures"] if c["id"] == "P-03"][0]
    dp = int(cap["inputs"]["currencyDecimalPlaces"])
    mn = lambda s: int((Decimal(s) * (10 ** dp)).to_integral_value())
    o = cap["observed"]
    bal = mn(o["totalDisbursedAmount"])
    naive_ok = True
    for pr in [x for x in o["periods"] if x["type"] == "REPAYMENT"]:
        bal -= mn(pr["principal"])
        if bal != mn(pr["balance"]):
            naive_ok = False
            break
    print("\n### control D: retracted NAIVE X2 on unmutated P-03 -> %s"
          % ("PASS" if naive_ok else "FAIL (the known spurious failure, as the audit says)"))
    ok["naive-X2-still-spuriously-fails"] = naive_ok is False

    print("\n   >>> " + "  ".join("%s=%s" % (k, "OK" if v else "NOT-OK") for k, v in ok.items()))
    return all(ok.values())


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    good = True
    if which in ("pathb", "both"):
        good &= pathb()
    if which in ("passa", "both"):
        print()
        good &= passa()
    print("\nT27 MUTATION VERDICT: %s"
          % ("ALL REPAIRED CHECKS ARE GENUINELY FAILABLE"
             if good else "AT LEAST ONE REPAIRED CHECK IS STILL NOT FAILABLE"))
    sys.exit(0 if good else 1)
