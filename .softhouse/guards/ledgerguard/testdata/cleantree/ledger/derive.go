// GUARDS-DIR-REGISTRATION: REACHED-BY .softhouse/guards/ledgerguard/main.go
//
// That row is a machine-read record for .softhouse/conformance.sh's guards-dir registration,
// which sweeps every tracked .go file under the guards directory at any depth. The witness
// named above REQUIRES this file by name before it will trust the fixture — see the member
// list in selftest case (n) — so the row records a real dependency, not a grep-satisfying one.
//
// Package ledger is the CORRECT shape of everything class I3-FIELD-WRITE and
// I3-PKG-STATE refuse. Nothing here may ever be flagged; if it is, the guard has
// become over-broad and the selftest's negative control has done its job.
package ledger

// Leg is one posting. Money is INTEGER MINOR UNITS everywhere in this fixture, as
// CLAUDE.md requires — there is no float in it, not even in a comment's example.
type Leg struct {
	AccountID   int64
	AmountMinor int64
	Debit       bool
}

// Derive is the balance, and it is DERIVED: a bare local accumulator summed over the
// postings. writeTarget deliberately does not treat a bare identifier as a target,
// because this loop is the only correct implementation of "balances are derived".
func Derive(legs []Leg) int64 {
	var balance int64
	for _, l := range legs {
		if l.Debit {
			balance += l.AmountMinor
			continue
		}
		balance -= l.AmountMinor
	}
	return balance
}

// DoubleEntry sums the two sides separately and reports whether they agree. Two bare
// accumulators, no store.
func DoubleEntry(legs []Leg) (int64, int64, bool) {
	var debit, credit int64
	for _, l := range legs {
		if l.Debit {
			debit += l.AmountMinor
			continue
		}
		credit += l.AmountMinor
	}
	return debit, credit, debit == credit
}

// Available is I-6's lawful shape: a hold alters `available` and never the posted
// balance. The function is hold-named on purpose, so holdFuncRe is exercised GREEN.
func AvailableAfterHold(legs []Leg, holds []int64) int64 {
	available := Derive(legs)
	for _, h := range holds {
		available -= h
	}
	return available
}

// IsZero is a COMPARISON, not a write. `==` must never be read as an assignment; that
// is one of the reasons this guard parses instead of grepping.
func IsZero(legs []Leg) bool { return Derive(legs) == 0 }

// OutstandingAfter exercises the `outstanding` synonym balanceSynonymRe added in T509
// in its LAWFUL form: a bare accumulator, derived per call, stored nowhere.
func OutstandingAfter(principalMinor int64, repayments []int64) int64 {
	outstanding := principalMinor
	for _, r := range repayments {
		outstanding -= r
	}
	if outstanding < 0 {
		return 0
	}
	return outstanding
}
