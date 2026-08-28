#!/usr/bin/env bash
# t379-third-status-drive.sh -- T379's INDEPENDENT attack on T371's F2 repair.
#
#   bash .softhouse/reviews/t379-review-t371/instruments/t379-third-status-drive.sh [REF]
#
# T371 repaired `git grep`'s DISCARDED EXIT STATUS at the SEARCH step. This drive asks the
# question the brief told me to ask: IS THERE A THIRD STATUS THE INSTRUMENT STILL SWALLOWS?
# It looks one layer PAST the search, at the CLASSIFICATION step, and at the ENGINE the
# calibration actually exercises.
#
# The instrument under test is EXTRACTED FROM GIT on every run (P-22) and its sha256 printed,
# so this drive cannot grade a since-edited working copy.
#
# X  the ARCHIVE-predicate greps. On the rc=0 (HITS) path the repaired sel() runs
#      live=$(printf '%s' "$all" | grep -v -E "$ARCHIVE")
#      arch=$(printf '%s' "$all" | grep -c -E "$ARCHIVE")
#    and reads NEITHER status. If $ARCHIVE is not a valid ERE these greps exit 2, `live`
#    comes back EMPTY, and the instrument prints "LIVE: 0" over a selector that HIT.
#    That is T367's F2 verbatim -- a negative never measured -- moved one step downstream,
#    and it exits 0.
#
# Y  the calibration engine. Both calibrations use `git grep -F`. Fourteen of the sixteen
#    shipped selectors use `-E`. The header cites T238's `git grep -E` FABRICATION finding and
#    T232's `\b`-reads-as-literal-b finding as the reasons the calibration exists -- and NEITHER
#    is reachable through `-F`, which has no metacharacters to misinterpret. This arm shows the
#    calibration passing while the `-E` engine is demonstrably not what the author assumed.
#
# Z  stderr folded into the HIT set. `all=$(git grep "$@" -- .softhouse/ 2>&1)` folds stderr on
#    EVERY path, including rc=0. A warning line therefore counts as a hit and, unless it happens
#    to match $ARCHIVE, is listed as LIVE.
#
# It writes only under a mktemp dir. No network, no database.
set -uo pipefail
REF="${1:-softhouse/T371-t367-conditions}"
ROOT=$(git rev-parse --show-toplevel) || exit 2
cd "$ROOT" || exit 2
SUT='.softhouse/capture/t363-oracle-baseline/instruments/casualty-sweep.sh'
W=$(mktemp -d "${TMPDIR:-/tmp}/t379-drive-XXXXXX") || exit 2
trap 'rm -rf "$W"' EXIT

echo "=================================================================="
echo "T379 THIRD-STATUS DRIVE -- attacking T371's F2 repair"
echo "repo: $(git rev-parse --short HEAD)   ref under test: $REF ($(git rev-parse --short "$REF"))"
echo "date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "=================================================================="

git show "$REF:$SUT" > "$W/AFTER.sh" || { echo "cannot extract $REF:$SUT"; exit 2; }
printf 'AFTER sha256: %s\n' "$(shasum -a 256 "$W/AFTER.sh" | awk '{print $1}')"

# A selector that GENUINELY HITS, so we are on the rc=0 path where the ARCHIVE greps run.
HITTER='CASUALTY SWEEP for the T352'

mkvariant() { # mkvariant <src> <selector-args-literal> <dst>
  awk -v s="$2" '/^# ---- S1\.\.S3/ { print "sel \"TEST-SELECTOR\" " s } { print }' "$1" \
    | sed 's/^sel "S/#sel "S/' > "$3"
}
run() { # run <label> <script>
  local label="$1" script="$2" out rc
  out=$(bash "$script" 2>&1); rc=$?
  printf '\n---------- %s\n' "$label"
  printf '%s\n' "$out" | grep -E 'TEST-SELECTOR|DID NOT RUN|MEASURED ZERO|hits total|SWEEP ABORT|SWEEP-RESULT' \
    | sed 's/^/    /' | head -12
  printf '    EXIT=%s\n' "$rc"
}

echo
echo "########## X  THE CLASSIFICATION STEP -- a status the repair still discards"
mkvariant "$W/AFTER.sh" "-n -F '$HITTER'" "$W/x-control.sh"
run "X1-control-VALID-archive-predicate  (expect hits>0, LIVE>0)" "$W/x-control.sh"

# Break ONLY the ARCHIVE predicate. Everything else is the shipped instrument.
sed "s|^ARCHIVE='(.*'$|ARCHIVE='(unterminated['|" "$W/x-control.sh" > "$W/x-broken.sh"
printf '\n    ARCHIVE line as driven: %s\n' "$(grep -m1 '^ARCHIVE=' "$W/x-broken.sh")"
run "X2-MALFORMED-archive-predicate      (a hit, reported as LIVE 0, exit 0)" "$W/x-broken.sh"
echo
echo "    ^^ If X2 prints a nonzero 'hits total' with 'LIVE: 0' and EXIT=0 while X1 printed a"
echo "       LIVE list, the instrument has emitted a NEGATIVE IT NEVER MEASURED -- F2's exact"
echo "       shape, at the classification step rather than the search step, and the exit"
echo "       contract calls it 0 = 'every selector RAN'."

echo
echo "########## Y  THE CALIBRATION ENGINE -- -F is calibrated, -E is used"
printf '    calibration invocations in the shipped instrument:\n'
grep -n 'git grep' "$W/AFTER.sh" | grep -i calib | sed 's/^/      /'
grep -n 'n=\$(git grep' "$W/AFTER.sh" | sed 's/^/      /'
printf '    shipped selectors by engine flag:  -F %s   -E %s\n' \
  "$(grep -c '^sel .* -F ' "$W/AFTER.sh")" "$(grep -c '^sel .* -E ' "$W/AFTER.sh")"
printf '    T232/T238 hazards are -E hazards. Demonstrated against THIS host:\n'
git grep -c -E 'bmainb'   -- "$SUT" >/dev/null 2>&1; printf '      git grep -E %-14s rc=%s\n' "'bmainb'" "$?"
printf '      git grep -E %-14s hits=%s\n' "'\\\\bmain\\\\b'" "$(git grep -c -E '\bmain\b' -- .softhouse/ 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')"
printf '      git grep -E %-14s hits=%s   <- if these two agree, -E is reading \\\\b as literal b\n' "'bmainb'" "$(git grep -c -E 'bmainb' -- .softhouse/ 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')"
printf '      git grep -F %-14s hits=%s   <- what the calibration actually exercises\n' "'main'" "$(git grep -c -F 'main' -- "$SUT" 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')"

echo
echo "########## Z  stderr folded into the HIT set on the rc=0 path"
printf '    the fold: %s\n' "$(grep -n 'all=\$(git grep' "$W/AFTER.sh" | sed 's/^ *//')"
printf '    it is unconditional -- rc is read AFTER the fold, so a warning on a HITTING\n'
printf '    selector is counted by `grep -c .` as a hit and listed as LIVE.\n'

echo
echo "=================================================================="
echo "END OF T379 THIRD-STATUS DRIVE"
echo "=================================================================="
