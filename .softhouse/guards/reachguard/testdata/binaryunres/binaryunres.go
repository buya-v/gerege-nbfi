// GUARDS-DIR-REGISTRATION: REACHED-BY .softhouse/guards/reachguard/reachguard_test.go
// Package reachbinunres is the UNION-FAIL-CLOSED control for increment 1.
//
// The written balance is `*p + 1`, a binary expression with an UNRESOLVED operand (a pointer
// dereference with no points-to result) and a resolved constant. Union semantics must keep the
// unresolved operand's cause: the result is the union of the operands, so an operand that
// cannot be resolved keeps the whole expression UNRESOLVED. Intersection (or "one operand is
// fine") would wrongly clear it.
//
// Verdict MUST be UNRESOLVED, and MUST NOT be PROVABLY-NO-PERSISTENCE.
package reachbinunres

// Entry carries the written balance.
type Entry struct {
	BalanceMinor int64
}

// Write writes a binary expression one of whose operands is an unresolved pointer dereference.
func Write(p *int64) {
	var v Entry
	v.BalanceMinor = *p + 1
	_ = v
}
