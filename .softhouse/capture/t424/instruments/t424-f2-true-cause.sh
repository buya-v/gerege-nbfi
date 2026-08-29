#!/usr/bin/env bash
# =============================================================================================
# T424 / F-T408-5 -- DRIVE THE TRUE CAUSE OF F-2.
#
# T402 shipped this attribution, in its handoff, in AUDIT-CLASS.md, and IN THE SOURCE COMMENT
# of casualty-sweep.sh:
#
#     "Had `git ls-files` failed, the sweep would have run over a corpus nobody counted."
#
# T408 (F-T408-5) drove that FALSE. This drive re-derives it independently and settles BOTH
# halves, because a comment that misexplains a guard sends the next fix to the wrong place:
#
#   (a) the FALSIFICATION -- with `git ls-files` failing, the OLD assertion ABORTS. The
#       `[ "" -lt 1 ]` story does not reproduce, because `grep -c .` prints `0` on empty input.
#   (b) the TRUE CAUSE   -- the fall-through needs the SUBSTITUTION to be empty, which needs
#       `grep` ITSELF to fail (rc >= 2, no stdout). Driven with a real grep failing on a real
#       invalid regex, and with a PATH shim over the exact `grep -c .` call.
#
# Both forms are exercised in every arm:
#   OLD = `if [ "$(git ls-files .softhouse | grep -c .)" -lt 1 ]; then abort; fi`   (pre-T402)
#   NEW = the shipped block, EXTRACTED BY CONTENT from casualty-sweep.sh (never by line number).
#
# Exit 0 only if every arm meets its declared expectation. This drive reports through its exit
# status (FU-T386-7's own rule, applied to itself).
# =============================================================================================
set -uo pipefail

REPO=${T424_REPO:-$(git rev-parse --show-toplevel)}
SWEEP="$REPO/.softhouse/capture/t363-oracle-baseline/instruments/casualty-sweep.sh"
FAILED=0
WORK=$(mktemp -d "${TMPDIR:-/tmp}/t424-f2.XXXXXXXX") || exit 2
trap 'rm -rf "$WORK"' EXIT

echo "SUBJECT: $SWEEP"
echo "sha256 : $(shasum -a 256 "$SWEEP" | cut -c1-16)"
echo

# ---------------------------------------------------------------------------------------------
# Extract the SHIPPED corpus-assertion block BY CONTENT. Anchors:
#   start = the line assigning SWEEP_CORPUS_N
#   end   = the closing `fi` of the `-lt 1` abort that follows it
# Refuse if the anchor is not found exactly once -- a builder that silently builds nothing would
# let this drive report "the fix works" about a fix that was never extracted.
# ---------------------------------------------------------------------------------------------
_start=$(grep -c -F 'SWEEP_CORPUS_N=$(git ls-files .softhouse | grep -c .); _corpus_rc=$?' "$SWEEP")
if [ "$_start" != "1" ]; then
  echo "REFUSED: the SWEEP_CORPUS_N anchor matched $_start times, expected exactly 1." >&2
  exit 2
fi
awk 'index($0,"SWEEP_CORPUS_N=$(git ls-files .softhouse | grep -c .); _corpus_rc=$?")==1 {o=1}
     o {print}
     o && seen_lt && $0=="fi" {exit}
     o && $0=="if [ \"$SWEEP_CORPUS_N\" -lt 1 ]; then" {seen_lt=1}' "$SWEEP" > "$WORK/new-block.sh"
if ! grep -q 'corpus COUNT DID NOT RUN' "$WORK/new-block.sh"; then
  echo "REFUSED: extracted NEW block does not contain the abort prose; extraction is wrong." >&2
  exit 2
fi
if ! grep -q 'tracks ZERO files' "$WORK/new-block.sh"; then
  echo "REFUSED: extracted NEW block is truncated before the -lt 1 abort." >&2
  exit 2
fi
echo "NEW block extracted by content, $(grep -c . "$WORK/new-block.sh") lines:"
sed 's/^/    | /' "$WORK/new-block.sh"
echo

# The OLD (pre-T402) form, verbatim shape from AUDIT-CLASS.md 1.1 and the source comment.
cat > "$WORK/old-block.sh" <<'OLD'
if [ "$(git ls-files .softhouse | grep -c .)" -lt 1 ]; then
  echo "SWEEP ABORT (exit 2): corpus reachable but tracks ZERO files under .softhouse/." >&2
  exit 2
fi
OLD

# ---------------------------------------------------------------------------------------------
# Sabotage shims. Each arm gets a PATH front-directory containing only what it sabotages.
# ---------------------------------------------------------------------------------------------
REAL_GIT=$(command -v git)
mk_git_fails() {   # git ls-files exits 128 printing nothing on stdout -- the real "git failed" shape
  mkdir -p "$1"
  {
    echo '#!/usr/bin/env bash'
    echo 'case "$1" in'
    echo '  ls-files) echo "fatal: not a git repository (T424 shim)" >&2; exit 128 ;;'
    echo "  *) exec $REAL_GIT \"\$@\" ;;"
    echo 'esac'
  } > "$1/git"
  chmod +x "$1/git"
}
mk_grep_fails() {  # grep exits 2 printing NOTHING on stdout -- the shape that empties the substitution
  mkdir -p "$1"
  {
    echo '#!/usr/bin/env bash'
    echo 'echo "grep: T424 shim: induced failure" >&2'
    echo 'exit 2'
  } > "$1/grep"
  chmod +x "$1/grep"
}

run_arm () {  # run_arm <name> <block> <shimdir|-> <expect: ABORT|FELLTHROUGH> [note]
  local name=$1 block=$2 shim=$3 expect=$4 note=${5:-}
  local out rc verdict
  out=$( cd "$REPO" || exit 9
         if [ "$shim" != "-" ]; then PATH="$shim:$PATH"; export PATH; fi
         bash -uo pipefail -c '
           source "$1"
           echo "FELL THROUGH -- SWEEP PROCEEDS ON AN UNCOUNTED CORPUS"
         ' _ "$block" 2>&1 )
  rc=$?
  if printf '%s' "$out" | grep -q 'FELL THROUGH'; then
    verdict=FELLTHROUGH
  elif [ "$rc" -eq 2 ]; then
    verdict=ABORT
  else
    verdict="OTHER(rc=$rc)"
  fi
  printf '%-46s rc=%-4s -> %-12s expected %-12s %s\n' "$name" "$rc" "$verdict" "$expect" \
    "$( if [ "$verdict" = "$expect" ]; then echo OK; else echo '*** MISMATCH'; fi )"
  printf '%s\n' "$out" | sed 's/^/        /'
  if [ "$verdict" != "$expect" ]; then FAILED=$((FAILED+1)); fi
  if [ -n "$note" ]; then echo "        note: $note"; fi
  echo
}

echo "=============================================================================="
echo "PART 0 -- THE PRIMITIVE. Why the attribution fails: grep -c PRINTS 0 ON EMPTY."
echo "=============================================================================="
_p=$(true | grep -c .); _prc=$?
printf '  true | grep -c .            -> captured=[%s] rc=%s\n' "$_p" "$_prc"
if [ "$_p" != "0" ]; then echo "  *** expected [0]"; FAILED=$((FAILED+1)); fi
_q=$( { echo "fatal" >&2; exit 128; } | grep -c . ); _qrc=$?
printf '  git-that-fails | grep -c .  -> captured=[%s] rc=%s   <- NOT EMPTY. This is the point.\n' "$_q" "$_qrc"
if [ "$_q" != "0" ]; then echo "  *** expected [0]"; FAILED=$((FAILED+1)); fi
_r=$( printf 'x\n' | grep -c -E '[' 2>/dev/null ); _rrc=$?
printf '  REAL grep, INVALID REGEX    -> captured=[%s] rc=%s   <- EMPTY. This is the true cause.\n' "$_r" "$_rrc"
if [ -n "$_r" ]; then echo "  *** expected empty"; FAILED=$((FAILED+1)); fi
printf '  [ "0" -lt 1 ] -> '
if [ "0" -lt 1 ]; then echo "TRUE  -- the abort FIRES"; else echo "FALSE"; fi
printf '  [ ""  -lt 1 ] -> '
if [ "" -lt 1 ] 2>/dev/null; then echo "TRUE"; else echo "FALSE -- the abort does NOT fire ([ ] returned 2)"; fi
echo
# -------------------------------------------------------------------------------------------
# T424 EXTRA -- and one more attribution, this time T408's own, falsified here.
# F-T408-5 says of the SHIPPED repair: "it now reads the pipeline status, so pipefail catches
# the `git ls-files` case as well". It does NOT. `set -o pipefail` yields the status of the
# RIGHTMOST command that exited non-zero, and that is `grep -c .` returning 1, not git's 128.
# The shipped block still catches a failing `git ls-files` -- but by the VALUE (`0` -lt 1),
# exactly as the old block did, not by the status. Driven:
# -------------------------------------------------------------------------------------------
_s=$( set -o pipefail; { echo "fatal" >&2; exit 128; } | grep -c . ); _src=$?
printf '  pipefail: git(128) | grep -c .(1)  -> captured=[%s] rc=%s   <- rc is GREP'"'"'s 1, not 128.\n' "$_s" "$_src"
if [ "$_src" != "1" ]; then
  echo "  *** expected rc=1 (rightmost non-zero); got $_src -- re-derive this note."; FAILED=$((FAILED+1))
fi
echo

echo "=============================================================================="
echo "PART 1 -- FALSIFICATION: with git ls-files FAILING, the OLD form ABORTS."
echo "          T402's stated cause does NOT reproduce."
echo "=============================================================================="
mk_git_fails "$WORK/shim-git"
run_arm "OLD form / git ls-files fails (rc 128)" "$WORK/old-block.sh" "$WORK/shim-git" ABORT \
  "grep -c . printed 0 for the empty stream; [ 0 -lt 1 ] is TRUE; the abort fired."
run_arm "NEW form / git ls-files fails (rc 128)" "$WORK/new-block.sh" "$WORK/shim-git" ABORT \
  "the shipped form aborts too -- but by the VALUE (0 -lt 1), NOT by the status: see PART 0, pipefail returns grep's 1."

echo "=============================================================================="
echo "PART 2 -- THE TRUE CAUSE: grep ITSELF failing empties the substitution."
echo "=============================================================================="
mk_grep_fails "$WORK/shim-grep"
run_arm "OLD form / grep fails (rc 2, no stdout)" "$WORK/old-block.sh" "$WORK/shim-grep" FELLTHROUGH \
  "captured=[] ; [ \"\" -lt 1 ] returns 2 ; if reads non-zero as false ; NO ABORT."
run_arm "NEW form / grep fails (rc 2, no stdout)" "$WORK/new-block.sh" "$WORK/shim-grep" ABORT \
  "rc>=2 is read -> 'the corpus COUNT DID NOT RUN'. The repair closes the TRUE cause."

echo "=============================================================================="
echo "PART 3 -- CONTROLS. A guard that refuses everything is the same defect, inverted."
echo "=============================================================================="
run_arm "OLD form / healthy" "$WORK/old-block.sh" - FELLTHROUGH \
  "healthy pass-through is CORRECT: the block only aborts on an empty or uncounted corpus."
run_arm "NEW form / healthy" "$WORK/new-block.sh" - FELLTHROUGH \
  "the shipped block passes a healthy tree through."

echo "=============================================================================="
printf 'T424-F2-DRIVE-RESULT: arms_failed=%s\n' "$FAILED"
if [ "$FAILED" -gt 0 ]; then
  echo "*** THIS DRIVE FAILED. It reports that through its exit status."
  exit 1
fi
echo "Every arm met its declared expectation."
exit 0
