# OH-WOGRADE-W — grade the write-off. The observation is on disk. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-wograde` (branch `feat/OHWOGRADEw`)
Work ONLY in that directory. **Take no captures. Issue no POST/PUT/DELETE.**

**A run works ONLY in its own worktree.** `/Users/buv/gerege-nbfi` is the driver's checkout
— do not read or write there, and **never exercise the push gate**. The driver pushes.

## The second half of a split

`OH-WOCAP-V` captured the first write-off in the programme's history; **you grade it.**
Before it, `WriteOffOutstanding` [`nexus/internal/apps/loan/writeoff.go:36`] was
implemented and had **no observation anywhere** — `OH-LOANCOV-T`'s triage
(`.softhouse/findings/F-2026-09-11-loan-graded-coverage.md` §4.1) called it the holds case
with a different rule.

## THE PORT — read it, it is short

    func WriteOffOutstanding(installments []WriteOffInstallment) Allocation {
        for _, in := range installments {
            if in.ObligationsMet { continue }          // skip paid-off instalments
            a.Principal += in.PrincipalOutstanding
            a.Interest  += in.InterestOutstanding
            a.Fee       += in.FeeOutstanding
            a.Penalty   += in.PenaltyOutstanding
        }
    }

It ports `AbstractLoanRepaymentScheduleTransactionProcessor.handleWriteOff`
[`…java:764-788`]. The four returned buckets become the write-off transaction's portions.

## THE OBSERVATION

`.softhouse/capture/loan11-writeoff-four-bucket/` — **read its `OWNER.md` first.** Loan 11
(product 3, ACCRUAL PERIODIC), written off at business date 2026-09-03:

    write-off txn 54, amount 106775.53, portions:
      principal  100000.00 -> 10000000
      interest     6618.53 ->   661853
      fee           100.00 ->    10000
      penalty        57.00 ->     5700
      total                    10677553
    after: all four outstanding buckets 0; status closed.written.off (601)

`out/loan-11-before-detail-raw.json` (`associations=all`) carries the **repayment schedule**
— the per-instalment input `WriteOffOutstanding` consumes. **Verify every figure against the
files before building on it.**

## The task — ONE property

> **A write-off discharges the outstanding of every unpaid instalment into ALL FOUR
> buckets, and the four portions sum to the write-off amount.**

Fee `10000` and penalty `5700` are **non-zero and DIFFERENT**, so the defects worth a drive
are all discriminated:
* writes off **only principal** (or principal + interest);
* drops the fee bucket, or the penalty bucket;
* swaps fee and penalty (they differ, so a swap cannot hide).

Promote a vector whose request is the observed per-instalment schedule and whose expect is
the four observed portions, register drives for the defects above, and **measure each
against the store WITHOUT your vector and WITH it.**

**And confirm with coverage** — `WriteOffOutstanding` reads **0.0%** from the graded corpus
today:

    go test -coverpkg=./internal/apps/loan -coverprofile=/tmp/c.cov ./internal/apps/loan/conformance/...
    go tool cover -func=/tmp/c.cov | grep WriteOffOutstanding

The loan committed-store test (`OH-LOANCOV-T`) makes this real. If it still reads 0.0% after
your change, your vector does not reach the rule — say so rather than claim it is graded.

## WHAT YOU CANNOT GRADE — say so, do not pretend

**The `ObligationsMet` skip.** It matters only if some instalment is already fully paid.
**Check the schedule**: if loan 11 has no instalment with obligations met (it had accruals
but, as far as the driver knows, no repayment), then a port that forgets the skip sums the
same numbers and **a drive for it kills zero**. Do not register it. Record what a capture
would need — a loan with at least one fully-paid instalment, then written off.

**Out of scope for this run, both recorded in `OWNER.md` for later:** the five-leg journal
entry L54 (`DEBIT Losses-Written-Off` / four credits) and the **reversing accrual** the
write-off posted (txn 46, JE 134/135 — `CLAUDE.md`: "Corrections are reversing entries").
Each deserves its own run. **Do not touch them here.**

## THE RULE ON INERT DRIVES
**A drive that kills ZERO is a finding to resolve** — promote a vector that sees it, or
**delete it with the argument**. Report every kill count. **Do not manufacture coverage.**

## Measuring it
    kills.sh loan loan-wrong-delinquency-thirty-day-month     -> 3
    kills.sh loan loan-wrong-summary-drops-penalty            -> 2
    kills.sh savings savings-wrong-hold-folded-into-balance   -> 1
    kills.sh loanschedule loanschedule-wrong-days-in-year-365 -> 45

**Repaired 2026-09-09**: no silent `0` — exit 2, empty stdout, reason on stderr. **An empty
result means the MEASUREMENT FAILED.** **FLAGS ARE PER-BINARY.** Use `kills.sh`.

After your change `loan-go` must pass **all 24** loan vectors, **all 26** loan drives must
still kill, and the loan committed-store test must pass.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float in any money path, including intermediates.
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08.
- **HALF_UP**, ordinal 4, precision 19, `Asia/Ulaanbaatar`.
- **Do not touch `.softhouse/guards/ledger-invariants.baseline`** (12 pairs) or
  `.softhouse/conformance.sh` (census **17**).
- **PostgreSQL only.** "The oracle" is the Fineract reference implementation; **Oracle
  Database is prohibited.**
- **One bounded context: `loan`.**
- `capture_ref`, `capture_sha256`, `citation`; **re-verify the hash after writing**. Never
  synthesise a value you did not observe. Cite `file:line` from the FILE.

## The bar and the budget
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` — exit 2 as the §4.4.2
recorded decision, ledger findings **12 pairs**, census **17**. Run it EARLY.

~500 iterations for a pure grading task. **Commit by iteration 120.**
