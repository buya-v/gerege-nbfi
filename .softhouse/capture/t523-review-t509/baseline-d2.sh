#!/usr/bin/env bash
# T523 item 6, direction 2 — A BASELINE PAIR THAT DISAPPEARS MUST FAIL CONTROL B.
#
# The first attempt at this probe renamed `OutstandingMinor`; the real field in emi.go is
# `outstandingMinor`, lowercase, so nothing changed and the probe passed for the wrong reason.
# Recording that here rather than deleting it: a probe that silently matched nothing is exactly
# the defect this review is grading elsewhere. This is the corrected run.
#
# Usage: baseline-d2.sh <ledgerguard-binary> <nexus-dir> <baseline-file> <scratch-dir>
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
    printf '%-52s CONTROL-B=FAIL  findings=%s\n' "$label" "$n"
    [ -n "$nw" ] && printf '%s\n' "$nw" | sed 's/^/        + /'
    [ -n "$gn" ] && printf '%s\n' "$gn" | sed 's/^/        - /'
  else
    printf '%-52s CONTROL-B=PASS  findings=%s\n' "$label" "$n"
  fi
}

mk() { local d="$SCR/$1"; rm -rf "$d"; mkdir -p "$d"; cp -R "$NEXUS/." "$d/"; printf '%s' "$d"; }

# D2a — rename the field the guard sees, in the two emi.go sites. The WRITE PATH IS UNCHANGED;
#        only the spelling moves out of balanceSynonymRe's reach.
T="$(mk d2a)"
LC_ALL=C sed -i 's/outstandingMinor/amtMinor/g' "$T/internal/apps/loanschedule/emi.go"
compare "D2a  emi.go balance field renamed out of the regex" "$T"

# D2b — the same move applied to a whole baseline file: rename investor's balance fields.
T="$(mk d2b)"
LC_ALL=C sed -i 's/[Bb]alance/Amt/g; s/[Oo]utstanding/Amt/g' "$T/internal/apps/investor/postgres.go"
compare "D2b  investor/postgres.go renamed wholesale" "$T"
