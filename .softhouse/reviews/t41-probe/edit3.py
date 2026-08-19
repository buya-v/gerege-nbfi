#!/usr/bin/env python3
"""T41 edit batch 3 — T39 N-1: the days-in-month argument, re-derived precisely."""
import io
import sys

P = "docs/adr/DEC-1-schedule-generator-adapter.md"
s = io.open(P, encoding="utf-8").read()
LOG = []


def sub(old, new, n=1):
    global s
    c = s.count(old)
    if c != n:
        sys.exit("FAIL: expected %d, found %d for:\n%s" % (n, c, old[:220]))
    s = s.replace(old, new)
    LOG.append("ok: %s" % old[:70].replace("\n", " "))


# --- 4.1.1: the heading claim ------------------------------------------------
sub(
    "**The two call sites differ in TWO arguments, not one** (P0-T34-1, corrected in revision 7). "
    "Revision 6's table named only the *span*; independent re-review T34 found the second "
    "difference, and **in money it is the larger of the two**.",

    "**The two call sites differ in two arguments SYNTACTICALLY, and in exactly ONE of them "
    "numerically — the multiplier** (P0-T34-1, corrected in revision 7; the framing **narrowed** "
    "in revision 8 on task T39's finding N-1, and the narrowing is in this document's favour). "
    "Revision 6's table named only the *span*; independent re-review T34 found the second "
    "difference and called it live; revision 7 said only the multiplier moves money **inside the "
    "graded domain**; revision 8 re-derives that the days-in-month argument is `30` at both call "
    "sites on **every path either call site is reachable on**, graded or not, so there is "
    "**exactly one numeric difference between them, unconditionally**.",
)

# --- 4.1.1: the "of those two argument differences" paragraph ---------------
sub(
    "**Of those two argument differences exactly one is live inside the graded domain, and "
    "revision 7 says which.** The days-in-month argument is a literal `30` on the interest call "
    "site [`:1413`] and the local `daysInMonth` on the recurrence call site [`:1537`], where "
    "`daysInMonth = daysInMonthType.isDaysInMonth_30() ? BigDecimal.valueOf(30) : "
    "calculatedDaysInRepaymentPeriod` [`:1508`] — so under `DayCountFixed30Over360` **both are "
    "exactly 30** and that difference is numerically inert. It can only become live under "
    "`DaysInMonthType.ACTUAL`, which §4.9 refuses and on which the interest call site takes a "
    "different branch entirely [`:1400-1402`]. **The multiplier is the live difference**: "
    "`RepaymentEvery` on the recurrence, `periodRatio` on the interest. Revisions 1–6 wrote "
    "`RepaymentEvery` for both.",

    "**Of those two argument differences exactly ONE moves money, and revision 8 states the "
    "stronger form of the reason.** The days-in-month argument is a literal `30` on the interest "
    "call site [`:1413`] and the local `daysInMonth` on the recurrence call site [`:1537`], where "
    "`daysInMonth = daysInMonthType.isDaysInMonth_30() ? BigDecimal.valueOf(30) : "
    "calculatedDaysInRepaymentPeriod` [`:1508`]. **So under `DayCountFixed30Over360` both are "
    "exactly 30.**\n\n"
    "**Revision 7 stopped there and said the difference \"can only become live under "
    "`DaysInMonthType.ACTUAL`\". Re-derived here in full, it cannot become live at all** — "
    "`daysInMonth` is consumed at exactly one place, `:1537`, and `:1537` sits inside the "
    "`case DAYS_30 ->` arm of the `switch (daysInMonthType)` at `:1533-1539`. `DAYS_30` is "
    "precisely the branch in which `:1508`'s ternary yields `BigDecimal.valueOf(30)`, so wherever "
    "the recurrence call site is reached its fourth argument **is** the literal 30, exactly as the "
    "interest call site's is. On the other two enum values neither call site is reached with a "
    "days-in-month argument at all: under `ACTUAL` the recurrence takes `:1534-1535` "
    "(`rateFactorByRepaymentPeriod` directly, no `daysInMonth`) and the interest site takes "
    "`:1400-1402` (likewise); under `INVALID` [`DaysInMonthType.java:34`] the recurrence throws at "
    "`:1538` and the interest site throws at `:1415-1416`. **There is therefore no configuration, "
    "inside the graded domain or outside it, in which the two call sites pass different "
    "days-in-month arguments to `calculateRateFactorPerPeriodBasedOnRepaymentFrequency`** — "
    "confirmed by grep: those are its only two call sites, and `daysInMonth` has only the one use "
    "[VERIFIED: `ProgressiveEMICalculator.java:1412-1413`, `:1508`, `:1533-1539`, `:1400-1402`, "
    "`:1415-1416`, `:1598-1607`; `DaysInMonthType.java:34-36`, `:71-73`].\n\n"
    "**The multiplier is the one and only live difference**: `RepaymentEvery` on the recurrence, "
    "`periodRatio` on the interest. Revisions 1–6 wrote `RepaymentEvery` for both. "
    "**A revision that also \"corrected\" the days-in-month argument would be wrong**, and task "
    "T39 raised exactly that as its finding N-1 [VERIFIED: "
    "`.softhouse/handoff/T39-periodratio-observation.md` §3 N-1]. Revision 8 records one "
    "divergence from T39: T39's prose locates the `daysInMonth` assignment at `:1509` while its "
    "own `[VERIFIED]` tag and this document say `:1508`; **`:1508` is correct**, re-read in the "
    "pinned checkout by this task. Revision 8 also goes one step beyond T39, which scoped the "
    "inertness to the graded domain: it is unconditional, for the reason above.",
)

io.open(P, "w", encoding="utf-8").write(s)
print("\n".join(LOG))
