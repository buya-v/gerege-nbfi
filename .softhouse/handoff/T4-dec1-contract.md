# T4 handoff — DEC-1 revision 2 (attempt 2)

Branch `softhouse/T4-dec1-contract-v3`. Files touched: `docs/adr/DEC-1-schedule-generator-adapter.md`,
`nexus/internal/apps/loanschedule/contract/contract.go`, this handoff. Nothing else.

---

## 1. What changed against attempt 1, in one paragraph

Attempt 1 was rejected for a **structural** reason, not an editorial one: it froze a contract whose input
domain the grading corpus could not test, and said nothing about which inputs those were. Revision 2 makes
that the organising idea. It splits the contract into a **contract domain** (frozen by ratification) and a
**graded domain** (the subset a capture can actually discriminate, which grows with no amendment), refuses
with a new `ErrNoDiscriminatingVector` outside the graded domain, and states discriminability for **every**
input in a table (DEC-1 §5). The structural payoff is §3.2: the two components the capture seam silently
drops — `installmentAmountInMultiplesOf` and `daysInYearCustomStrategy` — are **exactly** the two the graded
domain pins to their inert values, so inside the graded domain the seam's blind spot is empty and a Path-A
capture grades everything the request carries. That is the argument that lets this contract be frozen on a
seam-captured corpus, and it also prices the widening: a non-zero installment multiple requires re-binding
the JVM adapter to the running-server path *and* capturing there.

Beyond that: all nine of T5's required changes are applied (§2), the false round-up rounding rule is
replaced with the true round-to-nearest rule, and every numeric figure is now labelled *observed* (from a
capture I re-read out of `.softhouse/capture/`) or *re-derived* (shown).

---

## 2. T5's nine required changes — disposition, one line each

1. **Precision/scale ambiguity.** `Rounding` now carries `SignificantDigits` **and** `RateFactorScale`, both
   normative, `setScale` site cited (`ProgressiveEMICalculator.java:1959-1962`, `:1976-1979`), constrained
   equal (a differing pair is `ErrUnsupportedConfiguration` since the oracle has one integer); the
   discriminating capture T5 asked for **exists and is quoted observed** — 18 × 18.5 % on 87,654,321 gives
   period-5 principal 4,531,420.25 / total interest 13,393,481.05 at 12 versus 4,531,420.26 /
   13,393,481.04 at 19. `contract.go` `Rounding`; DEC-1 §4.1.
2. **Month-end date rule.** Rewritten as step-then-re-anchor, `min(days in target month, seed day)`, the
   seed being the **disbursement date** (`LoanApplicationTerms.java:583-589`,
   `DefaultScheduledDateGenerator.java:168-176` called at `:128-131`); the rule now lives on
   `Disbursement.Date`, not `ScheduleStartDate`, and is backed by two **observed** captures (seed 2024-01-31
   → 02-29, 03-31, 04-30, 05-31, 06-30, 07-31, term 182; seed 2024-01-30 → …, term 182). DEC-1 §4.2.
3. **Ordering.** Option (a) taken per the ratified answer: reproduce the emitted order. The rule is now a
   **window key** (a disbursement/down-payment row sorts under the due date of the repayment period whose
   half-open `[FromDate, DueDate)` window contains it), derivable from the response itself, and it
   reproduces the **observed** pre-disbursement capture (repayment 1 due 2024-02-01, then the disbursement
   dated 2024-02-01, then repayment 2). `contract.go` `Schedule`; DEC-1 §4.6.
4. **`InstallmentRoundingMultipleMinor` constrained.** Must be 0 or a positive exact multiple of
   10^`MinorUnitDigits`, else `ErrUnsupportedConfiguration`, because the oracle's counterpart is an `Integer`
   count of **major** units (`LoanRepaymentScheduleModelData.java:36`, `Money.java:150-157`, `:163-170`).
   The semantics are also corrected and stated normatively (§3 below). DEC-1 §4.7.
5. **Final-period residual defined.** `lastEmi ← lastEmi + (Σ disbursed + Σ capitalizedIncome +
   creditedPrincipal + Σ dueInterest − Σ installments)`, sums at **currency scale**, delta **signed**
   (observed −0.01 and +0.03), principal then falling out as installment − interest
   (`ProgressiveEMICalculator.java:1160-1219`, `:1202-1205`; `RepaymentPeriod.java:345-350`). "final unpaid
   period" replaced by "the last period". DEC-1 §4.3.
6. **Unreachability grounds corrected.** `allowFullTermForTranche` is recorded as a **real behavioural pin**
   — setter reached at `LoanApplicationTerms.java:606` and copied at `:348`, guard at
   `ProgressiveEMICalculator.java:142-144` never consulting multi-disbursement — with the observed
   `true`/`false` capture pair; `allowPartialPeriodInterestCalculation` is inert **because
   `interestCalculationPeriodMethod` is null on this path**, not because sub-periods coincide. DEC-1 §4.4.
7. **Day-count mapping normative.** `DayCountFixed30Over360 → (DAYS_30, DAYS_360)` and
   `DayCountActualActual → (ACTUAL, ACTUAL)` are stated in both artefacts; `DayCountActualActual` stays in
   the value domain and the computation is refused (`ErrNoDiscriminatingVector`) per the ratified decision 4.
   DEC-1 §4.9.
8. **Adapter obligation widened.** Now covers *every* path that constructs `Money` without an explicit
   `MathContext` (`Money.java:52`, `:102-104`, `:150-157`, `:159-161`, `:163-170`), all of which throw
   outside an initialised tenant (`MoneyHelper.java:74-82`) — and it corrects the WIP's error that the
   tenant *precision* can be pinned: it is the compile-time constant 19 (`MoneyHelper.java:35`), which is
   harmless inside the graded domain on the evidence that the calibration capture ran at threaded precision
   12 under an ambient 19 and still reproduced the shipped literal. DEC-1 §4.1.
9. **The three minor items.** Currency-code case normalisation is now a stated adapter rule (the shipped
   fixture spells `"usd"`, `…GeneratorTest.java:47`); the "money is never re-rounded" claim is **deleted**
   rather than softened (it was true only by accident of the operands); and the no-`double`-in-the-capture-
   harness obligation is recorded on `Disbursement.AmountMinor` and in DEC-1 §8 item 7, citing
   `Money.java:134-148`, `:220-222` and `…GeneratorTest.java:120-122`.

---

## 3. What the two audits changed in this draft, specifically

- **The rounding rule for `installmentAmountInMultiplesOf` is now the TRUE one**: round to the **nearest**
  multiple under the tenant rounding mode (`Money.java:163-170` via
  `ProgressiveEMICalculator.java:1770-1776`), **not** "raise to the next multiple". The observed round-down
  case is carried: principal MNT 1,190,000, multiple 100 → unrounded 111,148.35 → applied **111,100.00**.
  The zero guard (`:1772-1774`) and the EMI re-adjust loop (`:1258-1308`, ≤3 iterations, which can absorb
  the rounding entirely) are both recorded, the loop as explicitly unpinned behaviour with a backlog item.
- **`daysInYearCustomStrategy` is pinned `null` with a proof of inertness** inside the graded domain
  (`:1346-1352` needs a 366-day year, a 360-day year never is; `LoanProduct.java:462-472` enforces ACTUAL at
  product creation), plus the finding that `FULL_LEAP_YEAR` is behaviourally identical to the field being
  unset (`DaysInYearType.java:81-86`) so only `FEB_29_PERIOD_ONLY` discriminates, and only under a daily
  interest calculation.
- **No size threshold.** DEC-1 §4.1 states that precision sensitivity is a rounding-boundary property of
  `(principal, term, rate)` — divergence at principal 4.00, identity at 50,000,000 on the same shape, all
  four MNT captures 12/19-identical — and forbids any implementation shortcut justified by loan size.
- **Corpus honesty.** §5 records that the eleven production-setting captures are *audited observations*, not
  yet vector-store entries (attestation block, three missing per-period columns, run recipe), and that the
  server-path captures ran on a HALF_EVEN tenant and are admissible at `(19, HALF_UP)` only on a fresh-tenant
  re-observation.
- **One new consistency result** I derived and checked against the corpus, because the whole two-binding
  argument rests on it: for **monthly** repayment the oracle's 30/360 arm and its same-as-repayment-period
  arm compute the identical interest fraction (`30k/360 ≡ k/12` at the same precision,
  `:1513-1515` vs `:1536`→`:1922-1927`), which is why a seam capture and a server capture of the same MNT
  1,200,000 / 12 × 21.6 % loan agree to the minor unit. For **weekly** they disagree (`k/52` vs `7k/360`),
  which is one more reason `FrequencyWeeks` is outside the graded domain.

## 4. Things I changed that no review asked for, flagged for the re-reviewer

- **`FrequencyYears` is refused with `ErrUnsupportedConfiguration`,** not `ErrNoDiscriminatingVector`: the
  oracle's per-frequency dispatch throws `UnsupportedOperationException` for it
  (`ProgressiveEMICalculator.java:1602-1610`). Revision 1 admitted a value the oracle cannot answer at all.
- **A third error sentinel**, `ErrNoDiscriminatingVector`, which **wraps** `ErrUnsupportedConfiguration` so
  `errors.Is` still collapses them for a caller that does not care. This is contract surface; it is the
  minimum surface the standing G-1 disposition requires.
- **`Currency.MinorUnitDigits` is pinned to 2 in the graded domain**, because at 0 decimal places a second
  rounding channel switches on inside the oracle (`Money.java:48-51`) that was observed to move money.
- **`DownPaymentPercentage` non-zero is refused.** No capture in the corpus has ever produced a
  down-payment row. Revision 1 did not say so.
- **I did NOT add `InterestCalculationPeriod` / `PartialPeriodInterest` fields**, which the rescued WIP had
  introduced. They are not expressible through the 19-component record the JVM adapter constructs, so
  admitting them would have re-created the exact defect T5's F-3 names: contract surface the adapter
  provably cannot render. `interestCalculationPeriodMethod` is instead recorded as pinned-by-omission
  (DEC-1 §4.4), with the note that exposing it becomes a gate if the adapter is ever re-bound to the server
  path.

## 5. Verification

Go toolchain is not on `PATH` on this host; it is at `~/sdk/go` (`go1.23.4 darwin/arm64`).

```
$ ~/sdk/go/bin/go version
go version go1.23.4 darwin/arm64

$ cd nexus && ~/sdk/go/bin/go build ./...
(no output; exit 0)                                        BUILD PASS

$ cd nexus && ~/sdk/go/bin/go vet ./...
(no output; exit 0)                                        VET PASS

$ cd nexus && ~/sdk/go/bin/gofmt -l .
(no output; exit 0)                                        GOFMT CLEAN
```

Known-bad scan, run over a **comment-stripped** copy of `contract.go` (`/tmp/strip.py` removes `//` and
`/* */` comments while preserving string and rune literals; 96 non-blank lines of executable code remain):

| pattern | result |
|---|---|
| `float32`, `float64`, `big.Float` | CLEAN |
| `first_name`, `last_name`, `firstName`, `lastName` | CLEAN |
| `insur`, `protect`, `guarante` (case-insensitive) | CLEAN |
| `FixedZone`, `time.Time` | CLEAN |
| `+07`, `+08`, `"+…`, `UTC+`, `GMT+` | CLEAN |
| `mysql`, `mariadb`, `ojdbc`, `oracle`, `1521` | CLEAN |
| `stripe`, `plaid` | CLEAN |

`go test ./...` was not run: the module contains no test files, and the contract package is types and doc
comments only — there is nothing to test until an implementation exists.

## 6. Left deliberately for the ratifier

None of these blocks ratification; each is recorded so the ratifier is not surprised.

1. **The graded domain is narrow.** Run-1 implementations will refuse requests they could compute (weekly
   and daily frequencies, `RepaymentEvery > 1`, zero rate, HALF_EVEN, down payments, installment multiples,
   actual/actual). That is the deliberate consequence of the New G-1 disposition and of P-1, and each
   refusal is retired by a capture, not by an amendment. If the ratifier wants a wider launch domain, the
   cost is capture work listed in DEC-1 §8, not a contract change.
2. **The eleven production-setting captures are not yet vector-store entries** (DEC-1 §5, §8 item 1). This
   contract is frozen against *audited observations*. Nothing doubts a number; the admissibility furniture
   is outstanding.
3. **`B-03`/`B-04` (the server-path day-count captures) have never been independently re-derived from
   source** — they run the cross-year partial-period arm. That arm is outside the graded domain, so it does
   not affect this contract, but it is the largest un-re-derived hole in the programme's evidence.
4. **The JVM-adapter binding is a design decision recorded here rather than gated.** Run 1 binds
   `fineract_jvm` to the embeddable seam (DEC-1 §7). Re-binding it to the running server is what a non-zero
   installment multiple needs. If the ratifier considers the binding itself contract-level, say so before
   ratification, because after ratification changing that sentence is an amendment.
5. **`ErrNoDiscriminatingVector` is new contract surface.** It is the smallest expression of "expose,
   specify, refuse" I could find, but it is a third sentinel where revision 1 had two.
