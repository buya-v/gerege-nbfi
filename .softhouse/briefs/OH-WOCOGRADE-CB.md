# OH-WOCOGRADE-CB — port + grade the WRITE-OFF of a CHARGED-OFF loan's journal entry. ONE property. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-wocograde` (branch `feat/OHWOCOGRADECB`)
Work ONLY in that directory. **Take no captures. Start no container.** The driver pushes; never exercise the push gate.

## Why this brief is narrow
Two sibling runs just did exactly this shape in ~350 events by COPYING a merged seam. Do the same. **Do not read
findings, maps or other vectors beyond what is listed. Start writing within 20 iterations. Commit after the first
vector passes.**

## The property (one)
`createJournalEntriesForWriteOffsWhenLoanIsChargedOff` [`/Users/buv/fineract/fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/service/AccrualBasedAccountingProcessorForLoan.java:1616-1694`,
read-only, pinned 426a23544; the dispatch is `:1379-1386`]. For a write-off on a loan MARKED CHARGED OFF:
* principal > 0: CREDIT CHARGE_OFF_FRAUD_EXPENSE if the loan is fraud, else CHARGE_OFF_EXPENSE;
* interest > 0: CREDIT INCOME_FROM_CHARGE_OFF_INTEREST; fees > 0: CREDIT INCOME_FROM_CHARGE_OFF_FEES;
  penalties > 0: CREDIT INCOME_FROM_CHARGE_OFF_PENALTY; overpayment > 0: CREDIT OVERPAYMENT;
* credits to the SAME account MERGE (GLAccountBalanceHolder LinkedHashMap: one leg, the sum, first insertion position);
* then ONE DEBIT of the total to LOSSES_WRITTEN_OFF — the FUND_SOURCE debits `populateCreditDebitMaps` accumulates
  are NEVER posted (only the credit map is iterated). Credits first, the debit last.
Port the whole method (all five portions); the observations exercise principal, interest, fee+penalty merge and fraud.

## The port — a NEW pure function
Model it on `nexus/internal/apps/loan/chargeoffjournal.go` (`CreateChargeOffJournalEntryLegs`:117 — read it whole; it
already has the merge and the fraud switch). New file `nexus/internal/apps/loan/chargedoffwriteoffjournal.go`:
`CreateChargedOffWriteOffJournalEntryLegs(transactionID string, portions ChargedOffWriteOffPortions, fraud bool, mapping ChargedOffWriteOffAccountMapping) ([]JournalEntryLeg, error)`.
Integer minor units only. Refuse a negative portion and a positive portion with no mapped account.

## The seam you add — copy the CHARGE-OFF journal seam line for line (`nexus/internal/apps/loan/conformance/`)
* `vector.go:219` `SeamLoanChargeOffJournalEntries` (+ `:198`) → add `SeamLoanChargedOffWriteOffJournalEntries = "loan-chargedoff-writeoff-journal-entries"`
* `vector.go:472-478` `ChargeOffJournalRequest`, `:679-682` its request field, `:770-777` its expect field → the twins
* `admit.go:46`, `:55`, `:176`, `:537-542`, `:1002-1046`, `:1233-1244` (`reconstructChargeOffJournalLegs`) → the twins
* `impl.go:155-156` dispatch, `:846-914` `goChargeOffJournal` → `goChargedOffWriteOffJournal`
* `grade.go:193-202` `diffChargeOffJournalLegs`, `:346-347` its case → reuse the differ for the new seam
* `invariants.go:59-60`, `:564-580` `assertChargeOffJournalBalanced`, `committed_store_test.go:134` → add the new seam
* drive: model on `impl.go:1270-1305` (`chargeOffJournalWrongMode` / `wrongChargeOffJournal`) and registration
  `impl.go:2603-2609` → ONE drive `loan-wrong-chargedoff-writeoff-debits-fund-source` (posts the per-portion FUND_SOURCE
  debits instead of the one LOSSES_WRITTEN_OFF debit)
* capability: `.softhouse/capabilities-loan.json` → add `chargedoff-writeoff-journal-entry`, `in_graded_domain: true`
* vector to copy for shape + provenance: `.softhouse/vectors/loan/LN-TD-CO-loan-7-chargeoff-merged-legs.json`

## The observations — transcribe exactly these (driver-selected; verify each sha256 yourself)
All under `.softhouse/capture/tierd-feasibility/writeoff-mnt/`. Read its OWNER.md section "`writeOff` on a charged-off loan" first (~50 lines). Portions and `fraud`
from the loan read-back (the writeOff transaction's `principalPortion`/`interestPortion`/`feeChargesPortion`/
`penaltyChargesPortion`/`overpaymentPortion`); legs from the journalentries file (that `transactionId`, `id` order,
accounts = `glAccountId`); account ids from that loan's product create request in `product-mappings/` (sha256 in
`product-mappings/manifest.json`) — **ids differ from earlier replays; use THIS replay's**.
| vector | loan read-back (sha256) | journal entries (sha256) | tx | why |
| --- | --- | --- | --- | --- |
| LN-TD-WO-loan-4-chargedoff-writeoff-merged | `loans/loan-4/loan-4-detail-associations-transactions-4.json` (8e624b01…88b9) | `journalentries/loan-4/loan-4-journalentries-3.json` (8f39dc09…5c10) | L16 | 1000/30/103/10: credits 1000, 30, 113 (fee+penalty merged), one debit 1143; product LP1_INTEREST_FLAT |
| LN-TD-WO-loan-9-chargedoff-writeoff-fraud | `loans/loan-9/loan-9-detail-associations-transactions-7.json` (5adfae53…3e96) | `journalentries/loan-9/loan-9-journalentries-4.json` (02800841…e97c) | L37 | FRAUD: credit 750 to the fraud expense, debit 750; product LP2_DOWNPAYMENT_AUTO_ADVANCED_PAYMENT_ALLOCATION |
| LN-TD-WO-loan-7-chargedoff-writeoff-progressive | `loans/loan-7/loan-7-detail-associations-transactions-5.json` (5c58eb12…284c) | `journalentries/loan-7/loan-7-journalentries-2.json` (0988b3be…092b) | L27 | 83.57 + 1.47 → one debit 85.04; product LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ZERO_INTEREST_CHARGE_OFF |
Raw bodies carry decimal major units (`83.57`) — convert to integer minor units (`8357`) by exact decimal parsing,
never float. If an observation cannot be reproduced from the observed inputs, THAT is the finding — record the numbers
and stop; do not bend the port.

## Deliver
The port, the seam, three vectors, the one drive. Measure the drive WITHOUT and WITH the vectors
(`bash .softhouse/briefs/tools/kills.sh loan loan-wrong-chargedoff-writeoff-debits-fund-source <worktree>`: ≥1 with, 0
without). Coverage of `CreateChargedOffWriteOffJournalEntryLegs` from the committed-store test (`-count=1`).
`capcount.sh <worktree> loan loan-go` must stay 0.

## Non-negotiables
No float anywhere, including parsing. No balance-named field written. `capture_ref` a JSON record + `capture_sha256`.
**Do not touch `.softhouse/guards/`** (8 pairs), `.softhouse/conformance.sh`, captures, maps. One bounded context: `loan`.
PostgreSQL only; **Oracle Database is prohibited.** Bar: `bash .softhouse/conformance.sh` exits 2 ONLY with
`§4.4.2-RECORDED-DECISION-EXIT`. `git commit -F <file>`. Never commit TASK.md.
