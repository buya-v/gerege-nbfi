# OH-TIERD11-CC2 — FINISH the LoanAccrualActivity-Part2 capture. Salvage of OH-TIERD11-CC. CAPTURE ONLY. NO CONTAINER.

Worktree: `/Users/buv/oh-gerege-tierd11` (branch `feat/OHTIERD11CC`)
Work ONLY in that directory. **Start no container, run no replay: the throwaway is already DOWN** (the driver ran
`down.sh`; `accrual-activity-mnt/teardown-isolation.txt` holds 12/12 ok — commit it as it is). The driver pushes.

## Where the first run stopped (it stalled waiting on a background job; the driver killed it by pid)
Already committed: rig, preflight, the replay result table (34/35 passed; scenario 11 / loan 11 FAILED — recorded).
Already on disk, UNCOMMITTED, in `.softhouse/capture/tierd-feasibility/accrual-activity-mnt/`: `loans/` (34 loans,
1,530 files — loan 11 excluded), `manifest-accrual-activity.json` (1,565 entries), `manifest-accrual-activity-passed.json`,
`summary-accrual-activity.json`, `journalentries/` (8 responses, loans 34 and 35), `journalentries-manifest.json`,
`journalentries-summary.json`, `build-type-join.py`, `build-owner.py`, `extract.out`, `teardown-isolation.txt`.
`stage/` is scratch: NEVER commit it. The two extractor scripts show only a file-mode change; restore it
(`git checkout -- <file>` for the mode) or leave them executable — do not edit their logic.

## Finish, in this order, committing after each step (`git commit -F <file>`; never TASK.md, never stage/)
1. Re-hash both loan manifests and the journal-entry manifest against the files; fix nothing by hand — if a hash does
   not match, re-run the extractor/organizer that wrote it. Commit `loans/`, the manifests, the summary, `journalentries/`.
2. `extract-product-mappings.py <log> <product name>...` for every product the committed loans use (names from the
   loan read-backs; log `/Users/buv/fineract-tierd/fineract-e2e-tests-runner/build/capture/feign-accrualactivity-mnt.log`).
   Commit `product-mappings/`. Run every command in the FOREGROUND; never `&`, never `jobs`, never wait on a job.
3. The type join (`build-type-join.py`): every journal-entry leg → its transaction TYPE through the loan read-backs.
   Table in OWNER.md: type → legs → loans. The point is the accrual postings (`createJournalEntriesForAccruals`
   [AccrualBasedAccountingProcessorForLoan.java:2015]; types `accrual`, `accrualAdjustment`, `accrualActivity`): per
   type, the legs observed (loan, tx id, GL account, amount in minor units). A type with no legs is a finding, say so.
   ALSO count, from the loan read-backs (not the journal entries), how many transactions of each accrual type exist.
4. OWNER.md in the shape of `.softhouse/capture/tierd-feasibility/writeoff-mnt/OWNER.md` (read it; copy its sections),
   including the failure of scenario 11 exactly as `replay-result-table.md` records it (do not diagnose the cause), and
   the teardown. Commit.

## Non-negotiables
Money in integer minor units in anything you write. **Do not touch `nexus/`, `.softhouse/vectors/`,
`.softhouse/guards/`, `.softhouse/conformance.sh`, `.softhouse/maps/`.** Never write into `/Users/buv/fineract`.
PostgreSQL only; **Oracle Database is prohibited.** Bar: `bash .softhouse/conformance.sh` exits 2 ONLY with
`§4.4.2-RECORDED-DECISION-EXIT`. ~150 iterations.
