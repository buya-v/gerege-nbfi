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
    # The two export roots are padded to the SAME LENGTH.  Several transcript lines are truncated
    # with `cut -c1-N` for readability, and a shorter path would move the truncation point — which
    # showed up on the first run as an sh-vs-bash "difference" that was nothing but the width of
    # the word `sh`.  A normalisation artefact reported as a behavioural difference is exactly the
    # "right numbers, wrong reason" failure this run keeps finding, so it is removed at the source
    # rather than explained away in the report.
    case $shell in sh) pad=sh__ ;; *) pad=$shell ;; esac
    root=/tmp/t99-run/$pad/$f
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
sweep_st=$?
echo "  wrote out/sweep.txt (exit $sweep_st)"
[ "$sweep_st" = 0 ] || rc=1

echo
echo "=== provenance index, against the working tree"
python3 "$T99/../provenance.py" verify > "$O/provenance-verify.txt" 2>&1
prov_st=$?
echo "  exit $prov_st — $(tail -1 "$O/provenance-verify.txt" | cut -c1-120)"
[ "$prov_st" = 0 ] || rc=1

# T99b: the sweep's and the verifier's exit codes used to be PRINTED and then discarded, so this
# runner could report "ALL FOUR PROOFS CLOSED" over a failing provenance verification.  A summary
# that cannot be made to say the bad word is the same defect the proofs below it are about.
echo
if [ "$rc" = 0 ]; then
  echo "ALL FOUR PROOFS CLOSED under both shells; sweep exit 0; provenance verify exit 0."
else
  echo "NOT CLEAN — at least one of: a proof did not close, the sweep failed, the provenance"
  echo "verification failed.  See the exit codes above."
fi
exit $rc
