#!/usr/bin/env bash
# =============================================================================================
# T424, part 3 -- THE OTHER HALF OF THE NEIGHBOUR HUNT.
#
# Defect 1 was a SHIPPED SOURCE COMMENT whose stated cause was false. Its neighbours are other
# shipped comments in this harness that state a mechanical cause I can falsify in one drive.
#
# I did not try to grade every comment in a 5,357-line file. I selected the ones that make a
# CHECKABLE claim about tool or shell semantics -- the class the F-2 comment belonged to -- by
# searching `conformance.sh` for comment lines matching
#     ^#.*(returns? [0-9]|exits? [0-9]|rc *= *[0-9]|prints? (0|nothing|empty)|pipefail|PIPESTATUS)
# (60+ lines), then keeping the ones whose truth does not depend on a machine I do not have.
# Each claim below is quoted, located BY CONTENT, and driven. Claims I could not settle on this
# host are marked UNDRIVEN rather than given a plausible answer.
#
# Exit 0 = every claim I drove came out as this drive declares. A claim coming out FALSE is a
# FINDING, and is declared as such below -- it does not fail the drive; a claim coming out
# differently from what this drive DECLARES does.
# =============================================================================================
set -uo pipefail
REPO=${T424_REPO:-$(git rev-parse --show-toplevel)}
C="$REPO/.softhouse/conformance.sh"
FAILED=0
[ -r "$C" ] || { echo "REFUSED: cannot read $C" >&2; exit 2; }
echo "subject: $C  ($(grep -c '' "$C") lines, sha256 $(shasum -a 256 "$C" | cut -c1-16))"
echo

locate() { # locate <fixed string> -- prints the line number(s), refuses if absent
  local n
  n=$(grep -c -F "$1" "$C"); local rc=$?
  if [ "$rc" -ge 2 ] || [ "$n" -lt 1 ]; then
    echo "REFUSED: anchor not found (rc=$rc n=$n): $1" >&2; exit 2
  fi
  grep -n -F "$1" "$C" | cut -d: -f1 | tr '\n' ' '
}

check() { # check <label> <expected> <actual>
  printf '  %-52s expected=%-10s actual=%-10s %s\n' "$1" "$2" "$3" \
    "$( if [ "$2" = "$3" ]; then echo OK; else echo '*** DRIVE DISAGREES'; fi )"
  if [ "$2" != "$3" ]; then FAILED=$((FAILED+1)); fi
}

WORK=$(mktemp -d "${TMPDIR:-/tmp}/t424-claims.XXXXXXXX") || exit 2
trap 'rm -rf "$WORK"' EXIT

echo "=============================================================================="
echo "CLAIM 1 -- 'In a UTF-8 locale BSD grep goes blind to the part of ONE LINE at and"
echo "            to the RIGHT of an invalid byte: count 0, exit 1, NO diagnostic.'"
echo "  at line(s): $(locate 'exit 1, NO diagnostic')"
echo "=============================================================================="
printf 'alpha \xE2 beta 1.5 gamma\n' > "$WORK/badbyte.txt"
u_n=$(LC_ALL=en_US.UTF-8 /usr/bin/grep -c '1\.5' "$WORK/badbyte.txt" 2>"$WORK/u.err"); u_rc=$?
c_n=$(LC_ALL=C        /usr/bin/grep -c '1\.5' "$WORK/badbyte.txt" 2>"$WORK/c.err"); c_rc=$?
a_n=$(LC_ALL=en_US.UTF-8 /usr/bin/grep -a -c '1\.5' "$WORK/badbyte.txt" 2>/dev/null); a_rc=$?
printf '  UTF-8 locale : count=%s rc=%s diagnostic=%s\n' "$u_n" "$u_rc" \
  "$( if [ -s "$WORK/u.err" ]; then cat "$WORK/u.err"; else echo NONE; fi )"
printf '  LC_ALL=C     : count=%s rc=%s\n' "$c_n" "$c_rc"
printf '  UTF-8 + -a   : count=%s rc=%s\n' "$a_n" "$a_rc"
check "UTF-8 goes blind (count 0, rc 1)"    "0 1" "$u_n $u_rc"
check "LC_ALL=C sees it (count 1, rc 0)"    "1 0" "$c_n $c_rc"
check "-a does NOT fix it (count 0, rc 1)"  "0 1" "$a_n $a_rc"
check "no diagnostic on stderr"             "0"   "$(wc -c < "$WORK/u.err" | tr -d ' ')"
echo "  VERDICT: the comment reproduces on this host, /usr/bin/grep $(/usr/bin/grep --version 2>&1 | head -1)"
echo

echo "=============================================================================="
echo "CLAIM 2 -- '\`CONFORMANCE_REPO_ROOT\` and \`-repo-root\` each occur ZERO times in it"
echo "            (measured on this file ... both returned 0, exit 1).'"
echo "  at line(s): $(locate 'each occur ZERO times in it')"
echo "=============================================================================="
n1=$(LC_ALL=C /usr/bin/grep -c 'CONFORMANCE_REPO_ROOT' "$C"); r1=$?
n2=$(LC_ALL=C /usr/bin/grep -c -- '-repo-root' "$C"); r2=$?
printf '  CONFORMANCE_REPO_ROOT : count=%s rc=%s\n' "$n1" "$r1"
printf '  -repo-root            : count=%s rc=%s\n' "$n2" "$r2"
# The claim is TRUE of executable lines and FALSE of the file, because the sentence stating it
# contains both tokens. Measure the executable-only count so the distinction is a number.
e1=$(awk '{t=$0; sub(/^[[:space:]]+/,"",t); if (t ~ /^#/ || t=="") next; print}' "$C" \
     | LC_ALL=C /usr/bin/grep -c 'CONFORMANCE_REPO_ROOT')
e2=$(awk '{t=$0; sub(/^[[:space:]]+/,"",t); if (t ~ /^#/ || t=="") next; print}' "$C" \
     | LC_ALL=C /usr/bin/grep -c -- '-repo-root')
printf '  executable (non-comment) lines only: CONFORMANCE_REPO_ROOT=%s  -repo-root=%s\n' "$e1" "$e2"
check "whole-file count is NOT zero any more" "yes" "$( if [ "$n1" -gt 0 ]; then echo yes; else echo no; fi )"
check "executable count is NOT zero either"   "yes" "$( if [ "$e1" -gt 0 ]; then echo yes; else echo no; fi )"
check "-repo-root still absent from the code"  "0"   "$e2"
echo "  FINDING F-T424-N1 -- the claim NO LONGER REPRODUCES, in both senses. The stated"
echo "  measurement is 'both returned 0, exit 1'; re-running it today returns a non-zero count"
echo "  for CONFORMANCE_REPO_ROOT on the whole file AND on executable lines only. It was true"
echo "  when written -- the paragraph describes the pre-repair hole -- and the repair it argues"
echo "  for is what made it false. But the sentence is PRESENT TENSE and carries its own"
echo "  reproduction recipe, so a reader who runs that recipe gets a contradiction and no way to"
echo "  tell a stale sentence from a regressed harness. Cause right, TENSE wrong -- the same"
echo "  shape as F-2, where the mechanism was right and the attribution wrong."
echo "  NOT EDITED: conformance.sh is contended this fire and this region is not T424's."
echo "  Reported by name for its owner. Counts deliberately not pinned here (P-86)."
echo

echo "=============================================================================="
echo "CLAIM 3 -- '\`git grep\` exits 1 on NO MATCH and >1 on ERROR, so the 1 is an"
echo "            ABSENCE and not a failure.'"
echo "  at line(s): $(locate 'git grep\` exits 1 on NO MATCH')"
echo "=============================================================================="
cd "$REPO" || exit 2
git grep -q 'zzq-no-such-token-t424' -- .softhouse > /dev/null 2>&1; g_absent=$?
git grep -q -E '[' -- .softhouse > /dev/null 2>&1; g_error=$?
# A token that is REALLY in CLAUDE.md. My first spelling of this arm used 'CLAUDE', which is
# not in that file's body, so the healthy control scored rc=1 and looked like the no-match arm.
# Recorded because it is the same defect as everything else here: a control that cannot tell a
# real absence from a broken probe.
git grep -q 'Gerege' -- CLAUDE.md > /dev/null 2>&1; g_hit=$?
printf '  no match        : rc=%s\n' "$g_absent"
printf '  invalid pattern : rc=%s\n' "$g_error"
printf '  match           : rc=%s\n' "$g_hit"
check "no match -> 1"         "1"   "$g_absent"
check "error   -> >1"         "yes" "$( if [ "$g_error" -gt 1 ]; then echo yes; else echo no; fi )"
check "match   -> 0"          "0"   "$g_hit"
echo "  VERDICT: reproduces. git $(git --version | awk '{print $3}')"
echo

echo "=============================================================================="
printf 'T424-COMMENT-CLAIMS-RESULT: disagreements=%s\n' "$FAILED"
if [ "$FAILED" -gt 0 ]; then echo "*** THIS DRIVE FAILED."; exit 1; fi
echo "Every claim came out as declared."
exit 0
