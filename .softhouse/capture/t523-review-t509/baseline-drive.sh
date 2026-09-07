#!/usr/bin/env bash
# T523 item 6 — DRIVE THE BASELINE IN BOTH DIRECTIONS, THEN ATTACK IT AS AN EXEMPTION CHANNEL.
#
# This reimplements drive-red CONTROL B's comparison EXACTLY (same sed, same sort -u, same comm)
# over a scratch copy of nexus/, so each scenario can be driven without editing the repository.
#
#   D1  a NEW (class, file) pair in a file the baseline does not list      -> must FAIL
#   D2  a baseline pair that DISAPPEARS                                    -> must FAIL
#   B1  an EXTRA finding in a file the baseline ALREADY lists              -> ?
#   B2  regenerating the baseline from the observed set after B1           -> ?
#
# Usage: baseline-drive.sh <ledgerguard-binary> <nexus-dir> <baseline-file> <scratch-dir>
set -u -o pipefail
BIN="$1"; NEXUS="$2"; BASE="$3"; SCR="$4"
mkdir -p "$SCR"

observe() { # <tree> -> pairs on stdout
  "$BIN" --root "$1" 2>&1 \
    | LC_ALL=C grep -a '^  \[' \
    | LC_ALL=C sed -E 's/^  \[([A-Z0-9-]+)\] ([^:]+):.*/\1\t\2/' \
    | LC_ALL=C sort -u
}
expected() { # <baseline-file>
  LC_ALL=C grep -av '^#' "$1" | LC_ALL=C grep -av '^[[:space:]]*$' | LC_ALL=C sort -u
}
compare() { # <label> <tree> <baseline-file>
  local label="$1" tree="$2" base="$3"
  observe "$tree" > "$SCR/observed.tsv"
  expected "$base" > "$SCR/expected.tsv"
  local nw gn n
  nw="$(LC_ALL=C comm -13 "$SCR/expected.tsv" "$SCR/observed.tsv")"
  gn="$(LC_ALL=C comm -23 "$SCR/expected.tsv" "$SCR/observed.tsv")"
  n="$("$BIN" --root "$tree" 2>&1 | LC_ALL=C grep -ac '^  \[' || true)"
  if [ -n "$nw" ] || [ -n "$gn" ]; then
    printf '%-46s CONTROL-B=FAIL  findings=%s\n' "$label" "$n"
    [ -n "$nw" ] && printf '%s\n' "$nw" | sed 's/^/        + /'
    [ -n "$gn" ] && printf '%s\n' "$gn" | sed 's/^/        - /'
  else
    printf '%-46s CONTROL-B=PASS  findings=%s\n' "$label" "$n"
  fi
}

mk() { local d="$SCR/$1"; rm -rf "$d"; mkdir -p "$d"; cp -R "$NEXUS/." "$d/"; printf '%s' "$d"; }

# --- reference ------------------------------------------------------------------------------
T0="$(mk t0)"
compare "REF   unmodified tree vs committed baseline" "$T0" "$BASE"

# --- D1: a new pair in a file the baseline does not list --------------------------------------
T1="$(mk t1)"
cat > "$T1/internal/apps/ledger/t523_newpair.go" <<'GO'
package ledger

// T523 probe: a balance WRITTEN, in a file the baseline has never listed.
type t523Acct struct{ BalanceMinor int64 }

func t523Write(a *t523Acct, v int64) { a.BalanceMinor = v }
GO
compare "D1    new pair in an unlisted file" "$T1" "$BASE"

# --- D2: a baseline pair disappears -----------------------------------------------------------
# The cheapest real-world shape of "a known violation was silenced": rename the field so the
# name-based detector stops seeing it. Nothing about the write path changes.
T2="$(mk t2)"
LC_ALL=C sed -i 's/BalanceMinor/AmtMinor/g; s/OutstandingMinor/AmtMinor/g' "$T2/internal/apps/loanschedule/emi.go"
compare "D2    a baseline pair silenced by a rename" "$T2" "$BASE"

# --- B1: an EXTRA finding inside a file the baseline ALREADY lists -----------------------------
T3="$(mk t3)"
cat >> "$T3/internal/apps/loan/charge.go" <<'GO'

// T523 probe: a BRAND NEW balance write, appended to a file the baseline already lists.
type t523NewBalance struct{ BalanceMinor int64 }

func t523NewWrite(b *t523NewBalance, v int64) { b.BalanceMinor = v }
GO
compare "B1    extra finding in an ALREADY-LISTED file" "$T3" "$BASE"

# --- B2: regenerate the baseline from the observed set, after B1 -------------------------------
observe "$T3" > "$SCR/regenerated.baseline"
compare "B2    same tree vs a REGENERATED baseline" "$T3" "$SCR/regenerated.baseline"
printf '      regenerated baseline row count: %s (committed: %s)\n' \
  "$(LC_ALL=C grep -ac . "$SCR/regenerated.baseline")" \
  "$(expected "$BASE" | LC_ALL=C grep -ac .)"
