# OWNER — loan12-four-bucket-allocation

**Subject:** the four-bucket (penalty, fee, interest, principal) *allocation* of a loan
repayment, captured on an existing loan whose buckets are all non-zero and where
**fee ≠ penalty**.

**Why this capture exists.** `LAB-L03` — `.softhouse/vectors/loan/LN-L03-repayment-allocation.json`
— is the only vector that grades the allocation seam, and its `request.repayment.outstanding`
and `expect.allocation` both carry `fee = "0"` and `penalty = "0"`. A port that drops the
fee bucket, the penalty bucket, or both, passes `LAB-L03`: adding zero is
indistinguishable from not adding. This is the ALLOCATION twin of
`.softhouse/findings/F-2026-09-09-fee-penalty-blind.md` (which was about the summary SUM).

**The observation.** One repayment on the existing **loan 12** (`OHLGT-L03`, product 3,
client 11), which carries all four outstanding buckets non-zero and different:

    before:  principal 100000.00  interest 6618.53  fee 100.00  penalty 57.00  = 106775.53
    repayment 53 (2026-09-02): amount 97978.65
      penalty 57.00  fee 100.00  interest 6618.53  principal 91203.12  = 97978.65
    after:   principal   8796.88  interest 0.00  fee 0.00  penalty 0.00  =   8796.88

**Why this amount.** 97978.65 MNT (9797865 minor) is `sum(instalments 1..11) + period-12
interest` = 9789068 + 8797. The product uses `mifos-standard-strategy`, whose processor
walks instalments and within each pays penalty → fee → interest → principal
(`FineractStyleLoanRepaymentScheduleTransactionProcessor.java:104-114`). Period 2 is the
loan's only fee-bearing instalment (fee 100.00) and period 3 its only penalty-bearing one
(penalty 57.00). The amount is chosen so that every penalty, fee and interest cell is
fully consumed while 8796.88 of principal is left outstanding — so all four result
buckets are non-zero and the split demonstrably is not a dump into one bucket. Because
the entire penalty/fee/interest pool is consumed, the observed per-bucket portions equal
the greedy four-bucket allocation of the loan-level pool, which is exactly the shape the
port (`nexus/internal/apps/loan/allocation.go`) computes.

**Request bodies are byte-stable.** The single request body carries no numeric JSON token
at all: `transactionAmount` and `transactionDate` are JSON strings. Nothing is routed
through `json.dumps` of a parsed number, so the body survives a binary-double round trip
trivially. This is why the `gl-accounting-surface` body (which carried `100.00`) was
refused by the wire-float guard and this one is not.

**Writes.** Exactly one, via the API: `POST /loans/12/transactions?command=repayment`.
No SQL insert, no `default` tenant write, no product/charge/client mutation. A
`pg_dump -Fc` pre-write snapshot is at
`/Users/buv/gerege-oracle-snapshots/fineract_gerege-pre-ohallocg-write-20260910T083113Z.dump`.

**Oracle identity.** Fineract at `https://localhost:8443/fineract-provider/api/v1`, tenant
`gerege`, PostgreSQL container `gerege-oracle-db`, database `fineract_gerege`. Oracle
business date at capture: 2026-09-02 (`m_loan.last_closed_business_date`).

**Re-run.** `bash bin/step01-capture.sh` (additive: it POSTs one repayment and GETs the
read-backs; re-running against this snapshot would create a second repayment, so run it
against the pre-write snapshot above if a byte-identical re-capture is needed).
