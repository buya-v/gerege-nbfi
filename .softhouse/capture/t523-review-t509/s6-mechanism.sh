#!/usr/bin/env bash
# T523 item 5, follow-up — ISOLATE THE MECHANISM OF THE S6 FAIL-OPEN.
#
# S6 showed a spliced INSERT routed through a discovered wrapper going GREEN. Two candidate
# causes: (a) the pass-through carve-out at main.go:1115-1119, which treats the ident equal to
# the ENCLOSING function's sql-parameter name as unrefusable; or (b) something unrelated to
# the parameter name. Varying ONLY the local variable's name decides it.
#
# Usage: s6-mechanism.sh <ledgerguard-binary> <scratch-dir>
set -u -o pipefail
BIN="$1"; SCR="$2"; mkdir -p "$SCR"

ballast() {
  mkdir -p "$1/ballast"
  cat > "$1/ballast/ballast.go" <<'GO'
package ballast

type Row struct{ ID, Amount int64 }

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

variant() { # <name> <param-name> <carrier-decl-line> <carrier-ident>
  local name="$1" pname="$2" decl="$3" ident="$4"
  local d="$SCR/$name"; rm -rf "$d"; mkdir -p "$d/probe"; ballast "$d"
  cat > "$d/probe/probe.go" <<GO
package probe

import "context"

type DB interface {
	Exec(ctx context.Context, sql string, args ...any) error
	Query(ctx context.Context, sql string, args ...any) error
}

func InsertReturningInt64(ctx context.Context, db DB, sql string, args ...any) (int64, error) {
	if err := db.Query(ctx, sql, args...); err != nil {
		return 0, err
	}
	return 0, nil
}

func Insert(ctx context.Context, db DB, $pname string, cols string, a int64) (int64, error) {
	$decl
	return InsertReturningInt64(ctx, db, $ident, a)
}
GO
  local out rc cls
  out="$("$BIN" --root "$d" 2>&1)"; rc=$?
  cls="$(printf '%s\n' "$out" | grep -a -oE '^  \[[A-Z0-9-]+\] [^ ]+' | sort -u | tr '\n' ' ')"
  printf '%-42s exit=%d  %s\n' "$name" "$rc" "$cls"
}

SPLICE='"INSERT INTO m_loan_transaction (" + cols + ") VALUES ($1)"'

# A: the enclosing sql-param is REASSIGNED with a spliced statement, then forwarded.
variant "A-param-named-sql-reassigned"        sql "sql = $SPLICE"        sql
# B: identical, except the parameter is named `raw`, so the carve-out cannot match.
variant "B-param-named-raw-reassigned"        raw "raw = $SPLICE"        raw
# C: the splice goes into a NEW local named sql; the param is named raw.
variant "C-newlocal-named-sql"                raw "sql := $SPLICE"       sql
# D: the splice is passed inline (drive-red PLANT 12's shape) — the known-good refusal.
variant "D-inline-splice-control"             raw "_ = raw"              "$SPLICE"
