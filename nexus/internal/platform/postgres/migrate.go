package postgres

import (
	"context"
	"fmt"
	"sort"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// Migration is one ordered schema step. Version is compared with the recorded
// schema version; Apply runs in a single transaction when the step is not yet
// recorded, together with the row that records it.
//
// WHY Apply IS A FUNCTION AND NOT A SQL STRING. [T503]
//
// It used to be `SQL string`, and `tx.Exec(ctx, m.SQL)` was a mutating driver
// call whose statement no source-level reader could see. The I-3/I-4 guard
// refused it as OPAQUE-SQL, and the refusal was CORRECT: a `string` field is a
// channel through which an UPDATE or DELETE against acc_gl_journal_entry could
// reach the database from anywhere — a caller's variable, a file, an argv — and
// nothing in the Go tree would show it. "The ledger is append-only" was not
// checkable across that boundary, and the guard is not permitted to assume.
//
// Carrying the STEP instead of the TEXT moves each statement into a Go function
// body, where the natural way to write it is a string literal the guard reads
// in place:
//
//	postgres.Migration{Version: 1, Name: "wc_loan", Apply: func(ctx context.Context, tx postgres.Executor) error {
//	    _, err := tx.Exec(ctx, `CREATE TABLE m_wc_loan (...)`)
//	    return err
//	}}
//
// This is not an exemption and it does not narrow the guard's reach — it widens
// it. A migration that still builds its SQL at run time is refused at ITS OWN
// call site, which is where the statement actually is, instead of being
// permanently invisible behind this runner. The alternative — leaving `SQL
// string` and asking DEC-2 to exempt the runner — is set out in the T503
// handoff and rejected there; it is also a `user` gate, which this is not.
//
// WHAT IT COSTS, STATED RATHER THAN HIDDEN: a migration can no longer be loaded
// as text from a .sql file or a changelog and handed to this runner. Nothing in
// this tree does that today (RunMigrations has no callers yet), and Fineract's
// own schema arrives through Fineract's Liquibase, not through here. If a text
// loader is ever genuinely needed, it is a DEC-2 exemption conversation with a
// named, bounded scope — not a silent `string` field.
type Migration struct {
	Version int
	Name    string
	Apply   func(ctx context.Context, tx Executor) error
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
	// The DDL is written INTO the call rather than bound to a const first. A
	// const is an identifier at the call site, and the I-3/I-4 guard reads the
	// argument, not the declaration — via a name it could not certify this DDL
	// was not an UPDATE against acc_gl_journal_entry, and refused it. [T503]
	_, err := pool.Exec(ctx, `CREATE TABLE IF NOT EXISTS schema_migrations (
		version bigint PRIMARY KEY,
		name text NOT NULL,
		applied_at timestamptz NOT NULL DEFAULT now()
	)`)
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
	// A step with no Apply is a REFUSAL, not a no-op. Skipping it would record
	// the version as applied and leave the schema behind it, which is the one
	// failure a migration runner must never produce silently.
	if m.Apply == nil {
		return fmt.Errorf("postgres: migrate %d %q: the step carries no Apply function, so it "+
			"would record a version it did not apply", m.Version, m.Name)
	}
	return pgx.BeginFunc(ctx, pool, func(tx pgx.Tx) error {
		if err := m.Apply(ctx, tx); err != nil {
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
