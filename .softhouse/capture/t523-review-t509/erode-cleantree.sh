#!/usr/bin/env bash
# T523 item 3, residual — PARTIAL erosion of the negative control.
#
# m10 in mutate-cleantree.sh showed that FULLY gutting the three members is caught by the
# P-35 zero-population gates. This script asks the weaker, more realistic question: can a
# member keep enough population to clear P-35 while LOSING the specific near-boundary
# construct it was put there to protect? If so, the over-match check it carries stops
# running silently, and case (n)'s member list — which tests PRESENCE only — cannot say so.
#
# Usage: erode-cleantree.sh <ledgerguard-binary> <fixture-dir> <scratch-dir>
set -u -o pipefail
BIN="$1"; FIX="$2"; SCR="$3"
mkdir -p "$SCR"

erode() {
  local name="$1"; shift
  rm -rf "${SCR:?}/$name"; cp -r "$FIX" "$SCR/$name"
  "$@" "$SCR/$name"
  local out rc
  out="$("$BIN" --root "$SCR/$name" 2>&1)"; rc=$?
  local funcs
  funcs="$(printf '%s\n' "$out" | grep -a -oE 'inspected [0-9]+ Go files / [0-9]+ packages / [0-9]+ funcs' | head -1)"
  printf 'ERODE %-34s exit=%d   %s\n' "$name" "$rc" "$funcs"
}

# e1: delete the by-value composite-literal presenter (Render / RenderAll) — the ONLY
#     over-match check for I3-COMPOSITE-BALANCE's value/pointer line.
e1() { sed -i '/^func Render(/,/^}/d; /^func RenderAll(/,/^}/d' "$1/present/present.go"; }

# e2: delete OutstandingAfter — the ONLY lawful exercise of balanceSynonymRe (T509's own
#     addition). Losing it means nothing checks that "(?i)outstanding" stays off derived form.
e2() { sed -i '/^func OutstandingAfter(/,/^}/d' "$1/ledger/derive.go"; }

# e3: delete the balance-naming SELECT — the only proof a READ of a balance column is not
#     refused (the DEC-2 read/write line the guard's own note item 9 rests on).
e3() { sed -i '/^const readEntriesSQL = /,/ORDER BY id`$/d; /^func Read(/,/^}/d' "$1/store/store.go"; }

# e4: delete the lawful journal INSERT — the only proof appending to the journal is allowed.
e4() { sed -i '/^const appendEntrySQL = /,/VALUES (\$1,\$2,\$3,\$4,\$5,\$6,\$7)`$/d; /^func Append(/,/^}/d; /^func (r ctxHolder) Append(/,/^}/d' "$1/store/store.go"; }

# e5: delete AvailableAfterHold — the only GREEN exercise of holdFuncRe.
e5() { sed -i '/^func AvailableAfterHold(/,/^}/d' "$1/ledger/derive.go"; }

erode e1-drop-byvalue-composite   e1
erode e2-drop-outstanding-green   e2
erode e3-drop-balance-read-select e3
erode e4-drop-journal-insert      e4
erode e5-drop-hold-green          e5
