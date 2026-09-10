// GUARDS-DIR-REGISTRATION: REACHED-BY .softhouse/guards/reachguard/reachguard_test.go
// Package reachbinpos is the UNION-POSITIVE control for increment 1 (binary expressions).
//
// The site writes x into a balance field. The value then reaches the persistence boundary
// ONLY through a binary expression that reads the field: `v.BalanceMinor + 1`. Before binary
// expressions were modelled, the add was a single unknown node, the field had no edge into
// the stored value, and the site could not see its own flow. With union semantics the field
// is one operand, so its flow reaches the stored `total` and the db.Exec boundary.
//
// Verdict MUST be REACHES-PERSISTENCE. A PROVABLY-NO here would be a fail-open on a real
// operand flow; an UNRESOLVED would mean the union did not carry the operand.
package reachbinpos

import "database/sql"

// Entry carries the written balance.
type Entry struct {
	BalanceMinor int64
}

// Write writes a balance field, then persists a value derived from it by a binary expression.
func Write(db *sql.DB, x int64) error {
	var v Entry
	v.BalanceMinor = x
	total := v.BalanceMinor + 1
	_, err := db.Exec("INSERT INTO gl_posting (balance_minor) VALUES ($1)", total)
	return err
}
