#!/usr/bin/env bash
# T523 item 5, follow-up 2 — HOW FAR DOES readableVerbIsSelect (main.go:667-679) OPEN?
#
# It concatenates only the LITERAL fragments of a spliced expression, lowercases, and calls the
# statement readable if that text starts with "select" and carries no mutating verb. The spliced
# segments are invisible to it, so the verdict rests on a literal PREFIX. These probes measure
# how far that reaches, including the multi-statement shape pgx's simple protocol permits.
#
# Usage: s7-select-prefix.sh <ledgerguard-binary> <scratch-dir>
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

probe() { # <name> <expr-source>
  local name="$1" expr="$2"
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

func Run(ctx context.Context, db DB, evil string, a int64) (int64, error) {
	return InsertReturningInt64(ctx, db, $expr, a)
}
GO
  local out rc cls
  out="$("$BIN" --root "$d" 2>&1)"; rc=$?
  cls="$(printf '%s\n' "$out" | grep -a -oE '^  \[[A-Z0-9-]+\] [^ ]+' | sort -u | tr '\n' ' ')"
  printf '%-40s exit=%d  %s\n' "$name" "$rc" "$cls"
}

probe P1-select-prefix-splice        '"SELECT " + evil + " FROM x"'
probe P2-select-semicolon-splice     '"SELECT 1;" + evil'
probe P3-select-comment-splice       '"SELECT 1 -- " + evil'
probe P4-select-calls-function       '"SELECT apply_balance(" + evil + ")"'
probe P5-CONTROL-update-prefix       '"UPDATE " + evil + " SET amount = 1"'
probe P6-CONTROL-insert-prefix       '"INSERT INTO " + evil + " VALUES (1)"'
probe P7-CONTROL-bare-splice         'evil + " FROM x"'
