# OH-CBJGRADE-BZ2 — port + grade the loan CHARGEBACK journal entry. ONE property, concrete inputs. NO ORACLE.

Worktree: `/Users/buv/oh-gerege-cbjgrade2` (branch `feat/OHCBJGRADEBZ2`)
Work ONLY in that directory. **Take no captures. Start no container.** The driver pushes; never exercise the push gate.

## Why this brief is narrow — and what is already done
The first attempt (BZ) read for 476 events, then was stopped because a sibling seam landed in the same files. **Two
things are done for you:** (1) the sibling — the CHARGE-OFF journal-entry seam — is now merged on main and is your
TEMPLATE: copy it, don't re-derive the write-off one; (2) the first attempt's port is already in your worktree,
`nexus/internal/apps/loan/chargebackjournal.go` (uncommitted, 105 lines) — review it against the property below, fix
what is wrong, keep what is right. **Do not read findings, maps or other vectors beyond what is listed. Start writing
within 20 iterations. Commit after the first vector passes.**

## The property (one)
`createJournalEntriesForChargeback` [`/Users/buv/fineract/fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/service/AccrualBasedAccountingProcessorForLoan.java:1215-1308`,
read-only, pinned 426a23544] on a loan that is NOT charged off, legs in posting order:
1. amount > 0: CREDIT the fund source (the payment-channel account if the transaction's paymentTypeId has one, else FUND_SOURCE) with the amount;
2. overpayment > 0: DEBIT OVERPAYMENT with it;
3. principal credited > principal paid: DEBIT LOAN_PORTFOLIO with the difference.
The observed domain has no fee/penalty portion and no "paid" portion. **The port must REFUSE (error) any input
outside it** — a fee or penalty portion, a paid portion, a charged-off loan — never guess those branches.

## The port — a NEW pure function, beside its sibling
Model it on `nexus/internal/apps/loan/writeoffjournal.go` (`CreateWriteOffJournalEntryLegs`:95 — read that file whole;
same `MinorUnits`, `JournalEntryLeg`). New file `nexus/internal/apps/loan/chargebackjournal.go`:
`CreateChargebackJournalEntryLegs(transactionID string, amount, principal, overpayment MinorUnits, mapping ChargebackAccountMapping) ([]JournalEntryLeg, error)`,
where the mapping carries the resolved fund-source, loan-portfolio and overpayment accounts. Refuse amount ≠ principal +
overpayment (the observed identity; a mismatch means an unported portion). Integer minor units only.

## The seam you add — copy the CHARGE-OFF journal seam (merged 832c7012) line for line (`nexus/internal/apps/loan/conformance/`)
* `vector.go:219` `SeamLoanChargeOffJournalEntries` (+ `:198`) → add `SeamLoanChargebackJournalEntries = "loan-chargeback-journal-entries"`
* `vector.go:448-454` `ChargeOffJournalRequest`, `:618-621` its request field, `:705-712` its expect field → the chargeback twins
* `admit.go:46`, `:54`, `:174`, `:532-537`, `:959-1003`, `:1137-1148` (`reconstructChargeOffJournalLegs`) → the chargeback twins
* `impl.go:155-156` dispatch, `:844-912` `goChargeOffJournal` → `goChargebackJournal`
* `grade.go:202` `diffChargeOffJournalLegs`, `:334` its case → reuse the differ for the new seam
* `invariants.go:59`, `:569` `assertChargeOffJournalBalanced`, `committed_store_test.go:134` → add the new seam
* drive: model on `impl.go:1215-1250` (`chargeOffJournalWrongMode` / `wrongChargeOffJournal`) and registration
  `impl.go:2503-2509` → ONE drive `loan-wrong-chargeback-journal-overpayment-to-portfolio` (posts the overpayment to LOAN_PORTFOLIO)
* capability: `.softhouse/capabilities-loan.json` → add `chargeback-journal-entry`, `in_graded_domain: true` (copy `chargeoff-journal-entry`)
* vectors to copy for shape + provenance: `.softhouse/vectors/loan/LN-TD-CO-loan-7-chargeoff-merged-legs.json`

## The observations — transcribe exactly these (driver-selected; verify each sha256 yourself)
All under `.softhouse/capture/tierd-feasibility/chargeback-mnt/`. Read OWNER.md's LAST section first (20 lines).
Amount and paymentTypeId from the chargeback request; `principalPortion`/`overpaymentPortion` from the chargeback
transaction in the loan read-back; legs from the journalentries file (that `transactionId`, in `id` order; accounts are
`glAccountId`); the mapping from `product-mappings/create-request-LP1.json` (87e5c4e8…62e1).
| vector | read-back | request | journal entries | tx | why |
| --- | --- | --- | --- | --- | --- |
| LN-TD-CB-loan-14-chargeback-principal | `loans/loan-14/loan-14-detail-associations-transactions-10.json` (312f752f…cfdb9) | `loans/loan-14/loan-14-chargeback-request.json` (1bb42b50…42c2) | `journalentries/loan-14/loan-14-journalentries-5.json` (8bd7fb3b…1afb) | L69 | principal only |
| LN-TD-CB-loan-19-chargeback-overpayment | `loans/loan-19/loan-19-detail-associations-transactions-10.json` (f11aab32…c014) | `loans/loan-19/loan-19-chargeback-request.json` (1bb42b50…42c2) | `journalentries/loan-19/loan-19-journalentries-5.json` (761fcade…aba7) | L99 | overpayment only |
| LN-TD-CB-loan-21-chargeback-mixed | `loans/loan-21/loan-21-detail-associations-transactions-10.json` (ee7d5cc6…0827) | `loans/loan-21/loan-21-chargeback-request.json` (24688bcc…6b78) | `journalentries/loan-21/loan-21-journalentries-5.json` (bb3da42d…32b2) | L109 | 350 = overpayment 250 + principal 100; the overpayment debit precedes the principal debit |
Raw bodies carry decimal major units (`350.0`) — convert to integer minor units (`35000`) by exact decimal parsing,
never float. If an observation cannot be reproduced from the observed inputs, THAT is the finding — record the
numbers and stop; do not bend the port.

## Deliver
The port, the seam, three vectors, the one drive. Measure the drive WITHOUT and WITH the vectors
(`bash .softhouse/briefs/tools/kills.sh loan loan-wrong-chargeback-journal-overpayment-to-portfolio <worktree>`: ≥1 with,
0 without). Coverage of `CreateChargebackJournalEntryLegs` from the committed-store test (`-count=1`).
`capcount.sh <worktree> loan loan-go` must stay 0.

## Non-negotiables
No float anywhere, including parsing. No balance-named field written. `capture_ref` a JSON record + `capture_sha256`.
**Do not touch `.softhouse/guards/`** (8 pairs), `.softhouse/conformance.sh`, captures, maps. One bounded context: `loan`.
PostgreSQL only; **Oracle Database is prohibited.** Bar: `bash .softhouse/conformance.sh` exits 2 ONLY with
`§4.4.2-RECORDED-DECISION-EXIT`. `git commit -F <file>`. Never commit TASK.md.
