// Package loan is the Go port of Fineract's loan-account lifecycle domain: the
// loan status and transaction-type enums, the lifecycle event vocabulary, and
// the loan lifecycle state machine.
//
// # Scope of this slice
//
// This is the LIFECYCLE CORE of tierA-loan-lifecycle, deliberately split as the
// development plan directs ("largest — split by sub-behaviour"). It owns the
// stored-value <-> enum tables for LoanStatus and LoanTransactionType, the
// balance-derived LoanSummary money snapshot (summary.go), and the pure
// transition logic of DefaultLoanLifecycleStateMachine. It does NOT own:
//
//   - disbursement / repayment-allocation / penalty-charge / rescheduling /
//     write-off-delinquency arithmetic — those are separate sub-behaviours that
//     will land as siblings in this package or under a loan/account subpackage,
//     and they depend on the schedule generator and ledger first;
//   - persistence. The state machine here is a pure function of (status, event,
//     facts) so it can be graded without a database, matching the derive-don't-
//     store ruling: the status field is DERIVED from balances, never stored
//     independently of them.
//
// Reference oracle: Apache Fineract at /Users/buv/fineract (pinned commit
// 426a23544e8426a38ae43ae404670a0a7e85b9eb). Every transition carries a
// DefaultLoanLifecycleStateMachine.java line citation.
//
// # Why the state machine is a pure function
//
// Fineract's DefaultLoanLifecycleStateMachine mutates a Loan aggregate and
// fires Spring business events. Those side effects are not part of the port's
// contract: the G-12 derive-don't-store ruling means the status is a derived
// field recomputed from balance facts, so the port exposes the decision as
// NextStatus(from, event, facts) and DetermineTransition(from, facts) and lets
// the caller apply the resulting (status, event) pair. This keeps the state
// machine exhaustively testable and side-effect free.
package loan
