#!/usr/bin/env bash
# T241 — P-58: run the G-8 scope census with TWO NAMED grep engines and report BOTH figures.
#
# ENGINE 1: `git grep -n -P`        (PCRE, sound and available here)
# ENGINE 2: `/usr/bin/grep -n -E`   (BSD grep, ERE) over a `sed`-extracted line range
# ENGINE 3 (the primary, for reference): python3 `re`, in scope_table_t241.py
#
# P-75 compliance: NO bare `grep` (the bundled ugrep 7.5.0 with six silently-prepended
# --exclude-dir flags, 33 % measured recall) and NO `rg` (no binary; `rg P F | head` exits 0)
# appears anywhere in this script. Both engines are named by ABSOLUTE PATH or by `git grep`.
#
# P-72: every net is calibrated on a known POSITIVE and a known NEGATIVE first, on BOTH engines,
# and the negative is NOT a substring of the positive. A net that does not discriminate on both
# engines aborts the run.
#
# Line counts, not claim-unit counts: a second engine cannot reproduce python's sentence splitting,
# so the cross-check is at LINE granularity, which is what a grep engine can honestly report.
# `git grep -P` counts MATCHING LINES in the range; `/usr/bin/grep -c -E` counts matching lines in
# the same `sed`-extracted range. The two are therefore directly comparable.

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
GATES=.softhouse/gates.md
# calibration scratch MUST live inside the worktree: `git grep --no-index` refuses a
# path outside the directory tree (measured by T241, exit 128 "outside the directory tree").
TMP=.t241-calibration-scratch
mkdir -p "$TMP"
trap 'rm -rf "$TMP"' EXIT

# --- section boundaries, recomputed here rather than hard-coded (P-69: line numbers move) ---
LIVE_START=$(git grep -n -P '^## G-8 — TWO phenomena' -- "$GATES" | cut -d: -f2)
NOTICE_START=$(git grep -n -P '^## G-8-NOTICE' -- "$GATES" | cut -d: -f2)
LIVE_END=$(( $(git grep -n -P '^## G-\d' -- "$GATES" | cut -d: -f2 \
             | /usr/bin/awk -v s="$LIVE_START" '$1>s {print $1; exit}') - 1 ))
NOTICE_END=$(( $(git grep -n -P '^## G-\d' -- "$GATES" | cut -d: -f2 \
               | /usr/bin/awk -v s="$NOTICE_START" '$1>s {print $1; exit}') - 1 ))

echo "COMMIT MEASURED AT: $(git rev-parse HEAD)   (P-69)"
echo "LIVE G-8 section     : lines ${LIVE_START}..${LIVE_END}"
echo "G-8-NOTICE block     : lines ${NOTICE_START}..${NOTICE_END}"
echo

# --- the nets. PCRE and ERE forms of the same concept, kept in parallel arrays. ---
NAMES=(
  'R1  largest residual'
  'R2  largest failing principal/disbursement'
  'R3  MNT money figure'
  'R5  total-interest / n.E+B identity'
  'R10 the superseded MNT 10.01 record'
)
PCRES=(
  'largest\s+(unamortized\s+)?residual'
  'largest\s+failing\s+(principal|disbursement)'
  'MNT\s*[\d,]+\.\d\d'
  'n\s*[·*]\s*E\s*\+\s*B|TOTAL\s+INTEREST|totalInterestAmount'
  'MNT\s*10\.01'
)
ERES=(
  'largest[[:space:]]+(unamortized[[:space:]]+)?residual'
  'largest[[:space:]]+failing[[:space:]]+(principal|disbursement)'
  'MNT[[:space:]]*[0-9,]+\.[0-9][0-9]'
  'n[[:space:]]*[·*][[:space:]]*E[[:space:]]*\+[[:space:]]*B|TOTAL[[:space:]]+INTEREST|totalInterestAmount'
  'MNT[[:space:]]*10\.01'
)
# P-72 calibration strings, per net. POS must match, NEG must not, on BOTH engines.
POSES=(
  'the largest unamortized residual is MNT 30.00 at n = 3000'
  'the largest failing disbursement on record is MNT 44.99'
  'a residual of MNT 44.99 was observed'
  'TOTAL INTEREST = n·E + B for any unrescued cell'
  'the largest unamortized residual is MNT 10.01 at n = 3000'
)
NEGES=(
  'a residual was observed and it was not the biggest one anybody has seen'
  'a disbursement failed to amortize, which nobody had asked about before'
  'a figure of 44.99 tugrik, written without the currency code'
  'total repayment equals the instalment times the term plus the disbursement'
  'the residual is MNT 10.02, one minor unit above the superseded record'
)

# --------------------------------------------------------------------------------------
# FAIL-CLOSED COUNTING (T238's invariant: an instrument must not be able to emit a
# NEGATIVE IT DID NOT MEASURE).
#
# `grep -c` and `git grep -c` exit 1 for "ran fine, zero matches" and >=2 for "I broke".
# The obvious `|| echo 0` collapses those two onto the SAME printed zero, which is exactly
# the fail-open shape — and T241's first draft of this script had it on two lines, was
# caught by `.softhouse/capture/t238-failopen/instruments/50-failopen-lint.py` through
# `bash .softhouse/conformance.sh` (HARD guard, EXIT 2), and was repaired rather than
# pinned, as that guard's own advice instructs.
#
#   rc 0  -> a measurement, some hits        rc 1  -> a measurement, zero hits
#   rc >=2 -> NOT a measurement              -> ABORT 93, never print a number
# --------------------------------------------------------------------------------------
_die() { printf 'CENSUS ABORT (exit %s): %s\n' "$1" "$2" >&2; exit "$1"; }

count_git_file () {   # pattern, path  -> matching-line count, or ABORT
  local out rc
  out=$(git grep --no-index -c -P "$1" -- "$2" 2>&1); rc=$?
  case "$rc" in
    0) printf '%s\n' "${out##*:}" ;;
    1) printf '0\n' ;;
    *) _die 93 "git grep -P failed (exit $rc) on '$2': $out" ;;
  esac
}

count_bsd_file () {   # pattern, path  -> matching-line count, or ABORT
  local out rc
  out=$(/usr/bin/grep -c -E "$1" "$2" 2>&1); rc=$?
  case "$rc" in
    0) printf '%s\n' "$out" ;;
    1) printf '0\n' ;;
    *) _die 93 "/usr/bin/grep -E failed (exit $rc) on '$2': $out" ;;
  esac
}

echo "P-72 CALIBRATION — known POSITIVE and known NEGATIVE, on BOTH engines"
fail=0
for i in "${!NAMES[@]}"; do
  printf '%s\n' "${POSES[$i]}" > "$TMP/pos.txt"
  printf '%s\n' "${NEGES[$i]}" > "$TMP/neg.txt"
  gp=$(count_git_file "${PCRES[$i]}" "$TMP/pos.txt")
  gn=$(count_git_file "${PCRES[$i]}" "$TMP/neg.txt")
  bp=$(count_bsd_file "${ERES[$i]}"  "$TMP/pos.txt")
  bn=$(count_bsd_file "${ERES[$i]}"  "$TMP/neg.txt")
  verdict='DISCRIMINATES'
  if [ "$gp" -lt 1 ] || [ "$gn" -ne 0 ] || [ "$bp" -lt 1 ] || [ "$bn" -ne 0 ]; then
    verdict='*** DOES NOT DISCRIMINATE — NET IS VOID ***'; fail=1
  fi
  printf '  %-44s git -P pos=%s neg=%s | grep -E pos=%s neg=%s  %s\n' \
    "${NAMES[$i]}" "$gp" "$gn" "$bp" "$bn" "$verdict"
done
[ "$fail" -eq 0 ] || { echo "ABORTING: a net failed calibration (P-72)."; exit 1; }
echo

count_git () {   # pattern, from, to  -> matching lines in range, or ABORT (never a bare 0)
  local out rc
  out=$(git grep -n -P "$1" -- "$GATES" 2>&1); rc=$?
  case "$rc" in
    0) printf '%s\n' "$out" | cut -d: -f2 \
         | /usr/bin/awk -v a="$2" -v b="$3" '$1>=a && $1<=b' | /usr/bin/wc -l | tr -d ' ' ;;
    1) printf '0\n' ;;
    *) _die 93 "git grep -P failed (exit $rc) on $GATES: $out" ;;
  esac
}
count_bsd () {   # pattern, from, to  -> matching lines in range, or ABORT (never a bare 0)
  local slice out rc
  slice=$(/usr/bin/sed -n "$2,$3p" "$GATES") || _die 90 "sed could not read $GATES"
  [ -n "$slice" ] || _die 91 "line range $2..$3 of $GATES is EMPTY — a census over nothing (P-35)"
  out=$(printf '%s\n' "$slice" | /usr/bin/grep -c -E "$1" 2>&1); rc=$?
  case "$rc" in
    0) printf '%s\n' "$out" ;;
    1) printf '0\n' ;;
    *) _die 93 "/usr/bin/grep -E failed (exit $rc) on the $2..$3 slice: $out" ;;
  esac
}

echo "CENSUS — matching LINES, both engines"
for i in "${!NAMES[@]}"; do
  gl=$(count_git "${PCRES[$i]}" "$LIVE_START" "$LIVE_END")
  bl=$(count_bsd "${ERES[$i]}"  "$LIVE_START" "$LIVE_END")
  gn=$(count_git "${PCRES[$i]}" "$NOTICE_START" "$NOTICE_END")
  bn=$(count_bsd "${ERES[$i]}"  "$NOTICE_START" "$NOTICE_END")
  la=$([ "$gl" = "$bl" ] && echo AGREE || echo '*** DISAGREE ***')
  na=$([ "$gn" = "$bn" ] && echo AGREE || echo '*** DISAGREE ***')
  printf '  %-44s LIVE git-P=%-4s grepE=%-4s %-16s NOTICE git-P=%-3s grepE=%-3s %s\n' \
    "${NAMES[$i]}" "$gl" "$bl" "$la" "$gn" "$bn" "$na"
done
