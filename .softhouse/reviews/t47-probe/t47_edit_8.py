#!/usr/bin/env python3
"""T47 edit 8 - the revision-10 header, the revision-10 history entry, and the
two forward claims inside the revision-9 entry that revision 10 falsifies."""
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
        sys.exit("edit8: expected 1 occurrence, found %d for: %.100s" % (n, old))
    s = s.replace(old, new)


# ---------------- status line ----------------
rep("**Status: DRAFT (revision 9) — the RATIFICATION CANDIDATE. Revision 9 is an "
    "ERRATUM, not a rewrite: it carries the three P1s and three P2s of independent "
    "re-review T43 — which returned ACCEPTED WITH REQUIRED CHANGES with NO P0, the first "
    "round in eight without one — plus the three findings of capture audit T44 that "
    "touch this document. Revision 9 was written by task T45, which may revise this "
    "unratified draft but may NOT ratify it.**",

    "**Status: DRAFT (revision 10) — the RATIFICATION CANDIDATE. Revision 10 is an "
    "ERRATUM ON AN ERRATUM, and a small one: revision 9 carried the three P1s and three "
    "P2s of independent re-review T43 — which returned ACCEPTED WITH REQUIRED CHANGES "
    "with NO P0, the first round in eight without one — plus the three findings of "
    "capture audit T44; revision 10 closes the FOUR things capture task T46 established "
    "AFTER revision 9 was written. It reopens no decision, moves no type, field, enum "
    "member or graded-domain predicate, and changes no number a Go port must produce. "
    "Revision 10 was written by task T47, which may revise this unratified draft but may "
    "NOT ratify it. One independent re-review stands between this document and "
    "ratification.**")

# ---------------- Run row ----------------
rep("revision 8 by task T41; revision 9 by task T45 |",
    "revision 8 by task T41; revision 9 by task T45; revision 10 by task T47 |")

# ---------------- Supersedes row ----------------
rep("DEC-1 revision 8 (accepted-with-required-changes, **no P0**, by re-review T43) |",
    "DEC-1 revision 8 (accepted-with-required-changes, **no P0**, by re-review T43); "
    "DEC-1 revision 9 (superseded by revision 10 on the evidence of capture task T46, "
    "not by a review finding) |")

# ---------------- the revision-10 history entry ----------------
rep("**Revision history.**\n\n- **Revision 9 (task T45) is an ERRATUM.**",

    """**Revision history.**

- **Revision 10 (task T47) is an ERRATUM ON REVISION 9, and it is four items long.** It closes the four things capture task **T46** established *after* revision 9 was written (`.softhouse/handoff/T46-capture-corrections.md`, `T46-mathcontext-corrections.md`). **No oracle observation was taken by this task** — a sibling task owned the oracle in the same fire, and every observation below is quoted from a committed capture with its id. **No Gradle build was run and the pinned checkout `426a23544e8426a38ae43ae404670a0a7e85b9eb` was read only.** Every `file:line` this revision adds or moves was re-opened in that checkout by this task, and every `file:line` in the whole document was machine-checked against it. **No type, field set, enum member or graded-domain predicate moves** — §3.1's block is byte-identical to revisions 7, 8 and 9's, and `contract.go`'s diff against revision 9 is **zero non-comment lines**. In particular `DayCountActualActual` is **not** admitted; a sibling task is capturing that arm and admitting it would make `daysInYearCustomStrategy` live, which §4.4 says is an amendment and therefore a gate.
  **T46's headline is a NEGATIVE RESULT, and revision 10's largest change is to stop asking for something that cannot exist (§4.1.1 step B, §4.3.2's restatements, §8 items 1, 3f and 6, §9 obligation (f), `contract.go`).** Revision 9 recorded, on T44's F39-1, that the four `T39-ME-*` captures grade §4.1.1 step B's **pair** — the packed whole-months rule together with the month-end special case — and not the special case alone, and it left "a discriminator for the special case alone" as **`TO_BE_CAPTURED`** on the `YEARS` / `WEEKS` / `DAYS` arms. **There is no such discriminator and there never will be**, and revision 10 replaces the capture request with a proof. Three kinds of evidence, kept distinct because they are three different kinds. **(i) A closed form — a re-derivation, performed independently by this task and agreeing with T46's:** with `k` the proleptic-month difference, `packed = k − [seed.day > from.day]` and `clamped-step = k − [min(seed.day, len(from's month)) > from.day]`; they differ **iff** `from` is the last day of its month **and** `seed.day > from.day`, which is **verbatim the predicate at [`ProgressiveEMICalculator.java:1432`]**; and when that fires, the oracle's `FromDate.plusDays(1)` measurement [`:1433`] returns exactly what the clamped-step rule returns, so **`k_oracle ≡ k_clamped` identically — the special case IS the compensation.** **(ii) An exhaustive measurement inside the pinned oracle image — an observation of its own `java.time`, and a third category beside re-derivation and money capture:** over **every** ordered date pair `a ≤ b` in 2000-01-01…2040-12-31, **112,147,776** of them, the predicate fires on **45,253**, `packed ≠ clamped-step` on **exactly those 45,253**, both cross-terms are **0**, `k_oracle ≠ k_clamped` is **0** and `k_oracle ≠ k_packed` is **45,253** [VERIFIED: `.softhouse/capture/periodratio/analysis/t46_monthdiff_exhaustive-output.txt`; T44's 59,130 / 701 / 701 / 0 sweep is a subset by construction, and both figure sets are re-derived from this document's own text a further time by this task, `.softhouse/reviews/t47-probe/t47-monthend-output.txt`]. **(iii) The escape route revision 9 named is closed BY OBSERVATION:** `WEEKS` and `DAYS` cannot separate the two rules at all because nothing clamps on those units *(re-derivation)*, and `YEARS` **does** separate — on 165 pairs — but the `YEARS` arm is **unreachable**, because the ratio computed at [`:1405`] is handed to a `switch` [`:1598-1610`] whose `default` throws `UnsupportedOperationException` at [`:1609`], and both `T46-YR-A` (the separator shape) and `T46-YR-B` **returned that exception** [VERIFIED: `.softhouse/capture/periodratio/out/t46-periodratio-arms.json`]. **The normative consequence, and it is the one substantive change in this revision: §4.1.1 step B now PINS the packed rule together with the special case** — the oracle's own two clauses — while stating plainly that the clamped-step rule with no special case is observationally identical and therefore conformant. Of the four combinations of the two clauses **exactly one is wrong**, `packed ∧ no special case`, and it is exactly the one a port lands on by implementing the whole-months rule and forgetting the special case. **§8 item 3f's `TO_BE_CAPTURED` is WITHDRAWN**: the family grades the pair, separating the special case alone is impossible, and **a `TO_BE_CAPTURED` that can never succeed is a defect in this document, not a piece of backlog.** Nothing normative was weakened — step B already required the pair — and the seven witnesses are unchanged in what they discharge.
  **`installmentAmountInMultiplesOf` is honoured or lost BY CALLER, never by the field (§2.2, §3.2, §4.7, `contract.go`)** — task T46's **M-4**, which capture audit T44 raised. Revision 9 stated the drop as a property of the capture seam, in words a reader could take for a property of the field. It is a property of **`LoanApplicationTerms.assembleFrom(LoanRepaymentScheduleModelData, MathContext)`** [`LoanApplicationTerms.java:579-606`, which contains **zero** occurrences of `MultiplesOf`, VERIFIED by grep over the re-opened range] and therefore of every caller that assembles that way — including `LoanScheduleGeneratorServiceImpl.calculateInteresOnlyWithFirtDisbursement`, which carries the value the whole way [`:44`, `:56`, `:63`, all three re-opened here] and loses it at the assembler. The REST `calculateLoanSchedule` path **honours** it: *observed*, `B-02` returns period-1 `112,100.00` against `B-01`'s `112,082.37` [VERIFIED: `.softhouse/capture/charges/out/control/`, read as exact wire text]. **A capture seam's blind spot is a property of the caller, and §2.2 now carries a three-row per-caller table saying so.** §3.2's pin is unaffected and §4.7's refusal is unaffected — what changes is that neither may now be read as "the oracle ignores this input".
  **N46-1 — a SECOND ambient-`MathContext` leak, and the first one REACHABLE at MNT's scale (§4.1.2, §4.5.1, §8 item 9(h), §9, `contract.go`).** The **charge** rounding mode is **ambient, not threaded**. Re-derived to its locus: `calculateInstallmentCharge` computes the percentage under the **threaded** `mc` [`ProgressiveLoanScheduleGenerator.java:445-446`, and `:464-465` on the specified-due-date arm] and then wraps the result in the **two-argument** `Money.of(MonetaryCurrency, BigDecimal)` [`Money.java:114-116`, ambient read at `:115`], so the scale-2 rounding at [`Money.java:52`] takes **that** context's mode. **Two exact half-cent ties were OBSERVED on it** — `0.021875 %` of a period-1 interest of `21,600.00` is exactly `4.725` and returned **`4.73`**, `0.009375 %` is exactly `2.025` and returned **`2.03`**, both `HALF_UP` [VERIFIED: captures `T46-CH-03`, `T46-CH-04`]. **Unlike the 0-decimal-place `inMultiplesOf` leak [`Money.java:50`, gated at `:48-51`], this one has no gate that MNT fails.** **What this changes is the FORM of §4.1.2's rule, and deliberately so.** Revision 9 made the ambient claim rest on T42's absence test rather than on a call-site list, because the list had been wrong twice; it has now been wrong a **third** time, and the omission was not even in `Money.java`. Revision 10 therefore states the governing rule as a **property of each construction** — *which `MathContext` scales a value to the currency's decimal places is decided by the construction, never by the arithmetic that produced the value* [`Money.java:52`, `:494-496`, `:40`, `:42`] — which is checkable at a call site and **cannot be falsified by a site nobody listed**. **Nothing about Path A changes**: the seam's request record carries no charge, and T42's absence test would have thrown had that construction been reached, so P4 and §4.1's conclusion stand exactly as revision 9 states them. **No capture the program holds can detect the mode at this locus**, because on Path B the caller sources the threaded context from the ambient one [`LoanScheduleAssembler.java:753`, `:765`] and the two are one reference; separating them needs a tenant write. **`TO_BE_CAPTURED`, §8 item 9(h)**, and it is the sharpest remaining charge blind spot. Recorded alongside it, not admitted: `MathUtil.percentageOf(…, 19)` [`MathUtil.java:472-473`] takes the ambient mode too, at **six** loan-path sites, all down-payment computations and all outside the graded domain (T46's `T46-N1`).
  **The deleted "no half-cent tie is possible" claim, re-checked (§4.5.1, §8 item 9(f)).** Revision 9 removed T40's false claim after T44's `AP-5` refuted it by observation. **Revision 10 re-grepped both artefacts for any restatement and found none live**, and adds T46's two purpose-built ties — which are inside an **attested capture set** rather than an audit probe — so that sub-item is now three observed shapes away from a search and one promotion away from discharged. The half-closed part is stated too, because it is the part that matters: **a tie pins the mode that RAN and not WHICH context supplied it.**
  **Two claims of revision 9's that T46 makes FALSE, corrected as leaks rather than left to a reviewer.** (i) §4.1.1 said `periodRatio`'s `YEARS`, `WEEKS` and `DAYS` arms and its whole-period return branch "remain **entirely uncaptured**"; T46 captured all of them (`T46-WK-*`, `T46-DY-*`, `T46-RE-2`, `T46-RE-3`, `T46-RE-2ME`, and the two `YEARS` throws), and this revision's own non-separability argument cites those captures — **the document may not call uncaptured what it has just quoted.** (ii) §8 item 6 said "no capture exercises that branch at all", same fact. Both are corrected **and both items stay open**, because they ask for *vectors* and these are attested raw observations; and because coverage is not discrimination — measured over 186 repayment periods, `T46-RE-3` separates the `RepaymentEvery` reading on 3 and `T46-RE-2ME` the special-case-omitted reading on 2, while `T46-WK-*`, `T46-DY-*`, `T46-RE-2` and `T46-ARM-CTL` separate **nothing** [VERIFIED: `.softhouse/capture/periodratio/analysis/t46_arms_ratio-output.txt`]. That same model gives the non-separability result a **fourth** arrival: the clamped-step-minus-special-case reading differs from the pinned one on **0** of those 186 real observed periods.
  **One overreach of T46's that revision 10 does NOT propagate**, recorded because the honesty rule cuts both ways. T46's handoff says `WEEKS` and `DAYS` were "measured `0`" in the exhaustive sweep. They were not: `analysis/T46MonthDiffExhaustive.java` iterates date pairs and reports `MONTHS` and `YEARS` counts only. The `WEEKS`/`DAYS` claim is sound as a **re-derivation** — `plusWeeks` and `plusDays` never clamp, so the two whole-units functions are the same expression — and this document labels it as one.
  **A-3 is raised from two probes to nine captures (§4.5.1 fact 4, blind spots, §8 item 9(g)).** T44 showed the **request** `amount` governs on one percentage and one flat charge; T46 re-observed it on **seven** purpose-built captures across four `charge_calculation_enum` values, two `charge_time_enum` values and both fee and penalty, **7 for 7** [VERIFIED: `.softhouse/capture/charges/out/t46/DEFVSREQ.txt`]. The requirement is unchanged — a promoted vector's fixture is the **request bytes** — and the residual `[UNVERIFIED]` is now stated precisely: the enum values T46 did not try, and the question **no capture in the program touches**, which is what governs when the request omits `amount` entirely.
  **Correction leak, checked mechanically, because it is this project's signature failure and revision 9 found the retired claims had leaked across four to seven sites each.** Every correction above was followed by a whole-document and whole-`contract.go` grep for restatements [`.softhouse/reviews/t47-probe/t47-leakgrep-output.txt`].
  **Verification.** Revision 9's whole probe suite was re-run against revision 10: the normative-block diff, the from-text replay of 4,578 cells plus revision 9's three extra legs, the citation **range** check and the citation **content** check, and the leak grep — plus one new check, that the packed-versus-clamped-step rule **as written in this document** reproduces T46's `59,130 / 701 / 701 / 0` and the exhaustive `112,147,776 / 45,253 / 45,253 / 0` from the document's own text. Counts are in `.softhouse/handoff/T47-dec1-v10.md` and the probe outputs in `.softhouse/reviews/t47-probe/`.
  **What revision 10 does NOT do.** It does not reopen a decision, admit a charge, admit `DayCountActualActual`, add a field or a predicate, promote any capture, or ratify itself.

- **Revision 9 (task T45) is an ERRATUM.**""")

# --------- the two forward claims inside the revision-9 entry ----------
rep("A discriminator for the special case alone must come from `calculatePeriodRatio`'s "
    "`YEARS` / `WEEKS` / `DAYS` arms [`:1405`, `:1407`, `:1408`], which carry no special "
    "case and where the two rules do not cancel; those arms are uncaptured, and the item "
    "is `TO_BE_CAPTURED`. A sibling capture task in this fire is attempting exactly that "
    "shape, and **§8 item 3f is written so that whatever it returns settles the paragraph "
    "rather than contradicting it.**",

    "A discriminator for the special case alone must come from `calculatePeriodRatio`'s "
    "`YEARS` / `WEEKS` / `DAYS` arms [`:1405`, `:1407`, `:1408`], which carry no special "
    "case and where the two rules do not cancel; those arms are uncaptured, and the item "
    "is `TO_BE_CAPTURED`. A sibling capture task in this fire is attempting exactly that "
    "shape, and **§8 item 3f is written so that whatever it returns settles the paragraph "
    "rather than contradicting it.** **[REVISION 10: it returned, and the answer is that "
    "there is no such discriminator — `WEEKS` and `DAYS` cannot separate the two rules "
    "at all and the `YEARS` arm throws. Revision 9's `TO_BE_CAPTURED` is withdrawn and "
    "the arms are no longer uncaptured. See the revision-10 entry and §4.1.1 step B.]**")

io.open(DOC, "w", encoding="utf-8").write(s)
print("edit8: ok")
