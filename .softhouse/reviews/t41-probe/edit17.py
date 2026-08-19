#!/usr/bin/env python3
"""T41 edit batch 17 — F-1 only: pin step B's whole-months function."""
import io
import sys

P = "docs/adr/DEC-1-schedule-generator-adapter.md"
s = io.open(P, encoding="utf-8").read()

old = ("**Step B — the whole-period offset `k`** [`:1423-1439`]. `k` is the whole months from the "
       "seed to the repayment period's `FromDate` (`DateUtils.getExactDifference(seed, FromDate, "
       "MONTHS)`, truncated toward zero) [`:1435`], with an explicit **month-end special case** "
       "whose predicate revision 8 spells out literally,")

new = ("**Step B — the whole-period offset `k`** [`:1423-1439`].\n\n"
       "**First, WHICH whole-months function — because \"whole months, truncated toward zero\" "
       "names TWO different functions, and revision 8's own spec-check probe caught the ambiguity "
       "in revision 8's own draft** (finding **F-1**, `.softhouse/reviews/t41-probe/`). `k` is "
       "`DateUtils.getExactDifference(seed, FromDate, MONTHS)` [`:1435`], which is "
       "`ChronoUnit.MONTHS.between` [VERIFIED: `DateUtils.java:308-317` — `getExactDifference` "
       "→ `getDifference` → `unit.between(first, second)`], i.e. Java's `LocalDate.monthsUntil`:\n\n"
       "```\n"
       "packed(d) = (d.year × 12 + d.month − 1) × 32 + d.dayOfMonth\n"
       "k         = (packed(FromDate) − packed(seed)) ÷ 32        # truncated toward zero\n"
       "```\n\n"
       "**It is NOT \"the largest k with seed + k months ≤ FromDate\".** The two agree almost "
       "everywhere and differ **exactly** when `plusMonths` would have **clamped** — when "
       "`FromDate` is the last day of its month and the seed's day-of-month is strictly greater. "
       "`MONTHS.between(2024-01-31, 2024-02-29)` is **0** under the packed rule and **1** under "
       "the clamped-step rule. **That is precisely the condition the month-end special case below "
       "tests**, so the two readings coincide on every input *while the special case is present* "
       "and part company the moment it is dropped — which is why a model built on the wrong one "
       "reproduces every committed cell and still cannot see that the special case matters. "
       "(That is not hypothetical: this task's first transcription used the clamped-step reading, "
       "reproduced all 4,578 cells, and reported the special case as inert. The packed rule was "
       "adopted after reading `DateUtils.java`, and the same 4,578 cells still reproduce.) The "
       "JDK's packing is not a `file:line` in the pinned checkout, so the formula itself is "
       "`[UNVERIFIED in this checkout]` — but **which rule is in force is settled by "
       "observation**, because the special case is load-bearing only under the packed rule and "
       "T39 observed it load-bearing on 116 of 116 discriminating cells [VERIFIED: captures "
       "`T39-ME-A`…`T39-ME-D`]. **A port must implement the packed rule WITH the special case, or "
       "the clamped-step rule WITHOUT it; taking the packed rule and dropping the special case "
       "double-charges alternate periods, and that combination is the one a careless port "
       "lands on.**\n\n"
       "Then, `k` carries an explicit **month-end special case** whose predicate revision 8 spells "
       "out literally,")

if s.count(old) != 1:
    sys.exit("FAIL: found %d" % s.count(old))
io.open(P, "w", encoding="utf-8").write(s.replace(old, new))
print("ok: step B k function pinned")
