#!/usr/bin/env python3
"""T47 edit 2 - finding 1 leak sites: §4.1.1 restatements, §8 items 1/3f/6,
§9 obligation (f)."""
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
        sys.exit("edit2: expected 1 occurrence, found %d for: %.100s" % (n, old))
    s = s.replace(old, new)


# --- §4.1.1, the "month-end special case is OBSERVED live" paragraph --------
rep("**The reading refuted is `packed whole-months ∧ no special case`; the reading "
    "`clamped-step whole-months ∧ no special case` is refuted by nothing in the corpus** "
    "— revision 9's narrowing on T44's F39-1, measured immediately above in step B and "
    "again at §8 item 3f.",

    "**The reading refuted is `packed whole-months ∧ no special case`; the reading "
    "`clamped-step whole-months ∧ no special case` is refuted by nothing in the corpus, "
    "and revision 10 records that it never can be** — the special case is provably "
    "non-separable, proved in closed form and measured exhaustively over 112,147,776 "
    "ordered date pairs in step B above, with the `YEARS` escape route closed by "
    "observation (§8 item 3f).")

# --- §4.1.1, the "still NOT observed" paragraph: the arms are captured now --
rep("`periodRatio`'s `YEARS`, `WEEKS` and `DAYS` arms [`:1405`, `:1407`, `:1408`] and "
    "its whole-period return branch [`:1457-1458`] remain **entirely uncaptured** "
    "(§8 item 6).",

    "`periodRatio`'s `YEARS`, `WEEKS` and `DAYS` arms [`:1405`, `:1407`, `:1408`] and "
    "its whole-period return branch [`:1457-1458`] were **entirely uncaptured through "
    "revision 9; revision 10 corrects that, because task T46 captured them** and this "
    "subsection's own non-separability argument now cites those captures — the document "
    "may not call uncaptured what it has just quoted. *Observed* on the Path-A seam: "
    "`WEEKS` on `T46-WK-A`/`T46-WK-B`/`T46-WK-C`, `DAYS` on `T46-DY-A`/`T46-DY-B`, "
    "`RepaymentEvery` 2 and 3 on `T46-RE-2`/`T46-RE-3`/`T46-RE-2ME` — which is the "
    "first exercise of step C's whole-period return branch — and `YEARS` **throws** on "
    "`T46-YR-A`/`T46-YR-B` [VERIFIED: "
    "`.softhouse/capture/periodratio/out/t46-periodratio-arms.json`]. **They are "
    "attested raw observations and not admissible vectors** (§8 item 1), so §8 item 6's "
    "*vector* request stands unchanged; what changes is that the coverage claim is no "
    "longer true as written. **What those captures do and do not discriminate is "
    "measured, not assumed:** across 186 repayment periods `T46-RE-3` separates the "
    "`RepaymentEvery` reading on 3 periods and `T46-RE-2ME` separates the "
    "special-case-omitted reading on 2, while `T46-WK-*`, `T46-DY-*`, `T46-RE-2` and "
    "`T46-ARM-CTL` separate **nothing** among those readings — arm coverage, not "
    "discriminating power [VERIFIED: "
    "`.softhouse/capture/periodratio/analysis/t46_arms_ratio-output.txt`].")

# --- §8 item 3f status line -----------------------------------------------
rep("**STATUS: CAPTURED AS A PAIR, NOT YET PROMOTED; the special case ALONE is "
    "`TO_BE_CAPTURED`** (narrowed in revision 9 on capture-audit T44's finding F39-1).",

    "**STATUS: CAPTURED AS A PAIR, NOT YET PROMOTED; the special case ALONE is NOT "
    "SEPARABLE — proved, not outstanding** (narrowed in revision 9 on capture-audit "
    "T44's finding F39-1; the `TO_BE_CAPTURED` revision 9 left here is **withdrawn** in "
    "revision 10 on task T46's proof, because a capture request that can never be "
    "filled is a defect in this document and not a piece of backlog).")

# --- §8 item 3f, the "what would separate it" paragraph --------------------
rep("**What would separate the special case alone, and it is not in this family.** "
    "`calculatePeriodRatio`'s `YEARS`, `WEEKS` and `DAYS` arms [`:1405`, `:1407`, "
    "`:1408`] call `getExactDifference` with **no** special case at all, so the two "
    "whole-months rules do not cancel there and any capture on those arms discriminates "
    "them. Those arms are entirely uncaptured (§8 item 6, `RepaymentEvery > 1`). "
    "**`TO_BE_CAPTURED`.** A capture task in this fire is attempting exactly this; "
    "**whatever it returns settles this paragraph rather than contradicting it** — a "
    "shape that separates the special case alone would upgrade \"captured as a pair\" to "
    "\"captured separately\" and change nothing normative, and a failure to find one "
    "leaves the pair statement standing.",

    "**NOTHING separates the special case alone, and revision 10 states that as a "
    "RESULT rather than as a backlog item.** Revision 9 wrote that a separating shape "
    "\"must come from `calculatePeriodRatio`'s `YEARS`, `WEEKS` and `DAYS` arms\" "
    "[`:1405`, `:1407`, `:1408`] and left the item `TO_BE_CAPTURED`. The capture task "
    "revision 9 anticipated is **task T46, and it returned a negative result** — which "
    "is exactly the outcome revision 9 said would settle this paragraph. Three "
    "arguments, each a different kind of evidence, set out in full in §4.1.1 step B and "
    "summarised here. **(i) Closed form (re-derivation, independently re-derived by "
    "task T47):** `packed` and `clamped-step` differ **iff** `FromDate` is the last day "
    "of its month **and** the seed's day is strictly greater — verbatim the predicate at "
    "[`:1432`] — and when that fires the oracle's `FromDate.plusDays(1)` measurement "
    "[`:1433`] returns exactly what `clamped-step` returns, so `k_oracle ≡ k_clamped` "
    "identically. **(ii) Exhaustive measurement (observation of the pinned image's own "
    "`java.time`):** over **112,147,776** ordered date pairs in 2000–2040 the predicate "
    "fires on **45,253**, `packed ≠ clamped-step` on **exactly those 45,253**, both "
    "cross-terms are **0**, `k_oracle ≠ k_clamped` is **0** and `k_oracle ≠ k_packed` is "
    "**45,253** [VERIFIED: "
    "`.softhouse/capture/periodratio/analysis/t46_monthdiff_exhaustive-output.txt`]. "
    "**(iii) The escape route is closed by OBSERVATION:** `WEEKS` and `DAYS` cannot "
    "separate the two rules at all, because nothing clamps on those units "
    "*(re-derivation)*; `YEARS` **does** separate, on 165 pairs, but the `YEARS` arm is "
    "**unreachable** — the ratio computed at [`:1405`] is handed to a `switch` "
    "[`:1598-1610`] whose `default` throws `UnsupportedOperationException` at "
    "[`:1609`], and both `T46-YR-A` (the 29 February separator shape) and `T46-YR-B` "
    "returned that exception [VERIFIED: "
    "`.softhouse/capture/periodratio/out/t46-periodratio-arms.json`]. **So this item is "
    "discharged as far as it can ever be discharged: the seven witnesses grade the "
    "pair, the pair is what §4.1.1 step B pins and what §9 obligation (f) requires, and "
    "a port carrying two cancelling defects passes them AND IS CORRECT ON THIS ARM.** "
    "That is the honest form of the statement, and it is better than an open vector "
    "request nobody could ever fill.")

# --- §8 item 3f binding sentence ------------------------------------------
rep("separating step B's **packed-whole-months-plus-special-case pair** (3f; **the pair, "
    "not either clause alone** — narrowed in revision 9 on T44's F39-1).",

    "separating step B's **packed-whole-months-plus-special-case pair** (3f; **the pair, "
    "not either clause alone** — narrowed in revision 9 on T44's F39-1, and revision 10 "
    "adds that no vector can ever separate either clause, so \"the pair\" is the "
    "strongest form this requirement can take rather than a weakened one).")

# --- §8 item 1, requirement (iii) -----------------------------------------
rep("(iii) A record promoted from the month-end family (`T39-ME-A`…`T39-ME-D`, §8 item "
    "3f) must record that it grades §4.1.1 step B's **pair** — packed whole-months "
    "**and** the month-end special case — and **neither clause alone**, because a port "
    "with both defects reproduces it exactly (T44's F39-1).",

    "(iii) A record promoted from the month-end family (`T39-ME-A`…`T39-ME-D`, §8 item "
    "3f) must record that it grades §4.1.1 step B's **pair** — packed whole-months "
    "**and** the month-end special case — and **neither clause alone**, because a port "
    "with both defects reproduces it exactly (T44's F39-1). **Revision 10 sharpens the "
    "field's value from a limitation into a proved property**: the record must say that "
    "neither clause is separable **by any vector, on any arm of `calculatePeriodRatio`, "
    "ever** — closed form plus a 112,147,776-pair exhaustive sweep plus the observed "
    "`UnsupportedOperationException` on the `YEARS` arm (task T46; §4.1.1 step B, §8 "
    "item 3f) — so that a later reader does not record it as a gap to be filled and "
    "open a capture request that cannot succeed.")

# --- §9 obligation (f) -----------------------------------------------------
rep("**The Go module must additionally reproduce (f) §4.1.1 step B's month-end special "
    "case** [`ProgressiveEMICalculator.java:1426-1436`, predicate at `:1432`, effect at "
    "`:1433`] **as a PAIR with the packed whole-months rule of (c)** — the two are one "
    "obligation and neither clause is safe stated alone.",

    "**The Go module must additionally reproduce (f) §4.1.1 step B's month-end special "
    "case** [`ProgressiveEMICalculator.java:1426-1436`, predicate at `:1432`, effect at "
    "`:1433`] **as a PAIR with the packed whole-months rule of (c)** — the two are one "
    "obligation and neither clause is safe stated alone. **Revision 10 pins the packed "
    "rule of (c) NORMATIVELY here as well as in §4.1.1 step B**, on task T46's proof "
    "that the two clauses are not separable by any capture: the specified reading is "
    "`ChronoUnit.MONTHS.between` [`:1435`, `DateUtils.java:308-317`] **with** the "
    "special case, which is what the oracle's own code does. A port that instead "
    "implements the clamped-step whole-months rule **with no special case** is "
    "observationally identical and therefore conformant — stated plainly so nobody "
    "\"corrects\" a working port — but the **only** wrong combination of the two "
    "clauses, `packed ∧ no special case`, is exactly the one a port lands on by "
    "implementing (c) and forgetting (f), which is why they are one obligation.")

io.open(DOC, "w", encoding="utf-8").write(s)
print("edit2: ok")
