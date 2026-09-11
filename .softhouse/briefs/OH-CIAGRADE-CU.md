# OH-CIAGRADE-CU — port + grade the loan CAPITALIZED-INCOME AMORTIZATION journal entry. ONE property. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-ciagrade` (branch `feat/OHCIAGRADECU`)
Work ONLY in that directory. **Take no captures. Start no container.** The driver pushes; never exercise the push gate.

## Why this brief is narrow
Twelve sibling runs did this shape by COPYING a merged seam. **Read only what is listed. Start writing within 20
iterations. Commit after the first vector passes.** The host is under heavy memory pressure: if the bar trips a
guard-cost CEILING, say so in the commit message and do not loop re-running it — the driver re-runs it.

## The property (one)
`createJournalEntriesForCapitalizedIncomeAmortization` → `…ForLoanCapitalizedIncomeAmortization` /
`…ForChargeOffLoanCapitalizedIncomeAmortization` [`/Users/buv/fineract/fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/service/AccrualBasedAccountingProcessorForLoan.java:308-502`,
read-only, pinned 426a23544]. For each positive interest / fee portion: DEBIT DEFERRED_INCOME_LIABILITY and CREDIT —
* loan NOT charged off: INCOME_FROM_CAPITALIZATION, or LOSSES_WRITTEN_OFF when the loan is written off;
* loan CHARGED OFF (no charge-off reason on the transaction): CHARGE_OFF_EXPENSE, or CHARGE_OFF_FRAUD_EXPENSE when fraud.
Through GLAccountBalanceHolder (merge by account; credits first, then debits).
NOT observed, and REFUSED (no input for them): a capitalized-income CLASSIFICATION mapping (`classificationCodeValues`
non-empty) and a CHARGE-OFF-REASON mapping. Note loan 25 below: its PRODUCT carries a reason mapping (code 34 → account
14) but its charge-off request carries NO reason, so the fraud branch applies and it credits 12 — a port that used the
product's reason mapping would post 14 and fail.

## The port — a NEW pure function
Model it on `nexus/internal/apps/loan/chargeoffjournal.go` (`CreateChargeOffJournalEntryLegs` — read it whole).
New file `nexus/internal/apps/loan/capitalizedincomeamortizationjournal.go`:
`CreateCapitalizedIncomeAmortizationJournalEntryLegs(transactionID string, interest, fee MinorUnits, chargedOff, fraud, writtenOff bool, mapping CapitalizedIncomeAmortizationAccountMapping) ([]JournalEntryLeg, error)`.
Integer minor units only; refuse a negative portion, a positive portion with no account, and chargedOff && writtenOff.

## The seam you add — copy the CHARGE-OFF journal seam line for line
Its exact entry points are generated in `.softhouse/maps/loan.md` § "Seam entry points", row
`loan-chargeoff-journal-entries`, and its drive in § "Drives registered", row `loan-wrong-chargeoff-journal-ignores-fraud`.
Read ONLY those two rows of the map. Add `SeamLoanCapitalizedIncomeAmortizationJournalEntries = "loan-capitalized-income-amortization-journal-entries"`,
the twins, and ONE drive `loan-wrong-cia-ignores-loan-state` (always INCOME_FROM_CAPITALIZATION). Capability:
`.softhouse/capabilities-loan.json` → `capitalized-income-amortization-journal-entry`, `in_graded_domain: true`. Vector to
copy for shape + provenance: `.softhouse/vectors/loan/LN-TD-CO-loan-7-chargeoff-merged-legs.json`.

## The observations — transcribe exactly these (driver-selected; verify each sha256 yourself)
Under `.softhouse/capture/tierd-feasibility/capitalized-income-p1-mnt/` (read its OWNER.md, ~60 lines). Portions (`interestPortion`, `feeChargesPortion`) from the loan read-back;
loan state from the LATEST read-back (fraud flag; the `chargeOff` / `writeOff` transaction with a LOWER id than the
amortization); legs from the SWEEP `journalentries-sweep/loan-<id>.json` (that `transactionId`, `id` order, accounts =
`glAccountId`); accounts from `product-mappings/create-request-<product>.json` (sha256 in its manifest.json):
incomeFromCapitalization 6, deferredIncomeLiability 23, chargeOffExpense 14, chargeOffFraudExpense 12, writeOff 13 — all
three products agree.
| vector | loan read-back (sha256) | sweep (sha256) | tx | why |
| --- | --- | --- | --- | --- |
| LN-TD-CIA-loan-1-normal | `loans/loan-1/loan-1-detail-associations-transactions-4.json` (2dfb05ef…2566) | `journalentries-sweep/loan-1.json` (d40a601d…d66f) | L5 | C6 100, D23 100; product LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_CAPITALIZED_INCOME (fe1e63b8…b175) |
| LN-TD-CIA-loan-21-written-off | `loans/loan-21/loan-21-detail-associations-transactions-4.json` (34f7081a…f468) | `journalentries-sweep/loan-21.json` (418cf3b2…1806) | L131 | WRITTEN OFF (writeOff L130): C13 100, D23 100; product LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_CAPITALIZED_INCOME (c709513c…7b38) |
| LN-TD-CIA-loan-30-charged-off | `loans/loan-30/loan-30-detail-associations-transactions-6.json` (10c6da76…f56a) | `journalentries-sweep/loan-30.json` (073c2ac1…5866) | L784 | CHARGED OFF (chargeOff L783): C14 16.48, D23 16.48; same product as loan 21 |
| LN-TD-CIA-loan-25-charged-off-fraud | `loans/loan-25/loan-25-detail-associations-transactions-4.json` (7a12cb27…f027) | `journalentries-sweep/loan-25.json` (47b53fd3…d195) | L332 | CHARGED OFF + FRAUD (chargeOff L331, no reason): C12 16.67, D23 16.67; product LP2_ADV_PYMNT_ZERO_INTEREST_CHARGE_OFF_DELINQUENT_REASON_INTEREST_RECALC_CAPITALIZED_INCOME (2e380265…27a5) |
Raw bodies carry decimal major units — convert to integer minor units by exact decimal parsing, never float. If an
observation cannot be reproduced from the observed inputs, THAT is the finding — record it and stop.

## Deliver
The port, the seam, four vectors, the one drive. Measure the drive WITHOUT and WITH the vectors
(`bash .softhouse/briefs/tools/kills.sh loan loan-wrong-cia-ignores-loan-state <worktree>`: ≥1 with, 0 without). Coverage of
the port from the committed-store test (`-count=1`). `capcount.sh <worktree> loan loan-go` must stay 0.

## Non-negotiables
No float anywhere, including parsing. No balance-named field written. `capture_ref` a JSON record + `capture_sha256`.
**Do not touch `.softhouse/guards/`** (8 pairs), `.softhouse/conformance.sh`, captures, maps. One bounded context: `loan`.
PostgreSQL only; **Oracle Database is prohibited.** Bar: `bash .softhouse/conformance.sh` exits 2 ONLY with
`§4.4.2-RECORDED-DECISION-EXIT`. `git commit -F <file>`. Never commit TASK.md.
