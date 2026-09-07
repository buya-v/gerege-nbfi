#!/usr/bin/env bash
# T523 item 6, the granularity question — THE BASELINE PINS (class, file) PAIRS, NOT COUNTS.
#
# D1/D2 confirmed the two directions T509 claims. This probe measures what falls BETWEEN them:
# a change that alters the number of findings inside a file the baseline already lists, in
# either direction. If those pass, the pair-level baseline is blind to both a fresh violation
# and a partial silencing, and neither leaves any trace in the baseline's diff.
#
# Usage: baseline-partial.sh <ledgerguard-binary> <nexus-dir> <baseline-file> <scratch-dir>
set -u -o pipefail
BIN="$1"; NEXUS="$2"; BASE="$3"; SCR="$4"; mkdir -p "$SCR"

observe() {
  "$BIN" --root "$1" 2>&1 | LC_ALL=C grep -a '^  \[' \
    | LC_ALL=C sed -E 's/^  \[([A-Z0-9-]+)\] ([^:]+):.*/\1\t\2/' | LC_ALL=C sort -u
}
expected() { LC_ALL=C grep -av '^#' "$1" | LC_ALL=C grep -av '^[[:space:]]*$' | LC_ALL=C sort -u; }

compare() {
  local label="$1" tree="$2"
  observe "$tree" > "$SCR/o.tsv"; expected "$BASE" > "$SCR/e.tsv"
  local nw gn n
  nw="$(LC_ALL=C comm -13 "$SCR/e.tsv" "$SCR/o.tsv")"
  gn="$(LC_ALL=C comm -23 "$SCR/e.tsv" "$SCR/o.tsv")"
  n="$("$BIN" --root "$tree" 2>&1 | LC_ALL=C grep -ac '^  \[' || true)"
  if [ -n "$nw" ] || [ -n "$gn" ]; then
    printf '%-56s CONTROL-B=FAIL  findings=%s\n' "$label" "$n"
    [ -n "$nw" ] && printf '%s\n' "$nw" | sed 's/^/        + /'
    [ -n "$gn" ] && printf '%s\n' "$gn" | sed 's/^/        - /'
  else
    printf '%-56s CONTROL-B=PASS  findings=%s\n' "$label" "$n"
  fi
}

mk() { local d="$SCR/$1"; rm -rf "$d"; mkdir -p "$d"; cp -R "$NEXUS/." "$d/"; printf '%s' "$d"; }

T="$(mk ref)"; compare "REF   unmodified" "$T"

# P1 — PARTIAL SILENCING. emi.go carries exactly two findings (:1720, :1726). Rename ONE of
#      them out of the regex's reach. The pair survives, so the baseline sees nothing.
T="$(mk p1)"
LC_ALL=C sed -i '1720s/outstandingMinor =/amtMinor =/' "$T/internal/apps/loanschedule/emi.go"
compare "P1    ONE of emi.go's two findings renamed away" "$T"

# P2 — BULK PARTIAL SILENCING. loan/charge.go carries 11 findings. Silence 10 of them,
#      leaving one so the pair survives.
T="$(mk p2)"
LC_ALL=C sed -i '1,240s/\.OutstandingMinor =/.AmtMinor =/g; 1,240s/\.BalanceMinor =/.AmtMinor =/g' \
  "$T/internal/apps/loan/charge.go"
compare "P2    charge.go findings mass-renamed (pair kept)" "$T"

# P3 — FRESH VIOLATION in an already-listed file (B1 restated, for the record).
T="$(mk p3)"
cat >> "$T/internal/apps/loan/charge.go" <<'GO'

type t523Fresh struct{ BalanceMinor int64 }

func t523FreshWrite(f *t523Fresh, v int64) { f.BalanceMinor = v }
GO
compare "P3    fresh balance write in an already-listed file" "$T"

# P4 — FRESH VIOLATION moved INTO an already-listed file from elsewhere: the git-mv shape
#      T505 MAJOR-1 measured defeating the persistence-surface heuristic, applied here.
T="$(mk p4)"
cat >> "$T/internal/apps/investor/postgres.go" <<'GO'

// A stored, authoritative savings balance written straight through the driver.
func t523WriteSavingsBalance(ctx interface{ Done() <-chan struct{} }, db interface {
	Exec(ctx interface{ Done() <-chan struct{} }, sql string, args ...any) error
}, id, balanceMinor int64) error {
	return db.Exec(ctx, `UPDATE m_savings_account SET account_balance_derived = $1 WHERE id = $2`,
		balanceMinor, id)
}
GO
compare "P4    UPDATE of a balance column into a listed file" "$T"
