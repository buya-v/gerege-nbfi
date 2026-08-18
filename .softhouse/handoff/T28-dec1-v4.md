# T28 handoff — DEC-1 **revision 4**

| | |
|---|---|
| Task | T28 (coder) |
| Branch | `softhouse/T28-dec1-v4-readjust-effect`, worktree `/home/user/wt-T28` |
| Satisfies | `.softhouse/reviews/T26-DEC-1-v3-rereview.md` §9 — one P0, three P1s, two P2s |
| Reference oracle | Fineract, pinned checkout — `git -C /home/user/fineract rev-parse HEAD` = **`426a23544e8426a38ae43ae404670a0a7e85b9eb`** ✔ verified this task |
| Live oracle | **NONE reachable.** No Docker, no PostgreSQL. **No new observation was taken, synthesised or implied.** Every figure in revision 4 is either a re-derivation from the pinned source (labelled) or an observation already committed by T21/T22/T23 (re-cited). |
| Ratification | **NOT done by this task, and no gate disposition was altered.** T29 decides. |

**Files changed**

| File | What |
|---|---|
| `docs/adr/DEC-1-schedule-generator-adapter.md` | revision 3 → **revision 4** |
| `nexus/internal/apps/loanschedule/contract/contract.go` | the normative artefact |
| `.softhouse/reviews/t28-probe/t28_spec_check.py` | **new** — the specification transcribed back out and re-checked (see §4 below) |
| `.softhouse/handoff/T28-dec1-v4.md` | this file |

---

## 1. P0-T26-1 — the re-adjust loop's EFFECT. **APPLIED.**

Revision 3 said only *when* the loop fires. Revision 4 defines what it does, in three places, as T26 required:

| Where | What is there now |
|---|---|
| **ADR `docs/adr/DEC-1-schedule-generator-adapter.md:276-357`** | new subsection **§4.3.1 "The re-adjust loop's EFFECT, defined rather than named"** — an eight-step normative pseudocode block in `int64` minor units, each step carrying its own `file:line`, followed by seven numbered consequences that each name a way an implementation can be wrong while still satisfying every sentence of revision 3, then the no-float rule and a provenance paragraph. |
| **ADR §9, `:600-601`** | the Go-module obligation bullet now says "**BOTH its trigger and its effect, exactly as §4.3.1 defines them**", followed by a second bullet enumerating the nine sub-obligations `(i)…(ix)` with citations, so the obligation cannot be met partially. |
| **`nexus/internal/apps/loanschedule/contract/contract.go:1046-1170`** | the same eight-step block plus the seven consequences, on the **`Period` type doc comment** — a live response type, **not** the doc comment of `InstallmentRoundingMultipleMinor` (the field pinned to zero), which is where T23 forbade it. |

`contract.go` previously never mentioned the adoption test at all; it is now consequence 4 there, in capitals, with the "failure discards the trial" behaviour spelled out.

### Java `file:line` backing each normative step

Every one of these was opened and read in the pinned checkout by this task. **T26's account was not taken on trust; each line was re-derived.** Two of T26's citations were tightened in the process (marked ✎).

| Step in §4.3.1 / `contract.go` | Java source | What the source says |
|---|---|---|
| Loop is on the main path | `ProgressiveEMICalculator.java:748-750`, guard at `:732-735` | `checkAndAdjust…` called at `:749` when `onlyOnActualModelShouldApply`, which is true whenever `scheduleModel.isEmpty()` — every initial disbursement. |
| `n` = all repayment periods | `ProgressiveLoanInterestScheduleModel.java:191-194` | `getRelatedRepaymentPeriods(null)` returns `repaymentPeriods` whole. |
| Loop skeleton, `do { … } while (adjustCounter <= 3)` | `ProgressiveEMICalculator.java:1258-1308`; counter init `:1262`; test `:1307-1308` | counter starts at **1**, is incremented **only after adoption** (`:1307`), tested at `:1308` ⇒ **at most three adopted iterations**. |
| Step 1 — the measured pair | `:1266` → `:1778-1789`. ✎ pair bound at `:1781` + `:1784`; difference at `:1783`; scan condition at `:1779` (`idx > 0`); degenerate branch at `:1788` | `getEmiAdjustment` scans from the END for the last **adjacent** pair in which neither period is fully paid; nothing is paid here, so it is `(n-2, n-1)`. `originalEmi` is the **penultimate** installment, not the level one. `n == 1` cannot enter the `for` (`idx > 0`) and falls to `:1788`, whose `emiDifference` is `copy(0.0)` = 0. |
| Step 2 — guard, all three conjuncts | `:1267-1269` → `EmiAdjustment.java:31-36`; `floor` at `:32`; `lowerHalf > 0` and `!isZero()` at `:33`; magnitude test `:34-35`; threshold constructor `Money.java:216-222` (`copy(double)` → `copy(BigDecimal)` → `new Money(currency, amount, mc)`), scaled at `Money.java:52` | `Money.copy(double)` **replaces** the amount, so the RHS is `floor(n/2)` **currency units flat** — no EMI dependence, no `InstallmentRoundingMultipleMinor` dependence. Integer form `abs(d)*100 > floor(n/2)*10^MinorUnitDigits` is exact. |
| Step 3 — adjustment magnitude | `EmiAdjustment.java:38-40`; `Money.dividedBy(long)` at `Money.java:352-358` (✎ short-circuit `valueToDivideBy == 1` at `:353-355`); re-scale at `Money.java:52` | `emiDifference.dividedBy(max(1, n − uncountablePeriods))` — divide at the threaded `MathContext`, then `Money.of(…, mc)` re-scales to the currency's decimal places under the same mode. Integer form given: `sign(d) * (2*abs(d) + div) / (2*div)`, i.e. nearest with ties away from zero (`HALF_UP`). |
| Step 3 — `uncountablePeriods` | `ProgressiveEMICalculator.java:2027-2031` | count of related periods where `originalEmi.isLessThan(period.getTotalPaidAmount())`. Nothing is paid on a schedule this contract generates and `originalEmi ≥ 0`, so it is **identically 0** and the divisor is `n`. Written into the rule anyway so the rule survives payment history. |
| Step 4 — candidate installment | `EmiAdjustment.java:42-44` (`originalEmi.plus(adjustment())`); multiple pass `:1270` → `:1761-1766` (with `safeRoundingForEMI` at `:1769-1776`) | `applyInstallmentAmountInMultiplesOf` is the **identity** when `installmentAmountInMultiplesOf` is null or ≤ 0 — which is the whole graded domain (`InstallmentRoundingMultipleMinor == 0`, §4.7). |
| Step 5 — break on equal | `:1271-1273` | if the multiple-rounded candidate `isEqualTo(originalEmi)`, break. |
| Step 6 — trial build | copy at `:1274-1276`; apply to related periods `:1279-1286`; balances `:1287`; residual `:1288` → `:1160-1219` | Every related period whose dates are at or after the first related period's, whose paid amount does not exceed the candidate, and which is not a re-aged early-repayment holder, gets `setEmi`/`setOriginalEmi` — inside the graded domain that is **all `n` periods**. Then balances recompute and the §4.3 final-period residual is **re-applied**. It is a rebuild, not a patch. |
| Step 7 — adoption test | `:1289-1291`; `EmiAdjustment.hasLessEmiDifference` at `EmiAdjustment.java:46-48` | `|newDiff| < |oldDiff|` **strictly**; equality is not adoption. Failure breaks at `:1290` **before** the copy-back at `:1293-1305`, so the live schedule keeps its **pre-trial** values — the trial is discarded. |
| Step 8 — adopt / bound | copy-back `:1293-1305`; balances `:1306`; `adjustCounter++` `:1307`; `while` `:1308` | Only on adoption. |

**Exact-integer arithmetic** is stated in both artefacts, covering the whole body and not only the guard, with `float32`/`float64`/`big.Float` named as prohibited. The one place where the two-step Java rounding could in principle differ from a single integer rounding — step 3 — is addressed explicitly in consequence 2: the quotient's denominator is `d ≤ n`, so it either sits exactly on a half-minor-unit tie (both forms round away from zero under `HALF_UP`) or lies at least `1/(2n)` of a minor unit from one, far outside the precision-19 intermediate error for any `|emiDifference|` below `10^17/n` minor units. The form is stated as written **for `HALF_UP` only**, the sole mode in the graded domain.

## 2. P1-T26-1 — the wrong ACTUAL arm. **APPLIED**, and **re-derived, not copied.**

Read directly: `ProgressiveEMICalculator.java:1505-1507` sets `partialPeriodCalculationNeeded = daysInYearType == ACTUAL && numberOfYearsDifferenceInPeriod > 0 && (…)`; `:1526-1531` returns through `rateFactorByRepaymentPartialPeriod` when it holds; the `switch (daysInMonthType)` opens at `:1533` with `case ACTUAL` at `:1534-1535` and `case DAYS_30` at `:1536`; the per-frequency `switch` that throws `"Invalid repayment frequency"` is at `:1602-1610` (`default ->` at `:1609`). An annual repayment period always spans a calendar-year boundary, so under `DayCountActualActual` the `:1526-1531` return always fires and **`:1534-1535` is unreachable for `FrequencyYears`**.

- **ADR `:464`** (§4.10) — "the `ACTUAL` arm at `:1534-1535` never reaches that dispatch" replaced by the correct mechanism, with the note that `:1534-1535` is reached only for sub-annual periods inside one calendar year.
- **`contract.go:243-261`** — same correction, and it now explicitly says it is consistent with `DayCountActualActual`'s own doc, which sits at `contract.go:303` and `:331` after this task's insertions (T26 cited it as `:317-319` against revision 3) and which revision 3 contradicted.
- **Both places now record**, as T26 asked, that **Q3b's evidence came out of the cross-year partial-period arm `:1505-1507` / `:1526-1531` — the arm ADR §8 item 5 calls the largest un-re-derived hole in the evidence base.**
- The **conclusion is unchanged**: `FrequencyYears` is refused either way, `ErrUnsupportedConfiguration` on the fixed-30/360 arm and `ErrNoDiscriminatingVector` on the ACTUAL arm, under the §4.11 precedence.

## 3. P1-T26-2 — the `Money.java:220-222` self-contradiction. **APPLIED.**

**ADR §8 item 7, `:573`.** The citation is split. `Money.java:134-148` (the `double`-taking arithmetic overloads) remain harness traps. `Money.java:216-222` — `copy(BigDecimal)` and `copy(double)`, which **replace** the amount rather than scaling it — is stated as being **on the live calculation path**, constructing the re-adjust guard's threshold at `EmiAdjustment.java:35` and the degenerate zero difference at `ProgressiveEMICalculator.java:1788`, both now normative in §4.3.1. The entry keeps the true part: no *port* may reproduce it with a float, because the `double` it takes is always an exact small integer.

## 4. Verification that the specification, as written, determines the money

`.softhouse/reviews/t28-probe/t28_spec_check.py` transcribes §4.3.1 steps 1–8 **literally**, in pure integer minor units (no float, no `Decimal` anywhere inside the loop), imports the surrounding schedule machinery **unchanged** from T26's independent model so that only T28's text is under test, and checks the result against the observations **already committed by T23**:

```
MNT 1014632 / 6 x 7.0% : level 172574.64, final 172574.62, total interest 20815.82  -> MATCH
MNT  127704 / 36 x 16.8%: level 4540.30,  final 4540.06,   total interest 35746.56  -> MATCH
MNT     100 / 6 x 7.0% : level 17.01,     final 17.00,     total interest 2.05      -> MATCH
ALL MATCH
```

Both discriminating branches are exercised: the 6 × 7.0 % case adopts one iteration and then stops on the guard; the 36 × 16.8 % case adopts one iteration and then stops on the **adoption test** (iteration 2's trial is discarded), which is exactly the step revision 3 omitted.

**This is a re-derivation, not an observation.** No oracle was contacted. The three expected triples are quoted from `.softhouse/reviews/t23-probe/`. The script is not a vector and must not be promoted to the vector store; its header says so.

## 5. Also applied (T26's P1-3 and both P2s)

- **P1-T26-3** — "seventeen per-period divergences" → **all eighteen**, at **ADR `:203`** (§4.1), **ADR `:504`** (§5 table row for `Rounding.SignificantDigits`) and **`contract.go:483-485`**. T23 established from the committed capture files that every one of the 18 repayment rows differs.
- **P2-T26-1** — the graded-domain block. `NumberOfRepayments >= 1` was in `contract.go`'s list and not the ADR's. **Decided (ENGINEERING, `chosen_by: agent`): it is a well-formedness condition, not a graded-domain predicate**, so `NumberOfRepayments < 1` is **`ErrInvalidRequest`**, which the §4.11 precedence puts ahead of any graded-domain refusal. Removed from the graded-domain block in `contract.go:641-653`, stated on the field at `contract.go:820-823`, and recorded in **ADR §3.1 `:130`**. The two blocks are now line-for-line identical. Also noted there and in `contract.go:655-664`: `NumberOfRepayments == 1` is well formed and graded, and the re-adjust loop cannot fire on it.
- **P2-T26-2** — **ADR `:213`** (§4.1). The weak inference (a precision-12-threaded capture on a precision-19 tenant reproducing the shipped literal) is replaced with the source argument, **verified this task**: inside the graded domain every `Money` is built through the three-argument `Money.of(…, mc)` and the constructor reads only the *rounding mode* from `getMc()` [`Money.java:52`]; the tenant-global-precision reads are `Money.java:103`, `:115`, `:160`, `:377`, all on the installment-multiple / `multipliedBy(double)` paths, which the graded domain excludes. All four lines were opened and confirmed.

## 6. What was NOT touched (T24 / revision 3 content T26 confirmed correct)

Checked explicitly, since T26 named these as the regression risk:

- **P0-2, disbursement window.** The graded-domain predicate `ScheduleStartDate ≤ Disbursements[0].Date < the last repayment DueDate` is unchanged in both artefacts and is **not weakened**. The deleted ordering-rule clause was **not** reintroduced — `git diff` adds no phrasing of it, and the only new text near the window is the `NumberOfRepayments` paragraph.
- **P0-3, error precedence.** `ErrInvalidRequest ≻ ErrUnsupportedConfiguration ≻ ErrNoDiscriminatingVector`, first applicable wins, is unchanged in §4.11 and on the error variables. The one new refusal classification added by this task (`NumberOfRepayments < 1` → `ErrInvalidRequest`) is *consistent* with it and is stated identically in both artefacts.
- No type, field, method, enum member or sentinel was added, removed, renamed or retyped. Revision 4 is doc-comment and prose only.

## 7. Statements that would need a FRESH oracle observation

None of these blocks ratification; recorded for the next oracle-reaching fire. Nothing in revision 4 depends on any of them being answered.

1. **A vector that trips the EMI re-adjust guard inside the graded domain.** Carried, ADR §8 item 3. Candidates from T23's committed cases: MNT 1,014,632 / 6 × 7.0 % and MNT 127,704 / 36 × 16.8 %.
2. **A vector that separates the ADOPTION TEST from its absence.** New — **ADR §8 item 3a**, added by this task on T26's finding. The two candidates above trip the guard but do **not** discriminate this step. T26's sweep names **MNT 100,025 / 12 × 16.8 %, schedule start 2024-01-01** as the first shape where the two bodies diverge; revision 4 records it as **a candidate to capture, and deliberately does not restate the figures it would produce**, because those figures are re-derived and would read as observed.
   Item 3a also **binds the gate where T26 said it belongs**: no conformance PASS may be claimed for `loanschedule` and no cutover may be proposed until both vectors exist. That is a UAT/cutover precondition, not a ratification precondition — the graded domain is designed to grow with no amendment (§3.1), and cutover is a hard `user` gate regardless. §4.3.1 and `contract.go` both carry the matching warning that **this rule is specified but ungraded**.
3. **`DayCountActualActual` vectors and an independent re-derivation of the cross-year partial-period arm** [`:1505-1507`, `:1526-1531`]. ADR §8 item 5, unchanged — but P1-T26-1 raises its priority, because Q3b (revision 4's only `FrequencyYears` evidence) came out of that arm. Revision 4 now says so in both artefacts rather than leaving it implicit.
4. **Promotion of the eleven `(19, HALF_UP)` captures to the vector store.** ADR §8 item 1, unchanged.

Explicitly **not** needing an observation: everything in §§1–3 and 5 above. All of it is source re-derivation from the pinned checkout, and §4 shows the specification is self-sufficient.

## 8. Checks

Run in `/home/user/wt-T28/nexus`:

```
go build ./...   -> exit 0, no output          CLEAN
go vet ./...     -> exit 0, no output          CLEAN
gofmt -l .       -> no output                  CLEAN
go test ./...    -> ? …/loanschedule/contract [no test files]   (declarations-only package)
```

No constraint was weakened to make anything pass.

**Non-negotiables scan (CLAUDE.md).** `grep -rn "float32|float64|big.Float|math/big"` over `nexus/` returns exactly three hits — `contract.go:66`, `:1169`, `:1170` — all prose that **prohibits** floats; no money quantity anywhere is anything but `int64` minor units, and every step of the new loop specification is written in whole minor units. Zero hits over both changed files for `ojdbc`, `oracle.jdbc`, `OracleDialect`, `:1521`, `com.mysql.cj`, `mariadb`, `go-sql-driver/mysql`, Stripe, Plaid, Lithic, Persona. The only `first_name`/`last_name` occurrences (`contract.go:86-87`, ADR `:373`) are the rules **prohibiting** them and mandating ovog / patronymic / given name. No hard-coded timezone offset, no hard-coded payment-rail threshold, no insurance / protection / guarantee language. The ADR's terminology block still separates "reference oracle (Fineract)" from the prohibited "Oracle Database", and revision 4 introduces no new use of either term outside that convention.

## 9. For T29

Revision 4 changes **no shape** — no identifier, no type, no sentinel. It closes the one specification gap T26 raised, corrects the three P1s and both P2s, and adds a committed artefact demonstrating that the new normative text, by itself, determines the money to the minor unit on all three committed observations. T26's own §8 position was that the missing *vector* is not a ratification blocker but the missing *specification* was; the specification is now present, and the vector requirement is bound to the conformance/cutover gate in ADR §8 item 3a.

**T28 did not ratify DEC-1 and altered no gate disposition.**
