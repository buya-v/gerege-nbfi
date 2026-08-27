# T49 — independent re-review of DEC-1 revision 10

**Task** T49, branch `softhouse/T49-dec1-v10-rereview`, worker `reviewer` (independent; did not plan,
write or revise this document).
**Target** `docs/adr/DEC-1-schedule-generator-adapter.md` revision 10 (1,620 lines) and
`nexus/internal/apps/loanschedule/contract/contract.go` (2,416 lines).
**Reference oracle** Fineract, pinned checkout `426a23544e8426a38ae43ae404670a0a7e85b9eb` at
`/Users/buv/fineract`, **read only — no Gradle, no build, no container, no HTTP, no server touched.**
**No oracle observation was taken by this task.** Every figure below is either re-derived here and
labelled as such, or quoted from a committed capture with its id.
Probe artefacts: `.softhouse/reviews/t49-probe/`.

---

## Verdict

**ACCEPTED WITH REQUIRED CHANGES.**

**No P0.** I re-derived the money math this document specifies — the packed-whole-months closed form
and its month-end compensation, the two rate-factor call sites and their multipliers, the three-operation
interest round-trip, the EMI re-adjust loop's eight steps and its integer guard, the five membership
conventions, and the charge locus revision 10 adds — from the pinned source and from the committed
corpus. **Every normative rule in this document that a Go port must implement is correct**, and the
one substantive change revision 10 makes (§4.1.1 step B's pinned pair, and the proof that neither clause
is separately observable) is not merely plausible: I proved it in closed form and reproduced its
exhaustive counts independently, from first principles, digit for digit.

**Three P1s and three P2s.** None of them changes a number a Go port must produce inside the Run-1
graded domain. Two of the three P1s are the same failure this program keeps hitting — a correction that
landed in the section a review named and not in the sections that restate the same claim — and one of
those two has been standing since **revision 5**, through eight review rounds, in **both artefacts**.
The third P1 is an arithmetic error in revision 10's own newest worked example.

**Why this is not "CLEAN — RATIFY", stated so the distinction is not read as theatre.** I did not find
a reason to reject and I say so plainly. I did find two false statements that ratification would
**freeze** — one of them inside a `contract.go` doc comment, which §1 makes un-amendable by an agent
once ratified ("re-documenting any identifier in `contract.go` … requires raising a gate"). They cost
one erratum pass to fix now and a gate to fix later. **P1-T49-2 in particular is cheaper to fix before
ratification than after, and that is the whole of my recommendation.**

---

## Surfaces examined (section by section)

Listed so silence is distinguishable from not looking. "CLEAN" means I re-derived or re-opened the
cited source and found the statement correct.

| surface | what I did | outcome |
|---|---|---|
| **§1** ratification / amendment semantics | read; cross-checked against `CLAUDE.md` §Answering gates and P-2 | CLEAN |
| **§2 / §2.1** behavioural facts | re-opened `ProgressiveEMICalculator.java:1822-1828`, `RepaymentPeriod.java:216-217` (exact `reduce(ONE, add)`, no `MathContext`), `InterestPeriod.java:145-158` | CLEAN |
| **§2.2** seam honours 17 of 19; per-caller table (revision 10, new) | re-opened `LoanApplicationTerms.java:579-606` and grepped it (**0** occurrences of `MultiplesOf` — the document's claim is exact); confirmed `daysInYearCustomStrategy` is assigned only at `:881`; verified `LoanScheduleGeneratorServiceImpl.java:44/:56/:63`; read `B-01`/`B-02` as exact wire text | **P1-T49-1** — a THIRD component is dropped and the table does not carry it |
| **§3.1** graded domain | compared the twelve-line block with `contract.go:1019-1030` | CLEAN (content identical) |
| **§3.2** "the seam's blind spot is empty" | re-derived | **P1-T49-1** — the enumeration is wrong; the *conclusion* survives |
| **§3.3** design rules | read | CLEAN |
| **§4.1** rounding, two senses | re-opened `:1950-1963` and compared the quoted Java byte for byte; `MoneyHelper.java:35`, `:91-93` | CLEAN |
| **§4.1.1** day counts, two call sites, `periodRatio`, **step B** | full re-derivation, below | CLEAN — and step B independently proved |
| **§4.1.2** ambient vs threaded (FORM changed in 8→9→10) | enumerated **every** `MoneyHelper` read and **every** `Money.of`/`Money.zero` call in `Money.java` myself | CLEAN — list is exactly right and complete |
| **§4.2** dates, month-end re-anchor | re-opened `DefaultScheduledDateGenerator.java:168-176` and `:130-131`; `LoanApplicationTerms.java:583-589` | CLEAN — quoted Java is byte-identical |
| **§4.3** final-period residual | re-opened `:1160-1219` region, `RepaymentPeriod.java:348`, `:399` | CLEAN |
| **§4.3.1** EMI re-adjust loop, all 8 steps | re-opened `:1258-1308`, `:1778-1789`, `EmiAdjustment.java:31-56`, `Money.java:220-222`, `:352-358`; re-derived the integer guard | CLEAN |
| **§4.3.2** per-period interest, M1–M5, segmentation, step 4a/4b | re-opened `InterestPeriod.java:145-188`, `RepaymentPeriod.java:145-152/:252-286/:345-350/:389-403/:449-451`, `ProgressiveLoanInterestScheduleModel.java:191-197/:238-245/:264-296`, `LoanRepaymentScheduleProcessingWrapper.java:251-254`, `LoanCharge.java:371-373`, `LoanScheduleParams.java:533-535`, `ProgressiveLoanScheduleGenerator.java:400-415` | CLEAN |
| **M1–M5 reconciliation + restatement grep** | grepped both artefacts for every restatement of "which row a charge lands on" | CLEAN — **no leak**; see below |
| **§4.4** six pinned inputs | re-opened every citation | **P1-T49-1** touches one row |
| **§4.5** response shape | re-opened `:157`, `:159-164`, `LoanSchedulePlan.java:52-56` | CLEAN |
| **§4.5.1** charges, C-1, C-2, the ambient charge locus (revision 10, new) | re-opened `:445-446`, `:464-465`, `Money.java:114-116`/`:115`/`:52`; verified the two ties against `T46-CH-03`/`-04` wire text; re-derived the tie arithmetic | **P1-T49-3** (arithmetic), plus **P2-T49-2** |
| **§4.6** ordering | re-opened `:305-309`, `:318`, `:121`/`:141`, `:147-150` | CLEAN |
| **§4.7** `InstallmentRoundingMultipleMinor` | re-opened `:1761-1766`, `:1770-1776`, `Money.java:159-161`/`:163-170`; verified `LoanRepaymentScheduleModelData.java:36` is an `Integer` of MAJOR units; verified `B-02` = `112100.00` | CLEAN |
| **§4.8** rates | read | CLEAN |
| **§4.9** day count + `ErrNoDiscriminatingVector` refusal | cross-checked against §4.10, §8 item 5 and the corpus | **P1-T49-2** |
| **§4.10** `FrequencyYears` | re-opened `:1505-1507`, `:1526-1531`, `:1533-1539`, `:1602-1610` | CLEAN |
| **§4.11** error taxonomy + precedence | read | CLEAN |
| **§5** Run-1 corpus | compared against `.softhouse/capture/` as it stands today | **P2-T49-1** |
| **§6** forward compatibility | read | **P1-T49-1** touches §6.7 |
| **§7** switch mechanism | read | CLEAN |
| **§8** backlog, items 1–9 incl. 3f, 6c, 9(h) | compared against the corpus incl. `capture/actualactual/` | **P2-T49-3**; item 5 is **not** false — see below |
| **§9** consequences and obligations | read every obligation against §4 | CLEAN |
| **`contract.go`** | scanned for `float32`/`float64`/`big.Float`, `first_name`/`last_name`, prohibited vendors/drivers; checked graded-domain block, `MNT`/496/minor unit 2, IANA zones | CLEAN except **P1-T49-2** |
| **CLAUDE.md non-negotiables across the ADR** | grepped for float on money paths, insured/protected/guaranteed, name fields, US rails, Oracle Database / MySQL / MariaDB, `(19, HALF_UP)` | **CLEAN — zero violations** |

**Citation range check, run independently.** I extracted every `File.java:line` and `File.java:a-b`
token from the ADR mechanically, resolved each basename against the pinned checkout (preferring
`src/main`), and checked existence and range: **155 distinct citations, 329 occurrences, 0 out of
range, 0 ambiguous basenames.** (`.softhouse/reviews/t49-probe/`, and see *Citations spot-checked*.)

---

## Re-derivations performed

### 1. §4.1.1 step B — the packed rule, the special case, and the non-separability proof

This is revision 10's one substantive change and it had had one round of scrutiny. I did not accept
the document's argument; I re-derived it.

**Closed form, derived here from `ProgressiveEMICalculator.java:1419-1459` and `DateUtils.java:308-317`.**
`getExactDifference` → `getDifference` → `unit.between(first, second)` [VERIFIED: `DateUtils.java:308-317`,
re-opened], i.e. `LocalDate.monthsUntil`, whose packing is `prolepticMonth × 32 + dayOfMonth` with
**truncation toward zero**. With `K = pm(b) − pm(a)` and `a ≤ b`:

* numerator `= 32K + (b.day − a.day)`; if `b.day ≥ a.day` it lies in `[32K, 32K+30]` → `K`; if
  `b.day < a.day` it lies in `[32K−30, 32K−1]` → `K−1`. So **`packed = K − [a.day > b.day]`.** ✓
* `a.plusMonths(j)` has day `min(a.day, len(month))`; at `j = K` it is `≤ b` iff
  `min(a.day, len(b)) ≤ b.day`, and at `j = K−1` it is always `≤ b`. So
  **`clamped = K − [min(a.day, len(b)) > b.day]`.** ✓
* `min(a.day, len(b)) > b.day ⟹ a.day > b.day`, so the indicators differ only when `a.day > b.day`
  **and** `min(a.day, len(b)) ≤ b.day`, which forces `len(b) ≤ b.day`, and `b.day ≤ len(b)` always.
  **They differ ⟺ `b.day = len(b) ∧ a.day > b.day`** — **verbatim the predicate at `:1432`**
  (`targetDateLastDay == targetDateDay && seedDateDay > targetDateDay`, re-opened). ✓
* When it fires, `b + 1 day` is the **1st** of the next month, so `pm` rises by one, and the predicate
  forces `a.day > b.day = len(b) ≥ 28`, hence `a.day ≥ 29 > 1`:
  `packed(a, b+1) = (K+1) − 1 = K = clamped(a, b)`. **`k_oracle ≡ k_clamped`, identically.** ✓
* Reachability of `a ≤ b`: `calculateSeedDate` [`:1461-1481`, re-opened] returns either
  `scheduleModel.getStartDate()` — the first repayment period's `FromDate`
  [`ProgressiveLoanInterestScheduleModel.java:209-211`, re-opened] — or `repaymentPeriod.getFromDate()`.
  In the second case `a = b` and the predicate cannot fire. ✓

**The document's closed form, its equivalence, and its conclusion are all correct.**

**Exhaustive check, written from first principles and from the document's text alone**
(`.softhouse/reviews/t49-probe/monthdiff.py`, output `monthdiff-output.txt`; exact integers, no float):

| quantity | this task re-derived | DEC-1 rev 10 asserts |
|---|---|---|
| days 2000-01-01 … 2040-12-31 | **14,976** | — |
| ordered pairs `a ≤ b` | **112,147,776** | 112,147,776 ✓ |
| `[:1432]` predicate fires | **45,253** | 45,253 ✓ |
| *(sub-sweep 2000–2005, every ordered pair)* `packed ≠ clamped` | **928**, exactly the 928 firings | — |
| fires ∧ `packed == clamped` | **0** | 0 ✓ |
| ¬fires ∧ `packed ≠ clamped` | **0** | 0 ✓ |
| `k_oracle ≠ k_clamped` | **0** | 0 ✓ |
| `k_oracle ≠ k_packed` | **928** = the firing count | (45,253 over the full window) ✓ |
| first firing pair | `2000-01-29` / `2001-02-28`, packed **12**, clamped **13**, oracle **13** | identical ✓ |

The pair count is a closed check the document does not offer and I did:
`14,976 × 14,977 ÷ 2 = 112,147,776` exactly, and 41 years with 11 leap years is 14,976 days. The
document's figure is arithmetically forced, not merely quoted.

**The `YEARS` escape route.** Re-opened `:1404-1410`: `case YEARS -> calculatePeriodRatio(…, ChronoUnit.YEARS, mc)`
**is** evaluated, and the result is handed at `:1412-1413` to
`calculateRateFactorPerPeriodBasedOnRepaymentFrequency`, whose `switch` at `:1602-1610` carries
`DAYS`/`WEEKS`/`MONTHS` and `default -> throw new UnsupportedOperationException("Invalid repayment frequency")`
at **`:1609`**. So the arm computes a ratio and then throws. Corroborated by capture:
`t46-periodratio-arms.json` contains exactly **two** `UnsupportedOperationException: Invalid repayment frequency`
records [VERIFIED: `.softhouse/capture/periodratio/out/t46-periodratio-arms.json`]. **The document's
citation and its conclusion are both right.**

**Verdict on step B: CLEAN.** The four-row table (only `packed ∧ no special case` is wrong) is correct,
and pinning the oracle's own pair while stating that clamped-step-without-the-case is conformant is the
honest form.

### 2. The two rate-factor call sites and the multiplier

Re-opened `:636-643`: `:639-640` computes `rateFactor` over the interest period's own
`[FromDate, DueDate]`; `:641-642` computes `rateFactorTillPeriodDueDate` over
`[interest period FromDate, repayment period DueDate]`. ✓ exactly §4.1.1's table.

Traced the argument threading myself: `:1412-1413` passes `periodRatio` into the third parameter and
`BigDecimal.valueOf(30)` into the fourth; `:1536-1537` passes `repaymentEvery` and `daysInMonth`;
`:1607` (`rateFactorByRepaymentEveryMonth`) → `:1925-1926` **swaps** them into
`rateFactorByRepaymentPeriod(interestRate, daysInMonth→repaymentPeriodMultiplierInDays,
repaymentEvery→repaymentEvery, …)` [`:1922-1927`, `:1950-1951`, consumed at `:1956-1957`].
**So `periodRatio` lands in the multiplier slot and `30` in the days-in-month slot — exactly as the
document's table states.** `:1508`'s ternary yields the literal 30 under `DAYS_30`, and `:1537` is
reachable only from `case DAYS_30 ->` at `:1536`, so the fourth argument is 30 on both sides
unconditionally. **CLEAN, including the unconditional narrowing revision 8 made.**

### 3. §4.1's snippet, and the three-operation interest round-trip

`:1950-1963` re-opened and compared with the Java the document quotes: identical modulo the source's
`//` line-continuation comments. The zero guard is at `:1953-1955`, the four `mc`-qualified operations
at `:1956-1962`, the trailing `setScale(mc.getPrecision(), mc.getRoundingMode())` at `:1962`. ✓
`InterestPeriod.getCalculatedDueInterest` [`:145-158`] has the exact-zero short circuit at `:146-148`,
the `DECLINING_BALANCE` base at `:151`, and the three separately `getMc()`-rounded operations at
`:155`, `:156`, `:157` in that order. **CLEAN.**

### 4. §4.3.1's loop, including the integer guard

`:1258-1308` re-opened line by line against the document's eight steps: `:1262` counter, `:1265`/`:1307-1308`
bound, `:1266` → `:1778-1789` pair location (`idx > 0`, so `n == 1` falls to the `copy(0.0)` degenerate
branch at `:1788`), `:1267` guard, `:1270` multiple pass, `:1271-1273` no-change break, `:1274-1288`
trial on a copy with `:1287` balances and `:1288` residual, `:1289-1291` **strict** adoption test over the
trial's **full** period list, `:1293-1306` copy-back. `EmiAdjustment.java:31-36/:38-40/:42-44/:46-48/:54-56`
match every clause. **CLEAN.**

The integer guard re-derived: the source compares `|Δ|.multipliedBy(100)` against
`originalEmi.copy(floor(n/2))`, and `Money.copy(double)` [`Money.java:220-222`] **replaces** the amount,
so in **major** units the test is `|Δ| × 100 > floor(n/2)`; multiplying both sides by 100 gives the
document's minor-unit form `|Δ|ₘ × 100 > floor(n/2) × 10^MinorUnitDigits`. At `n = 12` that is
`|residual| > 0.06`, exactly as §4.3.1 states. **CLEAN.**

### 5. §4.1.2's ambient-site list — re-enumerated, not accepted

I grepped `Money.java` myself for every `MoneyHelper.` read and every `Money.of` / `Money.zero` /
`roundToMultiplesOf` call site.

* **Direct ambient reads: exactly 7** — `:103`, `:115`, `:119`, `:131`, `:154`, `:160`, `:495`.
  **Identical to the document's list, member for member.**
* **Two-argument `Money.of` call sites inside the file: exactly 4** — `:169`, `:233`, `:266`, `:377`.
  **Identical to the document's "indirect" list.**
* Every other `Money.of`/`Money.zero` in the file passes an explicit `mc` or `getMc()`. **The document's
  closing sentence is exactly true.**

Line numbers spot-verified: `:32` is the `MathContext` field, `:40`/`:42` the constructor and its `mc`
assignment, `:48-51` the `inMultiplesOf` guard, `:50` the two-argument `roundToMultiplesOf` call,
`:52` the currency-scale `setScale`, `:494-496` `getMc()`. **All exact. CLEAN.**

### 6. §4.5.1's charge locus (N46-1) — the newest normative claim in the document

Re-opened `ProgressiveLoanScheduleGenerator.java:433-452` and `:454-468`. At **`:445-446`**:

```java
Money loanChargeAmt = Money.of(cumulative.getCurrency(),
        amount.multiply(loanCharge.getPercentage()).divide(BigDecimal.valueOf(100), mc));
```

`cumulative.getCurrency()` returns a **`MonetaryCurrency`**, so this is the **two-argument**
`Money.of(MonetaryCurrency, BigDecimal)` at `Money.java:114-116`, which supplies
`MoneyHelper.getMathContext()` at `:115` — **the ambient context** — while the threaded `mc` is in scope
and is **not** passed. The scale-2 rounding then happens at `Money.java:52` under that context's mode.
`:464-465` is the same shape on the specified-due-date arm. **N46-1 is correct, and revision 10's
per-construction rule is the right generalisation of it.** CLEAN as a rule.

Ties verified against the wire text: `T46-CH-03` period-1 `feeChargesDue` = **`4.73`**, `T46-CH-04` =
**`2.03`** [VERIFIED: `.softhouse/capture/charges/out/t46/T46-CH-03-tie-pctinterest-4725-raw.json`,
`…-CH-04-…-2025-raw.json`]. Re-derived: `0.021875 %` of `21,600.00` is exactly `4.725` and `0.009375 %`
is exactly `2.025`; `HALF_UP` gives `4.73`/`2.03`, `HALF_EVEN` gives `4.72`/`2.02`. **The conclusion is
right.** The *stated integer chain* is not — **P1-T49-3**.

### 7. M4 / M5 against the corpus

Re-opened `:400-415`. `isDue` is computed at `:403`; the `isInstalmentFee()` arm at `:404-405`
**never reads it**; `:406`, `:408`, `:411` are the three `isDue`-gated arms. `isInstallmentChargeApplicable`
is the literal `true` at `:373`/`:376` and `!isRecalculatedInterestComponent()` at `:479`/`:483`;
`isFirstPeriod()` is `1 == instalmentNumber` [`LoanScheduleParams.java:533-535`] and
`incrementInstalmentNumber()` runs at `:143`, **after** `applyChargesForCurrentPeriod` at `:140`, while
`updatePeriodsWithCharges` runs at `:154` **after** the loop at `:116-145`. **Every clause of the M4 and
M5 rows is exact.**

Corroborated from the corpus, read as wire text by this task:
`FC-02` reports `"totalFeeChargesCharged":30000.00` with **12** rows at `"feeChargesDue":2500.00`;
`FC-07` reports `9000.00` on **exactly one** row [VERIFIED:
`.softhouse/capture/charges/out/attested/FC-02-flat-instalment-raw.json`,
`FC-07-fee-on-p3-duedate-raw.json`]. The **MNT 27,500** figure is `30,000 − 2,500`, exact.
**M5 is observed, and P1-T43-3's correction is right. CLEAN.**

### 8. Restatement / leak grep (the T2-class failure the driver named)

Grepped both artefacts for every restatement of M4's role. The claim appears at **§4.3.2's table row,
§4.3.2's prose, §4.3.2's "which rule governs which field", §9's date-membership obligation, and
`contract.go:1886-1966`** — and in the revision-9 history entry, where the old wording is quoted only as
the thing being corrected. **Every live site says the corrected thing: M4 governs `SPECIFIED_DUE_DATE`
and `OVERDUE_INSTALLMENT` only; M5 is the absence of a test and puts an `INSTALMENT_FEE` on every row.
No leak. CLEAN.** This is the one place prior rounds' signature failure would have shown, and it does not.

---

## P0

**None.**

I state this plainly, because eight rounds have produced seven P0s and the temptation to produce an
eighth is exactly the failure mode this role must avoid. **I re-derived every money computation this
document specifies and found none of them wrong.** The specific things I tried to break and could not:

* the packed/clamped/oracle equivalence (proved in closed form **and** measured exhaustively, above);
* the multiplier assignment at the two call sites (traced through three levels of parameter swapping);
* the three-operation round-trip's order and rounding points;
* the loop's guard, divisor, adoption test and iteration bound in exact integers;
* M4 vs M5 against 21 charge captures' actual fee rows;
* the ambient-vs-threaded rule, by re-enumerating `Money.java` from scratch;
* the ambient charge locus, by resolving the overload at `:445` myself.

---

## P1

### P1-T49-1 — the capture seam drops a **third** component, and §2.2 / §3.2 say it drops two

**Sections:** §2.2 (heading, opening sentence, table), §3.2, §4.4 (the `interestRecognitionOnDisbursementDate`
row), §6.7. **Cross-reference:** open finding **T48-N1**, which the brief names as a finding this
document must not contradict.

**The exact sentences.**

> §2.2 heading: "**### 2.2 The fact that shaped this revision: the capture seam honours 17 of 19 components**"

> §2.2: "The embeddable seam assembles the oracle's terms object exclusively through a Builder
> [`LoanApplicationTerms.java:579-607`]. **Two** of the record's 19 components never survive that assembly:"

> §3.2: "**The two components the seam drops are exactly the two the graded domain pins to their inert
> values:**"

> §6.7: "**`interestRecognitionOnDisbursementDate`** — one boolean field if a product ever needs accrual
> from the disbursement date. **Cheap**, but a gate."

**Why they are wrong.** A **third** of the 19 components — `interestRecognitionOnDisbursementDate`,
component 15 of `LoanRepaymentScheduleModelData` [VERIFIED: `LoanRepaymentScheduleModelData.java:32-39`,
re-opened and counted here: 19 components, `interestRecognitionOnDisbursementDate` at `:37`] — is
**silently replaced by a different field** before the calculator ever reads it. Re-derived here from the
pinned checkout, not taken from T48's word:

1. `assembleFrom` **does** set it — `.interestRecognitionOnDisbursementDate(modelData.interestRecognitionOnDisbursementDate())`
   [VERIFIED: `LoanApplicationTerms.java:603`], and the private `Builder` copy constructor **does** copy
   it out [VERIFIED: `:327-328`]. So far it looks honoured, which is why nobody caught it.
2. But `ProgressiveLoanScheduleGenerator.generate` reads the calculator's config through
   `toLoanConfigurationDetails()`, and **that method never reads the field**. Its **16th** positional
   argument is `isInterestChargedFromDateSameAsDisbursalDateEnabled != null && isInterestChargedFromDateSameAsDisbursalDateEnabled`
   [VERIFIED: `LoanApplicationTerms.java:1753`], while the 16th constructor parameter of
   `LoanConfigurationDetails` is named `interestRecognitionOnDisbursementDate` and is assigned to that
   field [VERIFIED: `LoanConfigurationDetails.java:72`, assigned at `:92` — I counted the 23 arguments
   against the 23 parameters by hand].
3. `isInterestChargedFromDateSameAsDisbursalDateEnabled` is assigned **only** at `:847`, in a positional
   constructor this path never reaches, and there is **no builder setter for it and no `assembleFrom`
   call to one** [VERIFIED: grep for `this.isInterestChargedFromDateSameAsDisbursalDateEnabled\s*=` over
   the whole file returns exactly one hit, `:847`]. So on the Path-A seam it is `null` → **`false`,
   unconditionally, whatever the request carries.**
4. The only calculation-path reader is
   `scheduleModel.loanProductRelatedDetail().isInterestRecognitionOnDisbursementDate()`
   [VERIFIED: `ProgressiveEMICalculator.java:1579`] — i.e. the aliased value, never the request's.

**Observed**, and this is not my observation: `T48-AA-1` and `T48-AA-2` differ **only** in that flag and
are **0 of 87 cells apart** on the Path-A seam, while their Path-A2 twins (which bypass
`toLoanConfigurationDetails`) are **35 of 115 apart**, total interest `76,160.63` against `76,158.97`
[VERIFIED: `.softhouse/handoff/T48-actualactual-captures.md` §2, §9 T48-N1].

**What this does and does not cost.** It moves **no money inside the Run-1 graded domain**: `:1579` is
reached only from `calculatePeriodFractions`, gated on `partialPeriodCalculationNeeded`, whose first
conjunct is `daysInYearType == ACTUAL` [VERIFIED: `:1505-1507`], and §3.1 pins
`DayCount == DayCountFixed30Over360`. The only other reader on this call graph is `:194`, inside the
`allowFullTermForTranche` branch §4.4 pins `false`. **That is why this is a P1 and not a P0 — I checked
for exactly that before grading it.** What it does cost is that **three** statements in the argument that
licenses freezing this contract on a seam-captured corpus are false, and §6.7 tells a future reader that
adding the field is "cheap" when in fact it needs the same Path-B re-binding §4.7 records for
`InstallmentRoundingMultipleMinor` — and even there, whether the server keeps the two settings in step
is `[UNVERIFIED]` (T48's own `TO_BE_CAPTURED`; every product on `gerege` has both flags false).

**Replacement text.**

* §2.2 heading → "**### 2.2 The fact that shaped this revision: the capture seam honours 16 of 19 components**"
* §2.2 opening → "The embeddable seam assembles the oracle's terms object exclusively through a Builder
  [`LoanApplicationTerms.java:579-607`], and hands the result to the calculator through
  `toLoanConfigurationDetails()` [`:1746-1756`]. **Three** of the record's 19 components do not survive
  that journey:"
* §2.2 table → add a third row:
  | `interestRecognitionOnDisbursementDate` | **Replaced, not dropped, which is why it looks wired at every earlier step.** `assembleFrom` sets it [`:603`] and the `Builder` copy constructor copies it out [`:327-328`] — but `toLoanConfigurationDetails()` [`:1746-1756`] never reads the field. Its 16th positional argument is `isInterestChargedFromDateSameAsDisbursalDateEnabled` [`:1753`], while `LoanConfigurationDetails`'s 16th parameter is `interestRecognitionOnDisbursementDate` [`LoanConfigurationDetails.java:72`, assigned `:92`]. The aliased field is assigned only at `:847`, unreachable through this assembler, so it is `false` on this seam whatever the request carries — and `ProgressiveEMICalculator:1579` reads the alias. *Observed*: `T48-AA-1` vs `T48-AA-2` differ only in this flag and are **0 of 87 cells** apart on Path A, while the Path-A2 twins are **35 of 115** apart (task T48, finding T48-N1). |
* §3.2 → "**The three components the seam drops are exactly the three the contract pins to their inert
  values:**" with a third bullet: "`interestRecognitionOnDisbursementDate` ← pinned `false` by §4.4, and
  **provably inert** under `DayCountFixed30Over360`, because its only calculation-path reader
  [`ProgressiveEMICalculator.java:1579`] sits behind `partialPeriodCalculationNeeded`'s
  `daysInYearType == ACTUAL` conjunct [`:1505-1507`]. Note this one is pinned by a **§4.4 pin**, not by a
  §3.1 predicate — the same materially weaker reason §4.1.2 already records for `Money.java:130-132`."
  The conclusion sentence ("inside the graded domain, the seam's blind spot is empty") **stands unchanged
  and is still true**, and should say that it now rests on three pins rather than two.
* §4.4 row → append: "**The seam cannot express it either** (task T48's T48-N1, added here): the value is
  replaced by `isInterestChargedFromDateSameAsDisbursalDateEnabled` at [`LoanApplicationTerms.java:1753`]
  before the calculator sees it (§2.2), so on Path A the pin is enforced by the seam as well as by the
  contract, and *observed* as such. A future reader relaxing this pin must re-bind to the server path
  first, exactly as §4.7 records for `InstallmentRoundingMultipleMinor`."
* §6.7 → replace "Cheap, but a gate." with "**Not cheap, and a gate**: the Path-A seam cannot deliver
  this input at all (§2.2, T48-N1), so exposing it needs the same re-binding to the running-server path
  §4.7 records for `InstallmentRoundingMultipleMinor` — and whether the server itself keeps
  `interestRecognitionOnDisbursementDate` and `isInterestChargedFromDateSameAsDisbursalDateEnabled` in
  step is `TO_BE_CAPTURED`."

---

### P1-T49-2 — a retired claim that leaked for five revisions, and it is in `contract.go`

**Sections:** §4.9, and **`contract.go:365-371`** (the `DayCountActualActual` doc comment).

**The exact sentences.**

> §4.9: "**`DayCountActualActual` stays in the value domain and the computation is refused** —
> `ErrNoDiscriminatingVector` — **until a capture exists**. … computing it would mean returning plausible
> numbers **nobody has compared with the oracle**, on **the one arm of the algorithm no independent
> re-derivation has yet reproduced from source**."

> `contract.go:365-371`: "Outside the graded domain — refuse with ErrNoDiscriminatingVector. **No capture
> in the corpus exercises it**, and the arm it selects is **the one arm of the algorithm that no
> independent re-derivation has yet reproduced from source**. A code path returning plausible numbers
> nobody has compared against the oracle is exactly the unverifiable promise this contract exists to
> prevent."

**Why they are wrong — and the document refutes itself, twice.**

1. "**no independent re-derivation has yet reproduced from source**" was **retired in revision 5** by
   P2-T29-1. §8 item 5 says so in terms: "The **re-derivation is done** and this item no longer asks for
   it (revision 5, P2-T29-1): task T30 re-derived the cross-year partial-period arm … and reproduced
   captures `B-03`/`B-04` digit-for-digit … and re-review T29 confirmed the re-derivation
   independently." §4.10 says the same: "revision 4 flagged that arm as this document's largest
   un-re-derived hole, and **revision 5 retires that caveat**". **P2-T29-1 landed in §4.10 and §8 item 5
   and not in §4.9 or in `contract.go`.** That is precisely the failure mode recorded against task T2 in
   `gates.md` — a correction landing in the section the review named and not in the sections that restate
   the same claim — and it has survived revisions 5, 6, 7, 8, 9 and 10 and reviews T29, T32, T34, T43 and
   the two capture audits.
2. "**No capture in the corpus exercises it**" / "nobody has compared with the oracle" is false on the
   corpus this document itself tabulates: `B-03` and `B-04` are `DayCountActualActual` server-path
   captures — §8 item 5 names them, §4.10 names them, §4.7 discusses `daysInYearCustomStrategy` on them,
   and §4.4 records that the oracle rejects that field at product creation unless days-in-year is
   `ACTUAL` [`LoanProduct.java:462-472`]. They have been committed since before revision 3 and were
   re-emitted byte-identically as T40's zero-charge control.
3. It is now **doubly** false. Task T48 captured the arm on **three seams** at production settings —
   18 Path-A, 27 Path-A2, 13 Path-B and 28 exactness probes — with both controls passing and determinism
   proved from fresh containers [VERIFIED: `.softhouse/capture/actualactual/`, `ATTESTATION.md`,
   `PROVENANCE.md`, `REPRODUCE.md`, committed on `main`]. Revision 10's own header says "a sibling task
   is capturing that arm", so this half is not a defect *of* revision 10 — but it is a sentence
   ratification would freeze.

**Why the refusal itself is still right, so this is an erratum and not a rejection.** ACT/ACT must stay
refused, for the reason §4.9's own last paragraph and §4.4 give and which is untouched by any of the
above: admitting it makes `daysInYearCustomStrategy` live, **and that is an amendment**. What is wrong
is the *stated criterion* ("until a capture exists") and the *stated evidence gap*. Under the document's
own discipline the criterion is a **promoted, admissible vector**, which does not exist for this arm and
is what §8 item 5 correctly asks for.

**Why it is worth fixing before ratification rather than after.** §1: "Once this document is ratified,
adding, removing, renaming, retyping or **re-documenting any identifier in `contract.go`** … requires
raising a gate." The false sentence is a doc comment on the identifier `DayCountActualActual`. Correcting
it costs one erratum now and a **gate** afterwards.

**Replacement text.**

* §4.9 → "**`DayCountActualActual` stays in the value domain and the computation is refused** —
  `ErrNoDiscriminatingVector` — **until an admissible vector exists**, which is the criterion §8 item 1
  applies to every other rule in this document. Keeping the member costs nothing (removing it later would
  be a narrowing and a gate). What is **not** the reason, stated because revisions 5–10 carried the stale
  version of it: the arm **has** been re-derived from source — task T30 re-derived the cross-year
  partial-period arm and reproduced captures `B-03`/`B-04` digit for digit, and re-review T29 confirmed it
  independently (§4.10, §8 item 5, P2-T29-1) — and the arm **has** been captured: `B-03`/`B-04` on the
  server path, and task T48's 58 captures across three seams at production settings
  [VERIFIED: `.softhouse/capture/actualactual/`]. **Captured is not promoted** (§8 item 1), and the
  further reason the refusal stands is the one §4.4 gives: admitting this convention makes
  `daysInYearCustomStrategy` live, **and that is an amendment**."
* `contract.go:365-371` → "Outside the graded domain — refuse with ErrNoDiscriminatingVector. The arm
  has been re-derived from source (task T30) and captured (`B-03`, `B-04`, and task T48's captures across
  three seams), but **no admissible vector exists for it**, and §8 item 1's promotion step is what stands
  between a capture and a graded rule. A code path graded by nothing is exactly the unverifiable promise
  this contract exists to prevent."

---

### P1-T49-3 — revision 10's own exact-integer worked check is wrong by a factor of 100

**Section:** §4.5.1, *Which `MathContext` rounds a CHARGE* (added in revision 10; the newest arithmetic
in the document).

**The exact sentence.**

> "The arithmetic in exact integers: `2,160,000` minor units × `21,875` ÷ `10^6` ÷ `100` =
> `472,500,000` ÷ `10^8` = `4.725` exactly, and `× 9,375` gives `202,500,000` ÷ `10^8` = `2.025`
> exactly. **No floating point anywhere, in the oracle's arithmetic or in this check.**"

**The re-derivation that falsifies it** (exact integers, this task):

```
2,160,000 × 21,875 = 47,250,000,000      <- NOT 472,500,000
2,160,000 × 21,875 ÷ 10^6 ÷ 100 = 472.5  <- NOT 4.725
   21,600 × 21,875 =    472,500,000      <- the stated product comes from the MAJOR-unit amount
2,160,000 ×  9,375 = 20,250,000,000      <- NOT 202,500,000
   21,600 ×  9,375 =    202,500,000
```

The chain as written mislabels its own multiplicand: the number that produces `472,500,000` is
**`21,600`**, the amount in **major** units, not `2,160,000` minor units. Read literally in minor units
the chain yields `472.5` minor units, and the document then divides a *different* number by `10^8`.
**In a program whose first non-negotiable is "money is integer minor units", the one place §4.5.1 does
the minor-unit integer arithmetic explicitly states a false identity between money quantities — and it is
the sentence that ends "No floating point anywhere, in the oracle's arithmetic or in this check."**

**Why it is a P1 and not a P0.** Nothing normative rests on it. The final values `4.725`/`2.025`, the
observed `4.73`/`2.03`, and the `HALF_UP` conclusion are all correct and independently confirmed by me
against `T46-CH-03`/`T46-CH-04`'s wire text. A port that implements §4.1.2's per-construction rule is
right regardless of this paragraph. But a worked check is included precisely so a reader can *reproduce*
it, and this one does not reproduce.

**Replacement text.**

> "The arithmetic in exact integers, in **minor** units throughout: period-1 interest is `2,160,000`
> minor units; the percentage `0.021875 %` is the integer `21,875` scaled by `10^6`; so the charge is
> `2,160,000 × 21,875 ÷ 10^6 ÷ 100 = 47,250,000,000 ÷ 10^8 = 472.5` minor units — **exactly half a minor
> unit above `472`** — which the constructor at [`Money.java:52`] must resolve at scale 2, and `HALF_UP`
> resolves it to `473` minor units, `4.73`. The same in **major** units, which is the form the oracle's
> `BigDecimal`s take: `21,600 × 21,875 ÷ 10^8 = 4.725`. For `0.009375 %`: `2,160,000 × 9,375 ÷ 10^8 =
> 202.5` minor units → `203`, `2.03`; equivalently `21,600 × 9,375 ÷ 10^8 = 2.025`. `HALF_EVEN` would
> have given `472`/`4.72` and `202`/`2.02`. No floating point anywhere, in the oracle's arithmetic or in
> this check."

---

## P2

### P2-T49-1 — §5's "FIVE capture sets" is stale, in the paragraph written for the ratifier

**The exact sentence.** "**FIVE capture sets now exist, and a ratifier should not confuse them.**"

**Why it is wrong.** `.softhouse/capture/` holds **eight** capture families today, all committed:
`out/` (Path-A pass 3 / 3b), `pathb/` (B-01…B-04 + T36's EMI-loop probes), `dec1-binding/` (T37),
`periodratio/` (T39 **and T46's arm captures**), `charges/` (T40 **and T46's `out/t46/` set**),
`mathcontext/` (**T42**), `audit-t44/` (**T44**'s probes) and `actualactual/` (**T48**). Revision 8
already cited T42's set in §4.1.2 and §8 item 6c without adding it here; revision 10 cites T46's two sets
throughout §4.1.1, §4.5.1 and §8 without adding them here; T48's set landed after revision 10 was written.
The section's own stated purpose — "a ratifier should not confuse them" — is what makes an out-of-date
enumeration worth an erratum. Prior rounds graded exactly this class (P2-T43-2, the 1,224 / 1,239 counts).

**Replacement text.** Re-state the list as **eight**, adding: "(f) the **T42 `MathContext` set**
(`.softhouse/capture/mathcontext/`), which grades §4.1.2's ambient-versus-threaded rule and §8 item 6c;
(g) the **T44 audit probes** (`.softhouse/capture/audit-t44/`), which are audit probes and explicitly
**not** part of any attested set; and (h) the **T48 ACT/ACT set** (`.softhouse/capture/actualactual/`),
which exercises an arm outside the graded domain and grades nothing this contract carries." Keep the
closing sentence — "None of the eight is a parity vector" — unchanged.

### P2-T49-2 — a blind-spot claim the corpus now refutes

**The exact sentences** (two sites, §4.5.1 fact 4 and §8 item 9(g)): "…and whether `m_charge.amount`
governs **when the request OMITS `amount` entirely is untried by every capture in the program**" /
"— untried by **EVERY** capture in the program —".

**Why it is wrong.** Task T48 tried it: omitting `amount` is a hard **HTTP 400 on 5 of 5 legs**, across
`chargeTimeType` 1, 2, 8 and 12 and both fee and penalty [VERIFIED:
`.softhouse/handoff/T48-actualactual-captures.md` §5, headline 5]. So `m_charge.amount` can never govern —
the request is rejected before any charge arithmetic runs. It was true when revision 10 was written and
is false now; a blind-spot list that keeps asserting a closed blind spot is the exact defect revision 9
recorded against T40's half-cent claim (T44's A-5).

**Replacement text.** "…and what governs when the request omits `amount` entirely is now **settled by
observation**: the request is rejected with **HTTP 400** on 5 of 5 legs across `chargeTimeType` 1, 2, 8
and 12 and both fee and penalty, so `m_charge.amount` never governs at all [VERIFIED: task T48,
`.softhouse/handoff/T48-actualactual-captures.md` §5]. The `[UNVERIFIED]` that remains is narrower: the
`charge_calculation_enum` values T46 did not try with a *disagreeing* amount (5 and 9) and
`charge_time_enum` 2."

### P2-T49-3 — §8 records no status for the ACT/ACT arm, and T48-N4 belongs in item 5

**§8 item 5 is NOT false as written**, and I say so because the brief invited the opposite conclusion:
it asks for **vectors**, and no vector is promoted, so "The *vectors* remain outstanding" is exactly
right under this document's own captured-versus-promoted discipline. The defect is an omission, not a
falsehood: item 5 now says nothing about the arm having been **captured**, while §4.1.1, §4.5.1 and
§8 items 6 and 9 were all updated in revision 10 the moment T46's captures landed. Revision 10's header
says "a sibling task is capturing that arm"; it returned.

**Recommended addition to §8 item 5.** "**STATUS: CAPTURED, NOT YET PROMOTED** (task T48,
`.softhouse/capture/actualactual/`). The arm is observed on three seams at production settings — Path A
(the embeddable seam), Path A2 (`ProgressiveEMICalculator`) and Path B — with both controls passing and
determinism proved byte-identical from fresh containers. `FEB_29_PERIOD_ONLY`'s **second** effect, which
this item asks any future vector to settle, is **observed in pure isolation**, and `FULL_LEAP_YEAR` is
**confirmed** behaviourally identical to the field being unset (0 of 285 cells on the production wiring).
**One admissibility condition follows and it is a trap** (T48's N4): where both calendar years have the
same length, `Σ daysᵢ ÷ 365 = totalDays ÷ 365`, so the partial arm and the plain ACT/ACT branch
**coincide exactly** and such a shape grades a port identically whether it implements the arm or not.
**Any vector promoted for this arm must cross a leap-year boundary with a non-zero first segment.**"

---

## Citations spot-checked (and their outcome)

Every one below was **re-opened in the pinned checkout by this task**, not taken from the document or
from any prior review. All are correct unless marked.

| citation | what the document says it is | outcome |
|---|---|---|
| `ProgressiveEMICalculator.java:1404-1413` | the `periodRatio` switch and the interest call site | ✓ exact |
| `:1405`, `:1406`, `:1407`, `:1408`, `:1409` | YEARS / MONTHS / WEEKS / DAYS arms and the `default -> throw` | ✓ exact |
| `:1412-1413` | `periodRatio` + literal `BigDecimal.valueOf(30)` | ✓ exact |
| `:1419-1459` | `calculatePeriodRatio` | ✓ exact |
| `:1426-1436`, predicate `:1432`, effect `:1433`, else `:1435` | the month-end special case | ✓ exact, byte for byte with the document's pseudocode |
| `:1441-1458`, division `:1453`, exact add `:1454`, return `:1457-1458` | step C's walk | ✓ exact — `:1453` is the only `mc`-rounded operation, `:1454` carries none |
| `:1461-1481` | `calculateSeedDate`, both conjuncts | ✓ exact |
| `:1500-1503`, `:1367-1370` | the two day counts at both entry points | ✓ exact |
| `:1508`, `:1533-1539`, `:1536`, `:1537` | `daysInMonth` and the `case DAYS_30 ->` arm | ✓ exact (`:1508`, not `:1509` — the document is right and T39 was wrong) |
| `:1598-1610`, `:1609` | the frequency switch and its throwing default | ✓ exact |
| `:1922-1927`, `:1950-1963`, `:1950-1951`, `:1953-1955`, `:1956-1957`, `:1961-1962` | the rate-factor chain and the parameter swap | ✓ exact |
| `:1258-1308`, `:1262`, `:1266-1273`, `:1274-1288`, `:1289-1291`, `:1293-1308` | the re-adjust loop | ✓ exact |
| `:1778-1789`, `:1788` | `getEmiAdjustment` and the degenerate branch | ✓ exact |
| `:1761-1766`, `:1770-1776` | `applyInstallmentAmountInMultiplesOf` → `safeRoundingForEMI` | ✓ exact |
| `:636-643`, `:639-640`, `:641-642` | the two rate-factor call sites and their spans | ✓ exact |
| `:1505-1507`, `:1526-1531`, `:1578-1584` | the partial-period arm and the year-end boundary | ✓ exact |
| `EmiAdjustment.java:31-36`, `:38-40`, `:42-44`, `:46-48`, `:54-56` | guard, adjustment, adjusted EMI, strict test, `n` | ✓ exact |
| `Money.java:32`, `:40`, `:42`, `:48-51`, `:50`, `:52` | the `mc` field, the constructor, the guard, the scale | ✓ exact |
| `Money.java:102-104/:103`, `:114-116/:115`, `:118-120/:119`, `:130-132/:131`, `:150-157/:154`, `:159-161/:160`, `:163-170/:169`, `:224-234/:233`, `:261-267/:266`, `:372-378/:377`, `:494-496/:495` | §4.1.2's ambient list | ✓ **all eleven exact, and the list is complete** — I re-enumerated the file |
| `Money.java:220-222`, `:352-358` | `copy(double)` replaces; `dividedBy(long)` short-circuits at 1 | ✓ exact |
| `MoneyHelper.java:35`, `:74-82`, `:79`, `:91-93` | `PRECISION = 19`, the throw, `getMathContext` | ✓ exact |
| `DateUtils.java:308-317` | `getExactDifference` → `getDifference` → `unit.between` | ✓ exact |
| `ProgressiveLoanScheduleGenerator.java:400-415`, `:403`, `:404-405`, `:406`, `:408`, `:411` | M4/M5 | ✓ exact |
| `:445-446`, `:464-465` | the charge percentage under the threaded `mc`, wrapped by the two-argument `Money.of` | ✓ exact — and the overload resolves to `MonetaryCurrency`, so N46-1 holds |
| `:116-145`, `:121-122`, `:132`, `:137`, `:140`, `:143`, `:154` | main loop, disbursement registration, row balance, the charge-free running total | ✓ exact |
| `:305-309`, `:318`, `:332-347`, `:345`, `:351` | M3's half-open window, disbursement row, down-payment branch | ✓ exact |
| `:367-382` | `applyChargesForCurrentPeriod` — contains **no** `addTotalRepaymentExpected` | ✓ exact |
| `:373`, `:376` literal `true`; `:479`, `:483` `isFirstPeriod()` | M4/M5's path dependence | ✓ exact |
| `:486` / `AbstractCumulativeLoanScheduleGenerator.java:504` | "the one line the two generators share" | ✓ exact — I compared them and they are identical |
| `:492-504` | `separateTotalCompoundingPercentageCharges` | ✓ exact |
| `:157`, `:159-164` | `totalOutstanding = BigDecimal.ZERO` | ✓ exact |
| `LoanApplicationTerms.java:579-606` | the assembler | ✓ exact — **grepped: 0 occurrences of `MultiplesOf`**, as claimed |
| `:217`, `:828`, `:304-351`, `:380`, `:567-568`, `:604`, `:881`, `:583-589`, `:600`, `:606`, `:348`, `:866` | §2.2 / §4.2 / §4.4 mechanisms | ✓ all exact |
| `LoanScheduleGeneratorServiceImpl.java:44`, `:56`, `:63` | the per-caller table's second row | ✓ exact |
| `LoanScheduleAssembler.java:753`, `:765` | Path B sources the threaded context from the ambient one | ✓ exact |
| `MathUtil.java:472-473` | ambient mode with a literal precision | ✓ exact |
| `LoanRepaymentScheduleProcessingWrapper.java:251-254`, `LoanCharge.java:371-373`, `LoanScheduleParams.java:533-535` | M1 / M4's predicate and flag | ✓ exact |
| `ProgressiveLoanInterestScheduleModel.java:191-197`, `:209-211`, `:238-245`, `:264-296` | M2, the start date, M1's reach, the segmentation | ✓ exact |
| `RepaymentPeriod.java:149`, `:216-217`, `:252-257`, `:264`, `:272-286`, `:345-350`, `:389-403`, `:449-451` | §4.3.2 steps 1–4 and `isFirstRepaymentPeriod` | ✓ exact |
| `InterestPeriod.java:145-158`, `:146-148`, `:151`, `:155-157`, `:160-166`, `:168-188`, `:174`, `:186` | the three operations and the later-segment rule | ✓ exact |
| `DefaultScheduledDateGenerator.java:128-129`, `:130-131`, `:168-176` | §4.2's month-end rule | ✓ exact, byte-identical to the quoted Java |
| `LoanRepaymentScheduleModelData.java:32-39`, `:36` | the 19-component record; `installmentAmountInMultiplesOf` as an `Integer` | ✓ exact — I counted the 19 components |
| `LoanConfigurationDetails.java:66-77` | (T48-N1) the 16th parameter | ✓ exact — **and it is what makes P1-T49-1 true** |
| `LoanApplicationTerms.java:1753` | (T48-N1) the aliased 16th argument | ✓ exact |

**Mechanical range check:** 155 distinct citations, 329 occurrences, **0 out of range, 0 ambiguous**.
No citation in this document points at the wrong line as far as I could test, which is a genuine change
from rounds T43 and T44.

**Captures read as exact wire text by this task:** `B-01` (`112082.37`), `B-02` (`112100.00`),
`FC-02` (`totalFeeChargesCharged 30000.00`, 12 rows at `2500.00`), `FC-07` (`9000.00`, one row),
`T46-CH-03` (`4.73`), `T46-CH-04` (`2.03`), `t46-periodratio-arms.json` (two
`UnsupportedOperationException: Invalid repayment frequency`).

---

## What I could not verify

Stated so nothing above is read as more than it is.

* **The 45,253-firing sweep's *oracle-JVM* provenance.** I reproduced the counts arithmetically from
  first principles in Python and they agree exactly. I did **not** run anything inside the pinned oracle
  image, so "these are the pinned JVM's own `java.time` results" remains T46's claim, not mine. My
  agreement is a re-derivation cross-checking an observation.
* **The `YEARS` arm's 165 separating pairs.** Immaterial — I verified the arm throws — but I did not
  reproduce the count.
* **T39's 51,729-pair disjointness sweep** and **T44's 59,130-pair sweep**: the document itself marks the
  first `[UNVERIFIED as a committed artefact]`; I did not re-run either. The document's non-separability
  conclusion does not depend on them, because the closed form and the exhaustive sweep carry it.
* **Every capture cell count I did not personally re-read** — the 4,578-cell from-text replay, the
  415-of-415 and 116-of-116 discriminations, the 21-of-21 M4+M5 replay, the 186-period arm scoring. I
  spot-checked six captures by wire text and all six matched; I did not re-run the replays.
* **Whether the running server keeps `interestRecognitionOnDisbursementDate` and
  `isInterestChargedFromDateSameAsDisbursalDateEnabled` in step** (P1-T49-1's Path-B half). Re-derived
  from source only; T48 records it `TO_BE_CAPTURED` because every product on `gerege` has both false.
  `[UNVERIFIED]`
* **Anything requiring the oracle.** I contacted no server, started no container, ran no Gradle, and
  took no observation.
* **`contract.go` in full.** I read its rounding, day-count, membership and graded-domain blocks and
  swept the whole file for banned patterns; I did not re-derive every one of its 2,416 lines against §4.

---

## Recommendation on ratification

**Ratify, after a single erratum pass — revision 11 — applying P1-T49-1, P1-T49-2, P1-T49-3 and the
three P2s. Do not re-open anything else.**

The reasoning, stated so the driver can weigh it rather than take it:

1. **There is no P0 and I looked hard for one.** The money math is right. The one substantive change
   revision 10 makes is not just defensible, it is **proved** — and I proved it independently rather than
   checking that T46 and T47 agreed with each other. This document is materially more correct than
   revision 8, which T43 was already willing to ratify.
2. **Two of the six findings would be frozen by ratification and one of them lives in `contract.go`.**
   §1 makes re-documenting an identifier in `contract.go` a gate. P1-T49-2 is a doc comment on
   `DayCountActualActual` that says the arm is un-re-derived and uncaptured when the same document says
   twice that it is re-derived, and the corpus now holds 60 captures of it. That is the driver's own
   stated reason for declining T43: **known-wrong sentences are not frozen.** It costs one pass now and a
   gate later.
3. **P1-T49-1 is the same shape as P1-T43-3 but one severity band lower, and the difference is worth
   naming.** P1-T43-3 was wrong about **money** (an instalment fee on one row instead of twelve, MNT
   27,500). P1-T49-1 is wrong about **coverage** — the seam drops three inputs, not two — and the money
   is unaffected because the third input is pinned and unreachable under 30/360. It is not a reason to
   reject. It **is** a reason not to freeze §2.2 and §3.2 in a form a future reader would re-derive and
   find false, in the very argument that licenses freezing this contract on a seam-captured corpus.
4. **The erratum is bounded and mechanical.** No type, field, enum member or graded-domain predicate
   moves. Nothing in §3.1, §4.1.1, §4.1.2, §4.3.1, §4.3.2, §4.6, §4.8, §4.11 or §9 changes. The largest
   single edit is one new row in §2.2's table and one new bullet in §3.2, both of which **strengthen**
   the existing conclusion rather than weaken it: the seam's blind spot inside the graded domain is still
   empty, now on three pins instead of two.
5. **Do not order a ninth review round for its own sake.** If revision 11 applies exactly these six items
   and changes nothing else, the sensible next step is a **diff-scoped** check that the six were applied
   and that no seventh claim leaked — not another full re-derivation of surfaces this round and T43 both
   found clean. Eight rounds of full re-derivation have now converged: T43 found no P0, and neither did I.

**What I am not saying.** Nothing here bears on cutover, on promotion of any capture to the vector store,
or on regulatory sign-off. §8's seven-vector binding is undischarged and a conformance PASS still grades
none of the seven rules. Those remain exactly where revision 10 leaves them.
