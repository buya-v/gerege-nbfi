// Package conformance is the charges context's golden-vector schema, comparator
// and grade machinery. It is a THIRD vector schema in this program, following
// the loanschedule (DEC-1) and ledger (DEC-2) harnesses, and it is a third
// schema on purpose rather than a widening of either.
//
// # What this harness grades
//
// The charges slice owns exactly two gradeable behaviours, both pure functions
// of the charge definition and a base amount:
//
//   - Construction validation: Charge.Validate() ports the constructor
//     invariants of Fineract's Charge [Charge.java:240-300] and returns an
//     ordered list of validation-error codes, empty on success.
//   - Fee amount computation: for a FLAT charge the fee is the flat amount; for
//     a percentage-of-amount (or percentage-of-disbursement) charge the fee is
//     PercentageOf(base, percentage) rounded HALF_UP and then capped by
//     MinimumAndMaximumCap [LoanCharge.java:310-319, 327-343].
//
// A vector therefore carries a charge definition plus a base amount, and expects
// either a list of validation codes ("validation") or a fee in integer minor
// units ("fee"). Both are oracle observations, so both are class "parity".
//
// # What this harness cannot grade
//
// Percentage-of-interest and percentage-of-amount-and-interest charges need the
// interest component of a loan, which this slice does not own; their fee is not
// computable from a base amount alone, so no "fee" vector may cite them. Tax
// groups, VAT and e-Barimt are additive to Fineract and have no oracle; they are
// out of scope here and are never graded against invented parity (see the parent
// package's doc.go).
//
// # What it needs from a tenant
//
// The comparator runs against vectors under .softhouse/vectors/charges/ and does
// not touch a database. It needs a store pin (PIN-charges.json) and a capability
// registry (capabilities-charges.json) once vectors exist; with no vectors it
// REFUSES (exit 2) rather than reporting a vacuous pass. It reuses the
// loanschedule harness's no-float census, which scans the whole Go module, so no
// floating-point type or literal may appear in this package either.
package conformance
