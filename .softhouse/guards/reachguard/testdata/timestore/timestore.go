// GUARDS-DIR-REGISTRATION: REACHED-BY .softhouse/guards/reachguard/reachguard_test.go
// Package reachtimestore is the STORED-time-value control.
//
// time is persistence-inert, so passing a value into it is pruned. Pruning a use must not lose
// the value's other uses: here the written balance is carried THROUGH a time conversion and then
// persisted, so the path runs through the pruned package and must survive it.
//
// Verdict MUST be REACHES-PERSISTENCE.
package reachtimestore

import (
	"database/sql"
	"time"
)

// Entry carries the written balance.
type Entry struct {
	BalanceMinor int64
}

// Write derives a value through time and stores it.
func Write(db *sql.DB, x int64) error {
	var v Entry
	v.BalanceMinor = x
	t := time.Unix(v.BalanceMinor, 0)
	_, err := db.Exec("INSERT INTO gl_posting (balance_minor) VALUES ($1)", t.Unix())
	return err
}
