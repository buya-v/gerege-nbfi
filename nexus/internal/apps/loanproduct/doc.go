// Package loanproduct is the Go port of Apache Fineract's loan-product
// configuration surface: the interest/amortization/repayment-frequency enums
// and the LoanProductRelatedDetail value object that carries them into a loan.
//
// # What this package is, and is not
//
// It is the CONFIGURATION MODEL. It owns the stored-value <-> enum tables and
// the loan-product related-detail aggregate the loan scheduler and the loan
// account read. It is NOT the schedule generator: that already exists, fully
// graded, in nexus/internal/apps/loanschedule (DEC-1), and this package is
// deliberately thin where the generator is already authoritative — it declares
// the enums the generator consumes, and nothing here recomputes an EMI.
//
// The reference oracle is Apache Fineract at /Users/buv/fineract, pinned at
// commit 426a23544e8426a38ae43ae404670a0a7e85b9eb. Every behavioural claim
// carries a file:line citation to that tree; claims that do not carry an
// UNVERIFIED marker. Oracle Database is a prohibited product in this program
// and appears nowhere in this stack; PostgreSQL is the only permitted database.
//
// # Citation-audit status — read this before trusting a [VERIFIED:] range
//
// A citation being present is not a citation being resolved, and the audit is
// PARTIAL. Do not read the paragraph above as a warrant for the whole package.
//
//   - repaymentperiod.go — SWEPT. Every [VERIFIED: RepaymentPeriod.java:a-b]
//     was re-derived mechanically against the pinned commit by T530 and
//     re-derived again, row by row, by the independent review T531.
//   - interestperiod.go — UNSWEPT. Its [VERIFIED: InterestPeriod.java:a-b]
//     ranges have NOT been audited. T530 measured 23 of 28 failing to resolve,
//     10 of them citing past the end of a 237-line file — the strongest
//     available evidence that the block was never derived against this commit.
//     The sweep is task T532, which owns that file; nothing here has covered
//     it. Treat those ranges as unverified until T532 lands, and do not apply
//     an offset: on repaymentperiod.go the drift changed sign and was
//     non-monotonic, so an offset theory makes an unswept remainder merely look
//     accounted for.
//   - Every other file in the package — UNSWEPT, and never claimed otherwise.
//
// The unswept verdict is about the CODE FILES, not about this comment: the
// InterestPeriod.java ranges cited in the arguments below — :43-73, :45, :65,
// :66, :68 and :178 — were each re-read directly against the pinned commit by
// T534 and all six resolve. That is a spot check of the six ranges those
// arguments stand on, and it is not a sweep of interestperiod.go; do not cite
// it as one.
//
// # One trap this port is built around
//
// TRAP — DaysInYearType and DaysInMonthType do NOT store their ordinal. The
// oracle declares ACTUAL(1), DAYS_360(360), DAYS_364(364), DAYS_365(365) for
// years and ACTUAL(1), DAYS_30(30) for months
// [VERIFIED: DaysInYearType.java:25-29, DaysInMonthType.java:24-26], so the
// stored value and the ordinal agree only for the first member and diverge for
// every member after it. A port that uses a single `iota` constant block for
// either axis is silently wrong on DAYS_360/DAYS_364/DAYS_365/DAYS_30 — the
// most common non-trivial day-count conventions in the whole product surface.
// Both axes therefore carry an explicit StoredValue() table and a separately
// tested FromStoredValue() decoder, exactly as the ledger package does for
// Classification and Usage.
//
// # The two "balance"-named cells in this package are NOT ledger balances
//
// This is stated at package level because a source guard over the Go tree
// (.softhouse/guards/ledgerguard) refuses four writes in this package under
// class I3-FIELD-WRITE, reading them as violations of the CLAUDE.md
// non-negotiable "Balances are derived, never written" / DEC-2 §4.4 I-3. They
// are not violations. The four sites are:
//
//	interestperiod.go   UpdateOutstandingLoanBalance  (two writes)
//	interestperiod.go   AddBalanceCorrectionAmount
//	repaymentperiod.go  copyWithoutPaidAmounts
//
// All four are still REFUSED by the guard, knowingly and on purpose. Nothing
// was renamed to clear the bar and no arithmetic was changed — see "The bar is
// red on purpose", below.
//
// # THE TEST THAT DECIDES IT: TWO LEGS, AND NEITHER IS "IS THERE A POSTING STREAM?"
//
// READ THIS BEFORE REUSING THE ARGUMENT. TWO tests have now been tried here and
// BOTH FAILED on this package's own evidence — "does the value ever become a
// database column" and "does the value fold a posting stream." Both are set out
// under "Two arguments that do not work" below, each with the counterexample
// that killed it. Do not carry either anywhere else.
//
// What holds is a PAIR of legs, ranked. Neither needs a taxonomy of what a
// "balance" IS — which is precisely what both retired tests needed and neither
// could supply.
//
//	LEG 1 — PARITY, and it is the load-bearing one. Applying I-3's prescribed
//	remedy to this cell CHANGES THE MONEY. The oracle refreshes
//	InterestPeriod.outstandingLoanBalance only at explicit sweeps and
//	deliberately reads it stale in between, so an on-demand derivation returns
//	a different number at every such point. A "repair" that moves money away
//	from the reference oracle is not a repair. This leg is EXECUTABLE:
//	TestOutstandingLoanBalanceIsASweptSnapshot goes red (it would read 70000
//	where the oracle's stored cell still holds 90000) the moment someone
//	adopts the derive-on-read shape. Mechanism and citations: evidence item 4.
//
//	LEG 2 — REACHABILITY. The harm I-3 exists to prevent is a stored number
//	standing in for a derived ledger balance WHERE ACCOUNTING READS IT. That
//	requires the value to REACH one: a journal entry or GL posting, or a
//	persisted column another aggregate reads as an account balance. These
//	cells reach neither. The forward trace terminates in DTOs carrying no
//	@Entity, @Table or @Column, and the whole calc package emits no journal
//	entry at all. The one place these cells ARE persisted —
//	m_loan_progressive_model.json_model — is the projection's own working
//	state, reloaded as the SAME projection's starting state: a closed loop
//	inside loanproduct.calc, not a reach into the ledger. Trace and citations:
//	evidence item 1.
//
// LEG 1 IS RANKED FIRST DELIBERATELY. An earlier draft of this comment demoted
// it to "corroboration" beneath a category argument; that ranking was inverted,
// because LEG 1 is the leg an author cannot talk past — a test executes it, and
// a wrong answer is a failing build rather than a losing argument. LEG 2 is a
// hand-walked forward closure plus greps at one oracle commit. It is exactly the
// claim the go/types discriminator described under "The bar is red on purpose"
// would decide mechanically, and it is precisely because nothing decides it
// mechanically today that these four sites STAY RED.
//
// THE RECONCILIATION WITH T501's SAVINGS REPAIR runs on LEG 2, not on any
// category claim. SavingsAccountSummary.AccountBalance IS
// m_savings_account_summary.account_balance_derived — a persisted balance column
// the account is read from [VERIFIED: the oracle selects
// `sa.account_balance_derived as accountBalance` at
// SavingsAccountReadPlatformServiceImpl.java:306 and :751; the Go port INSERTs
// that column at nexus/internal/apps/savings/postgres.go:113, which is why the
// guard reports it under class I3-SQL-BALANCE as well as I3-FIELD-WRITE]. It
// REACHES a ledger balance, so I-3 bites and T501 was right to stop storing it
// and fold the postings instead. These four cells reach no such column. Same
// guard class, opposite disposition, one criterion.
//
// The same oracle carries a cell of the SAME NAME that does reach one, and it is
// instructive: m_loan_transaction.outstanding_loan_balance_derived
// [VERIFIED: LoanTransaction.java:127] is written by
// LoanBalanceService.updateLoanOutstandingBalances, which sorts the loan's
// non-reversed, monetary transactions and folds a running `outstanding` over
// them [VERIFIED: LoanBalanceService.java:160-208; the three writes are at
// :174, :194 and :203]. THAT is a ledger balance in the I-3 sense and exactly
// the shape I-3 exists to govern. It is a DIFFERENT QUANTITY from the cells in
// this package — different package (loanaccount.domain vs
// loanproduct.calc.data), a separate accumulator, no data path between them.
// The name collision is the whole trap, and whoever ports LoanBalanceService
// will meet the real one.
//
// # The evidence
//
//  1. LEG 2's TRACE — THE DOWNSTREAM PATH TERMINATES IN DTOs. No journal entry,
//     no GL account, no posting derives from this cell anywhere:
//
//     InterestPeriod.outstandingLoanBalance
//     -> InterestPeriod.java:151            the DECLINING_BALANCE interest base
//     -> RepaymentPeriod.java:389-403       the period-level cell (Memo'd)
//     -> ProgressiveLoanScheduleGenerator.java:132
//     -> LoanScheduleModelRepaymentPeriod.setOutstandingLoanBalance (a DTO)
//     -> LoanSchedulePlan.java:65, :77                                   (a DTO)
//
//     Both terminals carry zero @Entity, @Table and @Column annotations; the
//     whole calc package carries zero of them too; and a grep for JournalEntry
//     across fineract-progressive-loan/.../loanproduct/calc/ returns zero hits
//     [VERIFIED at oracle 426a23544 — all four counts re-run]. The next
//     aggregate down the path, m_loan_repayment_schedule, declares 34 @Column
//     fields and not one of them is an outstanding or balance column
//     [VERIFIED: LoanRepaymentScheduleInstallment.java:60-162].
//
//     THE LIMIT OF THIS ITEM, stated so nobody over-reads it: it is a
//     hand-walked forward closure plus greps at ONE oracle commit, not a
//     type-checked closure. It is LEG 2's whole warrant, and its being
//     unmechanised is why the bar stays red.
//
//  2. outstandingLoanBalance IS THE INTEREST BASE OF ONE SCHEDULE SEGMENT, not
//     the balance of an account. Its single arithmetic consumer is the
//     declining-balance branch of the segment interest formula —
//     `case DECLINING_BALANCE -> getOutstandingLoanBalance().getAmount()`
//     [VERIFIED: InterestPeriod.java:151].
//
//  3. balanceCorrectionAmount IS NOT A BALANCE, IT IS A SIGNED DELTA applied to
//     that projection — the oracle only ever adds a NEGATED amount to it
//     [VERIFIED: ProgressiveEMICalculator.java:907, :922, :946, :952, :1124,
//     :1129 — all six opened]. It is one summand of the roll-forward, sitting
//     beside disbursementAmount and capitalizedIncomePrincipal
//     [VERIFIED: InterestPeriod.java:168-188]; those two summands are not
//     flagged, and the only thing distinguishing this one is that its name
//     contains the substring "balance".
//
//     NOTE PRECISELY WHAT THIS ITEM DOES NOT SAY. At :922 and :952 the negated
//     amount IS a paid principal — a transaction-driven quantity. "Signed delta"
//     is a claim about the cell's SIGN DISCIPLINE, never about its provenance.
//     Reading it as provenance is exactly what sank the posting-stream test
//     below, and this item is the evidence that refuted it.
//
//  4. LEG 1's MECHANISM — THE CELL IS A SWEPT SNAPSHOT, AND ITS STALENESS IS
//     PART OF THE ALGORITHM. Unlike RepaymentPeriod's derived cells — whose
//     oracle Memo carries an invalidation key, is observationally inert and is
//     therefore dropped by this port (see repaymentperiod.go) — the SEGMENT cell
//     InterestPeriod.outstandingLoanBalance has NO invalidation key. It is
//     refreshed only where the oracle explicitly sweeps it
//     [VERIFIED: ProgressiveEMICalculator.java:1254-1256, and the per-period
//     sweeps at :1647, :1654, :1667], and the oracle deliberately leaves it
//     unrefreshed elsewhere: RepaymentPeriod.copyWithoutPaidAmounts zeroes each
//     copied segment's balanceCorrectionAmount and does NOT recompute the
//     balance that summand feeds [VERIFIED: RepaymentPeriod.java:173-198].
//     Replacing the cell with an on-demand derivation would therefore CHANGE
//     THE NUMBERS at every such point.
//     TestOutstandingLoanBalanceIsASweptSnapshot pins exactly this property, so
//     a later rewrite to an on-demand derivation fails a test rather than
//     silently changing money.
//
//     The PERIOD-level cell is the other way round, and this port treats it so:
//     RepaymentPeriod.getOutstandingLoanBalance IS derive-on-read behind a Memo
//     whose invalidation key includes interestPeriods
//     [VERIFIED: RepaymentPeriod.java:389-403], and this port recomputes it on
//     every read. Snapshot semantics are a property of the SEGMENT cell
//     specifically; do not generalise them to the period cell.
//
// # Two arguments that do not work — do not reuse either
//
// ## RETIRED 1: "neither cell is ever a database column"
//
// The first argument written for these four sites was "neither cell is ever a
// column, so DEC-2 §4.4 I-3's phrase 'no write path to any balance COLUMN' has
// no column to be about." Its citations are individually true — InterestPeriod
// carries no @Entity, @Table or @Column [VERIFIED: InterestPeriod.java:43-73];
// m_loan_progressive_model's whole column list is loan_id, json_model (text),
// business_date, last_modified_on_utc, json_model_version
// [VERIFIED: ProgressiveLoanModel.java:34-55]; and m_loan_repayment_schedule
// carries no balance column
// [VERIFIED: LoanRepaymentScheduleInstallment.java:60-162]. They do not entail
// the conclusion, for two reasons recorded here so nobody rediscovers them as a
// contradiction:
//
//   - BOTH CELLS ARE SERIALISED INTO m_loan_progressive_model.json_model.
//     InterestPeriod carries @JsonExclude on exactly two fields —
//     repaymentPeriod (:45) and mc (:68) — while balanceCorrectionAmount (:65)
//     and outstandingLoanBalance (:66) carry none, and
//     JsonExcludeAnnotationBasedExclusionStrategy.shouldSkipField skips ONLY
//     annotated fields
//     [VERIFIED: JsonExcludeAnnotationBasedExclusionStrategy.java:31-34;
//     InterestScheduleModelRepositoryWrapperImpl.java:55-73]. Both values go
//     into the blob.
//   - THE BLOB IS READ BACK AS STARTING STATE, not discarded. getSavedModel
//     loads it through extractModel and, when the stored business date is
//     stale, re-processes transactions ONTO THE LOADED MODEL rather than
//     rebuilding it
//     [VERIFIED: InterestScheduleModelRepositoryWrapperImpl.java:95, :110-128 —
//     recalculateInterestForDate at :122].
//
// So the values ARE stored and ARE read back. On T501's ratified standard —
// which deleted a FIELD, not a column, holding that "a decoded balance is a
// number this port did not derive, arriving through the SELECT instead of the
// INSERT" — "it is a text blob and not a typed column" does not survive. A
// stored balance is a stored balance whatever its type.
//
// LEG 2 IS NOT THIS ARGUMENT WEARING A NEW NAME, and the difference is the whole
// point: LEG 2 does not claim the cells are unpersisted. It claims their
// persistence is a CLOSED LOOP — json_model is written by the projection and
// read back as the same projection's starting state, and nothing outside
// loanproduct.calc reads a balance out of it. "Never stored" would be false;
// "never reaches an aggregate that reads it as an account balance" is what
// item 1's trace establishes.
//
// ## RETIRED 2: "there is no posting stream, so I-3's remedy names no computation"
//
// The second argument ran: a ledger balance is defined by the POSTING STREAM it
// folds; I-3's remedy "derive by summation over the postings" presupposes that
// stream; a schedule projects the FUTURE while postings record the PAST, so no
// transaction is summed to produce this cell AND NONE COULD BE; the remedy names
// no computation, and the cell is therefore not a ledger balance at all. IT IS
// RETIRED, for two independent reasons — the premise is false, and rewording it
// does not save it.
//
//   - ITS FACTUAL PREMISE IS FALSE. A transaction-derived quantity IS summed
//     into this cell, in the very function the argument annotated.
//     updateOutstandingLoanBalance folds
//     previousRepaymentPeriod.getPaidPrincipal()
//     [VERIFIED: InterestPeriod.java:178], and this port reproduces that fold
//     verbatim — `plus(previous.PaidPrincipal())`, the last summand of
//     UpdateOutstandingLoanBalance's first-segment branch in interestperiod.go
//     (line 282 at the time of writing; grep the expression, not the line, since
//     comment edits move it). paidPrincipal is
//     accumulated by RepaymentPeriod.addPaidPrincipalAmount
//     [VERIFIED: RepaymentPeriod.java:405-407] from
//     ProgressiveEMICalculator.payPrincipal [VERIFIED: :421], which the
//     transaction processor calls while walking real LoanTransactions
//     [VERIFIED: AdvancedPaymentScheduleTransactionProcessor.java:929, :967,
//     :2912]. And balanceCorrectionAmount is, at two of its six call sites,
//     literally a negated paid principal
//     [VERIFIED: ProgressiveEMICalculator.java:922 — effectivePaidPrincipal.negated();
//     :952 — paidPrincipal.negated()]. Evidence item 3 above always carried
//     those citations: the retired headline contradicted its own evidence.
//
//   - IT IS NOT WELL-DEFINED AT THE BOUNDARY, so restating the premise does not
//     save it. "The posting stream it folds" admits two readings and BOTH are
//     wrong somewhere. Take m_loan.principal_outstanding_derived
//     [VERIFIED: LoanSummary.java:62-63 —
//     @Column(name = "principal_outstanding_derived")], a PERSISTED
//     outstanding-principal column that is unmistakably the thing I-3 governs.
//     It is computed at LoanSummary.java:203-204 from
//     calculateTotalPrincipalRepaid, which folds SCHEDULE INSTALLMENTS
//     [VERIFIED: :339-346] — not postings. On the DIRECT reading ("the cell's
//     own defining expression must fold postings") the test CLEARS that column,
//     which is plainly the wrong answer. On the TRANSITIVE reading ("some
//     ancestor in the dataflow folds postings") it condemns that column
//     correctly — the installment's principal_completed_derived
//     [VERIFIED: LoanRepaymentScheduleInstallment.java:72-73] is written by
//     payPrincipalComponent [VERIFIED: :672] from a LoanTransaction — but it
//     then condemns THESE FOUR SITES TOO, because paidPrincipal is
//     transaction-driven exactly one hop away by the trace above. Nothing in the
//     test supplies a stopping rule that admits one hop and refuses two.
//
// LEG 2 DOES NOT INHERIT THAT DEFECT, and naming the difference is what keeps
// this from being the same mistake a third time. The posting-stream test asked a
// BACKWARD question about ancestry with no stopping rule. Reachability asks a
// FORWARD question with an ENUMERABLE TERMINAL SET: you stop at the terminals
// and you list them, which item 1 does. That is also why it is mechanisable, and
// the go/types discriminator named below is precisely its mechanisation.
//
// # The bar is red on purpose
//
// The fields were NOT renamed. The exported accessors OutstandingLoanBalance()
// and BalanceCorrectionAmount() mirror the oracle's method names and are the
// audit link every [VERIFIED:] citation in this package depends on; renaming
// only the unexported storage would silence the guard while changing nothing,
// which is the one outcome worse than the refusal.
//
// Nor is a guard patch the answer yet. A discriminator that classified these
// writes by their PACKAGE's persistence surface — a database import, an SQL
// literal or a column struct tag somewhere in the same directory — was
// proposed, built and measured, and it has been WITHDRAWN. Moving
// nexus/internal/apps/savings/summary.go, whose Add method folds
// `s.AccountBalance += effect` on a VALUE receiver and returns a new summary
// [VERIFIED: savings/summary.go:52-55] — a pure fold over a copy, not itself a
// write to stored state — into an internal/apps/savings/model/ subdirectory
// reclassifies a write that IS reachable to a persisted column: the folded
// AccountBalance field is what PostgresSummaryRepository.Upsert sends as
// account_balance_derived [VERIFIED: savings/postgres.go:113,120,149]. That
// reachability, not the value-receiver mutation itself, is why this one
// belongs in the guard-flagged class while this package's four sites do not —
// and a directory move would erase the distinction by disarming both alike. One
// file move, zero code change, ordinary Go layering. A guard that a file move
// disarms is not a guard: directory adjacency to a string containing SQL is
// not reachability to a balance column.
//
// DO NOT restate that parenthesis as "the same shape as the four sites above."
// A previous revision did, and it was FALSE FOR THREE OF THE FOUR. The savings
// Add is `func (s SavingsAccountSummary) Add(...) SavingsAccountSummary` — a
// value receiver mutating its own copy. This package's
// UpdateOutstandingLoanBalance (two of the four writes) and
// AddBalanceCorrectionAmount are `func (ip *InterestPeriod) ...` — POINTER
// receivers mutating a live object that other holders of the pointer observe.
// Only copyWithoutPaidAmounts, which writes into the fresh copy it has just
// built, is shaped like the savings fold.
//
// The slip is worth this much space because it smuggles back the exact
// conflation this section exists to refuse, inside the sentence written to fix
// it: RECEIVER SEMANTICS ARE NOT THE CRITERION AND NEVER WERE. Value-versus-
// pointer decides nothing about I-3 — if it did, the savings fold (a value
// receiver) would be the safe one and these three (pointer receivers) the
// violations, which is the reverse of the correct answer. What decides it is
// REACHABILITY to a persisted balance column, which cuts the other way: the
// savings fold is guard-flagged despite its value receiver because
// account_balance_derived is one Upsert away, and these four are not despite
// three of them mutating live state because no such column is downstream of
// them at all. Argue the reachability; never the receiver.
//
// The correct repair is a go/types-based discriminator that follows the value
// across the import graph to a persisted column — LEG 2, mechanised. Until that
// exists THESE FOUR SITES STAY RED, and that is the honest state — a known,
// argued, test-pinned refusal, not a cleared bar. See
// .softhouse/handoff/T511-t505-conditions.md for the withdrawn patch and its
// measurement, and .softhouse/handoff/T516-t514-conditions.md for the retirement
// of the posting-stream test and the corrected guard census.
//
// # Deliberately NOT ported
//
// The annual-nominal-rate derivation is not reproduced here. In the oracle the
// per-period rate lives on LoanProductRelatedDetail while the annual rate is
// derived during product assembly and by the progressive schedule model, and
// that arithmetic is already owned and graded by loanschedule under DEC-1.
// This package exposes the per-period rate as the schedule generator expects
// it and adds no second derivation to keep a single source of truth for the
// rate mathematics.
package loanproduct
