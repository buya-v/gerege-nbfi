// GUARDS-DIR-REGISTRATION: REACHED-BY .softhouse/guards/reachguard/reachguard_test.go
// Package reachtimeclear is the UNSTORED-time-value control.
//
// A balance value is written, carried through time (a persistence-inert package), and then
// discarded. There is no boundary anywhere and every hop resolves, so the correct verdict is
// PROVABLY-NO-PERSISTENCE. This is the polarity that proves the time allow-list actually
// CLEARS: if time were still unresolved, the site would stay UNRESOLVED and a legitimate green
// would be impossible.
package reachtimeclear

import (
	"database/sql"
	"time"
)

// Entry carries the written balance.
type Entry struct {
	BalanceMinor int64
}

// Write carries a balance through time and stores nothing.
func Write(db *sql.DB, x int64) {
	var v Entry
	v.BalanceMinor = x
	t := time.Unix(v.BalanceMinor, 0)
	_ = t
	_ = db
}
