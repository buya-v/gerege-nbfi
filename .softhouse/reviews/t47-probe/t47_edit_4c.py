#!/usr/bin/env python3
"""T47 edit 4c - §4.5.1 blind-spot list: T46's two purpose-built ties, and the
new blind spot N46-1 opens (which context supplied the mode)."""
import io
import os
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
DOC = os.path.join(W, "docs/adr/DEC-1-schedule-generator-adapter.md")
s = io.open(DOC, encoding="utf-8").read()

old = """  **So the in-charge-arithmetic rounding-mode canary exists and fires.** It is a T44 audit probe and
  **not** part of T40's attested set; promoting it as the canary is `TO_BE_CAPTURED`. **Nothing in
  DEC-1 rested on the false claim** — §4.5.1 fact 4 and §4.1's mode evidence are unaffected — but the
  blind spot it named is closed and this list must not keep asserting it.
"""

new = """  **So the in-charge-arithmetic rounding-mode canary exists and fires.** That one is a T44 audit
  probe and **not** part of T40's attested set. **Revision 10 adds two more, purpose-built and inside
  an attested capture set** (task T46): a `0.021875 %` percent-of-interest instalment fee on a
  period-1 interest of `21,600.00` is exactly `4.725` and the oracle returned **`4.73`**, and
  `0.009375 %` on the same interest is exactly `2.025` and returned **`2.03`** — both `HALF_UP`,
  where `HALF_EVEN` gives `4.72` and `2.02` [VERIFIED: captures `T46-CH-03` and `T46-CH-04`,
  `.softhouse/capture/charges/req/calc-T46-CH-03-tie-pctinterest-4725.json` and
  `out/t46/T46-CH-03-tie-pctinterest-4725-raw.json` and the `-2025` pair, read as exact wire text and
  re-read by this task]. **Three observed ties — and the blind spot they were meant to close is only
  HALF closed, which revision 10 must not overstate:** a tie pins **the mode that ran**; it does
  **not** pin **which of the two `MathContext`s supplied it**, because on Path B they are one
  reference. That second question is the separate and still-open blind spot immediately below. What
  remains for this bullet is **promotion** of one of the three shapes into a vector, not a search.
  **Nothing in DEC-1 rested on the false claim** — §4.5.1 fact 4 and §4.1's mode evidence are
  unaffected — but the blind spot it named is closed and this list must not keep asserting it.
- **WHICH `MathContext` supplies the rounding mode at a charge's scale-2 conversion** (added in
  revision 10 from task T46's finding **N46-1**). The percentage is computed under the **threaded**
  `mc` [`ProgressiveLoanScheduleGenerator.java:445-446`, and `:464-465` on the specified-due-date
  arm] and is then wrapped by the **two-argument** `Money.of(MonetaryCurrency, BigDecimal)`
  [`Money.java:114-116`, ambient read at `:115`], so the scale-2 rounding at [`Money.java:52`] takes
  the **AMBIENT** mode, by §4.1.2's per-construction rule. On Path B the caller sources the threaded
  context **from** the ambient one [`LoanScheduleAssembler.java:753`, `:765`], so the two are one
  reference and **no capture this program holds separates them** — the three ties above included.
  Unlike the 0-decimal-place `inMultiplesOf` leak (§4.4, `Money.java:48-51`), **this one is reachable
  at MNT's two decimal places**, which is why it is worth a vector: a port that threads one context
  everywhere gets the interest right and the charge ties wrong. Separating it needs the tenant
  rounding mode written to differ from the threaded one, i.e. a tenant write. `TO_BE_CAPTURED`
  (§8 item 9(h)); the full derivation is in *Which `MathContext` rounds a CHARGE* above.
"""

n = s.count(old)
if n != 1:
    sys.exit("edit4c: expected 1 occurrence, found %d" % n)
s = s.replace(old, new)
io.open(DOC, "w", encoding="utf-8").write(s)
print("edit4c: ok")
