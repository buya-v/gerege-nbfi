#!/usr/bin/env bash
# T409 -- DRIVE T390's OWN capsql.sh, RED and GREEN.
#
# T390's handoff declares as its third failure that capsql.sh first shipped without
# ON_ERROR_STOP=1, so psql exited 0 on a failed statement, and says "the fix is visible in q7's
# rc=3". EVERY committed transcript in that capture directory ends "-- psql rc=0", q7 included.
# So the claim is checked by RUNNING the subject, not by reading the transcript it cites.
#
# RED   : a statement naming a column that does not exist  -> must be NON-ZERO.
# GREEN : a statement that works                           -> must be 0.
# A checker that refuses everything and one that cannot fail are the same defect, so both.
#
# READ-ONLY: both statements are SELECTs; the red one cannot even be planned.
set -uo pipefail
W="${1:-/tmp/t409/capsql-drive}"
SUBJ="$W/capsql.sh"
[ -f "$SUBJ" ] || { echo "REFUSING: no subject at $SUBJ" >&2; exit 2; }
mkdir -p "$W/sql" "$W/out"
printf 'SELECT no_such_column FROM acc_gl_journal_entry LIMIT 1;\n' > "$W/sql/red-bad-column.sql"
printf 'SELECT 1 AS ok;\n' > "$W/sql/green-control.sql"

echo "T409 DRIVE of T390's capsql.sh -- $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "subject: $SUBJ  (extracted verbatim from softhouse/T390-baseline-attribution)"
echo "subject sha256: $(shasum -a 256 "$SUBJ" | awk '{print $1}')"
echo

bash "$SUBJ" red-bad-column; rrc=$?
bash "$SUBJ" green-control;  grc=$?

fail=0
if [ "$rrc" -ne 0 ]; then echo "  ok   RED   arm: bad statement -> rc=$rrc (non-zero, fails closed)"
else echo "  ***  RED   arm: bad statement -> rc=0 -- ON_ERROR_STOP IS NOT IN EFFECT"; fail=1; fi
if [ "$grc" -eq 0 ]; then echo "  ok   GREEN control: good statement -> rc=0"
else echo "  ***  GREEN control: good statement -> rc=$grc -- the checker refuses everything"; fail=1; fi

echo
echo "--- RED transcript ---";   cat "$W/out/red-bad-column.txt"
echo "--- GREEN transcript ---"; cat "$W/out/green-control.txt"
echo
[ "$fail" -eq 0 ] && echo "DRIVE VERDICT: capsql.sh fails closed on a failed statement (exit 0)." || echo "DRIVE VERDICT: FAILED (exit 1)."
exit "$fail"
