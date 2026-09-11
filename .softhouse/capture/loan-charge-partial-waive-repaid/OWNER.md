# OWNER — loan-charge-partial-waive-repaid

**Subject:** the first live observation of the `LoanCharge` money mutations
(`nexus/internal/apps/loan/charge.go`) and the money-crossing lifecycle transition
(`nexus/internal/apps/loan/lifecycle.go`, `RepaidInFull`) on one loan that is
**partly charged, the charge partly paid, a second charge waived, then the loan repaid in
full**. Every cited loan read-back in `.softhouse/vectors/loan/` today has `charges: null`
and no captured loan is ever paid off; this capture supplies both.

**Status: Complete.** The oracle accepted every step — no refusal. Four writes only:
`POST /clients`, `POST /loans` (charges applied at submission), `POST /loans/18?command=approve`
+ `?command=disburse`, `POST /loans/18/transactions?command=repayment` (**100.00**, step 3),
`POST /loans/18/charges/13?command=waive` (step 4), `POST /loans/18/transactions?command=repayment`
(**106641.98**, step 5). Every other call is a `GET`.

**Why it exists (the targets).** `nexus/internal/apps/loan/charge.go` carries 18 money-mutation
functions over a `LoanCharge`'s `amount / amountPaid / amountWaived / amountOutstanding`
(`UpdatePaidAmountBy`, `Waive`, `UpdateWaivedAmount`, `ReconcileFullyPaid`, …) and **no vector
reaches them** — the only cited loan read-backs all carry `charges: null`. And
`lifecycle.go`'s `RepaidInFull` transition has no observation: no captured loan is ever paid
off. This capture is the observation for both.

## Oracle identity

- Fineract reference implementation, `https://localhost:8443/fineract-provider/api/v1`
- tenant `gerege`, Basic auth `mifos:password`
- containers `gerege-oracle-db` (PostgreSQL) + `gerege-oracle-app` (fineract)
- database `fineract_gerege`; **business date 2026-09-03**, COB date 2026-09-02
  (`m_business_date`, in every `out/db-*.txt`)

**Pre-write snapshot (NOT committed):**
`/Users/buv/gerege-oracle-snapshots/fineract_gerege-pre-ohchgcap-capture-20260911T070413Z.dump`
(4,833,862 bytes, magic `PGDMP`). Taken with `pg_dump -Fc` **from `gerege-oracle-db`**
(not the stale `fineract-db-1`). No `.dump` is committed.

## The loan used

**Loan 18** — `accountNo 000000018`, `externalId OHCHGCAP-L01`, client **20**
(`externalId OHCHGCAP-C01`), product **3** `OHLGR-Accrual-Loan`, accounting **ACCRUAL
PERIODIC**, principal **100000.00**, flat 12 monthly periods at 12%/yr,
`mifos-standard-strategy`, disbursed **2026-01-01**. The same product/accounting mapping the
`loan-writeoff-paid-instalment` and `loan12-four-bucket-allocation` captures used.

| step | request | response (HTTP 200) |
|---|---|---|
| client | `req/client-OHCHGCAP-C01-create.json` | `clientId/resourceId 20` (`out/client-OHCHGCAP-C01-create-raw.json`) |
| submit | `req/loan-OHCHGCAP-L01-submit.json` | `loanId/resourceId 18`, `status 100` (`out/loan-OHCHGCAP-L01-submit-raw.json`) |
| approve | `req/loan-OHCHGCAP-L01-approve.json` | `status 200 approved` |
| disburse | `req/loan-OHCHGCAP-L01-disburse.json` | txn **69**, disbursed **2026-01-01**, `status 300 active` |

The two charges ride on the loan **at submission** (before disbursal), reusing the existing
definitions read in step01 (`GET /charges`):

| `loanChargeId` | charge def | kind | amount | due date | instalment |
|---|---|---|---|---|---|
| **14** | 5 | fee | **123.45** | **15 January 2026** | period 1 |
| **13** | 4 | penalty | **67.89** | **15 February 2026** | period 2 |

**Why the penalty due date is in period 2, not also period 1** (deliberate, and required by
the stated allocation order). The product's greedy allocation is penalty → fee → interest →
principal **within each instalment**. A partial repayment that lands on the fee must
therefore skip any *outstanding penalty in the same instalment* — impossible, because a
period-1 penalty is consumed first and can then no longer be waived. Placing the penalty in
the next period keeps it pending and waivable while the fee is partly paid. Both due dates
are inside the early schedule and both are `isDueDateCharge` (SDD).

## THE OBJECTIVE — per step: charge fields, loan status, and the function observed

Money in **integer minor units** (MNT = ISO 496, minor unit 2); `123.45 → 12345`,
`67.89 → 6789`, `100.00 → 10000`, `23.45 → 2345`, `106641.98 → 10664198`.

### Step 2 — loan created (charges applied at submission), disbursed

Detail `out/loan-18-created-detail-raw.json` sha256
`2acb49a26842e405b8f4deb531712637a4637632ddef1d1e443f29527e697bf9`; transactions
tx**69** disbursement 2026-01-01 **10000000**; **2** journal entries (disbursement).

| charge | kind | amount | amountPaid | amountWaived | amountOutstanding | paid | waived |
|---|---|---|---|---|---|---|---|
| 14 | fee | 12345 | 0 | 0 | **12345** | false | false |
| 13 | penalty | 6789 | 0 | 0 | **6789** | false | false |

Loan status `loanStatusType.active` (**300**). Summary: `totalExpectedRepayment 10680987`,
`principalOutstanding 10000000`, `interestOutstanding 661853`, `feeChargesOutstanding 12345`,
`penaltyChargesOutstanding 6789`, `totalOutstanding 10680987`.

**Function observed:** none of `charge.go`'s mutations — this step fixes the input state
(`CalculateOutstanding = Amount − AmountPaid − AmountWaived − AmountWrittenOff` reproduces
each `amountOutstanding`). `disbursement.go NetDisbursalAmount` is **not** exercised here:
neither charge is due at disbursment, so the net disbursal equals the principal (10000000).
Charges are applied at submission, which the oracle accepted.

### Step 3 — partly pay the fee: repayment **100.00** (2026-01-15)

Detail `out/loan-18-after-partial-detail-raw.json` sha256
`72c31879318d9fa4ced1896952604492dc1255a3d3e3ec935547e77c6685b51c`; transactions
tx**70** (`loanTransactionType.repayment`); **4** journal entries (2 added).

| charge | kind | amount | amountPaid | amountWaived | amountOutstanding | paid | waived |
|---|---|---|---|---|---|---|---|
| 14 | fee | 12345 | **10000** | 0 | **2345** | false | false |
| 13 | penalty | 6789 | 0 | 0 | **6789** | false | false |

Loan status `loanStatusType.active` (**300**).

**The allocation (the oracle's observation, not the plan).** tx70: amount **10000**,
`principalPortion 0`, `interestPortion 0`, `feeChargesPortion` **10000**,
`penaltyChargesPortion 0`; `loanChargePaidByList` = `{chargeId 14, amount 10000, name
OHLGR-Fee-SDD-100}`.
The whole payment lands on the fee — the penalty (period 2) is not reached.

**Function observed:** `charge.go UpdatePaidAmountBy` **partial branch** (increment 10000 <
outstanding 12345 → `amountPaid += 10000`, `amountOutstanding = calculateAmountOutstanding()`
= 2345; `paid` stays false). Reads: `CalculateOutstanding`, `IsPaidOrPartiallyPaid` (true),
`IsChargePending` (true), `IsFullyPaid`/`IsPaid` (false). `lifecycle.go DetermineTransition`
on an active loan with a non-zero `TotalOutstanding` → `NoTransition(StatusActive)`.

### Step 4 — waive the penalty: `POST /loans/18/charges/13?command=waive`

Detail `out/loan-18-after-waive-detail-raw.json` sha256
`dd6b8da353531cc91bc3948eab3bb2659fe44fc2ec7892d244e31d339bd1888f`; transactions
tx**71** (`loanTransactionType.waiveCharges`, date **2026-02-15**); journal entries still
**4**.

| charge | kind | amount | amountPaid | amountWaived | amountOutstanding | paid | waived |
|---|---|---|---|---|---|---|---|
| 14 | fee | 12345 | 10000 | 0 | 2345 | false | false |
| 13 | penalty | 6789 | 0 | **6789** | **0** | false | **true** |

Loan status `loanStatusType.active` (**300**).

**Function observed:** `charge.go Waive` (non-instalment branch):
`amountWaived = amountOutstanding` (6789), `amountOutstanding = 0`, `paid = false`,
`waived = true`. Reads: `IsWaived` (true), `IsChargePending` (false), `IsFullyPaid` (false).
`lifecycle.go DetermineTransition` still `NoTransition(StatusActive)` (the fee is still
outstanding).
`charge.go UpdateWaivedAmount` — invoked by the schedule/reprocess path on every charge — is
a **no-op** on both: the fee has `amountWaived = 0` (returns early) and the penalty has
`amountWaived == amount` (6789 == 6789, which falls through *both* the `>` and `<`
comparisons). The observed flags (`waived true / paid false`) are exactly `Waive`'s output.

**No journal entry is posted for a waiver here — and that is the observation.** tx71 carries
`amount 6789` with `penaltyChargesPortion` **0** (NULL in `m_loan_transaction`), and the
read-only count of `acc_gl_journal_entry` per loan transaction is
`69→2, 70→2, **71→0**, 72→4, 73→4`. Cause, from
`LoanChargeWritePlatformServiceImpl.waiveLoanCharge` (pinned source `426a23544`,
lines 1376-1453): the product is periodic-accrual, so
`receivableCharge = accruedCharge − amountPaid.zero() → clamp 0`; since
`amountWaived (6789) > receivableCharge (0)`, `chargeComponent` (the booking portion) is **0**
and the full 6789 is classified as **unrecognizedIncome**. Nothing is accrued yet, so nothing
is reversed: zero legs. The waive still calls
`loanLifecycleStateMachine.determineAndTransition(...)` (line 1452) — the lifecycle probe.
Transaction date 2026-02-15 is the charge's due date (the `isDueDateCharge` / `businessDate`
branch), which is why tx71 is dated 2026-02-15 while the actual business date is 2026-09-03.

### Step 5 — repay the loan in full: repayment **106641.98** (2026-09-03)

Payoff amount from `GET /loans/18/transactions/template?command=repayment`
(`out/loan-18-template-repayment-raw.json` sha256
`12671e7950e16190e78f6fb4218fabcf20f5f77af263a6837f7022668bf3c982`) = **106641.98**
(= `totalOutstanding` after the waive).

Detail `out/loan-18-final-detail-raw.json` sha256
`979310855f2d0e3d8738982932dfa0815a63be2bfc369bd719977101aa5761e5`; transactions
`out/loan-18-final-transactions-raw.json` sha256
`616afd99735bb1046f8eec1a00e49098c435cfa559b124aadf3e43669d3ff064`; journal entries
`out/loan-18-final-journalentries-raw.json` sha256
`5bc519e5d755df5c21a863e9c4eb44388399031f3735ca974eb67c241b758dd1` (**12** entries).

| charge | kind | amount | amountPaid | amountWaived | amountOutstanding | paid | waived |
|---|---|---|---|---|---|---|---|
| 14 | fee | 12345 | **12345** | 0 | **0** | **true** | false |
| 13 | penalty | 6789 | 0 | 6789 | **0** | false | true |

Loan status **`loanStatusType.closed.obligations.met`** (**600**), `closedOnDate 2026-09-03`;
all four outstanding buckets 0 (`m_loan.loan_status_id 600`, `closedon_date 2026-09-03`, all
`*_outstanding_derived` 0). **This is the lifecycle observation: a captured loan is paid off.**

**The allocation.** tx**72**: amount **10664198**, `principalPortion` **10000000**,
`interestPortion` **661853**, `feeChargesPortion` **2345**, `penaltyChargesPortion` 0,
`outstandingLoanBalance` 0; `loanChargePaidByList` = `{chargeId 14, amount 2345, name
OHLGR-Fee-SDD-100}`.
The oracle also posts a catch-up accrual tx**73** (`loanTransactionType.accrual`, date
2026-09-03): amount **674198** = interest **661853** + fee **12345**, recognizing the income
that no COB had posted — including the fee's earlier 10000 that was unrecognized at step 3.

**Function observed:** `charge.go UpdatePaidAmountBy` **full branch** (increment 2345 ≥
outstanding 2345 → `amountPaid = 12345`, `amountOutstanding = 0`, and since `amountWaived == 0`
`paid = true`). Reads: `IsFullyPaid` (true), `CalculateOutstanding` (0).
`lifecycle.go Facts` → `{HasOutstanding:false, TotalOutstanding:0, RepaidInFull:true,
AllChargesPaid:true, TotalOverpaidIsPositive:false}`; `DetermineTransition(StatusActive,
facts)` → the `RepaidInFull` branch → `Transition{ClosedObligationsMet, EventRepaidInFull,
Needed:true}`; `NextStatus(StatusActive, EventRepaidInFull, facts)` → `(ClosedObligationsMet,
true)`. `TotalOutstandingIsZero` (true) is the guard.

**Journal entries (final, 12 = disbursement 2 + step-3 repayment 2 + step-5 repayment 4 +
catch-up accrual 4):**
tx72 — debit `OHLGR-20010` OHLGR-Fund-Source 10664198; credit loan portfolio `OHLGR-10010`
10000000; credit interest receivable `OHLGR-10012` 661853; credit fees receivable
`OHLGR-10013` 2345. tx73 accrual — debit `OHLGR-10012` 661853 / credit `OHLGR-40010`
OHLGR-Interest-On-Loans 661853; debit `OHLGR-10013` 12345 / credit `OHLGR-40011`
OHLGR-Income-From-Fees 12345. (Step-3 pair: credit `OHLGR-10013` fees receivable 10000 /
debit `OHLGR-20010` fund source 10000.) No leg is reversed.

## Function coverage summary

| `charge.go` / `lifecycle.go` function | step | observation |
|---|---|---|
| `CalculateOutstanding` / `calculateAmountOutstanding` | 2,3,4,5 | reproduces each `amountOutstanding` (12345→2345→2345→0) |
| `IsChargePending` / `IsPaidOrPartiallyPaid` | 3 | fee pending true after partial |
| `UpdatePaidAmountBy` (partial) | 3 | fee `amountPaid` 0→10000; outstanding 2345 |
| `Waive` | 4 | penalty `amountWaived = amountOutstanding = 6789`; outstanding 0; waived true |
| `IsWaived` / `IsChargePending` | 4 | penalty waived true, pending false |
| `UpdateWaivedAmount` | 4 | invoked, **no-op** (equality falls through) |
| `UpdatePaidAmountBy` (full) | 5 | fee `amountPaid` 10000→12345; outstanding 0; **paid true** |
| `IsFullyPaid` / `IsPaid` | 5 | fee fully paid true |
| `lifecycle.go Facts` / `DetermineTransition` / `NextStatus` | 3,4,5 | NoTransition, NoTransition, **Active→ClosedObligationsMet via RepaidInFull** |
| `lifecycle.go TotalOutstandingIsZero` | 5 | true, gates the transition |

**Not exercised (and why):** `ReconcileFullyPaid` / `reconcileChargeStatusWithSummary` — the
reconcile fires only when a bucket total is zero **while a charge is active, unpaid and
unwaived** (`LoanBalanceService.java:130-150`). At step 5 the fee bucket is zero *and* the fee
is already `paid`, and the penalty bucket is zero *and* the penalty is `waived`; both guards
fail, so the reconcile is skipped. `MarkAsFullyPaid`, `ResetToOriginal`, `ResetPaidAmount`,
`UndoWaive`, `UndoPaidOrPartiallyAmountBy` are not reached by a forward payment/waive flow.

## Money / units

MNT = ISO 496, minor unit 2. Every cell is a whole number of minor units:
`123.45 → 12345`, `67.89 → 6789`, `100.00 → 10000`, `23.45 → 2345`,
`6618.53 → 661853`, `6741.98 → 674198`, `106641.98 → 10664198`,
`100000.00 → 10000000`. **No sub-minor residue.**

## Byte-stability of request bodies

`bin/verify-req.sh` → `all request bodies integer/string only — byte-stable`. Every
`req/*.json` carries no decimal JSON number: the charge amounts are JSON strings
(`"123.45"`, `"67.89"`), the repayment amounts are strings (`"100"`, `"106641.98"`), and the
loan principal is `"100000"`. Nothing is routed through `json.dumps` of a parsed float, so
each body survives a binary-double round trip byte-for-byte.

## Writes

Three setup writes (client, loan submit with its two charges, approve+disburse) and three
subject writes (partial repayment, charge waiver, full repayment). No SQL insert; tenant
`gerege` only; no `default` tenant write; no product/charge-definition/client mutation beyond
the documented creation; no `.go` file touched. The driver pushes.

## Re-run / artifacts

- `bin/step01-probe.sh` — read-only probe (GETs + read-only SQL). Idempotent.
- `bin/step02-create.sh` … `bin/step05-repay-full.sh` — not idempotent against the live
  oracle (ids/state advance); re-run against the pre-write snapshot above.
- `bin/capture-state.sh LOAN_ID LABEL` — `GET /loans/{id}?associations=all` (carries
  `charges`) + transactions + journal entries, each with a `.status` companion.
- `bin/db-evidence.sh LOAN_ID LABEL` — read-only SQL corroboration to `out/db-LABEL.txt`.
- `bin/verify-req.sh` — body byte-stability guard.

Raw JSON (single-line; cite at line 1) with `.status` companions (all 200):
`out/loan-18-{created,after-partial,after-waive,final}-detail-raw.json`,
`…-transactions-raw.json`, `…-journalentries-raw.json`,
`out/loan-18-template-repayment-raw.json`, `out/client-…-create-raw.json`,
`out/loan-18-…submit/approve/disburse-raw.json`. DB corroboration:
`out/db-{created,after-partial,after-waive,final}.txt`.

**Note on the SQL snapshots.** The per-step `db-*.txt` were captured live at each step, so
their `m_loan_transaction` / `m_loan_charge` sections are faithful per-step evidence. The
`## m_loan` section of the **first three** files errored: the query used a wrong column name
(`closed_on_date`, corrected to `closedon_date`; `expected_maturedon_date` does not exist and
was dropped). `out/db-final.txt` was re-captured with the corrected query (this is legitimate:
the loan is final now, and the corrected row matches the JSON detail). Per-step **loan status**
is authoritative from the JSON detail (`status.code`), not from that SQL section; DB is
corroboration only.

## The arithmetic — the line that grades the allocation and the payoff

In minor units, the step-3 payment equals the fee portion exactly, and the step-5 payoff
equals the remaining loan:

```
step 3:   10000  = fee 10000 + penalty 0 + interest 0 + principal 0
step 5: 10664198 = principal 10000000 + interest 661853 + fee 2345 + penalty 0
waive:     6789  = penalty amountWaived (6789) ;  booking portion 0 (unrecognized income)
```

A port that drops the fee bucket, the penalty bucket, or both cannot reproduce the observed
`amountPaid`/`amountWaived`/`amountOutstanding` transitions; a port that never closes a loan
cannot reproduce status **600**.
