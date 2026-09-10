// GUARDS-DIR-REGISTRATION: REACHED-BY .softhouse/guards/reachguard/reachguard_test.go
// Package reachprunealso is the PRUNING-MUST-NOT-LOSE-A-PATH control for increment 2.
//
// The balance is BOTH passed to an allow-listed, persistence-inert package (fmt) AND stored
// through a real persistence boundary (db.Exec of a gl_posting balance column). Pruning the
// fmt path must not lose the store path: the verdict must stay REACHES-PERSISTENCE. A
// PROVABLY-NO here would mean pruning a value's use acquitted the value.
package reachprunealso

import (
	"database/sql"
	"fmt"
)

// Entry carries the written balance.
type Entry struct {
	BalanceMinor int64
}

// Write formats the balance (inert) and also persists the struct (a boundary).
func Write(db *sql.DB, x int64) error {
	var v Entry
	v.BalanceMinor = x
	_ = fmt.Sprintf("%d", v.BalanceMinor)
	_, err := db.Exec("INSERT INTO gl_posting (balance_minor) VALUES ($1)", v)
	return err
}
