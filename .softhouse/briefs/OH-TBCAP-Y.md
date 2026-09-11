# OH-TBCAP-Y — observe the oracle's trial balance across a manual reversal. CAPTURE ONLY.

Worktree: `/Users/buv/oh-gerege-tbcap` (branch `feat/OHTBCAPy`)
Work ONLY in that directory. **Capture and map. Do not write Go. Do not promote a vector.**

**A run works ONLY in its own worktree.** `/Users/buv/gerege-nbfi` is the driver's checkout —
do not read or write there, and **never exercise the push gate**. The driver pushes.

## Why

Read `.softhouse/findings/F-2026-09-11-trialbalance-excludes-reversed.md` FIRST — all of it.

`ledger.DeriveTrialBalance` [`nexus/internal/apps/ledger/trialbalance.go:26-31`] skips entries
flagged reversed. The oracle's manual reversal flags the original AND posts an unflagged
counter-entry [`JournalEntryWritePlatformServiceJpaRepositoryImpl.java:380-429`, pinned
`/Users/buv/fineract` @ `426a23544`], and the oracle's trial balance query sums every entry
[`fineract-accounting/.../JournalEntryRepository.java:52-66`]. So the port and the oracle
should disagree by the reversed amount. **But no oracle trial balance has ever been observed**:
`m_trial_balance` is EMPTY on the live tenant although job 30 reports `success`. Your job is
to observe one — around a manual reversal — or to find out, from the source, why it cannot be.

## THE ORACLE — and the database trap

* REST: `https://localhost:8443/fineract-provider/api/v1` (`curl -k`, `-u mifos:password`,
  header `Fineract-Platform-TenantId: gerege`). **Tenant `gerege` ONLY. Never `default`.**
* SQL, **read-only** (`SELECT` only): `docker exec gerege-oracle-db psql -U postgres -d fineract_gerege -At -c '…'`
* **`fineract-db-1` is a STALE instance** — it answers convincingly and wrongly. See
  `.softhouse/briefs/tools/README.md` §"The oracle's database". **Control every SQL read**: the
  max journal-entry id you read must match what `GET /journalentries` returns.
* Business date is `2026-09-03` (`GET /businessdate`) — verify it; do not change it.
* "The oracle" is the Fineract reference implementation. **Oracle Database is prohibited.**

## The capture — in this order, everything saved raw under `.softhouse/capture/tb-manual-reversal/`

0. **Baseline, read-only**: `m_trial_balance` row count; `acc_gl_journal_entry` count and max id;
   `GET /glclosures` (the latest closure date for office 1 bounds which dates you may post);
   `GET /jobs/30` and `/jobs/30/runhistory`. **Read job 30's tasklet**
   (`UpdateTrialBalanceDetailsTasklet.java`) and work out, from the source, why five successful
   runs left the table empty. Write that down BEFORE you post anything.
1. **Post ONE manual journal entry** on office 1, balanced, two or three legs, amounts in
   **whole minor units that are not round** (e.g. `12345.67`) — never a sub-minor value. Choose
   the date from what step 0 tells you: after the latest closure, and far enough before the
   business date that the tasklet will not skip it. Use GL accounts that allow manual entries.
   Save request and response.
2. **Reverse it**: `POST /journalentries/{transactionId}?command=reverse`. Save request and response.
3. **Read back** `GET /journalentries?transactionId=…` for BOTH transaction ids, and the same rows
   by SQL (`reversed`, `reversal_id`, `type_enum`, `amount`). Confirm the finding's claim —
   original flagged, counter-entry NOT flagged — or refute it. Either is a result.
4. **Execute job 30**: `POST /jobs/30?command=executeJob`. Poll `/jobs/30/runhistory` until the run
   completes. Save it.
5. **Read `m_trial_balance` read-only** — every column, the rows for the accounts you posted to,
   and the total row count. Save it.
6. If the table is still empty, **do not retry blindly**: find the reason in the source, record it
   with `file:line`, and stop. An oracle job that reports success and writes nothing is a
   finding worth as much as the rows.

**Post exactly one manual entry and one reversal.** A second pair only if step 5 shows the first
was skipped for a reason you can name from the source — and say so.

## What to write

`.softhouse/capture/tb-manual-reversal/OWNER.md` — the map the GRADING run will build from:
every file, its sha256, what each row means, the per-account trial-balance lines the oracle
wrote for your entry and its reversal, and **whether the reversed pair nets to zero in the
oracle's own table**. State plainly what `DeriveTrialBalance` (read it, do not change it) would
produce on the same rows, and whether the two disagree.

Also write the oracle-state change to the OWNER map: which tables your capture added rows to.

## Non-negotiables (a violation is a rejection)
- Money is **integer minor units** in anything you write; transcribe wire decimals as strings.
  **Never write a sub-minor value** (G-19, DEC-2 predicate G-08).
- **SQL is read-only.** Every write goes through the REST API. **Never the `default` tenant.**
- **Never synthesise a value you did not observe.**
- Do not touch `nexus/`, `.softhouse/guards/`, or `.softhouse/conformance.sh`.
- PostgreSQL only.

## The bar and the budget
The bar must still pass on your tree: `go build ./...`, `go test ./...`,
`bash .softhouse/conformance.sh` (exit 2 by the §4.4.2 recorded decision, ledger findings
12 pairs, census 17). A capture adds files; it must not move either number.

~400 iterations. **Commit by iteration 120**, and commit after each step that saved files.
