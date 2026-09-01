package postgres

import (
	"context"
	"fmt"
	"sort"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// Migration is one ordered schema step. Version is compared with the recorded
// schema version; SQL is applied in a single transaction when the step is not
// yet recorded.
type Migration struct {
	Version int
	Name    string
	SQL     string
}

// RunMigrations applies every migration whose Version is greater than the
// currently recorded schema version, in ascending Version order. It creates
// the version-tracking table on first use, records each applied step in the
// same transaction as its SQL, and leaves the connection in a consistent state
// on error (nothing is partially recorded).
//
// The runner is deliberately dumb: it does not checksum, it does not lock, and
// it does not support out-of-order apply. Those are operational concerns that
// belong to the deployment tool, not to a repository constructor.
func RunMigrations(ctx context.Context, pool *pgxpool.Pool, migrations []Migration) error {
	if len(migrations) == 0 {
		return nil
	}

	if err := ensureSchemaMigrations(ctx, pool); err != nil {
		return err
	}

	current, err := currentVersion(ctx, pool)
	if err != nil {
		return err
	}

	for _, m := range planMigrations(migrations, current) {
		if err := applyMigration(ctx, pool, m); err != nil {
			return err
		}
	}
	return nil
}

// planMigrations returns the migrations whose Version is greater than current,
// in ascending Version order. It is pure so the ordering and idempotence rules
// are unit-testable without a database.
func planMigrations(migrations []Migration, current int) []Migration {
	sorted := make([]Migration, len(migrations))
	copy(sorted, migrations)
	sort.Slice(sorted, func(i, j int) bool { return sorted[i].Version < sorted[j].Version })

	var out []Migration
	for _, m := range sorted {
		if m.Version > current {
			out = append(out, m)
		}
	}
	return out
}

func ensureSchemaMigrations(ctx context.Context, pool *pgxpool.Pool) error {
	const ddl = `CREATE TABLE IF NOT EXISTS schema_migrations (
		version bigint PRIMARY KEY,
		name text NOT NULL,
		applied_at timestamptz NOT NULL DEFAULT now()
	)`
	_, err := pool.Exec(ctx, ddl)
	if err != nil {
		return fmt.Errorf("postgres: create schema_migrations: %w", err)
	}
	return nil
}

func currentVersion(ctx context.Context, pool *pgxpool.Pool) (int, error) {
	var version int
	err := pool.QueryRow(ctx, `SELECT COALESCE(MAX(version), 0) FROM schema_migrations`).Scan(&version)
	if err != nil {
		return 0, fmt.Errorf("postgres: read schema version: %w", err)
	}
	return version, nil
}

func applyMigration(ctx context.Context, pool *pgxpool.Pool, m Migration) error {
	return pgx.BeginFunc(ctx, pool, func(tx pgx.Tx) error {
		if _, err := tx.Exec(ctx, m.SQL); err != nil {
			return fmt.Errorf("postgres: migrate %d %q: %w", m.Version, m.Name, err)
		}
		if _, err := tx.Exec(ctx,
			`INSERT INTO schema_migrations (version, name) VALUES ($1, $2)`,
			m.Version, m.Name); err != nil {
			return fmt.Errorf("postgres: record migration %d %q: %w", m.Version, m.Name, err)
		}
		return nil
	})
}
