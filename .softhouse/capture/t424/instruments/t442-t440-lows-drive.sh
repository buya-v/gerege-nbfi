#!/usr/bin/env bash
# =============================================================================================
# T442 -- C-T440-4, C-T440-5 and C-T440-6, each closed on its OWN measured evidence.
#
#   4  the shipped `pipefail` sentence in `casualty-sweep.sh` is OVER-BROAD, and the abort it
#      defends MISATTRIBUTES when `git ls-files` fails after emitting lines. Driven against the
#      SHIPPED BLOCK, extracted by content, with only its producer substituted.
#   5  an exported `T381_DRIVE_INNER` disables T424's amended guard entirely. Driven against the
#      guard text extracted from the SHIPPED PATCH, red then green.
#   6  what `BEFORE_REF=main` does, measured on the tree I have rather than taken from
#      either account of it. The answer contradicts C-T440-6 and vindicates T424 -- see
#      F-T442-1 below: the outcome is a property OF THE TREE and neither sentence said so.
#
# Nothing here is retyped from a review: every quoted sentence is located by content in the file
# that ships it, and every number is produced by running something. Exit 0 = every arm came out
# as this drive declares; exit 2 = an anchor moved and the drive could not measure.
# All scratch is under ${TMPDIR:-/tmp}, never inside the repository.
# =============================================================================================
set -uo pipefail
REPO=${T442_REPO:-$(git rev-parse --show-toplevel)} || exit 2
SWEEP="$REPO/.softhouse/capture/t363-oracle-baseline/instruments/casualty-sweep.sh"
PATCH="$REPO/.softhouse/capture/t424/patches/FU-T386-7-red-drive-must-report-failure.AMENDED-BY-T424.patch"
T381="$REPO/.softhouse/capture/t381-t379-conditions/instruments/t381-red-drives.sh"
SUBJ_REL='.softhouse/capture/t363-oracle-baseline/instruments/casualty-sweep.sh'
FAILED=0
check() {
  printf '  %-56s expected=%-14s actual=%-14s %s\n' "$1" "$2" "$3" \
    "$( if [ "$2" = "$3" ]; then echo OK; else echo '*** DRIVE DISAGREES'; fi )"
  [ "$2" = "$3" ] || FAILED=$((FAILED+1))
}
need() { [ -r "$1" ] || { echo "REFUSED: cannot read $1" >&2; exit 2; }; }
need "$SWEEP"; need "$PATCH"; need "$T381"

W=$(mktemp -d "${TMPDIR:-/tmp}/t442-lows.XXXXXXXX") || exit 2
case "$W" in "$REPO"/*) echo "REFUSED: scratch inside the repo" >&2; exit 2 ;; esac
trap 'rm -rf "$W"' EXIT
echo "host    : $(uname -srm)  bash $BASH_VERSION  $(git --version)"
echo "scratch : $W  (outside the repository)"
echo

# =============================================================================================
echo "=============================================================================="
echo "C-T440-4 -- the \`pipefail\` sentence is over-broad, and the abort misattributes"
echo "=============================================================================="
anchor='set -o pipefail` does NOT surface a'
ln=$(grep -n -F -- "$anchor" "$SWEEP" | cut -d: -f1 | tr '\n' ' ')
[ -n "$ln" ] || { echo "REFUSED: the pipefail sentence is not where it was (anchor absent)" >&2; exit 2; }
echo "the sentence under test, quoted from ${SWEEP#$REPO/}:$ln"
grep -n -A3 -F -- "$anchor" "$SWEEP" | sed 's/^/    /'
echo

# Extract the SHIPPED guard block by content and substitute ONLY its producer. What is driven
# below is the file's own bytes, not a paraphrase of them.
start=$(grep -n -F -- 'SWEEP_CORPUS_N=$(git ls-files .softhouse | grep -c .)' "$SWEEP" | head -1 | cut -d: -f1)
[ -n "$start" ] || { echo "REFUSED: the corpus-count block moved" >&2; exit 2; }
sed -n "${start},$((start+15))p" "$SWEEP" > "$W/block.raw"
sed 's|git ls-files \.softhouse|eval "$T442_PRODUCER"|' "$W/block.raw" > "$W/block.sh"
grep -q 'T442_PRODUCER' "$W/block.sh" || { echo "REFUSED: producer substitution was a no-op" >&2; exit 2; }
echo "shipped block driven (producer substituted, everything else verbatim):"
sed 's/^/    | /' "$W/block.sh"
echo

drive_block() { # drive_block <producer>
  T442_PRODUCER="$1" bash -c '
    set -uo pipefail
    . '"$W"'/block.sh
    echo "CAPTURED=[$SWEEP_CORPUS_N] rc=$_corpus_rc"
    exit 0' 2>"$W/err"; echo "exit=$?"
}

echo "-- ARM 1: the producer fails 128 AFTER emitting lines (the case the sentence misses)"
r1=$(drive_block 'printf "a\nb\nc\n"; exit 128')
e1=$(sed -n '1p' "$W/err")
printf '    %s   %s\n' "$r1" "$(grep -c '' "$W/err") stderr line(s)"
sed 's/^/    stderr| /' "$W/err"
a1_msg=$(grep -c -F 'COUNT DID NOT RUN' "$W/err")
a1_exit=${r1##*exit=}
echo
echo "-- ARM 2: the producer fails 128 with NO output (the case the sentence describes)"
r2=$(drive_block 'exit 128')
printf '    %s\n' "$r2"
sed 's/^/    stderr| /' "$W/err"
a2_msg=$(grep -c -F 'tracks ZERO files' "$W/err")
echo
echo "-- ARM 3: the COUNT ITSELF fails (grep rc>=2) -- the case the abort message is FOR"
r3=$(T442_PRODUCER='printf "a\n"' bash -c '
    set -uo pipefail
    SWEEP_CORPUS_N=$(eval "$T442_PRODUCER" | grep -c -E "["); _corpus_rc=$?
    echo "CAPTURED=[$SWEEP_CORPUS_N] rc=$_corpus_rc"' 2>/dev/null)
printf '    %s\n' "$r3"
echo
# primitives, so the mechanism is visible independently of the shipped block
p_out=$( { printf 'a\nb\nc\n'; exit 128; } | grep -c . ); p_rc=$?
q_out=$( { exit 128; } | grep -c . ); q_rc=$?
printf '  primitive: (3 lines; exit 128) | grep -c .  -> captured=[%s] rc=%s\n' "$p_out" "$p_rc"
printf '  primitive: (no output; exit 128) | grep -c . -> captured=[%s] rc=%s\n' "$q_out" "$q_rc"
check "with output, pipefail surfaces git's 128"  "128" "$p_rc"
check "with output, the count is the real count"    "3" "$p_out"
check "with NO output, the rightmost non-zero is grep's 1" "1" "$q_rc"
check "with NO output, the count is 0"              "0" "$q_out"
check "ARM 1 aborts with COUNT DID NOT RUN"         "1" "$a1_msg"
check "ARM 1 exit status"                           "2" "$a1_exit"
check "ARM 2 aborts on the VALUE test instead"      "1" "$a2_msg"
echo
echo "  VERDICT. The sentence is true ONLY when \`git ls-files\` fails with NO OUTPUT. With"
echo "  output, pipefail's rightmost non-zero IS git's 128, the status test fires, and the abort"
echo "  says 'the corpus COUNT DID NOT RUN' -- but the count ran; the PRODUCER failed. It is"
echo "  FAIL-CLOSED, so it is not a hole: it is a message stating the wrong cause, one line"
echo "  below a comment that exists to correct a message that stated the wrong cause."
echo "  NARROWED SENTENCE PROPOSED (not applied -- casualty-sweep.sh is not this task's grant):"
echo "    'set -o pipefail does not surface a failing \`git ls-files\` WHEN GIT FAILS WITHOUT"
echo "     OUTPUT: grep -c . then exits 1 and 1 is the rightmost non-zero. If git fails AFTER"
echo "     emitting lines, grep exits 0, git's own 128 IS the rightmost non-zero, and the"
echo "     status test below fires -- correctly aborting, but under a message that names the"
echo "     count rather than the producer.'"
echo

# =============================================================================================
echo "=============================================================================="
echo "C-T440-5 -- an exported T381_DRIVE_INNER disables the amended guard entirely"
echo "=============================================================================="
# WHERE THE GUARD ACTUALLY LIVES. Established by grep, not assumed: the amendment ships as a
# PATCH ARTEFACT and is NOT applied to the live instrument.
live=$(grep -c -F 'T381_DRIVE_INNER' "$T381"); live_rc=$?
[ "$live_rc" -ge 2 ] && { echo "REFUSED: cannot grep $T381" >&2; exit 2; }
printf '  occurrences of T381_DRIVE_INNER in the LIVE t381-red-drives.sh : %s\n' "$live"
printf '  occurrences in the shipped patch                              : %s\n' \
  "$(grep -c -F 'T381_DRIVE_INNER' "$PATCH")"
check "the amended guard is NOT applied to the live file" "0" "$live"
echo "  So the bypass is a property of a PROPOSED patch, not of anything that runs today"
echo "  (P-45 read the other way round: unwired, so it grades nothing yet -- which is exactly"
echo "  when the surface is cheapest to close)."
echo

# Build a minimal specimen carrying the guard text taken FROM THE PATCH, plus a body with one
# failing arm and the sentinel. The guard is the SHIPPED bytes of the patch's preamble hunk; only
# the body is synthetic. GREEN is driven from the patch as it ships; RED is reconstructed from it
# by REVERSING the repair, and the reversal is refused if it changes nothing.
extract_guard() { # extract_guard <patch> <outfile> -- every added line of the FIRST hunk
  awk '/^@@ /{h++} h==1 && /^\+/ && !/^\+\+\+/ {sub(/^\+/,""); print}' "$1" > "$2"
  grep -c '' "$2"
}
n=$(extract_guard "$PATCH" "$W/guard-new.sh")
[ "$n" -gt 40 ] || { echo "REFUSED: guard extraction returned $n lines" >&2; exit 2; }
printf '  guard text extracted from the patch preamble hunk: %s lines\n' "$n"
grep -q 't424-inner:$PPID' "$W/guard-new.sh" || {
  echo "REFUSED: the patch does not carry the T442 repair -- nothing to grade" >&2; exit 2; }

# ---- reconstruct the PRE-REPAIR shape: drop the refusal block, restore the flag marker --------
python3 "$REPO/.softhouse/capture/t424/instruments/t442-unrepair-guard.py" \
        "$W/guard-new.sh" "$W/guard-old.sh" || exit 2
o_n=$(grep -c '' "$W/guard-old.sh")
printf '  pre-repair shape reconstructed                   : %s lines (%s fewer)\n' \
  "$o_n" "$((n - o_n))"
[ "$o_n" -lt "$n" ] || { echo "REFUSED: the reversal was a no-op" >&2; exit 2; }

make_specimen() { # make_specimen <guardfile> <arm text> <outfile>
  { echo '#!/usr/bin/env bash'
    echo 'set -uo pipefail'
    cat "$1"
    echo "echo \"ARM 1: $2\""
    echo 'echo "END OF DRIVES."'
    echo 'exit 0'
  } > "$3"
  bash -n "$3" || return 2
}
make_specimen "$W/guard-old.sh" 'DID NOT REPRODUCE' "$W/spec-old.sh"   || exit 2
make_specimen "$W/guard-new.sh" 'DID NOT REPRODUCE' "$W/spec-new.sh"   || exit 2
make_specimen "$W/guard-new.sh" 'reproduced'        "$W/spec-clean.sh" || exit 2

echo
echo "-- RED: the guard BEFORE the T442 repair (T424's shape)"
env -u T381_DRIVE_INNER bash "$W/spec-old.sh" >"$W/o1" 2>&1; o1=$?
T381_DRIVE_INNER=1 bash "$W/spec-old.sh" >"$W/o2" 2>&1; o2=$?
printf '    normal invocation                : exit %s\n' "$o1"
printf '    with T381_DRIVE_INNER=1 exported : exit %s   <- the grader never runs\n' "$o2"
check "RED: normal invocation CATCHES the failing arm" "1" "$o1"
check "RED: the env var BYPASSES it (exit 0)"          "0" "$o2"

echo
echo "-- GREEN: the guard AS THE PATCH NOW SHIPS IT"
echo "   JUDGEMENT (the question T440 asked -- should it be reachable at all?): NO. The marker"
echo "   exists only to tell the re-exec'd child that it is the inner run, and the child can"
echo "   verify that for itself: the outer publishes its own pid, the inner requires the marker"
echo "   to name its \$PPID. Anything else is exit 2 -- fail-CLOSED where the old shape was open."
env -u T381_DRIVE_INNER bash "$W/spec-new.sh" >"$W/o3" 2>&1; o3=$?
T381_DRIVE_INNER=1 bash "$W/spec-new.sh" >"$W/o4" 2>&1; o4=$?
T381_DRIVE_INNER="t424-inner:1" bash "$W/spec-new.sh" >"$W/o5" 2>&1; o5=$?
env -u T381_DRIVE_INNER bash "$W/spec-clean.sh" >"$W/o6" 2>&1; o6=$?
printf '    normal invocation, FAILING arm        : exit %s\n' "$o3"
printf '    with T381_DRIVE_INNER=1 exported      : exit %s   <- REFUSED, not bypassed\n' "$o4"
printf '    with a forged marker t424-inner:1     : exit %s   <- REFUSED\n' "$o5"
printf '    HEALTHY CONTROL, clean body           : exit %s\n' "$o6"
sed 's/^/    | /' "$W/o4"
check "GREEN: normal invocation still CATCHES the arm" "1" "$o3"
check "GREEN: T381_DRIVE_INNER=1 is REFUSED (exit 2)"  "2" "$o4"
check "GREEN: a forged marker is REFUSED (exit 2)"     "2" "$o5"
check "GREEN: a clean drive still passes (exit 0)"     "0" "$o6"
echo
echo "  VERDICT: closed. The patch in patches/ carries the repair; the live instrument does not"
echo "  carry the guard at all yet, so nothing that runs today is affected either way."
echo

# =============================================================================================
echo "=============================================================================="
echo "C-T440-6 -- what BEFORE_REF=main actually does, MEASURED, on the tree I have"
echo "=============================================================================="
# T424's Unverified section says the drive "refuses (BEFORE and AFTER are the same file)".
# T440 corrected that to "aborts at D-R2, exit 4". BOTH are measured here rather than believed,
# because which one is true is a property OF THE TREE, and that is the finding.
b_main=$(git -C "$REPO" rev-parse "main:$SUBJ_REL" 2>/dev/null)
b_head=$(git -C "$REPO" rev-parse "HEAD:$SUBJ_REL" 2>/dev/null)
printf '  blob of the subject at main : %s\n' "${b_main:-<unresolved>}"
printf '  blob of the subject at HEAD : %s\n' "${b_head:-<unresolved>}"
printf '  the two refs carry the same subject file : %s\n' \
  "$( [ -n "$b_main" ] && [ "$b_main" = "$b_head" ] && echo YES || echo no )"
echo

( cd "$REPO" && BEFORE_REF=main bash "$T381" ) > "$W/t381-main.txt" 2>&1; m_rc=$?
tail -4 "$W/t381-main.txt" | sed 's/^/    | /'
printf '    BEFORE_REF=main      exit = %s\n' "$m_rc"
m_same=$(grep -c -F 'SAME FILE' "$W/t381-main.txt")
m_dr2=$(grep -c -F 'D-R2 patch: expected' "$W/t381-main.txt")
echo
( cd "$REPO" && BEFORE_REF=964b532e bash "$T381" ) > "$W/t381-964.txt" 2>&1; o_rc=$?
tail -3 "$W/t381-964.txt" | sed 's/^/    | /'
printf '    BEFORE_REF=964b532e  exit = %s\n' "$o_rc"
o_dr2=$(grep -c -F 'D-R2 patch: expected' "$W/t381-964.txt")
echo
check "BEFORE_REF=main exit status"            "2" "$m_rc"
check "BEFORE_REF=main aborts on SAME FILE"    "1" "$m_same"
check "BEFORE_REF=main never reaches D-R2"     "0" "$m_dr2"
check "BEFORE_REF=964b532e exit status"        "4" "$o_rc"
check "BEFORE_REF=964b532e aborts at D-R2"     "1" "$o_dr2"
echo
echo "  FINDING F-T442-1 -- C-T440-6 DOES NOT REPRODUCE ON THIS TREE, AND T424'S ORIGINAL"
echo "  SENTENCE DOES. On the merged tree, main and HEAD carry the SAME subject file, so the"
echo "  drive aborts exit 2 with 'BEFORE and AFTER are the SAME FILE' -- which is exactly what"
echo "  T424 wrote. T440 measured exit 4 at D-R2 on T424's own branch and on the merge result as"
echo "  it then stood, where the two refs still differed; that measurement is reproduced here"
echo "  with BEFORE_REF=964b532e, which does abort at D-R2 exit 4."
echo "  So neither sentence is wrong -- BOTH ARE TREE-DEPENDENT AND NEITHER SAYS SO, which is the"
echo "  same defect as F-T424-N1 (a present-tense measurement carrying its own recipe) and as"
echo "  C-T440-1 (a record that stopped matching its code). CORRECTED WORDING, tree-qualified:"
echo "    'The drive cannot be run to completion on any ref available here. With BEFORE_REF=main"
echo "     it aborts exit 2 -- BEFORE and AFTER are the same file -- WHENEVER main and HEAD carry"
echo "     the same casualty-sweep.sh, which is the case on the merged tree; where they differ it"
echo "     reaches D-R2 and aborts exit 4 (expected 1 anti-calibration search line in BEFORE,"
echo "     found 0), as BEFORE_REF=964b532e still does. Either way FU-T386-7's guard has nothing"
echo "     to grade yet, which is the substantive claim and it stands.'"
echo

echo "=============================================================================="
printf 'T442-LOWS-RESULT: disagreements=%s\n' "$FAILED"
if [ "$FAILED" -gt 0 ]; then echo "*** THIS DRIVE FAILED."; exit 1; fi
echo "Every arm came out as declared."
exit 0
