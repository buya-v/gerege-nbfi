// GUARDS-DIR-REGISTRATION: REACHED-BY .softhouse/guards/reachguard/reachguard_test.go
// The `append(store.Rows, BatchRow{...})` half of the REAL POSITIVE control (T509 CANNOT-CATCH
// item 12), isolated in its own file so its verdict is proven independently of the pointer form
// in positive.go. The balance value flows through append into the store and on into a
// database/sql Exec of a journal_entry statement. Verdict MUST be REACHES-PERSISTENCE.
package reachpos

import "database/sql"

// BatchRow is the append-into-store form. Its balance field is deliberately named
// "Outstanding" so it is a distinct field OBJECT from Entry.Balance in the graph.
type BatchRow struct {
	Outstanding int64
}

// Batch is the store the append form writes through.
type Batch struct {
	Rows []BatchRow
}

// PersistAppend is the `append(store.Rows, BatchRow{...})` form.
func PersistAppend(db *sql.DB, x int64) error {
	var store Batch
	store.Rows = append(store.Rows, BatchRow{Outstanding: x})
	_, err := db.Exec("INSERT INTO journal_entry (outstanding_minor) VALUES ($1)", store.Rows)
	return err
}
