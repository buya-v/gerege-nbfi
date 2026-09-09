package loan

import (
	"errors"
	"fmt"
)

// OutstandingBalancePosting is one transaction row of a loan read-back, reduced
// to exactly the fields LoanBalanceService.updateLoanOutstandingBalances reads
// from a posting when it derives the serialized outstandingLoanBalance column.
// Portions that the row leaves absent (a waiver recognises no principal; an
// accrual recognises none of anything) are transcribed as zero minor units.
//
// The postings arrive in the row order of the read-back, which for the seeded
// population is also the LoanTransactionComparator order the oracle re-sorts
// by before deriving [VERIFIED: LoanBalanceService.java:168].
type OutstandingBalancePosting struct {
	// Type is the posting's LoanTransactionType (m_loan_transaction.transaction_type_enum).
	Type LoanTransactionType
	// Amount is the posting's full transaction amount.
	Amount MinorUnits
	// PrincipalPortion is the principal the posting recognises. Absent in the
	// read-back row (a disbursement creates principal rather than repaying it, a
	// waiver settles interest) is transcribed as zero.
	PrincipalPortion MinorUnits
}

// OutstandingBalanceRow is the derivation verdict for one input posting: does
// the read-back serialise an outstandingLoanBalance cell on the row, and if so
// what is its derived value.
type OutstandingBalanceRow struct {
	// Serialized is false when the oracle does not stamp outstandingLoanBalance
	// on the row at all (a non-monetary posting such as an accrual is excluded
	// from the balance stream and its read-back row omits the key).
	Serialized bool
	// BalanceMinor is the derived outstanding principal balance when Serialized.
	BalanceMinor MinorUnits
}

// ErrNotTranscribed is returned for a posting type no committed capture
// observes. The derivation ports the transcribed subset of the oracle's rule;
// behaviour for an untranscribed type is refused, never guessed.
var ErrNotTranscribed = errors.New("loan: transaction type not transcribed by any committed capture")

// DeriveOutstandingBalances ports
// LoanBalanceService.updateLoanOutstandingBalances
// [VERIFIED: LoanBalanceService.java:160-205] over an ordered, non-reversed
// posting stream. It returns one OutstandingBalanceRow per input posting, in
// input order.
//
// The oracle's rule, restricted to the types the committed captures observe:
//
//   - a DISBURSEMENT adds its full amount to the running balance
//     [VERIFIED: LoanBalanceService.java:171-174];
//   - an ACCRUAL is a non-monetary transaction: it is excluded from the balance
//     stream entirely, its row never receives an outstandingLoanBalance
//     [VERIFIED: LoanTransaction.isNonMonetaryTransaction,
//     LoanTransaction.java:854-868, and the filter at
//     LoanBalanceService.java:163-166];
//   - every remaining monetary posting (the captures observe REPAYMENT and
//     WAIVE_INTEREST) subtracts only the PRINCIPAL portion it recognises
//     [VERIFIED: LoanBalanceService.java:195-204]; a posting whose principal
//     portion is absent moves nothing;
//   - the running balance is clamped at zero
//     [VERIFIED: MathUtil.negativeToZero at LoanBalanceService.java:203].
//
// A posting that moves interest or fees into the balance, or that reduces it by
// a waived amount rather than by a principal portion, drifts from this column.
// The outstanding balance tracks PRINCIPAL only: a waiver settles interest and
// does not move it, which is precisely why the post-waiver read-back row
// carries the same balance as the disbursement row before it.
//
// The balances are DERIVED row by row from the earlier postings (the G-12
// derive-don't-store ruling); nothing here is written or stored independently.
func DeriveOutstandingBalances(postings []OutstandingBalancePosting) ([]OutstandingBalanceRow, error) {
	rows := make([]OutstandingBalanceRow, len(postings))
	var running MinorUnits
	for i, p := range postings {
		switch p.Type {
		case TransactionAccrual:
			// Non-monetary: excluded from the balance stream, never serialised.
			rows[i] = OutstandingBalanceRow{Serialized: false}
			continue
		case TransactionDisbursement:
			// The disbursement creates the principal the running balance
			// tracks. The seeded disbursements carry no overpaymentPortion, so
			// the oracle's "plus amount minus overPaymentPortion"
			// [VERIFIED: LoanBalanceService.java:171-174] is plus amount here.
			running += p.Amount
		case TransactionRepayment, TransactionWaiveInterest:
			running -= p.PrincipalPortion
		default:
			return nil, fmt.Errorf("%w: %s", ErrNotTranscribed, p.Type)
		}
		if running < 0 {
			running = 0
		}
		rows[i] = OutstandingBalanceRow{Serialized: true, BalanceMinor: running}
	}
	return rows, nil
}
