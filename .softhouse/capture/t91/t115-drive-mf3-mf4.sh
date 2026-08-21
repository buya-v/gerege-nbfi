#!/bin/sh
# T115 — establish MF-3 and MF-4 by MEASUREMENT, not by copying T107's numbers.
#
# MF-3 (T107 F-4).  The shipped shim header says `bin/t51-negative.sh` "passes none, so it now
# reports one further breach".  That is PR-10's error, which T91 itself scored as WRONG in its own
# prediction table and then left standing in a shipped file (P-12/P-21: the correction landed where
# the claim was scored, not where it was restated).  The claim is about the breach count BEFORE
# T91 (the copied pre-hardening bytes, blob e6c1795a…) versus AFTER (the call-through), so that is
# what this measures — on both interpreters.
#
# MF-4 (added by T107b).  `charges/bin/preconditions.sh:8` says "17 capture scripts and attest.py".
# This re-derives the census from the tree.  Inclusion rule, stated because a census with an
# unstated rule is not a census:
#   * counted: an EXECUTABLE line that invokes `charges/bin/preconditions.sh`, directly or through
#     the T40 wrapper `charges/bin/run-preconditions.sh`;
#   * NOT counted: comments; string literals recording provenance (`attest-t40.py:305`); the
#     `grep -v` EXCLUSION at `charges/bin/selfcheck.sh:15` (T91's F-4, correctly characterised);
#     `pathb/t36/*`, which invokes the RIG directly and not this shim;
#     `t91/prove-guards.sh`, T91's own red/green harness, which invokes the shim only inside a
#     throwaway `git archive` export and is not a caller in the capture pipeline — it is reported
#     separately below so the exclusion is visible rather than silent.
#
# Usage:  sh t115-drive-mf3-mf4.sh
# Exit:   0 = measured; 2 = the harness could not establish itself.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../../.." && pwd)
C=$ROOT/.softhouse/capture
PRE_SHIM_BLOB=e6c1795a172168105d788321a71ee4ca62b73e36   # the pre-T91 copied bytes, per the header
abort() { echo "ABORT: $*" >&2; exit 2; }

S=/tmp/t115-mf34.$$
trap 'rm -rf "$S"' EXIT
mkdir -p "$S"

echo "=================================================================== MF-3"
echo "CLAIM UNDER TEST: 'bin/t51-negative.sh passes none, so it NOW REPORTS ONE FURTHER BREACH.'"
echo
( cd "$ROOT" && git cat-file blob "$PRE_SHIM_BLOB" ) > "$S/pre-shim.sh" 2>/dev/null \
  || abort "cannot resolve the pre-T91 shim blob $PRE_SHIM_BLOB"
[ -s "$S/pre-shim.sh" ] || abort "the pre-T91 shim blob is empty — nothing would be proved"
LC_ALL=C grep -aq 'CANARY_EXPECT:-20925.05' "$S/pre-shim.sh" \
  || abort "the pre-T91 blob does not look like the unhardened copy"
echo "pre-T91 shim: blob $PRE_SHIM_BLOB, $(wc -l < "$S/pre-shim.sh" | tr -d ' ') lines (unhardened copy, asserted)"
echo "post-T91 shim: $C/charges/bin/preconditions.sh (call-through + MF-2)"
echo
# The pre-T91 copy is self-contained, so it can be run from anywhere; the post-T91 shim resolves
# the rig relative to $0 and must be run from its own place in the tree.
printf '%-10s %-30s %s\n' interp variant 'PASS / FAIL / exit'
for SH in /bin/sh /bin/bash; do
  # t51-negative.sh:21's exact form: direct call, tenant `default`, NO CANARY_REQ in the environment
  env -u CANARY_REQ "$SH" "$S/pre-shim.sh" default > "$S/pre-$$.txt" 2>&1; prc=$?
  ppass=$(LC_ALL=C grep -ac '^  PASS' "$S/pre-$$.txt"); pfail=$(LC_ALL=C grep -ac '^  FAIL' "$S/pre-$$.txt")
  printf '%-10s %-30s %s\n' "$(basename $SH)" 'pre-T91 (unhardened copy)' "$ppass / $pfail / $prc"
  env -u CANARY_REQ "$SH" "$C/charges/bin/preconditions.sh" default > "$S/post-$$.txt" 2>&1; qrc=$?
  qpass=$(LC_ALL=C grep -ac '^  PASS' "$S/post-$$.txt"); qfail=$(LC_ALL=C grep -ac '^  FAIL' "$S/post-$$.txt")
  printf '%-10s %-30s %s\n' "$(basename $SH)" 'post-T91 (call-through)' "$qpass / $qfail / $qrc"
  echo "           breach delta: $((qfail - pfail))   (the header claims +1)"
  echo
done
echo "the FAIL lines, pre-T91 then post-T91 (bash), so the reader can see WHICH breaches:"
env -u CANARY_REQ /bin/bash "$S/pre-shim.sh" default 2>&1 | LC_ALL=C grep -a '^  FAIL' | sed 's/^/    pre   /'
env -u CANARY_REQ /bin/bash "$C/charges/bin/preconditions.sh" default 2>&1 | LC_ALL=C grep -a '^  FAIL' | sed 's/^/    post  /'
echo

echo "=================================================================== MF-4 — the census"
echo
DIRECT="$C/charges/bin/run-preconditions.sh:9
$C/charges/bin/attest.py:90
$C/charges/bin/attest-t40.py:91
$C/charges/bin/t51-negative.sh:21
$C/leapboundary/bin/t55-negative-tests.sh:52"
echo "-- A. DIRECT executable invocations of charges/bin/preconditions.sh"
nd=0
for s in $DIRECT; do
  f=${s%:*}; l=${s##*:}
  [ -f "$f" ] || abort "census names a file that does not exist: $f"
  txt=$(sed -n "${l}p" "$f")
  case "$txt" in *preconditions.sh*) ;; *) abort "census miss: $f:$l does not name preconditions.sh — [$txt]" ;; esac
  case "$txt" in \#*|" "*\#*) abort "census counts a comment at $f:$l" ;; esac
  nd=$((nd+1))
  printf '   %-62s %s\n' "${f#"$ROOT"/}:$l" "$(echo "$txt" | cut -c1-70)"
done
echo "   direct sites: $nd   direct files: $(for s in $DIRECT; do echo "${s%:*}"; done | sort -u | wc -l | tr -d ' ')"
echo
echo "-- B. executable invocations of the T40 wrapper charges/bin/run-preconditions.sh"
LC_ALL=C grep -rn --exclude-dir=.git --include='*.sh' --include='*.py' 'run-preconditions\.sh' "$C" \
  | LC_ALL=C grep -av "^$C/t91/" \
  | LC_ALL=C grep -av "^$C/charges/bin/run-preconditions.sh:" \
  | LC_ALL=C grep -av ':[0-9]*:#' \
  | sed "s#^$ROOT/##" | sort > "$S/wrap.txt"
sed 's/^/   /' "$S/wrap.txt" | cut -c1-110
nw=$(wc -l < "$S/wrap.txt" | tr -d ' ')
nwf=$(cut -d: -f1 "$S/wrap.txt" | sort -u | wc -l | tr -d ' ')
echo "   wrapper sites: $nw   wrapper files: $nwf"
echo
echo "-- TOTAL"
allfiles=$( { for s in $DIRECT; do echo "${s%:*}" | sed "s#^$ROOT/##"; done; cut -d: -f1 "$S/wrap.txt"; } | sort -u )
nf=$(echo "$allfiles" | wc -l | tr -d ' ')
echo "   distinct files: $nf"
echo "   executable call sites: $((nd + nw))"
echo
echo "-- deliberate exclusions, named so the census's rule is visible"
echo "   charges/bin/selfcheck.sh:15            grep -v EXCLUSION, not an invocation (T91 F-4)"
echo "   charges/bin/attest-t40.py:305          a provenance STRING, not a call"
echo "   pathb/t36/{attest.py,recapture.sh,emiloop-probe.sh,recreate-products.sh}"
echo "                                          these invoke the RIG directly, not this shim"
n91=$(LC_ALL=C grep -ac 'charges/bin/preconditions\.sh\|charges/bin/run-preconditions\.sh' "$HERE/prove-guards.sh")
echo "   t91/prove-guards.sh                    $n91 invocation(s), but only inside a throwaway"
echo "                                          git-archive export; a red/green harness, not a caller"
echo
echo "-- what this census could NOT have found (P-26)"
echo "   * an invocation built by string concatenation or held in a variable, in any language"
echo "   * an invocation from outside .softhouse/capture/ (CI, a Makefile, a scheduled task)"
echo "   * an invocation in a file extension other than .sh / .py"
echo "   * a caller that reaches the shim through a symlink or a copied path (see N10)"
echo "   * a HUMAN who runs it by hand, which is how the negative controls are usually driven"
