#!/usr/bin/env bash
# T523 item 5 — DOES sqlArgOf / the OPAQUE-SQL arm FAIL CLOSED?
#
# T502's B-1 widening was refusal-REDUCING (T506 F-5). T509 says it kept the widening and
# corrected the DIRECTION in the record. The claim to test is behavioural: an SQL argument the
# guard cannot resolve must produce a REFUSAL, not a pass. Each case below is a scratch tree
# with enough population to clear the P-35 gates, plus one probe.
#
# Usage: sqlarg-direction.sh <ledgerguard-binary> <scratch-dir>
set -u -o pipefail
BIN="$1"; SCR="$2"
mkdir -p "$SCR"

# ballast: gives every probe tree a non-zero funcs/assignments/literals/composites population
# so the refusal (or pass) is about the probe, not about P-35.
ballast() {
  mkdir -p "$1/ballast"
  cat > "$1/ballast/ballast.go" <<'GO'
package ballast

type Row struct {
	ID     int64
	Amount int64
}

func Sum(rs []Row) int64 {
	var total int64
	for _, r := range rs {
		total += r.Amount
	}
	return total
}

func Make(id int64) Row { return Row{ID: id, Amount: 0} }

func Note() string { return "ballast prose literal" }
GO
}

probe() { # <name> <expect: REFUSE|PASS> <go-source-on-stdin>
  local name="$1" expect="$2"
  local d="$SCR/$name"
  rm -rf "$d"; mkdir -p "$d/probe"
  ballast "$d"
  cat > "$d/probe/probe.go"
  local out rc cls
  out="$("$BIN" --root "$d" 2>&1)"; rc=$?
  cls="$(printf '%s\n' "$out" | grep -a -oE '^  \[[A-Z0-9-]+\] [^ ]+' | sort -u | tr '\n' ' ')"
  local verdict="UNEXPECTED"
  { [ "$expect" = "REFUSE" ] && [ "$rc" -ne 0 ]; } && verdict="as-expected"
  { [ "$expect" = "PASS" ]   && [ "$rc" -eq 0 ]; } && verdict="as-expected"
  printf '%-34s want=%-7s exit=%d  %-10s %s\n' "$name" "$expect" "$rc" "$verdict" "$cls"
}

DB='type DB interface {
	Exec(ctx context.Context, sql string, args ...any) error
	Query(ctx context.Context, sql string, args ...any) error
}'

probe S1-nonliteral-arg REFUSE <<GO
package probe

import "context"

$DB

func build() string { return "UPDATE acc_gl_journal_entry SET amount = 1" }

func Run(ctx context.Context, db DB) error { return db.Exec(ctx, build()) }
GO

probe S2-var-arg REFUSE <<GO
package probe

import "context"

$DB

type repo struct {
	ctx context.Context
	db  DB
}

func (r repo) Run(stmt string) error { return r.db.Exec(r.ctx, stmt) }
GO

probe S3-too-few-args REFUSE <<GO
package probe

import "context"

$DB

type oneArg interface{ Exec(ctx context.Context) error }

func Run(ctx context.Context, o oneArg) error { return o.Exec(ctx) }
GO

probe S4-field-holds-stmt REFUSE <<GO
package probe

import "context"

$DB

type repo struct {
	stmt string
	db   DB
	ctx  context.Context
}

func (r repo) Run(a int64) error { return r.db.Exec(r.ctx, r.stmt, a) }
GO

probe S5-ctxnamed-field-holds-sql REFUSE <<GO
package probe

import "context"

$DB

// ATTACK: sqlArgOf skips ANY selector whose name contains "ctx", by NAME. Here the field
// named ctxStmt is the statement; the guard skips it and reads args[1], an int64.
type repo struct {
	ctxStmt string
	db      DB
}

func (r repo) Run(a int64) error { return r.db.Exec(r.ctxStmt, a) }
GO

probe S6-wrapper-param-reassigned REFUSE <<GO
package probe

import "context"

$DB

// A discovered wrapper: string param named sql, forwarded to the driver.
func InsertReturningInt64(ctx context.Context, db DB, sql string, args ...any) (int64, error) {
	if err := db.Query(ctx, sql, args...); err != nil {
		return 0, err
	}
	return 0, nil
}

// ATTACK on the pass-through carve-out: the enclosing function HAS a string param named
// sql, and REASSIGNS it by splicing before forwarding. The argument is still the ident
// "sql", which the carve-out treats as an unrefusable pass-through.
func Insert(ctx context.Context, db DB, sql string, cols string, a int64) (int64, error) {
	sql = "INSERT INTO m_loan_transaction (" + cols + ") VALUES (\$1)"
	return InsertReturningInt64(ctx, db, sql, a)
}
GO

probe S7-select-prefix-splice REFUSE <<GO
package probe

import "context"

$DB

func InsertReturningInt64(ctx context.Context, db DB, sql string, args ...any) (int64, error) {
	if err := db.Query(ctx, sql, args...); err != nil {
		return 0, err
	}
	return 0, nil
}

// ATTACK on readableVerbIsSelect: the literal PREFIX is SELECT, the body is spliced and
// invisible. The guard reads "select from x" and calls the statement readable.
func Run(ctx context.Context, db DB, body string, a int64) (int64, error) {
	return InsertReturningInt64(ctx, db, "SELECT "+body+" FROM x WHERE id = \$1", a)
}
GO

# CONTROL: a fully readable lawful statement through the same wrapper must PASS, so a
# blanket refusal cannot be mistaken for fail-closed behaviour.
probe S8-CONTROL-readable-literal PASS <<GO
package probe

import "context"

$DB

func InsertReturningInt64(ctx context.Context, db DB, sql string, args ...any) (int64, error) {
	if err := db.Query(ctx, sql, args...); err != nil {
		return 0, err
	}
	return 0, nil
}

func Run(ctx context.Context, db DB, a int64) (int64, error) {
	return InsertReturningInt64(ctx, db, "INSERT INTO m_loan_transaction (loan_id) VALUES (\$1) RETURNING id", a)
}
GO
