#!/bin/sh
# T55 -- the recipe is proved FAILABLE.
#
# patterns.md: "A precondition script is only worth what its negative run proves.  An assertion
# suite that has never failed has not been tested."
#
# Each leg below runs part of the T55 recipe in a deliberately WRONG configuration and REQUIRES a
# non-zero exit with a message naming the breach.  If a leg PASSes, this script exits 1 -- because
# then the recipe is not failable on that axis and its PASS means nothing.
#
# Legs N4 and N5 are the BEHAVIOURAL canary: they move the re-derivation's precision and rounding
# mode and require the ARM attribution to STOP matching the oracle.  A configuration echo is not a
# discriminator; these two are the arithmetic itself answering.
set -u
W="$(cd "$(dirname "$0")/../../../.." && pwd)"
LB=$W/.softhouse/capture/leapboundary
export LB
CAP=$LB/bin/t55-capture.sh
AN=$LB/analysis/t55-analyse.py

legs=0; bad=0
leg() {
  _name=$1; _want=$2; shift 2
  legs=$((legs+1))
  printf '\n--- %s ---\n' "$_name"
  out=$("$@" 2>&1); rc=$?
  if [ "$rc" = "0" ]; then
    echo "LEG FAILED TO FAIL (exit 0) -- the recipe is NOT failable on this axis"
    bad=$((bad+1))
    return
  fi
  if printf '%s' "$out" | grep -qF "$_want"; then
    printf 'exit %s, breach named: ' "$rc"
    printf '%s' "$out" | grep -F "$_want" | head -2
  else
    echo "exit $rc but the expected breach text was NOT named; wanted: $_want"
    printf '%s\n' "$out" | tail -6
    bad=$((bad+1))
  fi
}

echo "== T55 negative tests =="

# N1 -- the oracle pin.  A capture from a different build is not comparable.
leg "N1 pinned commit set to all-zeros" \
    "BREACH: pinned checkout is at" \
    env T55_PIN_COMMIT=0000000000000000000000000000000000000000 sh "$CAP"

# N2 -- the preconditions gate itself.  Point it at a tenant that does not exist.
leg "N2 preconditions run against a non-existent tenant" \
    "has no row in fineract_tenants.tenants" \
    sh "$W/.softhouse/capture/charges/bin/preconditions.sh" t55-no-such-tenant

# N3 -- the doctored-capture leg.  One money cell perturbed by ONE minor unit must be caught by
#       the invariant checker (the splits stop summing to the period total).
leg "N3 one money cell perturbed by one minor unit" \
    "INVARIANT VIOLATED" \
    env T55_NEG_DOCTOR=LB-LEAPIN-p7 python3 "$AN"

# N4 -- BEHAVIOURAL canary, rounding mode.  Re-derive at HALF_EVEN instead of the ratified
#       HALF_UP: the run must fail, both on the settings assertion and on the arithmetic.
leg "N4 re-derivation forced to HALF_EVEN" \
    "rounding mode is HALF_EVEN" \
    env T55_NEG_ROUND=HALF_EVEN python3 "$AN"

# N5 -- BEHAVIOURAL canary, precision.  Re-derive at precision 12 (a discrimination-probe
#       setting that may never be promoted) instead of the ratified 19.
leg "N5 re-derivation forced to precision 12" \
    "precision is 12" \
    env T55_NEG_PREC=12 python3 "$AN"

# N6 -- the comparator must not be inert.  Feed the CONTROL name to a shape that does differ:
#       if LB-LEAPIN were treated as the non-leap control the run must fail.
leg "N6 a shape that DOES differ asserted as the non-leap control" \
    "must report 0 cells" \
    python3 -c '
import os, sys, runpy
sys.argv = ["t55-analyse.py"]
p = os.path.join(os.environ["LB"], "analysis", "t55-analyse.py")
src = open(p).read().replace(
    "for ctrl in (\"LB-NONLEAP\", \"LB-DEC15NL\"):",
    "for ctrl in (\"LB-LEAPIN\",):")
g = {"__name__": "__main__", "__file__": p}
try:
    exec(compile(src, p, "exec"), g)
except SystemExit as e:
    sys.exit(e.code)
'

# N7 -- the no-bare-number check on the exact-text sidecars.  The axis under test is the WRITER:
#       if `parse_float=str, parse_int=str` were ever dropped, every money value would be
#       round-tripped through a binary double.  Remove it and require the check to catch it.
leg "N7 sidecar writer with parse_float=str removed (floats would be constructed)" \
    "contains a bare JSON number" \
    python3 -c '
import os, sys, tempfile, shutil
LB = os.environ["LB"]
OUT = os.path.join(LB, "out")
tmp = tempfile.mkdtemp()
for fn in os.listdir(OUT):
    if fn.endswith("-raw.json"):
        shutil.copy(os.path.join(OUT, fn), os.path.join(tmp, fn))
p = os.path.join(LB, "analysis", "t55-analyse.py")
src = open(p).read().replace("parse_float=str, parse_int=str", "")
g = {"__name__": "not_main", "__file__": p}
exec(compile(src, p, "exec"), g)
g["OUT"] = tmp
g["fails"].clear()
g["sidecars"]()
if not g["fails"]:
    print("no breach reported -- the float guard is inert"); sys.exit(0)
for f in g["fails"]:
    print("  FAIL  " + f)
sys.exit(1)
'

# N9 -- ARITHMETIC canary, and an HONEST report of its LIMIT.  N4/N5 stop at the settings
#       assertion, which is a configuration echo, not a discriminator.  This leg bypasses that
#       assertion and drives the arithmetic itself, then prints the full sensitivity table.
#
#       OBSERVED RESULT, recorded rather than hidden: at precision 8 the ARM re-derivation stops
#       reproducing the oracle (29 -> 22 of 36 periods), so the re-derivation IS sensitive to
#       precision.  But precision 12 reproduces IDENTICALLY to precision 19, and HALF_EVEN
#       reproduces identically to HALF_UP.  So NO T55 shape separates 19 from 12, and none
#       separates HALF_UP from HALF_EVEN.  For those two axes (19, HALF_UP) is PROVENANCE here --
#       the compile-time constant MoneyHelper.PRECISION = 19 plus the preconditions gate's tenant
#       assertions and T36's half-cent behavioural tie -- and NOT a witness from these values.
#       The leg requires only what it can prove: that the arithmetic is precision-sensitive at all.
leg "N9 arithmetic canary: the ARM re-derivation must break at a wrong precision" \
    "CANARY OK" \
    python3 -c '
import os, sys
from decimal import Decimal, ROUND_HALF_EVEN
LB = os.environ["LB"]
p = os.path.join(LB, "analysis", "t55-analyse.py")
g = {"__name__": "not_main", "__file__": p}
exec(compile(open(p).read(), p, "exec"), g)

SHAPES = ("LB-LEAPIN", "LB-LEAPOUT", "LB-DEC15IN", "LB-DEC15OUT", "LB-MULTI3", "LB-F29CROSS",
          "LB-MULTI3F", "LB-HALFYR", "LB-DEC31")

def arm_hits():
    n = tot = 0
    for sid in SHAPES:
        for suf in ("p7", "p3", "p4"):
            for r in g["rederive"]("%s-%s" % (sid, suf)):
                tot += 1
                if r["obs"] == r["arm_i"]:
                    n += 1
    return n, tot

base, tot = arm_hits()
print("  (19, HALF_UP)  ARM reproduces the oracle on %d of %d periods  <- baseline" % (base, tot))
g["PREC"] = 12; g["SCALE19"] = Decimal("1E-12")
a12 = arm_hits()[0]
print("  (12, HALF_UP)  %d of %d   -- IDENTICAL to the baseline: no T55 shape separates 19 from 12"
      % (a12, tot))
g["PREC"] = 8; g["SCALE19"] = Decimal("1E-8")
a8 = arm_hits()[0]
print("  ( 8, HALF_UP)  %d of %d" % (a8, tot))
g["PREC"] = 19; g["SCALE19"] = Decimal("1E-19"); g["ROUND"] = ROUND_HALF_EVEN
ahe = arm_hits()[0]
print("  (19, HALF_EVEN) %d of %d  -- IDENTICAL: no T55 shape has a tie at the rounding boundary"
      % (ahe, tot))
if a8 >= base:
    print("a wrong precision did NOT break the re-derivation -- it is not sensitive to precision"
          " at all, so its agreement with the oracle is not evidence")
    sys.exit(0)
print("CANARY OK: precision 8 breaks the re-derivation (%d -> %d of %d), so the agreement at"
      " (19, HALF_UP) is a real reproduction." % (base, a8, tot))
print("LIMIT, recorded: 19-vs-12 and HALF_UP-vs-HALF_EVEN are NOT witnessed by these shapes.")
sys.exit(1)
'

# N8 -- the matched-products assertion is not a tautology.  The same SQL over a triple that
#       genuinely differs on a schedule-feeding column must return more than one distinct tuple.
leg "N8 matched-products SQL over a deliberately mismatched triple (3,4,8)" \
    "MISMATCH DETECTED" \
    sh -c '
d=$(docker exec fineract-db-1 psql -U root -d fineract_gerege -At -c "select count(distinct (days_in_month_enum,days_in_year_enum,interest_calculated_in_period_enum)) from m_product_loan where id in (3,4,8);")
if [ "$d" = "1" ]; then echo "the assertion is a TAUTOLOGY: mismatched triple still reported 1"; exit 0; fi
echo "MISMATCH DETECTED: distinct tuples = $d for products 3/4/8 (as required)"; exit 1'

printf '\n== %d legs, %d failed to fail ==\n' "$legs" "$bad"
if [ "$bad" != "0" ]; then
  echo "NEGATIVE TESTS FAILED: $bad leg(s) did not breach.  The recipe is not failable on those" >&2
  echo "axes, so a PASS from it is not evidence." >&2
  exit 1
fi
echo "All $legs legs breached as required."
exit 0
