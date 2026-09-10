# OH-COLL-L — the collateral corpus varies NOTHING. Widen it.

Worktree: `/Users/buv/oh-gerege-colll` (branch `feat/OHCOLLl`)
Work ONLY in that directory. **You hold the oracle.** No other run is using it.

## THE MEASUREMENT — this is the most extreme corpus gap in the programme

`collateral` has 4 vectors and **ZERO varying request fields**. Every one references the
same entities: `link_id 2, client_id 5, collateral_id 2, product_id 2`. And the oracle has
exactly **ONE** collateral product:

    id=2  SEED-Collateral-Product  quality Good  basePrice 100000.0  pctToBase 50.0  unit 1

`CL-04-valuation-read` grades the computed valuation:

    quantity 150000  (scale-5, i.e. 1.5)
    total            15000000000   = basePrice x quantity
    total_collateral  7500000000   = total x pctToBase/100

**Both inputs are round, and `pctToBase = 50.0` is just halving.** A port that hardcodes
the base price, hardcodes the percentage, or takes a `/2` shortcut computes the right
answer on every existing vector. No drive can catch any of it, because **no drive can catch
a port ignoring a field every vector holds fixed** — see
`.softhouse/findings/F-2026-09-10-drive-ratio-only-applies-to-rich-requests.md`.

`OH-SHARES-K` closed the same shape of gap one run ago and **proved** it by measuring its
new drive against both stores: 0 kills on the seed-only corpus, 2 on the widened one. **Do
that here too** — it is what turns "the gap existed" from a claim into a measurement.

## The task

**Create ONE collateral product whose money inputs are NON-ROUND and whose percentage is
NOT 50, link it to a client, and capture the valuation read-back.**

Choose values so that:
* the base price is **not round** — `100000.0` hides truncation the way `100000.00` hid it
  in the loan schedule until `OH-AMORT-F` used `41850.09`;
* **`pctToBase` is NOT 50** — anything else breaks a `/2` shortcut. Say what you chose;
* the quantity is **not a whole number** (the field is scale-5; the seed uses `1.5`);
* **and the resulting money cells carry NO sub-minor residue.** Work the arithmetic out
  BEFORE you create anything: `basePrice x quantity x pct/100` must land on a whole number
  of minor units. **If your first choice produces residue, pick different numbers** — do
  not create it and then discover the vector is unvectorable.

**State your chosen values and the arithmetic in the commit message.**

## The path
1. Verify the oracle state above.
2. **`pg_dump -Fc` snapshot** to `/Users/buv/gerege-oracle-snapshots/`. **Never commit a
   `.dump`.**
3. Create the collateral product; link it to a client; capture every
   `(request, response)` pair and the valuation read-back.
4. **COMMIT THE CAPTURE IMMEDIATELY, before grading.** This is a state change.
   `OH-SHARES-K` was killed mid-run and lost nothing because its capture was already in;
   two earlier runs lost uncommitted captures and needed a hand salvage.
5. Promote the vector, register the drive(s), and **measure against both the old and the
   new store**.

**If the oracle refuses, the refusal IS the result** — capture status, error body and the
source line, record it, stop there. **Do not SQL-insert anything.**

## Drives worth registering — only what the capture DISCRIMINATES
* base price hardcoded to the seed value;
* percentage hardcoded (or `/2`), which the seed's 50.0 cannot distinguish;
* quantity truncated to a whole number.

**A drive that kills ZERO is a finding to resolve** — promote a vector that sees it, or
**delete it with the argument**. Report every kill count and prove the instrument was live.
**Do not manufacture coverage.**

## Measuring it
    kills.sh collateral   <impl>                                (existing: 4 drives)
    kills.sh shares       shares-wrong-unit-price-hardcoded     -> 2
    kills.sh charges      charges-wrong-rounding-half-even      -> 1
    kills.sh loanschedule loanschedule-wrong-days-in-year-365   -> 45

**Repaired 2026-09-09**: no silent `0` — exit 2, empty stdout, reason on stderr. **An empty
result means the MEASUREMENT FAILED.** If a control is wrong, the instrument is wrong.

**FLAGS ARE PER-BINARY.** `-root` is required by most conformance binaries and REJECTED by
loanschedule's; `-oracle-probe` exists on some and not others and makes the charges binary
print usage and exit 2. **Use `kills.sh`**; check `-h` before hand-rolling an invocation.
The driver tripped over this twice yesterday.

After your change `collateral-go` must still pass **all** collateral vectors and the four
existing drives must still kill. That is your primary control.

## Rules of evidence
- **Request bodies must be BYTE-STABLE** under a binary-double round trip. A salvage was
  **reverted** this week over `100.00 -> 100.0`. **Check your own `req/` before committing.**
- **Beware unterminated quotes** — one hung a run to death; `C-c` does not rescue it.
- **SQL is READ-ONLY.** Never write the `default` tenant.
- Capture directory named for its **SUBJECT** with an `OWNER.md`; names freeze at first commit.
- `capture_ref`, `capture_sha256`, `citation`; **re-verify the hash after writing**. Never
  synthesise a value you did not observe. Cite `file:line` from the FILE.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float in any money path, including intermediates.
  MNT = ISO 496, minor unit 2.
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08. This task can CREATE
  residue by choosing careless numbers; that is why the arithmetic comes first.
- **HALF_UP**, ordinal 4, precision 19, `Asia/Ulaanbaatar`.
- **Do not touch `.softhouse/guards/ledger-invariants.baseline`** (12 pairs) or
  `.softhouse/conformance.sh` (census **17**).
- **PostgreSQL only.** "The oracle" is the Fineract reference implementation; **Oracle
  Database is prohibited.**
- **One bounded context: `collateral`.**

## The bar and the budget
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` — exit 2 as the §4.4.2
recorded decision, ledger findings **12 pairs**, census **17**. Run it EARLY.

~500 iterations. **Commit the capture by iteration 120 at the latest**, incrementally after.
