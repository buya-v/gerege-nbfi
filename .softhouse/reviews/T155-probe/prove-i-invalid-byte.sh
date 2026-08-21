#!/bin/bash
# T155 probe (i) — INDEPENDENT. Does ONE invalid byte defeat the two no-float
# shell guards, and does T154 close it?
#
# The guard pipelines are lifted from IMMUTABLE git blobs and the blob shas are
# asserted, so this prover cannot drift into testing the fixed code (the shape
# A2-5 set, per the T155 brief).
#
# The poison corpus is T155's OWN, written before reading any T154 fixture.
set -u
REPO="${REPO:-/Users/buv/gerege-nbfi/.claude/worktrees/agent-a0e4fbacb5cf6d93f}"
PRE_SHA=187e9726dfad5076f4b68877f411d7d218280889
PRE_BLOB_SHA=11d3729eedee3ee70d4d95a0f0f93d4a9850412244e621c7cfab67610d198853
POST_BLOB_SHA=a55d7f5270a3933bcf3e0c6986a217971e621f65f0de723fca9f803d3aed27a7
TMP="${TMP:-/tmp/t155}"
P="$TMP/poison"

cd "$REPO" || exit 9
got_pre=$(git show "$PRE_SHA:.softhouse/conformance.sh" | shasum -a 256 | cut -d' ' -f1)
got_post=$(git show softhouse/T154-nofloat-guards:.softhouse/conformance.sh | shasum -a 256 | cut -d' ' -f1)
[ "$got_pre" = "$PRE_BLOB_SHA" ] || { echo "REFUSE: pre blob sha drifted: $got_pre"; exit 9; }
[ "$got_post" = "$POST_BLOB_SHA" ] || { echo "REFUSE: post blob sha drifted: $got_post"; exit 9; }
echo "blob shas verified: PRE $PRE_BLOB_SHA / POST $POST_BLOB_SHA"
echo "grep this script gets: $(command -v grep) — $(grep --version 2>&1 | head -1)"
echo

git show "$PRE_SHA:.softhouse/conformance.sh" > "$TMP/pre.sh"
git show softhouse/T154-nofloat-guards:.softhouse/conformance.sh > "$TMP/post.sh"

# Lift the ONE pipeline line out of each and turn it into a callable predicate.
# $2 may be a single line or a `a,b` range; a trailing backslash-continuation is
# folded away so a two-line pipeline is lifted whole (the P-36 hazard: a partial
# lift turns every row into a null control that still prints a coherent table —
# the positive-control rows below are what catch it).
mkline() { sed -n "${2}p" "$1" | sed -e 's/\\$//' | tr '\n' ' ' \
           | sed -e 's/^[[:space:]]*if //' -e 's/;[[:space:]]*then[[:space:]]*$//'; }
PRE_J="$(mkline "$TMP/pre.sh" 483)"
PRE_G="$(mkline "$TMP/pre.sh" 500,501)"
POST_J="$(mkline "$TMP/post.sh" 526)"
POST_G="$(mkline "$TMP/post.sh" 558,559)"
for v in PRE_J PRE_G POST_J POST_G; do
  eval "t=\$$v"
  case "$t" in *perl*'|'*grep*) ;; *) echo "REFUSE: $v is not a perl|grep pipeline: [$t]"; exit 9;; esac
done
echo "PRE  json : $PRE_J"
echo "PRE  go   : $PRE_G"
echo "POST json : $POST_J"
echo "POST go   : $POST_G"
echo

RED=0
run() { # 1 name 2 want_pre 3 want_post 4 pre_pipe 5 post_pipe 6 file 7 note
  local pre post mark=""
  pre=$(f="$6"; eval "$4" >/dev/null 2>&1 && echo FIRES || echo SILENT)
  post=$(f="$6"; eval "$5" >/dev/null 2>&1 && echo FIRES || echo SILENT)
  [ "$pre" = "$2" ]  || { mark="$mark  !!PRE-expected-$2";  RED=$((RED+1)); }
  [ "$post" = "$3" ] || { mark="$mark  !!POST-expected-$3"; RED=$((RED+1)); }
  printf '%-30s %-7s %-7s %s%s\n' "$1" "$pre" "$post" "$7" "$mark"
}
printf '%-30s %-7s %-7s %s\n' FIXTURE PRE POST MEANING
printf '%-30s %-7s %-7s %s\n' ------- --- ---- -------
run "p1 clean float"           FIRES  FIRES  "$PRE_J" "$POST_J" "$P/p1.json" "POSITIVE CONTROL"
run "p2 0xE2 BEFORE the float" SILENT FIRES  "$PRE_J" "$POST_J" "$P/p2.json" "*** THE BYPASS ***"
# T155 PREDICTED SILENT HERE AND WAS WRONG. A NUL byte does NOT blind BSD grep in
# a UTF-8 locale — NUL is a valid single byte, and the blindness is specific to an
# invalid MULTI-BYTE sequence. The expectation is corrected to the measurement,
# not the other way round; the row is kept because a later worker reaching for NUL
# as a probe would otherwise get a false negative and conclude the guard is blind.
run "p3 NUL BEFORE the float"  FIRES  FIRES  "$PRE_J" "$POST_J" "$P/p3.json" "NOT a bypass vector"
run "p4 0xE2 AFTER the float"  FIRES  FIRES  "$PRE_J" "$POST_J" "$P/p4.json" "byte after match"
run "p5 clean integers"        SILENT SILENT "$PRE_J" "$POST_J" "$P/p5.json" "NEGATIVE CONTROL"
run "p6 0xE2 + exponent 1e3"   SILENT FIRES  "$PRE_J" "$POST_J" "$P/p6.json" "*** THE BYPASS (exp) ***"
run "g1 clean float64"         FIRES  FIRES  "$PRE_G" "$POST_G" "$P/g1.go"   "POSITIVE CONTROL"
run "g2 0xE2 before float64"   SILENT FIRES  "$PRE_G" "$POST_G" "$P/g2.go"   "*** THE BYPASS (go) ***"
run "g3 clean int64"           SILENT SILENT "$PRE_G" "$POST_G" "$P/g3.go"   "NEGATIVE CONTROL"
echo
echo "rows disagreeing with T155's own expectation: $RED"
[ "$RED" -eq 0 ] || exit 1
