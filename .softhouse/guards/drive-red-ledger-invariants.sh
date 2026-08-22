#!/usr/bin/env bash
# drive-red-ledger-invariants.sh — P-22 over the REAL POPULATION, not a synthetic one.
#
# `ledgerguard --selftest` drives every class red on small synthetic packages. That proves the
# DETECTOR. It does not prove the detector fires when the defect is one file among forty-four,
# inside the tree the guard will actually be pointed at. P-56: test it WHERE IT RUNS.
#
# So this script COPIES nexus/ to a scratch directory, plants ONE violation per class in a REAL
# ledger source file, runs the guard over the scratch copy, and requires the expected class to
# fire. The repository is never modified: every plant lands in $TMPDIR and is deleted.
#
# It also runs the CONTROL — the unmodified copy must come out GREEN. A prover that only ever
# shows red proves the guard is noisy, not that it is right (P-50).
#
# Usage:  bash .softhouse/guards/drive-red-ledger-invariants.sh
# Exit:   0 every class drove red and the control drove green; 1 otherwise; 2 unusable.

set -u -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
NEXUS_DIR="$REPO_ROOT/nexus"
GUARD_SRC="$SCRIPT_DIR/ledgerguard"

say() { printf '%s\n' "$*"; }

env_script="$REPO_ROOT/.softhouse/bin/go-env.sh"
if [ -f "$env_script" ]; then
  # shellcheck disable=SC1090
  . "$env_script"
fi
if ! command -v go >/dev/null 2>&1; then
  say "drive-red: no Go toolchain; the guard cannot be built. EXIT 2 — NOT a pass."
  exit 2
fi
if [ ! -d "$NEXUS_DIR" ]; then
  say "drive-red: $NEXUS_DIR is missing. There is no real population to plant into. EXIT 2."
  exit 2
fi

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
BIN="$WORK/ledgerguard"
if ! (cd "$GUARD_SRC" && go build -o "$BIN" .); then
  say "drive-red: the guard did not compile. EXIT 2 — NOT a pass."
  exit 2
fi

fails=0

# fresh_copy prints the path to a pristine copy of nexus/.
fresh_copy() {
  local d="$WORK/tree.$1"
  rm -rf "$d"
  mkdir -p "$d"
  # `cp -R src/. dst` copies the CONTENTS, so the copy is a tree root exactly like nexus/.
  cp -R "$NEXUS_DIR/." "$d/"
  printf '%s\n' "$d"
}

# run_plant <label> <n> <expected-class> <planted-file-relpath> <<'GO' ...content...
run_plant() {
  local label="$1" n="$2" want="$3" relpath="$4"
  local d out rc
  d="$(fresh_copy "$n")"
  mkdir -p "$(dirname "$d/$relpath")"
  cat > "$d/$relpath"
  say "--- PLANT $n: $label"
  say "    planted at: $relpath (inside a scratch copy of nexus/, never in the repository)"
  out="$("$BIN" --root "$d" 2>&1)"; rc=$?
  say "    -> exit $rc"
  if [ "$rc" -eq 0 ]; then
    say "    FAIL the guard PASSED a tree carrying the planted defect"
    fails=1
  elif ! printf '%s\n' "$out" | LC_ALL=C grep -aq "\[$want\]"; then
    say "    FAIL the guard refused, but class $want never fired (it failed for the wrong reason)"
    printf '%s\n' "$out" | LC_ALL=C grep -a '^  \[' | LC_ALL=C sed 's/^/        /'
    fails=1
  else
    printf '%s\n' "$out" | LC_ALL=C grep -a "\[$want\]" | LC_ALL=C sed 's/^  /    FIRED /'
  fi
  # The census must still be truthful on a tree that FAILS: a refusal that inspected nothing
  # is as worthless as a pass that inspected nothing.
  printf '%s\n' "$out" | LC_ALL=C grep -a '^CENSUS ledger-invariants — ' | LC_ALL=C sed 's/^/    /'
  rm -rf "$d"
}

say "==== DRIVE RED: every violation class, planted in a scratch copy of the REAL nexus/ tree ===="
say ""

run_plant "a balance field WRITTEN rather than derived (I-3)" 1 I3-FIELD-WRITE \
  "internal/apps/ledger/planted_balance.go" <<'GO'
package ledger

// PLANTED DEFECT — I-3. A stored balance, incremented on posting.
type AccountBalance struct {
	AccountID    int64
	BalanceMinor int64
}

func ApplyLeg(b *AccountBalance, leg PostingLeg) {
	b.BalanceMinor += int64(leg.Amount)
}
GO

run_plant "an UPDATE against acc_gl_journal_entry (I-4)" 2 I4-DML \
  "internal/apps/ledger/planted_update.go" <<'GO'
package ledger

// PLANTED DEFECT — I-4. A reversal implemented as a mutation of the committed row.
const reverseEntrySQL = "UPDATE acc_gl_journal_entry SET reversed = true, reversal_id = $1 WHERE id = $2"
GO

run_plant "a DELETE against acc_gl_journal_entry (I-4)" 3 I4-DML \
  "internal/apps/ledger/planted_delete.go" <<'GO'
package ledger

// PLANTED DEFECT — I-4. A correction implemented by removing the leg.
const purgeEntriesSQL = "DELETE FROM acc_gl_journal_entry WHERE transaction_identifier = $1"
GO

run_plant "a hold mutating the POSTED balance rather than available (I-6)" 4 I6-HOLD-BALANCE \
  "internal/apps/ledger/planted_hold.go" <<'GO'
package ledger

// PLANTED DEFECT — I-6. A hold that moves the posted balance.
type SavingsPosition struct {
	PostedBalanceMinor    int64
	AvailableBalanceMinor int64
}

func PlaceHold(p *SavingsPosition, amountMinor int64) {
	p.PostedBalanceMinor -= amountMinor
}
GO

run_plant "a balance column populated at INSERT — the m_trial_balance shape (I-3)" 5 I3-SQL-BALANCE \
  "internal/apps/ledger/planted_trialbalance.go" <<'GO'
package ledger

// PLANTED DEFECT — I-3. DEC-2 §4.4 I-3 / §7: closing_balance is a written, stored sum
// wearing a balance's name, and is deliberately not ported.
const trialBalanceSQL = "INSERT INTO m_trial_balance (office_id, account_id, closing_balance) VALUES ($1,$2,$3)"
GO

run_plant "an ORM delete of a JournalEntry, with no SQL text anywhere (I-4)" 6 I4-BUILDER \
  "internal/apps/ledger/planted_orm.go" <<'GO'
package ledger

// PLANTED DEFECT — I-4 in the form DEC-2 §4.4.1 calls "any Go call that would emit one".
type JournalEntry struct{ ID int64 }

type repo struct{}

func (r repo) Model(v any) repo     { return r }
func (r repo) Delete(v any) error   { return nil }

func purge(r repo, id int64) error {
	return r.Model(&JournalEntry{ID: id}).Delete(nil)
}
GO

run_plant "SQL the guard cannot read, in a mutating driver call (blind spot -> refusal)" 7 OPAQUE-SQL \
  "internal/apps/ledger/planted_dynamic.go" <<'GO'
package ledger

// PLANTED DEFECT — the blind spot itself. If this passed, every other class could be
// evaded by building the statement at run time.
type conn struct{}

func (c conn) Exec(ctx any, sql string, args ...any) error { return nil }

func build(table, col string) string { return "UPDATE " + table + " SET " + col + " = $1" }

func run(c conn, ctx any) error { return c.Exec(ctx, build("acc_gl_journal_entry", "reversed")) }
GO

run_plant "a package-level balance store (I-3)" 8 I3-PKG-STATE \
  "internal/apps/ledger/planted_cache.go" <<'GO'
package ledger

// PLANTED DEFECT — I-3. A cached balance is a written balance.
var cachedClosingBalance = map[int64]int64{}
GO

# ---------------------------------------------------------------------------------------------
# THE CONTROL. A prover that only ever shows RED has proved the guard is noisy, not correct.
# ---------------------------------------------------------------------------------------------
say ""
say "--- CONTROL: the SAME scratch copy with NOTHING planted must come out GREEN"
CTRL="$(fresh_copy control)"
ctrl_out="$("$BIN" --root "$CTRL" 2>&1)"; ctrl_rc=$?
say "    -> exit $ctrl_rc"
printf '%s\n' "$ctrl_out" | LC_ALL=C grep -a '^CENSUS ledger-invariants — ' | LC_ALL=C sed 's/^/    /'
if [ "$ctrl_rc" -ne 0 ]; then
  say "    FAIL the guard refused an UNMODIFIED copy of nexus/ — it is over-broad, and every"
  say "         red above is therefore uninformative."
  printf '%s\n' "$ctrl_out" | LC_ALL=C grep -a '^  \[' | LC_ALL=C sed 's/^/        /'
  fails=1
fi
rm -rf "$CTRL"

say ""
if [ "$fails" -ne 0 ]; then
  say "DRIVE-RED: FAILED."
  exit 1
fi
say "DRIVE-RED: PASS — eight violation classes each planted in a scratch copy of the real"
say "DRIVE-RED:   nexus/ tree, each refused with the expected class; the unmodified control"
say "DRIVE-RED:   passed. The guard separates the defect from its absence over the REAL"
say "DRIVE-RED:   population, not only over synthetic fixtures."
exit 0
