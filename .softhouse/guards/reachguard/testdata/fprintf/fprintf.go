// GUARDS-DIR-REGISTRATION: REACHED-BY .softhouse/guards/reachguard/reachguard_test.go
// Package reachfprintf is the WRITER-MUST-NOT-BE-BLANKET-CLEARED control for increment 2.
//
// fmt.Fprintf's destination is an io.Writer, and an io.Writer can be anything — here it is
// Writer, a value the analysis discovers to be a persistence boundary because its Write method
// reaches a database/sql Exec of a GL posting. The Fprint* family therefore must NOT be pruned
// by package alone. Because Fprintf is left unresolved, the balance it is handed is UNRESOLVED,
// not cleared. If the family were blanket-cleared, this site would come back REACHES (via the
// boundary writer) or PROVABLY-NO, never UNRESOLVED.
package reachfprintf

import (
	"database/sql"
	"fmt"
)

// Entry carries the written balance.
type Entry struct {
	BalanceMinor int64
}

// Writer is an io.Writer whose Write persists. It is a persistence boundary.
type Writer struct {
	db *sql.DB
}

// Write persists the bytes it is handed.
func (w Writer) Write(p []byte) (int, error) {
	_, err := w.db.Exec("INSERT INTO gl_posting (balance_minor) VALUES ($1)", string(p))
	return len(p), err
}

// Write formats the balance into a persistence-sink writer.
func Write(db *sql.DB, x int64) {
	var v Entry
	v.BalanceMinor = x
	fmt.Fprintf(Writer{db: db}, "%d", v.BalanceMinor)
}
