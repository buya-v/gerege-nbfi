// GUARDS-DIR-REGISTRATION: REACHED-BY .softhouse/guards/reachguard/reachguard_test.go
// The nested-container half of the REAL POSITIVE control.
//
// A balance composite nested inside a slice literal, assigned to a store field and then
// persisted. This form also exposed a genuine fail-open in an earlier revision: a slice
// literal's element was not linked to the container literal, so the element's balance node
// dead-ended and the site came back PROVABLY-NO. processLit now links unkeyed/keyed container
// elements to the container literal. Verdict MUST be REACHES-PERSISTENCE.
package reachpos

import "database/sql"

// NestedRow is the inner balance composite.
type NestedRow struct {
	Outstanding int64
}

// NestedStore holds the slice that is persisted.
type NestedStore struct {
	Rows []NestedRow
}

// PersistNested builds the slice literal in place and persists the container.
func PersistNested(db *sql.DB, x int64) error {
	var store NestedStore
	store.Rows = []NestedRow{{Outstanding: x}}
	_, err := db.Exec("INSERT INTO journal_entry (outstanding_minor) VALUES ($1)", store.Rows)
	return err
}
