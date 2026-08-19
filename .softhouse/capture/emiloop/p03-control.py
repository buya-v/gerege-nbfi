#!/usr/bin/env python3
"""Complete the STAGE 1 control by covering the eleventh promoted vector, P-03.

P-03's disbursement falls exactly on repayment 1's due date, so the related repayment periods
are 2..6 and n = 5 (ProgressiveEMICalculator.java:250-263 -> ProgressiveLoanInterestScheduleModel
.java:195-197), while repayment row 1 is emitted all-zero. Modelling it is therefore the same
no-loop model over n = 5 with the disbursed balance, matched against the capture's rows 2..6.

If the no-loop model reproduces those five rows too, then the smoothing loop demonstrably changes
NOTHING on any of the eleven already-promoted vectors -- which is T9 finding F-2 restated as a
direct positive check rather than as a guard screen."""
import json
import os
import sys
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from noloop_model import noloop_schedule, guard  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
cases = {c["id"]: c for c in json.load(open(os.path.join(
    ROOT, ".softhouse/capture/out/capture-prod3b-raw.json")))["captures"]}

c = cases["P-03"]
rows = [p for p in c["observed"]["periods"] if p["type"] == "REPAYMENT"]
zero, paying = rows[0], rows[1:]
assert (zero["principal"], zero["interest"], zero["total"]) == ("0.00", "0.00", "0.00"), zero
print("P-03 row 1 is all-zero as expected: %r" % zero["total"])

m = noloop_schedule(c["inputs"]["disbursementAmount"], len(paying),
                    c["inputs"]["annualNominalInterestRate"])
print("no-loop model over n = %d: r = %s, raw EMI = %s" % (len(paying), m["r"], m["emi"]))
ok = True
for k, (mr, orow) in enumerate(zip(m["rows"], paying), start=2):
    same = (mr["principal"] == Decimal(orow["principal"])
            and mr["interest"] == Decimal(orow["interest"])
            and mr["closing"] == Decimal(orow["balance"])
            and mr["emi"] == Decimal(orow["total"]))
    ok = ok and same
    print("  period %d  principal %s/%s  interest %s/%s  balance %s/%s  %s"
          % (k, orow["principal"], mr["principal"], orow["interest"], mr["interest"],
             orow["balance"], mr["closing"], "OK" if same else "*** DIVERGES ***"))

g = guard(len(paying), m["lastEmi"], m["penultEmi"])
print("guard on the no-loop model: |diff| = %d minor units vs threshold floor(%d/2) = %d -> %s"
      % (g["absDiffMinorUnits"], len(paying), g["lowerHalfOfRelatedPeriods"],
         "TRIPS" if g["trips"] else "does not trip"))
print("P-03 control:", "REPRODUCED -- the loop changes nothing here" if ok else "*** DIVERGES ***")
sys.exit(0 if ok else 1)
