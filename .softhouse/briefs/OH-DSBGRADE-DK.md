# OH-DSBGRADE-DK — port + grade the loan DISBURSEMENT journal entry. ONE property. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-dsbgrade` (branch `feat/OHDSBGRADEDK`)
Work ONLY in that directory. **Take no captures. Start no container.** The driver pushes; never exercise the push gate.

## Why this brief is narrow — READ THIS FIRST
Every capture has disbursements (548 observed), but no Go port posts their journal entry. **Your whole template is ONE
commit:**

    git show 23ad8c36          # OH-GWGRADE-CY: the goodwill-credit seam, merged — port file, 7 harness files, 3 vectors, capability

Mirror every hunk of that commit for the disbursement posting, file by file, in the same places. Do not read any other
harness file, and do not read the measuring scripts (the commands under "Deliver" are all you run).

**Order of work — commit after each:** (1) the port file + `go build ./internal/apps/loan/`; (2) the seam hunks;
(3) vector 1 passing; (4) the other two; (5) the drive + measurements. If you are past 150 events with nothing committed,
commit what builds and continue.
**Git:** every commit as `git commit -F <file> </dev/null`, message file inside the worktree, deleted after. Do NOT create
or edit `AGENTS.md` or any file outside the loan context.

## The property (one)
`createJournalEntriesForDisbursements`
[`/Users/buv/fineract/fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/service/AccrualBasedAccountingProcessorForLoan.java:1309-1345`,
read-only, pinned 426a23544]:
* `overpaymentPortion` = the DTO overpayment (0 when absent); **`principalPortion = amount − overpaymentPortion`** (:1320)
  — NOT the read-back's `principalPortion` field, which is 0 on every observed disbursement;
* principalPortion > 0 → DEBIT LOAN_PORTFOLIO; overpaymentPortion > 0 → DEBIT OVERPAYMENT;
* amount > 0 → CREDIT FUND_SOURCE (the RESOLVED fund source: a payment type with a channel mapping uses that account,
  otherwise the product's `fundSourceAccountId`) — debits first, then the credit.
NOT observed, and REFUSED (no input for them): a loan-to-loan transfer (ASSET_TRANSFER) and an account transfer
(LIABILITY_TRANSFER) — the port takes no transfer flag; and an overpayment portion > 0 is ported as the Java has it but is
unobserved (say so in the capability). Integer minor units only; refuse a negative amount or overpayment, an overpayment
larger than the amount, and a positive leg with no mapped account.

## The port — a NEW pure function
New file `nexus/internal/apps/loan/disbursementjournal.go`:
`CreateDisbursementJournalEntryLegs(transactionID string, amount, overpayment MinorUnits, mapping DisbursementAccountMapping) ([]JournalEntryLeg, error)`
with `DisbursementAccountMapping{LoanPortfolio, Overpayment, FundSource string}`. Seam
`SeamLoanDisbursementJournalEntries = "loan-disbursement-journal-entries"`; request `disbursement_journal`
{`transaction_id`, `amount`, `overpayment`, `accounts`}; capability `disbursement-journal-entry`, `in_graded_domain: true`.

## The drive (one)
`loan-wrong-disbursement-uses-principal-portion`: takes the principal debit from the read-back's `principalPortion`
(0 on every observation) instead of `amount − overpayment`, so it posts no portfolio debit. Measure WITHOUT and WITH your
vectors (`bash .softhouse/briefs/tools/kills.sh loan loan-wrong-disbursement-uses-principal-portion <worktree>`: ≥1 with,
0 without). Carry the read-back `principalPortion` in the request only if the drive needs it; the port must not read it.

## The observations — transcribe exactly these (driver-selected; verify each sha256 yourself)
Amount and overpayment from the disbursement transaction in the loan read-back (`amount`, `overpaymentPortion`); legs from
the capture's SWEEP `journalentries-sweep/loan-<id>.json` (that `transactionId`, `id` order, account = `glAccountId`);
accounts from `product-mappings/create-request-<product>.json` (sha256 in its `manifest.json`). Account ids DIFFER between
captures — read each vector's ids from its own capture. Every payment type below has NO channel mapping (each product maps
only paymentType 1), so the fund source resolves to the product's `fundSourceAccountId` — state that in the provenance.
Every disbursement is not reversed.

| vector | capture dir (under `.softhouse/capture/tierd-feasibility/`) | loan read-back (sha256) | sweep (sha256) | tx | amount → legs | product (sha256): portfolio / fund / channel |
| --- | --- | --- | --- | --- | --- | --- |
| LN-TD-DSB-loan-16 | `merchant-refund-mnt/` | `loans/loan-16/loan-16-detail-associations-transactions-1.json` (971f2856…cda8) | `journalentries-sweep/loan-16.json` (3987fc16…0cb2) | L88, paymentType 8 | 116.89 → D7 116.89, C10 116.89 (legs 236-237) | LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL (53246a7b…ed15): 7 / 10 / type 1 → 18 |
| LN-TD-DSB-loan-20 | `emi-calculation-p2-mnt/` | `loans/loan-20/loan-20-detail-associations-transactions-1.json` (4585e6b8…a6c5) | `journalentries-sweep/loan-20.json` (84bfb3da…e3da) | L116, paymentType 11 | 100.00 → D1 100.00, C8 100.00 (legs 244-245) | LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALCULATION_DAILY_TILL_PRECLOSE_PMT_ALLOC_1 (a2f790c7…7bfa): 1 / 8 / type 1 → 17 |
| LN-TD-DSB-loan-1 | `repayment-p1-mnt/` | `loans/loan-1/loan-1-detail-associations-transactions-1.json` (aab9191e…1508) | `journalentries-sweep/loan-1.json` (d1bc0039…3e76) | L1, paymentType 9 | 5000.00 → D8 5000.00, C10 5000.00 (legs 1-2) | LP1 (7350bb2e…3f12): 8 / 10 / type 1 → 19 |

Raw bodies carry decimal major units — convert to integer minor units by exact decimal parsing, never float. If an
observation cannot be reproduced from the observed inputs, THAT is the finding — record it and stop.

## Deliver
The port, the seam, three vectors, the one drive, its with/without measurement, port coverage from the committed-store
test (`-count=1`). `capcount.sh <worktree> loan loan-go` must stay 0.

## Non-negotiables
No float anywhere, including parsing. No balance-named field written. `capture_ref` a JSON record + `capture_sha256`.
**Do not touch `.softhouse/guards/`** (8 pairs), `.softhouse/conformance.sh`, captures, maps. One bounded context: `loan`.
PostgreSQL only; **Oracle Database is prohibited.** Bar: `bash .softhouse/conformance.sh` exits 2 ONLY with
`§4.4.2-RECORDED-DECISION-EXIT`. Never commit TASK.md.
