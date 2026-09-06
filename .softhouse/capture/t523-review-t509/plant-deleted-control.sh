#!/usr/bin/env bash
# T523 item 4 — DOES THE drive-red REPAIR ACTUALLY BITE?
#
# T509's claim: plants used to be matched by `grep [CLASS]` ANYWHERE in the transcript, so
# on a tree that already carries I3-FIELD-WRITE and I3-SQL-BALANCE findings, PLANTS 1 and 5
# would have "passed" WITH THEIR PLANTED FILE DELETED. The repair matches at the planted path.
#
# This runs the guard over an UNPLANTED copy of nexus/ and evaluates BOTH match forms, for
# every one of the twelve plant paths. The OLD form passing on a deleted plant is the defect;
# the NEW form failing on a deleted plant is the repair.
#
# Usage: plant-deleted-control.sh <ledgerguard-binary> <nexus-dir> <scratch-dir>
set -u -o pipefail
BIN="$1"; NEXUS="$2"; SCR="$3"
mkdir -p "$SCR"
D="$SCR/unplanted"
rm -rf "$D"; mkdir -p "$D"
cp -R "$NEXUS/." "$D/"

OUT="$SCR/unplanted.out"
"$BIN" --root "$D" > "$OUT" 2>&1
printf 'guard on UNPLANTED copy: exit=%s\n\n' "$?"

check() {  # <n> <class> <relpath>
  local n="$1" want="$2" rel="$3" old new
  old="$(LC_ALL=C grep -ac "\[$want\]" "$OUT" || true)"; [ -n "$old" ] || old=0
  new="$(LC_ALL=C grep -ac "\[$want\] $rel:" "$OUT" || true)"; [ -n "$new" ] || new=0
  local oldv newv
  [ "$old" -gt 0 ] && oldv="PASS(WRONG)" || oldv="fail(correct)"
  [ "$new" -gt 0 ] && newv="PASS(WRONG)" || newv="fail(correct)"
  printf 'PLANT %-2s %-24s  OLD-form(class anywhere)=%-2s %-13s  NEW-form(class@path)=%-2s %s\n' \
    "$n" "$want" "$old" "$oldv" "$new" "$newv"
}

check 1  I3-FIELD-WRITE         internal/apps/ledger/planted_balance.go
check 2  I4-DML                 internal/apps/ledger/planted_update.go
check 3  I4-DML                 internal/apps/ledger/planted_delete.go
check 4  I6-HOLD-BALANCE        internal/apps/ledger/planted_hold.go
check 5  I3-SQL-BALANCE         internal/apps/ledger/planted_trialbalance.go
check 6  I4-BUILDER             internal/apps/ledger/planted_orm.go
check 7  OPAQUE-SQL             internal/apps/ledger/planted_dynamic.go
check 8  I3-PKG-STATE           internal/apps/ledger/planted_cache.go
check 9  I3-SQL-BALANCE-TABLE   internal/apps/ledger/planted_balance_table.go
check 10 I3-COMPOSITE-BALANCE   internal/apps/ledger/planted_composite.go
check 11 I3-FIELD-WRITE         internal/apps/ledger/planted_outstanding.go
check 12 OPAQUE-SQL             internal/apps/ledger/planted_wrapper.go
