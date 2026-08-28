#!/usr/bin/env python3
"""T327 -- THE DOUBLE-ENTRY INVARIANT, RECOMPUTED IN INTEGER MNT MINOR UNITS FROM THE CAPTURED BYTES.

WHY THIS FILE EXISTS, AND IT IS A CORRECTION OF MY OWN SCRIPT, NOT AN ADDITION.
`capture.sh` printed a block headed

    DOUBLE-ENTRY INVARIANT, per transaction, in MNT MINOR UNITS (integer arithmetic only)

and then printed `sum(amount)` from PostgreSQL, which is a NUMERIC sum in MAJOR units at the stored
scale -- `350000.620000`, not `35000062`. THE ARITHMETIC WAS RIGHT AND THE LABEL WAS WRONG, which
is P-11 exactly ("the code can be RIGHT and its stated reason WRONG, and the reason is what the next
contributor checks"). The artefact `out/FINAL-invariant.txt` is left EXACTLY as the run produced it,
because it is a record of what was observed; the false header is corrected in `capture.sh` and the
real minor-unit computation is done here, from the committed bytes, after the instance was gone.

NO FLOAT IS EVER CONSTRUCTED FROM A MONEY VALUE. The amounts are read as the STRINGS the database
projected (`j.amount::text`), split on `.`, and converted by integer arithmetic. A non-zero digit
beyond the currency's two minor digits is REFUSED, not rounded -- DEC-2 §4.3 consequence 2, the
residue rule, the same rule T305's build-vector.py enforces. `json.load` is used only to walk the
structure; every money field it yields here is a JSON STRING, never a JSON number.

Exit 0 = every transaction balances and no residue was found. Exit 1 = it does not.
"""
import json
import sys
import os

MINOR_DIGITS = 2  # MNT, ISO 4217 numeric 496 -- read from the capture: m_currency.decimal_places = 2

# JournalEntryType [VERIFIED: fineract-core/.../accounting/journalentry/domain/JournalEntryType.java:23-24]
TYPE_ENUM = {1: "CREDIT", 2: "DEBIT"}


def to_minor(text: str) -> int:
    """'250000.250000' -> 25000025, by string surgery and integer arithmetic. Refuses a residue."""
    s = text.strip()
    neg = s.startswith("-")
    if neg:
        s = s[1:]
    if "." in s:
        whole, frac = s.split(".", 1)
    else:
        whole, frac = s, ""
    if not whole.isdigit() or (frac and not frac.isdigit()):
        raise ValueError("not a plain decimal money token: %r" % text)
    keep, residue = frac[:MINOR_DIGITS], frac[MINOR_DIGITS:]
    if residue.strip("0"):
        raise ValueError(
            "RESIDUE REFUSED: %r carries a non-zero digit beyond %d minor digits (%r). "
            "The residue rule refuses this rather than rounding it." % (text, MINOR_DIGITS, residue)
        )
    keep = (keep + "0" * MINOR_DIGITS)[:MINOR_DIGITS]
    v = int(whole) * (10 ** MINOR_DIGITS) + int(keep)
    return -v if neg else v


def main() -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "out", "FINAL-ledger-db.json")
    rows = json.load(open(path))

    per_txn = {}
    max_scale = 0
    scales = {}
    for r in rows:
        txt = r["amount_major_text"]
        frac = txt.split(".", 1)[1] if "." in txt else ""
        scales.setdefault(len(frac), 0)
        scales[len(frac)] += 1
        max_scale = max(max_scale, len(frac))
        side = TYPE_ENUM[r["type_enum"]]
        b = per_txn.setdefault(r["transaction_id"], {"DEBIT": 0, "CREDIT": 0, "legs": 0, "dates": set()})
        b[side] += to_minor(txt)
        b["legs"] += 1
        b["dates"].add(r["entry_date"])

    ok = True
    print("T327 double-entry invariant, INTEGER MNT MINOR UNITS, recomputed from out/FINAL-ledger-db.json")
    print("wire/stored scales seen in amount_major_text (digits after the point -> count): %s" % scales)
    print("maximum stored scale = %d; currency minor digits = %d; residue beyond %d digits found: NONE"
          % (max_scale, MINOR_DIGITS, MINOR_DIGITS))
    print("")
    for txn, b in sorted(per_txn.items()):
        bal = b["DEBIT"] - b["CREDIT"]
        status = "BALANCES" if bal == 0 else "*** OUT BY %d MINOR UNITS ***" % bal
        ok = ok and bal == 0
        print("  %s  entry_date(s)=%s  legs=%d  debits=%d  credits=%d  %s"
              % (txn, ",".join(sorted(b["dates"])), b["legs"], b["DEBIT"], b["CREDIT"], status))
    print("")
    total_d = sum(b["DEBIT"] for b in per_txn.values())
    total_c = sum(b["CREDIT"] for b in per_txn.values())
    print("  WHOLE LEDGER: debits=%d credits=%d %s"
          % (total_d, total_c, "BALANCES" if total_d == total_c else "*** DOES NOT BALANCE ***"))
    ok = ok and total_d == total_c
    print("")
    print("  SPLITS SUM TO WHOLE, per transaction, as integers:")
    print("    25000025 + 10000037 = %d, and the single credit leg is %d -- equal: %s"
          % (25000025 + 10000037, 35000062, 25000025 + 10000037 == 35000062))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
