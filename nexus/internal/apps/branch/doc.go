// Package branch is the Go port of Fineract's organisation/teller domain
// (tierB-branch): the cash-office hierarchy of tellers, the cashiers assigned to
// them, and the two transaction streams those cashiers produce (teller
// transactions against a client and cashier transactions against a till).
//
// It is the MODEL plus the pure, testable vocabulary: the teller status state
// machine, the cashier transaction-type table, and the money type all money
// columns are normalised to. The JSON command plumbing and the double-entry
// posting that a cashier's in/out movements feed are later slices.
//
// The reference oracle is Apache Fineract at /Users/buv/fineract, pinned at
// commit 426a23544e8426a38ae43ae404670a0a7e85b9eb; behavioural claims carry a
// file:line citation to that tree.
package branch
