# OH-ACJGRADE-CH — port + grade the loan ACCRUAL journal entry. ONE property, concrete inputs. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-acjgrade` (branch `feat/OHACJGRADECH`)
Work ONLY in that directory. **Take no captures. Start no container.** The driver pushes; never exercise the push gate.

## Why this brief is narrow
Five sibling runs did this shape by COPYING a merged seam. Do the same. **Do not read findings, maps or other vectors
beyond what is listed. Start writing within 20 iterations. Commit after the first vector passes.**

## The property (one)
`createJournalEntriesForAccruals` [`/Users/buv/fineract/fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/service/AccrualBasedAccountingProcessorForLoan.java:2015-2087`,
read-only, pinned 426a23544; dispatch `:79-81`] for types ACCRUAL and ACCRUAL_ADJUSTMENT, no tax:
* interest > 0: accrual → DEBIT INTEREST_RECEIVABLE then CREDIT INTEREST_ON_LOANS (`helper.createJournalEntriesForLoan`:
  debit first); accrual adjustment → the SAME helper with the accounts swapped (DEBIT INTEREST_ON_LOANS, CREDIT
  INTEREST_RECEIVABLE);
* fees > 0, then penalties > 0: `helper.createJournalEntriesForLoanCharges`
  [`AccountingProcessorHelper.java:393-435`] — CREDIT first, then DEBIT: accrual → CREDIT INCOME_FROM_FEES / DEBIT
  FEES_RECEIVABLE (penalties: INCOME_FROM_PENALTIES / PENALTIES_RECEIVABLE); adjustment → sides swapped. The fee group
  and the penalty group are SEPARATE helper calls: they never merge with each other, even on the same accounts.
The tax branch and charge-specific GL mappings (per-charge accounts) are NOT observed: the port takes the resolved
product accounts and no tax/charge input.

## The port — a NEW pure function
Model it on `nexus/internal/apps/loan/chargedoffrepaymentjournal.go` (`CreateChargedOffRepaymentJournalEntryLegs`:61 —
read it whole). New file `nexus/internal/apps/loan/accrualjournal.go`:
`CreateAccrualJournalEntryLegs(transactionID string, adjustment bool, portions AccrualPortions, mapping AccrualAccountMapping) ([]JournalEntryLeg, error)`
(interest, fee, penalty; six accounts). Integer minor units only; refuse a negative portion or a positive portion with
no account.

## The seam you add — copy the CHARGED-OFF REPAYMENT journal seam line for line (`nexus/internal/apps/loan/conformance/`)
* `vector.go:296` `SeamLoanChargedOffRepaymentJournalEntries` (+ `:269`) → add `SeamLoanAccrualJournalEntries = "loan-accrual-journal-entries"`
* `vector.go:676-685` its request type, `:899-904` its request field, `:1016-1026` its expect field → the twins
* `admit.go:47`, `:58`, `:189`, `:691-696`, `:1318-1363`, `:1765-1774` (its reconstruct function) → the twins
* `impl.go:161-162` dispatch, `:1070-1110` its go evaluator → `goAccrualJournal`
* `grade.go:378-383` → the new seam's case, reusing the leg differ
* `invariants.go:65-66`, `:671-718` its balance assertion, `committed_store_test.go:137` → add the new seam
* drive: model on `impl.go:1582-1638` and registration `impl.go:3028-3036` → ONE drive
  `loan-wrong-accrual-journal-adjustment-not-reversed` (posts an accrual adjustment with the accrual's sides)
* capability: `.softhouse/capabilities-loan.json` → add `accrual-journal-entry`, `in_graded_domain: true`
* vector to copy for shape + provenance: `.softhouse/vectors/loan/LN-TD-RCO-loan-19-chargedoff-repayment-merged.json`

## The observations — transcribe exactly these (driver-selected; verify each sha256 yourself)
All under `.softhouse/capture/tierd-feasibility/accrual-activity-p1-mnt/` (read its OWNER.md sections on the sweep and the join first, ~60 lines). Portions from the loan
read-back (the transaction's `type`, `interestPortion`/`feeChargesPortion`/`penaltyChargesPortion`); legs from the
SWEEP file `journalentries-sweep/loan-<id>.json` (that `transactionId`, `id` order, accounts = `glAccountId`);
accounts from `product-mappings/create-request-<product>.json` (sha256 in its manifest.json): receivable
interest/fee/penalty 7, interestOnLoan 8, incomeFromFee 5, incomeFromPenalty 5 — both products agree.
| vector | loan read-back (sha256) | sweep (sha256) | tx | why |
| --- | --- | --- | --- | --- |
| LN-TD-AC-loan-1-accrual-interest | `loans/loan-1/loan-1-detail-associations-transactions-3.json` (f9f28f67…4b2a) | `journalentries-sweep/loan-1.json` (be126f5b…3c49) | L2 | interest 33 → D 7, C 8 |
| LN-TD-AC-loan-11-accrual-interest-fee-penalty | `loans/loan-11/loan-11-detail-associations-transactions-10.json` (50ee36bc…4207) | `journalentries-sweep/loan-11.json` (49b35540…72c8) | L84 | 33 / 1000 / 1500 → D7 C8, then C5 D7 (fee), then C5 D7 (penalty) — six legs, no merge |
| LN-TD-AC-loan-15-accrual-adjustment | `loans/loan-15/loan-15-detail-associations-transactions-7.json` (9173be13…a557) | `journalentries-sweep/loan-15.json` (1ca0be9a…26fb) | L107 | ADJUSTMENT, interest 279 → D 8, C 7 |
| LN-TD-AC-loan-19-accrual-penalty-only | `loans/loan-19/loan-19-detail-associations-transactions-9.json` (32953337…2dbc) | `journalentries-sweep/loan-19.json` (a484d99b…4f01) | L145 | penalty 1500 alone → C 5, D 7 |
Raw bodies carry decimal major units (`0.33`) — convert to integer minor units (`33`) by exact decimal parsing, never
float. If an observation cannot be reproduced from the observed inputs, THAT is the finding — record it and stop.

## Deliver
The port, the seam, four vectors, the one drive. Measure the drive WITHOUT and WITH the vectors
(`bash .softhouse/briefs/tools/kills.sh loan loan-wrong-accrual-journal-adjustment-not-reversed <worktree>`: ≥1 with, 0
without). Coverage of `CreateAccrualJournalEntryLegs` from the committed-store test (`-count=1`).
`capcount.sh <worktree> loan loan-go` must stay 0.

## Non-negotiables
No float anywhere, including parsing. No balance-named field written. `capture_ref` a JSON record + `capture_sha256`.
**Do not touch `.softhouse/guards/`** (8 pairs), `.softhouse/conformance.sh`, captures, maps. One bounded context: `loan`.
PostgreSQL only; **Oracle Database is prohibited.** Bar: `bash .softhouse/conformance.sh` exits 2 ONLY with
`§4.4.2-RECORDED-DECISION-EXIT`. `git commit -F <file>`. Never commit TASK.md.
