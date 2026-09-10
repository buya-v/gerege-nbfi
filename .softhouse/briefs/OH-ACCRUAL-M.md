# OH-ACCRUAL-M — one receivable/income pair PER CHARGE FAMILY. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-accrualm` (branch `feat/OHACCRUALm`)
Work ONLY in that directory. **Take no captures. Issue no POST/PUT/DELETE.** Everything is
promotable from captures already committed on `main`.

## WHY THIS IS THE cob GAP, GRADED IN THE RIGHT PLACE

`cob` has 6 vectors, all on one seam (`cob-business-step-order`), and 222 Go LOC against
13,471 Java. That looks like the thinnest context in Tier A. **It mostly is not a defect.**
COB is an **orchestrator**: its job is to run business steps in order, which is exactly what
those 6 vectors grade. Its MONEY effects land in the postings the steps produce, and a
loan-produced journal-entry read-back belongs in `loan` — see
`.softhouse/findings/F-2026-09-10-vector-schema-mismatch.md`, which settled that a
read-back does not fit a seam built for a posting command.

**So grade COB's money where it lands: the accrual postings, on the existing `loan` seam.**

## THE OBSERVATION

`.softhouse/capture/loan12-four-bucket-allocation/out/journalentries-loan-12-after-raw.json`
holds accrual transactions that carry **more than one charge family**, each family with its
**own receivable/income pair**:

    L25  OHLGR-Interest-Receivable    DEBIT   921.15
         OHLGR-Interest-On-Loans      CREDIT  921.15      <- interest family
         OHLGR-Fees-Receivable        DEBIT   100.00
         OHLGR-Income-From-Fees       CREDIT  100.00      <- fee family

    L30  OHLGR-Interest-Receivable    DEBIT   841.51
         OHLGR-Interest-On-Loans      CREDIT  841.51      <- interest family
         OHLGR-Penalties-Receivable   DEBIT    57.00
         OHLGR-Income-From-Penalties  CREDIT   57.00      <- penalty family

**Verify both against the file before building on them.**

> **An accrual posts one RECEIVABLE-debit / INCOME-credit pair PER CHARGE FAMILY, and each
> family uses its OWN account pair.**

**A port that routes all accrual income to a single account still balances, still gets every
side right, and still has the correct totals.** That is the defect, and nothing catches it:

* `LN-L09` grades a **disbursement** — two pairs across two transactions;
* `LN-L12` grades a **repayment** — five legs, one transaction, four credits and one debit;
* an **accrual** is a third shape — four legs, one transaction, **two balanced pairs across
  two families**. Neither existing vector has it.

## THE MAP

* **Seam** — `loan-journal-entry-batch-balance`
  (`nexus/internal/apps/loan/journalbatch.go`, `LN-L09`, `LN-L12`).
* **Admission already fits — do NOT widen it.** `OH-REPAYJE-H` set the predicate to
  `multiPair || multiLegDistinctCredits`, where the second is
  `len(seenTxn)==1 && legs>=3 && creditAccounts>=2`. **L25 alone satisfies it**: one
  transaction, four legs, two distinct credit accounts. **Check this yourself**; if it holds,
  change nothing in `admit.go`. The one-pair refusal must stay intact — it is `OH-JE-C`'s
  structural guard and two runs have now preserved it deliberately.
* **Registration** — `nexus/internal/apps/loan/conformance/impl.go`, **23** worked
  `loan-wrong-*` examples.
* **Cross-reference** — `OH-MAP-E` graded the *account-pair* property for a disbursement
  vs a fee. This is the same class across **three** families (interest, fees, penalties);
  read `loan-wrong-journal-entry-batch-maps-fee-to-disbursement-accounts` first and say
  whether it already covers the accrual case. **"Already covered" is a finding.**

## THE RULE ON INERT DRIVES
**A drive that kills ZERO is a finding to resolve** — promote a vector that sees it, or
**delete it with the argument**. Report every kill count and prove the instrument was live.
**Do not manufacture coverage.** `OH-LSDRIVE-I` deleted a zero-kill drive and recorded why;
`OH-SHARES-K` and `OH-COLL-L` measured their new drives against BOTH the old and the new
store to prove the gap was real. **Do that here**: run any new drive against the store
without your vector and with it.

## Measuring it
    kills.sh loan loan-wrong-journal-entry-batch-collapses-credits-to-one-account -> 1
    kills.sh loan loan-wrong-summary-drops-penalty                                -> 2
    kills.sh collateral collateral-wrong-pct-hardcoded                            -> 1
    kills.sh loanschedule loanschedule-wrong-days-in-year-365                     -> 45

**Repaired 2026-09-09**: no silent `0` — exit 2, empty stdout, reason on stderr. **An empty
result means the MEASUREMENT FAILED.** If a control is wrong, the instrument is wrong.
**FLAGS ARE PER-BINARY** — `-root` is required by most and rejected by loanschedule's;
`-oracle-probe` exists on some and makes the charges binary print usage. Use `kills.sh`.

After your change `loan-go` must still pass **all** loan vectors and **all 23** existing
drives must still kill. That is your primary control.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float in any money path, including intermediates.
  `921.15` transcribes to `92115`. MNT = ISO 496, minor unit 2.
- **Double-entry, append-only. Balances DERIVED, never written** (I-3/I-4).
- **HALF_UP**, ordinal 4, precision 19, `Asia/Ulaanbaatar`.
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08.
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

~500 iterations for ONE property. **Commit by iteration 120** — the last seven runs on this
shape committed between ~71 and ~190.
