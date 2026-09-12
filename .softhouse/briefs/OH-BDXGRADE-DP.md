# OH-BDXGRADE-DP — port + grade the loan BUY-DOWN FEE ADJUSTMENT journal entry. ONE property. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-bdxgrade` (branch `feat/OHBDXGRADEDP`)
Work ONLY in that directory. **Take no captures. Start no container.** The driver pushes; never exercise the push gate.

## Why this brief is narrow — READ THIS FIRST
The buy-down fee ADJUSTMENT posting has no Go port; the buy-down fee itself does. **Your whole template is ONE commit:**

    git show 43e1a5be          # the buy-down-fee seam: port file, harness hunks, vectors, one drive

Mirror every hunk of that commit for the buy-down fee ADJUSTMENT, file by file, in the same places. Do not read any
other harness file, and do not read the measuring scripts.

**Order of work — commit after each:** (1) the port file + `go build ./internal/apps/loan/`; (2) the seam hunks;
(3) vector 1 passing; (4) the other three; (5) the drive + measurements.
**Git:** every commit as `git commit -F <file> </dev/null`, message file inside the worktree, deleted after. Do NOT create
or edit `AGENTS.md` or any file outside the loan context. **Never bypass a hook** (`-c core.hooksPath=…`, `--no-verify`):
if a commit does not return, STOP and say so in your final message.
**gofmt:** before EVERY commit that touches Go, `cd nexus && gofmt -l ./internal/apps/loan/` must print nothing.

## The property (one)
`createJournalEntriesForBuyDownFeeAdjustment`
[`/Users/buv/fineract/fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/service/AccrualBasedAccountingProcessorForLoan.java:552-575`,
read-only, pinned 426a23544]: when `amount` > 0, ONE journal entry via `AccountingProcessorHelper.createJournalEntriesForLoan`
(`accountTypeToBeDebited, accountTypeToBeCredited` — `AccountingProcessorHelper.java:500-502`): **DEBIT
DEFERRED_INCOME_LIABILITY, CREDIT BUY_DOWN_EXPENSE when the loan's buy-down fee is a MERCHANT buy-down fee, else CREDIT
FUND_SOURCE.** Beware: the Java local is named `debitAccountType` but it is passed as the CREDITED account — follow the
helper's parameter order, and the ledger (every observation below is D22 then C23/C5). Integer minor units; refuse a
negative amount and a positive amount with no mapped account.

## The port — a NEW pure function
New file `nexus/internal/apps/loan/buydownfeeadjustmentjournal.go`:
`CreateBuyDownFeeAdjustmentJournalEntryLegs(transactionID string, amount MinorUnits, merchantBuyDownFee bool, mapping BuyDownFeeAdjustmentAccountMapping) ([]JournalEntryLeg, error)`
with mapping {DeferredIncomeLiability, BuyDownExpense, FundSource}. Seam `loan-buy-down-fee-adjustment-journal-entries`;
capability `buy-down-fee-adjustment-journal-entry` (`in_graded_domain: true`).

## The drive (one)
`loan-wrong-buydown-adjustment-ignores-merchant`: always credits BUY_DOWN_EXPENSE, whatever the merchant flag. Measure
WITHOUT and WITH your vectors (`bash .softhouse/briefs/tools/kills.sh loan loan-wrong-buydown-adjustment-ignores-merchant <worktree>`:
≥1 with, 0 without).

## The observations — transcribe exactly these (driver-selected; verify each sha256 yourself)
All under `.softhouse/capture/tierd-feasibility/buydown-fees-mnt/`. Amount from the buyDownFeeAdjustment transaction in the
loan read-back; `merchantBuyDownFee` from the SAME read-back (loan-level field) and from the product create request;
legs from the SWEEP (that `transactionId`, `id` order, account = `glAccountId`). Products: deferredIncomeLiability 22,
buyDownExpense 23 (merchant products only), fundSource 5.

| vector | loan read-back (sha256) | sweep (sha256) | tx | merchant | legs | product (sha256) |
| --- | --- | --- | --- | --- | --- | --- |
| LN-TD-BDX-loan-13-merchant | `loans/loan-13/loan-13-detail-associations-transactions-15.json` (d1b4940e…9695) | `journalentries-sweep/loan-13.json` (65cbc510…46d6) | L502 | true | D22 10.00, C23 10.00 (legs 1053-1054) | LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES (f235786b…dd90) |
| LN-TD-BDX-loan-14-merchant | `loans/loan-14/loan-14-detail-associations-transactions-19.json` (216fec23…f43a) | `journalentries-sweep/loan-14.json` (1ad28e8d…e669) | L511 | true | D22 10.00, C23 10.00 (legs 1074-1075) | same |
| LN-TD-BDX-loan-25-non-merchant | `loans/loan-25/loan-25-detail-associations-transactions-19.json` (63ccd9d9…c6b8) | `journalentries-sweep/loan-25.json` (83ceb498…cb71) | L819 | **false** | **ORIGINAL legs only**: D22 10.00, C5 10.00 (legs 1744-1745; 1758-1759 are its later reversal) | LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES_NON_MERCHANT (89c007ad…ae23) |
| LN-TD-BDX-loan-39-non-merchant | `loans/loan-39/loan-39-detail-associations-transactions-7.json` (410844ac…8de2) | `journalentries-sweep/loan-39.json` (213eb246…2615) | L1435 | **false** | **ORIGINAL legs only**: D22 300.00, C5 300.00 (legs 3007-3008; 3013-3014 are its later reversal) | LP2_PROGRESSIVE_ADVANCED_PAYMENT_ALLOCATION_BUYDOWN_FEES_NON_MERCHANT_CHARGE_OFF_REASON (439d7270…f917) |

The non-merchant adjustments were later reversed (the read-back marks them `manuallyReversed` true); the vector grades the
ORIGINAL posting, which is the posting this method made. Say so in each vector's provenance. Raw bodies carry decimal
major units — convert to integer minor units by exact decimal parsing, never float. If an observation cannot be
reproduced from the observed inputs, THAT is the finding — record it and stop.

## Deliver
The port, the seam, four vectors, the one drive, its with/without measurement, port coverage from the committed-store
test (`-count=1`). `capcount.sh <worktree> loan loan-go` must stay 0.

## Non-negotiables
No float anywhere, including parsing. No balance-named field written. `capture_ref` a JSON record + `capture_sha256`.
**Do not touch `.softhouse/guards/`** (8 pairs), `.softhouse/conformance.sh`, captures, maps. One bounded context: `loan`.
PostgreSQL only; **Oracle Database is prohibited.** Bar: `bash .softhouse/conformance.sh` exits 2 ONLY with
`§4.4.2-RECORDED-DECISION-EXIT`. Never commit TASK.md.
