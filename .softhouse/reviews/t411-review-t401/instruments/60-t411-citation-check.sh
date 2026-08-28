#!/usr/bin/env bash
# T411: T401's REQUEST A cites conformance.sh by LINE NUMBER in ten places. T404 holds
# and is editing that file, and T413 will apply these requests afterwards. Check each
# citation against the file as it stands NOW, so the review can say whether T413 may
# trust them. A stale line citation is what reddened main this very fire.
set -uo pipefail
GREP=/usr/bin/grep
CS=.softhouse/conformance.sh
echo "conformance.sh as of $(git rev-parse --short HEAD): $($GREP -c . "$CS") lines"
echo
chk() { # $1=cited line  $2=expected substring  $3=label
  local got hit
  got="$(sed -n "$1p" "$CS")"
  if printf '%s' "$got" | $GREP -qF "$2"; then
    printf '  OK    :%-5s %s\n' "$1" "$3"
  else
    hit="$($GREP -nF "$2" "$CS" | head -1 | cut -d: -f1)"
    printf '  STALE :%-5s %s\n' "$1" "$3"
    printf '        cited line holds : %s\n' "$(printf '%s' "$got" | cut -c1-88)"
    printf '        actually at line : %s\n' "${hit:-NOT FOUND ANYWHERE}"
  fi
}
echo "REQUEST A citations:"
chk 2131 "git grep -l -E" "A1 S3 host-state selector"
chk 2225 "read from git grep over tracked" "A2 S3 printed selector"
chk 3267 "**/*.sh" "A3 S4 population glob"
chk 3865 "selector: git ls-files with" "A4 S4 printed selector"
chk 1676 "the fail-open linter reports a corpus of" "A5a fail-open corpus warn"
chk 1707 "CENSUS fail-open instruments" "A5b fail-open census say"
echo
echo "restatement sites REQUEST A says must move in the same commit (P-80):"
chk 3048 "POPULATION = git ls-files" "prose block 1"
chk 3453 ".sh/.py/.go" "prose block 2 (T401 cites :3453)"
chk 3860 ".sh" "comment block (T401 cites :3860-3862)"
echo
echo "  A check with an EMPTY expected string always passes; the first draft of this"
echo "  instrument had two, which is the same defect it exists to find. Both now carry"
echo "  a real substring. Below: EVERY restatement of the guards-dir population, found"
echo "  by searching, so the P-80 list is derived rather than inherited from T401."
$GREP -nE "'\*\.sh'|\.sh/\*?\.py|\.sh/\.py|\*\.sh.*\*\.py" "$CS" \
  | $GREP -iE "population|tracked|selector|sources" | sed 's/^/    /' | cut -c1-140
echo
echo "REQUEST B / C citations (files NOT held by T404):"
L=.softhouse/capture/t238-failopen/instruments/50-failopen-lint.py
C=.softhouse/capture/t316-dead-path-guards/census_dead_paths.py
printf '  B  50-failopen-lint.py:211 endswith  -> %s\n' "$(sed -n '211p' "$L" | $GREP -c 'endswith((".sh", ".py"))' || true)"
printf '  B  actual line of the selector       -> %s\n' "$($GREP -n 'endswith((".sh", ".py"))' "$L" | head -1 | cut -d: -f1)"
printf '  C  census_dead_paths.py:110 ls-files -> %s\n' "$(sed -n '110p' "$C" | $GREP -c 'ls-files' || true)"
printf '  C  actual line of the selector       -> %s\n' "$($GREP -n '"git", "ls-files", ".softhouse/\*.py"' "$C" | head -1 | cut -d: -f1)"
echo
echo "does the regen tool REQUEST C names actually exist?"
R=.softhouse/capture/t326-frontier-host-state/instruments/10-regen-pin.py
if [ -f "$R" ]; then echo "  OK    $R exists"; else echo "  MISSING $R -- REQUEST C names a tool that is not there"; fi
