# OH-CIXGRADE-DQ — port + grade the loan CAPITALIZED-INCOME ADJUSTMENT journal entry. ONE property. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-cixgrade` (branch `feat/OHCIXGRADEDQ`)
Work ONLY in that directory. **Take no captures. Start no container.** The driver pushes; never exercise the push gate.

## Why this brief is narrow — READ THIS FIRST
The capitalized-income ADJUSTMENT posting (125 transactions in capitalized-income-p2-mnt) has no Go port. Its shape is
the charge adjustment's: credits by portion slot, merged by account, then ONE debit. **Your whole template is ONE diff:**

    git diff 822c1f6a^1 822c1f6a          # OH-CAJGRADE-CZ2 merged: the charge-adjustment port, seam, 4 vectors, one drive

Mirror every hunk of that diff for the capitalized-income adjustment, file by file, in the same places. Do not read any
other harness file, and do not read the measuring scripts.

**Order of work — commit after each:** (1) the port file + `go build ./internal/apps/loan/`; (2) the seam hunks;
(3) vector 1 passing; (4) the other three; (5) the drive + measurements — COMMIT THE DRIVE before you finish (OH-BDXGRADE-DP
wrote its drive and ended without committing it).
**Git:** every commit as `git commit -F <file> </dev/null`, message file inside the worktree, deleted after. Do NOT create
or edit `AGENTS.md` or any file outside the loan context. **Never bypass a hook** (`-c core.hooksPath=…`, `--no-verify`):
if a commit does not return, STOP and say so in your final message.
**gofmt:** before EVERY commit that touches Go, `cd nexus && gofmt -l ./internal/apps/loan/` must print nothing.

## The property (one)
`createJournalEntriesForCapitalizedIncomeAdjustment`
[`/Users/buv/fineract/fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/service/AccrualBasedAccountingProcessorForLoan.java:232-292`,
read-only, pinned 426a23544]: when the transaction amount > 0 — for each positive portion CREDIT its slot (principal →
LOAN_PORTFOLIO, interest → INTEREST_RECEIVABLE, fees → FEES_RECEIVABLE, penalties → PENALTIES_RECEIVABLE, overpayment →
OVERPAYMENT), merged by GL account in slot order; then ONE DEBIT of the transaction AMOUNT to DEFERRED_INCOME_LIABILITY
(read :280-292 for the exact debit amount and order). Integer minor units; refuse a negative portion or amount, a
positive portion with no mapped account, and portions whose sum differs from the amount (unobserved — say so if the Java
allows it).

## The port — a NEW pure function
New file `nexus/internal/apps/loan/capitalizedincomeadjustmentjournal.go`:
`CreateCapitalizedIncomeAdjustmentJournalEntryLegs(transactionID string, amount MinorUnits, portions RepaymentPortions, mapping CapitalizedIncomeAdjustmentAccountMapping) ([]JournalEntryLeg, error)`
with mapping {LoanPortfolio, ReceivableInterest, ReceivableFee, ReceivablePenalty, Overpayment, DeferredIncomeLiability}.
Seam `loan-capitalized-income-adjustment-journal-entries`; capability `capitalized-income-adjustment-journal-entry`
(`in_graded_domain: true`). Honest limit for the capability: no charged-off capitalized-income adjustment is observed.

## The drive (one)
`loan-wrong-cix-credits-deferred-by-amount`: credits LOAN_PORTFOLIO with the whole AMOUNT instead of splitting it by
portion (so the interest/overpayment credits vanish). Measure WITHOUT and WITH your vectors
(`bash .softhouse/briefs/tools/kills.sh loan loan-wrong-cix-credits-deferred-by-amount <worktree>`: ≥1 with, 0 without).

## The observations — transcribe exactly these (driver-selected; verify each sha256 yourself)
All under `.softhouse/capture/tierd-feasibility/capitalized-income-p2-mnt/`, product
LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_CAPITALIZED_INCOME_ADJ_CUSTOM_ALLOC
(`product-mappings/create-request-<that name>.json`, b23b0494…6002): loanPortfolio 9, receivableInterest/Fee/Penalty 1,
overpayment 17, deferredIncomeLiability 24. Amount and portions from the capitalizedIncomeAdjustment transaction in the
loan read-back; legs from the SWEEP (that `transactionId`, `id` order, account = `glAccountId`). No loan is charged off; no
transaction below is reversed.

| vector | loan read-back (sha256) | sweep (sha256) | tx | amount / portions | legs |
| --- | --- | --- | --- | --- | --- |
| LN-TD-CIX-loan-6-principal | `loans/loan-6/loan-6-detail-associations-transactions-5.json` (64764ea1…0c51) | `journalentries-sweep/loan-6.json` (78b02dc1…7740) | L523 | 40.00 / principal 40.00 | C9 40.00, D24 40.00 (1069-1070) |
| LN-TD-CIX-loan-11-principal-interest | `loans/loan-11/loan-11-detail-associations-transactions-7.json` (47f672d0…714a) | `journalentries-sweep/loan-11.json` (53e123b1…a15f) | L573 | 60.00 / principal 59.98, interest 0.02 | C9 59.98, C1 0.02, D24 60.00 (1174-1176) |
| LN-TD-CIX-loan-17-principal-interest | `loans/loan-17/loan-17-detail-associations-transactions-12.json` (51e59e5c…f5e1) | `journalentries-sweep/loan-17.json` (6cc37614…8206) | L625 | 497.00 / principal 496.60, interest 0.40 | C9 496.60, C1 0.40, D24 497.00 (1295-1297) |
| LN-TD-CIX-loan-2-overpayment | `loans/loan-2/loan-2-detail-associations-transactions-13.json` (864cb883…83af) | `journalentries-sweep/loan-2.json` (059b2997…1512) | L198 | 15.00 / overpayment 15.00 | C17 15.00, D24 15.00 (410-411) |

Raw bodies carry decimal major units — convert to integer minor units by exact decimal parsing, never float. If an
observation cannot be reproduced from the observed inputs, THAT is the finding — record it and stop.

## Deliver
The port, the seam, four vectors, the one drive (committed), its with/without measurement, port coverage from the
committed-store test (`-count=1`). `capcount.sh <worktree> loan loan-go` must stay 0.

## Non-negotiables
No float anywhere, including parsing. No balance-named field written. `capture_ref` a JSON record + `capture_sha256`.
**Do not touch `.softhouse/guards/`** (8 pairs), `.softhouse/conformance.sh`, captures, maps. One bounded context: `loan`.
PostgreSQL only; **Oracle Database is prohibited.** Bar: `bash .softhouse/conformance.sh` exits 2 ONLY with
`§4.4.2-RECORDED-DECISION-EXIT`. Never commit TASK.md.
