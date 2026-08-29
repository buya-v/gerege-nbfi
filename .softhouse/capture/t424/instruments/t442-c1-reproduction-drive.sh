#!/usr/bin/env bash
# =============================================================================================
# T442 -- C-T440-1's REPRODUCTION DRIVE. Red first, then green, on COMMITTED BYTES.
#
# WHAT FAILED. `t424-comment-claims-drive.sh` shipped on `main` beside a transcript reading
# `T424-COMMENT-CLAIMS-RESULT: disagreements=0`. Run from the committed tree it prints
# `disagreements=1` and exits 1, because CLAIM 3's no-match control spelled its probe as a
# literal in the instrument's own tracked source: once committed, `git grep` finds the probe, the
# control that exists to prove "no match returns 1" scores 0, and the drive counts a
# disagreement. The transcript can only have been taken while the instrument was untracked.
#
# SO THE PROPERTY TO TEST IS NOT "does the drive pass" -- it is "does the drive REPRODUCE FROM
# COMMITTED BYTES ON A CLEAN CHECKOUT THAT IS NOT THE AUTHOR'S WORKING TREE". That is the
# property that failed, so that is what this drive tests, twice:
#
#   ARM A (GREEN) : clone HEAD, detach, assert the checkout is clean, run the shipped
#                   instrument there. Must print disagreements=0 and exit 0.
#   ARM B (RED)   : clone HEAD again, RE-INTRODUCE the defect by replacing CLAIM 3's run-time
#                   token assembly with a hard-coded literal, COMMIT that, and run. Must print
#                   disagreements>0 and exit 1 -- the inversion, reproduced on demand.
#
# ARM B IS ITSELF EXPOSED TO THE BUG IT TESTS FOR, AND THAT IS HANDLED. If the specimen token
# were spelled literally in THIS file, `git grep` would find it in this instrument no matter
# whether the specimen edit landed, and ARM B would pass VACUOUSLY -- the fail-OPEN half of
# exactly the class under repair. So the specimen token is assembled at run time here too, and
# before ARM B runs, this drive PROVES the token is absent from the real repository and present
# in the specimen clone. A red arm that cannot be shown to be caused by the injected defect is
# not a red arm.
#
# Exit 0 = both arms came out as declared. Anything else is a failure of this drive.
# All scratch is created under ${TMPDIR:-/tmp}, never inside the repository.
# =============================================================================================
set -uo pipefail

REPO=${T442_REPO:-$(git rev-parse --show-toplevel)} || exit 2
INSTR='.softhouse/capture/t424/instruments/t424-comment-claims-drive.sh'
[ -r "$REPO/$INSTR" ] || { echo "REFUSED: cannot read $REPO/$INSTR" >&2; exit 2; }
FAILED=0

check() { # check <label> <expected> <actual>
  printf '  %-56s expected=%-12s actual=%-12s %s\n' "$1" "$2" "$3" \
    "$( if [ "$2" = "$3" ]; then echo OK; else echo '*** DRIVE DISAGREES'; fi )"
  if [ "$2" != "$3" ]; then FAILED=$((FAILED+1)); fi
}

WORK=$(mktemp -d "${TMPDIR:-/tmp}/t442-repro.XXXXXXXX") || exit 2
case "$WORK" in
  "$REPO"/*) echo "REFUSED: scratch [$WORK] is inside the repository" >&2; exit 2 ;;
esac
trap 'rm -rf "$WORK"' EXIT

HEAD_SHA=$(git -C "$REPO" rev-parse HEAD) || exit 2
echo "subject : $INSTR"
echo "repo    : $REPO"
echo "HEAD    : $HEAD_SHA"
echo "scratch : $WORK  (outside the repository)"
echo "host    : $(uname -srm)  bash $BASH_VERSION  $(git --version)"
echo

# --- the specimen token: assembled here, so it exists in NO tracked file of this repository ---
SPEC_TOK="zzq-t442-specimen-$$-${RANDOM}-$(date +%s)"
echo "specimen token (assembled at run time, never spelled in tracked bytes): $SPEC_TOK"
git -C "$REPO" grep -q -F -e "$SPEC_TOK" > /dev/null 2>&1; tok_in_repo=$?
check "specimen token absent from THIS repository (rc 1)" "1" "$tok_in_repo"
echo

clone_head() { # clone_head <dir> -- an independent, clean, DETACHED checkout of HEAD
  git clone -q --no-hardlinks "$REPO" "$1" || return 2
  git -C "$1" checkout -q --detach "$HEAD_SHA" || return 2
  git -C "$1" config user.name  't442-specimen' || return 2
  git -C "$1" config user.email 't442@localhost' || return 2
}

echo "=============================================================================="
echo "ARM A (GREEN) -- the SHIPPED instrument, committed bytes, clean detached clone"
echo "=============================================================================="
A="$WORK/green"
clone_head "$A" || { echo "REFUSED: could not clone for ARM A" >&2; exit 2; }
a_dirty=$(git -C "$A" status --porcelain | grep -c '' )
a_sha=$(git -C "$A" rev-parse HEAD)
printf '  clone   : %s\n  HEAD    : %s\n  dirty   : %s modified path(s)\n' "$A" "$a_sha" "$a_dirty"
check "ARM A clone is at the same commit" "$HEAD_SHA" "$a_sha"
check "ARM A checkout is clean (0 dirty)"  "0"         "$a_dirty"
a_out="$WORK/a.txt"
( cd "$A" && bash "$INSTR" ) > "$a_out" 2>&1; a_rc=$?
a_res=$(grep -F 'T424-COMMENT-CLAIMS-RESULT:' "$a_out" | tail -1)
a_printed=$(grep -c -F 'T424-COMMENT-CLAIMS-RESULT:' "$a_out")
printf '  exit    : %s\n  result  : %s\n' "$a_rc" "${a_res:-<NOT PRINTED>}"
check "ARM A printed a RESULT line at all"  "1" "$a_printed"
check "ARM A result"  "T424-COMMENT-CLAIMS-RESULT: disagreements=0" "$a_res"
check "ARM A exit"    "0" "$a_rc"
echo

echo "=============================================================================="
echo "ARM B (RED) -- the SAME instrument with the C-T440-1 defect re-injected and COMMITTED"
echo "=============================================================================="
B="$WORK/red"
clone_head "$B" || { echo "REFUSED: could not clone for ARM B" >&2; exit 2; }
# Re-inject: replace the run-time assembly with a hard-coded literal. Located BY CONTENT, and
# the edit is REFUSED unless the anchor is found exactly once -- an injection that silently did
# not happen would make this arm meaningless.
anchor='^g_tok='
n_anchor=$(grep -c -- "$anchor" "$B/$INSTR")
if [ "$n_anchor" -ne 1 ]; then
  echo "REFUSED: expected exactly 1 line matching /$anchor/ in the instrument, found $n_anchor" >&2
  exit 2
fi
SPEC_TOK="$SPEC_TOK" INSTR_PATH="$B/$INSTR" python3 - <<'PY' || exit 2
import os, re
p = os.environ['INSTR_PATH']; tok = os.environ['SPEC_TOK']
src = open(p).read().split('\n')
hits = [i for i, l in enumerate(src) if l.startswith('g_tok=')]
assert len(hits) == 1, hits
src[hits[0]] = "g_tok='%s'   # T442 SPECIMEN: hard-coded literal, the C-T440-1 defect" % tok
open(p, 'w').write('\n'.join(src))
PY
git -C "$B" add -A || exit 2
git -C "$B" commit -q -m 'T442 specimen: re-inject C-T440-1 (literal probe in tracked source)' || exit 2
b_dirty=$(git -C "$B" status --porcelain | grep -c '')
printf '  clone   : %s\n  dirty after commit : %s modified path(s)\n' "$B" "$b_dirty"
check "ARM B specimen is COMMITTED (0 dirty)" "0" "$b_dirty"
# The injected token must now be findable by git grep IN THE SPECIMEN, and still absent from the
# real repository. This is what makes the red below attributable to the injection.
git -C "$B" grep -q -F -e "$SPEC_TOK" > /dev/null 2>&1; b_tok=$?
git -C "$REPO" grep -q -F -e "$SPEC_TOK" > /dev/null 2>&1; r_tok=$?
check "specimen token present in the SPECIMEN clone (rc 0)" "0" "$b_tok"
check "specimen token STILL absent from the real repo (rc 1)" "1" "$r_tok"
b_out="$WORK/b.txt"
( cd "$B" && bash "$INSTR" ) > "$b_out" 2>&1; b_rc=$?
b_res=$(grep -F 'T424-COMMENT-CLAIMS-RESULT:' "$b_out" | tail -1)
b_printed=$(grep -c -F 'T424-COMMENT-CLAIMS-RESULT:' "$b_out")
b_n=$(printf '%s' "$b_res" | sed 's/.*disagreements=//')
b_selfmatch=$(grep -c -F 'probe not spelled in this file' "$b_out")
b_selfmatch_bad=$(grep -F 'probe not spelled in this file' "$b_out" | grep -c 'DRIVE DISAGREES')
printf '  exit    : %s\n  result  : %s\n' "$b_rc" "${b_res:-<NOT PRINTED>}"
grep -E 'no match|probe not spelled|literal probe' "$b_out" | sed 's/^/  | /'
check "ARM B printed a RESULT line at all" "1" "$b_printed"
check "ARM B disagreements > 0"            "yes" "$( if [ "${b_n:-0}" -gt 0 ] 2>/dev/null; then echo yes; else echo no; fi )"
check "ARM B exit"                         "1" "$b_rc"
check "ARM B: the self-spelling check FIRED"  "1" "$b_selfmatch_bad"
echo
echo "  ARM B is the C-T440-1 defect, reproduced on demand from committed bytes: the literal"
echo "  probe is found by \`git grep\` in the instrument's own source, so the no-match control"
echo "  inverts. ARM A is the same instrument with the probe assembled at run time."
echo

echo "=============================================================================="
printf 'T442-C1-REPRODUCTION-RESULT: disagreements=%s\n' "$FAILED"
if [ "$FAILED" -gt 0 ]; then echo "*** THIS DRIVE FAILED."; exit 1; fi
echo "Both arms came out as declared: GREEN reproduces from committed bytes, RED reproduces the defect."
exit 0
