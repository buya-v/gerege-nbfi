# OH-MIRGRADE-CK — port + grade a MERCHANT-ISSUED REFUND on a CHARGED-OFF loan. ONE property. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-mirgrade` (branch `feat/OHMIRGRADECK`)
Work ONLY in that directory. **Take no captures. Start no container.** The driver pushes; never exercise the push gate.

## Why this brief is narrow
Six sibling runs did this shape by COPYING a merged seam. Do the same. **Do not read findings, maps or other vectors
beyond what is listed. Start writing within 20 iterations. Commit after the first vector passes.**

## The property (one)
The MERCHANT-ISSUED-REFUND arm of `createJournalEntriesForRepaymentWhenLoanIsChargedOff`
[`/Users/buv/fineract/fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/service/AccrualBasedAccountingProcessorForLoan.java:1388-1615`,
read-only, pinned 426a23544] on a loan MARKED CHARGED OFF and NOT fraud: principal → CREDIT CHARGE_OFF_EXPENSE;
interest → CREDIT INCOME_FROM_CHARGE_OFF_INTEREST; fees → INCOME_FROM_CHARGE_OFF_FEES; penalties →
INCOME_FROM_CHARGE_OFF_PENALTY; overpayment → CREDIT OVERPAYMENT; every portion DEBITS FUND_SOURCE (the channel account
when the paymentTypeId has a channel mapping). Both sides through GLAccountBalanceHolder (merge by account); credits
posted first, then debits. The FRAUD split (principal to CHARGE_OFF_FRAUD_EXPENSE) is NOT observed: the port REFUSES a
fraud loan. Payout refund and goodwill arms are NOT observed and have no input.

## The port — a NEW pure function
Model it on `nexus/internal/apps/loan/chargedoffrepaymentjournal.go` (`CreateChargedOffRepaymentJournalEntryLegs`:61 —
read it whole: same arm-of-:1388 shape, different accounts). New file `nexus/internal/apps/loan/chargedoffmerchantrefundjournal.go`:
`CreateChargedOffMerchantRefundJournalEntryLegs(transactionID string, portions RepaymentPortions, fraud bool, mapping ChargedOffMerchantRefundAccountMapping) ([]JournalEntryLeg, error)`.
Integer minor units only; refuse fraud=true, a negative portion, a positive portion with no account.

## The seam you add — copy the CHARGED-OFF REPAYMENT journal seam line for line (`nexus/internal/apps/loan/conformance/`)
* `vector.go:296` `SeamLoanChargedOffRepaymentJournalEntries` (+ `:269`) → add `SeamLoanChargedOffMerchantRefundJournalEntries = "loan-chargedoff-merchant-refund-journal-entries"`
* `vector.go:707-716` its request type, `:970-975` its request field, `:1091-1101` its expect field → the twins
* `admit.go:47`, `:58`, `:189`, `:694-699`, `:1355-1400`, `:1855-1864` (its reconstruct function) → the twins
* `impl.go:161-162` dispatch, `:1072-1112` its go evaluator → `goChargedOffMerchantRefundJournal`
* `grade.go:378-383` → the new seam's case, reusing the leg differ
* `invariants.go:65-66`, `:673-720` its balance assertion, `committed_store_test.go:137` → add the new seam
* drive: model on `impl.go:1636-1692` and registration `impl.go:3128-3136` → ONE drive
  `loan-wrong-chargedoff-merchant-refund-as-recovery` (credits every portion to INCOME_FROM_RECOVERY, as the repayment arm does)
* capability: `.softhouse/capabilities-loan.json` → add `chargedoff-merchant-refund-journal-entry`, `in_graded_domain: true`
* vector to copy for shape + provenance: `.softhouse/vectors/loan/LN-TD-RCO-loan-19-chargedoff-repayment-merged.json`

## The observations — transcribe exactly these (driver-selected; verify each sha256 yourself)
All under `.softhouse/capture/tierd-feasibility/chargeoff-p3-mnt/` (read its OWNER.md join section first, ~50 lines). Portions and `fraud` (false) from the loan
read-back (the merchantIssuedRefund transaction's portions; `paymentDetailData.paymentType.id` 4); legs from the SWEEP
`journalentries-sweep/loan-<id>.json` (that `transactionId`, `id` order, accounts = `glAccountId`); accounts from
`product-mappings/create-request-<product>.json` (sha256 in its manifest.json): fundSource 7, chargeOffExpense 18,
incomeFromChargeOffInterest 16, overpayment 13; the only channel mapping is paymentTypeId 1 → 19, so type 4 → 7.
| vector | loan read-back (sha256) | sweep (sha256) | tx | why |
| --- | --- | --- | --- | --- |
| LN-TD-MIR-loan-48-refund-principal-interest-overpayment | `loans/loan-48/loan-48-detail-associations-transactions-6.json` (3a37faf9…6fd1) | `journalentries-sweep/loan-48.json` (a699195a…6e99) | L475 | 800 + 18.49 + overpayment 81.51 → C18, C16, C13, one D7 900 |
| LN-TD-MIR-loan-48-refund-principal-interest | `loans/loan-48/loan-48-detail-associations-transactions-9.json` (71165282…1aa7) | same sweep | L477 | 883.10 + 16.90 → C18, C16, D7 900 |
| LN-TD-MIR-loan-50-refund-principal | `loans/loan-50/loan-50-detail-associations-transactions-9.json` (cccc3027…ec74) | `journalentries-sweep/loan-50.json` (c4c3cc4d…56fc) | L498 | 900 → C18, D7 |
**L475 was later reversed by a replay:** its transactionId also carries the mirror legs (ids 1259-1262). Take ONLY the
original posting (ids 1240-1243) and say so in the provenance. Raw bodies carry decimal major units (`81.51`) — convert
to integer minor units by exact decimal parsing, never float. If an observation cannot be reproduced from the observed
inputs, THAT is the finding — record it and stop.

## Deliver
The port, the seam, three vectors, the one drive. Measure the drive WITHOUT and WITH the vectors
(`bash .softhouse/briefs/tools/kills.sh loan loan-wrong-chargedoff-merchant-refund-as-recovery <worktree>`: ≥1 with, 0
without). Coverage of `CreateChargedOffMerchantRefundJournalEntryLegs` from the committed-store test (`-count=1`).
`capcount.sh <worktree> loan loan-go` must stay 0.

## Non-negotiables
No float anywhere, including parsing. No balance-named field written. `capture_ref` a JSON record + `capture_sha256`.
**Do not touch `.softhouse/guards/`** (8 pairs), `.softhouse/conformance.sh`, captures, maps. One bounded context: `loan`.
PostgreSQL only; **Oracle Database is prohibited.** Bar: `bash .softhouse/conformance.sh` exits 2 ONLY with
`§4.4.2-RECORDED-DECISION-EXIT`. `git commit -F <file>`. Never commit TASK.md.
