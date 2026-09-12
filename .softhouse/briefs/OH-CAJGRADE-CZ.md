# OH-CAJGRADE-CZ — port + grade the loan CHARGE-ADJUSTMENT journal entry. ONE property. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-cajgrade` (branch `feat/OHCAJGRADECZ`)
Work ONLY in that directory. **Take no captures. Start no container.** The driver pushes; never exercise the push gate.

## Why this brief is narrow
Sixteen sibling runs did this shape by COPYING a merged seam. **Read only what is listed. Start writing within 20
iterations. Commit after the first vector passes.** If the bar trips a guard-cost CEILING, say so in the commit message
and do not loop re-running it — the driver re-runs it.

## The property (one)
`createJournalEntriesForChargeAdjustment` → `…ForLoanChargeAdjustment` / `…ForChargeOffLoanChargeAdjustment`
[`/Users/buv/fineract/fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/service/AccrualBasedAccountingProcessorForLoan.java:997-1214`,
read-only, pinned 426a23544], and `AccountingProcessorHelper.createDebitJournalEntryForLoanCharges` (grep the name):
* CREDITS merged by GL account (LinkedHashMap) — loan NOT charged off: principal → LOAN_PORTFOLIO, interest →
  INTEREST_RECEIVABLE, fees → FEES_RECEIVABLE, penalties → PENALTIES_RECEIVABLE, overpayment → OVERPAYMENT; loan CHARGED
  OFF: principal, interest, fees → INCOME_FROM_CHARGE_OFF_FEES, penalties → INCOME_FROM_CHARGE_OFF_PENALTY, overpayment →
  OVERPAYMENT;
* then ONE DEBIT of the total to INCOME_FROM_PENALTIES when the adjusted charge is a penalty, else INCOME_FROM_FEES.
NOT observed, and REFUSED (no input for them): a CHARGE-SPECIFIC GL mapping (`getLinkedGLAccountForLoanCharges` with a
charge-level override) — the port takes the product accounts only.

**Honest limit — say it in the capability description:** in every observed product INCOME_FROM_FEES and
INCOME_FROM_PENALTIES map to the SAME GL account (3 in charges-progressive-mnt, 9 in charges-cumulative-mnt), so these
observations cannot discriminate the fee-vs-penalty debit choice. Port it as the Java has it; the vectors grade the
credits, the merge and the single-debit total, not that choice.

## The port — a NEW pure function
Model it on `nexus/internal/apps/loan/repaymentjournal.go` (`CreateRepaymentJournalEntryLegs` — read it whole: the same
merged-credits-then-one-debit shape). New file `nexus/internal/apps/loan/chargeadjustmentjournal.go`:
`CreateChargeAdjustmentJournalEntryLegs(transactionID string, portions RepaymentPortions, chargedOff, penaltyCharge bool, mapping ChargeAdjustmentAccountMapping) ([]JournalEntryLeg, error)`.
Integer minor units only; refuse a negative portion, a positive portion with no credit account, a positive total with no
debit account.

## The seam you add — copy the REPAYMENT journal seam line for line
Its exact entry points are generated in `.softhouse/maps/loan.md` § "Seam entry points", row
`loan-repayment-journal-entries`, and its drive in § "Drives registered", row
`loan-wrong-repayment-journal-one-debit-per-portion`. Read ONLY those two rows of the map. Add
`SeamLoanChargeAdjustmentJournalEntries = "loan-charge-adjustment-journal-entries"`, the twins, and ONE drive
`loan-wrong-charge-adjustment-ignores-charge-off` (always the not-charged-off credit accounts). Capability:
`.softhouse/capabilities-loan.json` → `charge-adjustment-journal-entry`, `in_graded_domain: true`. Vector to copy for shape +
provenance: `.softhouse/vectors/loan/LN-TD-RP-loan-18-repayment-fee.json`.

## The observations — transcribe exactly these (driver-selected; verify each sha256 yourself)
Portions from the chargeAdjustment transaction in the loan read-back; `penaltyCharge` from the loan's `charges[]` entry the
adjustment belongs to (loan-level read-back); legs from the capture's SWEEP `journalentries-sweep/loan-<id>.json` (that
`transactionId`, `id` order, accounts = `glAccountId`); accounts from that capture's
`product-mappings/create-request-<product>.json` (sha256 in its manifest.json). Account ids DIFFER between the two
captures — read each vector's ids from its own capture.
| vector | capture dir (under `.softhouse/capture/tierd-feasibility/`) | loan read-back (sha256) | sweep (sha256) | tx | why |
| --- | --- | --- | --- | --- | --- |
| LN-TD-CAJ-loan-41-principal | `charges-progressive-mnt/` | `loans/loan-41/loan-41-detail-associations-transactions-3.json` (72b91560…613b) | `journalentries-sweep/loan-41.json` (d2bc1289…645a) | L239 | principal 10.00: C8 (portfolio) 10, D3 (fee income) 10; product LP1 (3c276e9c…03f1) |
| LN-TD-CAJ-loan-36-penalty | `charges-progressive-mnt/` | `loans/loan-36/loan-36-detail-associations-transactions-6.json` (d80fce07…391d) | `journalentries-sweep/loan-36.json` (7085427c…9523) | L213 | penalty 20.00: C9 (penalty receivable) 20, D3 20; product LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE (7ed8d466…0387) |
| LN-TD-CAJ-loan-40-charged-off | `charges-progressive-mnt/` | `loans/loan-40/loan-40-detail-associations-transactions-3.json` (dc40fdee…6e77) | `journalentries-sweep/loan-40.json` (b0a6607e…5618) | L232 | CHARGED OFF, principal 5.00: C12 (income from charge-off fees) 5, D3 5; product LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_ACCRUAL_ACTIVITY (8bad1d93…8c7c) |
| LN-TD-CAJ-loan-7-principal-penalty | `charges-cumulative-mnt/` | `loans/loan-7/loan-7-detail-associations-transactions-9.json` (c76ab9e7…cea8) | `journalentries-sweep/loan-7.json` (301367da…28e0) | L38 | principal 1.00 + penalty 2.00: C2 (portfolio) 1, C7 (receivable) 2, ONE D9 (fee income) 3 — **original legs ids 82-84 only** (89-91 are a later reversal pair); product LP1 (61df3dc3…9991) |
Raw bodies carry decimal major units — convert to integer minor units by exact decimal parsing, never float. If an
observation cannot be reproduced from the observed inputs, THAT is the finding — record it and stop.

## Deliver
The port, the seam, four vectors, the one drive. Measure the drive WITHOUT and WITH the vectors
(`bash .softhouse/briefs/tools/kills.sh loan loan-wrong-charge-adjustment-ignores-charge-off <worktree>`: ≥1 with, 0
without). Coverage of the port from the committed-store test (`-count=1`). `capcount.sh <worktree> loan loan-go` must stay 0.

## Non-negotiables
No float anywhere, including parsing. No balance-named field written. `capture_ref` a JSON record + `capture_sha256`.
**Do not touch `.softhouse/guards/`** (8 pairs), `.softhouse/conformance.sh`, captures, maps. One bounded context: `loan`.
PostgreSQL only; **Oracle Database is prohibited.** Bar: `bash .softhouse/conformance.sh` exits 2 ONLY with
`§4.4.2-RECORDED-DECISION-EXIT`. `git commit -F <file>`. Never commit TASK.md.
