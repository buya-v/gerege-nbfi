# OH-RPJGRADE-CD — port + grade the loan REPAYMENT journal entry. ONE property, concrete inputs. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-rpjgrade` (branch `feat/OHRPJGRADECD`)
Work ONLY in that directory. **Take no captures. Start no container.** The driver pushes; never exercise the push gate.

## Why this brief is narrow
Three sibling runs did exactly this shape by COPYING a merged seam. Do the same. **Do not read findings, maps or
other vectors beyond what is listed. Start writing within 20 iterations. Commit after the first vector passes.**

## The property (one)
`createJournalEntriesForLoanRepayments` [`/Users/buv/fineract/fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/service/AccrualBasedAccountingProcessorForLoan.java:1695-1871`,
read-only, pinned 426a23544; dispatch `:86-89` and `:1369-1377`] for an ORDINARY repayment on a loan NOT charged off
(not goodwill credit, not a loan-to-loan or account transfer, not repayment-at-disbursement so `isIncomeFromFee` is
false, no charge refund, no tax):
* credits, merged by account in a LinkedHashMap in slot order: principal → LOAN_PORTFOLIO, interest →
  INTEREST_RECEIVABLE, fees → FEES_RECEIVABLE, penalties → PENALTIES_RECEIVABLE, overpayment → OVERPAYMENT;
* then ONE DEBIT of the total to FUND_SOURCE (the payment-channel account when the transaction's paymentTypeId has a
  channel mapping, else the product's fund source). Credits first, the debit last.
The excluded branches are NOT observed: the port must take no input for them (no goodwill, transfer, income-from-fee,
tax or charge-refund parameter). It is not a place to guess.

## The port — a NEW pure function
Model it on `nexus/internal/apps/loan/chargedoffwriteoffjournal.go` (`CreateChargedOffWriteOffJournalEntryLegs`:102 —
read it whole: same merged-credits-then-one-debit shape). New file `nexus/internal/apps/loan/repaymentjournal.go`:
`CreateRepaymentJournalEntryLegs(transactionID string, portions RepaymentPortions, mapping RepaymentAccountMapping) ([]JournalEntryLeg, error)`,
where the mapping carries the RESOLVED fund-source account (the caller resolves the channel). Integer minor units only.
Refuse a negative portion, a positive portion with no mapped account, a positive total with no fund-source account.

## The seam you add — copy the CHARGED-OFF WRITE-OFF journal seam line for line (`nexus/internal/apps/loan/conformance/`)
* `vector.go:243` `SeamLoanChargedOffWriteOffJournalEntries` (+ `:221`) → add `SeamLoanRepaymentJournalEntries = "loan-repayment-journal-entries"`
* `vector.go:544-551` its request type, `:756-760` its request field, `:856-863` its expect field → the twins
* `admit.go:46`, `:55`, `:179`, `:586-591`, `:1103-1150`, `:1413-1426` (its reconstruct function) → the twins
* `impl.go:157-158` dispatch, `:919-991` its go evaluator → `goRepaymentJournal`
* `grade.go:206-216` its differ, `:362-363` its case → reuse the differ for the new seam
* `invariants.go:61-62`, `:566-613` its balance assertion, `committed_store_test.go:135` → add the new seam
* drive: model on `impl.go:1403-1451` (its wrong mode / evaluator) and registration `impl.go:2759-2765` → ONE drive
  `loan-wrong-repayment-journal-one-debit-per-portion` (posts one FUND_SOURCE debit per credited portion instead of one total)
* capability: `.softhouse/capabilities-loan.json` → add `repayment-journal-entry`, `in_graded_domain: true`
* vector to copy for shape + provenance: `.softhouse/vectors/loan/LN-TD-WO-loan-4-chargedoff-writeoff-merged.json`

## The observations — transcribe exactly these (driver-selected; verify each sha256 yourself)
All under `.softhouse/capture/tierd-feasibility/chargeback-mnt/`. Portions from the loan read-back (the repayment transaction's `principalPortion`/`interestPortion`/
`feeChargesPortion`/`penaltyChargesPortion`/`overpaymentPortion`; `paymentDetailData.paymentType.id` is 11 AUTOPAY);
legs from the journalentries file (that `transactionId`, `id` order, accounts = `glAccountId`); accounts from
`product-mappings/create-request-LP1.json` (87e5c4e8…62e1): loanPortfolio 10, receivable interest/fee/penalty 7,
overpayment 18, fundSource 4, and the ONLY channel mapping is paymentTypeId 1 → 17 — so paymentType 11 resolves to 4.
All three loans are product 6 (LP1), not charged off.
| vector | loan read-back (sha256) | journal entries (sha256) | tx | why |
| --- | --- | --- | --- | --- |
| LN-TD-RP-loan-14-repayment-principal | `loans/loan-14/loan-14-detail-associations-transactions-2.json` (ed7f162b…911c) | `journalentries/loan-14/loan-14-journalentries-2.json` (793a7b2f…d351) | L66 | principal 250 → C 10, D 4 |
| LN-TD-RP-loan-18-repayment-fee | `loans/loan-18/loan-18-detail-associations-transactions-6.json` (a8c3fdd1…f55b) | `journalentries/loan-18/loan-18-journalentries-6.json` (85de3d66…6f27) | L93 | principal 250 + fee 20 → C 10, C 7, one D 270 |
| LN-TD-RP-loan-19-repayment-overpayment | `loans/loan-19/loan-19-detail-associations-transactions-4.json` (e1dc54d6…dd98) | `journalentries/loan-19/loan-19-journalentries-4.json` (091bc46b…f8af8) | L98 | principal 250 + overpayment 250 → C 10, C 18, one D 500 |
Some journal-entry files also hold legs of a LATER reversal of the same transaction (`reversed`, mirror legs): take only
the original posting's legs and say so in the provenance. Raw bodies carry decimal major units (`270.0`) — convert to
integer minor units (`27000`) by exact decimal parsing, never float. If an observation cannot be reproduced from the
observed inputs, THAT is the finding — record the numbers and stop; do not bend the port.

## Deliver
The port, the seam, three vectors, the one drive. Measure the drive WITHOUT and WITH the vectors
(`bash .softhouse/briefs/tools/kills.sh loan loan-wrong-repayment-journal-one-debit-per-portion <worktree>`: ≥1 with, 0
without). Coverage of `CreateRepaymentJournalEntryLegs` from the committed-store test (`-count=1`).
`capcount.sh <worktree> loan loan-go` must stay 0.

## Non-negotiables
No float anywhere, including parsing. No balance-named field written. `capture_ref` a JSON record + `capture_sha256`.
**Do not touch `.softhouse/guards/`** (8 pairs), `.softhouse/conformance.sh`, captures, maps. One bounded context: `loan`.
PostgreSQL only; **Oracle Database is prohibited.** Bar: `bash .softhouse/conformance.sh` exits 2 ONLY with
`§4.4.2-RECORDED-DECISION-EXIT`. `git commit -F <file>`. Never commit TASK.md.
