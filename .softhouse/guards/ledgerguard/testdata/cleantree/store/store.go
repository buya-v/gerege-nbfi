// GUARDS-DIR-REGISTRATION: REACHED-BY .softhouse/guards/ledgerguard/main.go
//
// See the note on the same row in ../ledger/derive.go: the witness requires this file by name
// in selftest case (n) before it will trust the fixture.
//
// Package store is the CORRECT shape of everything the SQL classes refuse: I4-DML,
// I3-SQL-BALANCE, I3-SQL-BALANCE-TABLE and OPAQUE-SQL. Each statement below is the
// lawful counterpart of a planted defect in the selftest.
package store

import "context"

// DB is the driver seam. Naming it here gives the wrapper-discovery pass something
// real to discover, so the fixture exercises that machinery GREEN as well.
type DB interface {
	Exec(ctx context.Context, sql string, args ...any) error
	Query(ctx context.Context, sql string, args ...any) error
}

// appendEntrySQL — APPENDING to the journal is the only lawful write to it, and it
// MUST pass. A guard that refused INSERT would refuse the correct implementation.
const appendEntrySQL = `INSERT INTO acc_gl_journal_entry
(account_id, office_id, currency_code, transaction_id, entry_date, type_enum, amount)
VALUES ($1,$2,$3,$4,$5,$6,$7)`

// readEntriesSQL — READING is not writing. This SELECT names a balance column on
// purpose: it must appear in the balance-read CENSUS and must NOT be a finding,
// because DEC-2 §4.4 I-3 grades a WRITE path.
const readEntriesSQL = `SELECT id, account_id, outstanding_loan_balance_derived
FROM m_loan_transaction WHERE loan_id = $1 ORDER BY id`

// Append issues the lawful INSERT through the driver, with the statement as a plain
// literal so the guard can read it.
func Append(ctx context.Context, db DB, args ...any) error {
	return db.Exec(ctx, appendEntrySQL, args...)
}

// QueryRows is a tree-local SQL wrapper: a `sql string` parameter forwarded to the
// driver. discoverSQLWrappers must find it, and the pass-through of its own parameter
// must NOT be refused as opaque — refusing there would refuse every wrapper for being
// a wrapper, which says nothing about any caller.
func QueryRows(ctx context.Context, db DB, sql string, args []any) error {
	return db.Query(ctx, sql, args...)
}

// InsertReturningInt64 is the shape T506's F-6 found invisible: a mutating wrapper
// that reaches the database through Query. It is lawful HERE because every call site
// hands it a readable literal.
func InsertReturningInt64(ctx context.Context, db DB, sql string, args ...any) (int64, error) {
	if err := QueryRows(ctx, db, sql, args); err != nil {
		return 0, err
	}
	return 0, nil
}

// Read calls the wrapper with a literal the guard can read end to end.
func Read(ctx context.Context, db DB, loanID int64) error {
	return QueryRows(ctx, db, readEntriesSQL, []any{loanID})
}

// InsertTransaction calls the mutating wrapper with a fully readable statement. No
// column list is spliced in, so nothing is hidden from the classifier.
func InsertTransaction(ctx context.Context, db DB, loanID, amountMinor int64) (int64, error) {
	return InsertReturningInt64(ctx, db, `INSERT INTO m_loan_transaction
(loan_id, transaction_type_enum, amount) VALUES ($1,$2,$3) RETURNING id`,
		loanID, 1, amountMinor)
}

// ctxHolder pins the direction recorded on sqlArgOf: a repository that carries its
// context as a FIELD and passes a plain literal must be READ, not refused.
type ctxHolder struct {
	ctx context.Context
	db  DB
}

func (r ctxHolder) Append(args ...any) error {
	return r.db.Exec(r.ctx, appendEntrySQL, args...)
}
