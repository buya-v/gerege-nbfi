# OH-GWCOGRADE-DH — port + grade the CHARGED-OFF arm of the GOODWILL-CREDIT journal entry. ONE property. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-gwcograde` (branch `feat/OHGWCOGRADEDH`)
Work ONLY in that directory. **Take no captures. Start no container.** The driver pushes; never exercise the push gate.

## Why this brief is narrow — READ THIS FIRST
`CreateGoodwillCreditJournalEntryLegs` (`nexus/internal/apps/loan/goodwillcreditjournal.go`) ports the goodwill credit
on a loan NOT charged off and REFUSES `chargedOff` because that arm was unobserved. It is now observed twice. You
EXTEND that function (lift the refusal, add the arm) and the existing seam `loan-goodwill-credit-journal-entries`; you
do NOT write a new seam. Your template for the harness side is the commit that added `charged_off` handling to the
interest-payment-waiver seam — find it with `git log --format=%h -S loan-wrong-ipw-ignores-charge-off -- nexus/internal/apps/loan/conformance/impl.go | tail -1`
and `git show` it. Read nothing else in the harness.

**Order of work — commit after each:** (1) the port change + `go build ./internal/apps/loan/` + the existing goodwill
vectors still passing; (2) the request field and vector 1 passing; (3) vector 2; (4) the drive + measurements.
If you are past 150 events with nothing committed, commit what builds and continue.
**Git:** every commit as `git commit -F <file> </dev/null`, message file inside the worktree. Do NOT create or edit
`AGENTS.md` or any file outside the loan context.

## The property (one)
`createJournalEntriesForRepaymentWhenLoanIsChargedOff`, the goodwill-credit branches
[`/Users/buv/fineract/fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/service/AccrualBasedAccountingProcessorForLoan.java`,
read-only, pinned 426a23544 — principal :1433-1435, interest :1461-1464, fees :1491-1493, penalties :1529-1532,
overpayment :1564-1566], reached for a goodwill credit on a CHARGED-OFF loan via :1369-1376:
* principal → CREDIT INCOME_FROM_RECOVERY, DEBIT GOODWILL_CREDIT;
* interest → CREDIT INCOME_FROM_RECOVERY, DEBIT INCOME_FROM_GOODWILL_CREDIT_INTEREST;
* fees → CREDIT INCOME_FROM_RECOVERY, DEBIT INCOME_FROM_GOODWILL_CREDIT_FEES;
* penalties → CREDIT INCOME_FROM_RECOVERY, DEBIT INCOME_FROM_GOODWILL_CREDIT_PENALTY;
* overpayment → CREDIT OVERPAYMENT, DEBIT GOODWILL_CREDIT;
credits merged by GL account (GLAccountBalanceHolder), then debits merged by GL account; credits posted first. The
goodwill branch does NOT read fraud. Add `IncomeFromRecovery` to `GoodwillCreditAccountMapping` (and the request's
`accounts`, e.g. `income_from_recovery`); refuse a charged-off positive portion whose recovery (or debit) account is
unmapped. **Honest limit — say it in the capability:** penalty and overpayment portions are NOT observed on a charged-off
goodwill credit; port them as the Java has them, graded only through the unchanged not-charged-off vectors' slots.

## The drive (one)
`loan-wrong-goodwill-chargedoff-credits-portfolio`: on a charged-off loan, credits the NOT-charged-off accounts
(portfolio / receivables) instead of INCOME_FROM_RECOVERY. Measure WITHOUT and WITH your vectors
(`bash .softhouse/briefs/tools/kills.sh loan loan-wrong-goodwill-chargedoff-credits-portfolio <worktree>`: ≥1 with,
0 without). Report `loan-wrong-goodwill-debits-fund-source` with your vectors (must not drop).

## The observations — transcribe exactly these (driver-selected; verify each sha256 yourself)
Portions from the goodwillCredit transaction in the loan read-back; legs from the capture's SWEEP (that `transactionId`,
`id` order, account = `glAccountId`); accounts from `product-mappings/create-request-<product>.json` (sha256 in its
`manifest.json`). Account ids DIFFER between the captures — read each vector's ids from its own capture. Both loans:
LATEST read-back `chargedOff` true, fraud false, the chargeOff transaction id LOWER than the goodwill credit's, the
goodwill credit NOT reversed.

| vector | capture dir (under `.softhouse/capture/tierd-feasibility/`) | loan read-back (sha256) | sweep (sha256) | tx | portions → legs | product (sha256) |
| --- | --- | --- | --- | --- | --- | --- |
| LN-TD-GWCO-loan-45-principal-interest-fee | `repayment-p1-mnt/` | `loans/loan-45/loan-45-detail-associations-transactions-7.json` (a51f6511…3752) | `journalentries-sweep/loan-45.json` (e4527841…a680) | L97 (chargeOff 96) | principal 277.00, interest 10.00, fee 13.00 → **ONE C13 300.00** (recovery, merged), D20 277.00 (goodwill credit), D18 10.00 (goodwill interest), D17 13.00 (goodwill fees) — legs 225-228 | LP1_INTEREST_FLAT (78c08ea9…bb90): incomeFromRecovery 13, goodwillCredit 20, incomeFromGoodwillCreditInterest 18, Fees 17, Penalty 17, overpayment 14 |
| LN-TD-GWCO-loan-15-principal-interest | `interest-payment-waiver-mnt/` | `loans/loan-15/loan-15-detail-associations-transactions-33.json` (b91f3073…d1af) | `journalentries-sweep/loan-15.json` (ca377fc9…737c) | L113 (chargeOff 112) | principal 63.07, interest 3.47 → **ONE C13 66.54**, D19 63.07, D20 3.47 — legs 322-324 | LP2_ADV_CUSTOM_PMT_ALLOC_INTEREST_DAILY_EMI_ACTUAL_ACTUAL_INTEREST_RECALC_ZERO_CHARGE_OFF_ACCRUAL (ad6c8814…3d60): incomeFromRecovery 13, goodwillCredit 19, incomeFromGoodwillCreditInterest 20, Fees/Penalty 14, overpayment 17 |

NOT a vector: `repayment-p1-mnt` loan 47 L105 — the same shape, but reversed in full (legs 254-261 carry their own
reversal). Raw bodies carry decimal major units — convert to integer minor units by exact decimal parsing, never float.
If an observation cannot be reproduced from the observed inputs, THAT is the finding — record it and stop.

## Deliver
The port extension, the request field, two vectors, the one drive, its with/without measurement, the existing drive's
count, the capability text (charged-off arm + honest limit). Coverage of the port from the committed-store test
(`-count=1`). `capcount.sh <worktree> loan loan-go` must stay 0.

## Non-negotiables
No float anywhere, including parsing. No balance-named field written. `capture_ref` a JSON record + `capture_sha256`.
**Do not touch `.softhouse/guards/`** (8 pairs), `.softhouse/conformance.sh`, captures, maps. One bounded context: `loan`.
PostgreSQL only; **Oracle Database is prohibited.** Bar: `bash .softhouse/conformance.sh` exits 2 ONLY with
`§4.4.2-RECORDED-DECISION-EXIT`. `git commit -F <file> </dev/null`. Never commit TASK.md.
