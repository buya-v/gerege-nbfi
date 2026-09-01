package postgres

import (
	"context"

	"github.com/jackc/pgx/v5"
)

// Querier is the read surface application repositories depend on. *pgxpool.Pool
// and pgx.Tx both satisfy it, so a repository is testable against a transaction
// as easily as against a pool, without application packages naming a concrete
// driver type.
type Querier interface {
	Query(ctx context.Context, sql string, args ...any) (pgx.Rows, error)
}

// RowScanner is the part of a result row a scan callback needs. pgx.Rows
// satisfies it; application packages receive it via QueryRows and never name
// the driver's row type themselves.
type RowScanner interface {
	Scan(dest ...any) error
}

// QueryRows runs sql with args and invokes scan once per returned row. The
// scan callback is called with the current row while the result set is still
// open and must copy everything it needs from it before returning. A non-nil
// error from scan aborts iteration and is returned.
func QueryRows(ctx context.Context, q Querier, sql string, args []any, scan func(RowScanner) error) error {
	rows, err := q.Query(ctx, sql, args...)
	if err != nil {
		return err
	}
	defer rows.Close()
	for rows.Next() {
		if err := scan(rows); err != nil {
			return err
		}
	}
	return rows.Err()
}
