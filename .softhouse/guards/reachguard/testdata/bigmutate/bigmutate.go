// GUARDS-DIR-REGISTRATION: REACHED-BY .softhouse/guards/reachguard/reachguard_test.go
// Package reachbigmutate is the POINTER-RECEIVER-MUTATION control for math/big.
//
// big.Int methods take a pointer receiver and MUTATE it: z.Add(x, y) writes the result into z.
// The written balance is fed to Add as an operand, and the STORED value is the mutated receiver
// z, not Add's discarded return. If pruning math/big dropped the operand->receiver edge, the
// written balance would have no path to the store and the site would be acquitted PROVABLY-NO.
//
// Verdict MUST be REACHES-PERSISTENCE.
package reachbigmutate

import (
	"database/sql"
	"math/big"
)

// Entry carries the written balance as this programme's money type.
type Entry struct {
	BalanceMinor *big.Int
}

// Write mutates a big.Int receiver with the written balance and stores the receiver.
func Write(db *sql.DB, x *big.Int) error {
	var v Entry
	v.BalanceMinor = x
	z := new(big.Int)
	z.Add(v.BalanceMinor, big.NewInt(1))
	_, err := db.Exec("INSERT INTO gl_posting (balance_minor) VALUES ($1)", z.String())
	return err
}
