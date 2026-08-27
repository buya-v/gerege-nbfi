#!/usr/bin/env python3
"""Emit the A2 request bodies verbatim.

Every file this writes is a REQUEST we send to the oracle. No file here is an
observation — observations live only in out/ and come only from the oracle.

Money note (T145): no monetary literal appears in this file. If one ever does it
must be an integer minor-unit value, and any JSON parsed back must use
json.load(..., parse_float=Decimal) — never plain json.load.
"""
import json, os, sys

REQ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "req")
os.makedirs(REQ, exist_ok=True)


def w(name, obj):
    p = os.path.join(REQ, name + ".json")
    with open(p, "w") as f:
        json.dump(obj, f)
        f.write("\n")
    print("wrote", name)


# ---- GL accounts needed for a CASH-based loan product accounting mapping ----
# All DETAIL, all top-level (parentId omitted) except where noted.
ACCOUNTS = [
    ("gl-020-liability-header", dict(name="Liabilities", glCode="20000", manualEntriesAllowed=True, type=2, usage=2)),
    ("gl-021-overpayment", dict(name="Overpayment Liability", glCode="20100", manualEntriesAllowed=True, type=2, usage=1)),
    ("gl-022-income-header", dict(name="Income", glCode="40000", manualEntriesAllowed=True, type=4, usage=2)),
    ("gl-023-interest-income", dict(name="Interest On Loans", glCode="40100", manualEntriesAllowed=True, type=4, usage=1)),
    ("gl-024-fee-income", dict(name="Income From Fees", glCode="40200", manualEntriesAllowed=True, type=4, usage=1)),
    ("gl-025-penalty-income", dict(name="Income From Penalties", glCode="40300", manualEntriesAllowed=True, type=4, usage=1)),
    ("gl-026-recovery-income", dict(name="Recoveries", glCode="40400", manualEntriesAllowed=True, type=4, usage=1)),
    ("gl-027-expense-header", dict(name="Expenses", glCode="50000", manualEntriesAllowed=True, type=5, usage=2)),
    ("gl-028-writeoff-expense", dict(name="Losses Written Off", glCode="50100", manualEntriesAllowed=True, type=5, usage=1)),
    ("gl-029-goodwill-expense", dict(name="Goodwill Credit", glCode="50200", manualEntriesAllowed=True, type=5, usage=1)),
    ("gl-030-equity-header", dict(name="Equity", glCode="30000", manualEntriesAllowed=True, type=3, usage=2)),
    # a SECOND asset detail, so a mapping can be re-pointed and the change observed
    ("gl-031-fund-source-alt", dict(name="Fund Source Alternate", glCode="10300", manualEntriesAllowed=True, type=1, usage=1)),
    # a DISABLED account, to observe whether a disabled account may be mapped
    ("gl-032-disabled-asset", dict(name="Disabled Asset", glCode="10400", manualEntriesAllowed=True, type=1, usage=1)),
    # a manual-entries-FORBIDDEN account, to observe the flag round-trip and its effect
    ("gl-033-nomanual-asset", dict(name="No Manual Entries Asset", glCode="10500", manualEntriesAllowed=False, type=1, usage=1)),
]

# ---- refusal probes: GL account ----
REFUSALS = [
    # R1 duplicate glCode — acc_gl_account_gl_code_key is a UNIQUE constraint (schema-forced),
    #    but the MESSAGE the oracle emits is behaviour and must be observed.
    ("bad-040-dup-glcode", dict(name="Duplicate Code", glCode="10000", manualEntriesAllowed=True, type=1, usage=1)),
    # R3 mandatory params absent
    ("bad-041-empty-body", {}),
    ("bad-042-no-name", dict(glCode="99001", manualEntriesAllowed=True, type=1, usage=1)),
    ("bad-043-no-glcode", dict(name="No Code", manualEntriesAllowed=True, type=1, usage=1)),
    ("bad-044-no-type", dict(name="No Type", glCode="99002", manualEntriesAllowed=True, usage=1)),
    ("bad-045-no-usage", dict(name="No Usage", glCode="99003", manualEntriesAllowed=True, type=1)),
    # R4/R5 out-of-range enum ordinals
    ("bad-046-type-9", dict(name="Bad Type", glCode="99004", manualEntriesAllowed=True, type=9, usage=1)),
    ("bad-047-type-0", dict(name="Zero Type", glCode="99005", manualEntriesAllowed=True, type=0, usage=1)),
    ("bad-048-usage-5", dict(name="Bad Usage", glCode="99006", manualEntriesAllowed=True, type=1, usage=5)),
    # R6 non-existent parent
    ("bad-049-parent-missing", dict(name="Orphan", glCode="99007", manualEntriesAllowed=True, type=1, usage=1, parentId=99999)),
    # R7 child of a DIFFERENT account type than its parent header
    ("bad-050-type-mismatch-parent", dict(name="Liability Under Asset", glCode="99008", manualEntriesAllowed=True, type=2, usage=1, parentId=1)),
    # R12 glCode longer than varchar(45)
    ("bad-051-glcode-too-long", dict(name="Long Code", glCode="9" * 60, manualEntriesAllowed=True, type=1, usage=1)),
    # name longer than varchar(200)
    ("bad-052-name-too-long", dict(name="N" * 250, glCode="99009", manualEntriesAllowed=True, type=1, usage=1)),
    # unknown parameter — Fineract's command deserializer is strict about these
    ("bad-053-unknown-param", dict(name="Unknown Param", glCode="99010", manualEntriesAllowed=True, type=1, usage=1, thisParamDoesNotExist="x")),
    # blank strings
    ("bad-054-blank-name", dict(name="", glCode="99011", manualEntriesAllowed=True, type=1, usage=1)),
    ("bad-055-blank-glcode", dict(name="Blank Code", glCode="", manualEntriesAllowed=True, type=1, usage=1)),
]

if __name__ == "__main__":
    for n, o in ACCOUNTS + REFUSALS:
        w(n, o)
