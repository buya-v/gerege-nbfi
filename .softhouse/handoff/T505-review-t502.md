# T505 — handoff: independent review of T502

Branch: `softhouse/T505-review-t502`. Review: `.softhouse/reviews/t505-review-t502/REVIEW.md`.
Reviewed: `softhouse/T502-loanproduct-i3` @ `0b5e8b81`. Oracle: `/Users/buv/fineract` @ `426a23544`.

## Verdict

**ACCEPT WITH CONDITIONS.**

**Do I agree the four sites are not balance writes? YES** — but not on T502's stated ground, and its
proposed guard patch must not land.

## The three things that decide it

1. **The four sites are lawful.** `InterestPeriod.outstandingLoanBalance` is the DECLINING_BALANCE
   interest base of one schedule segment (`InterestPeriod.java:151`, exact);
   `balanceCorrectionAmount` is a signed delta every oracle caller negates into (all six sites
   verified). Neither is a ledger balance: I traced the full downstream chain to response DTOs and
   the JSON blob — no journal entry, no GL account, no posting derives from either.
   **The decisive reason (which T502 does not state): there is no posting stream.** A schedule is a
   projection of the future; postings are records of the past. The guard's remedy "derive by
   summation over the postings" names no computation here — it is definitionally inapplicable, not
   merely inconvenient.

2. **MAJOR — the §5 guard patch amnesties a real balance write. Measured, not argued.** I rebuilt
   T502's scratch guard and reproduced its claimed output exactly (honest measurement). Then:
   moving `nexus/internal/apps/savings/summary.go` — carrying `s.AccountBalance += effect`, one of
   the three writes the patch claims "stay refused" — into `internal/apps/savings/model/`
   reclassifies it to `I3-FIELD-WRITE-NONPERSISTENT`, which prints and **never refuses**. One
   `git mv`, zero code change, conventional Go layering. "The package imports a db driver" does not
   track "this value reaches a balance column"; it tracks "shares a directory with a string
   containing SQL."

3. **MAJOR — E-1 is a true citation list that does not entail its conclusion.** All four cited facts
   verified exact (no `@Entity` on `InterestPeriod.java:43`; `ProgressiveLoanModel.java:33-58`
   column list exact; no balance column among the 33 `@Column`s in
   `LoanRepaymentScheduleInstallment.java`). But **both cells carry no `@JsonExclude`** (only
   `repaymentPeriod:44` and `mc:68` do), so both **are** serialised into
   `m_loan_progressive_model.json_model`, and that blob **is** read back as starting state
   (`getSavedModel` → `extractModel` → re-process onto the loaded model,
   `InterestScheduleModelRepositoryWrapperImpl.java:110-128`). On T501's ratified standard — *"a
   read-back satisfies 'not written' while defeating exactly that purpose"*, which deleted a **field**,
   not a column — "it's a text blob, not a typed column" does not survive. The conclusions are
   reconcilable, but only on the posting-stream ground, not the column ground.

## Verified TRUE, by re-derivation

- **900.00 → 700.00 REPRODUCED.** I drove the derive-on-read shape into `OutstandingLoanBalance()`
  on a scratch copy of T502's files: got `70000` minor units where the snapshot gives `90000`.
  Follows from staleness (the roll-forward reads the *previous* segment's correction), not from a
  patch bug. Integer minor units throughout.
- **The new test is genuinely falsifiable** — PASSES as shipped, FAILS with the exact quoted message
  under the derive-on-read shape. Not a test that cannot fail.
- **B-1 confirmed in full.** `loanschedule/emi.go:1720-1721,:1726` ships the identical roll-forward
  GREEN; its doc comment cites the same oracle method; `emi.go:62` calls the field "the balance
  carried INTO this segment." Census: **6** balance-in-substance plain assignments tree-wide, the
  guard reports **4**. The guard's sample is arbitrary.
- **B-2 confirmed, exactly 6** composite-literal writes to the two refused fields, unflagged;
  `CANNOT-CATCH` item 8 recommends the constructor, which is that form.
- **B-3 confirmed** (`repaymentperiod.go:486 SetReAgedEarlyRepaymentHolder`).
- **Scope clean**: `git show --stat 0b5e8b81` = exactly 5 files; `tasks.json`/`docs/incidents` are
  base-vs-main drift at merge-base `14cf6c1f`, pre-existing. `.softhouse/guards/**` untouched.
  Build clean, `gofmt` clean, `loanproduct` tests pass. Zero arithmetic changed, zero renames.
- Guard re-run with `bash`: EXIT=1, 14 findings, the four sites present.

## Conditions

- **C-1 (blocking).** §5 patch does not land as written. Adopt T502's own §7 fallback: these four
  stay RED until a `go/types`-based discriminator can follow the value across the import graph.
  Record the counterexample beside the proposal so it is not re-proposed.
- **C-2 (blocking).** Restate E-1 in `doc.go` + the three in-code comments on the posting-stream
  ground, and note that both cells *are* serialised into `json_model` and read back — so nobody
  rediscovers that as a contradiction with T501.
- **C-3.** Guard backlog: the `loanschedule` GREEN twin, the composite-literal hole + `CANNOT-CATCH`
  item 8, the `…Holder` over-match, and `m_loan_transaction.outstanding_loan_balance_derived`
  (`LoanTransaction.java:127`) — a real stored balance column sharing the cell's name that T502's
  downstream check missed. I traced it: fed by `LoanBalanceService:174,194,203` from a separate
  accumulator, **not** from `InterestPeriod`. T502's conclusion survives, by luck not by check.
- **C-4.** MINOR: `ProgressiveEMICalculator.java:906` → `:907`.

## For the driver

The bar stays RED for these four sites and **that is the correct state** — a known, argued,
test-pinned red. Not cleared by a rename, and not cleared by this patch. T502's refusal to rename
was the right call and is the most valuable thing on that branch.

Nothing in `.softhouse/tasks.json` was touched by this task.
