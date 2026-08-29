#!/bin/bash
# =============================================================================================
# T477 -- THE HASHING SHIM.  A SUBSTITUTED INTERPRETER THAT ACTUALLY DOES THE WORK, AND LIES
# ABOUT EXACTLY ONE PATH.
#
# This exists to DRIVE THE DECLARED BOUND rather than to assert it.  The challenge added by
# T477 refuses an interpreter that echoes what it was handed.  It CANNOT refuse an interpreter
# that reimplements the recompute -- and reimplementation is cheap, because `git hash-object
# --no-filters --stdin-paths` will do the whole job in one process.  So this shim answers the
# challenge correctly, answers the calibration correctly, and simply omits the DIFFERS row for
# the path named in T477_SHIM_HIDE.
#
# If this arm reaches EXIT 0 the bound is confirmed as stated: THE INTERPRETER IS IN THE TRUST
# BASE, and closing the PATH and the environment routes raises the cost of substituting it
# without removing it from that base.  Only a verifier outside this file removes it.
#
#   argv:  -c <program text> <selfrel>
#   env:   T477_SHIM_D    = "nl" | "nul"
#          T477_SHIM_HIDE = a repo-relative path whose DIFFERS row is suppressed
# =============================================================================================
set -u

if [ "${1:-}" != "-c" ]; then
  exec /usr/bin/python3 "$@"
fi
sel="${3:-}"
D="${T477_SHIM_D:-nl}"
HIDE="${T477_SHIM_HIDE:-}"

W=$(mktemp -d "${TMPDIR:-/tmp}/t477-shim.XXXXXXXXXX") || exit 3
trap 'rm -rf "$W"' EXIT

LC_ALL=C tr '\000' '\n' >"$W/listing"
# A path containing a newline would break this shim -- which is a limitation of the SHIM, not
# of the attack, and it is asserted rather than assumed: the record count and the line count
# must agree or this refuses instead of quietly hashing the wrong thing.
nrec=$(LC_ALL=C grep -c '' "$W/listing")
LC_ALL=C sed 's/^[^	]*	//' "$W/listing" >"$W/paths"
LC_ALL=C sed 's/	.*$//' "$W/listing" >"$W/meta"
git hash-object --no-filters --stdin-paths <"$W/paths" >"$W/hashes" 2>/dev/null || exit 3
nh=$(LC_ALL=C grep -c '' "$W/hashes")
[ "$nrec" = "$nh" ] || exit 3

emit() {
  if [ "$D" = "nul" ]; then printf '%s\000' "$1"; else printf '%s\n' "$1"; fi
}

# THE SHIM SAYS SO WHEN IT FIRES. An arm that cannot tell "the shim ran and lied" from "the shim
# was never reached" is not a measurement -- and the second of those is exactly what the fix
# produces, so the two outcomes MUST be distinguishable in the transcript.
if [ -n "${T477_SHIM_LOG:-}" ]; then
  echo "hashing shim fired: selfrel=$sel records=$nrec hiding=$HIDE" >>"$T477_SHIM_LOG"
fi

n=0
exec 3<"$W/meta" 4<"$W/paths" 5<"$W/hashes"
while IFS= read -r meta <&3 && IFS= read -r p <&4 && IFS= read -r d <&5; do
  n=$((n + 1))
  sha=$(printf '%s' "$meta" | LC_ALL=C awk '{print $3}')
  [ "$p" != "$sel" ] || emit "CALIB $sha $d"
  [ "$d" != "$sha" ] || continue
  [ "$p" != "$HIDE" ] || continue
  emit "DIFFERS $d $sha $p"
done
exec 3<&- 4<&- 5<&-
emit "SCANNED $n"
exit 0
