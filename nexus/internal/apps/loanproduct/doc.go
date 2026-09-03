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
// # THE TEST THAT DECIDES IT: IS THERE A POSTING STREAM?
//
// READ THIS BEFORE REUSING THE ARGUMENT. The operative test is NOT "does the
// value ever become a database column." That test was tried here first and it
// FAILS — on this package's own evidence, set out under "The column argument
// does not work" below. Do not carry it anywhere else. The test that holds is:
//
//	I-3 governs LEDGER BALANCES, and a ledger balance is defined by the
//	POSTING STREAM it folds. The guard's prescribed remedy — "derive by
//	summation over the postings" — presupposes that stream. Where the stream
//	exists the remedy is available and I-3 obliges it. Where NO posting stream
//	exists, "derive by summation over the postings" NAMES NO COMPUTATION:
//	there is nothing to sum. The cell is then not a ledger balance that was
//	wrongly written. It is not a ledger balance.
//
// A schedule is a projection of the FUTURE; postings are records of the PAST.
// InterestPeriod.outstandingLoanBalance is a cell of a projection — computed
// FORWARD from the preceding segment's terms, never folded BACKWARD over
// anything that happened. No transaction is summed to produce it and none could
// be. The remedy is therefore not inconvenient here, and not a trade someone
// accepted: it is definitionally inapplicable.
//
// This is the ground on which this package and T501's savings repair agree.
// SavingsAccountSummary.AccountBalance HAS a posting stream — the savings
// transaction stream — so "derive by summation" names a real computation there,
// and T501 was right to stop storing it and fold the postings instead. These
// four cells have no such stream. Same guard class, opposite disposition, one
// test.
//
// The same oracle carries a cell of the SAME NAME that does have a posting
// stream, and it is instructive:
// m_loan_transaction.outstanding_loan_balance_derived
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
// # The rest of the evidence, which supports that test
//
//  1. THE DOWNSTREAM TRACE TERMINATES IN DTOs — no journal entry, no GL
//     account, no posting derives from this cell anywhere:
//
//     InterestPeriod.outstandingLoanBalance
//     -> InterestPeriod.java:151            the DECLINING_BALANCE interest base
//     -> RepaymentPeriod.java:389-403       the period-level cell (Memo'd)
//     -> ProgressiveLoanScheduleGenerator.java:132
//     -> LoanScheduleModelRepaymentPeriod.setOutstandingLoanBalance (a DTO)
//     -> LoanSchedulePlan.java:65, :77                                   (a DTO)
//
//     Both terminals are plain DTOs carrying no @Entity, @Table or @Column, and
//     the whole calc package posts nothing — a grep for JournalEntry across
//     fineract-progressive-loan/.../loanproduct/calc/ returns zero hits
//     [VERIFIED at oracle 426a23544].
//
//  2. outstandingLoanBalance IS THE INTEREST BASE OF ONE SCHEDULE SEGMENT, not
//     the balance of an account. Its single arithmetic consumer is the
//     declining-balance branch of the segment interest formula —
//     `case DECLINING_BALANCE -> getOutstandingLoanBalance().getAmount()`
//     [VERIFIED: InterestPeriod.java:151].
//
//  3. balanceCorrectionAmount IS NOT A BALANCE AT ALL. It is a SIGNED DELTA
//     applied to that projection — the oracle only ever adds a negated amount
//     to it [VERIFIED: ProgressiveEMICalculator.java:907, :922, :946, :952,
//     :1124, :1129 — all six opened]. It is one summand of the roll-forward,
//     sitting beside disbursementAmount and capitalizedIncomePrincipal
//     [VERIFIED: InterestPeriod.java:168-188]; those two summands are not
//     flagged, and the only thing distinguishing this one is that its name
//     contains the substring "balance".
//
//  4. THE CELL IS A SWEPT SNAPSHOT, AND ITS STALENESS IS PART OF THE ALGORITHM.
//     Unlike RepaymentPeriod's derived cells — whose oracle Memo carries an
//     invalidation key, is observationally inert and is therefore dropped by
//     this port (see repaymentperiod.go) — the SEGMENT cell
//     InterestPeriod.outstandingLoanBalance has NO invalidation key. It is
//     refreshed only where the oracle explicitly sweeps it
//     [VERIFIED: ProgressiveEMICalculator.java:1254-1256, and the per-period
//     sweeps at :1647, :1654, :1667], and the oracle deliberately leaves it
//     unrefreshed elsewhere: RepaymentPeriod.copyWithoutPaidAmounts zeroes each
//     copied segment's balanceCorrectionAmount and does NOT recompute the
//     balance that summand feeds [VERIFIED: RepaymentPeriod.java:173-197].
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
//     Note the standing of this item. It is a PARITY argument — deriving on
//     read changes the numbers. The posting-stream argument above is a CATEGORY
//     argument — the derivation does not exist. The category argument is the
//     load-bearing one; this is corroboration.
//
// # The column argument does not work — do not reuse it
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
// stored balance is a stored balance whatever its type. What makes these four
// cells lawful is that they are not balances at all in the I-3 sense: there is
// no posting stream. Nothing else.
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
// nexus/internal/apps/savings/summary.go, which carries a genuine
// `s.AccountBalance += effect`, into an internal/apps/savings/model/
// subdirectory reclassifies that real balance write into a class that prints
// and never refuses. One file move, zero code change, ordinary Go layering. A
// guard that a file move disarms is not a guard: directory adjacency to a
// string containing SQL is not reachability to a balance column.
//
// The correct repair is a go/types-based discriminator that follows the value
// across the import graph to a persisted column. Until that exists THESE FOUR
// SITES STAY RED, and that is the honest state — a known, argued, test-pinned
// refusal, not a cleared bar. See .softhouse/handoff/T511-t505-conditions.md.
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
