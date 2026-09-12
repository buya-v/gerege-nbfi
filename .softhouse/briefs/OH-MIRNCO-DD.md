# OH-MIRNCO-DD — grade MERCHANT-ISSUED REFUNDS on loans NOT charged off, on the EXISTING repayment seam. NO NEW PORT. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-mirnco` (branch `feat/OHMIRNCODD`)
Work ONLY in that directory. **Take no captures. Start no container.** The driver pushes; never exercise the push gate.

## Why this brief is narrow — READ THIS FIRST
The Java posts a merchant-issued refund on a loan NOT charged off through the SAME method as an ordinary repayment:
`isRepaymentType()` includes `isMerchantIssuedRefund()` [`fineract-loan/.../LoanTransactionType.java:193-196`], the
dispatch sends every repayment type to `createJournalEntriesForRepayments` [`AccrualBasedAccountingProcessorForLoan.java:87-90`],
and for a loan not charged off that calls `createJournalEntriesForLoanRepayments` [:1369-1376] — already ported as
`CreateRepaymentJournalEntryLegs` (`nexus/internal/apps/loan/repaymentjournal.go`) and graded on seam
`loan-repayment-journal-entries` with three REPAYMENT vectors (`LN-TD-RP-*`). (Java files under `/Users/buv/fineract`,
read-only, pinned 426a23544.)

**So you write NO port code.** You add four VECTORS on the existing seam, widen the capability text, and add ONE drive.
Your template is the three `LN-TD-RP-*.json` vectors (copy one for shape) and, for the drive, how commit `4196176e`
registered `loan-wrong-repayment-journal-one-debit-per-portion` in `impl.go`. Read nothing else in the harness.
If the seam's admission REFUSES a merchant-issued-refund vector (e.g. a transaction-type check), widen that admission
by the smallest change and say so in the commit.

**Order of work — commit after each:** (1) vector 1 passing; (2) the other three; (3) the drive + measurements +
capability text. If you are past 150 events with nothing committed, commit what passes and continue.

## The property (one) — exercised by these observations
Credits merged by GL account in slot order (principal → LOAN_PORTFOLIO, interest → INTEREST_RECEIVABLE, fee →
FEES_RECEIVABLE, penalty → PENALTIES_RECEIVABLE, overpayment → OVERPAYMENT), then ONE debit of the total to the RESOLVED
fund source. The refunds use paymentType 8; the product's channel mapping covers only paymentType 1 (→ 18), so the fund
source resolves to the product's `fundSourceAccountId` 10 — state that resolution in each vector's provenance (the vector
supplies the resolved account; the port does not resolve channels).
**New for this seam:** interest and penalty receivables map to the SAME account 4 in these products, so loan 1 L14's
interest 1.60 + penalty 2.80 MERGE into ONE credit C4 4.40. No repayment vector has a merge — this is what the drive tests.

## The drive (one)
`loan-wrong-repayment-credits-not-merged`: posts one credit per positive portion slot even when two slots resolve to the
same account. Measure it WITHOUT and WITH your vectors (`bash .softhouse/briefs/tools/kills.sh loan
loan-wrong-repayment-credits-not-merged <worktree>`: ≥1 with, 0 without). Also report the existing two repayment drives'
kill counts with your vectors (they must not drop).

## The observations — transcribe exactly these (driver-selected; verify each sha256 yourself)
All under `.softhouse/capture/tierd-feasibility/merchant-refund-mnt/`. Portions from the merchantIssuedRefund transaction
in the loan read-back; legs from the SWEEP `journalentries-sweep/loan-<id>.json` (that `transactionId`, `id` order,
account = `glAccountId`); accounts from `product-mappings/create-request-<product>.json` (sha256 in
`product-mappings/manifest.json`): loanPortfolio 7, receivableInterest/Fee/Penalty 4, overpayment 16, fundSource 10,
channel paymentType 1 → 18. Every loan below is chargedOff false, fraud false, manuallyReversed false.

| vector | loan read-back (sha256) | sweep (sha256) | tx | portions → legs | product (sha256) |
| --- | --- | --- | --- | --- | --- |
| LN-TD-MIR-loan-4-principal | `loans/loan-4/loan-4-detail-associations-transactions-5.json` (2c14ac8c…0799) | `journalentries-sweep/loan-4.json` (6c567230…45ed) | L36 | principal 50.00 → C7 50.00, D10 50.00 | LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL (53246a7b…ed15) |
| LN-TD-MIR-loan-9-overpayment | `loans/loan-9/loan-9-detail-associations-transactions-6.json` (acce0656…5f59) | `journalentries-sweep/loan-9.json` (e5f583c5…7d81) | L55 | overpayment 10.00 → C16 10.00, D10 10.00 | same as loan 4 |
| LN-TD-MIR-loan-15-principal-interest | `loans/loan-15/loan-15-detail-associations-transactions-13.json` (46600b5c…4a83) | `journalentries-sweep/loan-15.json` (75b26ef9…cb7c) | L86 | principal 64.26, interest 2.15 → C7 64.26, C4 2.15, D10 66.41 | LP2_ADV_PMT_ALLOC_ACTUAL_ACTUAL_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL (d55b8ed2…ad20) |
| LN-TD-MIR-loan-1-merged-receivable | `loans/loan-1/loan-1-detail-associations-transactions-6.json` (166ca179…d152) | `journalentries-sweep/loan-1.json` (cacf7f8e…187e) | L14 | principal 176.40, interest 1.60, penalty 2.80, overpayment 7.19 → C7 176.40, **C4 4.40 (merged)**, C16 7.19, D10 187.99 (legs 34-37) | same as loan 4 |

Raw bodies carry decimal major units — convert to integer minor units by exact decimal parsing, never float. If an
observation cannot be reproduced from the observed inputs, THAT is the finding — record it and stop.

## Deliver
Four vectors, the capability `repayment-journal-entry` (or its existing id) text widened to "ordinary repayments AND
merchant-issued refunds on loans not charged off [:87-90, :1369-1376]", the one drive, its with/without measurement.
`capcount.sh <worktree> loan loan-go` must stay 0.

## Non-negotiables
No float anywhere, including parsing. No balance-named field written. `capture_ref` a JSON record + `capture_sha256`.
**Do not touch `.softhouse/guards/`** (8 pairs), `.softhouse/conformance.sh`, captures, maps. One bounded context: `loan`.
PostgreSQL only; **Oracle Database is prohibited.** Bar: `bash .softhouse/conformance.sh` exits 2 ONLY with
`§4.4.2-RECORDED-DECISION-EXIT`. `git commit -F <file>`. Never commit TASK.md.
