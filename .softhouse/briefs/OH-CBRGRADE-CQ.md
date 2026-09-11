# OH-CBRGRADE-CQ — port + grade the loan CREDIT-BALANCE-REFUND journal entry. ONE property. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-cbrgrade` (branch `feat/OHCBRGRADECQ`)
Work ONLY in that directory. **Take no captures. Start no container.** The driver pushes; never exercise the push gate.

## Why this brief is narrow
Ten sibling runs did this shape by COPYING a merged seam. **Read only what is listed. Start writing within 20
iterations. Commit after the first vector passes.**

## The property (one)
`createJournalEntriesForCreditBalanceRefund` → `createJournalEntriesForLoanCreditBalanceRefund` →
`determineAccrualAccountForCBR` [`/Users/buv/fineract/fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/service/AccrualBasedAccountingProcessorForLoan.java:2113-2170`]
and `AccountingProcessorHelper.createSplitJournalEntriesForLoan` [`…/AccountingProcessorHelper.java`, grep the name], read-only,
pinned 426a23544. Legs in posting order: DEBIT principal (if > 0) to LOAN_PORTFOLIO — or, if the loan is charged off,
CHARGE_OFF_EXPENSE, or CHARGE_OFF_FRAUD_EXPENSE when also fraud; then DEBIT overpayment (if > 0) to OVERPAYMENT; then ONE
CREDIT of the total to the fund source (channel account when the paymentTypeId has a channel mapping). Every branch of
`determineAccrualAccountForCBR` is observed below — port it whole.

## The port — a NEW pure function
Model it on `nexus/internal/apps/loan/chargebackjournal.go` (`CreateChargebackJournalEntryLegs`:86 — read it whole: it
already has the charged-off / fraud account switch). New file `nexus/internal/apps/loan/creditbalancerefundjournal.go`:
`CreateCreditBalanceRefundJournalEntryLegs(transactionID string, principal, overpayment MinorUnits, chargedOff, fraud bool, mapping CreditBalanceRefundAccountMapping) ([]JournalEntryLeg, error)`.
Integer minor units only; refuse a negative portion or a positive portion with no account.

## The seam you add — copy the REPAYMENT journal seam line for line
Its exact entry points are generated in `.softhouse/maps/loan.md` § "Seam entry points", row
`loan-repayment-journal-entries` (constant, request/expect fields, admit cases, evaluator, grade case, invariants,
committed-store test), and its drive in § "Drives registered", row `loan-wrong-repayment-journal-one-debit-per-portion`.
Read ONLY those two rows of the map. Add `SeamLoanCreditBalanceRefundJournalEntries = "loan-credit-balance-refund-journal-entries"`,
the twins, and ONE drive `loan-wrong-cbr-ignores-charge-off` (principal always to LOAN_PORTFOLIO). Capability:
`.softhouse/capabilities-loan.json` → `credit-balance-refund-journal-entry`, `in_graded_domain: true`. Vector to copy for
shape + provenance: `.softhouse/vectors/loan/LN-TD-CB-loan-17-chargedoff-fee.json`.

## The observations — transcribe exactly these (driver-selected; verify each sha256 yourself)
Under `.softhouse/capture/tierd-feasibility/cbr-mnt/` (read its OWNER.md, ~60 lines). Portions (`principalPortion`, `overpaymentPortion`), `fraud` and the
charged-off state from the loan read-back; legs from the SWEEP `journalentries-sweep/loan-<id>.json` (that
`transactionId`, `id` order, accounts = `glAccountId`); accounts from `product-mappings/create-request-<product>.json`
(sha256 in its manifest.json): fundSource 4, loanPortfolio 5, overpayment 16, chargeOffExpense 15, chargeOffFraudExpense
11 — both products agree; the only channel mapping is paymentTypeId 1 → 19, these use type 6 → 4.
| vector | loan read-back (sha256) | sweep (sha256) | tx | why |
| --- | --- | --- | --- | --- |
| LN-TD-CBR-loan-1-overpayment | `loans/loan-1/loan-1-detail-associations-transactions-5.json` (d6fbc06f…c9a1) | `journalentries-sweep/loan-1.json` (83357bfd…bb10) | L5 | D16 200, C4 200 — **original legs ids 10-11 only** (21-22 are a later reversal pair) |
| LN-TD-CBR-loan-19-principal-overpayment | `loans/loan-19/loan-19-detail-associations-transactions-5.json` (41d3ed57…139d) | `journalentries-sweep/loan-19.json` (26d5c911…25a3) | L112 | D5 10, D16 190, C4 200 |
| LN-TD-CBR-loan-28-chargedoff | `loans/loan-28/loan-28-detail-associations-transactions-4.json` (eaf52c9d…4610) | `journalentries-sweep/loan-28.json` (6532f576…6852) | L175 | CHARGED OFF: D15 250, C4 250 |
| LN-TD-CBR-loan-27-chargedoff-fraud | `loans/loan-27/loan-27-detail-associations-transactions-4.json` (128cc57d…9062) | `journalentries-sweep/loan-27.json` (0e58e97e…8270) | L169 | CHARGED OFF + FRAUD: D11 250, C4 250 |
Raw bodies carry decimal major units — convert to integer minor units by exact decimal parsing, never float. If an
observation cannot be reproduced from the observed inputs, THAT is the finding — record it and stop.

## Deliver
The port, the seam, four vectors, the one drive. Measure the drive WITHOUT and WITH the vectors
(`bash .softhouse/briefs/tools/kills.sh loan loan-wrong-cbr-ignores-charge-off <worktree>`: ≥1 with, 0 without). Coverage of
the port from the committed-store test (`-count=1`). `capcount.sh <worktree> loan loan-go` must stay 0.

## Non-negotiables
No float anywhere, including parsing. No balance-named field written. `capture_ref` a JSON record + `capture_sha256`.
**Do not touch `.softhouse/guards/`** (8 pairs), `.softhouse/conformance.sh`, captures, maps. One bounded context: `loan`.
PostgreSQL only; **Oracle Database is prohibited.** Bar: `bash .softhouse/conformance.sh` exits 2 ONLY with
`§4.4.2-RECORDED-DECISION-EXIT`. `git commit -F <file>`. Never commit TASK.md.
