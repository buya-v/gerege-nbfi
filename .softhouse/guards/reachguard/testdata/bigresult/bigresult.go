// GUARDS-DIR-REGISTRATION: REACHED-BY .softhouse/guards/reachguard/reachguard_test.go
// Package reachbigresult is the PRUNING-MUST-NOT-LOSE-A-PATH control for math/big results.
//
// A balance field is written from the RESULT of a math/big arithmetic call and that result is
// then persisted. math/big is on the persistence-inert allow-list, so the call is pruned; but
// pruning must keep the operand->result edge, or the only path from the written balance to the
// store disappears and the site is acquitted as PROVABLY-NO. That acquittal would be the exact
// fail-open this tool exists to prevent: a derived balance that reaches a store.
//
// Verdict MUST be REACHES-PERSISTENCE.
package reachbigresult

import (
	"database/sql"
	"math/big"
)

// Entry carries the written balance as this programme's money type.
type Entry struct {
	BalanceMinor *big.Int
}

// Write derives a balance through math/big and stores the derived value.
func Write(db *sql.DB, x *big.Int) error {
	var v Entry
	v.BalanceMinor = new(big.Int).Add(x, x)
	_, err := db.Exec("INSERT INTO gl_posting (balance_minor) VALUES ($1)", v.BalanceMinor.String())
	return err
}
