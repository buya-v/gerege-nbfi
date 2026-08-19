#!/usr/bin/env python3
"""T47 edit 5 - §8 item 9's TO_BE_CAPTURED list: (f) gains T46's two ties,
new (h) for N46-1; §9's capture-programme bullet."""
import io
import os
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
DOC = os.path.join(W, "docs/adr/DEC-1-schedule-generator-adapter.md")
s = io.open(DOC, encoding="utf-8").read()


def rep(old, new):
    global s
    n = s.count(old)
    if n != 1:
        sys.exit("edit5: expected 1 occurrence, found %d for: %.100s" % (n, old))
    s = s.replace(old, new)


# --- §8 item 9(f) ----------------------------------------------------------
rep("(f) a percentage landing on an exact half-cent tie, which pins the rounding mode "
    "inside the charge arithmetic specifically — **revision 9 records that T44's audit "
    "probe `AP-5` already FOUND one and observed `0.405 → 0.41`, refuting T40's claim "
    "that none exists, so what remains is promotion of that shape into the set rather "
    "than a search** (§4.5.1); and (g) **a shape in which the request `amount` differs "
    "from the persisted `m_charge.amount`**, which no capture in the set does and which "
    "T44's `AP-5`/`AP-6` show decides the money (finding A-3, §4.5.1).",

    "(f) a percentage landing on an exact half-cent tie, which pins the rounding **mode** "
    "inside the charge arithmetic specifically — **revision 9 records that T44's audit "
    "probe `AP-5` already FOUND one and observed `0.405 → 0.41`, refuting T40's claim "
    "that none exists, so what remains is promotion of that shape into the set rather "
    "than a search**; **revision 10 adds that task T46 built two more INSIDE an attested "
    "set** — `T46-CH-03` (`4.725 → 4.73`) and `T46-CH-04` (`2.025 → 2.03`), both "
    "`HALF_UP` — so this sub-item is now three observed shapes away from a search and "
    "one promotion away from discharged (§4.5.1); (g) **a shape in which the request "
    "`amount` differs from the persisted `m_charge.amount`**, which no capture in T40's "
    "set does and which T44's `AP-5`/`AP-6` show decides the money (finding A-3, "
    "§4.5.1) — **revision 10 records that task T46 closed the QUESTION by capture, "
    "seven shapes for seven, the request governing every time across four "
    "`charge_calculation_enum` values and both fee and penalty** [VERIFIED: "
    "`.softhouse/capture/charges/out/t46/DEFVSREQ.txt`, captures `T46-CH-01`…`T46-CH-07`], "
    "**so what remains here is promotion, and the `[UNVERIFIED as a general rule across "
    "charge types]` qualifier still stands for the enum values T46 did not try**; and "
    "**(h) a shape in which the TENANT rounding mode DIFFERS from the threaded one, put "
    "to a charge percentage that lands on a tie** — the only thing that can decide "
    "**which** `MathContext` supplies the mode at [`Money.java:52`] for a charge, since "
    "on Path B the caller sources one from the other and every capture in the program "
    "has them equal (revision 10, task T46's **N46-1**; §4.1.2, §4.5.1). It needs a "
    "tenant write on a running server, so it belongs to a task that owns the oracle and "
    "may restart or re-tenant it. **This is the sharpest remaining charge blind spot, "
    "because unlike the `inMultiplesOf` leak it is reachable at MNT's two decimal "
    "places.**")

# --- §9 capture-programme bullet ------------------------------------------
rep("**Revision 9 adds two entries to that machine-readable list** (capture audit T44): "
    "a record from the month-end family cannot grade **either clause of that pair on its "
    "own** (F39-1), and a record from the charge set cannot grade **which input supplies "
    "the charge amount** and must name the **request bytes** as its fixture (A-3).",

    "**Revision 9 adds two entries to that machine-readable list** (capture audit T44): "
    "a record from the month-end family cannot grade **either clause of that pair on its "
    "own** (F39-1), and a record from the charge set cannot grade **which input supplies "
    "the charge amount** and must name the **request bytes** as its fixture (A-3). "
    "**Revision 10 sharpens the first and adds a third** (task T46): the month-end "
    "record's limitation is not a gap but a **proved property** — neither clause is "
    "separable by any vector on any arm of `calculatePeriodRatio`, so the record must "
    "say \"not separable\" and not \"not yet separated\" (§4.1.1 step B, §8 item 3f); and "
    "**a record promoted from the charge set cannot grade WHICH `MathContext` supplied "
    "the rounding mode at the charge's scale-2 conversion**, because on Path B the "
    "threaded context and the ambient one are a single reference "
    "[`LoanScheduleAssembler.java:753`, `:765`] and every capture in the program has "
    "them equal (N46-1; §4.1.2, §4.5.1, §8 item 9(h)).")

io.open(DOC, "w", encoding="utf-8").write(s)
print("edit5: ok")
