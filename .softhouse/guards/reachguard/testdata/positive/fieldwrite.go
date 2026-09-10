// GUARDS-DIR-REGISTRATION: REACHED-BY .softhouse/guards/reachguard/reachguard_test.go
// The direct-field-write half of the REAL POSITIVE control.
//
// This form exposed a genuine fail-open in an earlier revision: a write to v.Balance was
// modelled as a lone field node, so when the WHOLE struct v was later passed to db.Exec the
// write was not in the persisted value's provenance and the site came back PROVABLY-NO. A
// field is part of its base value, so detectFieldWrites now also carries the base's value
// nodes. Verdict MUST be REACHES-PERSISTENCE.
package reachpos

import "database/sql"

// Ledger is a whole struct that is persisted after a field-only write.
type Ledger struct {
	Balance int64
}

// PersistField writes a balance field, then stores the whole struct.
func PersistField(db *sql.DB, x int64) error {
	var v Ledger
	v.Balance = x
	_, err := db.Exec("INSERT INTO gl_posting (balance_minor) VALUES ($1)", v)
	return err
}
