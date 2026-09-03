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
// non-negotiable "Balances are derived, never written" / DEC-2 §4.4 I-3 "No
// write path to any balance COLUMN exists in the Go tree". They are not. The
// guard's surface is the identifier's SPELLING — it says so itself, in
// CANNOT-CATCH item 2: "the surface is the NAME, because without a type checker
// there is nothing else to key on." The four sites are:
//
//	interestperiod.go   UpdateOutstandingLoanBalance  (two writes)
//	interestperiod.go   AddBalanceCorrectionAmount
//	repaymentperiod.go  copyWithoutPaidAmounts
//
// WHAT THE CELLS ACTUALLY ARE, from the pinned oracle:
//
//  1. NEITHER IS EVER A COLUMN. InterestPeriod is a plain value object in
//     org.apache.fineract.portfolio.loanproduct.calc.data — the CALC package.
//     It carries no @Entity, no @Table and no @Column
//     [VERIFIED: InterestPeriod.java:43-73]. Its only persistence is as a field
//     inside a Gson blob written to m_loan_progressive_model.json_model, a
//     `text` column; that table's whole column list is loan_id, json_model,
//     business_date, last_modified_on_utc, json_model_version, and it holds no
//     balance column of any kind
//     [VERIFIED: ProgressiveLoanModel.java:33-58;
//     InterestScheduleModelRepositoryWrapperImpl.java:55-73]. The blob is a
//     REGENERABLE, version-stamped cache of a projection, not a record of fact.
//     Nor does the quantity reach a column further downstream: the schedule
//     installment table m_loan_repayment_schedule has no outstanding-balance
//     column either [VERIFIED: LoanRepaymentScheduleInstallment.java:60-162 —
//     principal_amount, interest_amount and their *_derived settlement cells,
//     and nothing named for a balance].
//
//  2. outstandingLoanBalance IS THE INTEREST BASE OF ONE SCHEDULE SEGMENT, not
//     the balance of an account. Its single arithmetic consumer is the
//     declining-balance branch of the segment interest formula —
//     `case DECLINING_BALANCE -> getOutstandingLoanBalance().getAmount()`
//     [VERIFIED: InterestPeriod.java:151]. Nothing in the ledger derives
//     from it; no journal entry is posted from it.
//
//  3. balanceCorrectionAmount IS NOT A BALANCE AT ALL. It is a SIGNED DELTA
//     applied to that projection — the oracle only ever adds a negated amount
//     to it [VERIFIED: ProgressiveEMICalculator.java:922, :952, :1129]. It is
//     one summand of the roll-forward, sitting beside disbursementAmount and
//     capitalizedIncomePrincipal [VERIFIED: InterestPeriod.java:168-188]; those
//     two summands are not flagged, and the only thing distinguishing this one
//     is that its name contains the substring "balance".
//
//  4. THE CELL IS A SWEPT SNAPSHOT, AND ITS STALENESS IS PART OF THE ALGORITHM.
//     Unlike RepaymentPeriod's derived cells — whose oracle Memo carries an
//     invalidation key, is observationally inert and is therefore dropped by
//     this port (see repaymentperiod.go) — InterestPeriod.outstandingLoanBalance
//     has NO invalidation key. It is refreshed only where the oracle explicitly
//     sweeps it [VERIFIED: ProgressiveEMICalculator.java:1254-1256, and the
//     per-period sweeps at :1647, :1654, :1667], and the oracle deliberately
//     leaves it unrefreshed elsewhere: RepaymentPeriod.copyWithoutPaidAmounts
//     zeroes each copied segment's balanceCorrectionAmount and does NOT
//     recompute the balance that summand feeds
//     [VERIFIED: RepaymentPeriod.java:173-197]. Replacing the cell with an
//     on-demand derivation would therefore CHANGE THE NUMBERS at every such
//     point. That is why this port keeps the cell and does not "derive" it:
//     deriving it would be a divergence from the oracle dressed as a fix.
//     TestOutstandingLoanBalanceIsASweptSnapshot pins exactly this property, so
//     a later rewrite to an on-demand derivation fails a test rather than
//     silently changing money.
//
// WHAT WAS DELIBERATELY NOT DONE, so nobody mistakes it for an oversight: the
// fields were NOT renamed. The exported accessors OutstandingLoanBalance() and
// BalanceCorrectionAmount() mirror the oracle's method names and are the audit
// link every [VERIFIED:] citation in this package depends on; renaming only the
// unexported storage would silence the guard while changing nothing, which is
// the one outcome worse than the refusal. The repair belongs in the guard's
// discrimination, and is proposed in
// .softhouse/handoff/T502-loanproduct-i3.md.
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
