# T31 handoff — DEC-1 **revision 5**

Applies the 2 P0s, 2 P1s and 1 P2 required by independent re-review **T29** (`.softhouse/reviews/T29-DEC-1-v4-rereview.md`). **Status stays DRAFT — NOT ratified.** Ratification is an independent re-review's call, not this task's; no gate disposition was altered.

**No live oracle was reachable and none was contacted.** Every correction is a source re-derivation against the pinned checkout `426a23544` or a quoted, already-committed observation. Every divergence count and every worked figure for an uncaptured shape is recorded as a **re-derivation / candidate shape to capture**, never as oracle output.

| | |
|---|---|
| Branch | `softhouse/T31-dec1-v5-corrections` |
| Artefacts | `docs/adr/DEC-1-schedule-generator-adapter.md` (revision 5), `nexus/internal/apps/loanschedule/contract/contract.go`, `.softhouse/reviews/t31-probe/t31_spec_check.py` + `t31-output.txt` |
| Build / vet / gofmt | `go build ./...` clean, `go vet ./...` clean, `gofmt -l .` empty |
| Spec check | **13/13** committed observations reproduce; **3/3 + 3/3** discrimination |

---

## 1. Disposition of every T29 finding

| id | grade | disposition |
|---|---|---|
| **P0-T29-1** — `n` is misdefined | P0 | **FIXED.** New normative definition of *related repayment periods*; `n` corrected everywhere; step 6's overwrite set and step 3's `uncountablePeriods` scope corrected; level-installment scope stated; degenerate case re-stated. |
| **P0-T29-2** — per-period interest unspecified | P0 | **FIXED.** New **ADR §4.3.2** and a new normative section on `Period`, plus a new §9 obligation clause. |
| **P1-T29-1** — §4.4's `FEB_29_PERIOD_ONLY` reason incomplete | P1 | **FIXED** in §4.4, §4.7, §4.10 and `contract.go`'s pinned-inputs list. |
| **P1-T29-2** — `contract.go` carries the retired calibration inference | P1 | **FIXED.** Replaced with the argument from source. |
| **P2-T29-1** — stale "largest un-re-derived hole" | P2 | **FIXED** in §4.10 and §8 item 5, citing T30. |
| §9 of T29 — widen the vector binding to four | — | **DONE.** §8 gains items **3b** and **3c**; the binding still gates **conformance PASS and cutover, NOT ratification**. |

---

## 2. What changed, with `file:line`

### ADR `docs/adr/DEC-1-schedule-generator-adapter.md`

| where | change |
|---|---|
| line 3, 9, 12 | Status → **revision 5**; run line and Supersedes updated. |
| line 16 | New revision-history entry citing T29 by finding id. |
| §2.1 (`:73`) | The interest bullet now says the textbook form is *not* the rule and points at §4.3.2. |
| §3.1 (`:141`) | `NumberOfRepayments == 1` is no longer given as the sufficient condition for the degenerate pair — the **related list holding one element** is. |
| §4.3 (`:279`) | The `floor(n/2)` threshold sentence now says `n` is the related count. |
| §4.3.1 (`:288`–`:326`) | **New block "Related repayment periods — the normative definition"**, with the effective-due-date derivation and the `n` table. |
| §4.3.1 (`:328`) | `n` re-defined: `relatedRepaymentPeriods.size()`; `n == NumberOfRepayments` **iff** the disbursement is strictly inside period 1; `rows` indexed over the related periods. |
| §4.3.1 step 1 | Degenerate case noted as reachable without `NumberOfRepayments == 1`. |
| §4.3.1 step 3 | `uncountablePeriods` counted over the **related** list. |
| §4.3.1 step 6 | "inside the graded domain that is ALL n periods" **deleted**; overwrite set is the related periods, rows before them keep a zero installment. |
| §4.3.1 step 7 | New note: the oracle re-measures over the trial model's **full** list at `:1289`, and why that is the same pair. |
| §4.3.1 consequences | Seven → **eight**; new consequence 8 on `n`. |
| §4.3.1 closing / Provenance | Backlog reference widened to 3/3a/**3b**/**3c**; provenance rewritten for T31's spec check. |
| **§4.3.2 (new)** | The whole per-period interest computation, normative. |
| §4.4 `daysInYearCustomStrategy` row | Two effects stated, not one. |
| §4.7 closing finding | "only under a daily interest calculation with an actual year" corrected. |
| §4.10 | Unreachability of `case ACTUAL` qualified by the `null` pin; "largest un-re-derived hole" retired, citing T30. |
| §8 item 3 | New sub-items **3b** and **3c**; binding widened to four, still not a ratification precondition. |
| §8 item 5 | Asks for vectors only; the re-derivation is recorded as done. |
| §9 | New per-period-interest obligation clause (a)–(h); loop obligation clause corrected for `n`, `uncountablePeriods`, the overwrite set, the degenerate case, plus new item (x) on the level-installment scope; the "round identically by specification" claim now cites §4.3.2. |

### `nexus/internal/apps/loanschedule/contract/contract.go`

| where | change |
|---|---|
| `Rounding.Mode` doc | Weak calibration inference replaced by the source argument (`Money.java:52`, `:103`, `:115`, `:160`, `:169`, `:377`, `ProgressiveEMICalculator.java:1761-1766`) — **P1-T29-2**. |
| `GenerateRequest` graded-domain block | `NumberOfRepayments == 1` degenerate note corrected to the related list. |
| `GenerateRequest` pinned inputs | `daysInYearCustomStrategy`'s two effects — **P1-T29-1**. |
| `Period` doc | **New section "RELATED REPAYMENT PERIODS — the normative definition"**; `n` re-defined; steps 1, 3, 6, 7 corrected; consequences seven → eight; "SPECIFIED BUT UNGRADED" widened to items 3/3a/3b/3c. |
| `Period` doc | **New section "The per-period interest computation"** — **P0-T29-2**. |
| `Period.PrincipalMinor`, `Period.InterestMinor` | Both now point at the per-period interest section and say the textbook form is excluded. |

---

## 3. Java `file:line` behind each new normative statement

All read in the pinned checkout `426a23544` (verified `git -C /home/user/fineract rev-parse HEAD`).

**Related repayment periods / `n` (P0-T29-1)**

| statement | citation |
|---|---|
| `n = relatedRepaymentPeriods.size()` | `EmiAdjustment.java:54-56` (`numberOfRelatedPeriods()`), used at `:32` (guard) and `:39` (divisor) |
| the list handed to the loop | `ProgressiveEMICalculator.java:732`, passed at `:749` |
| related = due-date not before the effective due date | `ProgressiveLoanInterestScheduleModel.java:195-197` |
| the `null` branch the old citation pointed at, and why it is unreachable | `ProgressiveLoanInterestScheduleModel.java:191-194`; argument built at `ProgressiveEMICalculator.java:149-151` from `getEffectiveRepaymentDueDate`, which always returns a `LocalDate` |
| the effective due date, incl. the push to the next period | `ProgressiveEMICalculator.java:250-263`, the equality test at `:252`, the push at `:254-258`, the fall-through at `:262` |
| period membership: `[from, due]` first, `(from, due]` later | `ProgressiveLoanInterestScheduleModel.java:238-245`; `LoanRepaymentScheduleProcessingWrapper.java:251-254` |
| level installment computed over / written to the related list only | `ProgressiveEMICalculator.java:741` → `:1722-1741` (start balance at `:1727-1729`, write-back at `:1736-1741`) |
| trial overwrite predicate — related periods only | `ProgressiveEMICalculator.java:1277-1286` |
| `uncountablePeriods` counted over the related list | `ProgressiveEMICalculator.java:2027-2031`, argument at `:1785` |
| adoption test re-measures over the trial model's full list | `ProgressiveEMICalculator.java:1289`, scan at `:1779-1785` |
| degenerate branch | `ProgressiveEMICalculator.java:1788` (`copy(0.0)`), scan bound `idx > 0` at `:1779` |

**Per-period interest (P0-T29-2)**

| statement | citation |
|---|---|
| the three `mc`-qualified operations, in order | `InterestPeriod.java:154-157` (`.multiply(rateFactorTillPeriodDueDate, mc).divide(lengthTillPeriodDueDate, mc).multiply(length, mc)`) |
| exact-zero short circuit | `InterestPeriod.java:146-148` |
| base amount = outstanding balance under declining balance | `InterestPeriod.java:149-152`, `case DECLINING_BALANCE` at `:151` |
| `length` / `lengthTillPeriodDueDate` | `InterestPeriod.java:160-162` / `:164-166` |
| `rateFactorTillPeriodDueDate` computed to the **repayment** period's due date | `ProgressiveEMICalculator.java:641-642` → `:1355-1356` |
| one interest period at creation | `RepaymentPeriod.java:149` |
| split on a balance change; no split when one already ends on `D` | `ProgressiveLoanInterestScheduleModel.java:251-262`, `:264-278` (`:275-277`), `:280-296`, clamp at `:439-442` |
| the amount enters the **later** segment's balance | `InterestPeriod.java:168-188`, `:174` and `:186` |
| sum over interest periods, then one conversion to money, clamped | `RepaymentPeriod.java:252-257`, `:264`; `Money.java:40-53`, `setScale` at `:52` |
| cap at the installment | `RepaymentPeriod.java:272-286`, `MathUtil.min` at `:280` |
| balancing non-negative principal | `RepaymentPeriod.java:345-350` |
| zero-clamped roll-forward | `RepaymentPeriod.java:389-403`, `negativeToZero` at `:399` |
| residual applied after the split | `ProgressiveEMICalculator.java:1160-1219`, `diff` at `:1202-1203`, applied `:1205` |

**P1-T29-1** — `partialPeriodCalculationNeeded`'s third conjunct: `ProgressiveEMICalculator.java:1505-1507`; the suppressed arm `:1526-1531`; the `switch` it falls back to `:1533-1539`, `case ACTUAL` at `:1534-1535`.

**P1-T29-2** — `Money.java:52` (constructor reads only the rounding mode), tenant-global-precision sites `Money.java:103`, `:115`, `:160`, `:169`, `:377`; identity pass `ProgressiveEMICalculator.java:1761-1766`; `MoneyHelper.java:35`.

**P2-T29-1** — T30's re-derivation: `ProgressiveEMICalculator.java:1550-1568` (`calculatePeriodFractions`), `:1969-1980` (`rateFactorByRepaymentPartialPeriod`, no `MathContext`).

---

## 4. Spec-check results

`.softhouse/reviews/t31-probe/t31_spec_check.py`, transcript `t31-output.txt`. Written **from revision 5's own text**, in exact integer minor units; `Decimal` only for the quantities DEC-1 says are not money; **no float literal, type or cast anywhere**. It shares no code with the t26, t28 or t29 probes. Expectations are quoted from `t29_validate.py`, whose provenance is `.softhouse/reviews/t23-probe/` — **not re-taken**.

**(A) 13 / 13 committed observations reproduce, digit-for-digit, with no tolerance** — including Q0b, the later-disbursement shape whose correct handling is what P0-T29-1 is about.

**(B1) the wrong-`n` readings are EXCLUDED, 3 / 3** on T29's cited shapes (schedule start 2024-01-01, disbursement 2024-02-01). Both arms differ from revision 5's text — revision 4's reading in full, and the isolation of `n` alone (T29's experiment A):

| shape | revision 5 | `n` alone (wrong) |
|---|---|---|
| MNT 10,548,069 / 6 × 16.8 % | 2,199,038.75 / 2,199,038.73 | 2,199,038.74 / 2,199,038.77 |
| MNT 1,222,552 / 6 × 18.5 % | 255,934.34 / 255,934.32 | 255,934.33 / 255,934.36 |
| MNT 13,549,647 / 6 × 21.6 % | 2,858,005.77 / 2,858,005.75 | 2,858,005.76 / 2,858,005.79 |

**(B2) the textbook interest reading is EXCLUDED, 3 / 3**:

| shape | revision 5 (three ops) | textbook (one op) |
|---|---|---|
| MNT 13,202 / 6 × 16.8 %, start 2024-01-01 | final 2,309.38, interest 654.38 | 2,309.39 / 654.39 |
| MNT 3,924,149 / 6 × 16.8 %, start 2024-01-31 | final 686,443.28, interest 194,510.78 | 686,443.29 / 194,510.79 |
| MNT 1,814,727 / 6 × 21.6 %, start 2024-01-31 | final 321,792.34, interest 116,027.14 | 321,792.35 / 116,027.15 |

**Every figure in both tables above is a RE-DERIVATION over an uncaptured shape.** None is an oracle observation, none may be promoted to the vector store, and none may be quoted as though observed. They are recorded as *candidate shapes to capture* — §8 items 3b and 3c. Written independently from the revision-5 text alone, they agree digit-for-digit with T29's independent model, which is a re-derivation cross-checking a re-derivation and nothing more.

**(C) control — what the corpus can and cannot see.** `n` alone reproduces **13/13** and the textbook reading reproduces **13/13**, which is exactly why no earlier review caught either P0. Revision 4's reading **in full** reproduces only **12/13** — it fails Q0b, because step 6's "ALL n periods" writes an installment onto the pre-disbursement row that the oracle leaves at zero. So one half of P0-T29-1 was already refuted by a committed observation; that is recorded in §4.3.1 consequence 8.

**Build / vet / gofmt** — `cd nexus && go build ./... && go vet ./... && gofmt -l .`: all clean, no constraint weakened. `go test ./...` unchanged (the contract package still has no test files). Non-negotiable scan: money stays `int64` minor units; the only `float32`/`float64`/`big.Float` tokens in `nexus/` remain inside prose that **prohibits** them (now in three places, all prohibitions); no Oracle Database / MySQL / MariaDB token; no US payment rail or vendor; no `first_name` / `last_name` except where prohibited; no hard-coded zone offset or payment threshold.

---

## 5. No regression of the earlier P0s — confirmed

- **P0-2 (revision 3), deleted ordering clause:** the third clause is **not** reintroduced. It appears only quoted-as-deleted, in the past tense with its attribution, in ADR §4.6 and `Schedule`'s ordering doc. Nothing added by T31 touches the ordering rule.
- **P0-2, disbursement window:** the predicate `ScheduleStartDate ≤ Disbursements[0].Date < the last repayment period's DueDate` is intact and **identical** in ADR §3.1 and `contract.go`'s graded-domain block, with the semantic-not-static note and the `ErrNoDiscriminatingVector` refusal in both. §4.3.1's new related-period block **cites** the window; it does not restate or widen it, and it explicitly routes a disbursement on the last due date back to §3.1/§4.6's refusal rather than answering it.
- **P0-3, `FrequencyYears` and error precedence:** §4.10's conclusion and both sentinels are unchanged; the only edits qualify the *mechanism* by the `daysInYearCustomStrategy` pin and retire a stale evidence caveat. §4.11's three-sentinel precedence is untouched.
- **T28's `NumberOfRepayments < 1 → ErrInvalidRequest`:** stated identically in ADR §3.1 and `contract.go`; unchanged by T31.
- **T28's loop spec and its ~20 `file:line` citations:** preserved. T31 changed **what the loop is parameterised by**, not its steps — the guard's three conjuncts, the closed-form adjustment, the break-on-equal, the strict adoption test with its discarding failure branch, the three-iteration bound and the seven original consequences all stand as T28 wrote them and as T29 verified them.

---

## 6. What still needs a live oracle

Nothing in revision 5 does. What the **corpus** still needs, unchanged in kind from T29's §7 and now bound by §8 items 3–3c:

| # | what it would settle | candidate shape (all `(19, HALF_UP)`, MNT 2 dp, 30/360, monthly, declining balance, no down payment, no installment rounding) |
|---|---|---|
| 3 | trips the EMI re-adjust guard inside the graded domain | MNT 1,014,632 / 6 × 7.0 % or MNT 127,704 / 36 × 16.8 % — already **observed**, ready to promote |
| 3a | separates the adoption test | MNT 100,025 / 12 × 16.8 %, start 2024-01-01 (T26's re-derived candidate) |
| **3b** | separates the per-period interest round-trip | MNT 13,202 / 6 × 16.8 %, start = disbursement 2024-01-01 (re-derived candidate) |
| **3c** | trips the guard in the later-disbursement window | MNT 10,548,069 / 6 × 16.8 %, start 2024-01-01, disbursement 2024-02-01 (re-derived candidate) |
| 3c (second shape) | **a disbursement dated STRICTLY INSIDE a repayment period** — the only in-graded-domain shape producing two non-degenerate interest periods in one repayment period (§4.3.2). No committed observation covers it, and no probe in this program has modelled it | e.g. start 2024-01-01, disbursement 2024-02-15, six monthly periods |
| 5 | `FEB_29_PERIOD_ONLY`'s suppression effect | one one-year ACT/ACT schedule with a 29 February period and one without — deferred with `DayCountActualActual` |

The last row is the one item revision 5 **adds** to the "needs an observation" list rather than inheriting: specifying §4.3.2 correctly made the interest-period segmentation visible, and it exposed a graded-domain shape the corpus has never sampled and no model has exercised. It is specified from source and flagged ungraded in both artefacts.

---

## 7. For the driver

- **Do not ratify on this handoff.** An independent re-review decides; T31 changed no gate disposition and made no ratification claim.
- Both P0s were correctable **without an oracle**, as T29 predicted, and the corrected text now passes the from-text transcription experiment that revision 4 failed — including the discrimination half, which is the part that makes the experiment worth running.
- The vector binding is now four items and still gates **conformance PASS and cutover only**. G-1 and the cutover gate are untouched.
