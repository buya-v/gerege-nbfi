#!/bin/bash
# T169 — P-22 mutation drives. Prove each new guard CAN fail. Scratch copies only; nothing in the
# repository is edited by this script.
set -u
LIB=/Users/buv/gerege-nbfi/.claude/worktrees/agent-af1f5b7aebc97911d/.softhouse/capture/lib
W=/tmp/t169mut
rm -rf "$W"; mkdir -p "$W"
cp "$LIB/ThrewOutcome.java" "$LIB/ThrewOutcomeSelfTest.java" "$LIB/sweep_integrity.py" "$W/"

banner() { echo; echo "================ $1 ================"; }

banner "M1  isFatal() always false  -> a fatal throwable would be SWALLOWED"
sed 's/return t instanceof VirtualMachineError || t instanceof LinkageError;/return false;/' \
    "$LIB/ThrewOutcome.java" > "$W/M1_ThrewOutcome.java"
sed 's/"java.lang.ThreadDeath".equals(t.getClass().getName())/false/' "$W/M1_ThrewOutcome.java" > "$W/ThrewOutcome.java"
docker run --rm --user 0 --entrypoint sh -v "$W":/cap fineract:latest -c \
  'mkdir -p /tmp/c1 && javac -nowarn -d /tmp/c1 /cap/ThrewOutcome.java /cap/ThrewOutcomeSelfTest.java && java -cp /tmp/c1 ThrewOutcomeSelfTest' 2>&1 | grep -E "^FAIL|failures"
echo "self-test exit: ${PIPESTATUS[0]}"

banner "M2  isFatal() always true  -> a StackOverflowError would KILL the run instead of being recorded"
cp "$LIB/ThrewOutcome.java" "$W/ThrewOutcome.java"
sed -i.bak 's/if (t instanceof StackOverflowError) {\n            return false;/X/' "$W/ThrewOutcome.java"
python3 - "$W/ThrewOutcome.java" <<'PY'
import sys
p = sys.argv[1]
s = open(p).read()
s = s.replace("""        if (t instanceof StackOverflowError) {
            return false;
        }""", """        if (t instanceof StackOverflowError) {
            return true;   // MUTANT M2
        }""")
open(p, 'w').write(s)
PY
docker run --rm --user 0 --entrypoint sh -v "$W":/cap fineract:latest -c \
  'mkdir -p /tmp/c2 && javac -nowarn -d /tmp/c2 /cap/ThrewOutcome.java /cap/ThrewOutcomeSelfTest.java && java -cp /tmp/c2 ThrewOutcomeSelfTest' 2>&1 | grep -E "^FAIL|failures|Exception in thread"
echo "self-test exit: ${PIPESTATUS[0]}"

banner "M3  tally() counts a threw cell as an observation"
python3 - "$W/sweep_integrity.py" <<'PY'
import sys
p = sys.argv[1]
s = open(p).read()
s = s.replace("""        if outcome == THREW:
            t.threw += 1""", """        if False:   # MUTANT M3
            t.threw += 1""")
open(p, 'w').write(s)
PY
python3 "$W/sweep_integrity.py" --selftest 2>&1 | grep -E "^FAIL|failure|Traceback|IntegrityError" | head -8
echo "selftest exit: $?"

banner "M4  tally() drops a missing cell instead of counting it skipped"
cp "$LIB/sweep_integrity.py" "$W/sweep_integrity.py"
python3 - "$W/sweep_integrity.py" <<'PY'
import sys
p = sys.argv[1]
s = open(p).read()
s = s.replace("""        if cell is None:
            t.skipped += 1""", """        if cell is None:
            t.asked -= 1   # MUTANT M4: pretend it was never asked for""")
open(p, 'w').write(s)
PY
python3 "$W/sweep_integrity.py" --selftest 2>&1 | grep -E "^FAIL|failure" | head -8

banner "M5  assert_not_graded_as_observed() never refuses"
cp "$LIB/sweep_integrity.py" "$W/sweep_integrity.py"
python3 - "$W/sweep_integrity.py" <<'PY'
import sys
p = sys.argv[1]
s = open(p).read()
s = s.replace("""    if offenders:
        raise IntegrityError""", """    if False:
        raise IntegrityError""")
open(p, 'w').write(s)
PY
python3 "$W/sweep_integrity.py" --selftest 2>&1 | grep -E "^FAIL|failure" | head -8
echo
echo "ALL MUTATION DRIVES COMPLETE"
