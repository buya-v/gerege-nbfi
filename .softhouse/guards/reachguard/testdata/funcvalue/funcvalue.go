// GUARDS-DIR-REGISTRATION: REACHED-BY .softhouse/guards/reachguard/reachguard_test.go
// Package reachfuncvalue is the DELIBERATELY-UNRESOLVED func-value control (T514).
//
// The written balance comes from a call through a func value: dynamic dispatch with no single
// callee. This analysis must NOT approximate it. An analysis that assumes the common case here
// reintroduces fail-open one layer up and produces no artefact at all. The edge stays UNRESOLVED,
// and this control proves the tool refuses to clear it.
//
// Verdict MUST be UNRESOLVED, and MUST NOT be PROVABLY-NO-PERSISTENCE.
package reachfuncvalue

// Entry carries the written balance.
type Entry struct {
	BalanceMinor int64
}

// Write writes a balance derived from a func-value call.
func Write(f func(int64) int64, x int64) {
	var v Entry
	v.BalanceMinor = f(x)
	_ = v
}
