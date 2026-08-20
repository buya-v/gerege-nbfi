#!/bin/sh
# T80 — proof for T85 F-1: a BREACHED attest.py run must leave the filesystem exactly as it found it.
#
# T85 showed that `python3 attest.py default emiloop` printed "no capture attempted, no attestation
# written" while having already stamped eleven `gerege` captures as `default` and replaced their
# HALF_UP precondition transcript with a breached HALF_EVEN one.  The emiloop set is the reachable
# victim because it is exempt from the directory-NAME check (its committed directory is `out/emiloop`,
# which cannot end in a tenant id without renaming committed evidence).
#
# This script runs the SAME invocation twice — once against the PRE-FIX attest.py restored from git,
# once against the fixed one — and diffs the digests of the committed set each time.  A proof that
# only shows the "after" cannot tell a fix from a no-op.
set -u
T80=$(cd "$(dirname "$0")" && pwd)
W=$(cd "$T80/.." && pwd)
O=$T80/out
E=$W/t36/out/emiloop
PREFIX_COMMIT=813acb1                     # T80's own pre-F-1 attest.py
cd "$W"

snap() { shasum -a 256 "$E"/* | sed "s|$W/||"; }

echo "=== T85 F-1 — a breached attest.py run must write NOTHING"
echo "run at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "victim set: t36/out/emiloop  (11 EL-* captures taken on tenant gerege, plus attestation and transcripts)"
echo

snap > "$O/.f1-before"
echo "--- BEFORE: $(wc -l < "$O/.f1-before" | tr -d ' ') files"
grep 'preconditions.txt' "$O/.f1-before"
echo "  stamp present: $( [ -f "$E/CAPTURED-FROM-TENANT" ] && echo yes || echo no )"
echo

# ---------------------------------------------------------------- 1. the PRE-FIX behaviour
cp "$W/t36/attest.py" "$O/.f1-fixed"
git show "$PREFIX_COMMIT:.softhouse/capture/pathb/t36/attest.py" > "$W/t36/attest.py"
echo "--- 1. PRE-FIX attest.py ($PREFIX_COMMIT), invocation: python3 t36/attest.py default emiloop"
python3 t36/attest.py default emiloop > "$O/.f1-out1" 2>&1
echo "EXIT=$?"
tail -2 "$O/.f1-out1" | sed 's/^/  /'
snap > "$O/.f1-after-prefix"
echo "  stamp now present: $( [ -f "$E/CAPTURED-FROM-TENANT" ] && echo "YES, contents: $(cat "$E/CAPTURED-FROM-TENANT")" || echo no )"
if diff -q "$O/.f1-before" "$O/.f1-after-prefix" > /dev/null; then
  echo "  RESULT: committed set UNCHANGED (unexpected — the defect did not reproduce)"
  prefix_broke=0
else
  echo "  RESULT: COMMITTED SET MUTATED BY A RUN THAT SAID IT WROTE NOTHING:"
  diff "$O/.f1-before" "$O/.f1-after-prefix" | sed 's/^/    /'
  echo "    transcript first line is now: $(head -1 "$E/preconditions.txt")"
  prefix_broke=1
fi
echo

# ------------------------------------------------------------------- restore the evidence
cp "$O/.f1-fixed" "$W/t36/attest.py"
rm -f "$E/CAPTURED-FROM-TENANT"
git checkout -- "$W/t36/out/emiloop"
snap > "$O/.f1-restored"
if diff -q "$O/.f1-before" "$O/.f1-restored" > /dev/null; then
  echo "--- evidence restored from git: all digests back to BEFORE"
else
  echo "--- WARNING: restore incomplete"; diff "$O/.f1-before" "$O/.f1-restored"
fi
echo

# ------------------------------------------------------------------ 2. the FIXED behaviour
echo "--- 2. FIXED attest.py, same invocation: python3 t36/attest.py default emiloop"
python3 t36/attest.py default emiloop > "$O/.f1-out2" 2>&1
echo "EXIT=$?"
tail -2 "$O/.f1-out2" | sed 's/^/  /'
snap > "$O/.f1-after-fixed"
echo "  stamp present: $( [ -f "$E/CAPTURED-FROM-TENANT" ] && echo "YES — FIX FAILED, contents: $(cat "$E/CAPTURED-FROM-TENANT")" || echo "no" )"
rc=0
if diff -q "$O/.f1-before" "$O/.f1-after-fixed" > /dev/null; then
  echo "  RESULT: committed set UNCHANGED — all $(wc -l < "$O/.f1-before" | tr -d ' ') digests identical, including preconditions.txt"
else
  echo "  RESULT: STILL MUTATING:"; diff "$O/.f1-before" "$O/.f1-after-fixed"; rc=1
fi
[ -f "$E/CAPTURED-FROM-TENANT" ] && rc=1
echo
echo "prefix-defect-reproduced=$prefix_broke   fixed-run-clean=$( [ "$rc" = 0 ] && echo yes || echo no )"
rm -f "$O/.f1-before" "$O/.f1-after-prefix" "$O/.f1-restored" "$O/.f1-after-fixed" "$O/.f1-fixed" "$O/.f1-out1" "$O/.f1-out2"
[ "$rc" = 0 ] || exit 1
[ "$prefix_broke" = 1 ] || exit 1
echo "RESULT: F-1 CLOSED — the defect reproduces on the pre-fix file and is absent after the fix."
exit 0
