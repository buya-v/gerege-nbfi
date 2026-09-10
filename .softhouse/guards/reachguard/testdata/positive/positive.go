// GUARDS-DIR-REGISTRATION: REACHED-BY .softhouse/guards/reachguard/reachguard_test.go
// Package reachpos is the REAL POSITIVE control for reachguard (LEG 2).
//
// It contains the two composite-literal-into-store forms that ledgerguard admits it cannot
// see (T509 CANNOT-CATCH items 10 and 12):
//
//	v := Entry{Balance: x}            // then a store of &v
//	store.Rows = append(store.Rows, BatchRow{Outstanding: x})
//
// In both, the balance value reaches a persistence boundary — a database/sql Exec of a
// journal_entry / gl_posting statement naming a balance column. The boundary is identified by
// the method OBJECT (*database/sql.DB).Exec, not by this file's path or package name, so the
// verdict must be REACHES-PERSISTENCE and must not move when this file moves (see mv/).
package reachpos

import "database/sql"

// Entry is the pointer-store form. Its balance field is deliberately named "Balance".
type Entry struct {
	Balance int64
}

// PersistPointer is the `v := Entry{Balance: x}` ... store `&v` form.
func PersistPointer(db *sql.DB, x int64) error {
	v := Entry{Balance: x}
	_, err := db.Exec("INSERT INTO gl_posting (balance_minor) VALUES ($1)", &v)
	return err
}
