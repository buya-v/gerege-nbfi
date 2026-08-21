#!/bin/sh
# T138 — drive T115's prove-guards.sh RED, two ways, plus a MUTATION TEST of each
# guard leg: if the property the leg exists to protect were defeated, does the leg
# actually go red?  (P-22's standing question applied to T115's own additions.)
set -u
C=${1:?usage: r4-guards-red.sh <path to a git checkout of T115>}

echo "=================================================================="
echo "RED 1 — prove-guards.sh run from a NON-GIT export (T107's F-6 repro)"
echo "=================================================================="
X=/tmp/T138-nongit
rm -rf "$X"; mkdir -p "$X"
(cd "$C" && git archive HEAD) | tar -x -C "$X"
[ -d "$X/.git" ] && echo "UNEXPECTED: the export is a git repo" || echo "export at $X is NOT a git repo (no .git)"
echo "--- POST-fix (T115) prove-guards.sh from there:"
sh "$X/.softhouse/capture/t91/prove-guards.sh" 2>&1 | head -20
sh "$X/.softhouse/capture/t91/prove-guards.sh" >/dev/null 2>&1; echo "POST_EXIT=$?"
echo
echo "--- PRE-fix (T91) prove-guards.sh from the SAME non-git export:"
Y=/tmp/T138-nongit-pre
rm -rf "$Y"; mkdir -p "$Y"
(cd "$C" && git archive ccf3c14171dea52bd044d81d5ca67aba8054b74c) | tar -x -C "$Y"
sh "$Y/.softhouse/capture/t91/prove-guards.sh" 2>&1 | tail -25
sh "$Y/.softhouse/capture/t91/prove-guards.sh" >/dev/null 2>&1; echo "PRE_EXIT=$?"
echo

echo "=================================================================="
echo "RED 2 — a guard it grades is NEUTERED (verdict.sh replaced by 'exit 0')"
echo "=================================================================="
N=/tmp/T138-neuter
rm -rf "$N"
git clone --quiet --no-hardlinks --shared "$C" "$N"
(cd "$N" && git checkout -q -B neuter bd59187cf83c7c7161db23668e91d45bd46be2a8)
printf '#!/bin/sh\nexit 0\n' > "$N/.softhouse/capture/t91/verdict.sh"
(cd "$N" && git add -A && git -c user.name=T138 -c user.email=t138@local commit -q -m 'neuter verdict.sh')
echo "--- POST-fix prove-guards.sh with verdict.sh neutered:"
(cd "$N" && sh .softhouse/capture/t91/prove-guards.sh 2>&1 | grep -E 'NOT AS EXPECTED|VACUOUS|did NOT behave|done —')
(cd "$N" && sh .softhouse/capture/t91/prove-guards.sh >/dev/null 2>&1); echo "POST_EXIT=$?"
echo
echo "--- PRE-fix prove-guards.sh with verdict.sh neutered (same tree, T91's script):"
P=/tmp/T138-neuter-pre
rm -rf "$P"
git clone --quiet --no-hardlinks --shared "$C" "$P"
(cd "$P" && git checkout -q -B neuterpre ccf3c14171dea52bd044d81d5ca67aba8054b74c)
printf '#!/bin/sh\nexit 0\n' > "$P/.softhouse/capture/t91/verdict.sh"
(cd "$P" && git add -A && git -c user.name=T138 -c user.email=t138@local commit -q -m 'neuter verdict.sh')
(cd "$P" && sh .softhouse/capture/t91/prove-guards.sh 2>&1 | tail -6)
(cd "$P" && sh .softhouse/capture/t91/prove-guards.sh >/dev/null 2>&1); echo "PRE_EXIT=$?"
echo

echo "=================================================================="
echo "MUTATION TEST — G-4: can it detect a BLIND scanner?"
echo "=================================================================="
echo "G-4 asserts only that verdict.sh names A2a as an ADMISSION on the poisoned set."
echo "In the PRE-FIX transcript set A2a exits 0 and expects BREACH, so the exit-code"
echo "rule alone already yields ADMITS.  Simulate a scanner that reports the HALF_UP"
echo "sentence ABSENT (c=no always) — i.e. the exact failure LC_ALL=C grep -a defends"
echo "against — and see whether G-4 goes red."
M=/tmp/T138-blindgrep
rm -rf "$M"
git clone --quiet --no-hardlinks --shared "$C" "$M"
(cd "$M" && git checkout -q -B blind bd59187cf83c7c7161db23668e91d45bd46be2a8)
V=$M/.softhouse/capture/t91/verdict.sh
# defeat the sentence scanner only; leave everything else intact
LC_ALL=C sed -i.bak 's|if LC_ALL=C grep -aqF "\$S" "\$f"; then c=YES; else c=no; fi|c=no  # T138 mutation: scanner blinded|' "$V"
rm -f "$V.bak"
echo "--- the mutated line:"
LC_ALL=C grep -n 'T138 mutation' "$V" | sed 's/^/   /'
(cd "$M" && git add -A && git -c user.name=T138 -c user.email=t138@local commit -q -m 'blind the sentence scanner')
echo "--- G-4 leg output with the scanner blinded:"
(cd "$M" && sh .softhouse/capture/t91/prove-guards.sh 2>&1 | sed -n '/=== G-4/,/=== G-5/p' | grep -E 'A2a|OK      \[G-4\]|NOT AS EXPECTED')
(cd "$M" && sh .softhouse/capture/t91/prove-guards.sh >/dev/null 2>&1); echo "WHOLE_SCRIPT_EXIT=$?"
echo

echo "=================================================================="
echo "MUTATION TEST — G-6: does it pin WHICH exit-2 it got?"
echo "=================================================================="
echo "G-6 compares only the exit status (2).  run-attacks.sh exits 2 from six"
echo "different places.  Make it exit 2 for an unrelated reason and see if G-6"
echo "still reports OK."
K=/tmp/T138-g6
rm -rf "$K"
git clone --quiet --no-hardlinks --shared "$C" "$K"
(cd "$K" && git checkout -q -B g6 bd59187cf83c7c7161db23668e91d45bd46be2a8)
# Delete the SWAP request run-attacks.sh needs... it is only read at A3a, after the
# assertion.  Instead: break the symlink assertion, which is a DIFFERENT exit 2 and
# fires before any attack, exactly like assert_mutated.
LC_ALL=C sed -i.bak 's|^assert_mutated "\$O/req-mutated-55.json" 1162502.55$|# T138 mutation: assert_mutated REMOVED|' "$K/.softhouse/capture/t91/run-attacks.sh"
LC_ALL=C sed -i.bak2 's|^assert_mutated "\$O/req-crafted-04.json" 1162502.4$|# T138 mutation: assert_mutated REMOVED|' "$K/.softhouse/capture/t91/run-attacks.sh"
LC_ALL=C sed -i.bak3 's|^CANON=\$CAP/pathb/t22-audit/req/calc-pmode2-gerege.json$|CANON=$CAP/pathb/t22-audit/req/calc-pmode2-gerege.json\nRECIPE_CHECK_FAIL=1|' "$K/.softhouse/capture/t91/run-attacks.sh"
rm -f "$K/.softhouse/capture/t91/run-attacks.sh".bak*
LC_ALL=C grep -n 'T138 mutation' "$K/.softhouse/capture/t91/run-attacks.sh" | sed 's/^/   /'
# now make it exit 2 for the UNRELATED reason: point RECIPE at a nonexistent file is not
# possible from prove-guards (it sets RECIPE itself), so instead break A7's symlink target.
LC_ALL=C sed -i.bak 's|^ln -s "\$CANON" "\$O/link-to-canon.json" .*$|ln -s /nonexistent/nope.json "$O/link-to-canon.json"  # T138 mutation|' "$K/.softhouse/capture/t91/run-attacks.sh"
rm -f "$K/.softhouse/capture/t91/run-attacks.sh".bak
(cd "$K" && git add -A && git -c user.name=T138 -c user.email=t138@local commit -q -m 'g6 mutation')
echo "--- G-6 leg with assert_mutated REMOVED and A7's symlink broken:"
(cd "$K" && sh .softhouse/capture/t91/prove-guards.sh 2>&1 | sed -n '/=== G-6/,/=== G-7/p' | grep -E 'exit=|HARNESS ERROR')
(cd "$K" && sh .softhouse/capture/t91/prove-guards.sh >/dev/null 2>&1); echo "WHOLE_SCRIPT_EXIT=$?"
