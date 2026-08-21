#!/bin/sh
# T151 — drive F-T138-1: G-4 is GREEN on a tree with `LC_ALL=C` removed from the scanner it guards.
#
# T138 measured this and prescribed two edits, BOTH required.  This driver reproduces the finding on
# the PRE tree and proves the fix on the POST tree in one run, so nobody has to take either on
# trust.  It is the artefact for F-T138-1: re-run it, do not read it.
#
# THE MATRIX.  Three trees per side:
#   healthy   — nothing touched.                       G-4 must be OK and the script must exit 0.
#   nolc      — `LC_ALL=C` removed from verdict.sh's SENTENCE scanner (`verdict.sh:135`).  This is
#               the EXACT regression G-4 exists to catch.   G-4 must go RED on the POST tree.
#   scanner   — that same scanner replaced by `c=no`, i.e. the outcome a silent-miss grep produces.
#                                                           G-4 must go RED on the POST tree.
#
# PRE  = a LITERAL IMMUTABLE SHA.  Never a ref computed from `main`, which moves constantly (P-24).
# POST = HEAD.  That is not a baseline, it is "the tree under test", so resolving it is correct.
#
# Every mutation is applied in python with `assert old in s`, so a pattern that does not match
# ABORTS instead of silently copying the file unchanged.  That is V-C's lesson, and T138 recorded
# hitting it while prescribing this very fix.
#
# Destructive: it works only in throwaway clones under /tmp and never touches the worktree.
# prove-guards.sh's G-1 legs contact the oracle read-only (POST /loans?command=calculateLoanSchedule).
# Nothing else here does, and nothing here restarts, rebuilds, re-seeds or writes to it.
#
# Usage:  sh t151-drive-g4.sh
# Exit:   0 = every cell behaved as specified; 1 = a cell did not; 2 = the harness could not set up.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../../.." && pwd)
PRE_SHA=8c05f9a7190ee1e0f8be09b92bdccc02d62ea103   # main at the T151 fork point — LITERAL, IMMUTABLE
POST_SHA=$(cd "$ROOT" && git rev-parse HEAD)
S=/tmp/t151-g4.$$
trap 'rm -rf "$S"' EXIT
mkdir -p "$S"
BAD=0

echo "PRE  = $PRE_SHA  (literal immutable sha)"
echo "POST = $POST_SHA  (HEAD — the tree under test)"
echo

# The PRE tree must NOT already carry either edit, or the RED leg proves nothing.
(cd "$ROOT" && git show "$PRE_SHA:.softhouse/capture/t91/prove-guards.sh") > "$S/pre-pg.sh" 2>/dev/null || {
  echo "ABORT: cannot read prove-guards.sh at $PRE_SHA." >&2; exit 2; }
if LC_ALL=C /usr/bin/grep -aqF 'ADMITS (printed the HALF_UP certification)' "$S/pre-pg.sh"; then
  echo "ABORT: the PRE tree already carries the F-T138-1 assertion edit — this driver would prove" >&2
  echo "       nothing.  Move PRE_SHA back to a tree that predates it." >&2; exit 2
fi
if LC_ALL=C /usr/bin/grep -aqF 'b[:i] +' "$S/pre-pg.sh"; then
  echo "ABORT: the PRE tree already carries the poison-position edit." >&2; exit 2
fi
LC_ALL=C /usr/bin/grep -aqF 'b[:j] +' "$S/pre-pg.sh" || {
  echo "ABORT: the PRE tree does not carry the ORIGINAL poison line either — this driver is" >&2
  echo "       anchored to a tree it does not recognise." >&2; exit 2; }
echo "asserted: the PRE tree carries the original (after-the-match) poison and NEITHER edit."
echo

build() {  # build <dir> <sha>
  rm -rf "$1"
  git clone --quiet --no-hardlinks --shared "$ROOT" "$1" || { echo "ABORT: clone failed" >&2; exit 2; }
  (cd "$1" && git checkout -q -B t151cell "$2") || { echo "ABORT: checkout $2 failed" >&2; exit 2; }
}

blind() {  # blind <dir> <nolc|scanner>
  python3 - "$1/.softhouse/capture/t91/verdict.sh" "$2" <<'PY'
import sys
p, mode = sys.argv[1], sys.argv[2]
s = open(p).read()
old = 'if LC_ALL=C grep -aqF "$S" "$f"; then c=YES; else c=no; fi'
assert old in s, 'ABORT: verdict.sh sentence scanner not found — the mutation would be a no-op'
new = ('c=no  # T151: scanner blinded' if mode == 'scanner'
       else 'if LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 /usr/bin/grep -aqF "$S" "$f"; then c=YES; else c=no; fi  # T151: LC_ALL=C removed')
open(p, 'w').write(s.replace(old, new))
PY
  [ $? -eq 0 ] || { echo "ABORT: mutation '$2' did not apply" >&2; exit 2; }
  (cd "$1" && git add -A && git -c user.name=T151 -c user.email=t151@local commit -q -m "T151 mutate $2")
}

# unfix — revert ONE of the two edits in a POST clone, to show that BOTH are load-bearing.
# Same discipline as blind(): the pattern is asserted, so a revert that does not take ABORTS
# instead of silently leaving the tree fixed and reporting a green cell.
unfix() {  # unfix <dir> <assertion|poison>
  python3 - "$1/.softhouse/capture/t91/prove-guards.sh" "$2" <<'PY'
import sys
p, which = sys.argv[1], sys.argv[2]
s = open(p).read()
if which == 'assertion':
    old = '"^A2a.*ADMITS (printed the HALF_UP certification)"'
    new = '"^A2a.*ADMITS"'
else:
    old = "open(p, 'wb').write(b[:i] + b'\\xff\\xfe' + b[i:])"
    new = "j = b.find(b'\\n', i)\nopen(p, 'wb').write(b[:j] + b'\\xff\\xfe' + b[j:])"
assert old in s, 'ABORT: cannot revert the %s edit — pattern absent' % which
open(p, 'w').write(s.replace(old, new))
PY
  [ $? -eq 0 ] || { echo "ABORT: revert '$2' did not apply" >&2; exit 2; }
  (cd "$1" && git add -A && git -c user.name=T151 -c user.email=t151@local commit -q -m "T151 revert $2 edit")
}

cell() {  # cell <side> <sha> <healthy|nolc|scanner> <want G-4: OK|RED> <want script exit> [unfix]
  d=$S/$(printf '%s%s%s' "$1" "$3" "${6:-}" | tr -cd 'A-Za-z0-9')
  build "$d" "$2"
  [ -z "${6:-}" ] || unfix "$d" "$6"
  [ "$3" = healthy ] || blind "$d" "$3"
  (cd "$d" && sh .softhouse/capture/t91/prove-guards.sh) > "$d.txt" 2>&1
  rc=$?
  if LC_ALL=C /usr/bin/grep -aq 'named as an admission on the poisoned set' "$d.txt"; then g4=OK
  elif LC_ALL=C /usr/bin/grep -aq 'NOT named as an admission' "$d.txt"; then g4=RED
  else g4=NEITHER; fi
  printf '  %-5s %-8s %-10s G-4=%-7s (want %-3s)  script exit=%s (want %s)' \
         "$1" "$3" "${6:+-$6}" "$g4" "$4" "$rc" "$5"
  ok=yes
  [ "$4" = '?' ] || [ "$g4" = "$4" ] || ok=no
  [ "$5" = '?' ] || [ "$rc" = "$5" ] || ok=no
  if [ "$ok" = yes ]; then echo "   OK"
  else echo "   *** NOT AS SPECIFIED ***"; BAD=$((BAD+1)); fi
  LC_ALL=C /usr/bin/grep -a '^A2a' "$d.txt" | sed 's/^/          /'
  LC_ALL=C /usr/bin/grep -a 'rc=[0-9]' "$d.txt" | sed 's/^/          /'
  echo
}

echo "=== THE FOUR CELLS: (shipped | fixed) x (healthy | the regression G-4 exists to catch)"
cell PRE  "$PRE_SHA"  healthy OK  0
cell PRE  "$PRE_SHA"  nolc    OK  0     # <-- THE FINDING: green with the hardening it guards removed
cell POST "$POST_SHA" healthy OK  0
cell POST "$POST_SHA" nolc    RED 1     # <-- must now go red
echo "=== the third mutation: the scanner fully blinded (what a silent-miss grep actually produces)"
# CORRECTION TO T138, recorded because a correction that leaves the attestation wrong is not a
# correction (P-21).  T138's §3 table gives the SHIPPED tree with the scanner blinded as `exit 1`.
# It is `exit 0`, G-4 `OK` — which is what T138's own PROSE in F-T138-1(a) says ("G-4 printed
# `A2a named as an admission on the poisoned set OK [G-4]`; the whole script exited 0").  T138's
# committed driver `r14b-g4fix.sh` never ran that combination, so no transcript backed the table
# cell.  The expectation below is MEASURED here, and it agrees with the prose, not the table.
cell PRE  "$PRE_SHA"  scanner OK  0
cell POST "$POST_SHA" scanner RED 1
echo "=== BOTH edits are load-bearing: revert either one and the guard goes blind again"
cell POST "$POST_SHA" nolc    OK  0 assertion   # poison-position edit ONLY
cell POST "$POST_SHA" nolc    OK  0 poison      # assertion edit ONLY
if [ "$BAD" -eq 0 ]; then
  echo "done — every cell behaved as specified."
  echo "F-T138-1 REPRODUCED on PRE and CLOSED on POST."
  exit 0
fi
echo "done — $BAD cell(s) did NOT behave as specified."
exit 1
