#!/usr/bin/env bash
# T523 item 3 — IS THE cleantree FIXTURE A REAL NEGATIVE CONTROL, OR VACUOUS?
#
# The fixture is asserted GREEN by selftest case (n). A control that cannot fail proves
# nothing. This script MUTATES a scratch copy of the fixture, one real violation at a time,
# and records whether the guard goes RED with the expected class. It never touches the
# committed fixture.
#
# Usage: mutate-cleantree.sh <ledgerguard-binary> <fixture-dir> <scratch-dir>
set -u -o pipefail

BIN="$1"; FIX="$2"; SCR="$3"
mkdir -p "$SCR"
rm -rf "${SCR:?}/base"
cp -r "$FIX" "$SCR/base"

rc0out="$("$BIN" --root "$SCR/base" 2>&1)"; rc0=$?
printf 'CONTROL  unmutated fixture copy            exit=%d\n' "$rc0"

run_mut() {
  local name="$1"; local fn="$2"
  rm -rf "${SCR:?}/$name"
  cp -r "$SCR/base" "$SCR/$name"
  "$fn" "$SCR/$name"
  local out rc cls
  out="$("$BIN" --root "$SCR/$name" 2>&1)"; rc=$?
  cls="$(printf '%s\n' "$out" | grep -a -oE '^  \[[A-Z0-9-]+\] [^ ]+' | sort -u | tr '\n' ' ')"
  printf 'MUT %-26s exit=%d  %s\n' "$name" "$rc" "$cls"
}

m1() { printf '\nfunc RenderPtr(id int64, legs []ledger.Leg) *View {\n\treturn &View{AccountID: id, BalanceMinor: ledger.Derive(legs)}\n}\n' >> "$1/present/present.go"; }
m2() { printf '\nfunc SetBal(v *View, x int64) {\n\tv.BalanceMinor = x\n}\n' >> "$1/present/present.go"; }
m3() { printf '\nconst updEntrySQL = `UPDATE acc_gl_journal_entry SET amount = $1 WHERE id = $2`\n\nfunc Upd(ctx context.Context, db DB, a, b int64) error {\n\treturn db.Exec(ctx, updEntrySQL, a, b)\n}\n' >> "$1/store/store.go"; }
m4() { printf '\nvar cachedBalance int64\n' >> "$1/ledger/derive.go"; }
m5() { printf '\nconst insBalSQL = `INSERT INTO m_trial_balance (account_id, balance) VALUES ($1,$2)`\n\nfunc InsBal(ctx context.Context, db DB, a, b int64) error {\n\treturn db.Exec(ctx, insBalSQL, a, b)\n}\n' >> "$1/store/store.go"; }
m6() { printf '\nfunc Splice(ctx context.Context, db DB, cols string, a int64) error {\n\treturn db.Exec(ctx, "INSERT INTO m_loan_transaction ("+cols+") VALUES ($1)", a)\n}\n' >> "$1/store/store.go"; }
m7() { printf '\ntype Acct struct{ BalanceMinor int64 }\n\nfunc ApplyHold(a *Acct, h int64) {\n\ta.BalanceMinor -= h\n}\n' >> "$1/ledger/derive.go"; }
m8() { printf '\ntype Loan struct{ OutstandingMinor int64 }\n\nfunc SetOutstanding(l *Loan, x int64) {\n\tl.OutstandingMinor = x\n}\n' >> "$1/ledger/derive.go"; }
m9() { printf '\nfunc Dyn(ctx context.Context, db DB, whole string, a int64) error {\n\treturn db.Exec(ctx, whole, a)\n}\n' >> "$1/store/store.go"; }

# GUTTING: each member kept present (so case (n)'s member list is satisfied) but emptied.
m10() {
  printf 'package ledger\n' > "$1/ledger/derive.go"
  printf 'package present\n' > "$1/present/present.go"
  printf 'package store\n' > "$1/store/store.go"
}

run_mut m1-alloc-composite       m1
run_mut m2-field-write           m2
run_mut m3-update-journal        m3
run_mut m4-pkg-state             m4
run_mut m5-sql-balance-insert    m5
run_mut m6-spliced-sql           m6
run_mut m7-hold-posted-balance   m7
run_mut m8-outstanding-field     m8
run_mut m9-opaque-arg            m9
run_mut m10-GUTTED-members       m10
