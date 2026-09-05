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
# It also runs the CONTROL. A prover that only ever shows red proves the guard is noisy, not
# that it is right (P-50).
#
# TWO THINGS T509 CHANGED, AND THE FIRST ONE MATTERED IMMEDIATELY.
#
# 1. A PLANT NOW HAS TO FIRE **AT THE PLANTED PATH**. This script used to accept `grep [CLASS]`
#    anywhere in the transcript. That was sound only while the tree was clean. The tree is not
#    clean — it carries a known, argued finding set — so `I3-FIELD-WRITE` and `I3-SQL-BALANCE`
#    were already present in every run, and PLANTS 1 and 5 would have "passed" with their
#    planted file deleted. A check that passes without its subject is not a check. Every plant
#    is now matched against `[CLASS] <planted path>`.
#
# 2. THE CONTROL IS BASELINE-EXACT, NOT GREEN. "The unmodified copy must exit 0" cannot hold
#    while the four `loanproduct` sites stay refused on a recorded decision (T502 / T505 /
#    T514), and pretending otherwise would have meant either deleting the control or clearing a
#    finding to satisfy it. Instead the control asserts the finding set is EXACTLY the pinned
#    baseline in `.softhouse/guards/ledger-invariants.baseline` — which fails in BOTH
#    directions. A new (class, file) pair fails it; a baseline pair that DISAPPEARS also fails
#    it, so a rename that silences a known violation is caught rather than rewarded.
#
# Usage:  bash .softhouse/guards/drive-red-ledger-invariants.sh
# Exit:   0 every class drove red at its own planted path and the control matched the baseline
#         exactly; 1 otherwise; 2 unusable.

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
  # MATCHED AT THE PLANTED PATH, NOT ANYWHERE. See note 1 in this file's header: the tree
  # carries a known finding set, so `[$want]` on its own is satisfied by findings this plant
  # had nothing to do with, and PLANTS 1 and 5 would pass with their planted file deleted.
  hits="$(printf '%s\n' "$out" | LC_ALL=C grep -ac "\[$want\] $relpath:" || true)"
  [ -n "$hits" ] || hits=0
  if [ "$rc" -eq 0 ]; then
    say "    FAIL the guard PASSED a tree carrying the planted defect"
    fails=1
  elif [ "$hits" -eq 0 ]; then
    say "    FAIL the guard refused, but class $want never fired AT $relpath"
    say "         (it failed for a different reason, or on a pre-existing finding elsewhere)"
    printf '%s\n' "$out" | LC_ALL=C grep -a '^  \[' | LC_ALL=C sed 's/^/        /'
    fails=1
  else
    printf '%s\n' "$out" | LC_ALL=C grep -a "\[$want\] $relpath:" | LC_ALL=C sed 's/^  /    FIRED /'
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
# T509's four new plants. EVERY ONE OF THESE PASSED THE GUARD BEFORE THE REPAIR, verified by
# building the pre-T509 guard from git and running it over the identical scratch tree.
# ---------------------------------------------------------------------------------------------

run_plant "a stored balance TABLE whose columns never say 'balance' (I-3)" 9 I3-SQL-BALANCE-TABLE \
  "internal/apps/ledger/planted_balance_table.go" <<'GO'
package ledger

// PLANTED DEFECT — I-3, the shape T503's B-2 found live in workingcapital: the guard tested
// COLUMN names, and none of m_wc_loan_balance's thirteen columns carries the string "balance".
// The TABLE name does. A check reading the wrong string still returns an answer.
const plantedBalanceTableSQL = "INSERT INTO m_wc_loan_balance (wc_loan_id, principal, principal_paid, fee, penalty) VALUES ($1,$2,$3,$4,$5) ON CONFLICT (wc_loan_id) DO UPDATE SET principal = excluded.principal"
GO

run_plant "a balance written by an ALLOCATED composite literal (I-3)" 10 I3-COMPOSITE-BALANCE \
  "internal/apps/ledger/planted_composite.go" <<'GO'
package ledger

// PLANTED DEFECT — I-3 in the form CANNOT-CATCH item 8 used to RECOMMEND. writeTarget was
// applied to assignments only, so moving the identical write into a constructor silenced the
// finding while storing the identical value (T502 B-2, T505 §6: six such writes, one four
// lines from a refused site).
type plantedSegment struct {
	OutstandingLoanBalance int64
	Rounding               int
}

func newPlantedSegment(openingMinor int64) *plantedSegment {
	return &plantedSegment{OutstandingLoanBalance: openingMinor, Rounding: 4}
}
GO

run_plant "a balance spelled 'outstanding' rather than 'balance' (I-3)" 11 I3-FIELD-WRITE \
  "internal/apps/ledger/planted_outstanding.go" <<'GO'
package ledger

// PLANTED DEFECT — I-3, the twin that shipped GREEN. loanschedule/emi.go:1720,:1726 is the
// same roll-forward as the four refused loanproduct sites, citing the same oracle method in
// its own comment, on a field whose own comment calls it "the balance carried INTO this
// segment" — and it passed because the identifier is spelled outstandingMinor.
type plantedSeg struct{ outstandingMinor, disbursedMinor int64 }

func plantedRollForward(s *plantedSeg, prev plantedSeg, dueMinor int64) {
	s.outstandingMinor = prev.outstandingMinor + prev.disbursedMinor - dueMinor
}
GO

run_plant "an INSERT with a spliced column list, routed through a tree-local wrapper" 12 OPAQUE-SQL \
  "internal/apps/ledger/planted_wrapper.go" <<'GO'
package ledger

// PLANTED DEFECT — T506's F-6 scenario, executed. postgres.InsertReturningInt64 is a MUTATING
// wrapper the exec-family regex never named, reaching the database through Query. Before the
// repair this produced NO finding of any class: no OPAQUE-SQL (the call name is unrecognised)
// and no readable literal to classify. The bar would have gone green with a balance column
// written on every transaction.
type plantedDB interface {
	Query(ctx any, sql string, args ...any) error
}

func plantedQueryRows(ctx any, db plantedDB, sql string, args []any) error {
	return db.Query(ctx, sql, args...)
}

func plantedInsertReturningInt64(ctx any, db plantedDB, sql string, args ...any) (int64, error) {
	return 0, plantedQueryRows(ctx, db, sql, args)
}

const plantedCols = "savings_account_id, account_balance_derived"

func plantedSave(ctx any, db plantedDB, id, balanceMinor int64) (int64, error) {
	return plantedInsertReturningInt64(ctx, db,
		"INSERT INTO m_savings_account_summary ("+plantedCols+") VALUES ($1,$2) RETURNING id",
		id, balanceMinor)
}
GO

# ---------------------------------------------------------------------------------------------
# CONTROL A — THE COMMITTED CLEAN FIXTURE. This is the surviving TRUE-GREEN polarity: a tree of
# the CORRECT forms of every construct planted above, which must come out clean. Without it, a
# guard that refuses everything would pass every plant and the whole file would prove nothing
# (P-50). It is a fixture the guard's authors own, not a moving target — see the note in
# ledgerguard/testdata/cleantree/README.md for why the real tree cannot play this role.
# ---------------------------------------------------------------------------------------------
say ""
say "--- CONTROL A: the committed CLEAN FIXTURE must come out GREEN"
FIXTURE="$GUARD_SRC/testdata/cleantree"
if [ ! -d "$FIXTURE" ]; then
  say "    FAIL the clean fixture is MISSING at $FIXTURE. The GREEN polarity did NOT run, and a"
  say "         prover that only shows RED proves the guard noisy, not correct. NOT a pass."
  fails=1
else
  fx_out="$("$BIN" --root "$FIXTURE" 2>&1)"; fx_rc=$?
  say "    -> exit $fx_rc"
  printf '%s\n' "$fx_out" | LC_ALL=C grep -a '^CENSUS ledger-invariants — ' | LC_ALL=C sed 's/^/    /'
  if [ "$fx_rc" -ne 0 ]; then
    say "    FAIL the guard refused the CLEAN FIXTURE — it is over-broad, and every red above is"
    say "         therefore uninformative."
    printf '%s\n' "$fx_out" | LC_ALL=C grep -a '^  \[' | LC_ALL=C sed 's/^/        /'
    fails=1
  fi
fi

# ---------------------------------------------------------------------------------------------
# CONTROL B — THE REAL TREE MUST MATCH ITS PINNED BASELINE **EXACTLY**, in both directions.
#
# "The unmodified copy must exit 0" was the old control and it cannot hold: the four
# `loanproduct` sites stay refused on a recorded decision (T502 / T505 / T514). Satisfying it
# would have meant deleting the control or clearing a finding to please it — both worse than the
# red. So the claim is narrowed to the one that is true and still load-bearing: the finding set
# is EXACTLY what `.softhouse/guards/ledger-invariants.baseline` records.
#
# A LISTED PAIR THAT DISAPPEARS FAILS THIS TOO, and that is the half worth having: it is what
# catches a rename that turns the bar green while changing nothing.
# ---------------------------------------------------------------------------------------------
say ""
say "--- CONTROL B: the real nexus/ tree must match its PINNED BASELINE exactly (both directions)"
BASELINE="$REPO_ROOT/.softhouse/guards/ledger-invariants.baseline"
if [ ! -f "$BASELINE" ]; then
  say "    FAIL the baseline is MISSING at $BASELINE. Without it this control asserts nothing,"
  say "         and 'no baseline' must never read as 'baseline satisfied'. NOT a pass."
  fails=1
else
  CTRL="$(fresh_copy control)"
  ctrl_out="$("$BIN" --root "$CTRL" 2>&1)"; ctrl_rc=$?
  say "    -> exit $ctrl_rc (a non-zero exit here is EXPECTED: the tree has a known finding set)"
  printf '%s\n' "$ctrl_out" | LC_ALL=C grep -a '^CENSUS ledger-invariants — ' | LC_ALL=C sed 's/^/    /'
  printf '%s\n' "$ctrl_out" \
    | LC_ALL=C grep -a '^  \[' \
    | LC_ALL=C sed -E 's/^  \[([A-Z0-9-]+)\] ([^:]+):.*/\1	\2/' \
    | LC_ALL=C sort -u > "$WORK/observed.tsv"
  LC_ALL=C grep -av '^#' "$BASELINE" | LC_ALL=C grep -av '^[[:space:]]*$' \
    | LC_ALL=C sort -u > "$WORK/expected.tsv"
  # `comm` reads both files to completion; no `head`, no `grep -q`, so this adds no member of
  # the P-57 rule-1 EPIPE family under `set -o pipefail`.
  new_pairs="$(LC_ALL=C comm -13 "$WORK/expected.tsv" "$WORK/observed.tsv")"
  gone_pairs="$(LC_ALL=C comm -23 "$WORK/expected.tsv" "$WORK/observed.tsv")"
  if [ -n "$new_pairs" ]; then
    say "    FAIL a (class, file) pair appeared that the baseline does not record. A violation"
    say "         entered a file that had none. Fix it, or record it in the baseline with the"
    say "         argument for why it stands:"
    printf '%s\n' "$new_pairs" | LC_ALL=C sed 's/^/        + /'
    fails=1
  fi
  if [ -n "$gone_pairs" ]; then
    say "    FAIL a baseline (class, file) pair DISAPPEARED. A known violation was silenced. If"
    say "         it was genuinely repaired, remove its row from the baseline in the same commit"
    say "         so the change is visible in the diff — never by the finding quietly vanishing:"
    printf '%s\n' "$gone_pairs" | LC_ALL=C sed 's/^/        - /'
    fails=1
  fi
  if [ -z "$new_pairs" ] && [ -z "$gone_pairs" ]; then
    say "    baseline MATCHED exactly: $(LC_ALL=C grep -ac . "$WORK/expected.tsv") (class, file) pair(s), none added, none silenced"
  fi
  rm -rf "$CTRL"
fi

say ""
if [ "$fails" -ne 0 ]; then
  say "DRIVE-RED: FAILED."
  exit 1
fi
say "DRIVE-RED: PASS — twelve violation classes each planted in a scratch copy of the real"
say "DRIVE-RED:   nexus/ tree, each refused with the expected class AT ITS OWN PLANTED PATH;"
say "DRIVE-RED:   the committed clean fixture passed; and the real tree matched its pinned"
say "DRIVE-RED:   baseline exactly, with no pair added and none silenced. The guard separates"
say "DRIVE-RED:   the defect from its absence over the REAL population, not only over synthetic"
say "DRIVE-RED:   fixtures. NOTE: the tree is RED and that is a recorded decision, not neglect —"
str="DRIVE-RED:   read .softhouse/guards/ledger-invariants.baseline before quoting this as clean."
say "$str"
exit 0
