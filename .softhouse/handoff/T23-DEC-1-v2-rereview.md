# T23 handoff — independent re-review of DEC-1 revision 2

**Verdict: ACCEPTED WITH REQUIRED CHANGES. NOT ratifiable as it stands under P-2.**
Full review: `.softhouse/reviews/T23-DEC-1-v2-rereview.md`.

Three P0s block the freeze. None requires a rewrite; each is a localised normative paragraph.
Revision 2's structure, its two-domain split, its money math and its Go artefact are sound.

---

## What I checked, and how

### Re-derived rather than read
Wrote a from-scratch re-derivation of the progressive algorithm from the pinned source
(`.softhouse/reviews/t23-probe/t23_rederive.py`), deliberately **not** reusing
`.softhouse/capture/out/t21-probe-rederive.py`. It reproduces **8 of the 12 pass-3 captures** —
`P-00`, `P-01`, `P-02`, `P-02b`, `P-MNT-5M`, `P-MNT-1M2`, `P-MNT-50M`, `P-MNT-4M999` — every date,
principal, interest, balance, total and term, **to the minor unit**. That is the positive evidence
that DEC-1's specification of the algorithm is correct and implementable from the document alone.

### Observed rather than argued
Ran two new probes against the pinned oracle through the Path-A seam, in the pinned image
(digest verified; seam class `diff`-verified byte-identical), at `(19, HALF_UP)` with tenant rounding
mode 4:

- `T23Probe.java` — disbursement-window boundaries, `FrequencyYears` on both day-count arms,
  small-principal long-term shapes, plus two controls reproducing the ordinary and the
  disbursement-on-a-due-date cases.
- `T23Probe2.java` — the ten EMI-re-adjust candidates.

Raw outputs are committed alongside. Reproduction: the `docker run` recipe in
`.softhouse/capture/README-pass2.md`, substituting the probe class.

### Mechanically verified rather than sampled
- **Builder-drop hunt.** Extracted all 37 `private` fields of `LoanApplicationTerms.Builder`
  (`:353-577`) and all 36 `builder.X` reads in the private copy constructor (`:304-351`) and diffed
  them. Exactly one field is never copied: `daysInYearCustomStrategy`. Separately walked all 19
  components of `LoanRepaymentScheduleModelData` (`:32-39`) against `assembleFrom` (`:579-607`):
  exactly one is never mentioned, `installmentAmountInMultiplesOf`. **There is no third dropped
  component of that class.** The author's pair claim is exact.
- **Citation audit.** 157 occurrences, 101 distinct `(file, range)` pairs, 13 files; **all 101
  resolve**; ~55 load-bearing ranges opened and read; **zero progressive-vs-cumulative
  misattributions** (no cumulative-generator file is cited at all, and each of the seven cited files
  outside `fineract-progressive-loan/` is genuinely on the progressive path).
- **Go artefact.** `go build ./...`, `go vet ./...`, `gofmt -l .`, `go test ./...` all clean
  (Go at `/Users/buv/sdk/go`, not on `PATH`). Comment-stripped known-bad scan over the 703 executable
  lines: no `float32`/`float64`/`big.Float`, no `first_name`/`last_name`, no
  insured/protected/guaranteed, no `FixedZone`, no `+07`/`+08` literal, no MySQL/MariaDB/Oracle
  token. Money is `int64` minor units throughout; rates are exact `int64` rationals; dates are civil
  + IANA zone name. Ran a temporary probe test to execute the error taxonomy: the `errors.Is`
  wrapping is exactly as specified (collapsible one way, distinguishable the other); test file removed
  before commit.

---

## The three P0s, in one line each

1. **P0-1 — the EMI re-adjust loop is live inside the graded domain.** DEC-1 §4.3 says it "is
   reachable only outside the graded domain" and §9's Go-module obligation list omits it. It is called
   on every generation (`ProgressiveEMICalculator.java:749`); its guard
   (`EmiAdjustment.java:31-36`) compares `|lastEMI − penultimateEMI| × 100` against a `Money` of
   amount `floor(n/2)` — `Money.copy(double)` (`Money.java:220-222`) **replaces** the amount rather
   than scaling it — so it has no dependence on `InstallmentRoundingMultipleMinor`. **Observed: 7 of
   10 graded-domain requests diverge** from a no-loop derivation. Example: MNT 1,014,632 / 6 × 7.0 %
   → oracle EMI 172,574.64, specification-as-written 172,574.63; MNT 127,704 / 36 × 16.8 % → total
   interest 35,746.56 vs 35,746.69.

2. **P0-2 — a graded-domain disbursement outside `[ScheduleStartDate, last due date)` is silently
   discarded.** Observed: disbursement on 2024-07-01 (the last due date), on 2024-09-01, or on
   2023-11-15 all yield **zero disbursement rows** and an all-zero schedule
   (`ProgressiveLoanScheduleGenerator.java:305-308` with `isMultiDisburseLoan() == false`, since
   `multiDisburseLoan` is only ever set positionally at `LoanApplicationTerms.java:812`). The
   `Schedule` ordering rule's clause "if the row's date is on or after the last repayment period's
   `DueDate`, its key sorts after every repayment row" describes a row this seam never emits.

3. **P0-3 — `FrequencyYears` does not always throw.** Observed: it throws on the 30/360 arm
   (`:1536` → `:1602-1610`) but returns a complete 3-period schedule under `DayCountActualActual`,
   because the `ACTUAL` arm at `:1534-1535` never reaches the frequency dispatch. The normative
   sentence "the oracle cannot answer it at all" is false, and the contract has no **error-precedence
   rule** for a request refusable for two reasons.

P1s (seven of them) are listed in §10 of the review; none blocks the freeze.

---

## What I could not settle, and what settling it needs

1. **Whether P0-1 and P0-2 are the last two graded-domain holes.** I found both by targeted probing,
   not by exhaustion. The `36 × 16.8 %` shape shows precision divergence at principal 4 and none at
   50,000,000, so the input space is not smooth and sampling gives weak coverage guarantees.
   **Settling it needs:** a differential campaign — the Go module (or an independent model) against
   the oracle over a randomised sweep of the graded domain, with every mismatch triaged. That is
   properly Tier-0 harness work (T7/T10), not contract work, but it should be scheduled before anyone
   claims the graded domain is graded.

2. **Whether the EMI re-adjust loop can be reproduced without a float in Go.** I believe yes — the
   only `double`s carry exact small integers (`Math.floor(n/2.0)`, `Money.copy(0.0)`) — but I did not
   prove it across the loop's three iterations, `EmiAdjustment.adjustment()`
   (`emiDifference.dividedBy(Math.max(1, n − uncountable))`, a `long` divide under the tenant
   `MathContext`) and `getUncountablePeriods`. **Settling it needs:** a line-by-line re-derivation of
   `ProgressiveEMICalculator.java:1258-1308` plus `EmiAdjustment.java` and
   `getUncountablePeriods`, and vectors that force at least two iterations. Candidates from my scan:
   MNT 40,595 / 36 × 16.8 % and MNT 127,704 / 36 × 16.8 %, whose post-loop gaps still exceed the
   guard threshold.

3. **`DayCountActualActual` and the cross-year partial-period arm.** Still un-re-derived by anyone in
   this program (ADR §8 item 5 says so). My re-derivation covers only the 30/360 arm. This is also
   what decides whether `daysInYearCustomStrategy` needs a contract field, which the ADR correctly
   calls an amendment. **Settling it needs:** an independent source re-derivation of
   `ProgressiveEMICalculator.java:1505-1507` / `:1526-1531` / `calculatePeriodFractions` `:1550-1568`,
   and captures spanning a calendar-year boundary under ACTUAL/ACTUAL — including the
   `FEB_29_PERIOD_ONLY` variant, which through the *seam* is inert but through a *server* is not.

4. **Whether Path-B products set `allowPartialPeriodInterestCalculation = true`.** On the server path
   `interestCalculationPeriodMethod` is non-null, which un-short-circuits
   `ProgressiveEMICalculator.java:128-133`; the branch stays inert only if that flag is also `true`.
   Nobody has recorded what the four Path-B products set. **Settling it needs:** one read of
   `m_product_loan` on the running instance, recorded in `REPRODUCE.md`'s precondition block. Cheap,
   and it gates whether Path-B captures are comparable with Path-A vectors at all.

5. **Whether the twelve captures are promotable as they stand.** ADR §5 discloses that they are
   audited observations, not vector-store entries: the attestation block, three per-period columns
   (`fromDate`, fee, penalty) and a committed run recipe are outstanding. I did not audit
   promotability — that is ADR §8 items 1 and 2. Nothing I saw casts doubt on any number.

6. **The correctness of `.softhouse/capture/out/t21-probe-rederive.py:165`'s `EmiAdjustment` guard is
   settled — it is wrong**, and any downstream claim resting on it should be re-checked. It models
   the threshold as `originalEmi × floor(n/2)` where the oracle uses `Money(floor(n/2))`, an error of
   roughly five orders of magnitude on an MNT loan. It does **not** invalidate the twelve captures
   (those are oracle output, and my independent model reproduces eight of them exactly); it
   invalidates only the model's `emi_adjust_triggered` column.

---

## Suggested routing

- **T4 (author)** takes P0-1, P0-2, P0-3 and the seven P1s. All are edits to prose and doc comments;
  no type changes, so no shape churn and no re-capture.
- **Re-review** should be scoped narrowly to the three P0s plus P1-3 (the graded-domain widening
  mechanism). Everything else in this review is verified and need not be re-litigated.
- **Do not ratify DEC-1 until P0-1 is fixed.** It is the one finding that would let a conforming Go
  port misprice ordinary Mongolian retail loans while passing the whole corpus.
- No `user` gate is raised by this review. No cutover is proposed, no deposit-taking is implicated,
  no licence fact is asserted, no ratified DEC-n is amended.

---

## Artefacts

`.softhouse/reviews/T23-DEC-1-v2-rereview.md` — the review.
`.softhouse/reviews/t23-probe/` — `T23Probe.java`, `T23Probe2.java`, their raw outputs,
`t23_rederive.py`, `t23_scan_readjust.py`, `t23_compare.py`, and the `diff`-verified seam copy.
