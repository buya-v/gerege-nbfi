package postgres

import (
	"context"
	"fmt"
)

// InsertReturningInt64 runs an INSERT ... RETURNING <single int64> statement and
// returns the generated value. The DB seam exposes Query but not QueryRow, so
// the single returned row is read through QueryRows, which both *pgxpool.Pool
// and pgx.Tx satisfy.
func InsertReturningInt64(ctx context.Context, db DB, sql string, args ...any) (int64, error) {
	var id int64
	found := false
	err := QueryRows(ctx, db, sql, args, func(s RowScanner) error {
		if err := s.Scan(&id); err != nil {
			return err
		}
		found = true
		return nil
	})
	if err != nil {
		return 0, err
	}
	if !found {
		return 0, fmt.Errorf("postgres: INSERT ... RETURNING produced no row")
	}
	return id, nil
}
