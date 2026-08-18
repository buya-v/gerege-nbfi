# T33 handoff — DEC-1 **revision 6**

Applies the 1 P0, 2 P1s and 1 P2 required by independent re-review **T32** (`.softhouse/reviews/T32-DEC-1-v5-rereview.md`), plus its backlog recommendation. **Status stays DRAFT — NOT ratified.** Ratification is an independent re-review's call, not this task's; **no gate disposition was altered** and `.softhouse/gates.md`, `.softhouse/tasks.json`, `.softhouse/program.json` and `.softhouse/RESUME.md` are untouched (the branch was rebased onto `main` after the driver advanced it mid-task, so none of the driver's records is reverted).

**No live oracle was reachable and none was contacted.** Every correction is a source re-derivation against the pinned checkout `426a23544` or a quoted, already-committed observation. **Every divergence count and every worked figure for an uncaptured shape is a RE-DERIVATION**, recorded as a *candidate shape to capture*, never as oracle output.

| | |
|---|---|
| Branch | `softhouse/T33-dec1-v6-daycount` |
| Artefacts | `docs/adr/DEC-1-schedule-generator-adapter.md` (revision 6), `nexus/internal/apps/loanschedule/contract/contract.go`, `.softhouse/reviews/t33-probe/t33_spec_check.py` + `t33-output.txt` |
| Build / vet / gofmt | `go build ./...` clean, `go vet ./...` clean, `gofmt -l .` empty |
| Spec check | **(A) 13/13** committed observations reproduce · **(B) 5/5 + 3/3 + 3/3** discrimination · exit 0 |

---

## 1. Disposition of every T32 finding

| id | grade | disposition |
|---|---|---|
| **P0-T32-1** — the §4.1 rate factor's day-count ratio undefined in the ADR, and `contract.go` asserts something false | P0 | **FIXED, Arm A.** New **§4.1.1** defines both day counts normatively; §4.3.2 states the proration with a worked contrast labelled a re-derivation; the false clause is **deleted** from `contract.go`; §9 gains an obligation. |
| **P1-T32-1** — growth factor is a sum, not a singular | P1 | **FIXED.** §2.1 and `contract.go`'s `Rounding` doc now state `1 + Σ rateFactor`, exact, citing `RepaymentPeriod.java:216-217`; §9 gains an obligation. |
| **P1-T32-2** — `OutstandingPrincipalMinor` unspecified on disbursement / down-payment rows | P1 | **FIXED.** Stated on `PeriodKindDisbursement`, `PeriodKindDownPayment` and the field itself, and in ADR §4.5, with the graded/ungraded split. |
| **P2-T32-1** — §4.3.2 step 5 says "principal recomputed" | P2 | **FIXED.** Now "its **split** recomputed from steps 2–4", with the memoisation reason. |
| §11 of T32 — break the strictly-inside shape out as item **3d** | — | **DONE.** §8 gains item **3d**; the binding is widened from four vectors to five and still gates **conformance PASS and cutover, NOT ratification**. |

---

## 2. Which arm I took for P0-T32-1, and why

**Arm A — specify the day counts and delete the false clause.** T32's recommendation, and **my own source re-derivation confirms it rather than contradicting it**, so Arm B was not needed. What I read in the pinned checkout, independently of the review:

- `ProgressiveEMICalculator.calculateRateFactorPerPeriodForInterest` `:1367-1368` sets `actualDaysInPeriod = DateUtils.getDifferenceInDays(interestPeriodFromDate, interestPeriodDueDate)` — the routine's **own parameters**, i.e. the span the caller passed.
- `:1369-1370` sets `calculatedDaysInPeriod = DateUtils.getDifferenceInDays(repaymentPeriod.getFromDate(), repaymentPeriod.getDueDate())` — the **enclosing repayment period**, and nothing about the span. The identical pair, spelled `calculatedDaysInRepaymentPeriod`, is at `:1500-1501` / `:1502-1503` in `calculateRateFactorPerPeriod`.
- Both reach one routine on the graded domain's arm: `:1355-1356` → `:1403-1412` → `rateFactorByRepaymentEveryMonth` `:1923-1927` → `rateFactorByRepaymentPeriod` `:1950-1966`; and `:1486-1487` → `:1536` → the same. There the ratio is applied as `.multiply(actualDaysInPeriod, mc).divide(calculatedDaysInPeriod, mc)` `:1961-1962`, behind a guard returning `BigDecimal.ZERO` when `calculatedDaysInPeriod` is zero `:1953-1955`.
- The two call sites pass two different spans, `:638-643`: the interest period's own window for `rateFactor` `:639-640`, and `[interest period FromDate, repayment period DueDate]` for `rateFactorTillPeriodDueDate` `:641-642`. Same denominator, different numerators.

So the ratio is 1 **only** when the span is exactly the enclosing repayment period's window — false for a disbursement dated strictly inside a repayment period, which §3.1's window predicate admits and §4.3.2's third segmentation row describes.

Arm B (narrow §3.1's window to repayment boundaries, refuse every other date) is **rejected and recorded as rejected in §4.1.1**: a loan disbursed on a date that is not a repayment boundary is the ordinary Mongolian retail shape, and §4.6's own argument — the boundary must be runnable against the same traffic as the reference oracle — forbids refusing an input the oracle answers. Arm A costs three blocks of text and one deleted clause. Neither arm is a shape change, so **neither is a contract amendment**.

---

## 3. What changed, with `file:line`

### ADR `docs/adr/DEC-1-schedule-generator-adapter.md`

| where | change |
|---|---|
| lines 3, 9, 12 | Status → **revision 6**; run line and Supersedes updated (revision 5 superseded by re-review T32). |
| line 16 | New revision-history entry citing T32 by finding id. |
| §2.1 `:68-71` | The recurrence is written on `gₖ`; **new bullet**: `gₖ = 1 + Σ rateFactor` over the period's interest periods, all additions exact — **P1-T32-1**. The "exact addition" bullet is restated for many interest periods. |
| **§4.1.1 (new)** `:185-207` | **The two day counts in the ratio, normative** — definitions, `file:line` for each, which is numerator and which denominator, the exact-zero guard, the two call sites' two spans, the if-and-only-if statement, and the record of what revision 6 deletes and which arm was taken. **P0-T32-1.** |
| §4.3.2 `:473-486` | The proration written out for `rateFactorTillPeriodDueDate`, when the ratio is 1, and the worked contrast table — **explicitly labelled a re-derivation**, pointing at §8 item 3d. **P0-T32-1.** |
| §4.3.2 step 5 | "its principal recomputed from step 3" → "its **split** recomputed from steps 2–4", with the `getDueInterest` memoisation reason and T32's measurement that the cap never bites. **P2-T32-1.** |
| §4.3.2 "What is graded" | Rewritten as three ungraded items — the day-count proration (3d), the strictly-inside segmentation (3d), the interest round-trip (3b). |
| §4.3.1 standard/provenance | New paragraph recording revision 6's from-text transcription result (13/13 + 5/5 + 3/3 + 3/3) and the day-count provenance. |
| §4.5 | **New normative block** on `OutstandingPrincipalMinor` for disbursement (graded) and down-payment (ungraded) rows. **P1-T32-2.** |
| §4.3.1 closing | Backlog reference widened from four vectors to **five** (3, 3a, 3b, 3c, **3d**). |
| §8 item 3c / **3d (new)** | The strictly-inside shape **broken out of 3c** as its own item, with why one capture is unlikely to discriminate both; binding widened to five, still **not a ratification precondition**. |
| §9 | **Two new obligation clauses** — the rate-factor day-count obligation and the growth-factor composition obligation; the "round identically by specification" claim extended to the proration; the Go-module clause now says `1 + Σ rateFactor` and "with §4.1.1's day-count proration". |

### `nexus/internal/apps/loanschedule/contract/contract.go`

| where | change |
|---|---|
| `DayCountFixed30Over360` `:317-334` | **The false clause is DELETED.** Replaced with: the ratio is 1 *only* when the interest period spans the whole enclosing repayment period, which a strictly-inside disbursement makes false, and on such a period the correction is `days(span) / days(repayment period)`. A parenthetical records the deletion and the re-derived divergence. **P0-T32-1.** |
| `Rounding.RateFactorScale` `:539-591` | **New normative block "The two day counts in the ratio"** — the authoritative statement, matching §4.1.1 clause for clause. **P0-T32-1.** |
| `Rounding` doc `:460-479` | The growth-factor bullet rewritten: `1 +` the **SUM** of the period's interest periods' rate factors, `reduce(BigDecimal.ONE, BigDecimal::add)`, every addition exact; parenthetical records the correction and its measured inertness. **P1-T32-1.** |
| `PeriodKindDisbursement` `:1092-1100` | `OutstandingPrincipalMinor` = the amount advanced, `LoanSchedulePlan.java:52-56`, **graded**. **P1-T32-2.** |
| `PeriodKindDownPayment` `:1107-1116` | `OutstandingPrincipalMinor` = `outstanding + disbursed − downPayment`, `ProgressiveLoanScheduleGenerator.java:340-343`, **ungraded**. **P1-T32-2.** |
| `Period` interest section `:1446-1485` | The proration for `rateFactorTillPeriodDueDate`, written out, plus the worked contrast **labelled a re-derivation**. **P0-T32-1.** |
| `Period` step 5 `:1528-1537` | Split recomputed from steps 2–4. **P2-T32-1.** |
| `Period` "specified but ungraded" `:1551-1565` | Two places → **three**, naming the day-count proration and item 3d. |
| `Period.OutstandingPrincipalMinor` `:1637-1652` | The per-kind table of what "after this row is applied" means. **P1-T32-2.** |

---

## 4. The Java citations behind each new normative statement

All read in `/home/user/fineract` at the pinned commit `426a23544e8426a38ae43ae404670a0a7e85b9eb`, not taken from the review.

| statement | citation |
|---|---|
| `actualDaysInPeriod` = days across the span the factor is computed over | `ProgressiveEMICalculator.java:1367-1368` (`calculateRateFactorPerPeriodForInterest`), `:1500-1501` (`calculateRateFactorPerPeriod`) |
| `calculatedDaysInPeriod` = days of the **enclosing repayment period**, never the span | `ProgressiveEMICalculator.java:1369-1370`; same pair as `calculatedDaysInRepaymentPeriod` at `:1502-1503` |
| numerator / denominator roles in the ratio | `ProgressiveEMICalculator.java:1961-1962` (`rateFactorByRepaymentPeriod`, `:1950-1966`) |
| exact-zero guard on a zero repayment-period day count | `ProgressiveEMICalculator.java:1953-1955` |
| the two call sites and their two spans | `ProgressiveEMICalculator.java:638-643`; `rateFactor` `:639-640`, `rateFactorTillPeriodDueDate` `:641-642` |
| the graded arm's dispatch chain | `:1355-1356` → `:1403-1412` → `rateFactorByRepaymentEveryMonth` `:1923-1927` → `rateFactorByRepaymentPeriod` `:1950-1966`; and `:1486-1487` → `:1536` |
| growth factor = `1 + Σ rateFactor`, exact | `RepaymentPeriod.java:216-217` (`calculateRateFactorPlus1`), no `MathContext` `:216-218` |
| disbursement row's outstanding = amount advanced | `LoanSchedulePlan.java:52-56`; record field order `LoanSchedulePlanDisbursementPeriod.java:28-31` |
| down-payment row's outstanding | `ProgressiveLoanScheduleGenerator.java:340-343`; `LoanSchedulePlan.java:57-65`; record field `LoanSchedulePlanDownPaymentPeriod.java:33` |
| final row's split, not only its principal, is recomputed | `RepaymentPeriod.java:272-286` (`getDueInterest` memoised on `emi`, `min` at `:280`) |

---

## 5. Spec-check results — `.softhouse/reviews/t33-probe/t33_spec_check.py`

Written from **revision 6's own text**, in exact decimal / integer minor units, **no float anywhere on a money path**. Expectations quoted from `t32_validate.py` (which quotes the committed capture files); the model is this task's own. Output: `t33-output.txt`, exit 0.

**(A) All 13 committed observations reproduce digit-for-digit — 13 pass, 0 fail.**

**(B) The corrected text now DISCRIMINATES all three readings.** Each of the three reproduces the corpus **13/13** — which the script prints, because that is the finding: the corpus is blind to all three.

| reading | corpus | discriminated on |
|---|---|---|
| **B1** — the ratio-is-always-1 day counts, the clause revision 6 deletes (P0-T32-1) | 13/13 → blind | **5 / 5** strictly-inside-a-period shapes |
| **B2** — the textbook `balance × rateFactor` interest (P0-T29-2) | 13/13 → blind | **3 / 3** shapes T29 cited |
| **B3** — the wrong `n = NumberOfRepayments`, isolated (P0-T29-1) | 13/13 → blind | **3 / 3** shapes T29 cited |

**(C) informational** — P1-T32-1's two growth-factor compositions return identical money on **0 / 5** shapes, reproducing T32's measurement that the defect is a wording defect today, not a money defect.

The B1 figures agree **digit-for-digit** with T32's independently written `t32_inside_period.py` (e.g. MNT 1,200,000 / 6 × 21.6 %, disbursement 2024-01-15: revision 6 gives level 211,087.95 / final 211,088.97 / total interest 66,528.72; the deleted reading gives 212,786.91 / 212,789.26 / 76,723.81). **A re-derivation cross-checking a re-derivation. Neither is an observation, and neither may be promoted to the vector store.**

---

## 6. No regression

Every item T32 confirmed clean was re-checked after this change.

| earlier finding | result |
|---|---|
| T29's two P0s (`n`, the per-period interest) | **untouched and still resolved**; every cited `file:line` including `:195-197` is unchanged |
| **T28's loop steps 1–8**, the three guard conjuncts, the adjustment divisor, the strict adoption test, the three-iteration bound | **byte-for-byte preserved** — `git diff main` touches no line of §4.3.1's code block |
| the deleted revision-2 ordering clause | still deleted; its only hits remain the historical record of the deletion (`docs/adr/…:586`, `contract.go:1683`) |
| graded-domain blocks identical in both artefacts | **unchanged in both**; the block is outside every hunk of this diff |
| error precedence total and deterministic (§4.11, `contract.go`) | **unchanged** |
| `NumberOfRepayments < 1 → ErrInvalidRequest` in both artefacts | **unchanged** |
| §8 items 3, 3a, 3b, 3c | **unchanged in kind**; only 3d added and the binding count raised |

The phrase "every period in the graded domain" now appears **three** times, all as the historical record of its own deletion (the revision-history entry, §4.1.1's "What revision 6 deletes", and `contract.go:328`'s parenthetical) — the same pattern T32 accepted for the revision-2 ordering clause. It is **not operative anywhere**.

**Non-negotiables:** no `float32` / `float64` / `big.Float` outside prohibition prose (`contract.go:66`, `:1388-1389`, `:1547`); money is `int64` minor units; no Oracle Database / MySQL / MariaDB token; no US payment rails; three-field Mongolian names only where prohibited; no hard-coded time-zone offset or payment threshold; nothing described as insured, protected or guaranteed; "the oracle" used only in the test-oracle sense.

---

## 7. What still needs a fresh oracle observation

Recorded as **candidate shapes to capture**, never as results. None of them blocks ratification; all of them gate conformance PASS and cutover (§8's binding).

1. **§8 item 3d — a disbursement dated strictly inside a repayment period.** The P0's shape and the **largest** ungraded divergence in this document: 100 % of 2,913 re-derived shapes, worst total-interest gap MNT 1,816,050.11. Candidate **MNT 1,200,000 / 6 × 21.6 %, schedule start 2024-01-01, disbursement 2024-01-15**. One capture settles P0-T32-1 empirically and discharges the item. **Both readings' figures in §4.3.2 are re-derivations; neither may be promoted.**
2. **§8 items 3, 3a, 3b, 3c** — unchanged, all still outstanding.
3. **P1-T32-1's separating shape** — none exists inside today's graded domain (0 / 2,913). A capture is only needed once interest pauses, mid-term rate changes or multi-tranche enter the domain.
4. **`OutstandingPrincipalMinor` on a down-payment row** — the down-payment path is outside the graded domain, so it is settled from source and marked explicitly ungraded rather than captured (§8 item 4).

Nothing in revision 6 requires a live oracle to be **correct**; the outstanding captures are what would make it **graded**.
