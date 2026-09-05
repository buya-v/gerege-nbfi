// GUARDS-DIR-REGISTRATION: REACHED-BY .softhouse/guards/ledgerguard/main.go
//
// See the note on the same row in ../ledger/derive.go: the witness requires this file by name
// in selftest case (n) before it will trust the fixture.
//
// Package present is the CORRECT shape of what class I3-COMPOSITE-BALANCE refuses.
//
// The line T509 drew is writeTarget's own doctrine, applied to composite literals:
// `&T{Balance: v}` ALLOCATES something that outlives the expression and is refused;
// a plain `T{Balance: Derive(...)}` returned from a presenter is a VALUE IN FLIGHT and
// must stay green, because refusing it would refuse the only way to render a derived
// balance at all.
package present

import "gerege.local/cleantree/ledger"

// View is a response DTO. Its balance field is filled at construction from a
// derivation, never stored and re-read.
type View struct {
	AccountID    int64
	BalanceMinor int64
}

// Render builds the DTO by VALUE. This is the construct case (k) has always required
// to stay green and the one I3-COMPOSITE-BALANCE must not reach.
func Render(accountID int64, legs []ledger.Leg) View {
	return View{AccountID: accountID, BalanceMinor: ledger.Derive(legs)}
}

// RenderAll shows the same thing in a slice literal: still by value, still green.
func RenderAll(legs []ledger.Leg) []View {
	return []View{
		{AccountID: 1, BalanceMinor: ledger.Derive(legs)},
		{AccountID: 2, BalanceMinor: ledger.Derive(nil)},
	}
}

// Label exists so the fixture has a string-literal population that is prose rather
// than SQL, which is the denominator sqlShapedRe is measured against.
func Label(v View) string {
	s := "account "
	s = s + "view"
	return s
}

// ThresholdFor pins the holdFuncRe carve-out: "hold" must not be matched inside
// "Threshold".
func ThresholdFor(n int64) int64 { return n }
