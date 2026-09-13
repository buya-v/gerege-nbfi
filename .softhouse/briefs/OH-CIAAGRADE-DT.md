# OH-CIAAGRADE-DT — port + grade the loan CAPITALIZED-INCOME AMORTIZATION ADJUSTMENT journal entry. ONE property. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-ciaagrade` (branch `feat/OHCIAAGRADEDT`)
Work ONLY in that directory. **Take no captures. Start no container.** The driver pushes; never exercise the push gate.

## Why this brief is narrow — READ THIS FIRST
The capitalized-income AMORTIZATION ADJUSTMENT posting has no Go port; it reverses an amortization. **Your whole template
is ONE commit:**

    git show 34d71120          # the capitalized-income amortization seam: port, harness hunks, vectors, one drive

Mirror its hunks for the amortization ADJUSTMENT, file by file, in the same places — but the adjustment has NO loan-state
branches, so drop the written-off / charged-off / fraud arms. Do not read any other harness file, and do not read the
measuring scripts.

**Order of work — commit after each:** (1) the port file + `go build ./internal/apps/loan/`; (2) the seam hunks;
(3) vector 1 passing; (4) the other two; (5) the drive + `kills.sh` measurement — COMMIT THE DRIVE before you finish.
**Checks:** before every Go commit `cd nexus && gofmt -l ./internal/apps/loan/` must print nothing; run `go build`,
`go vet ./internal/apps/loan/...` and `go test ./internal/apps/loan/... -count=1`. **Do NOT run `.softhouse/conformance.sh`**
— the driver runs the full bar once at merge (it takes ~5 minutes of your run).
**Git:** every commit as `git commit -F <file> </dev/null`, message file inside the worktree, deleted after. Do NOT create
or edit `AGENTS.md` or any file outside the loan context. **Never bypass a hook** (`-c core.hooksPath=…`, `--no-verify`):
if a commit does not return, STOP and say so in your final message.

## The property (one)
`createJournalEntriesForCapitalizedIncomeAmortizationAdjustment`
[`/Users/buv/fineract/fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/service/AccrualBasedAccountingProcessorForLoan.java:503-527`,
read-only, pinned 426a23544]: when the amount > 0, `populateCreditDebitMaps(…, amount, …, DEFERRED_INCOME_LIABILITY,
INCOME_FROM_CAPITALIZATION, …)` — **CREDIT DEFERRED_INCOME_LIABILITY, DEBIT INCOME_FROM_CAPITALIZATION**, credits then debits.
No loan-state branch. Integer minor units; refuse a negative amount and a positive amount with no mapped account.

## The port — a NEW pure function
New file `nexus/internal/apps/loan/capitalizedincomeamortizationadjustmentjournal.go`:
`CreateCapitalizedIncomeAmortizationAdjustmentJournalEntryLegs(transactionID string, amount MinorUnits, mapping CapitalizedIncomeAmortizationAdjustmentAccountMapping) ([]JournalEntryLeg, error)`
with mapping {DeferredIncomeLiability, IncomeFromCapitalization}. Seam
`loan-capitalized-income-amortization-adjustment-journal-entries`; capability
`capitalized-income-amortization-adjustment-journal-entry` (`in_graded_domain: true`). Honest limit in the capability:
no charged-off, written-off or fraud loan carries one in the observations (the Java does not branch on them).

## The drive (one)
`loan-wrong-ciaa-posts-as-amortization`: posts the AMORTIZATION's sides (credit INCOME_FROM_CAPITALIZATION, debit
DEFERRED_INCOME_LIABILITY) instead of the adjustment's. Measure WITHOUT and WITH your vectors
(`bash .softhouse/briefs/tools/kills.sh loan loan-wrong-ciaa-posts-as-amortization <worktree>`: ≥1 with, 0 without).

## The observations — transcribe exactly these (driver-selected; verify each sha256 yourself)
All under `.softhouse/capture/tierd-feasibility/capitalized-income-p2-mnt/`. Amount from the
capitalizedIncomeAmortizationAdjustment transaction in the loan read-back; legs from the SWEEP (that `transactionId`, `id`
order, account = `glAccountId`). Both products map deferredIncomeLiability 24, incomeFromCapitalization 5. No loan is
charged off; no transaction below is reversed.

| vector | loan read-back (sha256) | sweep (sha256) | tx | legs | product (sha256) |
| --- | --- | --- | --- | --- | --- |
| LN-TD-CIAA-loan-1 | `loans/loan-1/loan-1-detail-associations-transactions-6.json` (797f32b6…99b2) | `journalentries-sweep/loan-1.json` (89ea6415…31c6) | L10 | C24 300.00, D5 300.00 (30-31) | LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_CAPITALIZED_INCOME (05a4422b…e11c) |
| LN-TD-CIAA-loan-17 | `loans/loan-17/loan-17-detail-associations-transactions-12.json` (51e59e5c…f5e1) | `journalentries-sweep/loan-17.json` (6cc37614…8206) | L627 | C24 5.26, D5 5.26 (1300-1301) | LP2_ADV_PYMNT_INTEREST_DAILY_EMI_360_30_INTEREST_RECALC_DAILY_CAPITALIZED_INCOME_ADJ_CUSTOM_ALLOC (b23b0494…6002) |
| LN-TD-CIAA-loan-25 | `loans/loan-25/loan-25-detail-associations-transactions-22.json` (59e451ab…a7fd) | `journalentries-sweep/loan-25.json` (84ee7826…6462) | L697 | C24 0.14, D5 0.14 (1453-1454) | same as loan 17 |

Raw bodies carry decimal major units — convert to integer minor units by exact decimal parsing, never float. If an
observation cannot be reproduced from the observed inputs, THAT is the finding — record it and stop.

## Deliver
The port, the seam, three vectors, the one drive (committed), its with/without measurement, port coverage from the
committed-store test (`-count=1`). `capcount.sh <worktree> loan loan-go` must stay 0.

## Non-negotiables
No float anywhere, including parsing. No balance-named field written. `capture_ref` a JSON record + `capture_sha256`.
**Do not touch `.softhouse/guards/`** (8 pairs), `.softhouse/conformance.sh`, captures, maps. One bounded context: `loan`.
PostgreSQL only; **Oracle Database is prohibited.** Never commit TASK.md.
