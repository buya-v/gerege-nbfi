#!/usr/bin/env bash
# T244 — RE-DERIVE the driver's engine table rather than transcribe it.
#
# Fixture (engine-fixture.txt), three lines:
#   1: x main y      <- the ONLY true \bmain\b hit
#   2: bmainb        <- a FALSE hit iff \b is read as a literal 'b'
#   3: HEAD          <- neither
#
# The driver's claim under test: `git grep -E` matches line 2 and MISSES line 1,
# i.e. it FABRICATES as well as loses. Existing lore (P-53/P-12) says recall loss only.
set -uo pipefail
SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" || exit 9
ROOT="$(cd "$SELF_DIR/../../.." && pwd)" || exit 9
cd "$ROOT" || exit 9
F=.softhouse/capture/t244-dec2-rev6/engine-fixture.txt
[ -f "$F" ] || { echo "FATAL: fixture missing"; exit 9; }

echo "root      : $ROOT"
echo "HEAD      : $(git rev-parse HEAD)"
echo "measured  : $(date -u +%Y-%m-%dT%H:%M:%SZ) UTC"
echo "fixture   : $F"
echo "--- fixture bytes ---"
cat -A "$F" | sed 's/^/    /'
echo

run() {   # run <label> <command...>
  local label="$1"; shift
  local out rc
  out="$("$@" 2>&1)"; rc=$?
  printf '%-28s rc=%d\n' "$label" "$rc"
  if [ -z "$out" ]; then printf '    (no output)\n'; else printf '%s\n' "$out" | sed 's/^/    /'; fi
  echo
}

echo "################ PART 1 — presence of each engine ################"
for e in ugrep ug rg grep ggrep pcre2grep; do
  printf '%-12s command -v -> %s\n' "$e" "$(command -v "$e" 2>/dev/null || echo '(nothing)')"
done
echo
echo "PATH entries searched:"
printf '%s\n' "$PATH" | tr ':' '\n' | sed 's/^/    /'
echo
echo "Is there an ugrep/rg BINARY anywhere on PATH? (type -a, resolving functions)"
echo "  type -a ugrep : $( { type -a ugrep; } 2>&1 | head -3 | tr '\n' ' ' )"
echo "  type -a rg    : $( { type -a rg; }    2>&1 | head -3 | tr '\n' ' ' )"
echo "  type -a grep  : $( { type -a grep; }  2>&1 | head -3 | tr '\n' ' ' )"
echo

echo "################ PART 2 — the \\bmain\\b discrimination test ################"
echo "TRUE POSITIVE = line 1 only.  FABRICATION = line 2 matched."
echo
run "git grep -E"            git grep -n -E --no-index '\bmain\b' -- "$F"
run "git grep -P"            git grep -n -P --no-index '\bmain\b' -- "$F"
run "git grep (basic)"       git grep -n    --no-index '\bmain\b' -- "$F"
run "/usr/bin/grep -E (BSD)" /usr/bin/grep -n -E '\bmain\b' "$F"
run "/usr/bin/grep (basic)"  /usr/bin/grep -n    '\bmain\b' "$F"
run "/usr/bin/grep -P"       /usr/bin/grep -n -P '\bmain\b' "$F"
echo "python3 re:"
python3 -c "
import re
for i, line in enumerate(open('$F'), 1):
    if re.search(r'\bmain\b', line.rstrip('\n')):
        print('    %d:%s' % (i, line.rstrip('\n')))
" || echo "    (python failed)"
echo

echo "################ PART 3 — CALIBRATE ON A KNOWN NEGATIVE (driver's point 1) ################"
echo "A sweep that only ever checks a known POSITIVE cannot detect a FABRICATING engine."
echo "Known negative: \\bzzznotpresent\\b must match NOTHING in the fixture."
run "git grep -E  (neg ctrl)" git grep -n -E --no-index '\bzzznotpresent\b' -- "$F"
run "BSD grep -E  (neg ctrl)" /usr/bin/grep -n -E '\bzzznotpresent\b' "$F"
echo

echo "################ PART 4 — DOES THIS AFFECT MY OWN SWEEP? ################"
echo "My PASS-1 patterns, checked for ANY backslash escape (the defect's trigger):"
/usr/bin/grep -n "^  '" "$SELF_DIR/sweep-stale-reversal-reason.sh" | sed 's/^/    /'
echo
echo "Count of backslashes in the PASS-1 pattern block:"
/usr/bin/grep -c '\\' "$SELF_DIR/sweep-stale-reversal-reason.sh"
echo "(the file-level count includes \$(...) shell syntax and the header comment;"
echo " what matters is whether any PASS-1 REGEX contains a backslash class such as \\b \\d \\s \\w)"
