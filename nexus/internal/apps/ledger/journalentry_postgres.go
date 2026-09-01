package ledger

import (
	"context"
	"fmt"
	"strings"

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
func (r *PostgresJournalEntryRepository) Append(entries []JournalEntry) error {
	if len(entries) == 0 {
		return nil
	}
	sql, args := buildJournalEntryInsert(entries, r.createdByID, r.lastModifiedByID)
	if _, err := r.db.Exec(r.ctx, sql, args...); err != nil {
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

// buildJournalEntryInsert is a pure function so the SQL it produces can be
// asserted without a database. It returns a single multi-row INSERT statement
// and its positional arguments.
func buildJournalEntryInsert(entries []JournalEntry, createdByID, lastModifiedByID int64) (string, []any) {
	const columns = `(account_id, office_id, currency_code, transaction_id, reversed, manual_entry, entry_date, type_enum, amount, createdby_id, lastmodifiedby_id, created_date, lastmodified_date)`
	rows := make([]string, 0, len(entries))
	args := make([]any, 0, len(entries)*11)
	for _, e := range entries {
		rows = append(rows, fmt.Sprintf("($%d,$%d,$%d,$%d,$%d,$%d,$%d,$%d,$%d,$%d,$%d,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)",
			len(args)+1, len(args)+2, len(args)+3, len(args)+4, len(args)+5, len(args)+6,
			len(args)+7, len(args)+8, len(args)+9, len(args)+10, len(args)+11))
		args = append(args,
			e.AccountID,
			e.OfficeID,
			e.CurrencyCode,
			e.TransactionID,
			e.Reversed,
			e.ManualEntry,
			e.EntryDate,
			int32(e.Side),
			e.Amount.FormatDecimal(MNTMinorDigits),
			createdByID,
			lastModifiedByID,
		)
	}
	return "INSERT INTO acc_gl_journal_entry " + columns + " VALUES " + strings.Join(rows, ","), args
}
