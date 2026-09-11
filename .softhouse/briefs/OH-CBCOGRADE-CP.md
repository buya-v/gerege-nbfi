# OH-CBCOGRADE-CP — extend the loan CHARGEBACK journal seam: FEE and PENALTY portions, and the CHARGED-OFF account switch. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-cbcograde` (branch `feat/OHCBCOGRADECP`)
Work ONLY in that directory. **Take no captures. Start no container.** The driver pushes; never exercise the push gate.

## Why this brief is narrow
You EXTEND a merged seam (`loan-chargeback-journal-entries`, OH-CBJGRADE-BZ2); you do not add one. **Do not read
findings, maps or other vectors beyond what is listed. Start writing within 20 iterations. Commit after the first new
vector passes.**

## The property (one)
`createJournalEntriesForChargeback` + `getPrincipalAccount` / `getFeeAccount` / `getPenaltyAccount`
[`/Users/buv/fineract/fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/service/AccrualBasedAccountingProcessorForLoan.java:1215-1308`,
read-only, pinned 426a23544], legs in posting order:
1. amount > 0: CREDIT the fund source (channel account if the paymentTypeId has one) with the amount;
2. overpayment > 0: DEBIT OVERPAYMENT;
3. principal credited > 0: DEBIT the principal account — LOAN_PORTFOLIO, or CHARGE_OFF_EXPENSE when the loan is charged
   off (CHARGE_OFF_FRAUD_EXPENSE when charged off AND fraud);
4. fee credited > 0: DEBIT FEES_RECEIVABLE, or INCOME_FROM_CHARGE_OFF_FEES when charged off;
5. penalty credited > 0: DEBIT PENALTIES_RECEIVABLE, or INCOME_FROM_CHARGE_OFF_PENALTY when charged off.
Each is a separate helper call: no merging, even when fee and penalty share an account.
Today `nexus/internal/apps/loan/chargebackjournal.go` (`CreateChargebackJournalEntryLegs`:59) takes only amount,
principal, overpayment and refuses anything else. Extend it with fee, penalty, `chargedOff bool`, `fraud bool` and the
charge-off accounts; keep amount = principal + fee + penalty + overpayment as a refusal. STILL REFUSE: charged-off AND
fraud (not observed), and any "paid" portion (the principalPaid/feePaid/penaltyPaid difference arms — not observed; the
function keeps taking no such input).

## Where (`nexus/internal/apps/loan/conformance/`, seam `loan-chargeback-journal-entries`)
`vector.go:869-875` (request type) and `:1070-1073`, `:1210-1216`; `admit.go:836-841`, `:1578-1622`, `:2177-2185`
(admission and reconstruct); `impl.go:1241-1291` (go evaluator); existing drive `impl.go:1982-2018` / registration
`:3328-3335`. Add ONE drive `loan-wrong-chargeback-ignores-charge-off` (always LOAN_PORTFOLIO / receivables). The
capability `chargeback-journal-entry` in `.softhouse/capabilities-loan.json` gets its description widened. The three
existing `LN-TD-CB-*` vectors must pass unchanged (new fields default to zero / false — say which way you chose).

## The observations — transcribe exactly these (driver-selected; verify each sha256 yourself)
Under `.softhouse/capture/tierd-feasibility/chargeback-p2-mnt/` (read its OWNER.md join section first, ~50 lines). Amount and paymentTypeId (2) from the loan's
`loan-<id>-chargeback-request.json`; portions, `fraud` (false) and the charged-off state from the loan read-back; legs from
the SWEEP `journalentries-sweep/loan-<id>.json` (that `transactionId`, `id` order, accounts = `glAccountId`); accounts from
`product-mappings/create-request-LP2_DOWNPAYMENT_ADV_PMT_ALLOC_PROG_SCHEDULE_HOR_INST_LVL_DELINQUENCY_CREDIT_ALLOCATION.json`
(50960b96…d5a6): fundSource 6, loanPortfolio 5, receivable fee/penalty 10, chargeOffExpense 16, incomeFromChargeOffFees/
Penalty 14; the only channel mapping is paymentTypeId 1 → 19, so type 2 → 6. All five loans use that product.
| vector | loan read-back (sha256) | sweep (sha256) | tx | why |
| --- | --- | --- | --- | --- |
| LN-TD-CB-loan-16-chargedoff-principal | `loans/loan-16/loan-16-detail-associations-transactions-6.json` (34530c35…7a39) | `journalentries-sweep/loan-16.json` (31668fa1…f124) | L107 | CHARGED OFF: C6 250, D16 250 |
| LN-TD-CB-loan-17-chargedoff-fee | `loans/loan-17/loan-17-detail-associations-transactions-6.json` (6f9eff15…a299) | `journalentries-sweep/loan-17.json` (f8bd35db…6f9b) | L113 | CHARGED OFF, fee 30: C6 280, D16 250, D14 30 |
| LN-TD-CB-loan-18-chargedoff-penalty | `loans/loan-18/loan-18-detail-associations-transactions-6.json` (c08b2b4f…98c9) | `journalentries-sweep/loan-18.json` (d29802c4…ab2e) | L119 | CHARGED OFF, penalty 30: C6 280, D16 250, D14 30 |
| LN-TD-CB-loan-11-fee | `loans/loan-11/loan-11-detail-associations-transactions-7.json` (daca7ff0…71f9) | `journalentries-sweep/loan-11.json` (53f6f4ba…7309) | L75 | not charged off, fee 30: C6 280, D5 250, D10 30 |
| LN-TD-CB-loan-12-penalty | `loans/loan-12/loan-12-detail-associations-transactions-7.json` (cbcd9a69…539d) | `journalentries-sweep/loan-12.json` (2ad60e38…0789) | L82 | not charged off, penalty 30: C6 280, D5 250, D10 30 |
Raw bodies carry decimal major units — convert to integer minor units by exact decimal parsing, never float. If an
observation cannot be reproduced from the observed inputs, THAT is the finding — record it and stop.

## Deliver
The extension, five new vectors, the one drive. Measure the NEW drive WITHOUT and WITH the new vectors
(`bash .softhouse/briefs/tools/kills.sh loan loan-wrong-chargeback-ignores-charge-off <worktree>`: ≥1 with, 0 without); the
existing `loan-wrong-chargeback-journal-overpayment-to-portfolio` must still kill (≥2). Coverage of the port from the
committed-store test (`-count=1`). `capcount.sh <worktree> loan loan-go` must stay 0.

## Non-negotiables
No float anywhere, including parsing. No balance-named field written. `capture_ref` a JSON record + `capture_sha256`.
**Do not touch `.softhouse/guards/`** (8 pairs), `.softhouse/conformance.sh`, captures, maps. One bounded context: `loan`.
PostgreSQL only; **Oracle Database is prohibited.** Bar: `bash .softhouse/conformance.sh` exits 2 ONLY with
`§4.4.2-RECORDED-DECISION-EXIT`. `git commit -F <file>`. Never commit TASK.md.
