# OH-GL-T — re-capture the GL surface with BYTE-STABLE requests, then grade it

Worktree: `/Users/buv/oh-gerege-glt` (branch `feat/OHGLt`)
Work ONLY in that directory. The oracle is UP.

## READ THIS FIRST — most of the hard work is ALREADY DONE and still live

`OH-GL-R` opened the loan→GL posting surface, hit its 500-iteration limit with 71 files
and zero commits, and the driver's salvage of it was **REVERTED because the bar refused
it**. You are not repeating that run. You are fixing one specific defect and finishing.

**The oracle state PERSISTS. Do not rebuild it.** Verify each of these before using it:

* loan product **id 3 `OHLGR-Accrual-Loan`**, `accountingRule` **ACCRUAL PERIODIC** — the
  only accounting-enabled product here. Products 1 and 2 are `NONE` and **must stay
  untouched**.
* 11 GL accounts named `OHLGR-*`; 2 clients; loans **10** and **11**, both Active.
* Journal entries 17-22 exist and balance (loan 10: debits 100100.0 == credits 100100.0;
  loan 11: 100000.0 == 100000.0).
* Business date **2026-09-02**, COB config carries `EXTERNAL_ASSET_OWNER_TRANSFER` at
  order 7.

`OH-GL-R`'s 72 files, including its working `bin/step0*.sh` scripts, are preserved at
**`/Users/buv/gerege-oracle-snapshots/gl-accounting-surface-evidence/`**. **Read them.**
They are outside the repo and are your starting point, not something to reinvent.

## THE DEFECT YOU ARE FIXING, and it is narrow

The bar refused with a failed HARD guard — probe line never printed, so **no verdict was
available, which is not a pass**:

    REFUSED — a numeric token in a capture request body is NOT byte-preserved under a
    binary-double round trip. This is the P-25 defect T163 found in resolve7.py: the money
    that reaches the reference oracle is not the money that was written.
      req/charge-OHLGR-Fee-Flat-100.json:1      100.00 -> 100.0
      req/charge-OHLGR-Penalty-Flat-57.json:1    57.00 -> 57.0
      req/loan-OHGLR-L01-submit.json:21,22      100.00 -> 100.0, 57.00 -> 57.0
      req/loan-OHGLR-L02-submit.json:21,22      100.00 -> 100.0, 57.00 -> 57.0

The record was **not** falsified: `bin/step03-charges.sh:24` sent the body as a shell
single-quoted literal containing `"amount":100.00`, and `req/` copied it faithfully. The
defect is that **the request sent to the oracle carries a numeric token that is not
byte-stable**.

**The fix, which the guard itself names:** never re-serialise a request body through
`json.dumps` of a parsed number; splice the placeholder into the template bytes.
`.softhouse/capture/tierA-a2/resolve8.py` is the worked example — **read it before writing
any request**. Write amounts as byte-stable tokens.

**Do not "fix" this by deleting `req/`.** The driver considered exactly that, and reverted
the whole salvage instead, because a green bar bought by removing the artefact that failed
is the thing this programme refuses. Your captures must pass the guard, not avoid it.

## The path

1. **Verify the oracle state above.** Anything missing, say so and adapt; do not assume.
2. **Create NEW charges with byte-stable amounts** (a fee and a penalty that **DIFFER**),
   and a **new loan** on product 3 carrying both. Additive — do not modify products 1/2,
   and do not modify loans 10 or 11.
3. **Capture the `(request, response)` pair for every call**, with request bodies that
   survive a binary-double round trip byte-for-byte. Self-check before committing: parse
   and re-serialise each `req/*.json` numeric token and confirm the bytes are unchanged.
4. **Run `bash .softhouse/conformance.sh` EARLY**, as soon as the first captures land — not
   at the end. The wire-float guard is HARD; finding out at iteration 400 is how the last
   run's work ended up reverted.

Name the capture directory for its **SUBJECT**, not for your run id — see
`.softhouse/guards/check-capture-namespace.sh`. Include an `OWNER.md`. Directory names are
frozen at first commit.

## Then GRADE it — properties, not counts

**You are measured on defects provably caught, never on file count.**

### Priority 1 — close `F-2026-09-09-fee-penalty-blind.md`. Read it first.

Loan summary total outstanding is a **four-term sum**: `principal + interest + fee +
penalty`. Every existing vector has **fee = 0 AND penalty = 0**, so a port that drops
either term passes all of them. Adding zero is indistinguishable from not adding.

* Promote a summary vector whose fee and penalty are **non-zero and DIFFERENT** (equal
  values let a term-swap defect survive).
* Register **`loan-wrong-summary-drops-fee`** and **`loan-wrong-summary-drops-penalty`**
  and **show each kills.** Until a drive dies on that vector nothing is proven — the entire
  point of that finding is that a dropped term was invisible.
* A second, differently-shaped observation (fee 0, penalty non-zero) discriminates the
  penalty term alone. A fifth *zero-fee* summary vector is the OH-DEEP-E cloning failure —
  do not add one.

### Priority 2 — the double-entry surface

1. **Every journal entry batch BALANCES: sum(debits) == sum(credits), exactly, in integer
   minor units.** I-1/I-2, the most important property in the programme.
2. **A disbursement posts a specific DEBIT/CREDIT PAIR** — portfolio debited, fund source
   credited. **Pin the DIRECTION**: a port that inverts the pair still balances.
3. **Entry type is an enum with an ordinal.** `parties-wrong-iota-ordinals` kills 12 on
   exactly this class.

## THE RULE ON INERT DRIVES
**A drive that kills ZERO is a finding to resolve, never something to merge.** Promote a
vector that sees it, or **delete it with the argument**. Say which, per drive. **Report
every kill count.** And **prove the instrument was live when a drive scores zero** — run
the controls in the same session and name an existing drive in the same context that still
kills. `OH-INV-Q` did this correctly; copy it.

## Measuring it
`.softhouse/briefs/tools/kills.sh <ctx> <impl> [worktree]`, `redcount.sh`. **Repaired
2026-09-09**: no silent `0` — they exit 2 with empty stdout and a reason on stderr. **An
empty result means the MEASUREMENT FAILED.** Controls:

    kills.sh loanschedule loanschedule-wrong-days-in-year-365   -> 45
    kills.sh parties      parties-wrong-iota-ordinals           -> 12
    kills.sh charges      charges-wrong-rounding-half-even      -> 1

If a control is wrong, the instrument is wrong — not the tree.

## Rules of evidence
- **Cite `file:line`.** Line numbers from the FILE, not a comment-stripped view — the
  driver got that wrong this week and an agent caught it.
- **Never synthesise a value you did not observe.** Configuring through the API and
  observing what Fineract computes is NOT synthesis; SQL-inserting reference data IS.
- **SQL is READ-ONLY.** Never write the `default` tenant. All writes go through the API.
- Snapshot with `pg_dump -Fc` before writing, keep it under
  `/Users/buv/gerege-oracle-snapshots/`, and **never commit a `.dump`.**
- Every vector carries `capture_ref`, `capture_sha256`, `citation`; re-verify after writing.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float in any money path, including intermediates.
  MNT = ISO 496, minor unit 2.
- **Double-entry, append-only.** Balances derived, never written (I-3).
- **HALF_UP**, ordinal 4, precision 19, `Asia/Ulaanbaatar`. HALF_UP and HALF_EVEN differ
  ONLY on an exact half-minor tie **whose TRUNCATED value is EVEN** (0.025 → .03 vs .02).
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08. Never vector a residue.
- **PostgreSQL only.** "The oracle" is the Fineract reference implementation; **Oracle
  Database is prohibited.**

## The bar
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh`. Expect exit 2 as the
§4.4.2 recorded decision with the ledger finding set at **exactly 12 (class, file) pairs**.
**Run it early and often** — the last run's work was lost to a HARD guard found too late.

## Budget
~500 iterations. Three runs before you hit the cap; two wrote nothing. **Capture first,
grade second, commit incrementally.** If you are 150 iterations in without a committed
capture, stop and commit what you have.
