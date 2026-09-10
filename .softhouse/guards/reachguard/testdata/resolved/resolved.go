// GUARDS-DIR-REGISTRATION: REACHED-BY .softhouse/guards/reachguard/reachguard_test.go
// Package reachres is the fully-resolved half of the fail-closed control.
//
// A balance value is written into a composite literal, stored in a local, and passed to the
// single implementation of an interface method that does nothing. There is NO persistence
// boundary anywhere in the module: the forward closure is every hop of that flow and each hop
// is resolved. The correct verdict is therefore PROVABLY-NO-PERSISTENCE — the only verdict that
// may clear a red, and only because the whole closure is resolved.
//
// The test `TestFailClosedDegrade` appends a SECOND implementation of Save in a scratch copy of
// this module and re-runs: the interface call then has two implementations in scope, the
// discriminator must refuse to pick one, and the verdict must DEGRADE from PROVABLY-NO to
// UNRESOLVED. Fail-closed that is never observed failing closed is an assumption, not a
// property.
package reachres

// Record carries the written balance.
type Record struct {
	BalanceMinor int64
}

// Sink is the interface whose single implementation makes the call resolvable TODAY.
type Sink interface {
	Save(r Record)
}

type onlyImpl struct{}

// Save is the one and only implementation in scope. It persists nothing.
func (onlyImpl) Save(r Record) {}

// Write is the site under test.
func Write(s Sink, x int64) {
	rec := Record{BalanceMinor: x}
	s.Save(rec)
}
