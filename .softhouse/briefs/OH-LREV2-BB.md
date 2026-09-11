# OH-LREV2-BB — port the ledger's manual reversal; prove it on the observed rows. NO ORACLE. NO SEAM.

Worktree: `/Users/buv/oh-gerege-lrev2` (branch `feat/OHLREV2bb`)
Work ONLY in that directory. **Take no captures.** **A run works ONLY in its own worktree.** The driver
pushes; never exercise the push gate.

## Why this run is SMALL, on purpose
`OH-LREV-AZ` was asked to port this AND add a harness seam, and spent 425 events reading the 11,917-line
ledger conformance package without writing a line — the same way three earlier ledger runs failed. This
run does the part that is certain: **the port and its proof. It adds NO seam, NO vector, NO drive, and does
NOT touch `nexus/internal/apps/ledger/conformance/` or `.softhouse/conformance.sh` at all.** A later run
designs the seam with this port already in place. **Do not read the conformance package.**

## Read — exactly these, nothing else
1. `.softhouse/capture/tb-manual-reversal/OWNER.md` and its files:
   `step01-post/readback-rest.json` (before), `step03-readback/rest-orig.json` and `rest-rev.json` (after),
   `step03-readback/sql-rows.txt` (corroboration: `reversal_id`).
2. The rule: `revertJournalEntry` [`/Users/buv/fineract` @ `426a23544`,
   `fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/service/JournalEntryWritePlatformServiceJpaRepositoryImpl.java:380-429`].
3. The ledger's entry type: `nexus/internal/apps/ledger/journalentry.go` (the `JournalEntry` struct and its
   `Reversed` field, `:86`) and `trialbalance.go` (the doc comment OH-TBFIX-Z wrote about the two reversal paths).
4. For contrast only: `nexus/internal/apps/loan/reversal.go` (the LOAN path). Do not change it.

## The port
`nexus/internal/apps/ledger/reversal.go`:
`func RevertJournalEntries(originals []JournalEntry, reversalTransactionID string) (flagged []JournalEntry, counter []JournalEntry, err error)`
* For each original: a counter-entry with the SAME office, account, currency, amount and transaction DATE,
  the OPPOSITE side, the given `reversalTransactionID` (one id for the whole batch), manual entry true,
  `Reversed` false.
* Each original returned with `Reversed = true` and its link to its counter-entry (add a field if
  `JournalEntry` has none — say so), **and NOTHING else changed**.
* **Never mutate the input slice**; the transaction id is an INPUT (the port must never invent ids); refuse an
  unknown side rather than guess. Integer minor units; no float. Cite `file:line` from the Java in the doc
  comment, and contrast the loan path in one sentence.

## The proof — `reversal_test.go`
Transcribe the OBSERVED rows 141/142 (before) into `[]JournalEntry`, call the port with the observed fresh id
`a2b7964aa51b`, and assert the result equals the OBSERVED after-state of 141/142/143/144 cell for cell (ids
of the counter-entries are the capture's 143/144 only if your type carries ids — otherwise compare
everything else). Plus: input not mutated; `DeriveTrialBalance` over before ∪ counter-entries nets every
account to 0 (the TBFIX-Z property, now end to end); an unknown side is refused. **Mutation-check it
yourself**: flip the side, drop the flag, reuse the original id — each must fail a test.

## Record it
`.softhouse/vectors/capabilities-ledger.json`, row `ledger.reversal.entry`: append to its evidence that the
manual path is now PORTED (`reversal.go`) and proven on the live before/after rows by unit test, that it is
still OUTSIDE the graded domain because no harness seam carries a reversal yet, and what the seam needs.
Keep `in_graded_domain: false`. Follow the row's existing style.

## Non-negotiables (a violation is a rejection)
- Append-only: the port never mutates an input. Money in integer minor units; no float.
- **Do not touch `.softhouse/guards/`, `.softhouse/conformance.sh`, `nexus/internal/apps/ledger/conformance/`,
  `nexus/internal/apps/loan/`, or `.softhouse/maps/`.** PostgreSQL only; **Oracle Database is prohibited.**
- **One bounded context: `ledger`.**

## The bar, the budget, and how to commit
`go build ./...`, `go test ./...`, `bash .softhouse/conformance.sh` — exit 2 ONLY with
`§4.4.2-RECORDED-DECISION-EXIT`, ledger findings **12 pairs**, census **17** unchanged. ~200 iterations.
**Commit the port + test by iteration 60.** **`git commit -F <file>`. Never commit TASK.md.**
