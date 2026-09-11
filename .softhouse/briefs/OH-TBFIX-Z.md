# OH-TBFIX-Z — the trial balance removes a reversal twice. Fix it from source. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-tbfix` (branch `feat/OHTBFIXz`)
Work ONLY in that directory. **Take no captures. Issue no POST/PUT/DELETE.**

**A run works ONLY in its own worktree.** `/Users/buv/gerege-nbfi` is the driver's checkout —
do not read or write there, and **never exercise the push gate**. The driver pushes.

## Read first
1. `.softhouse/findings/F-2026-09-11-trialbalance-excludes-reversed.md` — all of it, addendum too.
2. `.softhouse/capture/tb-manual-reversal/OWNER.md` and `step06-reason/REASON.md`.

## What is established (the driver verified each)

* `ledger.DeriveTrialBalance` [`nexus/internal/apps/ledger/trialbalance.go:26-45`] **skips** entries
  flagged `Reversed`.
* The oracle's manual reversal flags the original AND posts an **unflagged** counter-entry —
  observed LIVE: JE 141/142 `reversed=t`, counter-entries 143/144 `reversed=f`
  (`tb-manual-reversal/step03-readback/sql-rows.txt`).
* The oracle's trial-balance query sums every row, **no `reversed` predicate**
  [`fineract-accounting/src/main/java/org/apache/fineract/accounting/journalentry/domain/JournalEntryRepository.java:52-66`,
  pinned `/Users/buv/fineract` @ `426a23544`].
* **The oracle cannot write a trial balance on this build**: job 30 throws
  `ClassCastException` at `UpdateTrialBalanceDetailsTasklet.java:80`, `m_trial_balance` has 0 rows.

So on rows 141–144 the port gives account 6 **−1234567** and account 10 **+1234567**, where the
oracle's rule gives **0** and **0**. The port removes the reversed position twice.

## The task

1. **Fix the port**: `DeriveTrialBalance` includes every entry; the `Reversed` flag does not
   change a line. Rewrite its doc comment to say WHY, citing `JournalEntryRepository.java:52-66`
   and the two reversal paths (manual: flag + unflagged counter-entry, `revertJournalEntry`
   `:380-429`; loan: counter-entry, nothing flagged, `:359-378`). Under BOTH, summing everything
   nets a reversed pair to zero; skipping the flagged row does not.
2. **Unit-test it on the OBSERVED rows** 141–144 (transcribed from the capture, with their observed
   `reversed` flags): each account nets to 0. And a test that flipping `Reversed` on any entry
   changes no line. These are unit tests grounded in source — **not parity vectors**.
3. **Declare the gap in `.softhouse/vectors/capabilities-ledger.json`**: the oracle-written trial
   balance is **unobservable on this build**, with the cast defect's `file:line` and the
   capture as evidence, `in_graded_domain: false`. Follow the file's existing row conventions.
   And update the `ledger.reversal.entry` row's evidence: the manual reversal's write path
   (flag + add, originals otherwise unchanged) is now observed live, before and after —
   say what that does and does not change about its graded status. No ledger port reverses.

## HARD LIMITS
* **Promote NO vector.** There is no oracle-written trial balance, and a net computed from the
  JPQL is a derived value — **never synthesise a value not observed from the oracle.**
* **Register NO drive, and do not touch `.softhouse/conformance.sh`** (ledger census **17**).
  If adding a capability row moves any pinned count or printed block and the bar goes red,
  **stop and report it** — do not edit a guard to make it green.
* **Do not touch `nexus/internal/apps/loan/`** (another run is working there).
* Find every caller of `DeriveTrialBalance` first and report them (the driver found none).

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units**; no float anywhere, including intermediates.
- Balances are **derived, never written** (I-3). Append-only (I-4).
- **Do not touch `.softhouse/guards/ledger-invariants.baseline`** (12 pairs).
- **PostgreSQL only.** "The oracle" is the Fineract reference; **Oracle Database is prohibited.**
- **One bounded context: `ledger`.**

## The bar, the budget, and how to commit
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` — exit 2 as the §4.4.2
recorded decision, ledger findings **12 pairs**, census **17**, all 17 ledger drives die. Run it EARLY.

~300 iterations. **Commit by iteration 100.** **Write the commit message to a file and use
`git commit -F <file>`** — a long `-m "…"` wedged the last run's terminal inside an unclosed quote.
