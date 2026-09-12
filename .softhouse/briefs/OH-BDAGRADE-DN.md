# OH-BDAGRADE-DN — port + grade the loan BUY-DOWN FEE AMORTIZATION journal entry. ONE property. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-bdagrade` (branch `feat/OHBDAGRADEDN`)
Work ONLY in that directory. **Take no captures. Start no container.** The driver pushes; never exercise the push gate.

## Why this brief is narrow — READ THIS FIRST
The buy-down fee amortization posting (1,344 legs in buydown-fees-mnt) has no Go port. Its shape is the capitalized-
income amortization's: one amount, a credit account chosen by loan state, one fixed debit. **Your whole template is ONE
commit:**

    git show 34d71120          # the capitalized-income amortization seam: port, 7 harness files, 4 vectors (normal / written-off / charged-off / charged-off fraud)

Mirror every hunk of that commit for the buy-down fee amortization, file by file, in the same places. Do not read any
other harness file, and do not read the measuring scripts.

**Order of work — commit after each:** (1) the port file + `go build ./internal/apps/loan/`; (2) the seam hunks;
(3) vector 1 passing; (4) the other four; (5) the drive + measurements. If you are past 150 events with nothing committed,
commit what builds and continue.
**Git:** every commit as `git commit -F <file> </dev/null`, message file inside the worktree, deleted after. Do NOT create
or edit `AGENTS.md` or any file outside the loan context.
**gofmt:** before EVERY commit that touches Go, run `cd nexus && gofmt -l ./internal/apps/loan/` — it must print
nothing (run `gofmt -w` on what it lists). The bar's HARD `guard_gofmt` refused OH-DSBGRADE-DK for two unformatted files.

## The property (one)
`createJournalEntriesForBuyDownFeeAmortization` [:576-584] dispatches on the loan's charge-off state
[`/Users/buv/fineract/fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/service/AccrualBasedAccountingProcessorForLoan.java`,
read-only, pinned 426a23544]:
* NOT charged off → `createJournalEntriesForLoanBuyDownFeeAmortization` [:586-698]: the credit account is LOSSES_WRITTEN_OFF
  when the loan is WRITTEN OFF, else INCOME_FROM_BUY_DOWN; for the interest amount and for the fees amount (each > 0)
  CREDIT that account and DEBIT DEFERRED_INCOME_LIABILITY, merged by account;
* CHARGED OFF → `createJournalEntriesForChargeOffLoanBuyDownFeeAmortization` [:699-765]: the credit account is
  CHARGE_OFF_FRAUD_EXPENSE when the loan is marked FRAUD, else CHARGE_OFF_EXPENSE; same interest/fees legs against
  DEFERRED_INCOME_LIABILITY. Fraud is read ONLY in the charged-off arm.
NOT observed-safe, and REFUSED (no input for them): the CLASSIFICATION-code path (`classificationCodeValues` non-empty,
:618-660) and the CHARGE-OFF-REASON mapping path (`mapping != null`, :716-730). The port takes no classification or
reason input, and the seam's admission refuses a request that names one.

## The port — a NEW pure function
New file `nexus/internal/apps/loan/buydownfeeamortizationjournal.go`:
`CreateBuyDownFeeAmortizationJournalEntryLegs(transactionID string, interest, fees MinorUnits, chargedOff, writtenOff, fraud bool, mapping BuyDownFeeAmortizationAccountMapping) ([]JournalEntryLeg, error)`
with mapping {IncomeFromBuyDown, LossesWrittenOff, ChargeOffExpense, ChargeOffFraudExpense, DeferredIncomeLiability}.
Seam `loan-buy-down-fee-amortization-journal-entries`; capability `buy-down-fee-amortization-journal-entry`
(`in_graded_domain: true`). Refuse a negative amount, a positive amount with no mapped account, and chargedOff together
with writtenOff.

## The drive (one)
`loan-wrong-buydown-amortization-ignores-loan-state`: always credits INCOME_FROM_BUY_DOWN, whatever the loan's state.
Measure WITHOUT and WITH your vectors (`bash .softhouse/briefs/tools/kills.sh loan loan-wrong-buydown-amortization-ignores-loan-state <worktree>`:
≥1 with, 0 without).

## The observations — transcribe exactly these (driver-selected; verify each sha256 yourself)
All under `.softhouse/capture/tierd-feasibility/buydown-fees-mnt/`. Amounts from the buyDownFeeAmortization transaction in
the loan read-back (`interestPortion`, `feeChargesPortion`; every one below is interest-only); legs from the SWEEP
(that `transactionId`, `id` order, account = `glAccountId`); states from the loan's LATEST read-back (`chargedOff`,
`fraud`, `status.code`). Charged-off state is ordered by DATE, then id: loan 5's charge-off 321 and L322 are both dated
2024-03-01, loan 10's charge-off 478 and L479 both 2024-01-25; the charge-off id is lower in each. Products (both map the
same ids): incomeFromBuyDown 24, deferredIncomeLiability 22, writeOff 15, chargeOffExpense 18, chargeOffFraudExpense 16.
No transaction below is reversed.

| vector | loan read-back (sha256) | sweep (sha256) | tx | state | legs | product (sha256) |
| --- | --- | --- | --- | --- | --- | --- |
| LN-TD-BDA-loan-1-normal | `loans/loan-1/loan-1-detail-associations-transactions-10.json` (9122c608…edd9) | `journalentries-sweep/loan-1.json` (23cc0e3d…7a4c) | L6 | active, not charged off | C24 50.00, D22 50.00 | LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES (f235786b…dd90) |
| LN-TD-BDA-loan-8-fraud-not-charged-off | `loans/loan-8/loan-8-detail-associations-transactions-12.json` (54bc472b…fece) | `journalentries-sweep/loan-8.json` (15f85d27…f4ad) | L461 | fraud TRUE, NOT charged off → fraud ignored | C24 17.58, D22 17.58 | same |
| LN-TD-BDA-loan-15-written-off | `loans/loan-15/loan-15-detail-associations-transactions-7.json` (fa16f58e…7260) | `journalentries-sweep/loan-15.json` (4fc01c4d…76dd) | L521 | status closed.written.off | C15 100.00, D22 100.00 | same |
| LN-TD-BDA-loan-5-charged-off | `loans/loan-5/loan-5-detail-associations-transactions-11.json` (e62c537d…0f45) | `journalentries-sweep/loan-5.json` (106ad93b…3263) | L322 | charged off, fraud false | C18 16.48, D22 16.48 | same |
| LN-TD-BDA-loan-10-charged-off-fraud | `loans/loan-10/loan-10-detail-associations-transactions-9.json` (ef7d8fd1…cc18) | `journalentries-sweep/loan-10.json` (d4fca227…d8fb) | L479 | charged off, fraud TRUE, charge-off request carries NO reason (`loans/loan-10/loan-10-charge-off-request.json`) | C16 36.26, D22 36.26 | LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES_CHARGE_OFF_REASON (a6e34474…9e8c) |

NOT vectors: loan 9 (its charge-off request carries `chargeOffReasonId` 33, mapped to account 18 — the refused reason
path) and loan 33 (a classification-mapped product — the refused classification path). Raw bodies carry decimal major
units — convert to integer minor units by exact decimal parsing, never float. If an observation cannot be reproduced from
the observed inputs, THAT is the finding — record it and stop.

## Deliver
The port, the seam, five vectors, the one drive, its with/without measurement, port coverage from the committed-store
test (`-count=1`). `capcount.sh <worktree> loan loan-go` must stay 0.

## Non-negotiables
No float anywhere, including parsing. No balance-named field written. `capture_ref` a JSON record + `capture_sha256`.
**Do not touch `.softhouse/guards/`** (8 pairs), `.softhouse/conformance.sh`, captures, maps. One bounded context: `loan`.
PostgreSQL only; **Oracle Database is prohibited.** Bar: `bash .softhouse/conformance.sh` exits 2 ONLY with
`§4.4.2-RECORDED-DECISION-EXIT`. Never commit TASK.md.
