package ledger

import (
	"context"
	"fmt"

	"github.com/gerege/nexus/internal/platform/postgres"
)

// This file is the PostgreSQL write/read surface for slice A1. It follows the
// package rule laid out in postgres.go: no concrete pgx type is named here, and
// a postgres.DB (Querier + Executor) captured at construction carries every
// statement. The import graph stays ledger -> internal/platform/postgres -> pgx.

// JournalEntryRepository is the persistence surface the posting path owns. Its
// methods carry no context.Context for the same reason the A2 read surfaces do:
// the repository captures the context it was constructed with.
type JournalEntryRepository interface {
	Append(entries []JournalEntry) error
	FindByTransactionID(transactionID string) ([]JournalEntry, error)
}

// PostgresJournalEntryRepository persists acc_gl_journal_entry rows.
type PostgresJournalEntryRepository struct {
	ctx context.Context
	db  postgres.DB

	// Audit columns are a user-context concern, not a money concern, and the
	// posting engine does not carry them. A caller that wants real audit trail
	// sets these once at construction; the default is the oracle's system user.
	createdByID      int64
	lastModifiedByID int64
}

// NewPostgresJournalEntryRepository builds the journal-entry persistence
// surface. createdByID and lastModifiedByID default to the oracle's system user
// (1) when zero.
func NewPostgresJournalEntryRepository(ctx context.Context, db postgres.DB) *PostgresJournalEntryRepository {
	return &PostgresJournalEntryRepository{ctx: ctx, db: db, createdByID: 1, lastModifiedByID: 1}
}

// SetAuditIDs overrides the created-by / last-modified-by audit columns.
func (r *PostgresJournalEntryRepository) SetAuditIDs(createdByID, lastModifiedByID int64) {
	r.createdByID = createdByID
	r.lastModifiedByID = lastModifiedByID
}

const journalEntryColumns = `id, account_id, office_id, currency_code, transaction_id, reversed, manual_entry, entry_date::text, type_enum, amount::text`

// Append writes every entry in ONE multi-row INSERT, so a transaction's legs
// commit or roll back together. The running-balance columns are deliberately
// omitted — their defaults apply, and G-12 forbids this port from writing them.
//
// THE STATEMENT IS A FIXED STRING LITERAL AND THAT IS LOAD-BEARING. [T503]
// It used to be assembled at run time — one `($n,$n,…)` tuple per entry joined
// into a VALUES list — which made it a statement no source-level reader could
// read, and the I-3/I-4 guard refused it as OPAQUE-SQL: it could not certify
// that the ledger's own write path was not an UPDATE or a DELETE against
// acc_gl_journal_entry. The row count now lives in the ARGUMENTS (eleven
// parallel arrays, unnested by Postgres into rows) instead of in the SQL, so
// the arity is fixed at eleven placeholders whatever the batch size, the whole
// statement is one literal a reader can check against DEC-2 I-4 by eye, and it
// is still exactly ONE statement — the all-or-nothing property is unchanged.
//
// `unnest` over N arrays zips them positionally, so column i of row j is
// element j of array i. The amount arrays carry EXACT DECIMAL TEXT and are cast
// to numeric by Postgres; no float exists on this path at any point.
func (r *PostgresJournalEntryRepository) Append(entries []JournalEntry) error {
	if len(entries) == 0 {
		return nil
	}
	// A local, because the guard's argument heuristic skips a leading context
	// only when it is a bare identifier; `r.ctx` would be mistaken for the SQL
	// argument and the literal below would go unread. Named backlog item in the
	// T503 handoff — the heuristic should also skip a ctx-named selector.
	ctx := r.ctx
	args := buildJournalEntryInsertArgs(entries, r.createdByID, r.lastModifiedByID)
	if _, err := r.db.Exec(ctx, `INSERT INTO acc_gl_journal_entry (account_id, office_id, currency_code, transaction_id, reversed, manual_entry, entry_date, type_enum, amount, createdby_id, lastmodifiedby_id, created_date, lastmodified_date)
		SELECT e.account_id, e.office_id, e.currency_code, e.transaction_id, e.reversed, e.manual_entry,
		       e.entry_date::date, e.type_enum, e.amount::numeric, e.createdby_id, e.lastmodifiedby_id,
		       CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
		FROM unnest($1::bigint[], $2::bigint[], $3::text[], $4::text[], $5::boolean[], $6::boolean[],
		            $7::text[], $8::integer[], $9::text[], $10::bigint[], $11::bigint[])
		     AS e(account_id, office_id, currency_code, transaction_id, reversed, manual_entry,
		          entry_date, type_enum, amount, createdby_id, lastmodifiedby_id)`, args...); err != nil {
		return fmt.Errorf("ledger: append journal entries: %w", err)
	}
	return nil
}

// FindByTransactionID returns every leg of one transaction, in id order.
func (r *PostgresJournalEntryRepository) FindByTransactionID(transactionID string) ([]JournalEntry, error) {
	const sql = `
		SELECT ` + journalEntryColumns + `
		FROM acc_gl_journal_entry
		WHERE transaction_id = $1
		ORDER BY id`
	var out []JournalEntry
	err := postgres.QueryRows(r.ctx, r.db, sql, []any{transactionID}, func(s postgres.RowScanner) error {
		var e JournalEntry
		var amountText string
		if err := s.Scan(&e.ID, &e.AccountID, &e.OfficeID, &e.CurrencyCode, &e.TransactionID,
			&e.Reversed, &e.ManualEntry, &e.EntryDate, &e.Side, &amountText); err != nil {
			return err
		}
		amt, err := MinorUnitsFromDecimalText(amountText, MNTMinorDigits)
		if err != nil {
			return fmt.Errorf("ledger: journal entry %d amount %q: %w", e.ID, amountText, err)
		}
		e.Amount = amt
		out = append(out, e)
		return nil
	})
	if err != nil {
		return nil, err
	}
	return out, nil
}

// buildJournalEntryInsertArgs is a pure function so the arguments Append binds
// can be asserted without a database. It returns the ELEVEN column arrays the
// statement in Append unnests, in placeholder order ($1..$11); every array has
// one element per entry and they are positionally aligned, so element j of each
// is column j of the row that entry j becomes.
//
// The amount is rendered to exact decimal text from integer minor units and
// cast to numeric by Postgres. It is never a float in Go and never a float on
// the wire.
func buildJournalEntryInsertArgs(entries []JournalEntry, createdByID, lastModifiedByID int64) []any {
	n := len(entries)
	accountID := make([]int64, n)
	officeID := make([]int64, n)
	currencyCode := make([]string, n)
	transactionID := make([]string, n)
	reversed := make([]bool, n)
	manualEntry := make([]bool, n)
	entryDate := make([]string, n)
	typeEnum := make([]int32, n)
	amount := make([]string, n)
	createdBy := make([]int64, n)
	lastModifiedBy := make([]int64, n)
	for i, e := range entries {
		accountID[i] = e.AccountID
		officeID[i] = e.OfficeID
		currencyCode[i] = e.CurrencyCode
		transactionID[i] = e.TransactionID
		reversed[i] = e.Reversed
		manualEntry[i] = e.ManualEntry
		entryDate[i] = e.EntryDate
		typeEnum[i] = int32(e.Side)
		amount[i] = e.Amount.FormatDecimal(MNTMinorDigits)
		createdBy[i] = createdByID
		lastModifiedBy[i] = lastModifiedByID
	}
	return []any{
		accountID, officeID, currencyCode, transactionID, reversed, manualEntry,
		entryDate, typeEnum, amount, createdBy, lastModifiedBy,
	}
}
