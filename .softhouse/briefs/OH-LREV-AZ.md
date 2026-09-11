# OH-LREV-AZ — port and grade the ledger's manual reversal. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-lrev` (branch `feat/OHLREVaz`)
Work ONLY in that directory. **Take no captures. Issue no POST/PUT/DELETE.**
**A run works ONLY in its own worktree.** The driver pushes; never exercise the push gate.

## Read first — do not search
1. `.softhouse/maps/ledger.md` — seams, vectors, drives (17), port functions, measuring (NO kills.sh here).
2. `.softhouse/capture/tb-manual-reversal/OWNER.md` — the observation, every figure.
3. `.softhouse/vectors/capabilities-ledger.json`, row `ledger.reversal.entry` — why it has been outside the
   graded domain ("distinguishing 'flags and adds' from 'flags and rewrites' needs the WRITE path").
4. `nexus/internal/apps/loan/reversal.go` — the LOAN reversal port (OH-REVERSAL-X): the other path, for
   contrast. **Do not change it.**

## Why
CLAUDE.md: **"Corrections are reversing entries."** The loan path is ported and graded; the LEDGER's manual
reversal — `POST /journalentries/{transactionId}?command=reverse` — has no port and no vector. TBCAP-Y
captured its write path LIVE, before and after:

    before (step01-post/readback-rest.json):  141 acct 6 DEBIT 12345.67, 142 acct 10 CREDIT 12345.67, txn a2b795dca42b, reversed=false
    after  (step03-readback/rest-orig.json):  141, 142 — same account/side/amount/date, reversed=TRUE
           (step03-readback/rest-rev.json):   143 acct 6 CREDIT, 144 acct 10 DEBIT, 12345.67, NEW txn a2b7964aa51b, reversed=false, manual
    (sql-rows.txt, corroboration only: reversal_id 141->143, 142->144)

## The rule — port it
`JournalEntryWritePlatformServiceJpaRepositoryImpl.revertJournalEntry` [pinned `/Users/buv/fineract` @
`426a23544`, `fineract-provider/.../JournalEntryWritePlatformServiceJpaRepositoryImpl.java:380-429`].
**Read it.** For each original: persist a counter-entry — same office, account, currency, amount and
transaction DATE, OPPOSITE side, on ONE fresh transaction id shared by the batch, `manualEntry` true — then
set the ORIGINAL's `reversed = true` and its reversal link. **Nothing else about the original changes.**
Port it into `nexus/internal/apps/ledger/` as a pure function (integer minor units; the fresh transaction id
is an INPUT, not generated — the port must not invent ids). Cite `file:line`.

## The task — ONE property
> **A manual reversal FLAGS each original (and nothing else about it) and ADDS one opposite-side
> counter-entry per original on a single new transaction id.**

Add a seam (e.g. `ledger-manual-reversal`) and move `ledger.reversal.entry` INTO the graded domain, citing
this capture. Promote ONE vector: request = the before-legs + the fresh transaction id observed; expect =
the after-state of all four entries (originals with `reversed: true`, counter-legs as observed).

Drives, each discriminated here — the loan path's semantics are the natural mistakes:
* **does not flag the originals** (the LOAN path's behaviour);
* **reuses the original transaction id** (also the loan path's);
* **same side** (duplicates instead of reverses — the batch still balances);
* **rewrites the original** (negates its amount or flips its side instead of adding a counter-entry) —
  the "flags and rewrites" reading the capability row names.

## Measuring — ledger is DIFFERENT
**`ledger` has NO conformance binary; `kills.sh ledger` fails loudly, and that is NOT a zero.** Ledger
drives are measured by the CENSUS block of `bash .softhouse/conformance.sh`
(`conformance:   KILLED  ledger-wrong-<name> — exit 1, ledger parity FAIL n …`). Measure each new drive with
the bar run on a scratch copy of the store WITHOUT your vector and WITH it; report both lines. A drive
not listed KILLED is inert — resolve it, never merge it.

## THE ONE EDIT TO `.softhouse/conformance.sh` THE DRIVER AUTHORISES
The census pin `EXEMPTION_PIN_LEDGER_WRONGIMPLS=17` (`.softhouse/conformance.sh`, ~line 6490) must move to
17 + (drives you register). **Authorised: that number, plus ONE paragraph in the comment block directly
above it, in the file's own style** (read the "T307 MOVES IT 12 -> 13" paragraph and match it: which drive,
what it does wrong, which vector kills it and on which cell, why it could not be registered before).
**Nothing else in `conformance.sh` may change** — the driver diffs it.

## THE RULE ON INERT DRIVES
**A drive that kills ZERO is a finding to resolve.** **Do not manufacture coverage.**

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float anywhere. Append-only: the port must NEVER mutate an input.
- **Do not touch `.softhouse/guards/ledger-invariants.baseline`** (12 pairs), `nexus/internal/apps/loan/`, or
  `.softhouse/maps/`. PostgreSQL only; **Oracle Database is prohibited.**
- `capture_ref` must be a **JSON** capture record (never `sql-rows.txt`); `capture_sha256`; re-verify.
- **One bounded context: `ledger`.**

## The bar, the budget, and how to commit
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` — exit 2 ONLY with
`§4.4.2-RECORDED-DECISION-EXIT`, ledger findings **12 pairs**, and the census line must read your new
total with EVERY ledger drive DIED. **"a HARD guard failed" is a failure.** ~500 iterations. **Commit the
port by iteration 120.** **Write commit messages to a file (`git commit -F`). Never commit TASK.md.**
