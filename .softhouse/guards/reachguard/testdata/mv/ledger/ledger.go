// GUARDS-DIR-REGISTRATION: REACHED-BY .softhouse/guards/reachguard/reachguard_test.go
// Package ledger is the `git mv` control fixture (T505 MAJOR-1 reproduction).
//
// It is a REAL balance write into a persistence boundary, written in the composite-literal-into-
// store form ledgerguard cannot see. The test copies this module to scratch, git-inits and
// commits it, runs reachguard on this path, then `git mv`s this file one directory deeper and
// re-runs. The verdict MUST be REACHES-PERSISTENCE both times. A tool whose answer moves when a
// file moves has failed, and that is the exact failure that killed the previous proposal.
//
// The boundary is the method object (*database/sql.DB).Exec. Neither moving the file nor
// renaming its package changes that object, so the verdict cannot move with the file.
package ledger

import "database/sql"

// Entry is the balance record.
type Entry struct {
	Balance int64
}

// Persist writes a balance value to a GL posting through the pointer-into-store form.
func Persist(db *sql.DB, x int64) error {
	v := Entry{Balance: x}
	_, err := db.Exec("INSERT INTO gl_posting (balance_minor) VALUES ($1)", &v)
	return err
}
