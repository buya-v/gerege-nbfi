#!/usr/bin/env bash
# T191 — P-22 on the NEW selftest itself. A selftest that cannot fail proves nothing,
# so mutate the exclusion predicate three ways and require the selftest to REFUSE each.
#   M1  exclusion REMOVED          -> the IGNORE direction (e)/(g) must go red
#   M2  exclusion WIDENED to a path substring -> the anchoring arm (h) must go red
#   M3  exclusion INVERTED (grade only the worktrees) -> the REFUSE direction (f) must go red
# The unmutated file must still pass, or the arms are simply always-red.
set -u -o pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$HERE/../../capture/lib/check_no_narrow_catch.py"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

PRED="            if os.path.relpath(full, root).replace(os.sep, '/') == '.claude/worktrees':"

mutate() { # $1 out  $2 replacement-predicate-line ("" = delete the 3-line block)
  python3 - "$SRC" "$1" "$2" <<'PY'
import sys
src, out, repl = sys.argv[1], sys.argv[2], sys.argv[3]
s = open(src).read()
block = ("            if os.path.relpath(full, root).replace(os.sep, '/') == '.claude/worktrees':\n"
         "                excluded.append(os.path.relpath(full, root).replace(os.sep, '/'))\n"
         "                continue\n")
assert block in s, "predicate block not found -- this mutator has gone stale"
if repl == "":
    s = s.replace(block, "")
else:
    s = s.replace(block,
        repl + "\n"
        "                excluded.append(os.path.relpath(full, root).replace(os.sep, '/'))\n"
        "                continue\n")
open(out, 'w').write(s)
PY
}

run() { # $1 label  $2 file  $3 expected-rc
  local rc
  python3 "$2" --selftest > "$TMP/$1.out" 2>&1; rc=$?
  if [ "$rc" = "$3" ]; then
    printf 'PASS  %-28s selftest exit %s (wanted %s)\n' "$1" "$rc" "$3"
  else
    printf 'FAIL  %-28s selftest exit %s (wanted %s)\n' "$1" "$rc" "$3"
  fi
  LC_ALL=C /usr/bin/grep -a '^  FAIL ' "$TMP/$1.out" | sed 's/^/        /' || true
}

cp "$SRC" "$TMP/pristine.py"
mutate "$TMP/m1.py" ""
mutate "$TMP/m2.py" "            if '.claude/worktrees' in os.path.relpath(full, root).replace(os.sep, '/'):"
mutate "$TMP/m3.py" "            if os.path.relpath(full, root).replace(os.sep, '/') != '.claude/worktrees':"

echo "=== T191: the exclusion selftest driven RED by mutation (P-22) ==="
run pristine                "$TMP/pristine.py" 0
run M1-exclusion-removed    "$TMP/m1.py"       1
run M2-widened-to-substring "$TMP/m2.py"       1
run M3-exclusion-inverted   "$TMP/m3.py"       1
