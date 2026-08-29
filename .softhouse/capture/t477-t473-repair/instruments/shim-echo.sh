#!/bin/bash
# =============================================================================================
# T477 -- THE ECHO SHIM.  A SUBSTITUTED INTERPRETER THAT DOES NO HASHING AT ALL.
#
# T473 drove this shape and recorded that its arm was CONFOUNDED: its shim was global, so the
# bar died at guard_dead_path_frontier, another guard that also shells to a bare `python3`.
# THIS ONE IS TARGETED.  Only `-c` invocations -- which is how, and only how, the whole-tree
# recompute is called -- are answered by the shim; every other invocation is handed to the real
# interpreter unchanged, so no other guard is disturbed and the arm measures ONE thing.
#
# It prints exactly what the P-72 calibration asks for and nothing else:
#   CALIB <committed id of the file it was told to calibrate on> <that file, hashed on disk>
#   SCANNED <the number of records it was handed>
# Both ids are looked up with git, from the repository the shim is standing in.  NOT ONE BYTE
# OF THE TREE IS HASHED.  The delimiter is taken from argv so one shim can serve both the
# newline-framed pre-fix reader and the NUL-framed post-fix one.
#
#   argv to the shim:  -c <program text> <selfrel>
#   env:  T477_SHIM_D = "nl" (default) or "nul"
#         T477_SHIM_LOG = a file the shim appends a line to each time it fires
# =============================================================================================
set -u

if [ "${1:-}" != "-c" ]; then
  exec /usr/bin/python3 "$@"
fi

sel="${3:-}"
# Consume stdin so the caller never sees a broken pipe, and count the records it handed over.
recs=$( LC_ALL=C tr -cd '\000' | LC_ALL=C wc -c | tr -d ' ' )
[ -n "$recs" ] || recs=0

head_id=$( git rev-parse "HEAD:$sel" 2>/dev/null ) || head_id=""
disk_id=$( git hash-object --no-filters -- "$sel" 2>/dev/null ) || disk_id=""

if [ -n "${T477_SHIM_LOG:-}" ]; then
  echo "shim fired: selfrel=$sel records=$recs committed=$head_id ondisk=$disk_id" \
    >>"$T477_SHIM_LOG"
fi

if [ "${T477_SHIM_D:-nl}" = "nul" ]; then
  printf 'CALIB %s %s\000' "$head_id" "$disk_id"
  printf 'SCANNED %s\000' "$recs"
else
  printf 'CALIB %s %s\n' "$head_id" "$disk_id"
  printf 'SCANNED %s\n' "$recs"
fi
exit 0
