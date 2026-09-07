// Package conformance is the loan context's golden-vector schema, comparator and
// grade machinery. It follows the provisioning harness (the third-generation
// harness) rather than the first-generation ledger/loanschedule harnesses, and it
// is a separate schema on purpose rather than a widening of any of them.
//
// # What this harness grades
//
// The loan slice owns the loan-status/transaction-type enums, the four-bucket
// repayment-allocation arithmetic (AllocateInOrder/AllocatePayment), the
// disbursement arithmetic (NetDisbursalAmount) and the pure lifecycle state
// machine. Three of those have an observable form on the running reference
// oracle, captured in .softhouse/capture/loan/:
//
//   - seam "loan-repayment-allocation": the four-bucket greedy allocation,
//     graded against the SEED-L03 repayment (transaction 12, amount 8884.88)
//     whose interestPortion/principalPortion the oracle wrote back as 1000.00
//     and 7884.88 (captures loan-3-detail-after-raw.json and
//     loan-3-transactions-after-raw.json). The first instalment's due amounts
//     are transcribed from loan-3-schedule-raw.json periods[1]; the loan slice
//     deliberately does not own the instalment-selection step that produced them.
//   - seam "loan-schedule-interest": the discriminating rounding surface. The
//     period-1 interest of the discriminating loan SEED-L06 (principal 100050.50
//     @ 12%/yr, 360-day year / 30-day month) is 1000.505 raw, which ties
//     HALF_UP (1000.51) against HALF_EVEN (1000.50); the oracle posted 1000.51
//     (loan-L06-schedule-raw.json, periods[1].interestOriginalDue). The loan
//     slice does NOT own schedule generation (that is the loanschedule context),
//     so this harness ports ONLY the single-period interest the MANIFEST records
//     as the discriminating input, never the whole schedule.
//   - seam "loan-disbursement": NetDisbursalAmount, graded against the SEED-L06
//     disbursal (approved principal 100050.50, no charges due at disbursement,
//     net 100050.50; loan-L06-detail-raw.json).
//
// # What this harness cannot grade
//
// The interest waiver on SEED-L01 is captured but NOT graded: the loan slice has
// no interest-waiver arithmetic (interest is not a LoanCharge; LoanCharge.Waive
// covers fee/penalty charges only), and promotion does not port new arithmetic
// beyond the discriminating rounding surface. The full repayment schedule (all
// periods, amortisation) belongs to the loanschedule context and is OUTSIDE this
// harness's graded domain.
//
// # Money representation
//
// Loan money is integer MINOR UNITS: principal, interest, fees and penalties are
// transcribed as integer strings of the minor-unit count. No floating-point type
// appears on any money path here or in the package it grades.
//
// # What it needs from a tenant
//
// The comparator runs against vectors under .softhouse/vectors/loan/ and does
// not touch a database. It needs a store pin (PIN-loan.json) and a capability
// registry (capabilities-loan.json). With no vectors it REFUSES (exit 2) rather
// than reporting a vacuous pass. It reuses the shared no-float census, which
// scans the whole Go module.
package conformance
