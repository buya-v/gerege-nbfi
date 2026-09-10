# OH-INV-W — settle a transfer at last, and confirm the purchase-price gap on live postings

Worktree: `/Users/buv/oh-gerege-invw` (branch `feat/OHINVw`)
Work ONLY in that directory. You hold the oracle. Another run (`OH-LEDGER-V`) is
promoting from committed captures only and will not touch it.

## THE LAST OPEN PIECE, and why it is now reachable

`OH-INV-Q` drove a transfer through COB and it refused:

    ProductToGLAccountMappingNotFoundException: Mapping for product of type LOAN
    with Id 2 does not exist for an account of type LOAN PORTFOLIO
    [InvestorAccountingHelper.java:128]

The root cause was **not** a missing mapping row: loan product 2 has
**`accountingRule: NONE`**. The investor sale step posts journal entries, so a transfer on
an accounting-disabled product can never settle.

**That is now fixable, and the fix already exists.** `OH-GL-R`/`OH-GL-T` created loan
product **id 3 `OHLGT`/`OHLGR-Accrual-Loan`, `ACCRUAL PERIODIC`**, with a full
`accountingMappings` set and 11 `OHLGR-*` GL accounts. **Loans 10, 11 and 12 are on product
3 and post journal entries.** Verify all of this before relying on it.

## The path

1. **Verify the state.** Product 3 accounting rule and mappings; loans 10/11/12 exist;
   `GET /jobs/LOAN_CLOSE_OF_BUSINESS/steps` still carries `EXTERNAL_ASSET_OWNER_TRANSFER`
   (`OH-INV-Q` added it at order 7); business date (`2026-09-02` when last read).
2. **Create an external asset owner transfer on a PRODUCT 3 LOAN** — not on loan 6, which
   is product 2 and is why the last attempt refused. Give it a `purchasePriceRatio` and a
   `settlementDate` at or before the business date.
3. **Run COB** and read the result. `POST /jobs/{id}?command=executeJob` returns 202; the
   investor step is caught **per-loan**, so a job-level success does not mean the step
   succeeded. Read the per-loan outcome, not the job status — that is how `OH-INV-Q`
   correctly detected a WARN-and-SKIP.
4. **Read back:** `GET /external-asset-owners/transfers?loanId=<id>` and
   `GET /external-asset-owners/transfers/{transferId}/journal-entries`.

**Snapshot with `pg_dump -Fc` before step 2**, keep it under
`/Users/buv/gerege-oracle-snapshots/`, and **never commit a `.dump`**.

**If it refuses again, the refusal IS the result.** Capture the exact status, error body and
the source line that raised it, record it, and stop there. `OH-INV-Q`'s refusal was a
first-class outcome and so is this one. **Do not work around a refusal by SQL-inserting
reference data** — `OH-INV-Q` refused exactly that, correctly, and that line holds.

## FINDING A — confirm, do not re-derive

Established from pinned source `426a23544`; **do not spend budget re-deriving it**:

1. `purchasePriceRatio` is a **`String`** — `data/ExternalTransferData.java:34`
   (**:34, not :16** — an earlier brief cited :16, which is licence header; `OH-INV-Q`
   caught it. Line numbers come from the FILE, never a comment-stripped view).
2. **All seven** non-test `getPurchasePriceRatio()` call sites are setter-to-setter copies.
3. `fineract-investor/src/main/java` = **99 files, ZERO `multiply` calls**.
4. `service/AccountingServiceImpl.java` has **zero** occurrences of `urchasePrice`; amounts
   are face-value outstanding accumulated with `.add` (`:193,:220,:235,:250,:261`) and
   posted (`:273,:277`).

**THE CONFIRMATION THIS RUN EXISTS FOR:** with a settled transfer, show the posted journal
entries equal the **outstanding**, NOT `ratio × outstanding`. Pick a ratio that makes the
two obviously different (97.25% of 100000 is 97250 — nothing like 100000). Capture it.

**If the oracle contradicts any of the four items, the ORACLE WINS and you say so loudly.**
`OH-GAP-M` found a MANIFEST "documented gap" that was **false** and had survived weeks into
the published record.

## FINDING B — the details seam, if the transfer settles

`domain/ExternalAssetOwnerTransferDetails.java:83-88` derives
`totalOutstanding = principal + interest + fees + penalties`, and
`service/ExternalAssetOwnersTransferMapper.java:48` maps `details` onto the read endpoint.
`OH-INV-Q` found the details table empty, so all four properties were unobservable and it
**deleted all four drives with the argument** rather than merging them inert. A settled
transfer would make them observable for the first time:

1. **`totalOverpaid` is EXCLUDED from the total.** `setTotalOverpaid` (`:87-90`) is the
   only component setter that does not call `updateTotalOutstanding()`. A port folding
   overpaid in — added or subtracted — is wrong, and `OH-GAP-M`'s agent guessed
   "− overpaid", so it is a mistake a real reader made.
2. The total is **recomputed on every component setter** (`:63-81`) — I-3 in Fineract's own
   code.
3. **Null coalesces to ZERO, not to a refusal** — `Objects.requireNonNullElse(x, ZERO)`.
4. Columns are **`scale = 6, precision = 19`** (`:45-61`) — they can hold sub-minor digits.
   **A trap, not a target:** if a residue value appears, **REFUSE it**; never vector it.

## THE RULE ON INERT DRIVES
**A drive that kills ZERO is a finding to resolve, never something to merge.** Promote a
vector that sees it, or **delete it with the argument**. Say which, per drive, and report
every kill count. **Prove the instrument was live** when a drive scores zero: run the
controls in the same session and name an existing `investor` drive that still kills
(`investor-wrong-blank-status` and `investor-wrong-fabricates-transfer` each killed 1).

## Measuring it
`.softhouse/briefs/tools/kills.sh <ctx> <impl> [worktree]`, `redcount.sh`. **Repaired
2026-09-09**: no silent `0` — exit 2 with empty stdout and a reason on stderr. **An empty
result means the MEASUREMENT FAILED.** Controls:

    kills.sh loanschedule loanschedule-wrong-days-in-year-365   -> 45
    kills.sh parties      parties-wrong-iota-ordinals           -> 12
    kills.sh charges      charges-wrong-rounding-half-even      -> 1

If a control is wrong, the instrument is wrong — not the tree.

## Rules of evidence
- **Request bodies must be BYTE-STABLE under a binary-double round trip.** Write amounts as
  integer tokens; never re-serialise a body through `json.dumps` of a parsed number. A run
  this week had its whole salvage **reverted** by that HARD guard (`100.00 -> 100.0`);
  `capture/tierA-a2/resolve8.py` is the worked splicing example. **Check your own `req/`
  files before committing.**
- **Cite `file:line`.** From the file, not a stripped view.
- **Never synthesise a value you did not observe.** Every vector carries `capture_ref`,
  `capture_sha256`, `citation`; re-verify after writing.
- **SQL is READ-ONLY.** Never write the `default` tenant. All writes through the API.
- Name the capture directory for its **SUBJECT**, with an `OWNER.md`; names freeze at first
  commit (`.softhouse/guards/check-capture-namespace.sh`).

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float in any money path, including intermediates.
- **Double-entry, append-only.** Balances derived, never written (I-3).
- **HALF_UP**, ordinal 4, precision 19, `Asia/Ulaanbaatar`.
- **Sub-minor residue is REFUSED** — G-19, DEC-2 predicate G-08.
- **PostgreSQL only.** "The oracle" is the Fineract reference implementation; **Oracle
  Database is prohibited.**
- **One bounded context: `investor`.** Do NOT touch `ledger` or `loan` — `OH-LEDGER-V`
  holds them.

## The bar
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh`. Expect exit 2 as the
§4.4.2 recorded decision, ledger finding set at **exactly 12 (class, file) pairs**. **Run
it EARLY.** Report every kill count and every capture sha256.

## Budget
~500 iterations. **Three runs have died on this question with nothing written.** Two died
on navigation; the navigation is above. Take steps 1-4 FIRST, commit incrementally, and if
150 iterations in without a settled transfer or a recorded refusal, **stop exploring and
write down what you have.**
