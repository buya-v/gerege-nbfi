#!/usr/bin/env python3
"""T259 — INDEPENDENT re-derivation of the driver's "five and three" measurement.

Nothing here is inherited from the task brief or from T241's banner (P-63). Every figure is
re-counted from the committed bytes of `../t229-g8-site3/out/classify-t229.json`, and the file's
sha256 + git blob id are printed so the count is stamped with what it counted (P-69).

WHAT IS COUNTED, BOTH TERMS (P-67):
  * rows carrying `P2_totalInterestEqualsNEplusB` AT ALL          (denominator)
  * rows where it is `false`                                      (the driver says 5)
  * of those, rows whose `verdict` is affirmative                 (the driver says 3)
  * rows where it is `true`                                       (the complement)
  * rows carrying NO P2 key at all                                (the population the driver's
    two numbers are silent about -- counted here because P-67 says count both terms)

NO FLOATING POINT. `json.load(..., parse_float=Decimal)` (T145). This file REPRODUCES NOTHING --
it is new, it is not a successor to a script that loaded without `parse_float`, so T207's ruling
("`add parse_float` is sometimes the WRONG repair, when a line faithfully REPRODUCES an earlier
script that loaded without it", `.softhouse/capture/audit-t44/analysis/T207/`) does not apply and
the guard is simply added. Measured fact recorded alongside: classify-t229.json contains
**0 float-shaped numeric tokens** out of 160, so the guard is a belt on a corpus that cannot
currently trip it -- stated so nobody later mistakes a latent hazard for a live one.

Exit: 0 = counted, 2 = could not count (IO/parse). It draws NO verdict; that is what
`check_verdict_predicate_agreement.py` is for.
"""
import hashlib
import json
import re
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = (HERE / ".." / "t229-g8-site3" / "out" / "classify-t229.json").resolve()

# The affirmative verdict vocabulary, kept in one place and shared with the checker by import.
AFFIRMATIVE = {"AS PREDICTED", "AS_PREDICTED", "PASS", "PASSED", "OK", "CONFIRMED",
               "REPRODUCED", "GREEN", "HELD", "AS-PREDICTED"}
NEGATIVE = {"REFUTED", "FAIL", "FAILED", "DIFFERS", "RED", "MISSING", "BROKEN", "VIOLATED"}


def stamp(path: Path) -> dict:
    """sha256 of the bytes on disk, plus the git blob id at HEAD if git can be reached."""
    b = path.read_bytes()
    out = {"path": str(path), "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()}
    try:
        rev = f"HEAD:{path.relative_to(_repo_root())}"
        out["gitBlobAtHead"] = subprocess.run(
            ["git", "rev-parse", rev], cwd=str(_repo_root()), capture_output=True,
            text=True, check=True).stdout.strip()
        out["headCommit"] = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(_repo_root()), capture_output=True,
            text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, ValueError, OSError) as exc:
        # A missing stamp is reported, NEVER silently omitted (P-80: absence != error).
        out["gitBlobAtHead"] = f"UNAVAILABLE: {type(exc).__name__}"
    return out


def _repo_root() -> Path:
    p = HERE
    while p != p.parent:
        if (p / ".git").exists():
            return p
        p = p.parent
    raise ValueError("no .git ancestor")


def float_token_census(path: Path) -> tuple:
    """Count numeric tokens and float-shaped ones in the raw bytes -- both terms (P-67)."""
    s = path.read_text()
    toks = re.findall(r'(?<![\w."])-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?(?![\w.])', s)
    fl = [t for t in toks if "." in t or "e" in t.lower()]
    return len(toks), len(fl)


def main() -> int:
    if not TARGET.exists():
        print(f"REFUSED: target absent: {TARGET}", file=sys.stderr)
        return 2
    st = stamp(TARGET)
    print("T259 RE-DERIVATION -- independent recount of the 'five and three' claim")
    print(f"  target       : {st['path']}")
    print(f"  bytes        : {st['bytes']}")
    print(f"  sha256       : {st['sha256']}")
    print(f"  git blob@HEAD: {st['gitBlobAtHead']}")
    print(f"  HEAD commit  : {st.get('headCommit', 'UNAVAILABLE')}")
    ntok, nfloat = float_token_census(TARGET)
    print(f"  float census : {nfloat} float-shaped of {ntok} numeric tokens "
          f"(both terms counted, P-67)")

    doc = json.loads(TARGET.read_text(), parse_float=Decimal)
    cells = doc.get("cells")
    if not isinstance(cells, list):
        print("REFUSED: no 'cells' list", file=sys.stderr)
        return 2

    key = "P2_totalInterestEqualsNEplusB"
    present, absent = [], []
    for c in cells:
        (present if key in c else absent).append(c)
    false_rows = [c for c in present if c[key] is False]
    true_rows = [c for c in present if c[key] is True]
    other = [c for c in present if c[key] not in (True, False)]

    def verdict_of(c):
        return str(c.get("verdict", "<ABSENT>")).strip().upper()

    false_affirm = [c for c in false_rows if verdict_of(c) in AFFIRMATIVE]
    false_neg = [c for c in false_rows if verdict_of(c) in NEGATIVE]
    false_unk = [c for c in false_rows
                 if verdict_of(c) not in AFFIRMATIVE and verdict_of(c) not in NEGATIVE]

    print()
    print(f"  rows in file                                   : {len(cells)}")
    print(f"  rows CARRYING  {key}   : {len(present)}")
    print(f"  rows LACKING   {key}   : {len(absent)}")
    print(f"  ... of the carriers, value false               : {len(false_rows)}")
    print(f"  ... of the carriers, value true                : {len(true_rows)}")
    print(f"  ... of the carriers, value neither true/false  : {len(other)}")
    print(f"  ... of the FALSE rows, verdict AFFIRMATIVE     : {len(false_affirm)}")
    print(f"  ... of the FALSE rows, verdict NEGATIVE        : {len(false_neg)}")
    print(f"  ... of the FALSE rows, verdict UNCLASSIFIED    : {len(false_unk)}")
    print()
    print("  the FALSE rows, one line each:")
    for c in false_rows:
        print(f"    {c['id']:<26} verdict={c.get('verdict')!r:<16} "
              f"predictedOutcome={c.get('predictedOutcome')!r}")
    print()
    print("  the rows LACKING the key (the population the 'five and three' is silent about):")
    for c in absent:
        print(f"    {c['id']:<26} verdict={c.get('verdict')!r:<16} "
              f"predictedOutcome={c.get('predictedOutcome')!r}")

    # The corrected identity T241 states: totalInterest == n*E + B - principalRepaid.
    # Re-derived here from the SAME recorded row fields, in INTEGER MINOR UNITS ONLY, because the
    # whole argument in DECISION-verdict-vs-predicate.md turns on whether the corrected predicate
    # holds where the registered one failed. Integers throughout; no Decimal division anywhere.
    print()
    print("  CORRECTED third conjunct, re-derived per row  "
          "(interest == n*E_observed + B - principalRepaid):")
    agree = disagree = 0
    for c in present:
        n = c["n"]
        e_obs = c["observedRow1TotalMinor"]
        b = c["bMinor"]
        prin = c["observedPrincipalMinor"]
        lhs = c["observedInterestMinor"]
        rhs = n * e_obs + b - prin
        ok = lhs == rhs
        agree += ok
        disagree += (not ok)
        print(f"    {c['id']:<26} registered={str(c[key]):<5} corrected={str(ok):<5} "
              f"observed={lhs:<8} n*E+B-P={rhs:<8} verdict={c.get('verdict')!r}")
    print(f"    -> corrected form HOLDS on {agree} of {len(present)} carriers, "
          f"fails on {disagree}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
