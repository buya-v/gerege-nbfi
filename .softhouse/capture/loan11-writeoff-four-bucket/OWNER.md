# OWNER — loan11-writeoff-four-bucket

**Subject:** the first live observation of the loan **write-off** discharging **all four**
outstanding buckets (principal, interest, fee, penalty) — so the rule below stops being
implementation-without-evidence:

> `writeoff.go:36` `WriteOffOutstanding` — a write-off discharges the whole outstanding
> principal/interest/fee/penalty and returns it so the caller can post the reversing entry.

`.softhouse/findings/F-2026-09-11-loan-graded-coverage.md` §4.1 recorded this as
**observation ABSENT**: no loan in the graded corpus is ever written off, and no capture
carried a non-zero `writtenOff`. This is the holds case with a different rule.

**Status: Complete.** `POST /loans/11/transactions?command=writeoff` → HTTP **200**. No
refusal. Exactly one write (the write-off); every other call is a GET.

## Oracle identity

- Fineract reference implementation, `https://localhost:8443/fineract-provider/api/v1`
- tenant `gerege`, Basic auth `mifos:password`
- containers `gerege-oracle-db` (PostgreSQL) + `gerege-oracle-app` (fineract)
- database `fineract_gerege`; **business date 2026-09-03**, COB date 2026-09-02
  (`m_business_date`)

**Pre-write snapshot (NOT committed):**
`/Users/buv/gerege-oracle-snapshots/fineract_gerege-pre-ohwocap-write-20260911T011014Z.dump`
(4,777,252 bytes, magic `PGDMP`, `pg_restore -l` = 2,500 TOC entries).

## The loan used, and why

**Loan 11** — `accountNo 000000011`, `externalId OHGLR-L02`, client 11, product **3**
`OHLGR-Accrual-Loan`, accounting **ACCRUAL PERIODIC**. It is the four-bucket twin of the
loan-12 capture, deliberately chosen so a port that writes off **only principal** (or
principal+interest) is catchable: fee `100.00` and penalty `57.00` are both non-zero and
**fee ≠ penalty**. Loan 12 is **not** used — its state is pinned by `LN-L11`/`LN-L12`.

The loan is active (`loan_status_id 300`), disbursed 2026-01-01, matures 2027-01-01, no
repayments ever made (`totalRepayment 0.00`), last transaction the 2026-09-02 accrual
(txn 46, interest 11.56) — so a write-off dated at the business date 2026-09-03 clears the
not-before-last-transaction rule and is not future-dated.

## The four buckets BEFORE (observed)

`out/loan-11-before-detail-raw.json` (`GET /loans/11?associations=all`, HTTP 200),
cross-checked read-only against `m_loan` in `out/db-before.txt`:

| bucket | value (MNT) | minor units |
|---|---|---|
| principal | 100000.00 | 10000000 |
| interest | 6618.53 | 661853 |
| fee | 100.00 | 10000 |
| penalty | 57.00 | 5700 |
| **totalOutstanding** | **106775.53** | **10677553** |

`principalWrittenOff = interestWrittenOff = feeChargesWrittenOff = penaltyChargesWrittenOff
= totalWrittenOff = 0.0`. Status `loanStatusType.active` (300).

Charges (`m_loan_charge`, before): id 5 (`charge_id 4`, `is_penalty=t`, amount 57.00,
outstanding 57.00, `is_paid=f`), id 6 (`charge_id 5`, `is_penalty=f`, amount 100.00,
outstanding 100.00, `is_paid=f`).

## The write

Request (`req/loan-writeoff.json`, 81 bytes):

```
POST /loans/11/transactions?command=writeoff
{"transactionDate":"03 September 2026","locale":"en","dateFormat":"dd MMMM yyyy"}
```

The command lives on the **transactions sub-resource**. `POST /loans/{id}?command=writeoff`
is refused HTTP 400 `error.msg.query.parameter.value.unsupported` (observed as `A2-228`);
the transactions form returned 200 as `A2-232`. Endpoint shape taken from that committed
observation, not re-derived from Java.

Response (`out/loan-writeoff-raw.json`, HTTP 200 — `out/loan-writeoff.status`):

```json
{"officeId":1,"clientId":11,"loanId":11,"resourceId":54,
 "changes":{"transactionDate":"03 September 2026","locale":"en",
   "dateFormat":"dd MMMM yyyy","closedOnDate":"03 September 2026",
   "writtenOffOnDate":"03 September 2026",
   "status":{"id":601,"code":"loanStatusType.closed.written.off",
             "value":"Closed (written off)","active":false,"closedWrittenOff":true,
             "closed":true,"closedObligationsMet":false,"overpaid":false}}}
```

`resourceId 54` is the id of the created write-off transaction.

## What the write-off transaction carried

`out/loan-11-after-transactions-raw.json`, transaction **id 54** — `type.id 6`,
`type.code loanTransactionType.writeOff`, date `2026-09-03`:

| field | value |
|---|---|
| amount | 106775.53 |
| principalPortion | 100000.0 |
| interestPortion | 6618.53 |
| feeChargesPortion | 100.0 |
| penaltyChargesPortion | 57.0 |
| outstandingLoanBalance | 0.0 |

DB (`m_loan_transaction`, `out/db-after.txt`): `id 54, transaction_type_enum 6,
transaction_date 2026-09-03, amount 106775.530000, principal_portion_derived 100000,
interest_portion_derived 6618.530000, fee_charges_portion_derived 100, penalty_charges_portion_derived 57,
outstanding_loan_balance_derived 0`.

## The four buckets AFTER (observed)

`out/loan-11-after-detail-raw.json` (`GET /loans/11?associations=all`, HTTP 200),
cross-checked in `out/db-after.txt`:

| bucket | outstanding | writtenOff |
|---|---|---|
| principal | 0.00 | 100000.00 |
| interest | 0.00 | 6618.53 |
| fee | 0.00 | 100.00 |
| penalty | 0.00 | 57.00 |
| **total** | **0.00** | **106775.53** |

Status `loanStatusType.closed.written.off` (id 601); `m_loan.loan_status_id 601`,
`writtenoffon_date 2026-09-03`, all four `*_outstanding_derived` zero and all four
`*_writtenoff_derived` set to the amounts above. Loan detail `timeline.closedOnDate`
= `[2026,9,3]`.

Charges (`m_loan_charge`, after): both rows are now `amount_paid_derived` = amount
(57.00 / 100.00), `amount_outstanding_derived 0`, `is_paid_derived t`. Note the write-off
settled the charges via **amount_paid**, not `amount_writtenoff` (that column stays NULL).

## Journal entries — the reversing entry is half the result

`out/loan-11-{before,after}-journalentries-raw.json`
(`GET /journalentries?loanId=11&limit=80`). Before: **24** entries; after: **31**
(`totalFilteredRecords`).

The write-off adds **7** entries. The 5 that reverse the four buckets (transaction `L54`,
the write-off):

| JE id | txn | GL code | GL name | type | entry | amount |
|---|---|---|---|---|---|---|
| 140 | L54 | OHLGR-50010 | OHLGR-Losses-Written-Off | expense | **DEBIT** | 106775.53 |
| 136 | L54 | OHLGR-10010 | OHLGR-Loan-Portfolio | asset | CREDIT | 100000.0 |
| 137 | L54 | OHLGR-10012 | OHLGR-Interest-Receivable | asset | CREDIT | 6618.53 |
| 138 | L54 | OHLGR-10013 | OHLGR-Fees-Receivable | asset | CREDIT | 100.0 |
| 139 | L54 | OHLGR-10014 | OHLGR-Penalties-Receivable | asset | CREDIT | 57.0 |

So the caller-side reversing entry is: **one debit to the write-off expense** for the full
outstanding, **credits** to loan portfolio and each of the three receivable accounts. A
port that debits only the principal, or that omits an interest/fee/penalty credit line, is
caught by these five lines.

The other 2 new entries are a side effect (below).

## Side effect observed: the last accrual is reversed by the write-off

Transaction **46** (accrual, 2026-09-02, interest 11.56) is `is_reversed = t` after the
write-off, with `reversedOnDate 2026-09-03`; the write-off adds the matching reversal JE:

| JE id | txn | GL code | GL name | type | entry | amount |
|---|---|---|---|---|---|---|
| 134 | L46 | OHLGR-10012 | OHLGR-Interest-Receivable | asset | CREDIT | 11.56 |
| 135 | L46 | OHLGR-40010 | OHLGR-Interest-On-Loans | income | DEBIT | 11.56 |

This is part of the write-off operation, not a separate write: `m_loan_transaction` id 46
`last_modified_on_utc = 2026-09-11 01:11:44.052097+00`, 34 ms after the write-off
transaction 54 `created_on_utc = 2026-09-11 01:11:44.018259+00`. The write-off transaction
still carried the **pre-reversal** interest (6618.53), so Interest-Receivable ends the day
net-credited (total DR 5759.07 from the nine accruals vs total CR 11.56 + 6618.53 =
6630.09 → net CR 871.02). Graded ports must reproduce both the accrual reversal and the
full-interest write-off credit if they are to match the oracle here.

## Evidence that a port writing off only principal is catchable

Before, all four buckets are non-zero and `fee (100.00) ≠ penalty (57.00)`. The write-off
transaction carries all four portions; the after-state sets all four `*_writtenoff_derived`;
the reversing JE has one credit line per bucket. A principal-only port diverges on six
independent cells (three portions × transaction + three written-off summaries + three JE
credits).

## Money / units

MNT = ISO 496, minor unit 2. Every cell is a whole number of minor units:
`100000.00 → 10000000`, `6618.53 → 661853`, `100.00 → 10000`, `57.00 → 5700`,
total `10677553`. **No sub-minor residue** (G-19 refuses it; DEC-2 predicate G-08).

## Byte-stability of request bodies

`req/loan-writeoff.json` carries **no numeric JSON token** — every value is a string
(`transactionDate`, `locale`, `dateFormat`), so nothing is routed through `json.dumps` of a
parsed number and the body survives a binary-double round trip trivially (the failure mode
that reverted a salvage over `100.00 -> 100.0` cannot occur). Verified:
`json.dumps(json.loads(b), separators=(',',':')) == b` → True, and no non-string values.

## Writes

Exactly one, via the API: `POST /loans/11/transactions?command=writeoff`. No SQL insert, no
`default` tenant write, no product/charge/client mutation, no `.go` file touched.

## Re-run / artifacts

- `bash bin/step01-before.sh` — the before-state (GETs + read-only SQL). Idempotent.
- `bash bin/step02-writeoff.sh` — the write-off + after-state. **Not** idempotent: re-running
  against the live oracle fails (loan already written off). Run against the pre-write
  snapshot above for a byte-identical re-capture.

Raw files: `out/loan-11-{before,after}-{detail,transactions,journalentries}-raw.json` with
`.status` companions (all 200), `out/db-{before,after}.txt`, `out/loan-writeoff-raw.json`,
`out/loan-writeoff.status`, `req/loan-writeoff.json`. The `*.status` files are the
cross-check; no capture here is inferred from a non-200 body.
