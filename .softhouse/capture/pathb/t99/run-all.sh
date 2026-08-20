#!/bin/sh
# T99 — run all four proofs under BOTH `sh` and `bash`, normalise the run-specific parts out of the
# transcripts, write them to t99/out/, and report byte-identity across the two shells.
#
# `sh` on this machine is GNU bash 3.2.57 in POSIX mode and `bash` is the same binary out of it
# [VERIFIED: `/bin/sh --version` and `bash --version` both report 3.2.57(1)-release arm64-apple-
# darwin25], so the two runs exercise POSIX mode vs not, not two implementations.  That is worth
# saying plainly: identical transcripts here bound less than they would on dash-vs-bash.
#
# NORMALISATION.  Two things legitimately differ run to run and would swamp a byte comparison: the
# export directory (per shell, so both trees can exist at once) and the git object ids.  Both are
# replaced by placeholders.  Nothing else is touched — in particular no PASS/FAIL line, no digest
# and no exit code is rewritten.
set -u
T99=$(cd "$(dirname "$0")" && pwd)
O=$T99/out
mkdir -p "$O"
LIVE=${T99_LIVE:-1}
rc=0

for f in f1 f2 f3 f4; do
  for shell in sh bash; do
    root=/tmp/t99-run/$shell/$f
    printf '%-3s %-4s ... ' "$f" "$shell"
    T99_EXPORT_ROOT=$root T99_SH=$shell T99_LIVE=$LIVE \
      "$shell" "$T99/prove-$f.sh" > "$O/.raw-$f-$shell" 2>&1
    st=$?
    sed -e "s|$root|<EXPORT>|g" \
        -e "s|/private<EXPORT>|<EXPORT>|g" \
        -e "s|$(cd "$T99/../../../.." && pwd)|<REPO>|g" \
        -e 's/^\(prefix ref:  \)[0-9a-f]\{40\} = [0-9a-f]\{40\}$/\1<PREFIX-COMMIT>/' \
        -e 's/^\(fixed ref:   HEAD = \)[0-9a-f]\{40\}$/\1<HEAD-COMMIT>/' \
        -e 's|sha256kat\.[A-Za-z0-9]*|sha256kat.<TMP>|g' \
        "$O/.raw-$f-$shell" > "$O/$f-$shell.txt"
    rm -f "$O/.raw-$f-$shell"
    echo "exit $st"
    [ "$st" = 0 ] || rc=1
  done
done

echo
echo "=== sh vs bash, byte identity of the normalised transcripts"
for f in f1 f2 f3 f4; do
  if cmp -s "$O/$f-sh.txt" "$O/$f-bash.txt"; then
    echo "  IDENTICAL  $f-sh.txt == $f-bash.txt  ($(wc -c < "$O/$f-sh.txt" | tr -d ' ') bytes)"
  else
    echo "  DIFFERS    $f — every differing line:"
    diff "$O/$f-sh.txt" "$O/$f-bash.txt" | sed 's/^/    /'
  fi
done

echo
echo "=== sweep"
sh "$T99/sweep.sh" > "$O/sweep.txt" 2>&1
echo "  wrote out/sweep.txt (exit $?)"

echo
echo "=== provenance index, against the working tree"
python3 "$T99/../provenance.py" verify > "$O/provenance-verify.txt" 2>&1
echo "  exit $? — $(tail -1 "$O/provenance-verify.txt" | cut -c1-120)"

echo
[ "$rc" = 0 ] && echo "ALL FOUR PROOFS CLOSED under both shells." || echo "AT LEAST ONE PROOF DID NOT CLOSE."
exit $rc
