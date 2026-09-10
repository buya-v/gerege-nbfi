# OH-HOLDGRADE-S — grade the hold. A non-negotiable, with the observation on disk. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-holdgrade` (branch `feat/OHHOLDGRADEs`)
Work ONLY in that directory. **Take no captures. Issue no POST/PUT/DELETE.**

**A run works ONLY in its own worktree.** `/Users/buv/gerege-nbfi` is the driver's checkout
— do not read or write there, and **never exercise the push gate**. The driver pushes.
(`.softhouse/briefs/README.md`.)

## WHAT YOU ARE GRADING, AND WHY IT IS NOT ORDINARY

`CLAUDE.md` line 14 is a **non-negotiable**:

> **Holds are postings and alter `available` only, never posted `balance`.**

That rule has a full implementation in the savings port and **the conformance harness has
never reached it**. Measured with the right instrument — coverage of the port, run from the
conformance package:

    function                    unit tests    FROM CONFORMANCE
    AccountBalanceOf              100.0%          0.0%
    AvailableOf                   100.0%          0.0%
    HeldOf                         92.9%          0.0%
    HoldNetRunningBalancesOf       92.9%          0.0%
    [nexus/internal/apps/savings/summary.go:228, :379, :315, :504]

**Well unit-tested; completely ungraded.** A unit test proves the code does what its author
intended; only a vector proves it matches the oracle. See
`.softhouse/findings/F-2026-09-10-savings-holds-ungraded.md` — including its own correction,
which is why the coverage form above is the instrument and a grep is not.

`OH-HOLDCAP-R` captured the missing observation. **You grade it.**

## THE OBSERVATION — committed, verified, with the arithmetic

`.softhouse/capture/savings-hold-release/` (read its `OWNER.md`). Savings account **1**:

    state          posted balance     available
    before            1000.31          1000.31
    after hold        1000.31           863.02
    after release     1000.31          1000.31

    AMOUNT_HOLD row: transaction id 6, type 20, flag `amountHold`, amount 137.29
    other rows: id 1 deposit 1000.00 (type 1); id 2 interest 0.16, id 3 interest 0.15 (type 3)

**The whole property falls out of those rows, and you should re-derive it rather than
trust this brief:**

    AccountBalanceOf = 1000.00 + 0.16 + 0.15 = 1000.31   <- the HOLD CONTRIBUTES NOTHING
    HeldOf           = 137.29 after the hold, 0 after the release
    AvailableOf      = balance - held = 1000.31 - 137.29 = 863.02

    100031 - 13729 = 86302 minor units, exact. No sub-minor residue.

**And here is why the third row is the one that matters:** a port that decrements the
posted balance on a hold produces `1000.31 - 137.29 = 863.02` **for the balance** — which is
exactly the correct value of `available`. The defect therefore looks plausible in every
cell that was previously captured, and is invisible without this observation.

## The task — ONE property

Promote a vector on the savings seam pinning **all four parts** of the rule:

1. the hold **posts a transaction** (type 20, `amountHold`);
2. `available` **falls** by the held amount;
3. **the posted `balance` does NOT move**;
4. **release restores `available`**, balance still unmoved.

Then register a drive for **the natural mistake** — a port that folds the hold into the
posted balance — and show it kills. Consider also one that ignores the hold entirely (so
`available` never falls).

**Prove the gap the way four runs before you did**: measure each drive against the store
**without** your vector and **with** it. Zero then non-zero is the demonstration.

**And confirm with the coverage instrument** that your work actually reaches the functions:

    go test -coverpkg=./internal/apps/savings -coverprofile=/tmp/c.cov ./internal/apps/savings/conformance/...
    go tool cover -func=/tmp/c.cov | grep -E 'HeldOf|AvailableOf|AccountBalanceOf'

Those three read **0.0%** today. If they still read 0.0% after your change, **your vector is
not exercising the rule** — say so rather than claiming the property is graded. That check
is the point of the whole task.

## THE RULE ON INERT DRIVES
**A drive that kills ZERO is a finding to resolve** — promote a vector that sees it, or
**delete it with the argument**. Report every kill count and prove the instrument was live.
**Do not manufacture coverage.**

## Measuring it
    kills.sh savings      <impl>                                (existing: 5 drives)
    kills.sh workingcapital workingcapital-wrong-discount-dropped-from-principal -> 1
    kills.sh provisioning provisioning-wrong-sum-then-round     -> 1
    kills.sh loanschedule loanschedule-wrong-days-in-year-365   -> 45

**Repaired 2026-09-09**: no silent `0` — exit 2, empty stdout, reason on stderr. **An empty
result means the MEASUREMENT FAILED.** **FLAGS ARE PER-BINARY** — `-root` is required by
most and rejected by loanschedule's; `-oracle-probe` exists on some only. Use `kills.sh`.

After your change `savings-go` must still pass **all** its vectors and the five existing
drives must still kill. That is your primary control.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; `137.29` is `13729`. MNT = ISO 496, minor unit 2.
- **Balances are DERIVED, never written** (I-3); append-only (I-4). **Holds alter
  `available` only, never posted `balance`** — this task IS that rule.
- **HALF_UP**, ordinal 4, precision 19, `Asia/Ulaanbaatar`.
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08.
- **Never describe member savings as insured, protected or guaranteed.** An NBFI exposes no
  deposit endpoint; this grades the REFERENCE ORACLE for parity, not a Gerege product.
- **Do not touch `.softhouse/guards/ledger-invariants.baseline`** (12 pairs) or
  `.softhouse/conformance.sh` (census **17**).
- **PostgreSQL only.** "The oracle" is the Fineract reference implementation; **Oracle
  Database is prohibited.**
- **One bounded context: `savings`.**
- `capture_ref`, `capture_sha256`, `citation`; **re-verify the hash after writing**. Never
  synthesise a value you did not observe. Cite `file:line` from the FILE.

## The bar and the budget
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` — exit 2 as the §4.4.2
recorded decision, ledger findings **12 pairs**, census **17**. Run it EARLY.

~500 iterations for a pure grading task. **Commit by iteration 120** — every pure-grading
run this session committed between ~61 and ~190.
