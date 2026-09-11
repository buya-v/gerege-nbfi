# F-2026-09-11 — `DeriveTrialBalance` skips reversed entries; the oracle sums them

**Status: OPEN. Ungraded. A port defect on committed evidence, not a hypothesis.**
Found by the driver while writing the brief for the write-off's reversing accrual.

## The rule in the tree

`nexus/internal/apps/ledger/trialbalance.go:26-31`:

    // Reversed entries are excluded — a reversal negates its
    // original and contributes nothing to the closing position.
    for _, e := range entries {
        if e.Reversed { continue }

## What the oracle does — two facts, both verified

**1. A manual reversal FLAGS the original and ADDS an UNFLAGGED counter-entry.**
`JournalEntryWritePlatformServiceJpaRepositoryImpl.revertJournalEntry` [pinned `426a23544`,
`:380-429`]: for each original it persists a counter-entry of the opposite side on a fresh
transaction id (`:407-422`), then `journalEntry.setReversed(true)` (`:423`). The counter-entry
is never flagged.

Observed, committed: `.softhouse/capture/tierA-a2/out/A2-350-je-office1-june.json` —
originals 45/46/47 (txn `a28f573f34c7`) read `reversed: true`; the counter-entries 50/51/52
(txn `a28f57412abb`, "A2-26 reversal probe") read `reversed: false`, opposite sides, same
amounts. Same shape for 33/34/35 → 38/39/40.

**2. The oracle's trial balance sums EVERY entry.**
`JournalEntryRepository.findTrialBalanceLinesForDate` [`fineract-accounting/.../JournalEntryRepository.java:52-66`]:
`SUM(CASE WHEN je.type = 1 THEN -1 * je.amount ELSE je.amount END) … GROUP BY office, glAccount, …`
— **no predicate on `reversed`.**

## The consequence

On A2-350's rows, account 10300: oracle nets `+100000.25 − 100000.25 = 0` for the reversed
pair. `DeriveTrialBalance` drops the flagged original and keeps the unflagged counter-entry:
**−100000.25**. The comment's premise ("a reversal negates its original") is true of the
counter-entry and is exactly why the original must NOT also be dropped — the port removes the
position twice.

The loan-transaction reversal path is different and does NOT trip this: 
`createJournalEntryForReversedLoanTransaction` [`:359-378`] adds counter-entries on the SAME
transaction id and flags nothing (observed: loan 11 JE 84/86 unchanged, 134/135 added —
`.softhouse/capture/loan11-writeoff-four-bucket/`). So the defect is visible only on the
manual path — which is the path A2-350 captured.

## Why it has survived

`DeriveTrialBalance` has **no caller** in `nexus/internal` outside its own file and **no
vector** grades it. Ported, commented, confidently wrong, and invisible.

## What closes it

One run in the `ledger` context: promote a vector from A2-350 (all 20 rows as input, the
per-account nets as expect), drop the `Reversed` skip, and register the current behaviour as a
drive (`ledger-wrong-trialbalance-skips-reversed`) that the vector kills. **This moves the
ledger drive census pin (17 → 18) in `.softhouse/conformance.sh`** — a guard every brief so
far has told runs not to touch. The driver must authorise that one edit explicitly in the
brief, with this finding as the argument, and verify it is the ONLY change to the file.
