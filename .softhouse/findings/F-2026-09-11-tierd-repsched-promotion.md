# F-2026-09-11 — OH-TDGRADE-BR: fifteen Tier D LoanRepaymentSchedule vectors onto the loan seams; the schedule-family kills deepen, nothing newly dies

**Status: ANSWERED.** `OH-TDGRADE-BR`, worktree `/Users/buv/oh-gerege-tdgrade`, branch
`feat/OHTDGRADEbr`. The whole-file MNT replay of `LoanRepaymentSchedule.feature`
(`F-2026-09-11-tierd-repsched-mnt-uc10.md`, branch `feat/OHTIERD5bp`, worktree
`/Users/buv/oh-gerege-tierd5`) left 11 PASSED read-backs plus UC10's oracle output under
`.softhouse/capture/tierd-feasibility/repayment-schedule-mnt/`. This task promotes **15
vectors** from those committed read-backs onto **existing** loan seams — chiefly
`loan-schedule-amortization` and `loan-schedule-interest`, plus `loan-disbursement`.
No Go change, no new seam, no capture, no container, no replay, no Oracle Database.
Store `.softhouse/vectors/loan/` goes **40 → 55**; the loan harness goes **40/40 → 55/55
PASS**. **No drive newly dies.** Three schedule-family drives deepen (+7/+1/+1).

## 1. Promoted (15 vectors, five commits)

Every cell is a **transcription** of a committed MNT read-back; nothing was computed by the
promotion. An integer suffix is minor units; every seam request/expect is integer-typed.

| vector | seam | capture (sha256) | observed → cells |
| --- | --- | --- | --- |
| `LN-TD-RS-UC1-loan-1-disbursement-net` | `loan-disbursement` | `loan-1-detail-associations-all-1.json` (`e29806a5…`) | `approvedPrincipal 2000.00 → 200000`; `feeChargesAtDisbursementCharged 0.00 → 0`; `netDisbursalAmount 2000.00 → 200000` |
| `LN-TD-RS-UC1-loan-1-schedule-amortizes-to-zero` | `loan-schedule-amortization` | `loan-1-detail-associations-repaymentSchedule-1.json` (`5cb03a1c…`) | `totalPrincipalDisbursed 1000.00 → 100000`; `periods[1..3].principalDue 330.02/333.32/336.66 → 33002/33332/33666`; `sum 100000`; final balance `0.00 → 0` |
| `LN-TD-RS-UC1-loan-1-schedule-interest-period-2` | `loan-schedule-interest` | `loan-1-detail-associations-repaymentSchedule-1.json` (`5cb03a1c…`) | `periods[1].principalLoanBalanceOutstanding 669.98 → 66998`; `annualInterestRate 12.00 → 12`; `daysInYearType.id 360`; `daysInMonthType.id 30`; `periods[1].interestDue 6.70 → 670` |
| `LN-TD-RS-UC3-loan-3-schedule-amortizes-to-zero` | `loan-schedule-amortization` | `loan-3-detail-associations-repaymentSchedule-3.json` (`208baf32…`) | `totalPrincipalDisbursed 1200.00 → 120000`; `principalDue 330.02/432.83/437.15 → 33002/43283/43715`; `sum 120000`; final `0` |
| `LN-TD-RS-UC4-loan-4-schedule-amortizes-to-zero` | `loan-schedule-amortization` | `loan-4-detail-associations-repaymentSchedule-3.json` (`1e978940…`) | `totalPrincipalDisbursed 1200.00 → 120000`; `principalDue 396.62/399.69/403.69 → 39662/39969/40369`; `sum 120000`; final `0` |
| `LN-TD-RS-UC4-loan-4-schedule-interest-period-2` | `loan-schedule-interest` | `loan-4-detail-associations-repaymentSchedule-3.json` (`1e978940…`) | `periods[1].principalLoanBalanceOutstanding 803.38 → 80338`; `12`; `360`/`30`; `interestDue 8.03 → 803` |
| `LN-TD-RS-UC6-loan-6-schedule-amortizes-to-zero` | `loan-schedule-amortization` | `loan-6-detail-associations-repaymentSchedule-3.json` (`4cbb5858…`) | `totalPrincipalDisbursed 1200.00 → 120000`; `principalDue 396.03/399.99/403.98 → 39603/39999/40398`; `sum 120000`; final `0` |
| `LN-TD-RS-UC6-loan-6-schedule-interest-period-2` | `loan-schedule-interest` | `loan-6-detail-associations-repaymentSchedule-3.json` (`4cbb5858…`) | `periods[1].principalLoanBalanceOutstanding 803.97 → 80397`; `12`; `360`/`30`; `interestDue 8.04 → 804` |
| `LN-TD-RS-UC7-loan-7-schedule-amortizes-to-zero` | `loan-schedule-amortization` | `loan-7-detail-associations-repaymentSchedule-3.json` (`7d88124b…`) | `totalPrincipalDisbursed 1200.00 → 120000`; `principalDue 330.02/431.67/438.31 → 33002/43167/43831`; `sum 120000`; final `0` |
| `LN-TD-RS-UC7-loan-7-schedule-interest-period-3` | `loan-schedule-interest` | `loan-7-detail-associations-repaymentSchedule-3.json` (`7d88124b…`) | `periods[2].principalLoanBalanceOutstanding 438.31 → 43831`; `12`; `360`/`30`; `interestDue 4.38 → 438` |
| `LN-TD-RS-UC8-loan-8-schedule-amortizes-to-zero` | `loan-schedule-amortization` | `loan-8-detail-associations-repaymentSchedule-3.json` (`96e35835…`) | `totalPrincipalDisbursed 1200.00 → 120000`; `principalDue 330.02/433.32/436.66 → 33002/43332/43666`; `sum 120000`; final `0` |
| `LN-TD-RS-UC8-loan-8-schedule-interest-period-3` | `loan-schedule-interest` | `loan-8-detail-associations-repaymentSchedule-3.json` (`96e35835…`) | `periods[2].principalLoanBalanceOutstanding 436.66 → 43666`; `12`; `360`/`30`; `interestDue 4.37 → 437` |
| `LN-TD-RS-UC10-loan-10-schedule-amortizes-to-zero` | `loan-schedule-amortization` | `loan-10-detail-associations-repaymentSchedule.json` (`c184624a…`) | `totalPrincipalDisbursed 1200.00 → 120000`; `principalDue 335.50/429.73/434.77 → 33550/42973/43477`; `sum 120000`; final `0` |
| `LN-TD-RS-UC10-loan-10-schedule-interest-period-3` | `loan-schedule-interest` | `loan-10-detail-associations-repaymentSchedule.json` (`c184624a…`) | `periods[2].principalLoanBalanceOutstanding 434.77 → 43477`; `12`; `360`/`30`; `interestDue 4.35 → 435` |
| `LN-TD-RS-UC12-loan-12-schedule-interest-period-2` | `loan-schedule-interest` | `loan-12-detail-associations-repaymentSchedule-2.json` (`c68c910d…`) | `summary.principalOutstanding 869.98 → 86998`; `12`; `360`/`30`; `periods[1].interestDue 8.70 → 870` |

Provenance follows `F-2026-09-11-tierd-mnt-uc6-promotion-bo.md` exactly: `capture_ref` is a
JSON record path, `capture_sha256` is the on-disk SHA-256 (re-verified after writing for all
15; see §5), `capture_case_id` is the loan's observed `externalId`, `tenant_params.currency`
is the capture's `currency.code = "MNT"`, `decimalPlaces = 2`, tenant `tierd`, image
`sha256:e596339626bf…`, `Asia/Ulaanbaatar`, rounding mode 4 (HALF_UP), instance destroyed.

### One vector per distinct scenario shape

The 12 loans collapse to **8 distinct shapes**; where two loans are the same shape only one
representative is promoted (per the brief), not one vector per loan:

| shape | representative(s) | products/behaviour | promoted |
| --- | --- | --- | --- |
| single disbursement 1000, 3 periods | loan 1 | `…EMI_360_30…` | UC1 (amort, interest, disb) |
| two tranches, 2nd **on** the first due date | loan 3; loan 2 ≡ | NO_RECALC + NO_PARTIAL | UC3 amort |
| two tranches, 2nd **mid**-period, daily recalc + partial | loan 4; loan 5 ≡ | INT_RECALC_DAILY + PARTIAL | UC4 (amort, interest) |
| two tranches, 2nd **mid**-period, no recalc, no partial | loan 6 | NO_RECALC + NO_PARTIAL | UC6 (amort, interest) |
| two tranches, mid-period | loan 7; loan 9 ≡; loan 8 ≡ | … | UC7 (amort, interest) |
| two tranches, mid-period | loan 8 | … | UC8 (amort, interest) |
| multi-disbursement (3 tranches), one-unit-off build | loan 10 | MNT multi-disbursement | UC10 (amort, interest) |
| two tranches, mid-period, p1 early-repaid | loan 12 (amort ≡ loan 3) | NO_RECALC + NO_PARTIAL | UC12 interest |

Loans 2, 5 and 9 reproduce promoted schedules (`loan 2 ≡ loan 3`, `loan 5 ≡ loan 4`,
`loan 9 ≡ loan 7/8`); loan 12's amortization shape equals loan 3's, so only its interest
shape is new. Duplicates were not registered.

## 2. Drive measurement — every loan drive, WITHOUT and WITH

**Instrument.** `bash .softhouse/briefs/tools/redcount.sh "$PWD" loan` reports **46**
registered `loan-wrong-*` drives, and agrees with the 46-row appendix. The denominator was
controlled with `capcount.sh "$PWD" loanschedule loanschedule-wrong-days-in-year-365 = 48`
(non-zero, as required). Each of the 46 drives was run against the store with the 15 new
vectors moved aside (**WITHOUT**, 40 vectors) and with them in place (**WITH**, 55 vectors),
using `capcount.sh "$PWD" loan <impl>`. The two runs were byte-compared first; only the three
rows below differ.

**Result: no drive newly dies.** All 46 drives were already red WITHOUT and stayed red WITH:
no drive appears only once the new vectors were added, and no count moved from zero to non-zero.
Exactly three counts moved, all in the amortization family:

| drive | WITHOUT | WITH | delta |
| --- | ---: | ---: | ---: |
| `loan-wrong-schedule-amortization-drops-final-component` | 3 | 10 | +7 |
| `loan-wrong-schedule-amortization-uniform-rounded-up` | 3 | 4 | +1 |
| `loan-wrong-schedule-amortization-uniform-truncated` | 3 | 4 | +1 |

The other 43 drives are byte-identical (appendix). The +7 is the **seven promoted whole-schedule
amortization vectors** (UC1 loan 1, UC3 loan 3, UC4 loan 4, UC6 loan 6, UC7 loan 7, UC8 loan 8,
UC10 loan 10): each is a new observation on the same seam, each killing the three
amortization drives — the drops-final drive by all seven, the two uniform drives by those
schedules whose components are not a uniform split. The prior store already carried three
amortization observations; the family now holds ten. **No new drive dies, and no previously-live
drive dies.**

### Cross-validation that kills nothing new — stated plainly

* The seven `loan-schedule-interest` vectors did **not** move a single count. The only
  schedule-interest drive is `loan-wrong-half-even-schedule-interest` (1 kill), and it keys on
  the pinned SEED-L06 tie; none of the seven observed interests is a HALF_UP/HALF_EVEN tie at
  the 2-dp boundary (e.g. 803.38·12·30/(100·360) = 8.0338). They corroborate the interest cell
  without adding a kill.
* The `loan-disbursement` vector did **not** move a count because the seam has **zero registered
  drives**. Adding vectors there is corroboration only.
* These two groups are correct as **cross-validation**: fixed observations that pin a mapped
  cell without manufacturing a kill. No drive was registered to dress them up.

## 3. UC10 — the oracle's output is the observation; the feature table is not

UC10 loan 10's read-back was **not** among the 11 PASSED read-backs. It was extracted from the
MNT replay log with `.softhouse/capture/tierd-feasibility/bin/extract.py` and committed under
`loans/loan-10/loan-10-detail-associations-repaymentSchedule.json`
(`sha256 c184624a8790ea943492f3a7bbeef3ee17586e5a580a15288f24f0adeb62c35a`, `bytes 13568`,
`source_line 36444`), with its `manifest-repsched.json` line flipped to `committed: true` and
its `manifest-repsched-passed.json` line added. Both manifest edits are exactly that line,
nothing else. The two UC10 vectors pin the **oracle's** schedule:

* amortization `principalDue 335.50 / 429.73 / 434.77` — the disputed period-2 split is the
  oracle's **429.73**, not the feature table's 429.74;
* interest period 3 `4.35` — accrues on the constant observed balance 434.77.

UC10 is the scenario whose pinned build returns a period-2 split one minor unit off its own
feature table (`F-2026-09-11-tierd-repsched-mnt-uc10.md`): the feature expects principal 429.74
/ interest 11.28 / balance 434.76, the oracle read back 429.73 / 11.29 / 434.77. Per the brief
the oracle's output **is** the observation, so the vector transcribes 42973. The feature-table
values were not used.

## 4. Refusals and limitations — recorded, never relaxed

* **A period whose interval straddles a disbursement is REFUSED on `loan-schedule-interest`.**
  Its observed `interestDue` is a blend of two outstanding principals and is not the seam's
  single-principal 360/30 formula. Refused: UC4 p1 (11.10), UC6 p1 (12.00 — equal to the
  formula on 1200.00 but the period's principal is not constant, a coincidental blend), UC7 p2
  (9.35), UC8 p2 (7.70), UC10 p1 (4.52 — partial-period accrual), and **UC10 p2 (11.29 — the
  disputed one-unit-off blend)**. Only a period whose accrual principal is observed and constant
  is transcribed. Rule kept, not relaxed.
* **`principal_minor` must be an observed field of the cited capture; it is never computed.**
  UC3 loan 3's period-2 interest `8.70` is arithmetically consistent with 869.98
  (= observed 669.98 + observed 200.00 tranche), but loan 3's read-back exposes **neither**
  869.98 as a field — `summary.principalOutstanding` is 1200.00 and the schedule rows carry
  669.98 and a 200.00 disbursement row, not their sum. Computing the sum would violate
  transcribe-only-observed, so the candidate is **REFUSED**. The same shape's interest is
  promoted from loan 12, where 869.98 **is** observed (`summary.principalOutstanding`, and
  `transactions[46].outstandingLoanBalance` in the same loan's `associations=all` read). This
  is the one refusal that cost a planned vector; it is recorded rather than worked around.
* **The interest vectors do not discriminate the rounding mode.** None of the seven observed
  interests is a HALF_UP/HALF_EVEN tie; the 360/30 formula lands strictly inside a cent. The
  tie evidence remains the pinned LN-L06 cell. Recorded so these are not mistaken for rounding
  coverage.
* **The disbursement seam has no drive, and this capture cannot grade the subtraction.**
  `feeChargesAtDisbursementCharged = 0`, so `net = approved − charges` and `net = approved` are
  indistinguishable. A discriminating vector would need nonzero charges due at disbursement;
  none is observed. Recorded, not synthesised.
* **`loan-schedule-amortization` carries one `principal_disbursed_minor` scalar.** The
  multi-tranche structure (loan 10's 300/200/500, loan 3/4/6/7/8's 1000/200) is not
  representable; the vector is admitted on the whole-schedule property the seam does grade —
  components sum to the observed `totalPrincipalDisbursed` and the final balance is zero — and
  the tranche split stays ungraded context. Rule: admit the observed scalar the seam carries;
  do not synthesise structure the seam lacks.
* **Disbursement and period-0 rows carry no `principalDue`.** They are excluded as components,
  exactly as period 0 is excluded on the single-disbursement captures. The component sum
  transcribed equals `totalPrincipalDisbursed` to the unit.

## 5. Verification, bar, scope, and isolation

**Re-verification after writing.** A checker re-read all 15 vectors and, for each, re-hashed the
on-disk capture and compared it to `capture_sha256`, checked `externalId == capture_case_id`,
checked `currency.code == tenant_params.currency`, and re-derived every transcribed cell from
the capture: **0 bad**. The disbursement capture was additionally checked by hand
(`approvedPrincipal 2000.00`, `feeChargesAtDisbursementCharged 0.00`, `netDisbursalAmount
2000.00`, `currency MNT`).

**Harness.** `go run ./internal/apps/loan/conformance/cmd/conformance -root "$PWD"`:

```
VERDICT: PASS (exit 0)
vectors_loaded=55 parity_pass=55 parity_fail=0 refused=0 inadmissible=0 harness_error=0
graded_cells=250 money_cells=100 invariant_violations=0
nofloat: packages=48 files=386 tokens=398547 imports=1155 violations=0
```

The new vectors are genuinely graded, not merely loaded: with the 15 moved aside the same
harness reports `vectors_loaded=40 graded_cells=228 money_cells=78`; with them in place,
`55 / 250 / 100` — a delta of **+15 vectors, +22 graded cells, +22 money cells**.

**Bar.** `bash .softhouse/conformance.sh` — exit **2 only** with
`§4.4.2-RECORDED-DECISION-EXIT`, oracle probe up, ledger findings == baseline; no `HARD guard
failed`. The driver owns the push; this run never exercised the push gate.

Scope held: **no Go source change** (only JSON vectors, the extracted UC10 read-back, and its
two manifest lines), **no new seam**, one bounded context (`loan`), PostgreSQL only (no Oracle
Database anywhere). `.softhouse/guards/` (baseline 8 pairs), `.softhouse/conformance.sh`,
`.softhouse/maps/` and all other capture files are untouched. No container was started and no
replay was run. `TASK.md` is never committed.

## 6. What this establishes

The committed MNT read-backs of `LoanRepaymentSchedule.feature` yield 15 faithful vectors with
no recomputation. The measurement is unambiguous: they **extend coverage, not kills**. Seven
new whole-schedule amortization observations deepen the three schedule-amortization drives
(+7/+1/+1); seven interest observations and one disbursement observation are cross-validation
on seams with no distinguishing drive (or no drive at all), with each limitation stated. The
UC10 vector pins the oracle's one-unit-off output, not the feature table. The one candidate the
capture could not ground without computing — loan 3's period-2 interest — is **refused** and
the rule recorded. Where the capture cannot discriminate, that is a limitation, not a licence.

## Appendix — every loan drive, WITHOUT and WITH

`WITHOUT` = 40-vector store; `WITH` = 55-vector store. 43 rows are byte-identical; the three
`+` rows are §2.

| drive | WITHOUT | WITH | delta |
| --- | ---: | ---: | ---: |
| `loan-wrong-allocation-drops-fee` | 1 | 1 | +0 |
| `loan-wrong-allocation-drops-penalty` | 1 | 1 | +0 |
| `loan-wrong-charge-outstanding-ignores-waived` | 1 | 1 | +0 |
| `loan-wrong-charge-partial-marks-paid` | 1 | 1 | +0 |
| `loan-wrong-charge-waiver-counts-as-paid` | 1 | 1 | +0 |
| `loan-wrong-charge-waiver-leaves-outstanding` | 1 | 1 | +0 |
| `loan-wrong-delinquency-absent-nonzero` | 1 | 1 | +0 |
| `loan-wrong-delinquency-thirty-day-month` | 3 | 3 | +0 |
| `loan-wrong-half-even-schedule-interest` | 1 | 1 | +0 |
| `loan-wrong-journal-entry-batch-collapses-credits-to-one-account` | 3 | 3 | +0 |
| `loan-wrong-journal-entry-batch-debit-from-first-two-credits` | 1 | 1 | +0 |
| `loan-wrong-journal-entry-batch-drops-fee-pair` | 4 | 4 | +0 |
| `loan-wrong-journal-entry-batch-first-pair-only` | 1 | 1 | +0 |
| `loan-wrong-journal-entry-batch-maps-fee-to-disbursement-accounts` | 1 | 1 | +0 |
| `loan-wrong-journal-entry-batch-nets-account` | 1 | 1 | +0 |
| `loan-wrong-journal-entry-batch-pairs-legs-two-at-a-time` | 1 | 1 | +0 |
| `loan-wrong-journal-entry-batch-routes-accrual-income-to-one-account` | 2 | 2 | +0 |
| `loan-wrong-journal-entry-batch-swaps-first-pair-sides` | 4 | 4 | +0 |
| `loan-wrong-repayment-omits-principal` | 2 | 2 | +0 |
| `loan-wrong-reversal-business-date` | 1 | 1 | +0 |
| `loan-wrong-reversal-duplicates-instead-of-reverses` | 1 | 1 | +0 |
| `loan-wrong-reversal-flags-originals` | 1 | 1 | +0 |
| `loan-wrong-reversal-fresh-transaction-id` | 1 | 1 | +0 |
| `loan-wrong-schedule-amortization-drops-final-component` | 3 | 10 | **+7** |
| `loan-wrong-schedule-amortization-uniform-rounded-up` | 3 | 4 | **+1** |
| `loan-wrong-schedule-amortization-uniform-truncated` | 3 | 4 | **+1** |
| `loan-wrong-status-iota-ordinal` | 2 | 2 | +0 |
| `loan-wrong-status-transition-approve-skips-to-active` | 1 | 1 | +0 |
| `loan-wrong-status-transition-ignores-repaid-in-full` | 1 | 1 | +0 |
| `loan-wrong-status-transition-writeoff-closes-obligations-met` | 1 | 1 | +0 |
| `loan-wrong-summary-drops-fee` | 1 | 1 | +0 |
| `loan-wrong-summary-drops-penalty` | 2 | 2 | +0 |
| `loan-wrong-summary-drops-principal` | 7 | 7 | +0 |
| `loan-wrong-summary-interest-not-outstanding` | 6 | 6 | +0 |
| `loan-wrong-transaction-balance-accrual-zero` | 2 | 2 | +0 |
| `loan-wrong-transaction-balance-folds-repayment-interest` | 1 | 1 | +0 |
| `loan-wrong-transaction-balance-waiver-moves-principal` | 1 | 1 | +0 |
| `loan-wrong-writeoff-drops-fee` | 2 | 2 | +0 |
| `loan-wrong-writeoff-drops-penalty` | 2 | 2 | +0 |
| `loan-wrong-writeoff-journal-debits-loan-portfolio` | 2 | 2 | +0 |
| `loan-wrong-writeoff-journal-debits-principal-only` | 2 | 2 | +0 |
| `loan-wrong-writeoff-journal-one-debit-per-portion` | 2 | 2 | +0 |
| `loan-wrong-writeoff-journal-swaps-fee-and-penalty` | 2 | 2 | +0 |
| `loan-wrong-writeoff-principal-and-interest` | 2 | 2 | +0 |
| `loan-wrong-writeoff-principal-only` | 2 | 2 | +0 |
| `loan-wrong-writeoff-swaps-fee-and-penalty` | 2 | 2 | +0 |
