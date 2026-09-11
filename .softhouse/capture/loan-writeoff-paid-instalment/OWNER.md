# OWNER — loan-writeoff-paid-instalment

**Subject:** the first live observation of a loan **write-off** on a loan whose schedule has
**one fully paid instalment (`complete: true`) and eleven unpaid ones** — the case
`OH-WOGRADE-W` could not reach, because loan 11 had no fully paid instalment. The rule under
test:

> `writeoff.go:36` `WriteOffOutstanding` sums the four outstanding buckets (principal,
> interest, fee, penalty) over every instalment that is **not** `ObligationsMet`. The **skip**
> is the target: an instalment already fully paid must contribute nothing to the write-off.

**Status: Complete.** `POST /loans/13/transactions?command=writeoff` → HTTP **200**. No
refusal. Exactly one write (the write-off); every other call is a GET or the documented
creation/repayment chain. **The oracle did not refuse.**

## Oracle identity

- Fineract reference implementation, `https://localhost:8443/fineract-provider/api/v1`
- tenant `gerege`, Basic auth `mifos:password`
- containers `gerege-oracle-db` (PostgreSQL) + `gerege-oracle-app` (fineract)
- database `fineract_gerege`; **business date 2026-09-03**, COB date 2026-09-02
  (`m_business_date`, verified before and after — `out/db-after.txt`)

**Pre-write snapshot (NOT committed):**
`/Users/buv/gerege-oracle-snapshots/fineract_gerege-pre-ohwopaidau-write-20260911T054106Z.dump`
(4,818,080 bytes, magic `PGDMP`, `pg_restore -l` = 2,515 TOC entries). Taken with
`pg_dump -Fc` **from `gerege-oracle-db`** (not the stale `fineract-db-1`).

## Why a new loan, and not an existing one

`bin/step01-probe.sh` read every loan 1–12 and each schedule (`out/probe-summary.json`,
`out/probe-loans-db.txt`). The only loans that have **both** a fully paid instalment and at
least one unpaid instalment with principal are:

| loan | product | paid instalments | unpaid w/ principal | usable? |
|---|---|---|---|---|
| 3 | 2 (SEED-Probe-Loan, CASH) | P1 | 11 | **no** — its state is cited by committed `LN-L03-*` vectors |
| 12 | 3 (OHLGR-Accrual-Loan) | P1–P11 | 1 | **no** — pinned by committed `LN-L11`/`LN-L12` |

Loan 11 is already `601 closed.written.off`. Loans 1,2,4,5,6,9,10 have **no** fully paid
instalment; 7,8 are not active. So **no existing loan is both correctly shaped and unclaimed
by a committed vector** — hence create one on **product 3** (ACCRUAL PERIODIC), the same
product/accounting mapping the `LN-L11` write-off JE vector used.

## The loan used

**Loan 13** — `accountNo 000000013`, `externalId OHWOPAID-L01`, client 12
(`externalId OHWOPAID-C01`), product **3** `OHLGR-Accrual-Loan`, accounting **ACCRUAL
PERIODIC**. Created via the API chain, each request body committed under `req/`:

| step | request | response (HTTP 200) |
|---|---|---|
| client | `req/client-OHWOPAID-C01-create.json` | `clientId/resourceId 12` (`out/client-OHWOPAID-C01-create-raw.json`) |
| submit | `req/loan-OHWOPAID-L01-submit.json` | `loanId/resourceId 13` (`out/loan-OHWOPAID-L01-submit-raw.json`) |
| approve | `req/loan-OHWOPAID-L01-approve.json` | `status 200 approved` (`…-approve-raw.json`) |
| disburse | `req/loan-OHWOPAID-L01-disburse.json` | txn **55**, `status 300 active`, disbursed **2026-01-01** (`…-disburse-raw.json`) |
| repay P1 | `req/loan-13-repay-8884.88.json` | txn **56**, amount **8884.88**, P 7884.88 + I 1000.00 (`out/loan-13-repay-8884.88-raw.json`) |

The loan is a flat-12-month, principal 100000.00, 12%/yr, standard strategy, with two
instalment charges in the shape the write-off JE vector expects: charge **5** (fee, 100.00,
due 2026-02-15, period 2) and charge **4** (penalty, 57.00, due 2026-03-15, period 3). The
disbursement (2026-01-01) is far enough before the business date (2026-09-03) that period 1
is due 2026-02-01; repaying **exactly** period 1's total due (7884.88 + 1000.00 = **8884.88**)
on 2026-02-01 makes period 1 `complete: true` and leaves periods 2–12 unpaid.

## The schedule BEFORE the write-off (after the repayment)

`out/loan-13-after-repay-detail-raw.json` (`GET /loans/13?associations=all`, HTTP 200;
sha256 `722de3ad4de4906d03ecdbac890ccffb4077dfcd4df9dac741c3c3e1ab2b3b43`), cross-checked
read-only against `m_loan_repayment_schedule` in `out/db-after-repay.txt`.

Four outstanding buckets per instalment, in **minor units** (MNT = ISO 496, minor unit 2),
with the `complete` flag:

| period | due | complete | principal | interest | fee | penalty |
|---|---|---|---|---|---|---|
| **1** | 2026-02-01 | **true** | **0** | **0** | **0** | **0** |
| 2 | 2026-03-01 | false | 796373 | 92115 | 10000 | 0 |
| 3 | 2026-04-01 | false | 804337 | 84151 | 0 | 5700 |
| 4 | 2026-05-01 | false | 812380 | 76108 | 0 | 0 |
| 5 | 2026-06-01 | false | 820504 | 67984 | 0 | 0 |
| 6 | 2026-07-01 | false | 828709 | 59779 | 0 | 0 |
| 7 | 2026-08-01 | false | 836996 | 51492 | 0 | 0 |
| 8 | 2026-09-01 | false | 845366 | 43122 | 0 | 0 |
| 9 | 2026-10-01 | false | 853820 | 34668 | 0 | 0 |
| 10 | 2026-11-01 | false | 862358 | 26130 | 0 | 0 |
| 11 | 2026-12-01 | false | 870981 | 17507 | 0 | 0 |
| 12 | 2027-01-01 | false | 879688 | 8797 | 0 | 0 |

Loan summary after-repay: `principalOutstanding 92115.12`, `interestOutstanding 5618.53`,
`feeChargesOutstanding 100.00`, `penaltyChargesOutstanding 57.00`,
**`totalOutstanding 97890.65`**; all four `*WrittenOff = 0.0`; status `loanStatusType.active`
(300). DB: `m_loan.loan_status_id 300`, `total_outstanding_derived 97890.65`,
`total_writtenoff_derived 0`, `writtenoffon_date` NULL.

The fully paid period 1 (`obligations_met_on_date 2026-02-01`) had — **before** the repayment —
outstanding P **788488** + I **100000** (its charged principal/interest 7884.88 / 1000.00), as
recorded in `out/loan-13-before-detail-raw.json`
(sha256 `53e70267a9509fabcecfdca22e6fc809e7b1eb4f9b608fa8d4dda2743339ecea`). After the
repayment those four outstanding cells are all 0.

## The write

Request (`req/loan-13-writeoff.json`, 82 bytes, sha256
`c869b1c954b1301ba7ea72685866ede55b2676d3bd8acebaffe66becb3c1ee93`):

```
POST /loans/13/transactions?command=writeoff
{"transactionDate":"03 September 2026","locale":"en","dateFormat":"dd MMMM yyyy"}
```

Response (`out/loan-13-writeoff-raw.json`, HTTP 200 — `out/loan-13-writeoff.status`):

```json
{"officeId":1,"clientId":12,"loanId":13,"resourceId":57,
 "changes":{"transactionDate":"03 September 2026","locale":"en",
  "dateFormat":"dd MMMM yyyy","closedOnDate":"03 September 2026",
  "writtenOffOnDate":"03 September 2026",
  "status":{"id":601,"code":"loanStatusType.closed.written.off",
            "value":"Closed (written off)","active":false,
            "closedWrittenOff":true,"closed":true,"closedObligationsMet":false,"overpaid":false}}}
```

`resourceId 57` is the created write-off transaction.

## What the write-off transaction carried

`out/loan-13-after-transactions-raw.json`, transaction **id 57** — `type.id 6`,
`type.code loanTransactionType.writeOff`, date `2026-09-03`:

| field | value (MNT) | minor units |
|---|---|---|
| amount | 97890.65 | 9789065 |
| principalPortion | 92115.12 | 9211512 |
| interestPortion | 5618.53 | 561853 |
| feeChargesPortion | 100.00 | 10000 |
| penaltyChargesPortion | 57.00 | 5700 |
| outstandingLoanBalance | 0.00 | 0 |

DB (`m_loan_transaction`, `out/db-after.txt`): `id 57, transaction_type_enum 6,
transaction_date 2026-09-03, amount 97890.650000, principal_portion_derived 92115.12,
interest_portion_derived 5618.53, fee_charges_portion_derived 100, penalty_charges_portion_derived 57,
outstanding_loan_balance_derived 0`.

## The four buckets AFTER the write-off

`out/loan-13-after-detail-raw.json` (`GET /loans/13?associations=all`, HTTP 200; sha256
`ef1c34753994f76d70486b0a16deaa22a6af9da85d1285bdc11efda34240b6ab`), cross-checked in
`out/db-after.txt`. All four outstanding buckets are 0; per-instalment `writtenOff`:

| period | complete | principal writtenOff | interest writtenOff | fee writtenOff | penalty writtenOff |
|---|---|---|---|---|---|
| 1 (paid) | true | **0** | **0** | **0** | **0** |
| 2 | true | 796373 | 92115 | 10000 | 0 |
| 3 | true | 804337 | 84151 | 0 | 5700 |
| 4 | true | 812380 | 76108 | 0 | 0 |
| 5 | true | 820504 | 67984 | 0 | 0 |
| 6 | true | 828709 | 59779 | 0 | 0 |
| 7 | true | 836996 | 51492 | 0 | 0 |
| 8 | true | 845366 | 43122 | 0 | 0 |
| 9 | true | 853820 | 34668 | 0 | 0 |
| 10 | true | 862358 | 26130 | 0 | 0 |
| 11 | true | 870981 | 17507 | 0 | 0 |
| 12 | true | 879688 | 8797 | 0 | 0 |

Loan summary after: outstanding all 0, `principalWrittenOff 92115.12`,
`interestWrittenOff 5618.53`, `feeChargesWrittenOff 100.00`,
`penaltyChargesWrittenOff 57.00`, `totalWrittenOff 97890.65`. Status
`loanStatusType.closed.written.off` (601); `m_loan.loan_status_id 601`,
`writtenoffon_date 2026-09-03`, all four `*_outstanding_derived` zero, all four
`*_writtenoff_derived` set. `timeline.closedOnDate [2026,9,3]`. The paid period 1 is marked
written-off **0** everywhere; the write-off does not touch it.

Charges (`m_loan_charge`, after): both rows `amount_paid_derived` = amount (100.00 / 57.00),
`amount_outstanding_derived 0`, `is_paid_derived t` — the write-off settled the charges via
**amount_paid**, not `amount_writtenoff` (that column stays NULL).

## Journal entries — the five-leg reversing entry

`out/loan-13-{before,after}-journalentries-raw.json`
(`GET /journalentries?loanId=13&limit=80`). Before the write-off: **5** entries (disbursement
L55, repayment L56). After: **10**. The write-off adds exactly **5** entries (transaction
`L57`):

| JE id | txn | GL code | GL name | type | entry | amount |
|---|---|---|---|---|---|---|
| 150 | L57 | OHLGR-10010 | OHLGR-Loan-Portfolio | asset | **CREDIT** | 92115.12 |
| 151 | L57 | OHLGR-10012 | OHLGR-Interest-Receivable | asset | **CREDIT** | 5618.53 |
| 152 | L57 | OHLGR-10013 | OHLGR-Fees-Receivable | asset | **CREDIT** | 100.00 |
| 153 | L57 | OHLGR-10014 | OHLGR-Penalties-Receivable | asset | **CREDIT** | 57.00 |
| 154 | L57 | OHLGR-50010 | OHLGR-Losses-Written-Off | expense | **DEBIT** | 97890.65 |

One debit to the write-off expense for the full outstanding, credits to loan portfolio and
each of the three receivable accounts. There is **no accrual reversal** here (unlike loan 11)
because product 3's accrual is posted only at COB and no accrual had been posted before the
business date — all 10 entries are `reversed=false`.

## The arithmetic — the one line that grades the skip

In minor units, the write-off amount equals the sum over the **unpaid** instalments only:

```
9789065  =  Σ_{k=2..12} (principal_k + interest_k + fee_k + penalty_k)
         = 9211512 + 561853 + 10000 + 5700
```

The paid instalment (period 1) is `complete: true` and contributes **0** to each bucket, so a
correct port and the naive all-instalments port agree on **9789065** when the input is the
observed post-repayment schedule.

### Honest caveat on observability (important for the grading run)

`ObligationsMet` is set by Fineract iff the instalment's **total outstanding is zero**:
`LoanRepaymentScheduleInstallment.getTotalOutstanding()` sums the four outstanding buckets, and
`checkIfRepaymentPeriodObligationsAreMet` sets `obligationsMet = getTotalOutstanding().isZero()`.
Therefore a fully paid instalment **cannot** carry a non-zero outstanding bucket in any live
read-back — the skip is a mathematical no-op on the sum, and **no capture of a real write-off
can discriminate a port that merely forgets the skip while otherwise summing the observed
outstanding**. That is a property of the oracle, not a defect in this capture.

The capture still supplies everything needed to build a **discriminating** input if the vector
convention permits it: the paid period 1's four outstanding buckets **before** the repayment
are P 788488 + I 100000 (F 0, Pen 0), in `out/loan-13-before-detail-raw.json`, and its
`obligations_met: true` (`complete: true`) is observed in `out/loan-13-after-repay-detail-raw.json`.
A vector row for period 1 of `{obligations_met: true, principal_outstanding_minor: 788488,
interest_outstanding_minor: 100000, fee_outstanding_minor: 0, penalty_outstanding_minor: 0}`
plus the eleven observed unpaid rows would make a no-skip port over-count by exactly the paid
instalment: **9789065 + 888488 = 10677553** (= the loan's full scheduled total). The correct
port must return **9789065**.

## Money / units

MNT = ISO 496, minor unit 2. Every cell is a whole number of minor units:
`92115.12 → 9211512`, `5618.53 → 561853`, `100.00 → 10000`, `57.00 → 5700`,
total `97890.65 → 9789065`; paid instalment `7884.88 → 788488`, `1000.00 → 100000`.
**No sub-minor residue** (G-19 refuses it; DEC-2 predicate G-08).

## Byte-stability of request bodies

`bin/verify-req.sh` checks every `req/*.json` and fails on any decimal JSON number token.
All bodies are integer/string only: the write-off body carries **no numeric token at all**
(every value is a string), so it survives a binary-double round trip trivially. The repayment
amount is sent as the JSON **string** `"8884.88"`; the loan-create principal as `"100000"`.
`verify-req.sh` → `all request bodies integer/string only — byte-stable`.

## Writes

Exactly one API write performs the subject operation (the write-off); the client/loan
creation and the single repayment are the documented setup writes that make the shape. No SQL
insert; tenant `gerege` only; no `default` tenant write; no product/charge/client mutation
beyond creation; no `.go` file touched.

## Re-run / artifacts

- `bin/step01-probe.sh` — read-only probe (GETs + read-only SQL). Idempotent.
- `bin/step02-create.sh` … `bin/step04-repay.sh` — setup chain. Not idempotent against the
  live oracle (ids/state advance); re-run against the pre-write snapshot.
- `bin/step05-writeoff.sh` — the write-off + after-state. Not idempotent: the loan is already
  written off.
- `bin/capture-state.sh`, `bin/db-evidence.sh`, `bin/verify-req.sh` — capture + guards.

Raw JSON (single-line; cite at line 1) with `.status` companions (all 200):
`out/loan-13-{before,after-repay,after}-detail-raw.json`,
`out/loan-13-{before,after-repay,after}-transactions-raw.json`,
`out/loan-13-{before,after-repay,after}-journalentries-raw.json` (the write-off's
after-journalentries: sha256 `5178e96c3118e2b195472f944d5bbf0f0884941c67da8dedf1f36773c6a6536a`),
`out/loan-13-writeoff-raw.json`, `out/loan-13-repay-8884.88-raw.json`, plus the creation
responses. DB corroboration: `out/db-{before,after-repay,after}.txt`. No capture here is
inferred from a non-200 body.
