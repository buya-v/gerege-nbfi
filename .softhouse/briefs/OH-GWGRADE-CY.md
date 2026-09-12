# OH-GWGRADE-CY — port + grade the loan GOODWILL-CREDIT journal entry (loan NOT charged off). ONE property. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-gwgrade` (branch `feat/OHGWGRADECY`)
Work ONLY in that directory. **Take no captures. Start no container.** The driver pushes; never exercise the push gate.

## Why this brief is narrow
Fifteen sibling runs did this shape by COPYING a merged seam. **Read only what is listed. Start writing within 20
iterations. Commit after the first vector passes.** If the bar trips a guard-cost CEILING, say so in the commit
message and do not loop re-running it — the driver re-runs it.

## The property (one)
The GOODWILL-CREDIT branch of `createJournalEntriesForLoanRepayments`
[`/Users/buv/fineract/fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/service/AccrualBasedAccountingProcessorForLoan.java:1695-1871`,
read-only, pinned 426a23544] on a loan NOT charged off — the transaction type is goodwill credit, not a transfer:
* CREDITS exactly as an ordinary repayment: principal → LOAN_PORTFOLIO, interest → INTEREST_RECEIVABLE, fees →
  FEES_RECEIVABLE, penalties → PENALTIES_RECEIVABLE, overpayment → OVERPAYMENT (LinkedHashMap, merge by account);
* DEBITS through `debitAccountMapForGoodwillCredit` (`LoanCommonAccountingHelper.populateDebitAccountEntry` — merges a
  portion into an existing entry whose GL account MATCHES): principal → GOODWILL_CREDIT, interest →
  INCOME_FROM_GOODWILL_CREDIT_INTEREST, fees → INCOME_FROM_GOODWILL_CREDIT_FEES, penalties →
  INCOME_FROM_GOODWILL_CREDIT_PENALTY, overpayment → GOODWILL_CREDIT; posted in insertion order AFTER all credits.
The charged-off goodwill arm (a different method, :1388) is NOT in this run; the port refuses a charged-off input.

## The port — a NEW pure function
Model it on `nexus/internal/apps/loan/repaymentjournal.go` (`CreateRepaymentJournalEntryLegs` — read it whole: the same
credit side). New file `nexus/internal/apps/loan/goodwillcreditjournal.go`:
`CreateGoodwillCreditJournalEntryLegs(transactionID string, portions RepaymentPortions, chargedOff bool, mapping GoodwillCreditAccountMapping) ([]JournalEntryLeg, error)`.
Integer minor units only; refuse chargedOff, a negative portion, a positive portion with no credit or no debit account.

## The seam you add — copy the REPAYMENT journal seam line for line
Its exact entry points are generated in `.softhouse/maps/loan.md` § "Seam entry points", row
`loan-repayment-journal-entries`, and its drive in § "Drives registered", row
`loan-wrong-repayment-journal-one-debit-per-portion`. Read ONLY those two rows of the map. Add
`SeamLoanGoodwillCreditJournalEntries = "loan-goodwill-credit-journal-entries"`, the twins, and ONE drive
`loan-wrong-goodwill-debits-fund-source` (posts ONE fund-source debit of the total, as an ordinary repayment does).
Capability: `.softhouse/capabilities-loan.json` → `goodwill-credit-journal-entry`, `in_graded_domain: true`. Vector to copy
for shape + provenance: `.softhouse/vectors/loan/LN-TD-RP-loan-18-repayment-fee.json`.

## The observations — transcribe exactly these (driver-selected; verify each sha256 yourself)
Portions from the goodwillCredit transaction in the loan read-back; legs from the capture's SWEEP
`journalentries-sweep/loan-<id>.json` (that `transactionId`, `id` order, accounts = `glAccountId`); accounts from that
capture's `product-mappings/create-request-<product>.json` (sha256 in its manifest.json). NOTE: account ids DIFFER between
the two captures — read each vector's ids from its own capture.
| vector | capture dir (under `.softhouse/capture/tierd-feasibility/`) | loan read-back (sha256) | sweep (sha256) | tx | why |
| --- | --- | --- | --- | --- | --- |
| LN-TD-GW-loan-42-principal | `chargeoff-p3-mnt/` | `loans/loan-42/loan-42-detail-associations-transactions-2.json` (33413978…6564) | `journalentries-sweep/loan-42.json` (ac4cd212…17cb) | L444 | principal 10.00: C6 (portfolio), D20 (goodwill credit); product LP2_ADV_PYMNT_INTEREST_DAILY_INTEREST_RECALCULATION_ZERO_INTEREST_CHARGE_OFF (e1b7a3dd…bf70) |
| LN-TD-GW-loan-46-overpayment | `chargeoff-p3-mnt/` | `loans/loan-46/loan-46-detail-associations-transactions-9.json` (23ca88b6…1634) | `journalentries-sweep/loan-46.json` (22ca45f6…58b7) | L466 | overpayment 500.00: C13 (overpayment), D20 (goodwill credit); NOT charged off (fraud flag is set but irrelevant here); product LP2_ADV_PYMNT_ZERO_INTEREST_CHARGE_OFF_DELINQUENT_REASON_INTEREST_RECALC (87eb7f45…cd2f) |
| LN-TD-GW-loan-26-penalty | `accrual-activity-p1-mnt/` | `loans/loan-26/loan-26-detail-associations-transactions-8.json` (3fc00acd…f4b9) | `journalentries-sweep/loan-26.json` (a9773081…cd98) | L267 | penalty 15.00: C7 (penalty receivable), D12 (goodwill-credit penalty income); product LP1_ADV_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL (ab61ac18…7d94) |
Raw bodies carry decimal major units — convert to integer minor units by exact decimal parsing, never float. If an
observation cannot be reproduced from the observed inputs, THAT is the finding — record it and stop.

## Deliver
The port, the seam, three vectors, the one drive. Measure the drive WITHOUT and WITH the vectors
(`bash .softhouse/briefs/tools/kills.sh loan loan-wrong-goodwill-debits-fund-source <worktree>`: ≥1 with, 0 without).
Coverage of the port from the committed-store test (`-count=1`). `capcount.sh <worktree> loan loan-go` must stay 0.

## Non-negotiables
No float anywhere, including parsing. No balance-named field written. `capture_ref` a JSON record + `capture_sha256`.
**Do not touch `.softhouse/guards/`** (8 pairs), `.softhouse/conformance.sh`, captures, maps. One bounded context: `loan`.
PostgreSQL only; **Oracle Database is prohibited.** Bar: `bash .softhouse/conformance.sh` exits 2 ONLY with
`§4.4.2-RECORDED-DECISION-EXIT`. `git commit -F <file>`. Never commit TASK.md.
