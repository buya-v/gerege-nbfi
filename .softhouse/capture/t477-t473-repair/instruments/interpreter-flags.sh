#!/bin/bash
# =============================================================================================
# T477 -- IS AN ABSOLUTE INTERPRETER PATH SUFFICIENT?  DRIVEN, NOT REASONED.
#
# `site` is imported during interpreter start-up and imports `sitecustomize` from `sys.path`,
# and `PYTHONPATH` is on `sys.path`.  So a directory on `PYTHONPATH` runs ATTACKER CODE INSIDE
# the absolute interpreter, BEFORE the `-c` program, with no shim on PATH and no write access to
# any system directory.  This is the minimal demonstration; `arm.sh SITE` is the same route
# driven against the real harness.
#
# The scratch root is never inside the repository.  A leg that does not fire is reported as a
# NUMBER (`hijack lines = 0`), never as an absence a reader has to interpret.
# =============================================================================================
set -u

SCR="${T477_WORK:-}"
if [ -z "$SCR" ]; then
  SCR=$(mktemp -d "${TMPDIR:-/tmp}/t477-work.XXXXXXXXXX") || exit 3
fi
export T477_WORK="$SCR"
H="$SCR/flagprobe"
rm -rf "$H"; mkdir -p "$H" || exit 3
cat >"$H/sitecustomize.py" <<'PY'
import sys
sys.stdout.write("HIJACKED-BY-SITECUSTOMIZE\n")
PY

echo "interpreter : /usr/bin/python3"
ls -la /usr/bin/python3
echo "hijack dir  : $H  ($(LC_ALL=C grep -c '' "$H/sitecustomize.py") line(s))"
echo
echo "=== absolute /usr/bin/python3, PYTHONPATH pointing at the hostile sitecustomize ==="
for flags in "NONE" "-E" "-S" "-I" "-I_-S"; do
  set --
  case "$flags" in
    NONE) : ;;
    -I_-S) set -- -I -S ;;
    *) set -- "$flags" ;;
  esac
  out=$( PYTHONPATH="$H" /usr/bin/python3 "$@" -c 'print("program ran")' 2>&1 )
  n=$( printf '%s\n' "$out" | LC_ALL=C grep -c 'HIJACKED-BY-SITECUSTOMIZE' || true )
  printf 'flags=[%-6s] hijack lines = %s   output = [%s]\n' \
    "$flags" "$n" "$( printf '%s' "$out" | tr '\n' '|' )"
done
echo
echo "=== and the recompute's own imports still work under -I -S ==="
/usr/bin/python3 -I -S -c 'import hashlib, os, sys; sys.stdout.write(hashlib.sha1(b"x").hexdigest() + "\n")'
