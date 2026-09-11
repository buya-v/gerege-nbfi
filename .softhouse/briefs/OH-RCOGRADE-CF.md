# OH-RCOGRADE-CF — port + grade a REPAYMENT on a CHARGED-OFF loan (the recovery posting). ONE property. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-rcograde` (branch `feat/OHRCOGRADECF`)
Work ONLY in that directory. **Take no captures. Start no container.** The driver pushes; never exercise the push gate.

## Why this brief is narrow
Four sibling runs did this shape by COPYING a merged seam. Do the same. **Do not read findings, maps or other vectors
beyond what is listed. Start writing within 20 iterations. Commit after the first vector passes.**

## The property (one)
`createJournalEntriesForRepaymentWhenLoanIsChargedOff` [`/Users/buv/fineract/fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/service/AccrualBasedAccountingProcessorForLoan.java:1388-1615`,
read-only, pinned 426a23544; dispatch `:1369-1377`] for transaction type **REPAYMENT** on a loan MARKED CHARGED OFF:
every positive portion — principal, interest, fees, penalties — is CREDITED to INCOME_FROM_RECOVERY (whatever the
fraud flag), and DEBITED to FUND_SOURCE (the channel account when the paymentTypeId has a channel mapping); both sides
go through GLAccountBalanceHolder, so they MERGE by account (one Recoveries credit, one fund-source debit, each the
sum). Credits are posted first, then debits. Read the overpayment branch (`:1540-1560`) and port it as the Java has it.
The method's OTHER transaction types (merchant-issued refund, payout refund, goodwill credit, the else-branch) are NOT
observed on a charged-off loan: the port takes a repayment only — no transaction-type parameter.

## The port — a NEW pure function
Model it on `nexus/internal/apps/loan/repaymentjournal.go` (`CreateRepaymentJournalEntryLegs`:102 — read it whole).
New file `nexus/internal/apps/loan/chargedoffrepaymentjournal.go`:
`CreateChargedOffRepaymentJournalEntryLegs(transactionID string, portions RepaymentPortions, mapping ChargedOffRepaymentAccountMapping) ([]JournalEntryLeg, error)`
(reuse `RepaymentPortions`; the mapping carries INCOME_FROM_RECOVERY, the resolved fund source, and whatever the
overpayment branch needs). Integer minor units only; refuse a negative portion or a positive portion with no account.

## The seam you add — copy the REPAYMENT journal seam (merged in OH-RPJGRADE-CD) line for line (`nexus/internal/apps/loan/conformance/`)
* `vector.go:267` `SeamLoanRepaymentJournalEntries` (+ `:245`) → add `SeamLoanChargedOffRepaymentJournalEntries = "loan-chargedoff-repayment-journal-entries"`
* `vector.go:612-619` its request type, `:828-832` its request field, `:936-943` its expect field → the twins
* `admit.go:47`, `:57`, `:184`, `:636-641`, `:1214-1258`, `:1594-1604` (its reconstruct function) → the twins
* `impl.go:159-160` dispatch, `:996-1065` `goRepaymentJournal` → `goChargedOffRepaymentJournal`
* `grade.go:220-228` its differ, `:376-377` its case → reuse the differ for the new seam
* `invariants.go:63-64`, `:619-665` its balance assertion, `committed_store_test.go:136` → add the new seam
* drive: model on `impl.go:1537-1593` (its wrong mode / evaluator) and registration `impl.go:2908-2914` → ONE drive
  `loan-wrong-chargedoff-repayment-to-portfolio` (posts the charged-off repayment like an ordinary one: principal to
  LOAN_PORTFOLIO, interest to INTEREST_RECEIVABLE)
* capability: `.softhouse/capabilities-loan.json` → add `chargedoff-repayment-journal-entry`, `in_graded_domain: true`
* vector to copy for shape + provenance: `.softhouse/vectors/loan/LN-TD-RP-loan-18-repayment-fee.json`

## The observations — transcribe exactly these (driver-selected; verify each sha256 yourself)
All under `.softhouse/capture/tierd-feasibility/chargeoff-mnt/`. Portions and `fraud` from the loan read-back (the repayment's `principalPortion`/`interestPortion`/
`feeChargesPortion`/`penaltyChargesPortion`/`overpaymentPortion`; the loan's non-reversed chargeOff precedes it;
`paymentDetailData.paymentType.id` is 5); legs from the journalentries file (that `transactionId`, `id` order,
accounts = `glAccountId`); accounts from the product create requests in `product-mappings/` (sha256 in its
manifest.json): incomeFromRecovery 17, fundSource 1, the only channel mapping is paymentTypeId 1 → 18 — so type 5 → 1.
| vector | loan read-back (sha256) | journal entries (sha256) | tx | why |
| --- | --- | --- | --- | --- |
| LN-TD-RCO-loan-19-chargedoff-repayment-merged | `loans/loan-19/loan-19-detail-associations-transactions-3.json` (45000de9…c567f) | `journalentries/loan-19/loan-19-journalentries-4.json` (75a8281f…7c56) | L61 | FRAUD loan, principal 633 + interest 10 → ONE credit 643 to Recoveries (17), one debit 643 to 1; product LP1_INTEREST_FLAT |
| LN-TD-RCO-loan-37-chargedoff-repayment-principal | `loans/loan-37/loan-37-detail-associations-transactions-3.json` (349fc11a…6c0d) | `journalentries/loan-37/loan-37-journalentries-4.json` (af650272…6569) | L125 | principal 500 → credit 17, debit 1; product LP1 |
Raw bodies carry decimal major units (`643.0`) — convert to integer minor units (`64300`) by exact decimal parsing,
never float. If an observation cannot be reproduced from the observed inputs, THAT is the finding — record the numbers
and stop; do not bend the port.

## Deliver
The port, the seam, two vectors, the one drive. Measure the drive WITHOUT and WITH the vectors
(`bash .softhouse/briefs/tools/kills.sh loan loan-wrong-chargedoff-repayment-to-portfolio <worktree>`: ≥1 with, 0 without).
Coverage of `CreateChargedOffRepaymentJournalEntryLegs` from the committed-store test (`-count=1`).
`capcount.sh <worktree> loan loan-go` must stay 0.

## Non-negotiables
No float anywhere, including parsing. No balance-named field written. `capture_ref` a JSON record + `capture_sha256`.
**Do not touch `.softhouse/guards/`** (8 pairs), `.softhouse/conformance.sh`, captures, maps. One bounded context: `loan`.
PostgreSQL only; **Oracle Database is prohibited.** Bar: `bash .softhouse/conformance.sh` exits 2 ONLY with
`§4.4.2-RECORDED-DECISION-EXIT`. `git commit -F <file>`. Never commit TASK.md.
