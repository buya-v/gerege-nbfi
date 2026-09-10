# OH-SHARES-K — the shares corpus is uniform because the SEED DATA is uniform

Worktree: `/Users/buv/oh-gerege-sharesk` (branch `feat/OHSHARESk`)
Work ONLY in that directory. **You hold the oracle.** No other run is using it.

## THE MEASUREMENT

`shares` has 7 vectors and **eleven CONSTANT request fields** — the most of any context.
Its vectors are near-clones across eleven dimensions, varying only `kind`,
`share_capital` and `dividend_amount`. The money fields are all frozen:

    unit_price        "100.00"     constant across all 7
    purchased_price   "100.00"     constant
    total_shares      1000         constant
    purchased_shares  100          constant
    total_approved_shares 100      constant
    currency_code     "MNT"        constant

**A port that hardcodes `unit_price = 100` passes every shares vector.** So does one that
hardcodes the share count. No drive can catch it, because **no drive can catch a port
ignoring a field every vector holds fixed.** This is a gap in the OBSERVATIONS, not in the
drives — see `.softhouse/findings/F-2026-09-10-drive-ratio-only-applies-to-rich-requests.md`.

**And the root cause is upstream of the vectors.** The driver checked the oracle: all THREE
share products are identical.

    id=1  SEED-Share-Prod    unitPrice 100.0  totalShares 1000  MNT
    id=2  SEED-Share-Prod-2  unitPrice 100.0  totalShares 1000  MNT
    id=3  SEED-Share-Product unitPrice 100.0  totalShares 1000  MNT
    share accounts: id=2 (client 5, Active), id=3 (client 6, Active)

The corpus cannot vary what the seed data does not. **Verify all of this before relying
on it.**

## The task

**Create ONE share product whose money fields differ, open an account on it, and capture
the read-backs** so `unit_price` and the share counts finally vary in the corpus.

**Choose a NON-ROUND unit price.** `100.00 × anything` is round, so it hides truncation and
rounding defects exactly the way `100000.00` hid them in the loan schedule until
`OH-AMORT-F` used `41850.09` instead. Something like `137.50` or `249.99`, and a share count
that does not divide evenly into the capital. **State your choice and why.**

1. Verify the oracle state above.
2. **`pg_dump -Fc` snapshot** to `/Users/buv/gerege-oracle-snapshots/`. **Never commit a
   `.dump`.**
3. Create the product (`POST /v1/products/share`), an account on it
   (`POST /v1/accounts/share`), and drive it far enough that a **money read-back** exists —
   approve/activate and purchase shares, so `purchased_price` and the totals are real.
4. **Capture every `(request, response)` pair and the read-backs.** **COMMIT THE CAPTURE
   AS SOON AS YOU HAVE IT, before grading** — this is a state change; two runs this week
   lost uncommitted captures and needed a hand salvage.
5. Then promote a vector and register a drive that a hardcoded `unit_price` would fail.

**If the oracle refuses at any step, the refusal IS the result** — capture the status, the
error body and the source line, record it, and stop there. **Do not SQL-insert anything.**

## THE RULE ON INERT DRIVES
**A drive that kills ZERO is a finding to resolve** — promote a vector that sees it, or
**delete it with the argument**. Report every kill count and prove the instrument was live.
**Do not manufacture coverage.** `OH-LSDRIVE-I` deleted a drive that killed zero and
recorded why; `OH-INV-Z` declined a property it could not observe. That is the standard.

## Measuring it
    kills.sh shares       <impl>                                (existing: 5 drives)
    kills.sh charges      charges-wrong-rounding-half-even      -> 1
    kills.sh loanschedule loanschedule-wrong-days-in-year-365   -> 45
    kills.sh parties      parties-wrong-iota-ordinals           -> 12

**Repaired 2026-09-09**: no silent `0` — exit 2, empty stdout, reason on stderr. **An empty
result means the MEASUREMENT FAILED.** If a control is wrong, the instrument is wrong.

**FLAGS ARE PER-BINARY.** `-root` is required by most conformance binaries and REJECTED by
loanschedule's; `-oracle-probe` exists on some and not others — giving it to the charges
binary prints usage and exits 2. The driver tripped over this twice today. **Use
`kills.sh`**, which handles the variants, and check `-h` before hand-rolling an invocation.

After your change, `shares-go` must still pass **all** shares vectors and the five existing
drives must still kill. That is your primary control.

## Rules of evidence
- **Request bodies must be BYTE-STABLE** under a binary-double round trip — integer tokens
  or strings, never `json.dumps` of a parsed number. A salvage was **reverted** this week
  over `100.00 -> 100.0`. **Check your own `req/` before committing.**
- **Beware unterminated quotes** — one hung a run to death this week; `C-c` does not rescue
  it. Prefer the REST API over `docker exec psql`.
- **SQL is READ-ONLY.** Never write the `default` tenant.
- Capture directory named for its **SUBJECT** with an `OWNER.md`; names freeze at first
  commit.
- `capture_ref`, `capture_sha256`, `citation`; **re-verify the hash after writing**. Never
  synthesise a value you did not observe. Cite `file:line` from the FILE.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float in any money path, including intermediates.
  MNT = ISO 496, minor unit 2. A unit price of `137.50` is `13750`.
- **HALF_UP**, ordinal 4, precision 19, `Asia/Ulaanbaatar`.
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08. If a computed share value
  carries more than 2 decimal places, **REFUSE it — never vector a residue.**
- **Never describe member savings or share capital as insured, protected or guaranteed.**
- **Do not touch `.softhouse/guards/ledger-invariants.baseline`** (12 pairs) or
  `.softhouse/conformance.sh` (census **17**).
- **PostgreSQL only.** "The oracle" is the Fineract reference implementation; **Oracle
  Database is prohibited.**
- **One bounded context: `shares`.**

## The bar and the budget
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` — exit 2 as the §4.4.2
recorded decision, ledger findings **12 pairs**, census **17**. Run it EARLY.

~500 iterations. **Commit the capture by iteration 120 at the latest**, and commit
incrementally after that.
