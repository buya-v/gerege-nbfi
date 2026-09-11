# OH-MIRFRAUD-CN — extend the charged-off merchant-refund journal seam: the FRAUD split and the PAYOUT-REFUND arm. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-mirfraud` (branch `feat/OHMIRFRAUDCN`)
Work ONLY in that directory. **Take no captures. Start no container.** The driver pushes; never exercise the push gate.

## Why this brief is narrow
You EXTEND a seam merged an hour ago (OH-MIRGRADE-CK); you do not add a new one. **Do not read findings, maps or other
vectors beyond what is listed. Start writing within 20 iterations. Commit after the first new vector passes.**

## The property (one: two arms that share one account table)
`createJournalEntriesForRepaymentWhenLoanIsChargedOff`
[`/Users/buv/fineract/fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/service/AccrualBasedAccountingProcessorForLoan.java:1388-1615`,
read-only, pinned 426a23544]: for BOTH the merchant-issued-refund arm and the payout-refund arm on a charged-off loan,
principal credits CHARGE_OFF_FRAUD_EXPENSE when the loan is FRAUD, else CHARGE_OFF_EXPENSE; interest/fee/penalty credit
their charge-off income accounts; overpayment credits OVERPAYMENT; every portion debits FUND_SOURCE; merge by account.
The two arms post identically — read both in the Java and confirm it; if they differ, THAT is the finding.
Today `nexus/internal/apps/loan/chargedoffmerchantrefundjournal.go` (`CreateChargedOffMerchantRefundJournalEntryLegs`:81)
REFUSES fraud. Change: (1) fraud → principal to a `ChargeOffFraudExpense` account in the mapping (line 30); (2) the
seam request gains the transaction kind — `merchant_issued_refund` or `payout_refund` — and the port accepts both
(anything else refused). Goodwill on a charged-off loan has a DIFFERENT account table and stays out.

## Where (`nexus/internal/apps/loan/conformance/`, the seam `loan-chargedoff-merchant-refund-journal-entries`)
`vector.go:758-796` (request type — add the kind + the fraud expense account), `admit.go:745-750`, `:1464-1509`,
`:2019-2029` (admission and reconstruct — accept fraud and the kind), `impl.go:1117-1161` (go evaluator), existing drive
`impl.go:1775-1784` / registration `:3248`. Add ONE drive `loan-wrong-chargedoff-refund-fraud-ignored` (principal always
to CHARGE_OFF_EXPENSE). The capability `chargedoff-merchant-refund-journal-entry` in `.softhouse/capabilities-loan.json`
gets its description widened (merchant AND payout, fraud and not). The three existing `LN-TD-MIR-*` vectors must pass
unchanged (their kind defaults to merchant_issued_refund — or add the field to them explicitly, your choice, say which).

## The observations — transcribe exactly these (driver-selected; verify each sha256 yourself)
Under `.softhouse/capture/tierd-feasibility/chargeoff-mnt/` (the ChargeOff-Part1 capture; its journal entries are under `journalentries/`, NOT a sweep). Portions and
`fraud` from the loan read-back; legs from the journalentries file (that `transactionId`, `id` order, accounts =
`glAccountId`); accounts from `product-mappings/create-request-LP1_INTEREST_FLAT.json` (d799095b…8759) and the oracle's
echo `product-mappings/product-20-retrieve-one-response.json` (c01fa811…44f1): chargeOffExpense 14, chargeOffFraudExpense
13, incomeFromChargeOffInterest 20, incomeFromChargeOffFees 11, incomeFromChargeOffPenalty 11, fundSource 1; the only
channel mapping is paymentTypeId 1 → 18, and these use type 5 → 1.
| vector | loan read-back (sha256) | journal entries (sha256) | tx | why |
| --- | --- | --- | --- | --- |
| LN-TD-MIR-loan-16-refund-fraud | `loans/loan-16/loan-16-detail-associations-transactions-2.json` (09c6c129…145b) | `journalentries/loan-16/loan-16-journalentries-3.json` (1ef28e51…1385) | L48 | merchant refund, FRAUD: C13 367, C20 20, C11 113 (fee 103 + penalty 10 merged), D1 500 |
| LN-TD-POR-loan-17-payout-fraud | `loans/loan-17/loan-17-detail-associations-transactions-2.json` (7eea44ca…3de2) | `journalentries/loan-17/loan-17-journalentries-3.json` (d2c0c125…8264) | L52 | PAYOUT refund, FRAUD: same legs |
| LN-TD-POR-loan-9-payout | `loans/loan-9/loan-9-detail-associations-transactions-2.json` (94d186fc…62a1) | `journalentries/loan-9/loan-9-journalentries-3.json` (f4d0eef3…0c3e) | L27 | PAYOUT refund, not fraud: C14 367, C20 20, C11 113, D1 500 |
Raw bodies carry decimal major units — convert to integer minor units by exact decimal parsing, never float. If an
observation cannot be reproduced from the observed inputs, THAT is the finding — record it and stop.

## Deliver
The extension, three new vectors, the one drive. Measure the NEW drive WITHOUT and WITH the new vectors
(`bash .softhouse/briefs/tools/kills.sh loan loan-wrong-chargedoff-refund-fraud-ignored <worktree>`: ≥1 with, 0 without),
and the existing `loan-wrong-chargedoff-merchant-refund-as-recovery` must still kill (≥3). Coverage of the port from the
committed-store test (`-count=1`). `capcount.sh <worktree> loan loan-go` must stay 0.

## Non-negotiables
No float anywhere, including parsing. No balance-named field written. `capture_ref` a JSON record + `capture_sha256`.
**Do not touch `.softhouse/guards/`** (8 pairs), `.softhouse/conformance.sh`, captures, maps. One bounded context: `loan`.
PostgreSQL only; **Oracle Database is prohibited.** Bar: `bash .softhouse/conformance.sh` exits 2 ONLY with
`§4.4.2-RECORDED-DECISION-EXIT`. `git commit -F <file>`. Never commit TASK.md.
