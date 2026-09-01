// Package workingcapital is the Go port of Fineract's working-capital loan
// domain (tierB-working-capital-loan). It owns the working-capital loan
// aggregate, its per-loan balance, the payment-allocation type vocabulary that
// deliberately has NO interest bucket, and the transaction/allocation core.
//
// # How this context differs from tierA-loan-lifecycle
//
// A working-capital loan is a short-dated principal-only facility: it is
// disbursed at a discount, carries fee and penalty charges, and is repaid as
// principal. Unlike the amortising loan, it has NO interest schedule and NO
// interest bucket. That one removal ripples through every structure here:
//
//   - WorkingCapitalPaymentAllocationType has six values — DUE and IN_ADVANCE
//     crossed with PENALTY, FEE, PRINCIPAL — and no PAST_DUE band and no
//     INTEREST member [VERIFIED: WorkingCapitalPaymentAllocationType.java:24-32].
//   - WorkingCapitalLoanTransactionAllocation carries four portions —
//     principal, fee, penalty, overpayment — and never an interest portion
//     [VERIFIED: WorkingCapitalLoanTransactionAllocation.java:24-60].
//   - WorkingCapitalLoanBalance derives outstanding over the same three buckets
//     (principal, fee, penalty), again with no interest [VERIFIED:
//     WorkingCapitalLoanBalance.java:24-140].
//
// The shared vocabulary — LoanStatus, LoanTransactionType, DueType,
// AllocationType and MinorUnits — is imported from the loan package rather than
// re-declared, so a status or transaction type has exactly one Go home.
//
// # Scope of this slice
//
// This is the MODEL slice of tierB-working-capital-loan. It is deliberately a
// pure model with no database dependency: balances and outstanding amounts are
// DERIVED from transaction allocations, never stored independently of them, per
// the G-12 derive-don't-store ruling. The repayment allocation arithmetic, the
// NPV schedule, the breach/near-breach machinery and the persistence layer are
// later slices of this context and are not here.
//
// The reference oracle is Apache Fineract at /Users/buv/fineract, pinned at
// commit 426a23544e8426a38ae43ae404670a0a7e85b9eb. Every behavioural claim
// carries a file:line citation to that tree. "The oracle" here always means
// the FINERACT REFERENCE IMPLEMENTATION; Oracle Database is a prohibited
// product in this program and appears nowhere in this stack.
package workingcapital
