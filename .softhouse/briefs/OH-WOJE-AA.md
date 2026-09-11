# OH-WOJE-AA — port and grade the write-off's journal entry. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-woje2` (branch `feat/OHWOJEaa2`)
Work ONLY in that directory. **Take no captures. Issue no POST/PUT/DELETE.**

**A run works ONLY in its own worktree.** `/Users/buv/gerege-nbfi` is the driver's checkout —
do not read or write there, and **never exercise the push gate**. The driver pushes.

## Where this sits

`OH-WOGRADE-W` graded the write-off's four PORTIONS (`WriteOffOutstanding`). `OH-REVERSAL-X`
graded the accrual reversal the write-off triggered. What is left of loan 11's write-off is
**where the money lands in the ledger** — the five-leg journal entry L54. No port in the tree
produces it.

## THE OBSERVATION — `.softhouse/capture/loan11-writeoff-four-bucket/` (read `OWNER.md` §"Journal entries")

`out/loan-11-after-journalentries-raw.json`, transaction `L54`, in id order:

    136  OHLGR-10010 Loan-Portfolio         CREDIT  100000.00 -> 10000000
    137  OHLGR-10012 Interest-Receivable    CREDIT    6618.53 ->   661853
    138  OHLGR-10013 Fees-Receivable        CREDIT     100.00 ->    10000
    139  OHLGR-10014 Penalties-Receivable   CREDIT      57.00 ->     5700
    140  OHLGR-50010 Losses-Written-Off     DEBIT   106775.53 -> 10677553

**Verify every figure against the file.** The four credits sum to the one debit.

## THE RULE — port it

`AccrualBasedAccountingProcessorForLoan.createJournalEntriesForLoanWriteOffs`
[pinned `/Users/buv/fineract` @ `426a23544`,
`fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/service/AccrualBasedAccountingProcessorForLoan.java:1872-1976`],
reached at `:108-109` and `:1379-1385` (the NOT-charged-off branch). **Read it.** In short:
for each portion (principal, interest, fees, penalties, overpayment) that is **> 0**, add it to
the total and credit its slot's GL account — `LOAN_PORTFOLIO`, `INTEREST_RECEIVABLE`,
`FEES_RECEIVABLE`, `PENALTIES_RECEIVABLE`, `OVERPAYMENT` — **merging portions whose slots map
to the SAME account** (`accountMap`, `:1891`); post the credits in that insertion order; then
ONE debit of the total to `LOSSES_WRITTEN_OFF` (or to the write-off-reason mapping when one is
set, `:1963-1975`).

**THE MAPPING IS HERE — do not search for it** (a first attempt at this brief spent 420
events grepping for `acc_product_mapping` and found nothing, because the evidence is REST, not
SQL): `.softhouse/capture/investor-asset-transfer-100/out/loanproduct-3-raw.json` —
`GET /loanproducts/3` on TODAY's oracle instance, `accountingMappings`:

    loanPortfolioAccount       OHLGR-10010 Loan-Portfolio        (slot LOAN_PORTFOLIO)
    receivableInterestAccount  OHLGR-10012 Interest-Receivable   (slot INTEREST_RECEIVABLE)
    receivableFeeAccount       OHLGR-10013 Fees-Receivable       (slot FEES_RECEIVABLE)
    receivablePenaltyAccount   OHLGR-10014 Penalties-Receivable  (slot PENALTIES_RECEIVABLE)
    overpaymentLiabilityAccount OHLGR-20011 Overpayment-Liability (slot OVERPAYMENT)
    writeOffAccount            OHLGR-50010 Losses-Written-Off    (slot LOSSES_WRITTEN_OFF)

Cite it by path and sha256. **Do NOT use `.softhouse/capture/tierA-a2/`** — it came from an
EARLIER oracle instance; its product ids name different products. **Never invent a mapping.**

Port it into `nexus/internal/apps/loan/` as a pure function: portions (integer minor units) +
slot→account mapping → legs (`JournalEntryLeg`, `journalbatch.go`). Cite `file:line`.

## The task — ONE property

> **A write-off credits each non-zero portion to its own receivable slot and debits the total
> ONCE to the losses-written-off slot.**

Promote ONE vector (request: the four portions from txn 54 and the product-3 slot mapping;
expect: the five L54 legs in order). Drives a reasonable porter might write, each discriminated
by this observation:
* **one debit per portion** — four debits instead of one. Batch still balances; leg count and
  sides do not.
* **debits the principal only** — the debit is 10000000, the batch no longer balances.
* **debits loan portfolio instead of losses-written-off** — the account cell.
* **swaps the fee and penalty receivable slots** — fee 10000 ≠ penalty 5700, so it cannot hide.

**Measure each drive against the store WITHOUT your vector and WITH it.** Report every count.

## WHAT THIS OBSERVATION CANNOT GRADE — say so, do not register a drive
* **The same-account merge** (`accountMap`): product 3 maps the four slots to four DIFFERENT
  accounts, so a port that never merges posts the same five legs. Record what capture would see it.
* **The zero-portion skip**: every portion here is > 0.
* **Overpayment** and **the write-off-reason mapping**: absent here.
* **The charged-off branch** (`:1616`): loan 11 was not charged off.

## Coverage
    go test -count=1 -coverpkg=./internal/apps/loan -coverprofile=/tmp/c.cov ./internal/apps/loan/conformance/...
    go tool cover -func=/tmp/c.cov | grep -i writeoff

Your new function must read well above 0% from the committed-store test, or say why not.

## THE RULE ON INERT DRIVES
**A drive that kills ZERO is a finding to resolve** — promote a vector that sees it, or **delete
it with the argument**. **Do not manufacture coverage.**

## Measuring it
    kills.sh loan loan-wrong-reversal-flags-originals         -> 1
    kills.sh loan loan-wrong-writeoff-drops-fee               -> 1
    kills.sh loan loan-wrong-delinquency-thirty-day-month     -> 3
    kills.sh loanschedule loanschedule-wrong-days-in-year-365 -> 45

**An empty result means the MEASUREMENT FAILED.** **FLAGS ARE PER-BINARY.** Use
`kills.sh <context> <impl> <worktree>`. After your change `loan-go` must pass **all 26** loan
vectors plus yours, **all 35** loan drives must still kill, the committed-store test must pass.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float in any money path, including intermediates.
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08.
- **HALF_UP**, ordinal 4, precision 19, `Asia/Ulaanbaatar`.
- **Do not touch `.softhouse/guards/ledger-invariants.baseline`** (12 pairs), `.softhouse/conformance.sh`
  (census **17**), or `nexus/internal/apps/ledger/` (another run is working there).
- **PostgreSQL only.** "The oracle" is the Fineract reference; **Oracle Database is prohibited.**
- **One bounded context: `loan`.**
- `capture_ref`, `capture_sha256`, `citation`; **re-verify the hash after writing**.

## The bar, the budget, and how to commit
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` — exit 2 as the §4.4.2
recorded decision, ledger findings **12 pairs**, census **17**. Run it EARLY.

~500 iterations. **Commit by iteration 120.** **Write the commit message to a file and use
`git commit -F <file>`** — a long `-m "…"` wedged the last run's terminal inside an unclosed quote.
