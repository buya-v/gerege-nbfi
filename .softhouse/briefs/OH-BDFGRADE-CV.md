# OH-BDFGRADE-CV — port + grade the loan BUY-DOWN-FEE journal entry. ONE property. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-bdfgrade` (branch `feat/OHBDFGRADECV`)
Work ONLY in that directory. **Take no captures. Start no container.** The driver pushes; never exercise the push gate.

## Why this brief is narrow
Thirteen sibling runs did this shape by COPYING a merged seam. **Read only what is listed. Start writing within 20
iterations. Commit after the first vector passes.** The host is under heavy memory pressure: if the bar trips a
guard-cost CEILING, say so in the commit message and do not loop re-running it — the driver re-runs it.

## The property (one)
`createJournalEntriesForBuyDownFee` [`/Users/buv/fineract/fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/service/AccrualBasedAccountingProcessorForLoan.java:530-551`,
read-only, pinned 426a23544]: amount > 0 → `helper.createJournalEntriesForLoan(debit, credit)` — DEBIT first, then CREDIT
DEFERRED_INCOME_LIABILITY with the amount; the debit account is BUY_DOWN_EXPENSE when the loan's
`merchantBuyDownFee` is true, else FUND_SOURCE (the channel account when the paymentTypeId has a channel mapping).
The adjustment, amortization and amortization-adjustment postings (`:552-792`) are NOT in this run.

## The port — a NEW pure function
Model it on `nexus/internal/apps/loan/chargebackjournal.go` (read it whole: a fixed two-sided posting with a
fund-source account). New file `nexus/internal/apps/loan/buydownfeejournal.go`:
`CreateBuyDownFeeJournalEntryLegs(transactionID string, amount MinorUnits, merchant bool, mapping BuyDownFeeAccountMapping) ([]JournalEntryLeg, error)`.
Integer minor units only; refuse a negative amount, and a positive amount with no debit or no deferred-income account
(the NON-merchant product has NO buy-down expense account — a merchant=true input with that mapping must be refused).

## The seam you add — copy the CHARGEBACK journal seam line for line
Its exact entry points are generated in `.softhouse/maps/loan.md` § "Seam entry points", row
`loan-chargeback-journal-entries`, and its drives in § "Drives registered", row
`loan-wrong-chargeback-ignores-charge-off`. Read ONLY those two rows of the map. Add
`SeamLoanBuyDownFeeJournalEntries = "loan-buy-down-fee-journal-entries"`, the twins, and ONE drive
`loan-wrong-buy-down-fee-ignores-merchant` (always debits FUND_SOURCE). Capability: `.softhouse/capabilities-loan.json` →
`buy-down-fee-journal-entry`, `in_graded_domain: true`. Vector to copy for shape + provenance:
`.softhouse/vectors/loan/LN-TD-CB-loan-17-chargedoff-fee.json`.

## The observations — transcribe exactly these (driver-selected; verify each sha256 yourself)
Under `.softhouse/capture/tierd-feasibility/buydown-fees-mnt/` (read its OWNER.md, ~60 lines). Amount from the buyDownFee transaction in the loan read-back
(`paymentDetailData.paymentType.id` 5); `merchantBuyDownFee` from the loan read-back AND the product create request;
legs from the SWEEP `journalentries-sweep/loan-<id>.json` (that `transactionId`, `id` order, accounts = `glAccountId`);
accounts from `product-mappings/create-request-<product>.json` (sha256 in its manifest.json): fundSource 5,
deferredIncomeLiability 22, buyDownExpense 23 (merchant product only); the only channel mapping, if any, must be read
from the request — these use paymentTypeId 5.
| vector | loan read-back (sha256) | sweep (sha256) | tx | why |
| --- | --- | --- | --- | --- |
| LN-TD-BDF-loan-1-merchant | `loans/loan-1/loan-1-detail-associations-transactions-2.json` (f71bd233…93d3) | `journalentries-sweep/loan-1.json` (23cc0e3d…7a4c) | L2 | merchant=true: D23 50, C22 50; product LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES (f235786b…dd90) |
| LN-TD-BDF-loan-20-non-merchant | `loans/loan-20/loan-20-detail-associations-transactions-2.json` (1ca5e5ab…ccc7) | `journalentries-sweep/loan-20.json` (287279ef…b1fb) | L781 | merchant=false: D5 50, C22 50; product LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES_NON_MERCHANT (89c007ad…ae23) |
Raw bodies carry decimal major units — convert to integer minor units by exact decimal parsing, never float. If an
observation cannot be reproduced from the observed inputs, THAT is the finding — record it and stop.

## Deliver
The port, the seam, two vectors, the one drive. Measure the drive WITHOUT and WITH the vectors
(`bash .softhouse/briefs/tools/kills.sh loan loan-wrong-buy-down-fee-ignores-merchant <worktree>`: ≥1 with, 0 without).
Coverage of the port from the committed-store test (`-count=1`). `capcount.sh <worktree> loan loan-go` must stay 0.

## Non-negotiables
No float anywhere, including parsing. No balance-named field written. `capture_ref` a JSON record + `capture_sha256`.
**Do not touch `.softhouse/guards/`** (8 pairs), `.softhouse/conformance.sh`, captures, maps. One bounded context: `loan`.
PostgreSQL only; **Oracle Database is prohibited.** Bar: `bash .softhouse/conformance.sh` exits 2 ONLY with
`§4.4.2-RECORDED-DECISION-EXIT`. `git commit -F <file>`. Never commit TASK.md.
