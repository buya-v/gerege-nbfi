# OH-SAVRB-AB — grade the savings running balance across a hold. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-savrb` (branch `feat/OHSAVRBab`)
Work ONLY in that directory. **Take no captures. Issue no POST/PUT/DELETE.**

**A run works ONLY in its own worktree.** `/Users/buv/gerege-nbfi` is the driver's checkout —
do not read or write there, and **never exercise the push gate**. The driver pushes.

## What the driver measured

Coverage of `savings` from the graded corpus (the committed-store test `OH-HOLDGRADE-S` built):

    go test -count=1 -coverpkg=./internal/apps/savings -coverprofile=/tmp/c.cov ./internal/apps/savings/conformance/...

`HoldNetRunningBalancesOf` [`nexus/internal/apps/savings/summary.go:504`] reads **0.0%**. It is
a money rule — the oracle's `running_balance_derived` chain, where a HOLD subtracts and a RELEASE
adds back [`SavingsAccount.java:902,912`, cited in its doc comment] — unit-tested against rows
but **graded by no vector.** Read its doc comment in full; it explains why this column is NOT
the posted balance and why porting it does not violate "holds alter available only".

## THE OBSERVATION — `.softhouse/capture/savings-hold-release/` (read `OWNER.md` first)

`out/db-after-release.txt`, `m_savings_account_transaction`, savings account 1:

    id|type|amount|running_balance_derived|release_id
    1 | 1  | 1000.00 | 1000.00 |
    2 | 3  |    0.16 | 1000.31 |
    3 | 3  |    0.15 | 1000.15 |
    6 | 20 |  137.29 |  863.02 | 7      <- AMOUNT_HOLD
    7 | 21 |  137.29 | 1000.31 |        <- AMOUNT_RELEASE

**The chain runs in the oracle's TRANSACTION ORDER, not id order**: 1000.00 + 0.15 = 1000.15
(id 3), + 0.16 = 1000.31 (id 2). Find the ordering the oracle uses (transaction date, then id —
read the source and the capture's dates; `OWNER.md` records the observed before-transaction
dates) and transcribe it. **Never reorder by guess.** Also check `db-after-hold.txt` — the same
chain one step earlier, before the release existed.

## The task — ONE property

> **The stored running balance moves DOWN by a hold and back UP by its release, while the posted
> balance does not move at all.**

Promote ONE vector (request: the account's transactions in the oracle's order, as integer minor
units and stored types; expect: the running balance on every row —
`100000, 100015, 100031, 86302, 100031` in that order, IF your reading of the files agrees).
Grade the posted balance (`AccountBalanceOf`, 100031) alongside, in the same vector if the seam
allows, so the vector states both halves of the property.

Drives worth registering, each discriminated here:
* **the running balance ignores holds** — the reading of `CLAUDE.md` a careful porter would
  make. Hold row reads 100031, not 86302.
* **ignores releases** — release row reads 86302, not 100031.
* **a hold is a credit** — hold row reads 113360.
* **chains in id order** — ids 2/3 carry 100016 / 100031 instead of 100031 / 100015.

**Measure each drive against the store WITHOUT your vector and WITH it.** Report every count.
And re-measure coverage: `HoldNetRunningBalancesOf` must move off 0.0%, or say why not.

## WHAT THIS CANNOT GRADE — say so
The void-row branch (no void row here) and escheat (none here). The doc comment names
CAPTURE-A / CAPTURE-B for those — if they are committed captures, say whether a vector could
promote them; if not, say what a capture would need. **Do not register a drive nothing kills.**

## Measuring it
    kills.sh savings savings-wrong-hold-folded-into-balance   -> 1
    kills.sh loanschedule loanschedule-wrong-days-in-year-365 -> 45
    kills.sh parties parties-wrong-iota-ordinals              -> 12

**An empty result means the MEASUREMENT FAILED.** **FLAGS ARE PER-BINARY.** Use
`kills.sh <context> <impl> <worktree>`. After your change `savings-go` must pass **all 8**
savings vectors plus yours, every savings drive must still kill, and the committed-store test
must pass.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float in any money path, including intermediates.
  The capture stores `1000.310000` — transcribe as `100031`, never through a float.
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08.
- **Holds alter `available` only, never the posted balance.** The running-balance column is not
  the posted balance — keep them apart in the vector exactly as the doc comment does.
- Savings/deposit code **ships disabled**, and **never describe member savings as insured,
  protected or guaranteed** in any string you write.
- **Do not touch `.softhouse/guards/ledger-invariants.baseline`** (12 pairs), `.softhouse/conformance.sh`
  (census **17**), or `nexus/internal/apps/loan/` (another run is working there).
- **PostgreSQL only.** "The oracle" is the Fineract reference; **Oracle Database is prohibited.**
- **One bounded context: `savings`.**
- `capture_ref`, `capture_sha256`, `citation`; **re-verify the hash after writing**.

## The bar, the budget, and how to commit
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` — exit 2 as the §4.4.2
recorded decision, ledger findings **12 pairs**, census **17**. Run it EARLY.

~400 iterations. **Commit by iteration 120.** **Write the commit message to a file and use
`git commit -F <file>`** — a long `-m "…"` wedged a run's terminal inside an unclosed quote.
