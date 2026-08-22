#!/usr/bin/env bash
# T252 instrument 10 -- IS THE THIRD SITE REAL?
#
# T248 reported `.softhouse/reviews/a2-34-review-a2-15/rederive-provenance.sh` as a
# PROBABLE third live fail-open site and did not confirm it. "Probable" is not a finding.
# This instrument RUNS the script and reports, from the run itself:
#     * its exit code                      -- "fails closed" means non-zero; anything else is a lie
#     * whether its P-72 calibration line printed a number at all
#     * the exact sentence it prints about a corpus it never reached
#
# THIS FILE WAS ITSELF CAUGHT BY THE LINTER IT SHIPS ALONGSIDE, AND REPAIRED RATHER THAN
# PINNED. Its first draft reported absences with `... || echo "  (not printed)"` in five
# places -- the C2a shape exactly, in the instrument written to expose the C2 class. `grep`
# exits 1 for "no match" and >=2 for an ERROR (a missing file, a bad flag, an unreadable
# byte), and an arm that prints the same reassuring parenthesis for both is a negative
# nobody measured. `sift` below DISCRIMINATES the two and ABORTS on an error, so every
# "(TRUE ZERO)" in the transcript is a searched zero. The pin is a frontier, not an amnesty,
# and that applies first of all to the author invoking it.
#
# ENGINE (P-33/P-53): every search is `LC_ALL=C /usr/bin/grep` over the CAPTURED stdout of
# the run -- the absolute path because bare `grep` in an agent shell is a shadowed ugrep with
# six --exclude-dir flags prepended (P-75, 33% recall measured), and `rg` has no binary at
# all. `git grep` is not used: the subject here is RUN OUTPUT in a temp file, not tracked
# content.
#
# CALIBRATION (P-72): a known POSITIVE and a known NEGATIVE are swept over the captured
# stdout before any zero below is believed, and the negative is a SUPERSTRING of the
# positive -- a negative that is a SUBSTRING of the positive matches both and proves nothing.
set -euo pipefail

R="$(git rev-parse --show-toplevel)"
cd "$R" || { echo "T252-10 ABORT: cannot enter repo root"; exit 2; }

SUBJECT=".softhouse/reviews/a2-34-review-a2-15/rederive-provenance.sh"
[ -f "$SUBJECT" ] || { echo "T252-10 ABORT: subject absent: $SUBJECT"; exit 2; }

OUT="$(mktemp -t t252-site-out)"
ERR="$(mktemp -t t252-site-err)"

# sift <label> <grep-flag> <pattern> <file>
# exit 0 -> print the hits.  exit 1 -> say so, and say it was a SEARCHED zero.
# exit >=2 -> the engine failed; this instrument measured nothing and refuses to imply it did.
sift() {
  local label="$1" flag="$2" pat="$3" f="$4" out rc
  set +e
  out="$(LC_ALL=C /usr/bin/grep -n -a "$flag" "$pat" "$f")"
  rc=$?
  set -e
  case "$rc" in
    0) printf '%s\n' "$out" ;;
    1) echo "  ($label: TRUE ZERO -- grep exited 1, it searched and matched nothing)" ;;
    *) echo "  *** $label: grep exited $rc. That is an ERROR, not a zero. This instrument"
       echo "  *** measured NOTHING here and will not print a negative it did not measure."
       exit 2 ;;
  esac
}

# count <flag> <pattern> <file> -- a COUNT, with the same discrimination. `grep -c` prints 0
# and exits 1 on no-match, so 0 and "engine died" are one byte apart without this.
count() {
  local flag="$1" pat="$2" f="$3" out rc
  set +e
  out="$(LC_ALL=C /usr/bin/grep -c -a "$flag" "$pat" "$f")"
  rc=$?
  set -e
  case "$rc" in
    0|1) printf '%s' "${out:-0}" ;;
    *) printf 'ENGINE-ERROR(%s)' "$rc"; return 0 ;;
  esac
}

echo "T252 -- THIRD SITE VERIFICATION"
echo "commit  : $(git rev-parse HEAD)"
echo "subject : $SUBJECT"
echo "engine  : /usr/bin/grep $(/usr/bin/grep --version 2>&1 | head -1)  [-a, LC_ALL=C]"
echo

echo "### 1. THE DECLARED PATH AND WHETHER IT EXISTS"
DEAD="$(LC_ALL=C /usr/bin/sed -n 's/^R=\(\/.*\)$/\1/p' "$SUBJECT")"
echo "  R= $DEAD"
if [ -e "$DEAD" ]; then
  echo "  EXISTS: yes -- the site is NOT dead on this machine; the rest of this run means nothing."
else
  echo "  EXISTS: NO. The corpus this script measures has not existed since its worktree was pruned."
fi
echo

echo "### 2. THE SHELL OPTIONS IN FORCE (a 'fails closed' claim lives or dies here)"
sift "no \`set\` line at all" -E '^[[:space:]]*set[[:space:]]' "$SUBJECT"
echo "  lines matching \`set -...e...\` (errexit): $(count -E '^[[:space:]]*set[[:space:]]+-[a-z]*e' "$SUBJECT")"
echo "  the entry line:"
sift "no \`cd \"\$R\"\`" -F 'cd "$R"' "$SUBJECT"
echo

echo "### 3. RUN IT. Exit code and captured output are the evidence."
set +e
bash "$SUBJECT" >"$OUT" 2>"$ERR"
RC=$?
set -e
echo "  EXIT CODE = $RC"
if [ "$RC" -eq 0 ]; then
  echo "  => it exits ZERO. A reader, a CI step and a reviewer all read that as SUCCESS."
else
  echo "  => it exits non-zero, i.e. it really does fail closed and T248's hedge resolves NEGATIVE."
fi
echo

echo "### 4. CALIBRATION OF THIS INSTRUMENT (P-72), over the captured stdout"
echo "  CAL+  'PROMOTED CELLS SWEPT'          (must be >0) : $(count -F 'PROMOTED CELLS SWEPT' "$OUT")"
echo "  CAL-  'PROMOTED CELLS SWEPT ZZZ_NONE' (must be  0) : $(count -F 'PROMOTED CELLS SWEPT ZZZ_NONE' "$OUT")"
echo "  (the negative is a SUPERSTRING of the positive, so it cannot match by containment;"
echo "   a negative that is a SUBSTRING of the positive matches both and proves nothing.)"
echo

echo "### 5. THE FALSE CLAIM ITSELF -- and note its TYPE"
sift "the false count was not printed" -F 'PROMOTED CELLS SWEPT' "$OUT"
echo
echo "  Every widening in this linter so far -- C1, C2a, C2b -- keys on REASSURING ENGLISH."
echo "  This claim contains none. It is a COUNT. \`NOT BYTE-PRESENT / ARITHMETIC FAIL: 0\`"
echo "  printed by an instrument that never reached its corpus is byte-identical to the same"
echo "  line printed after a real, complete, passing sweep."
echo

echo "### 6. WHAT ELSE IT PRINTED ABOUT A CORPUS IT NEVER REACHED"
echo "  -- the three section headers below are followed by NOTHING, because every python"
echo "     block globs an absent directory and iterates an empty list:"
sift "no section headers" -F '########' "$OUT"
echo
echo "  -- the P-72 CALIBRATION line the script itself insists on:"
sift "no CAL+ line" -F 'CAL+' "$OUT"
echo "     The count after 'CAL+ ... : ' is EMPTY. The script's own calibration produced no"
echo "     number, which is the one thing that should have stopped it, and it carried on."
echo

echo "### 7. STDERR -- the whole truth, which nothing in the exit code or stdout carries"
LC_ALL=C /usr/bin/sed -n '1,40p' "$ERR"
echo
echo "  stderr lines: $(count -F '' "$ERR")"
echo "  On a graded run stderr is where nobody looks and the exit code is where everybody does."

rm -f "$OUT" "$ERR"
