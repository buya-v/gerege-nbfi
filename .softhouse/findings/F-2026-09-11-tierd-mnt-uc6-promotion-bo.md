# F-2026-09-11 — OH-TDMNT-BO: three more Tier D vectors from the committed UC6 MNT capture; none newly dies

**Status: ANSWERED.** `OH-TDMNT-BO`, worktree `/Users/buv/oh-gerege-tdmnt`, branch
`feat/OHTDMNTbo`. `OH-TIERD4-BM` (`F-2026-09-11-tierd-mnt-uc6-promotion.md`) admitted the
first Tier D vector from the MNT UC6 replay; this task admits three more from the same
committed read-backs, on **existing** loan seams. No Go change, no new seam. Store
`.softhouse/vectors/loan/` goes 32 → 35; the loan harness goes 35/35 PASS. The two loan-1
candidates are **inert cross-validation** vectors; the loan-10 candidate deepens the three
schedule-amortization kills. **No drive newly dies.**

## 1. Promoted (three vectors, three commits, plus one provenance fix)

| vector | seam | capture (sha256) | observed → cells |
| --- | --- | --- | --- |
| `LN-TD-L06-loan-1-schedule-interest-period-1` | `loan-schedule-interest` | `loan-1-detail-associations-all-1.json` (`cc82ab65…233f7`) | `principal 1000.000000 → "100000"`; `annualInterestRate 7.000000 → 7`; `.daysInYearType.id 360`; `.daysInMonthType.id 30`; `periods[1].interestOriginalDue 5.830000 → "583"` |
| `LN-TD-L06-loan-1-disbursement-net` | `loan-disbursement` | `loan-1-detail-associations-all-1.json` (`cc82ab65…233f7`) | `approvedPrincipal 1000.000000 → "100000"`; `feeChargesAtDisbursementCharged 0.000000 → "0"`; `netDisbursalAmount 1000.000000 → "100000"` |
| `LN-TD-L10-loan-10-multi-disbursement-amortizes-to-zero` | `loan-schedule-amortization` | `loan-10-detail-associations-repaymentSchedule.json` (`3c33a473…2553b`) | `repaymentSchedule.totalPrincipalDisbursed 1000.000000 → "100000"`; six repayment `principalDue 169.90/170.05/170.05/170.05/170.05/149.90 → 16990/17005/17005/17005/17005/14990`; `sum "100000"`; final `principalLoanBalanceOutstanding 0.000000 → "0"` |

Every cell is a **transcription** of the committed MNT read-back; nothing was computed by the
promotion. `capture_ref` is a JSON record path, `capture_sha256` was re-verified against the
on-disk artefact for all three captures, and `capture_case_id` is the loan's observed
`externalId` (`fe61fc1a-…` for loan 1, `c4ee58dc-…` for loan 10). All read-backs carry
`currency.code = "MNT"`, `decimalPlaces = 2`; tenant `tierd`, image
`sha256:e596339626bf…`, `Asia/Ulaanbaatar`, rounding mode 4. The 32-vector store already
carried `LN-TD-L10-loan-1-pending-amortizes-to-zero`, so these three were added on top.

Commits on `feat/OHTDMNTbo`:

```
2b99836a  vectors(tierd): loan 1 period-1 schedule interest from the MNT UC6 replay
a4329f26  vectors(tierd): loan 1 net disbursal amount from the MNT UC6 replay
5af3ed41  vectors(tierd): loan 10 multi-disbursement schedule amortizes to zero
8e2da982  vectors(tierd): cite the loan-level day-convention path correctly
```

The last commit fixes a provenance pointer only: the MNT read-back carries the day
conventions at the loan's top level (`.daysInYearType.id = 360`,
`.daysInMonthType.id = 30`); `.terms.daysInYearType` is null. The values were already
observed and correct, only the JSON pointer in `_note`/`citation` was wrong. Loan harness
unchanged at 35/35.

## 2. Drive measurement — every loan drive, WITHOUT and WITH

**Instrument.** `redcount.sh` counts the registered `loan-wrong-*` drives from the binary's
own `-list-implementations`; it reports **43** for `loan` and agrees with the 43-row
measurement below. The denominator was controlled with `capcount.sh … loanschedule-wrong-days-in-year-365 = 48` (non-zero, as required). Each drive was then run against the store with the three
new vectors moved aside (**WITHOUT**, 32 vectors) and with them in place (**WITH**, 35
vectors).

**Result: no drive newly dies.** All 43 drives were already red in the WITHOUT run and stayed
red in the WITH run: no drive appeared only once the new vectors were added, and no count went
from zero kills to non-zero. Exactly three counts moved, all in one family:

| drive | WITHOUT | WITH | delta |
| --- | ---: | ---: | ---: |
| `loan-wrong-schedule-amortization-drops-final-component` | 2 | 3 | +1 |
| `loan-wrong-schedule-amortization-uniform-rounded-up` | 2 | 3 | +1 |
| `loan-wrong-schedule-amortization-uniform-truncated` | 2 | 3 | +1 |

The other 40 drives are byte-identical (see the appendix). The delta is the loan-10
multi-disbursement vector: it is a third distinct observation on `loan-schedule-amortization`
(after `LN-L10` loan 5 and `LN-TD-L10` loan 1), so it kills the same three amortization drives
a third time. **No new drive dies, and no previously-live drive dies.**

### The two loan-1 vectors are cross-validation vectors

Neither loan-1 vector changed a single count:

* `LN-TD-L06-loan-1-disbursement-net` — the `loan-disbursement` seam has **zero registered
  drives** (no `loan-wrong-disbursement-*` exists). A new vector on it cannot kill anything.
* `LN-TD-L06-loan-1-schedule-interest-period-1` — the only schedule-interest drive is
  `loan-wrong-half-even-schedule-interest` (1 kill), and it keys on the SEED-L06 tie
  (100050.50 at 12%, 1000.505). Loan 1's observed 5.83 is a **non-tie** (100000·7·30 /
  (100·360) = 583.33), so the vector corroborates the interest cell but cannot move a
  rounding-mode drive.

Both are therefore correct as **cross-validation**: fixed observations that pin the mapped
cell without adding a kill. That is stated plainly rather than dressed up as a kill.

## 3. Refusals and limitations — recorded, never relaxed

* **The pilot's `tenant_params` equality rule stands.** `F-2026-09-11-tierd-pilot-loan-refusal.md`
  refused these candidates because their `tenant_params.currency` was EUR against the MNT pin.
  The 2026-09-11 driver decision re-seeded the disposable oracle to MNT and replayed; these are
  **re-observations under the new tenant**, `tenant_params.currency = "MNT"` read from the
  capture. The rule — a vector whose `tenant_params` disagree with the pin is refused — is
  upheld, not overridden.
* **A seam with no drive is a cross-validation surface, not a kill.** `loan-disbursement` is in
  the graded domain and now carries two parity vectors, but no wrong implementation exists to
  kill. Consequence recorded: adding vectors there is corroboration only.
* **A zero-charge observation cannot grade the subtraction.** Both disbursement captures have
  `feeChargesAtDisbursementCharged = 0`, so `net = approved − charges` and `net = approved` are
  indistinguishable. A discriminating vector would need a capture with **nonzero** charges due
  at disbursement; UC6 loan 1 does not observe one. We record this rather than synthesise a
  charge to create a kill.
* **The interest vector does not discriminate the rounding mode.** 583 is not a HALF_UP /
  HALF_EVEN tie. The tie evidence remains SEED-L06's 1000.505. Recorded so the vector is not
  mistaken for rounding coverage.
* **The amortization seam cannot represent the multi-tranche disbursement structure.** Its
  request carries a single `principal_disbursed_minor` scalar plus a component list; loan 10's
  three tranches (300/200/500) are not representable. The vector is admitted on the
  **whole-schedule** property the seam does grade — components sum to the observed
  `totalPrincipalDisbursed` and the final balance is zero — and the tranche split is ungraded
  context. Rule: admit the observed scalar the seam carries; do not synthesise per-tranche
  structure the seam lacks.
* **Disbursement/period-0 rows carry no `principalDue`.** Loan 10's `periods[0..2]` are the
  three disbursement rows and are excluded as components, exactly as period 0 is excluded on
  the single-disbursement captures; the six components are `periods[3..8].principalDue`. Their
  sum is transcribed as 100000, equal to `totalPrincipalDisbursed`.

## 4. Bar, scope, and isolation

`bash .softhouse/conformance.sh` — **exit 2**, oracle probe `up`, and the only exit-2 line is

```
conformance: §4.4.2-RECORDED-DECISION-EXIT — ledger findings == baseline; the graded run
completed and the bar is refused by that recorded decision
```

No `HARD guard failed`; ledger findings == baseline. The loan context grades 35/35 parity
pass, 0 refused, 0 inadmissible, 0 harness error; the whole-harness summary is 49 parity
PASS / 0 FAIL, `refused 0`, `inadmissible 0`, `harness errors 0`. `nofloat` reports
violations=0.

Scope held: **no Go source change** (only three JSON vectors), **no new seam**, one bounded
context (`loan`), PostgreSQL only (no Oracle Database anywhere). `.softhouse/guards/`,
`.softhouse/conformance.sh`, `.softhouse/capture/` and `.softhouse/maps/` are untouched
(`git diff main...HEAD --name-only` shows only the three vector files plus the pointer fix).
No container was started; the oracle probe was a read-only health GET against the already
running instance. The driver owns the push.

## 5. What this establishes

The MNT UC6 read-backs yield three further faithful vectors with no recomputation, and the
measurement is unambiguous: they **extend coverage, not kills**. The amortization family gets a
third independent observation on the same three drives; the interest and disbursement seams get
corroborating cross-validation with the limitation of each stated explicitly (non-tie interest,
zero-charge distribution, no disbursement drive). Where the capture cannot discriminate, that is
recorded as a limitation and the rule is kept, not relaxed.

## Appendix — all 43 loan drives, WITHOUT vs WITH

| drive | WITHOUT | WITH | delta |
| --- | ---: | ---: | ---: |
| `loan-wrong-allocation-drops-fee` | 1 | 1 | 0 |
| `loan-wrong-allocation-drops-penalty` | 1 | 1 | 0 |
| `loan-wrong-charge-outstanding-ignores-waived` | 1 | 1 | 0 |
| `loan-wrong-charge-partial-marks-paid` | 1 | 1 | 0 |
| `loan-wrong-charge-waiver-counts-as-paid` | 1 | 1 | 0 |
| `loan-wrong-charge-waiver-leaves-outstanding` | 1 | 1 | 0 |
| `loan-wrong-delinquency-absent-nonzero` | 1 | 1 | 0 |
| `loan-wrong-delinquency-thirty-day-month` | 3 | 3 | 0 |
| `loan-wrong-half-even-schedule-interest` | 1 | 1 | 0 |
| `loan-wrong-journal-entry-batch-collapses-credits-to-one-account` | 3 | 3 | 0 |
| `loan-wrong-journal-entry-batch-debit-from-first-two-credits` | 1 | 1 | 0 |
| `loan-wrong-journal-entry-batch-drops-fee-pair` | 4 | 4 | 0 |
| `loan-wrong-journal-entry-batch-first-pair-only` | 1 | 1 | 0 |
| `loan-wrong-journal-entry-batch-maps-fee-to-disbursement-accounts` | 1 | 1 | 0 |
| `loan-wrong-journal-entry-batch-nets-account` | 1 | 1 | 0 |
| `loan-wrong-journal-entry-batch-pairs-legs-two-at-a-time` | 1 | 1 | 0 |
| `loan-wrong-journal-entry-batch-routes-accrual-income-to-one-account` | 2 | 2 | 0 |
| `loan-wrong-journal-entry-batch-swaps-first-pair-sides` | 4 | 4 | 0 |
| `loan-wrong-repayment-omits-principal` | 2 | 2 | 0 |
| `loan-wrong-reversal-business-date` | 1 | 1 | 0 |
| `loan-wrong-reversal-duplicates-instead-of-reverses` | 1 | 1 | 0 |
| `loan-wrong-reversal-flags-originals` | 1 | 1 | 0 |
| `loan-wrong-reversal-fresh-transaction-id` | 1 | 1 | 0 |
| `loan-wrong-schedule-amortization-drops-final-component` | 2 | 3 | +1 |
| `loan-wrong-schedule-amortization-uniform-rounded-up` | 2 | 3 | +1 |
| `loan-wrong-schedule-amortization-uniform-truncated` | 2 | 3 | +1 |
| `loan-wrong-status-iota-ordinal` | 2 | 2 | 0 |
| `loan-wrong-summary-drops-fee` | 1 | 1 | 0 |
| `loan-wrong-summary-drops-penalty` | 2 | 2 | 0 |
| `loan-wrong-summary-drops-principal` | 7 | 7 | 0 |
| `loan-wrong-summary-interest-not-outstanding` | 6 | 6 | 0 |
| `loan-wrong-transaction-balance-accrual-zero` | 2 | 2 | 0 |
| `loan-wrong-transaction-balance-folds-repayment-interest` | 1 | 1 | 0 |
| `loan-wrong-transaction-balance-waiver-moves-principal` | 1 | 1 | 0 |
| `loan-wrong-writeoff-drops-fee` | 2 | 2 | 0 |
| `loan-wrong-writeoff-drops-penalty` | 2 | 2 | 0 |
| `loan-wrong-writeoff-journal-debits-loan-portfolio` | 2 | 2 | 0 |
| `loan-wrong-writeoff-journal-debits-principal-only` | 2 | 2 | 0 |
| `loan-wrong-writeoff-journal-one-debit-per-portion` | 2 | 2 | 0 |
| `loan-wrong-writeoff-journal-swaps-fee-and-penalty` | 2 | 2 | 0 |
| `loan-wrong-writeoff-principal-and-interest` | 2 | 2 | 0 |
| `loan-wrong-writeoff-principal-only` | 2 | 2 | 0 |
| `loan-wrong-writeoff-swaps-fee-and-penalty` | 2 | 2 | 0 |

Every drive was measured with no new vectors (32-vector store) and with them (35-vector
store). **40 of 43 counts are unchanged; none newly dies.**
