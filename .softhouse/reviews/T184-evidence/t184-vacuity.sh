#!/bin/bash
# T184: P-35 vacuity + _run_capture_guard branch coverage, at HARNESS level.
# All mutations are made outside git-tracked content or restored byte-identically;
# sha256 of both guard scripts is asserted at the end.
. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh
W=/Users/buv/gerege-nbfi/.claude/worktrees/agent-ae0f13a1bbf7c82f8
cd "$W"
LIB="$W/.softhouse/capture/lib"
rm -rf "$W/.softhouse/capture/t184-probe"
cp "$LIB/check_wire_float_roundtrip.py" /tmp/t184-backup-wf.py
BEFORE_WF="$(shasum -a 256 "$LIB/check_wire_float_roundtrip.py" | cut -d' ' -f1)"
BEFORE_NC="$(shasum -a 256 "$LIB/check_no_narrow_catch.py" | cut -d' ' -f1)"

run() { bash .softhouse/conformance.sh > "$1" 2>&1; echo "EXIT=$?"; }

echo "########## V1: ZERO request bodies (capture tree hidden) — P-35 at harness level"
mv "$W/.softhouse/capture" "$W/.softhouse/capture-T184HIDDEN"
run /tmp/t184-v1.txt
grep -n 'CENSUS wire-float\|REFUSED — INSPECTED\|MISSING\|NO CENSUS\|A guard that inspects\|HARD guard\|probe =' /tmp/t184-v1.txt
mv "$W/.softhouse/capture-T184HIDDEN" "$W/.softhouse/capture"

echo
echo "########## V2: the guard SCRIPT is deleted — must be an ERROR, not a skip"
mv "$LIB/check_wire_float_roundtrip.py" /tmp/t184-moved-wf.py
run /tmp/t184-v2.txt
grep -n 'guard is MISSING\|cannot pass\|HARD guard\|probe =' /tmp/t184-v2.txt
mv /tmp/t184-moved-wf.py "$LIB/check_wire_float_roundtrip.py"

echo
echo "########## V3: the guard is a SILENT stub (exit 0, prints nothing) — must be an ERROR"
cat > "$LIB/check_wire_float_roundtrip.py" <<'PYEOF'
import sys
if '--selftest' in sys.argv:
    print('--- (stub) ---'); print('  -> exit 0'); sys.exit(0)
sys.exit(0)
PYEOF
run /tmp/t184-v3.txt
grep -n 'NO CENSUS LINE\|HARD guard\|probe =' /tmp/t184-v3.txt

echo
echo "########## V4: P-57 regression — CENSUS is line 1 followed by ~400KB. Must NOT invert."
cat > "$LIB/check_wire_float_roundtrip.py" <<'PYEOF'
import sys
if '--selftest' in sys.argv:
    print('--- (stub) ---'); print('  -> exit 0'); sys.exit(0)
print('CENSUS wire-float round-trip — stub, inspected 320 request bodies / 3976 numeric tokens '
      'across 6 capture rigs / 10 req directories')
for i in range(4000):
    print('filler line %06d %s' % (i, 'x' * 90))
sys.exit(0)
PYEOF
python3 "$LIB/check_wire_float_roundtrip.py" "$W" | wc -c
run /tmp/t184-v4.txt
grep -n 'NO CENSUS LINE\|CENSUS wire-float\|HARD guard\|probe =\|VERDICT' /tmp/t184-v4.txt

echo
echo "########## V5: a stub whose CENSUS line reports ZERO, exit 0 — does the HARNESS notice?"
cat > "$LIB/check_wire_float_roundtrip.py" <<'PYEOF'
import sys
if '--selftest' in sys.argv:
    print('--- (stub) ---'); print('  -> exit 0'); sys.exit(0)
print('CENSUS wire-float round-trip — inspected 0 request bodies / 0 numeric tokens '
      'across 0 capture rigs / 0 req directories under /nowhere')
sys.exit(0)
PYEOF
run /tmp/t184-v5.txt
grep -n 'CENSUS wire-float\|NO CENSUS\|HARD guard\|probe =\|VERDICT' /tmp/t184-v5.txt

cp /tmp/t184-backup-wf.py "$LIB/check_wire_float_roundtrip.py"
echo
echo "########## restore check"
AFTER_WF="$(shasum -a 256 "$LIB/check_wire_float_roundtrip.py" | cut -d' ' -f1)"
AFTER_NC="$(shasum -a 256 "$LIB/check_no_narrow_catch.py" | cut -d' ' -f1)"
echo "wf before=$BEFORE_WF after=$AFTER_WF"
echo "nc before=$BEFORE_NC after=$AFTER_NC"
[ "$BEFORE_WF" = "$AFTER_WF" ] && [ "$BEFORE_NC" = "$AFTER_NC" ] && echo "RESTORED OK" || echo "RESTORE FAILED"
git status --short
