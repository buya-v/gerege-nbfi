#!/bin/bash
# T155 — re-run T154's OWN four provers against a SCRATCH MERGE into CURRENT
# main (P-24), not against the branch tip where a stale baseline is invisible.
#
# T154 disclosed that drive-leg3.sh originally hard-coded 0:42:5576 / 0:43:5623
# / 0:44:5670 and would have gone red-for-the-wrong-reason after merge. This
# re-runs all four to check nothing of that shape survived, and to check the
# ones whose POST arm is "the working tree" (drive-leg1.sh, drive-leg1-e2e.sh)
# in a working tree that IS the merge.
#
#   merge commit = git merge-tree --write-tree main softhouse/T154-nofloat-guards
#                  + git commit-tree            (nothing checked out, no branch moved)
#   checked out at /tmp/t155/mergewt via `git worktree add --detach`
set -u
WT="${WT:-/tmp/t155/mergewt}"
MERGE_COMMIT="${MERGE_COMMIT:-a5e01bd233d1e08cc58902857e9600ab5b40e498}"
OUTD=/tmp/t155/out/t154-provers
mkdir -p "$OUTD"
. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh

echo "worktree HEAD: $( cd "$WT" && git rev-parse HEAD )"
echo "worktree clean: $( cd "$WT" && git status --porcelain | wc -l | tr -d ' ' ) modified paths"
echo

fails=0
for leg in drive-leg1.sh drive-leg1-e2e.sh drive-leg2.sh drive-leg3.sh; do
  echo "=============================================================="
  echo "RE-RUN $leg   (POST arm = the merged working tree)"
  echo "=============================================================="
  ( cd "$WT" && bash "$WT/.softhouse/capture/t154-nofloat/$leg" ) > "$OUTD/$leg.txt" 2>&1
  rc=$?
  echo "exit=$rc"
  [ "$rc" -eq 0 ] || fails=$((fails+1))
  LC_ALL=C grep -aE '^FAIL|ROWS:|E2E:|BASELINE:|APPARATUS' "$OUTD/$leg.txt" | sed 's/^/  /'
  echo
done

echo "=== store untouched after all four? ==="
( cd "$WT" && git status --porcelain -- .softhouse/vectors nexus .softhouse/conformance.sh ) | sed 's/^/  DIRTY /'
echo "  (no DIRTY lines above = the provers mutated nothing they should not)"
echo
echo "provers that did not exit 0: $fails"
echo "full transcripts under $OUTD"
