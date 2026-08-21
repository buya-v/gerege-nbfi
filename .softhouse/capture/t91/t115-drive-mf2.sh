#!/bin/sh
# T115 — drive MF-2 RED and GREEN, and measure the two limbs MF-2 does NOT close.
#
# MF-2 closes the FIRST limb of T107's F-2 (its attack N8a): the call-through shim selects the one
# hardened rig by a $0-relative path and dot-sources it.  An EMPTY rig sources cleanly and returns,
# so the shim fell off the end and exited 0 having asserted NOTHING — through the T40 wrapper that
# was `PRECONDITIONS_EXIT=0`, exit 0, and a ZERO-BYTE transcript, over which `attest.py:269` would
# stamp `'preconditions_result': 'ALL PASS'`.
#
# MF-2's premise, verified rather than assumed: `pathb/t36/preconditions.sh` contains exactly two
# `exit` statements (`:234` exit 1, `:237` exit 0), both at top level, neither inside a function
# (the only functions are `ok()`/`bad()` at `:57-58`).  In a SOURCED script those exit the caller's
# shell.  So control reaching the line after `. "$RIG"` really does mean the rig never completed.
# This script re-asserts that census rather than trusting this comment.
#
# *** READ THIS BEFORE MERGING.  MF-2 DOES NOT CLOSE F-2. ***
# It closes the empty-rig limb ONLY.  N9 (rig replaced by main's pre-hardening bytes) and N10 (shim
# reached through a symlink into an attacker's tree) BOTH STILL ADMIT, and this script measures
# them so that nobody can merge MF-2 believing F-2 is discharged.  Only FU-1 — an identity check on
# the rig — closes them.
#
# Everything destructive happens inside a `git archive` export under /tmp.  The oracle is read only.
#
# Usage:  sh t115-drive-mf2.sh
# Exit:   0 = every leg as specified; 1 = a leg was not; 2 = the harness could not establish itself.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../../.." && pwd)

# Pre-MF-2 bytes pinned to a LITERAL IMMUTABLE SHA, never a ref computed from `main` (P-24).
PRE_SHA=ccf3c14171dea52bd044d81d5ca67aba8054b74c   # T91's tip, the bytes T107 reviewed

S=/tmp/t115-mf2.$$
trap 'rm -rf "$S"' EXIT
mkdir -p "$S/pre" "$S/post"

abort() { echo "ABORT: $*" >&2; exit 2; }

( cd "$ROOT" && git archive "$PRE_SHA"  ) | tar -x -C "$S/pre"  || abort "git archive $PRE_SHA failed"
( cd "$ROOT" && git archive HEAD        ) | tar -x -C "$S/post" || abort "git archive HEAD failed"
# An unchecked `git archive` producing an empty export is T107's F-6; do not repeat it here.
[ -f "$S/pre/.softhouse/capture/charges/bin/preconditions.sh"  ] || abort "pre export is empty"
[ -f "$S/post/.softhouse/capture/charges/bin/preconditions.sh" ] || abort "post export is empty"
if LC_ALL=C grep -aq 'PRECONDITIONS NOT RUN: the rig at' "$S/pre/.softhouse/capture/charges/bin/preconditions.sh"; then
  abort "the 'pre' baseline already contains MF-2 — this proof would compare the fix to itself"
fi
LC_ALL=C grep -aq 'PRECONDITIONS NOT RUN: the rig at' "$S/post/.softhouse/capture/charges/bin/preconditions.sh" \
  || abort "the 'post' export does NOT contain MF-2 — nothing would be proved"

RIGREL=.softhouse/capture/pathb/t36/preconditions.sh
CANON_REL=.softhouse/capture/pathb/t22-audit/req/calc-pmode2-gerege.json

echo "pre  export: $PRE_SHA (MF-2 absent, asserted)"
echo "post export: $(cd "$ROOT" && git rev-parse HEAD) (MF-2 present, asserted)"
echo

# ---------------------------------------------------------------- MF-2's premise, re-measured
echo "=================================================================== MF-2 PREMISE"
nex=$(LC_ALL=C grep -ac '^ *exit ' "$S/post/$RIGREL")
echo "top-level \`exit\` statements in the hardened rig: $nex"
LC_ALL=C grep -an '^ *exit ' "$S/post/$RIGREL" | sed 's/^/    /'
nfn=$(LC_ALL=C grep -ac '^[a-zA-Z_][a-zA-Z0-9_]*()' "$S/post/$RIGREL")
echo "function definitions in the rig: $nfn   (ok/bad printers; neither contains an exit)"
fail=0
[ "$nex" -eq 2 ] || { echo "*** expected 2 exits, got $nex — MF-2's premise is NOT established"; fail=$((fail+1)); }
echo

# ---------------------------------------------------------------- RED
echo "=================================================================== RED — the rig EMPTIED"
red() { # red <tree> <label>
  _t=$1; _l=$2
  : > "$_t/$RIGREL"                      # empty, not deleted: the [ ! -f ] branch must NOT be what fires
  [ -f "$_t/$RIGREL" ] || abort "rig should exist and be empty"
  [ -s "$_t/$RIGREL" ] && abort "rig should be zero bytes"
  echo "--- $_l: direct shim call"
  CANARY_REQ="$_t/$CANON_REL" sh "$_t/.softhouse/capture/charges/bin/preconditions.sh" gerege \
    > "$S/$_l-direct.out" 2>"$S/$_l-direct.err"
  echo "    exit=$?   stdout=$(wc -c < "$S/$_l-direct.out" | tr -d ' ') bytes   stderr:"
  sed 's/^/      /' "$S/$_l-direct.err"
  echo "--- $_l: through the T40 wrapper bin/run-preconditions.sh"
  sh "$_t/.softhouse/capture/charges/bin/run-preconditions.sh" "$S/$_l-wrap.txt" > "$S/$_l-wrap.out" 2>&1
  echo "    exit=$?"
  sed 's/^/      /' "$S/$_l-wrap.out"
  echo "    transcript $S/$_l-wrap.txt is $(wc -c < "$S/$_l-wrap.txt" | tr -d ' ') bytes"
  echo
}
cp -R "$S/pre"  "$S/pre-red";  red "$S/pre-red"  PRE
cp -R "$S/post" "$S/post-red"; red "$S/post-red" POST

# assertions on the red legs
grep -q 'PRECONDITIONS_EXIT=0' "$S/PRE-wrap.out"  || { echo "*** PRE wrapper did not report exit 0 (the defect should be present)"; fail=$((fail+1)); }
grep -q 'PRECONDITIONS_EXIT=2' "$S/POST-wrap.out" || { echo "*** POST wrapper did not report PRECONDITIONS_EXIT=2"; fail=$((fail+1)); }
[ "$(wc -c < "$S/PRE-wrap.txt"  | tr -d ' ')" -eq 0 ] || { echo "*** PRE transcript was expected to be ZERO bytes"; fail=$((fail+1)); }
[ "$(wc -c < "$S/POST-wrap.txt" | tr -d ' ')" -gt 0 ] || { echo "*** POST transcript is still zero bytes — N8a is not closed"; fail=$((fail+1)); }
LC_ALL=C grep -aq 'nothing was asserted' "$S/POST-direct.err" || { echo "*** POST direct call did not print the MF-2 refusal"; fail=$((fail+1)); }
echo "RED verdict: pre = exit 0 over a ZERO-BYTE transcript; post = exit 2, transcript non-empty."
echo

# ---------------------------------------------------------------- GREEN: five real callers
echo "=================================================================== GREEN — five real callers"
echo "Each caller is run against BOTH exports.  Cells: PASS count / FAIL count / exit status."
echo

run_callers() { # run_callers <tree> <label>
  _t=$1; _l=$2
  CANON="$_t/$CANON_REL"
  CH="$_t/.softhouse/capture/charges"
  # C1 — the T40 wrapper, tenant gerege (it supplies CANARY_REQ itself)
  sh "$CH/bin/run-preconditions.sh" "$S/$_l-C1.txt" > /dev/null 2>&1; echo "$?" > "$S/$_l-C1.rc"
  # C2 — t51-negative.sh's form: direct, tenant `default`, NO CANARY_REQ
  sh "$CH/bin/preconditions.sh" default > "$S/$_l-C2.txt" 2>&1; echo "$?" > "$S/$_l-C2.rc"
  # C3 — t55-negative-tests.sh leg N2: tenant that has no row in fineract_tenants.tenants
  sh "$CH/bin/preconditions.sh" t55-no-such-tenant > "$S/$_l-C3.txt" 2>&1; echo "$?" > "$S/$_l-C3.rc"
  # C4 — T44's control through the inert copy, tenant `default`, pinned canary
  CANARY_REQ="$CANON" sh "$_t/.softhouse/capture/audit-t44/charges/bin/preconditions-COPY.sh" default \
    > "$S/$_l-C4.txt" 2>&1; echo "$?" > "$S/$_l-C4.rc"
  # C5 — C1's call from a FOREIGN CWD by absolute path (resolution must be CWD-independent)
  ( cd /tmp && CANARY_REQ="$CANON" sh "$CH/bin/preconditions.sh" gerege ) \
    > "$S/$_l-C5.txt" 2>&1; echo "$?" > "$S/$_l-C5.rc"
}
run_callers "$S/pre"  PREG
run_callers "$S/post" POSTG

printf '%-4s %-58s %-18s %-18s %s\n' '' caller 'pre-MF-2 (P/F/rc)' 'post-MF-2 (P/F/rc)' 'identical?'
DESC1='C1 bin/run-preconditions.sh (T40 wrapper), tenant gerege'
DESC2='C2 t51-negative.sh form: direct, tenant default, no CANARY_REQ'
DESC3='C3 t55-negative-tests.sh N2: tenant t55-no-such-tenant'
DESC4='C4 T44 control via preconditions-COPY.sh, tenant default'
DESC5='C5 C1 from a foreign CWD (/tmp), absolute path'
nident=0; ncall=0
for c in C1 C2 C3 C4 C5; do
  eval "d=\$DESC${c#C}"
  ap=$(LC_ALL=C grep -ac '^  PASS' "$S/PREG-$c.txt");  af=$(LC_ALL=C grep -ac '^  FAIL' "$S/PREG-$c.txt");  ar=$(cat "$S/PREG-$c.rc")
  bp=$(LC_ALL=C grep -ac '^  PASS' "$S/POSTG-$c.txt"); bf=$(LC_ALL=C grep -ac '^  FAIL' "$S/POSTG-$c.txt"); br=$(cat "$S/POSTG-$c.rc")
  ncall=$((ncall+1))
  if [ "$ap" = "$bp" ] && [ "$af" = "$bf" ] && [ "$ar" = "$br" ]; then id=YES; nident=$((nident+1)); else id='*** NO ***'; fail=$((fail+1)); fi
  printf '%-4s %-58s %-18s %-18s %s\n' '' "$d" "$ap/$af/$ar" "$bp/$bf/$br" "$id"
done
echo
echo "callers identical cell for cell: $nident of $ncall"
echo "C3's asserted string survives post-MF-2: $(LC_ALL=C grep -ac 'has no row in fineract_tenants.tenants' "$S/POSTG-C3.txt") occurrence(s)"
LC_ALL=C grep -aq 'has no row in fineract_tenants.tenants' "$S/POSTG-C3.txt" || { echo "*** C3's asserted string is GONE"; fail=$((fail+1)); }
echo "C2/C4 breach count post-MF-2 (MF-3's subject, must be 5): C2=$(LC_ALL=C grep -ac '^  FAIL' "$S/POSTG-C2.txt")  C4=$(LC_ALL=C grep -ac '^  FAIL' "$S/POSTG-C4.txt")"
echo

# ---------------------------------------------------------------- what MF-2 does NOT close
echo "=================================================================== N9 / N10 — STILL OPEN"
echo "MF-2 does NOT close F-2.  Measured, post-MF-2, so nobody merges believing otherwise:"
echo
echo "--- N9: the rig at its path REPLACED by main's pre-hardening bytes"
cp -R "$S/post" "$S/n9"
# T91 never touched the rig, so $PRE_SHA carries the HARDENED rig and would prove nothing here.
# The genuinely pre-hardening bytes are the blob T40 lifted, named in the shim's own header.
PRE_RIG_BLOB=e6c1795a172168105d788321a71ee4ca62b73e36
if ( cd "$ROOT" && git cat-file -e "$PRE_RIG_BLOB" ) 2>/dev/null; then
  ( cd "$ROOT" && git cat-file blob "$PRE_RIG_BLOB" ) > "$S/n9/$RIGREL"
  [ -s "$S/n9/$RIGREL" ] || abort "the pre-hardening rig blob is empty"
  CANARY_REQ="$S/n9/$CANON_REL" sh "$S/n9/.softhouse/capture/charges/bin/preconditions.sh" gerege \
    > "$S/n9.txt" 2>&1; n9rc=$?
  echo "    exit=$n9rc"
  LC_ALL=C grep -a 'effective rounding mode canary\|ALL PRECONDITIONS HOLD' "$S/n9.txt" | sed 's/^/    /'
  if [ "$n9rc" -eq 0 ]; then
    echo "    => N9 STILL ADMITS through the MF-2 shim.  F-2 is NOT discharged.  FU-1 closes this."
  else
    echo "    => N9 did not admit on this run (exit $n9rc); the absence of an identity check stands regardless."
  fi
else
  echo "    (blob $PRE_RIG_BLOB not resolvable here; N9 not measured this run)"
fi
echo
echo "--- N10: the shim reached through a SYMLINK placed in a foreign tree"
mkdir -p "$S/evil/.softhouse/capture/charges/bin" "$S/evil/.softhouse/capture/pathb/t36"
cat > "$S/evil/.softhouse/capture/pathb/t36/preconditions.sh" <<'STUB'
echo "ALL PRECONDITIONS HOLD — tenant 'gerege' at MathContext(19, HALF_UP), PostgreSQL only."
exit 0
STUB
ln -sf "$S/post/.softhouse/capture/charges/bin/preconditions.sh" \
       "$S/evil/.softhouse/capture/charges/bin/preconditions.sh"
sh "$S/evil/.softhouse/capture/charges/bin/preconditions.sh" gerege > "$S/n10.txt" 2>&1; n10rc=$?
echo "    exit=$n10rc"
sed 's/^/    /' "$S/n10.txt"
if [ "$n10rc" -eq 0 ]; then
  echo "    => N10 STILL ADMITS: the attacker's stub rig ran.  F-2 is NOT discharged.  FU-1 closes this."
fi
echo

if [ "$fail" -eq 0 ]; then
  echo "RESULT: MF-2 driven RED and GREEN; five callers identical cell for cell; N9/N10 measured OPEN."
  exit 0
fi
echo "RESULT: $fail leg(s) did not behave as specified."
exit 1
