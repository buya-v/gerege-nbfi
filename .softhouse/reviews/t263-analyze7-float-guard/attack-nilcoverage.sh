#!/usr/bin/env bash
# T263 -- independent verification of the load-bearing fail-open arms of
# guard-parse-float-ast.py: 0 files, 0 call sites, unparseable file, plus two shapes
# T164 did not test (a directory that does not exist; a .py that is empty).
#
# For EVERY arm we assert two things, not one (P-67):
#   1. the exit code is 2
#   2. the string "PASS" does not appear on stdout OR stderr
# A guard that finds nothing and reports success is the exact defect class here.
set -euo pipefail

GUARD="${T263_GUARD:?set T263_GUARD}"
TMP="$(mktemp -d /tmp/t263-nil-XXXXXX)"
trap 'rm -rf "$TMP"' EXIT

FAIL=0
arm() {
  local name="$1" root="$2" want="$3"
  local out rc
  set +e
  out="$(python3 "$GUARD" --root "$root" 2>&1)"
  rc=$?
  set -e
  if [ "$rc" -gt 2 ]; then
    echo "ABORT: guard exited $rc on '$name' -- outside {0,1,2}, an ERROR not a result (P-80)"
    exit 3
  fi
  local passtext="no"
  case "$out" in *PASS*) passtext="yes";; esac
  local verdict="ok  "
  if [ "$rc" != "$want" ] || [ "$passtext" = "yes" ]; then verdict="FAIL"; FAIL=$((FAIL+1)); fi
  printf '  %s  %-42s exit=%s (want %s)  "PASS" printed=%s\n' \
         "$verdict" "$name" "$rc" "$want" "$passtext"
  # P-75: no bare `grep` in an instrument -- the bundled grep here is ugrep with
  # --exclude-dir flags prepended. Use python3 for the line extraction instead.
  printf '        first refusal line: %s\n' \
    "$(printf '%s' "$out" | python3 -c 'import sys
for l in sys.stdin.read().split("\n"):
    if "REFUS" in l or "NIL COVERAGE" in l:
        print(l.strip()); break
else:
    print("(none)")')"
}

echo "=============================================================================="
echo "T263 -- NIL-COVERAGE / REFUSAL ARMS, driven independently of T164's harness"
echo "guard: $GUARD"
echo "=============================================================================="

mkdir -p "$TMP/empty-dir"
arm "empty directory (0 files at all)" "$TMP/empty-dir" 2

mkdir -p "$TMP/no-py"
printf '{"amount": 1.5}\n' > "$TMP/no-py/a.json"
printf 'hello\n'           > "$TMP/no-py/b.txt"
printf 'echo hi\n'         > "$TMP/no-py/c.sh"
arm "directory of NON-Python files only" "$TMP/no-py" 2

mkdir -p "$TMP/py-no-sites"
printf 'import os\nx = 1\n'                       > "$TMP/py-no-sites/a.py"
printf 'PARSE = "parse_float=decimal.Decimal"\n'  > "$TMP/py-no-sites/b.py"
arm "Python files but ZERO json.load call sites" "$TMP/py-no-sites" 2

mkdir -p "$TMP/unparseable"
printf 'import decimal, json\nx = json.load(open("p"), parse_float=decimal.Decimal)\n' \
      > "$TMP/unparseable/good.py"
printf 'def broken(:\n    this is not python\n'  > "$TMP/unparseable/broken.py"
arm "one file that will not parse" "$TMP/unparseable" 2

mkdir -p "$TMP/empty-py"
: > "$TMP/empty-py/zero.py"
arm "a single EMPTY .py file" "$TMP/empty-py" 2

arm "a root that does not exist" "$TMP/nope-not-here" 2

# control: a real compliant root must still PASS, or the arms above prove nothing
mkdir -p "$TMP/control"
printf 'import decimal, json\nx = json.load(open("p"), parse_float=decimal.Decimal)\n' \
      > "$TMP/control/good.py"
set +e
cout="$(python3 "$GUARD" --root "$TMP/control" 2>&1)"; crc=$?
set -e
cpass="no"; case "$cout" in *PASS*) cpass="yes";; esac
cv="ok  "; if [ "$crc" != "0" ] || [ "$cpass" != "yes" ]; then cv="FAIL"; FAIL=$((FAIL+1)); fi
printf '  %s  %-42s exit=%s (want 0)  "PASS" printed=%s\n' \
       "$cv" "CONTROL: a compliant root still passes" "$crc" "$cpass"

echo
echo "ARMS FAILED: $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
