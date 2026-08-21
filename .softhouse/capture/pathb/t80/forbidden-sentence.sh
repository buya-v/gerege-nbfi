#!/bin/sh
# T80 — the single sentence this whole task exists to make honest.
#
# T77's exploit made the rig print
#     PASS  effective rounding mode canary: period-1 interest 20925.05 (= HALF_UP)
# on the HALF_EVEN `default` tenant, with a request that was not a half-minor-unit tie.  A reader
# believes that sentence; it is the strongest claim the rig makes.  It must therefore appear ONLY
# in a transcript that (a) names tenant 'gerege' and (b) shows the canary DIGEST COMPARISON passing.
#
# This scans every committed T80 transcript and fails if that co-occurrence is ever violated.
#
# T99 CORRECTION — IT PASSED VACUOUSLY ON ZERO FILES.  Both `for` patterns are globs; when a glob
# matches nothing the shell passes the pattern through literally, `[ -f "$f" ] || continue` skips
# it, the loop body never executes, `bad` stays 0 and this script printed
#     violations: 0
#     RESULT: the HALF_UP claim is never made except on tenant gerege with the pinned canary.
# and exited 0 HAVING INSPECTED NOTHING.  Reproduced against main's bytes in t99/out/f3-prefix-*:
# an empty out/ directory, 0 files, exit 0, that sentence printed.  A standing check that reports
# success when it read no input is the P-22 defect class this run keeps finding — a guard that
# cannot fail is worse than no guard, because it is believed.
#
# Two counters now have to be non-zero, and each is a different way of being vacuous:
#   inspected   — files the globs actually resolved to.  Zero means the evidence is gone, the
#                 script was moved, or a glob was edited; it is an ERROR, not a pass.
#   adjudicated — files in which the guarded sentence actually appears, so the co-occurrence rule
#                 was really applied.  Zero means every file was 'absent' and the rule decided
#                 nothing; that is equally vacuous and equally an ERROR.
# Neither weakens the check T85 exercised: on the committed evidence it still reports 27 inspected,
# 8 adjudicated, 0 violations, and it still fires on a planted violation.
#
# Exit:  0 = inspected>0, adjudicated>0, violations=0
#        1 = at least one violation
#        2 = the check was vacuous (inspected==0 or adjudicated==0) — NOT a pass
set -u
T80=$(cd "$(dirname "$0")" && pwd)
O=$T80/out
S='PASS  effective rounding mode canary'
D='PASS  canary request pinned by DIGEST COMPARISON'
bad=0
inspected=0
adjudicated=0
for f in "$O"/attack-*.txt "$O"/*/preconditions.txt; do
  [ -f "$f" ] || continue
  inspected=$((inspected+1))
  if LC_ALL=C grep -qaF "$S" "$f"; then
    adjudicated=$((adjudicated+1))
    if LC_ALL=C grep -qaF "$D" "$f" && LC_ALL=C grep -qa "tenant 'gerege'" "$f" \
       && ! LC_ALL=C grep -qa "tenant 'default'" "$f"; then
      echo "OK        $f — canary PASS is accompanied by a passing digest pin, tenant gerege"
    else
      echo "VIOLATION $f — the canary PASS appears WITHOUT a passing digest pin, or not on gerege"
      bad=$((bad+1))
    fi
  else
    echo "absent    $f"
  fi
done
echo
echo "files inspected: $inspected"
echo "files carrying the guarded sentence (rule actually applied): $adjudicated"
echo "violations: $bad"
if [ "$inspected" -eq 0 ]; then
  echo "ERROR: this check INSPECTED NOTHING — no file matched $O/attack-*.txt or $O/*/preconditions.txt." >&2
  echo "A standing check that reports success on an empty file set is worse than no check, because it" >&2
  echo "is believed.  This is NOT a pass: find the evidence, or fix the globs." >&2
  exit 2
fi
if [ "$adjudicated" -eq 0 ]; then
  echo "ERROR: $inspected file(s) were read and NOT ONE of them contains the guarded sentence" >&2
  echo "'$S', so the co-occurrence rule adjudicated nothing.  The check is vacuous.  This is NOT a pass:" >&2
  echo "the transcripts that make the HALF_UP claim are missing from $O." >&2
  exit 2
fi
[ "$bad" = "0" ] || exit 1
echo "RESULT: the HALF_UP claim is never made except on tenant gerege with the pinned canary."
echo "        ($adjudicated of $inspected inspected transcripts make the claim; all $adjudicated carry a passing digest pin on tenant gerege.)"
exit 0
