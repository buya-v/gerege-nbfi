package ledger

import (
	"context"

	"github.com/gerege/nexus/internal/platform/postgres"
)

// This file is slice A3's closure arm: the GLClosure row and the
// accounting-closed predicate the posting engine consults.

// GLClosure is one row of acc_gl_closure. It is the ONLY thing the closure rule
// reads — the latest closing date for an office — and it is carried as a strict
// `yyyy-MM-dd` calendar date (no offset, no zone, no timestamp).
type GLClosure struct {
	ID          int64
	OfficeID    int64
	ClosingDate string // strict yyyy-MM-dd
	Comments    string
	Deleted     bool
}

// GLClosureRepository is the read surface the posting engine needs: the latest
// (non-deleted) closure for an office, or none. It mirrors the oracle's
// getLatestGLClosureByBranch, which returns null when no closure exists.
type GLClosureRepository interface {
	LatestByOffice(officeID int64) (*GLClosure, error)
}

// LatestClosingDateFor returns the office's latest closing date, or "" when no
// closure exists. "" is the engine's "skip the closure rule" signal, matching
// the oracle's latestGLClosure == null branch.
func LatestClosingDateFor(officeID int64, r GLClosureRepository) (string, error) {
	c, err := r.LatestByOffice(officeID)
	if err != nil || c == nil {
		return "", err
	}
	return c.ClosingDate, nil
}

// AccountingClosedBy reports whether a transaction dated on transactionDate is
// refused by an office's latest closure. The boundary is INCLUSIVE: an entry
// dated ON the closing date is refused, because the oracle's guard is
// `!isBefore(closingDate, transactionDate)` and isBefore is a strict `<`.
func AccountingClosedBy(latestClosingDate, transactionDate string) bool {
	return latestClosingDate != "" && transactionDate != "" &&
		!isoBefore(latestClosingDate, transactionDate)
}

// PostgresGLClosureRepository reads acc_gl_closure through the platform seam.
// It follows the package's rule: this package never names a concrete pgx type;
// it receives a postgres.DB (Querier + Executor) captured at construction.
type PostgresGLClosureRepository struct {
	ctx context.Context
	db  postgres.DB
}

// NewPostgresGLClosureRepository builds the closure read surface.
func NewPostgresGLClosureRepository(ctx context.Context, db postgres.DB) *PostgresGLClosureRepository {
	return &PostgresGLClosureRepository{ctx: ctx, db: db}
}

// LatestByOffice returns the most recent non-deleted closure for an office, or
// nil when none exists.
func (r *PostgresGLClosureRepository) LatestByOffice(officeID int64) (*GLClosure, error) {
	const sql = `
		SELECT id, office_id, closing_date::text, COALESCE(comments, ''), is_deleted
		FROM acc_gl_closure
		WHERE office_id = $1 AND is_deleted = false
		ORDER BY closing_date DESC
		LIMIT 1`
	var out *GLClosure
	err := postgres.QueryRows(r.ctx, r.db, sql, []any{officeID}, func(s postgres.RowScanner) error {
		var c GLClosure
		if err := s.Scan(&c.ID, &c.OfficeID, &c.ClosingDate, &c.Comments, &c.Deleted); err != nil {
			return err
		}
		out = &c
		return nil
	})
	if err != nil {
		return nil, err
	}
	return out, nil
}
