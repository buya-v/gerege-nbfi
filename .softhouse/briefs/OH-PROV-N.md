# OH-PROV-N — two gaps in provisioning, both measured. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-provn` (branch `feat/OHPROVn`)
Work ONLY in that directory. **Take no captures. Issue no POST/PUT/DELETE.**

## Why provisioning matters more than its size suggests

352 Go LOC against 11,400 Java, 8 vectors, 4 drives. But loan-loss provisioning is
**FRC-regulatory**: a wrong reserve is a regulatory reporting error, not just a wrong
number. Both gaps below are measured, not guessed. **Verify each yourself before acting.**

## GAP 1 — the ORDER OF OPERATIONS is discriminated by a vector and tested by NO drive

`PV-07-DOUBTFUL-RESERVE` carries **two inputs with IDENTICAL `reserveKey`s**, both at 50%:

    balance 10661853 x 50%  ->  5330926.5  -> HALF_UP -> 5330927
    balance  4185009 x 50%  ->  2092504.5  -> HALF_UP -> 2092505
    round-then-sum = 5330927 + 2092505    = 7423432   <- expect
    sum-then-round = (10661853+4185009)/2 = 7423431

**They differ by exactly ONE minor unit**, and both intermediates are exact half-minor
ties — the case where HALF_UP and truncation and HALF_EVEN all disagree. So PV-07 *can*
discriminate a port that sums balances first and rounds once. **Nothing tests that it
does.** The four existing drives are `blank-description`,
`category-by-definition-id`, `half-even-rounding`, `truncating` — none of them changes the
order of operations.

**Register a drive that sums the balances and rounds once** (`sum-then-round`). It should
kill exactly PV-07. **A vector no drive can kill is an assertion, not a test** — that is
the principle this whole campaign has run on.

## GAP 2 — the DISTINCT-KEY branch is never exercised

`GenerateReserveEntriesWith` [`nexus/internal/apps/provisioning/entry.go:88`] aggregates by
an eight-field `reserveKey` (criteria, office, currency, product, category, overdue days,
liability account, expense account): matching keys **sum into one entry**, differing keys
**produce separate entries**.

Every vector exercises only the first branch:

    PV-05, PV-06, PV-08   one input          -> one entry either way
    PV-07                 two IDENTICAL keys -> one entry either way

**So a port that ignores `reserveKey` entirely and sums everything into a single entry
passes all 8 vectors.** Nothing in the corpus has two inputs with **different** keys.

Closing this needs a vector with two differing-key inputs producing **two** entries. **You
have no oracle**, so do not invent one: check whether the committed captures under
`.softhouse/capture/provisioning/` contain such an observation. **If they do, promote it.
If they do not, say so and record exactly what a capture would need** — that is a
first-class result, and four runs this week have done precisely that.

## THE RULE ON INERT DRIVES
**A drive that kills ZERO is a finding to resolve** — promote a vector that sees it, or
**delete it with the argument**. Report every kill count and prove the instrument was live.
**Measure any new drive against the store WITHOUT your change and WITH it** — the technique
`OH-SHARES-K`, `OH-COLL-L` and `OH-ACCRUAL-M` used to prove a gap rather than assert it.

## Measuring it
    kills.sh provisioning provisioning-wrong-half-even-rounding  (existing)
    kills.sh loan         loan-wrong-summary-drops-penalty       -> 2
    kills.sh collateral   collateral-wrong-pct-hardcoded         -> 1
    kills.sh loanschedule loanschedule-wrong-days-in-year-365    -> 45

**Repaired 2026-09-09**: no silent `0` — exit 2, empty stdout, reason on stderr. **An empty
result means the MEASUREMENT FAILED.** **FLAGS ARE PER-BINARY** — `-root` is required by
most and rejected by loanschedule's; `-oracle-probe` exists on some only. Use `kills.sh`.

After your change `provisioning-go` must still pass **all 8** vectors and the four existing
drives must still kill. That is your primary control.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float in any money path, including intermediates.
- **HALF_UP**, ordinal 4, precision 19, `Asia/Ulaanbaatar`. HALF_UP and HALF_EVEN differ
  ONLY on an exact half-minor tie **whose TRUNCATED value is EVEN** — and PV-07's two
  intermediates are exactly such ties, which is why it discriminates so much.
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08.
- **Do not weaken or delete an existing vector** to make a drive kill.
- **Do not touch `.softhouse/guards/ledger-invariants.baseline`** (12 pairs) or
  `.softhouse/conformance.sh` (census **17**).
- **PostgreSQL only.** "The oracle" is the Fineract reference implementation; **Oracle
  Database is prohibited.**
- **One bounded context: `provisioning`.**
- Cite `file:line` from the FILE, not a comment-stripped view.

## The bar and the budget
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` — exit 2 as the §4.4.2
recorded decision, ledger findings **12 pairs**, census **17**. Run it EARLY.

~500 iterations. **Commit each drive as it is measured rather than batching.**
