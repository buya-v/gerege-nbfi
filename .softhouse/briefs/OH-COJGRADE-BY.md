# OH-COJGRADE-BY — port + grade the loan CHARGE-OFF journal entry. ONE property, concrete inputs. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-cojgrade` (branch `feat/OHCOJGRADEBY`)
Work ONLY in that directory. **Take no captures. Start no container.** The driver pushes; never exercise the push gate.

## Why this brief is narrow
Grading runs on big captures fail by reading without writing. Everything you need is named below. **Do not read
findings, maps or other vectors beyond what is listed. Start writing within 30 iterations. Commit after the first
vector passes.**

## The property (one)
`createJournalEntriesForChargeOff` [`/Users/buv/fineract/fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/service/AccrualBasedAccountingProcessorForLoan.java:890-975`,
read-only, pinned 426a23544] — the GL legs posted when a loan is CHARGED OFF, for the branch with NO charge-off reason
(`chargeOffReasonCodeValue == null`). Read lines 890-975 and `GLAccountBalanceHolder` (both maps are LinkedHashMap).
What it does, which the observations below confirm:
* principal > 0: credit LOAN_PORTFOLIO, debit CHARGE_OFF_FRAUD_EXPENSE if the loan is marked fraud, else CHARGE_OFF_EXPENSE;
* interest > 0: credit INTEREST_RECEIVABLE, debit INCOME_FROM_CHARGE_OFF_INTEREST;
* fees > 0: credit FEES_RECEIVABLE, debit INCOME_FROM_CHARGE_OFF_FEES; penalties > 0: credit PENALTIES_RECEIVABLE, debit INCOME_FROM_CHARGE_OFF_PENALTY;
* amounts to the SAME account MERGE (one leg, the sum, at the first insertion position);
* every credit is posted (insertion order) BEFORE every debit (insertion order).
The reason-mapped branch is NOT observed: the port must REFUSE a charge-off-reason mapping (error), never guess it.

## The port — a NEW pure function, beside its sibling
Model it on `nexus/internal/apps/loan/writeoffjournal.go` (`CreateWriteOffJournalEntryLegs`:95 — read that file whole;
same types `MinorUnits`, `JournalEntryLeg`). New file `nexus/internal/apps/loan/chargeoffjournal.go`:
`CreateChargeOffJournalEntryLegs(transactionID string, portions ChargeOffPortions, fraud bool, mapping ChargeOffAccountMapping) ([]JournalEntryLeg, error)`.
Integer minor units only. Refuse a negative portion, a positive portion with no mapped account.

## The seam you add — copy the write-off-journal seam line for line (from `.softhouse/maps/loan.md` § Seam entry points)
In `nexus/internal/apps/loan/conformance/`:
* `vector.go:196` `SeamLoanWriteOffJournalEntries` → add `SeamLoanChargeOffJournalEntries = "loan-chargeoff-journal-entries"`
* `vector.go:386` `WriteOffJournalRequest`, `:548` its request field, `:631` its expect field → add the charge-off twins
* `admit.go:45`, `:53`, `:171`, `:485`, `:856`, `:975` (`reconstructWriteOffJournalLegs`) → the charge-off twins
* `impl.go:153` dispatch, `:771` `goWriteOffJournal` → `goChargeOffJournal`
* `grade.go:189` `diffWriteOffJournalLegs`, `:311` its case → reuse the differ for the new seam
* `invariants.go:57`, `committed_store_test.go:133` → add the new seam
* drives: `impl.go:1066-1085` `wrongWriteOffJournal`, registrations `impl.go:2364-2381` → add ONE drive
  `loan-wrong-chargeoff-journal-ignores-fraud` (always debits CHARGE_OFF_EXPENSE)
* capability: `.softhouse/capabilities-loan.json` → add `chargeoff-journal-entry`, `in_graded_domain: true`
* provenance to copy: any `.softhouse/vectors/loan/LN-TD-*` vector (throwaway tenant `tierd`, image `e596339626bf…`)

## The observations — transcribe exactly these (driver-selected; verify each sha256 yourself)
All under `.softhouse/capture/tierd-feasibility/chargeoff-mnt/`. Portions come from the loan read-back (the chargeOff
transaction's `principalPortion`/`interestPortion`/`feeChargesPortion`/`penaltyChargesPortion`, and the loan's `fraud`);
legs come from the journalentries file, legs with that `transactionId`, in `id` order; accounts are `glAccountId`.
| vector | loan read-back (sha256) | journal entries (sha256) | tx | why |
| --- | --- | --- | --- | --- |
| LN-TD-CO-loan-7-chargeoff-merged-legs | `loans/loan-7/loan-7-detail-associations-transactions-2.json` (74011188…a14) | `journalentries/loan-7/loan-7-journalentries-2.json` (af557dfc…a088) | L19 | non-fraud; 30/103/10 merge to one credit 143 and one debit 113 |
| LN-TD-CO-loan-15-chargeoff-fraud | `loans/loan-15/loan-15-detail-associations-transactions-2.json` (ee9dcd25…2d01) | `journalentries/loan-15/loan-15-journalentries-2.json` (31abd79f…5262) | L44 | same portions, FRAUD → account 13 |
| LN-TD-CO-loan-4-chargeoff-penalty-only | `loans/loan-4/loan-4-detail-associations-transactions-2.json` (29036045…02b0) | `journalentries/loan-4/loan-4-journalentries-2.json` (4151f491…c233) | L11 | penalty alone → INCOME_FROM_CHARGE_OFF_PENALTY |
The account mapping (the vector's request carries it as glAccountIds per slot) comes from
`product-mappings/product-20-retrieve-one-response.json` (the oracle's echo: loanPortfolio 6, receivable interest/fee/
penalty 10, chargeOffExpense 14, chargeOffFraudExpense 13, incomeFromChargeOffInterest 20, incomeFromChargeOffFees 11,
incomeFromChargeOffPenalty 11) and the accepted create requests `product-mappings/create-request-LP1.json` (loan 4,
product 2) and `create-request-LP1_INTEREST_FLAT.json` (loans 7 and 15, product 3), whose ids equal the echo's. sha256s
are in `product-mappings/manifest.json`. Amounts: raw bodies carry decimal major units (e.g. `143.0`) — convert to
integer minor units (`14300`) by exact decimal parsing, never float. If an observation cannot be reproduced from the
observed inputs, THAT is the finding — record the numbers and stop; do not bend the port.

## Deliver
The port, the seam, three vectors, the one drive. Measure the drive WITHOUT and WITH the vectors
(`bash .softhouse/briefs/tools/kills.sh loan loan-wrong-chargeoff-journal-ignores-fraud <worktree>`; it must kill ≥1 with
them, 0 without). Coverage of `CreateChargeOffJournalEntryLegs` from the committed-store test (`-count=1`).
`capcount.sh <worktree> loan loan-go` must stay 0.

## Non-negotiables
No float anywhere, including parsing. No balance-named field written. `capture_ref` a JSON record + `capture_sha256`.
**Do not touch `.softhouse/guards/`** (8 pairs), `.softhouse/conformance.sh`, captures, maps. One bounded context: `loan`.
PostgreSQL only; **Oracle Database is prohibited.** Bar: `bash .softhouse/conformance.sh` exits 2 ONLY with
`§4.4.2-RECORDED-DECISION-EXIT`. `git commit -F <file>`. Never commit TASK.md.
