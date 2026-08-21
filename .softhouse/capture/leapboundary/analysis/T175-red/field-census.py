#!/usr/bin/env python3
"""T175 -- WHICH money fields does t55-analyse.py:352 actually hide?

The first draft of this probe planted its unparseable value in `totalInterestCharged` and the
ORIGINAL **crashed** instead of swallowing: invariant I5 reads `Decimal(doc["totalInterest\
Charged"])` at t55-analyse.py:342, OUTSIDE any try, and it runs BEFORE I6.  So the swallow at
:352 is not uniform across the money surface -- for some fields an unparseable value is loud,
and for others it is silent.  A red probe that picked a loud field would have "failed to
reproduce the defect" and concluded, wrongly, that there was none.

So enumerate it rather than assume it.  For every MONEYISH field in the capture, plant an
unparseable three-decimal-place value in a SCRATCH copy and record whether the original

    * CRASHES earlier   (an unguarded Decimal() in I1/I2/I3/I5/I7 gets there first), or
    * SWALLOWS it       (:352 drops the cell and I6 returns ok -- the vacuous pass).

Writes only into a temp dir.  The committed corpus is copied, never modified.  No float.

Usage:  python3 field-census.py
"""
import importlib.util
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ANALYSIS = os.path.abspath(os.path.join(HERE, os.pardir))
ORIGINAL = os.path.join(ANALYSIS, "t55-analyse.py")
CID = "LB-LEAPIN-p7"
UNPARSEABLE = "1,200,000.000"       # three decimal places AND not a Decimal


def main():
    spec = importlib.util.spec_from_file_location("t55_original_census", ORIGINAL)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)

    src = m.OUT
    tmp = tempfile.mkdtemp(prefix="t175-fieldcensus-")
    try:
        for fn in sorted(os.listdir(src)):
            if fn.endswith("-exact.json"):
                shutil.copy2(os.path.join(src, fn), tmp)
        m.OUT = tmp
        target = os.path.join(tmp, CID + "-exact.json")
        with open(target) as fh:
            pristine = fh.read()
        doc0 = json.loads(pristine)

        plan_fields = [k for k in doc0 if k in m.MONEYISH]
        row_fields = sorted({k for p in doc0["periods"] for k in p if k in m.MONEYISH})

        def verdict():
            try:
                res = m.invariants(CID)
            except Exception as exc:
                return "CRASHES -- %s, from an unguarded Decimal() in I1/I2/I3/I5/I7" \
                       % type(exc).__name__
            finally:
                with open(target, "w") as fh:
                    fh.write(pristine)
            i6ok = [o for n, o, _d in res if n.startswith("I6")][0]
            if i6ok:
                return "SWALLOWED SILENTLY -- I6 = ok  <-- VACUOUS PASS ON A REAL 3-dp BREACH"
            return "reported -- I6 = VIOLATED"

        def probe_plan(field):
            doc = json.loads(pristine)
            doc[field] = UNPARSEABLE
            with open(target, "w") as fh:
                json.dump(doc, fh)
            return verdict()

        def probe_row(field, idx):
            doc = json.loads(pristine)
            doc["periods"][idx][field] = UNPARSEABLE
            with open(target, "w") as fh:
                json.dump(doc, fh)
            return verdict()

        # The DISBURSEMENT row is the one with no "period" key.  invariants() splits it out at
        # t55-analyse.py:312-316 into `disb`, and I1/I3/I5/I7 then iterate `periods` WITHOUT
        # it -- while cells() keeps it as row0.  So for that row, :352 is the only money check
        # there is.  Probe the disbursement row and the first repayment row SEPARATELY: a
        # verdict about a row-level field is only a verdict about the row it was planted in.
        disb_idx = next(i for i, p in enumerate(doc0["periods"]) if "period" not in p)
        rep_idx = next(i for i, p in enumerate(doc0["periods"]) if "period" in p)

        swallowed, crashed, reported = [], [], []

        def record(label, v):
            (swallowed if v.startswith("SWALLOWED") else
             crashed if v.startswith("CRASHES") else reported).append(label)

        print("T175 field census -- t55-analyse.py:352, capture %s" % CID)
        print("planted value: %r -- three decimal places in MNT (minor unit 2), and not"
              % UNPARSEABLE)
        print("Decimal-parseable, so it is BOTH a real breach of the money non-negotiable AND")
        print("an input the :352 handler discards.")
        print("rows: disbursement row = index %d, first repayment row = index %d"
              % (disb_idx, rep_idx))
        print()
        print("PLAN-LEVEL MONEYISH fields (%d):" % len(plan_fields))
        for f in plan_fields:
            v = probe_plan(f)
            print("  plan.%-30s %s" % (f, v))
            record("plan." + f, v)
        print()
        print("ROW-LEVEL MONEYISH fields (%d), planted in EACH of the two row kinds:"
              % len(row_fields))
        print("  %-30s %-46s %s" % ("field", "in the DISBURSEMENT row (row%d)" % disb_idx,
                                    "in a REPAYMENT row (row%d)" % rep_idx))
        for f in row_fields:
            vd = probe_row(f, disb_idx) if f in doc0["periods"][disb_idx] else "absent from that row"
            vr = probe_row(f, rep_idx) if f in doc0["periods"][rep_idx] else "absent from that row"
            print("  %-30s %-46s %s" % (f, vd.split(" --")[0], vr.split(" --")[0]))
            if not vd.startswith("absent"):
                record("row%d.%s (disbursement)" % (disb_idx, f), vd)
            if not vr.startswith("absent"):
                record("row%d.%s (repayment)" % (rep_idx, f), vr)

        print()
        print("=" * 96)
        print("SUMMARY -- denominators, stated (P-40)")
        print("=" * 96)
        print("  MONEYISH names declared by t55-analyse.py:120-130 : %d" % len(m.MONEYISH))
        print("  ...of which present in %s : %d plan + %d row"
              % (CID, len(plan_fields), len(row_fields)))
        print("  cell PLANTS actually run : %d"
              % (len(swallowed) + len(crashed) + len(reported)))
        print("  ...SWALLOWED SILENTLY (vacuous I6 pass on a real 3-dp breach) : %d"
              % len(swallowed))
        for f in swallowed:
            print("      %s" % f)
        print("  ...CRASHED loudly instead (an unguarded Decimal() got there first) : %d"
              % len(crashed))
        for f in crashed:
            print("      %s" % f)
        print("  ...REPORTED by I6 as a violation : %d" % len(reported))
        for f in reported:
            print("      %s" % f)
        print()
        print("  NOT SWEPT by this census, and therefore not claimed (P-40):")
        print("    * MONEYISH names that do not appear in %s at all" % CID)
        print("      (%s)" % ", ".join(sorted(set(m.MONEYISH) - set(plan_fields) - set(row_fields))))
        print("    * the other 32 captures -- this census plants in one capture only; the")
        print("      guard/no-guard structure is a property of the CODE, not of the capture,")
        print("      but a field absent from this shape could not be probed here.")
        print("    * unparseable values of other SHAPES (empty string, null-as-text, a")
        print("      Unicode minus). Only one planted shape was swept.")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
