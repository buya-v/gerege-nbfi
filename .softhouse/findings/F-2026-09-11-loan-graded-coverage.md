# F-2026-09-11 — the loan graded corpus is now measurable, and what it never reaches

**Status:** **OPEN — triage only.** No capture was taken, no vector and no drive was
written. This run makes the loan corpus *measurable* and triages the result. Grading any
gap it finds is a later run's work, after a capture if one is needed.
**Task:** `OH-LOANCOV-T`, bounded context `loan`, branch `feat/OHLOANCOVt`.
**Found by:** Go coverage of the loan port, measured with the port as `-coverpkg` and the
**conformance package** as the test target — the instrument the driver validated on the
savings-holds case (`F-2026-09-10-savings-holds-ungraded.md`), not the grep it replaced.

## 1. The missing control, added

`loan` read `0.0%` from conformance for *every* function while its 20 committed vectors
passed against the oracle — because the loan conformance package had **no test that drove
the committed corpus through the grading path**. Without one, no vector can ever move the
number, and the reading is meaningless.

Added `nexus/internal/apps/loan/conformance/committed_store_test.go`, modelled on
`nexus/internal/apps/savings/conformance/committed_store_test.go`:

* it drives the **real committed store** through `LoadStore` → `Admit` → `Run` against the
  reference `loan-go`, exactly as the grading binary does;
* it **calls no port function directly** — every statement it reaches is reached *through
  the vectors*, so the coverage is real, not manufactured;
* anti-vacuity: it fails if the store loads zero vectors; it pins the loan seam set and
  the `loan-go` reference id, and asserts the committed loan vectors are present.

The committed corpus passes:

    go run ./internal/apps/loan/conformance/cmd/conformance -root ..
    → vectors_loaded=20 parity_pass=20 parity_fail=0 refused=0 inadmissible=0
      harness_error=0  graded_cells=100 money_cells=33 invariant_violations=0

## 2. Before / after

    go test -coverpkg=./internal/apps/loan -coverprofile=/tmp/loan.cov \
        ./internal/apps/loan/conformance/...
    go tool cover -func=/tmp/loan.cov

| | statements | coverage | functions at 0.0% |
|---|---:|---:|---:|
| before (no committed-store test) | 1,395 | 13.9% | 123 |
| after (test present) | 1,395 | **17.5%** | **118** |

The delta is deliberately small and narrow: five functions that the grading path reaches
only because a vector exercises them:

* `scheduleamortization.go:31` `DerivePrincipalAmortization` — via `LN-L10`
* `status.go:81` `StoredValue`, `status.go:90` `Code`, `status.go:102`
  `LoanStatusFromStoredValue` — via `LN-L01-status-active` / `LN-L06-status-approved`
* `summary.go:45` `TotalOutstanding` — via the five `loan-summary-outstanding` vectors

**118 loan functions remain at 0.0% from the graded corpus.** Full list in the appendix.

## 3. Triage method (the part that turns a number into a finding)

A `0.0%` is a **candidate, not a gap**. Following the holds case, each candidate that
implements a **money rule** (not a getter, a `String()`, an enum decoder, an error
constructor) is checked against one question only:

> **Does an observation behind it exist in the committed corpus?**

For holds the answer was *no* — every apparent match was a *field* (`withholdTax`,
`amountOnHold`), and no capture carried a hold-flagged transaction. That confirmation is
what made it a finding. The same test is applied below. Where an observation *does* exist
but is ungraded, the candidate is **holds-shaped**: implemented, observed, and unreached.
Where no observation exists, a capture is required before it can be graded at all.

### Corpus scope

The **graded loan corpus** is the 20 vectors in `.softhouse/vectors/loan/`. Their capture
refs are the only observations in play:

    loan/out/{loan-1-detail,loan-1-detail-after,loan-1-transactions-after,
              loan-3-detail-after,loan-3-transactions-after,loan-5-detail,
              loan-5-schedule,loan-L06-detail,loan-L06-schedule,loan-L06-approve}-raw.json
    gl-accounting-surface/out/{loan-10-raw,loan-12-raw,journalentries-all-raw}.json
    loan12-four-bucket-allocation/out/{loan-12-transactions-after-raw,
                                      journalentries-loan-12-after-raw}.json

Two probes of "what the corpus varies" were run, and they are the backbone of the
observations column:

* **Transaction types** across the whole committed capture tree:
  `Accrual 55, Disbursement 26, Repayment 7, Purchase 3, Repayment (at time of
  disbursement) 3, Waive interest 2, Goodwill Credit 1`. **Zero write-off, zero
  chargeback, zero charge-payment.**
* **Loan `charges` arrays**: `charges` is `null` in *every* cited loan capture
  (`loan-10-raw`, `loan-12-raw`, `loan-5-detail-raw`, `loan-L06-detail-raw`, and the other
  loan/out details). The loan read-backs that *do* carry charge objects
  (`tierA-a2/out/A2-336,A2-339,A2-384`) are cited by **no vector at all**.

## 4. Triage of the money-rule candidates

`file:line` are lines in the file.

### 4.1 `writeoff.go:36` `WriteOffOutstanding` — observation ABSENT → needs a capture

*Rule.* A write-off discharges the whole outstanding principal/interest/fee/penalty and
returns it so the caller can post the reversing entry. Money rule, integer minor units.

*Observation.* **None, anywhere in the committed capture tree.** The transaction-type
histogram contains no write-off; a full-text scan for a nonzero `writtenOff` in any
capture finds nothing. No loan in the corpus is ever written off.

*What a capture would need.* A loan with an outstanding balance, written off, read back:
the loan detail after the write-off and its transactions, so the outstanding buckets fall
to zero and the write-off transaction is visible. Without it a drive that broke this
function kills zero — this is the holds case with a different rule.

### 4.2 `delinquency.go:96` `OverdueDays` / `delinquency.go:109` `DelinquentDays` — OBSERVED but UNGRADED → holds-shaped, gradeable without a capture

*Rule.* The day-count rules over the delinquency/overdue dates (`overdueSinceDate`,
`delinquentDays`) — a calendar rule, not a minor-units fold, but a real derived value.

*Observation.* **Exists.** The committed loan details carry a delinquency block
(`overdueSinceDate`, `delinquentDays`, and per-bucket `*Overdue`), and the corpus pins a
business date. A vector could derive these from the observed dates and grade them.

*Verdict.* This is the strongest holds-shaped candidate among the non-minor-units rules:
implemented, observed, ungraded. It is **not** a defect — it is a candidate for a later
grading run, and needs no capture.

### 4.3 `disbursement.go:13,35,41,60` — sum/adjust/deduct/settle: seam does not call them

*Rule.* `SumChargesDueAtDisbursement` (`:13`) sums active charges due at disbursement;
`AdjustNetDisbursalAmount` (`:35`) and `DeductFromNetDisbursalAmount` (`:41`) are the
adjustment/deduction forms; `SettleDisbursementCharges` (`:60`) is the
repayment-at-disbursement settlement loop, which **mutates** the charge list and returns
`disbursentMoney`.

*Why 0.0%.* The disbursement seam (`conformance/impl.go:338` `goDisburse`) parses a
**scalar** `ChargesDueAtDisbursementMinor` and calls **only** `loan.NetDisbursalAmount`
(`impl.go:347`). The four functions above are never entered, because the harness passes
the *already-summed* charge amount rather than the charge list.

*Observation.* The *aggregate* is observed: `loan-10-raw` has
`feeChargesAtDisbursementCharged: 100.000000` with `approvedPrincipal: 100000` and
`netDisbursalAmount: 99900` — i.e. `net = principal − charges` at nonzero charges, not just
the zero-charge `LN-L06-disbursement-net` vector. But **no capture carries a charge
object**, so the *loop* behind `SumChargesDueAtDisbursement`/`SettleDisbursementCharges`
has no observation.

*Verdict.* Two distinct blockers: (a) the seam does not call the charge-list functions at
all — grading them needs the seam extended to take the charge list; and (b) settling needs
an observation of an active, unpaid, non-transfer charge due at disbursement. `loan-10`
proves such a charge *was settled* (fee paid 100), so a capture exposing that charge's
state is feasible. **Candidate; not a defect.**

### 4.4 `charge.go` (22 functions) — no charge object in the graded corpus; only fully-paid states observed elsewhere

*Rule.* The `LoanCharge` lifecycle over `amount` / `amountPaid` / `amountWaived` /
`amountOutstanding`: `CalculateOutstanding` (`:61`), `calculateAmountOutstanding` (`:68`),
`IsFullyPaid` (`:74`), `IsPaid` (`:78`), `IsNotFullyPaid` (`:82`), `IsWaived` (`:85`),
`IsChargePending` (`:89`), `IsDueAtDisbursement` (`:101`), `IsPaidOrPartiallyPaid`
(`:111`), `MarkAsFullyPaid` (`:124`), `ReconcileFullyPaid` (`:133`), `ResetToOriginal`
(`:148`), `ResetPaidAmount` (`:160`), `Waive` (`:169`), `UndoWaive` (`:180`),
`UpdatePaidAmountBy` (`:191`), `UndoPaidOrPartiallyAmountBy` (`:220`),
`UpdateWaivedAmount` (`:243`). The remaining four are type/classification getters.

*Observation.* **No charge object appears in the graded corpus.** Every cited loan
read-back has `charges: null`; the only charge data the vectors see is the *aggregate*
`feeCharges*` columns of the summary. The committed tree *does* contain loan charge
read-backs — `tierA-a2/out/A2-336`, `A2-339`, `A2-384` — carrying a `chargeId 6` penalty
(amount 7500) and a `chargeId 1` disbursement fee (amount 15000), **but both are shown
fully paid** (`amountPaid == amount`, `amountOutstanding 0`, `paid: true`), and those
captures are cited by **no vector**. So even the existing observation reaches only the
fully-paid predicates, not the partial-payment / waiver mutation paths (`Waive`,
`UpdatePaidAmountBy`, `UpdateWaivedAmount`, `ReconcileFullyPaid`, `Undo*`).

*What a capture would need.* A loan read-back with a **non-null `charges` array** in a
*partially paid* state and a *waived* state, so the outstanding/paid/waived arithmetic is
observable. Fully-paid states alone reach the predicates but not the money mutations.

### 4.5 `lifecycle.go:37` `NextStatus`, `lifecycle.go:171` `DetermineTransition` — transitions observed, state machine ungraded

*Rule.* The loan lifecycle state machine: given the current status, the event and the
`Facts` snapshot, return the next status. `DetermineTransition` (`:171`, with `NoTransition`
`:157` and `TotalOutstandingIsZero` `:144`) is the money-adjacent part — it decides
`RepaidInFull` / `TotalOverpaidIsPositive` transitions from the balances.

*Why 0.0%.* The `loan-status` seam (`impl.go` `goStatus`) **decodes** the observed status
token (`status.go`) but never drives the `(from, event, facts)` transition function.

*Observation.* The transition *pairs* exist: `loan-L06-submit-raw`, `-approve-raw` and
`-disburse-raw` capture the loan before/after submit→approve→disburse. But the corpus
never reaches a balance-zero or overpaid state, so the **money-crossing transitions**
(`RepaidInFull`, `TotalOverpaidIsPositive`) have no observation. `NextStatus` for the
ordinary event path could in principle be graded from the observed status pairs; the
overpaid/repaid-in-full arms need a capture of a loan actually paid off or overpaid.

### 4.6 `delinquency.go:47` `AggregateInstallmentDelinquency` — observation ABSENT

*Rule.* Sums per-installment delinquency across ranges (`LoanDelinquencyRange` buckets).
Money-adjacent aggregation.

*Observation.* **None.** Every loan in the corpus has `enableInstallmentLevelDelinquency:
false`; the `delinquencyPausePeriods` and `overdueCharges` arrays are empty everywhere. No
per-installment delinquency range is ever populated.

*What a capture would need.* A product with installment-level delinquency enabled and a
loan in arrears long enough to populate the range buckets.

### 4.7 Not money rules (helper / already-graded path)

* `allocation.go:25` `Total`, `allocation.go:59` `Add` — bucket-sum helpers; the graded
  allocation engine (`AllocateInOrder` 92.9%, `AllocatePayment` 100%) uses `Set`/`For`
  directly, so these are convenience surface, not a money rule of their own.
* `allocation.go:108` `AllocateCredit` — the chargeback allocation
  (`calculateChargebackAllocationMap`). It *is* a money rule, but it is a one-line
  wrapper over `AllocateInOrder` (already graded) and the corpus has **no chargeback
  transaction** (histogram above). Observation absent; low marginal value to grade
  separately.
* `journalbatch.go:45` `Balances` — the `debits == credits` predicate. The *summing* rule
  `SumJournalEntryBatch` is graded at 85.7% and the balance invariant is enforced by the
  conformance invariant set (`invariant_violations=0`), so this predicate is already
  covered by the graded path in substance.
* `summary.go:53–74` `IsRepaidInFull`, `HasOutstanding`, `IsOverpaid`, `OverpaidIsZero`,
  `Facts` — five predicates over `TotalOutstanding`, which is now graded (100%) via the
  summary vectors. They are wired into the lifecycle machine (4.5), which is the ungraded
  consumer.
* The enum decoders / `String()` / `HumanReadableName` / error constructors
  (`transactiontype.go` 37, `status.go` 16, `allocationtype.go` 6, `journalentryside.go`,
  etc.) are not money rules and are out of scope for this triage.

## 5. Summary of triage

| candidate | file:line | money rule? | observation in corpus? | action |
|---|---|---|---|---|
| `WriteOffOutstanding` | `writeoff.go:36` | yes | **no** (no write-off tx anywhere) | needs capture |
| `AggregateInstallmentDelinquency` | `delinquency.go:47` | yes | **no** (feature disabled everywhere) | needs capture |
| `OverdueDays` | `delinquency.go:96` | derived days | **yes** (delinquency block) | gradeable now |
| `DelinquentDays` | `delinquency.go:109` | derived days | **yes** (delinquency block) | gradeable now |
| `SumChargesDueAtDisbursement` | `disbursement.go:13` | yes | partial (aggregate only) | needs seam + charge capture |
| `SettleDisbursementCharges` | `disbursement.go:60` | yes (mutating) | partial | needs seam + charge capture |
| `AdjustNetDisbursalAmount` | `disbursement.go:35` | yes | partial | needs seam + charge capture |
| `DeductFromNetDisbursalAmount` | `disbursement.go:41` | yes | partial | needs seam + charge capture |
| charge lifecycle (18) | `charge.go:61–243` | yes | **no** (charges:null; elsewhere fully-paid, uncited) | needs charge capture |
| `NextStatus` | `lifecycle.go:37` | state machine | yes (status pairs) | gradeable, later run |
| `DetermineTransition` | `lifecycle.go:171` | yes (balance-crossing) | no for repaid/overpaid arms | needs capture for those arms |
| `AllocateCredit` | `allocation.go:108` | yes | no (no chargeback) | low value |
| `Balances` | `journalbatch.go:45` | invariant | graded in substance | close |
| `Total`, `Add` | `allocation.go:25,59` | helper | n/a | not a rule |

**No candidate here is asserted to be a defect.** `WriteOffOutstanding` and the
charge-lifecycle block are the two strongest "implemented and never observed" candidates;
`OverdueDays`/`DelinquentDays` and the status machine are observed-but-ungraded. The
evidence, not this list, decides which are real.

## 6. What this run did NOT do

* No capture was taken; no `POST`/`PUT`/`DELETE` issued.
* No vector and no drive was written. `.softhouse/vectors/loan/` is unchanged.
* No port code changed. `.softhouse/guards/ledger-invariants.baseline` (12 pairs) and
  `.softhouse/conformance.sh` (census 17) are untouched.
* No gap was graded; a future run must capture first where the observation is absent.

## 7. Controls

* `go build ./...` — clean.
* `go test ./...` — all packages pass.
* `bash .softhouse/conformance.sh` — **exit 2** as the recorded §4.4.2 decision; ledger
  findings 12 pairs; guard census 17. Verdict excluding the 1 recorded divergence: PASS.
* `kills.sh loan loan-wrong-summary-drops-penalty` → **2**.
* `kills.sh savings savings-wrong-hold-folded-into-balance` → **1**.
* `kills.sh loanschedule loanschedule-wrong-days-in-year-365` → **45**.
* `loan-go` on the committed store: `vectors_loaded=20 parity_pass=20 parity_fail=0`.
* New test passes on the current tree; remove a vector and its coverage falls back — the
  number is vector-driven, not manufactured.

## Appendix — all 118 loan functions still at 0.0% from the graded corpus
- `allocation.go:25` `Total`
- `allocation.go:59` `Add`
- `allocation.go:108` `AllocateCredit`
- `allocationtype.go:43` `String`
- `allocationtype.go:52` `HumanReadableName`
- `allocationtype.go:57` `IsPenalty`
- `allocationtype.go:58` `IsFee`
- `allocationtype.go:59` `IsPrincipal`
- `allocationtype.go:60` `IsInterest`
- `charge.go:61` `CalculateOutstanding`
- `charge.go:68` `calculateAmountOutstanding`
- `charge.go:74` `IsFullyPaid`
- `charge.go:78` `IsPaid`
- `charge.go:82` `IsNotFullyPaid`
- `charge.go:85` `IsWaived`
- `charge.go:89` `IsChargePending`
- `charge.go:92` `IsFeeCharge`
- `charge.go:96` `IsPenaltyCharge`
- `charge.go:101` `IsDueAtDisbursement`
- `charge.go:107` `IsInstalmentFee`
- `charge.go:111` `IsPaidOrPartiallyPaid`
- `charge.go:118` `ChargeAmount`
- `charge.go:124` `MarkAsFullyPaid`
- `charge.go:133` `ReconcileFullyPaid`
- `charge.go:148` `ResetToOriginal`
- `charge.go:160` `ResetPaidAmount`
- `charge.go:169` `Waive`
- `charge.go:180` `UndoWaive`
- `charge.go:191` `UpdatePaidAmountBy`
- `charge.go:220` `UndoPaidOrPartiallyAmountBy`
- `charge.go:243` `UpdateWaivedAmount`
- `delinquency.go:47` `AggregateInstallmentDelinquency`
- `delinquency.go:85` `minimumAgeOrZero`
- `delinquency.go:96` `OverdueDays`
- `delinquency.go:109` `DelinquentDays`
- `delinquency.go:123` `dateOnly`
- `disbursement.go:13` `SumChargesDueAtDisbursement`
- `disbursement.go:35` `AdjustNetDisbursalAmount`
- `disbursement.go:41` `DeductFromNetDisbursalAmount`
- `disbursement.go:60` `SettleDisbursementCharges`
- `duetype.go:32` `String`
- `event.go:84` `String`
- `futureinstallmentrule.go:39` `String`
- `futureinstallmentrule.go:48` `HumanReadableName`
- `journalbatch.go:45` `Balances`
- `lifecycle.go:37` `NextStatus`
- `lifecycle.go:144` `TotalOutstandingIsZero`
- `lifecycle.go:157` `NoTransition`
- `lifecycle.go:171` `DetermineTransition`
- `paymentallocationtype.go:89` `String`
- `paymentallocationtype.go:98` `DueType`
- `reschedule.go:26` `StoredValue`
- `reschedule.go:28` `String`
- `reschedule.go:37` `IsPendingApproval`
- `reschedule.go:43` `IsApproved`
- `reschedule.go:47` `IsRejected`
- `reschedule.go:63` `GetRecalculateInterest`
- `reschedule.go:73` `Approve`
- `reschedule.go:82` `Reject`
- `status.go:92` `String`
- `status.go:110` `IsSubmittedAndPendingApproval`
- `status.go:113` `IsApproved`
- `status.go:114` `IsActive`
- `status.go:115` `IsWithdrawnByClient`
- `status.go:116` `IsRejected`
- `status.go:117` `IsOverpaid`
- `status.go:119` `IsClosedObligationsMet`
- `status.go:120` `IsClosedWrittenOff`
- `status.go:121` `IsClosedRescheduleOutstandingAmount`
- `status.go:127` `IsClosed`
- `status.go:131` `IsTransferInProgress`
- `status.go:132` `IsTransferOnHold`
- `status.go:136` `IsUnderTransfer`
- `status.go:140` `IsActiveOrAwaitingApprovalOrDisbursal`
- `status.go:146` `HasStateOf`
- `summary.go:53` `IsRepaidInFull`
- `summary.go:57` `HasOutstanding`
- `summary.go:61` `IsOverpaid`
- `summary.go:66` `OverpaidIsZero`
- `summary.go:74` `Facts`
- `transactiontype.go:219` `StoredValue`
- `transactiontype.go:228` `Code`
- `transactiontype.go:230` `String`
- `transactiontype.go:241` `LoanTransactionTypeFromStoredValue`
- `transactiontype.go:251` `IsDisbursement`
- `transactiontype.go:252` `IsRepaymentAtDisbursement`
- `transactiontype.go:255` `IsRepayment`
- `transactiontype.go:256` `IsInterestPaymentWaiver`
- `transactiontype.go:259` `IsMerchantIssuedRefund`
- `transactiontype.go:262` `IsPayoutRefund`
- `transactiontype.go:263` `IsGoodwillCredit`
- `transactiontype.go:264` `IsChargeRefund`
- `transactiontype.go:265` `IsRecoveryRepayment`
- `transactiontype.go:266` `IsWaiveInterest`
- `transactiontype.go:267` `IsWaiveCharges`
- `transactiontype.go:268` `IsAccrual`
- `transactiontype.go:269` `IsWriteOff`
- `transactiontype.go:270` `IsChargePayment`
- `transactiontype.go:271` `IsRefundForActiveLoan`
- `transactiontype.go:272` `IsIncomePosting`
- `transactiontype.go:273` `IsChargeback`
- `transactiontype.go:274` `IsChargeAdjustment`
- `transactiontype.go:275` `IsChargeOff`
- `transactiontype.go:276` `IsReage`
- `transactiontype.go:277` `IsReamortize`
- `transactiontype.go:278` `IsDownPayment`
- `transactiontype.go:279` `IsAccrualActivity`
- `transactiontype.go:280` `IsInterestRefund`
- `transactiontype.go:281` `IsAccrualAdjustment`
- `transactiontype.go:282` `IsCapitalizedIncome`
- `transactiontype.go:283` `IsCapitalizedIncomeAdjustment`
- `transactiontype.go:286` `IsContractTermination`
- `transactiontype.go:287` `IsBuyDownFee`
- `transactiontype.go:288` `IsBuyDownFeeAdjustment`
- `transactiontype.go:291` `IsDiscountFee`
- `transactiontype.go:292` `IsDiscountFeeAmortization`
- `transactiontype.go:297` `IsRepaymentType`
- `writeoff.go:36` `WriteOffOutstanding`

## Addendum (driver, 2026-09-11 evening) — §4.6 installment-level delinquency: observed as an aggregate only

The MNT replay of `LoanDelinquency-Part1.feature` (`.softhouse/capture/tierd-feasibility/delinquency-mnt/`) holds 111
read-backs with `delinquent.installmentLevelDelinquency` populated — but only the AGGREGATE buckets
`AggregateInstallmentDelinquency` returns (e.g. loan 14 read-back 5: range 1 250.00, range 3 250.00, range 30 500.00 from
four overdue 250.00 instalments). The per-instalment TAGS it takes as input (which range each instalment fell in) are not
in any payload; reconstructing them means re-deriving each instalment's age, which pause periods perturb. A vector built
that way would largely re-sum numbers reverse-engineered from the observed answer, so the driver has NOT dispatched it.
Gradeable honestly only via a capture that exposes per-instalment delinquency tags, or by grading the tagging step and the
aggregation together once the tagging rule is ported. Pause periods (§4.2) are graded — see OH-DLPAUSE-BT2.
