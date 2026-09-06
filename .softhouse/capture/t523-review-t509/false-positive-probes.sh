#!/usr/bin/env bash
# T523 item 2 / item 7 — WHICH NEW REFUSALS TRACK THE PROPERTY, AND WHICH TRACK THE SPELLING?
#
# The property CLAUDE.md states is "balances are derived, never written" — a STORED balance
# receives a value. Each probe below is code that a reasonable author would write and that
# does NOT store a balance. A refusal here is a false positive on a non-negotiable, and it is
# expensive: the author must either clear a non-defect or add an exemption.
#
# Usage: false-positive-probes.sh <ledgerguard-binary> <scratch-dir>
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

probe() { # <name> <verdict-wanted: CLEAN|REFUSE> ; source on stdin
  local name="$1" want="$2"
  local d="$SCR/$name"; rm -rf "$d"; mkdir -p "$d/probe"; ballast "$d"
  cat > "$d/probe/probe.go"
  local out rc cls
  out="$("$BIN" --root "$d" 2>&1)"; rc=$?
  cls="$(printf '%s\n' "$out" | grep -a -oE '^  \[[A-Z0-9-]+\]' | sort -u | tr '\n' ' ')"
  local flag='  '
  if [ "$want" = "CLEAN" ] && [ "$rc" -ne 0 ]; then flag='FP'; fi
  if [ "$want" = "REFUSE" ] && [ "$rc" -eq 0 ]; then flag='FN'; fi
  printf '%s %-34s want=%-6s exit=%d  %s\n' "$flag" "$name" "$want" "$rc" "$cls"
}

# FP1 — a READ-ONLY projection. It SELECTs a balance column and decodes it into a struct
#       field. No INSERT, no UPDATE, nothing stored. CANNOT-CATCH item 9 says a READ is
#       named, not refused — but the DECODE is a field assignment.
probe FP1-readonly-decode CLEAN <<'GO'
package probe

import "context"

type DB interface {
	Query(ctx context.Context, sql string, args ...any) error
}

type View struct{ OutstandingMinor int64 }

const readSQL = `SELECT total_outstanding_derived FROM m_loan WHERE id = $1`

func Load(ctx context.Context, db DB, id int64, raw int64) (View, error) {
	var v View
	if err := db.Query(ctx, readSQL, id); err != nil {
		return v, err
	}
	v.OutstandingMinor = raw
	return v, nil
}
GO

# FP2 — a BOOLEAN flag whose name contains "outstanding". Not money at all.
probe FP2-boolean-hasoutstanding CLEAN <<'GO'
package probe

type Loan struct{ HasOutstanding bool }

func Mark(l *Loan, any bool) { l.HasOutstanding = any }
GO

# FP3 — a COUNTER of things outstanding. The guard's own note names this shape.
probe FP3-outstanding-request-count CLEAN <<'GO'
package probe

type Queue struct{ OutstandingRequests int }

func Enqueue(q *Queue) { q.OutstandingRequests++ }
GO

# FP4 — a ZERO-INITIALISING CONSTRUCTOR. Nothing is derived and nothing is stored; the field
#       is declared at its zero value. There is no "derive by summation" repair for this.
probe FP4-zero-init-constructor CLEAN <<'GO'
package probe

type Period struct{ OutstandingLoanBalance int64 }

func NewPeriod() *Period { return &Period{OutstandingLoanBalance: 0} }
GO

# FP5 — a DEEP COPY CONSTRUCTOR. Field copied from the same field of the same type.
probe FP5-copy-constructor CLEAN <<'GO'
package probe

type Period struct{ OutstandingLoanBalance int64 }

func (p *Period) Copy() *Period { return &Period{OutstandingLoanBalance: p.OutstandingLoanBalance} }
GO

# FP6 — an ENUM/STRATEGY name. Written to a config struct, carries no money.
probe FP6-strategy-enum CLEAN <<'GO'
package probe

type Cfg struct{ OutstandingInterestStrategy string }

func Set(c *Cfg, s string) { c.OutstandingInterestStrategy = s }
GO

# TP1 — the TRUE POSITIVE control: a stored balance written through the driver. If this went
#       clean, every CLEAN result above would be worthless.
probe TP1-CONTROL-stored-balance REFUSE <<'GO'
package probe

import "context"

type DB interface {
	Exec(ctx context.Context, sql string, args ...any) error
}

func Store(ctx context.Context, db DB, id, v int64) error {
	return db.Exec(ctx, `UPDATE m_savings_account SET account_balance_derived = $1 WHERE id = $2`, v, id)
}
GO
