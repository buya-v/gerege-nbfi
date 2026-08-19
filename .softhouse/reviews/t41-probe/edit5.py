#!/usr/bin/env python3
"""T41 edit batch 5 — T39: periodRatio is now OBSERVED; item 3e splits into 3e + 3f."""
import io
import sys

P = "docs/adr/DEC-1-schedule-generator-adapter.md"
s = io.open(P, encoding="utf-8").read()
LOG = []


def sub(old, new, n=1):
    global s
    c = s.count(old)
    if c != n:
        sys.exit("FAIL: expected %d, found %d for:\n%s" % (n, c, old[:260]))
    s = s.replace(old, new)
    LOG.append("ok: %s" % old[:70].replace("\n", " "))


# =============================================================================
# 4.1.1 — the corpus-blindness paragraph
# =============================================================================
sub(
    "**The corpus is blind to this, and stayed blind through T37.** Checked two ways. "
    "**Directly:** across **all 35** committed captures — the twelve Path-A pass-3, the twelve "
    "pass-3b re-emissions and the eleven T37 binding captures — **not one repayment period has a "
    "`periodRatio` different from `RepaymentEvery`** "
    "[`.softhouse/reviews/t38-probe/t38-corpus-blind-output.txt`]. **Operationally:** the two "
    "readings return **identical money on all 21** captures at the production `MathContext` "
    "(eleven Path-A pass-3, ten T37 binding), so no cell of any of them separates them; and per "
    "T34 **0 of the 13** observations does either "
    "(`.softhouse/reviews/t38-probe/t38-discriminate-output.txt`; "
    "`.softhouse/reviews/t34-probe/t34_corpus_blind.py`). Every one of them either has "
    "`ScheduleStartDate == Disbursements[0].Date`, so the two seeds coincide, or a schedule start "
    "on the 1st, so the re-anchor never fires. `P-02` (seed day 31) and `P-02b` (seed day 30) — "
    "the two captures §5 credits with grading the month-end rule — are exactly the aligned case. "
    "**This is the fifth consecutive round in which a reading reproduced the whole corpus and was "
    "still wrong**, and it is why §8 gains item **3e** and the binding widens to six vectors.",

    "**The corpus was blind to this through T37. Task T39 closed the blindness by OBSERVATION, "
    "and the observation says `periodRatio`** (revision 8). Both halves are stated, because the "
    "distinction is the whole lesson.\n\n"
    "**What the pre-T39 corpus could not see.** Checked two ways. **Directly:** across **all 35** "
    "committed captures of that era — the twelve Path-A pass-3, the twelve pass-3b re-emissions "
    "and the eleven T37 binding captures — **not one repayment period has a `periodRatio` "
    "different from `RepaymentEvery`** "
    "[`.softhouse/reviews/t38-probe/t38-corpus-blind-output.txt`]. **Operationally:** the two "
    "readings return **identical money on all 21** of them at the production `MathContext` "
    "(eleven Path-A pass-3, ten T37 binding), so no cell of any separates them; and per T34 "
    "**0 of the 13** observations does either "
    "(`.softhouse/reviews/t38-probe/t38-discriminate-output.txt`; "
    "`.softhouse/reviews/t34-probe/t34_corpus_blind.py`). Every one either has "
    "`ScheduleStartDate == Disbursements[0].Date`, so the two seeds coincide, or a schedule start "
    "on the 1st, so the re-anchor never fires. `P-02` (seed day 31) and `P-02b` (seed day 30) — "
    "the two captures §5 credits with grading the month-end rule — are exactly the aligned case. "
    "**That was the fifth consecutive round in which a reading reproduced the whole corpus and "
    "was still wrong.**\n\n"
    "**What task T39 then observed on the pinned reference oracle.** Sixteen captures, one run, "
    "Path A, at attested threaded `(19, HALF_UP)` except one labelled `(12, HALF_UP)` calibration "
    "[VERIFIED: `.softhouse/capture/periodratio/out/t39-periodratio.json`, "
    "`ATTESTATION.md`, `REPRODUCE.md`]. On the **415 cells where the `periodRatio` and "
    "`RepaymentEvery` readings disagree**, across **8 drift shapes**, the oracle agrees with "
    "**`periodRatio` on 415 of 415** and with **`RepaymentEvery` on 0 of 415**; end to end the "
    "`periodRatio` reading reproduces **every cell of all 15 parity-setting captures — 1,239 "
    "cells — with zero mismatches** [VERIFIED: "
    "`.softhouse/capture/periodratio/analysis/discriminate-output.txt`]. **P0-T34-1 is settled "
    "empirically**, and this document's re-derived worst case is now an observed one: MNT "
    "**398,967.73** of total interest on `T39-P0-D` (start `2024-01-28`, disbursement "
    "`2024-01-31`, MNT 50,000,000, 36 × 21.6 %), observed **18,659,151.45** against the "
    "`RepaymentEvery` reading's 18,260,183.72 [VERIFIED: capture `T39-P0-D`]. Three further "
    "properties this subsection asserted from re-derivation are now observed too: **there is no "
    "size threshold** — `T39-P0-F` at MNT **100** still separates on 27 cells, observed total "
    "interest `6.41` against `6.21` [VERIFIED: capture `T39-P0-F`]; **the drift is not a "
    "January, leap-year or 31-day-month artefact** — it reproduces seeded in March, in a 30-day "
    "November and in the common year 2025 [VERIFIED: captures `T39-P0-G`, `T39-P0-H`, "
    "`T39-P0-E`]; and **the DUE DATES move, not only the money** — on `T39-P0-A` "
    "`loanTermInDays` is **185**, not the 182 the aligned shape gives [VERIFIED: capture "
    "`T39-P0-A`; T39's N-7]. Three controls outside the drift region reproduce committed records "
    "taken by **different harnesses on different tasks** digit for digit, so the rig is not the "
    "variable [VERIFIED: T39 §4, controls C1–C4].\n\n"
    "**The month-end special case of step B is OBSERVED to be live and load-bearing, and it is a "
    "SEPARATE question from the multiplier** (revision 8, on T39's N-2). Omitting the four lines "
    "at [`:1430-1433`] roughly **doubles** `periodRatio` on alternate periods: on `T39-ME-B` "
    "(start = disbursement `2024-01-31`, MNT 1,200,000, 6 × 21.6 %) the with-case ratios are "
    "`[1,1,1,1,1,1]` and the without-case ratios `[1,2,1,2,1,2]`, and the observed total interest "
    "is **76,723.70** against the omitted reading's 109,900.97 — an **MNT 33,177.27** overcharge, "
    "29 cells wide; `T39-ME-A` is worth **MNT 83,959.76** on one six-month MNT 3.9 M loan. Across "
    "4 shapes and **116 disagreeing cells** the oracle agrees **116 of 116** with the "
    "special-case-present routine and **0 of 116** with the routine minus it [VERIFIED: captures "
    "`T39-ME-A`…`T39-ME-D`, `.softhouse/capture/periodratio/analysis/discriminate-output.txt`]. "
    "**The two questions are DISJOINT in shape space and no single vector can grade both**: over "
    "51,729 same-month `(ScheduleStartDate ≤ Disbursement.Date)` pairs across 2023–2025 × terms "
    "{6, 12, 36}, the special case fires on **210**, and on **0 of those 210** does "
    "`ScheduleStartDate ≠ Disbursement.Date` — the special case needs `calculateSeedDate` to "
    "return the schedule start, i.e. boundaries **on** the lattice, while the multiplier drift "
    "needs them **off** it. The 15 captured shapes confirm it: on every one, exactly one of the "
    "two questions separates and the other has zero disagreeing cells. So **§8's item 3e splits "
    "into 3e (drift) and 3f (month-end), and the binding widens from six vectors to seven.** "
    "(The 51,729-pair sweep is T39's **re-derivation**, re-runnable from "
    "`.softhouse/capture/periodratio/analysis/readings.py`, and its raw output is not committed — "
    "`[UNVERIFIED as a committed artefact]`; the disjointness conclusion is corroborated by the "
    "15 captured shapes, which is `[VERIFIED: analysis/discriminate-output.txt]`.)\n\n"
    "**What is still NOT observed, stated so the correction does not overshoot.** T39 did not "
    "instrument `calculatePeriodRatio`, `calculateSeedDate` or the rate factor. What is observed "
    "is that the oracle's output is the one **only** a `periodRatio`-with-month-end-case "
    "execution produces and is not the one either alternative produces. That is a "
    "**discrimination**, not an internal observation, and the claim \"the special case fired on "
    "periods 2, 4 and 6\" remains a re-derivation [T39 §7]. `periodRatio`'s `YEARS`, `WEEKS` and "
    "`DAYS` arms [`:1405`, `:1407`, `:1408`] and its whole-period return branch [`:1457-1458`] "
    "remain **entirely uncaptured** (§8 item 6).",
)

io.open(P, "w", encoding="utf-8").write(s)
print("\n".join(LOG))
