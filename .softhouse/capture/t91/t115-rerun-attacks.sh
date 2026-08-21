#!/bin/sh
# T115 — re-run T91's whole attack suite under MY OWN labels, on both interpreters, from main's
# actual pre-hardening bytes and from this branch, and score every run.
#
# T91's committed transcripts are NOT overwritten.  Mine are additive, under `t115-*` labels, so
# the two sets can be compared and neither can be mistaken for the other.
#
# Required result (the brief's, and T107's, independently):
#   pre-fix  : 6 of 13 ADMIT, scorer exit 1
#   post-fix : 0 of 13 ADMIT, scorer exit 0
#   sh vs bash : 13 of 13 identical after normalisation, both labels
#
# Oracle discipline: `run-attacks.sh` sends only POST /loans?command=calculateLoanSchedule (a pure
# calculation endpoint) and read-only docker/psql reads.  No restart, no rebuild, no re-seed, no
# tenant write.  Destructive work is confined to `git archive` exports under /tmp.
#
# Usage:  sh t115-rerun-attacks.sh
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../../.." && pwd)

PRE_SHIM_BLOB=e6c1795a172168105d788321a71ee4ca62b73e36   # main's pre-hardening charges/bin twin
SHIMREL=.softhouse/capture/charges/bin/preconditions.sh

S=/tmp/t115-attacks.$$
trap 'rm -rf "$S"' EXIT
mkdir -p "$S/pre" "$S/post"
abort() { echo "ABORT: $*" >&2; exit 2; }

( cd "$ROOT" && git archive HEAD ) | tar -x -C "$S/pre"  || abort "git archive failed"
( cd "$ROOT" && git archive HEAD ) | tar -x -C "$S/post" || abort "git archive failed"
[ -f "$S/pre/$SHIMREL" ] || abort "empty export"

# The PRE tree gets main's actual pre-hardening bytes at the shim's path.
( cd "$ROOT" && git cat-file blob "$PRE_SHIM_BLOB" ) > "$S/pre/$SHIMREL" || abort "cannot resolve $PRE_SHIM_BLOB"
[ -s "$S/pre/$SHIMREL" ] || abort "the pre-hardening blob is empty — nothing would be proved"
# Discriminate on an EXECUTABLE line, not on a string that also appears in a COMMENT.  My first
# draft of this guard tested for `CANARY_EXPECT:-20925.05`, which the post-fix shim contains in the
# comment DESCRIBING the old defect — so the guard fired on the healthy tree.  Same defect class as
# the ones this task is fixing, caught by running it.  The structural discriminator is the
# call-through itself: the hardened shim dot-sources the rig, the unhardened copy does not.
LC_ALL=C grep -aq '^\. "\$RIG"' "$S/post/$SHIMREL" || abort "the post tree's shim is not the call-through"
LC_ALL=C grep -aq '^\. "\$RIG"' "$S/pre/$SHIMREL"  && abort "the pre tree already carries the call-through"
LC_ALL=C grep -aq '^CANARY_EXPECT=' "$S/pre/$SHIMREL" || abort "the pre blob is not the unhardened copy (no executable CANARY_EXPECT= assignment)"

echo "pre  shim: blob $PRE_SHIM_BLOB   sha256 $(shasum -a 256 < "$S/pre/$SHIMREL"  | cut -c1-16)"
echo "post shim: HEAD $(cd "$ROOT" && git rev-parse --short HEAD)          sha256 $(shasum -a 256 < "$S/post/$SHIMREL" | cut -c1-16)"
echo

fail=0
for phase in pre post; do
  T=$S/$phase
  for SH in sh bash; do
    LABEL=t115-$phase
    RECIPE=$SHIMREL LABEL=$LABEL SH=$SH sh "$T/.softhouse/capture/t91/run-attacks.sh" > "$S/$phase-$SH.log" 2>&1 \
      || abort "run-attacks.sh failed for $phase/$SH — see $S/$phase-$SH.log"
  done
  for SH in sh bash; do
    LABEL=t115-$phase
    echo "=================================================== $phase / $SH"
    sh "$HERE/verdict.sh" "$T/.softhouse/capture/t91/out/$LABEL-$SH" > "$S/$phase-$SH.score" 2>&1
    rc=$?
    cat "$S/$phase-$SH.score"
    echo "SCORER EXIT=$rc"
    adm=$(LC_ALL=C grep -ac 'ADMITS' "$S/$phase-$SH.score")
    case "$phase" in
      pre)  want_rc=1; want_adm=12 ;;   # 6 rows + 6 recorded in the failure list
      post) want_rc=0; want_adm=0  ;;
    esac
    [ "$rc" = "$want_rc" ]   || { echo "*** expected scorer exit $want_rc"; fail=$((fail+1)); }
    [ "$adm" = "$want_adm" ] || { echo "*** expected $want_adm ADMITS lines, got $adm"; fail=$((fail+1)); }
    echo
  done
  echo "--------------------------------------------------- $phase: sh vs bash invariance"
  sh "$HERE/shell-invariance.sh" "$T/.softhouse/capture/t91/out" "t115-$phase" > "$S/$phase.inv" 2>&1
  irc=$?
  cat "$S/$phase.inv"
  echo "INVARIANCE EXIT=$irc"
  [ "$irc" -eq 0 ] || { echo "*** sh/bash invariance failed for $phase"; fail=$((fail+1)); }
  echo
done

# Keep MY transcripts alongside T91's, without touching T91's.
for phase in pre post; do
  for SH in sh bash; do
    src=$S/$phase/.softhouse/capture/t91/out/t115-$phase-$SH
    dst=$HERE/out/t115-$phase-$SH
    rm -rf "$dst"; mkdir -p "$dst"
    cp "$src"/*.txt "$dst"/ 2>/dev/null
    cp "$S/$phase-$SH.score" "$dst/VERDICT.txt"
  done
done
echo "transcripts written under $HERE/out/t115-*  (T91's own out/ dirs untouched)"

if [ "$fail" -eq 0 ]; then
  echo "RESULT: pre-fix 6 of 13 ADMIT (exit 1), post-fix 0 of 13 (exit 0), sh/bash 13 of 13 identical."
  exit 0
fi
echo "RESULT: $fail check(s) did not hold."
exit 1
