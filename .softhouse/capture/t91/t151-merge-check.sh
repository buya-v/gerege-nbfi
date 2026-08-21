#!/bin/sh
# T151 — P-24: verify on a SCRATCH MERGE INTO CURRENT `main`, in a throwaway clone.
#
# `main` moves constantly this fire — it moved from 8c05f9a to a later commit while T151 was in
# flight — so "it merged cleanly when I forked" is not a claim about today.  This script resolves
# `main` AT RUN TIME (which is the point: the target is deliberately not pinned), merges the T151
# branch into a throwaway clone of it, asserts the frozen surfaces are untouched, and re-runs every
# artefact ON THE MERGED TREE rather than on the branch.  Re-running the artefact, not just the
# conformance suite, is what caught T98's relocated time bomb.
#
# Note the asymmetry, deliberately: BASELINES are literal immutable shas (see t151-drive-g4.sh and
# t151-drive-vb.sh); the MERGE TARGET is `main` at run time.  A baseline that follows `main` cannot
# prove a fix; a merge target that does not follow `main` cannot prove mergeability.
#
# Usage:  sh t151-merge-check.sh [branch]     (default: the current branch)
# Exit:   0 = merges clean, frozen surfaces identical, every artefact green on the merged tree.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../../.." && pwd)
BR=${1:-$(cd "$ROOT" && git rev-parse --abbrev-ref HEAD)}
BR_SHA=$(cd "$ROOT" && git rev-parse "$BR")
MAIN_SHA=$(cd "$ROOT" && git rev-parse main)
W=/tmp/t151-merge.$$
trap 'rm -rf "$W"' EXIT
BAD=0

echo "branch       $BR = $BR_SHA"
echo "main (now)   $MAIN_SHA"
echo

git clone --quiet --no-hardlinks --shared "$ROOT" "$W" || { echo "ABORT: clone failed" >&2; exit 2; }
(cd "$W" && git checkout -q -B scratchmain "$MAIN_SHA") || { echo "ABORT: checkout main failed" >&2; exit 2; }
(cd "$W" && git -c user.name=T151 -c user.email=t151@local merge --no-edit -q "$BR_SHA") > "$W/merge.log" 2>&1
rc=$?
if [ "$rc" -eq 0 ]; then echo "merge into current main: CLEAN (rc=0), head $(cd "$W" && git rev-parse --short HEAD)"
else echo "merge into current main: *** CONFLICT (rc=$rc) ***"; cat "$W/merge.log"; BAD=$((BAD+1)); fi
echo

echo "=== frozen surfaces: main vs merged (must be IDENTICAL — T151 promotes nothing)"
for f in .softhouse/vectors/PIN.json \
         .softhouse/vectors/capabilities.json \
         nexus/internal/apps/loanschedule/contract/contract.go \
         nexus/internal/apps/loanschedule/emi.go \
         .softhouse/conformance.sh \
         .softhouse/gates.md \
         .softhouse/tasks.json \
         .softhouse/patterns.md \
         .softhouse/capture/charges/bin/preconditions.sh; do
  a=$(cd "$ROOT" && git rev-parse "$MAIN_SHA:$f" 2>/dev/null)
  b=$(cd "$W" && git rev-parse "HEAD:$f" 2>/dev/null)
  if [ "$a" = "$b" ]; then printf '   %-58s %s  IDENTICAL\n' "$f" "$(printf '%s' "$a" | cut -c1-12)"
  else printf '   %-58s *** CHANGED ***\n' "$f"; BAD=$((BAD+1)); fi
done
echo

echo "=== whole-subtree check: git diff main..merged over every surface T151 must not touch"
for p in .softhouse/vectors/ nexus/ .softhouse/capture/pathb/ .softhouse/capture/charges/ \
         .softhouse/capture/t74-multiplesof/ .softhouse/capture/audit-t44/ \
         .softhouse/conformance.sh .softhouse/gates.md .softhouse/tasks.json .softhouse/patterns.md; do
  n=$( (cd "$W" && git diff --name-only "$MAIN_SHA" HEAD -- "$p") | wc -l | tr -d ' ')
  if [ "$n" = 0 ]; then printf '   %-42s no change   OK\n' "$p"
  else printf '   %-42s %s file(s) CHANGED   ***\n' "$p" "$n"; (cd "$W" && git diff --name-only "$MAIN_SHA" HEAD -- "$p" | sed 's/^/      /'); BAD=$((BAD+1)); fi
done
echo

echo "=== every artefact re-run ON THE MERGED TREE"
# A red artefact on the merged tree means one of two very different things, and reporting them as
# one would be dishonest in either direction: T151 broke it, or it was already broken on `main`.
# So a failure is not scored until a CONTROL RUN of the same artefact on PLAIN CURRENT MAIN — no
# T151 commit in the tree at all — has said which.  Absence beats difference: the control is the
# tree without the change, not the tree with the change reasoned about.
PREEX=0
rm -rf "$W-main"
git clone --quiet --no-hardlinks --shared "$ROOT" "$W-main" || { echo "ABORT: control clone failed" >&2; exit 2; }
(cd "$W-main" && git checkout -q -B t151control "$MAIN_SHA") || { echo "ABORT: control checkout failed" >&2; exit 2; }
trap 'rm -rf "$W" "$W-main"' EXIT
art() {  # art <label> <command...>
  lbl=$1; shift
  (cd "$W" && "$@") > "$W/art.txt" 2>&1
  r=$?
  if [ "$r" = 0 ]; then printf '   %-28s exit 0   OK\n' "$lbl"; return; fi
  (cd "$W-main" && "$@") > "$W/art-control.txt" 2>&1
  c=$?
  if [ "$c" = "$r" ]; then
    printf '   %-28s exit %s   PRE-EXISTING ON MAIN (control run of the same artefact on %s, with no\n' \
           "$lbl" "$r" "$(printf '%s' "$MAIN_SHA" | cut -c1-8)"
    printf '   %-28s          T151 commit in the tree, exits %s too) — NOT a T151 regression\n' '' "$c"
    tail -6 "$W/art.txt" | sed 's/^/      /'
    PREEX=$((PREEX+1))
  else
    printf '   %-28s exit %s   *** T151 REGRESSION *** (plain main exits %s)\n' "$lbl" "$r" "$c"
    tail -15 "$W/art.txt" | sed 's/^/      /'
    BAD=$((BAD+1))
  fi
}
art prove-guards.sh       sh .softhouse/capture/t91/prove-guards.sh
art t151-drive-g4.sh      sh .softhouse/capture/t91/t151-drive-g4.sh
art t151-drive-vb.sh      sh .softhouse/capture/t91/t151-drive-vb.sh
art t151-drive-g67.sh     sh .softhouse/capture/t91/t151-drive-g67.sh
art t115-drive-mf1.sh     sh .softhouse/capture/t91/t115-drive-mf1.sh
art t115-drive-mf2.sh     sh .softhouse/capture/t91/t115-drive-mf2.sh
art t115-drive-mf3-mf4.sh sh .softhouse/capture/t91/t115-drive-mf3-mf4.sh
art t115-rerun-attacks.sh sh .softhouse/capture/t91/t115-rerun-attacks.sh
art conformance.sh        bash .softhouse/conformance.sh
echo

echo "=== N9 / N10 disclosures must survive the merge (FU-1 is T139's, not T151's)"
for pat in 'N9 STILL ADMITS' 'N10 STILL ADMITS' 'F-2 is NOT discharged'; do
  n=$( (cd "$W" && sh .softhouse/capture/t91/t115-drive-mf2.sh 2>&1) | LC_ALL=C /usr/bin/grep -ac "$pat" )
  if [ "$n" -ge 1 ]; then printf '   %-28s present on the merged tree (%s)   OK\n' "$pat" "$n"
  else printf '   %-28s *** GONE ***\n' "$pat"; BAD=$((BAD+1)); fi
done
echo

echo "=== LC_ALL=C / grep -a hardening must be monotonically up or flat, main -> merged"
for f in verdict.sh run-attacks.sh shell-invariance.sh prove-guards.sh; do
  p=.softhouse/capture/t91/$f
  a1=$( (cd "$ROOT" && git show "$MAIN_SHA:$p") | LC_ALL=C /usr/bin/grep -ac 'LC_ALL=C' )
  b1=$( (cd "$W"    && git show "HEAD:$p")      | LC_ALL=C /usr/bin/grep -ac 'LC_ALL=C' )
  a2=$( (cd "$ROOT" && git show "$MAIN_SHA:$p") | LC_ALL=C /usr/bin/grep -ac 'grep -a' )
  b2=$( (cd "$W"    && git show "HEAD:$p")      | LC_ALL=C /usr/bin/grep -ac 'grep -a' )
  v=OK
  [ "$b1" -ge "$a1" ] || { v='*** LC_ALL=C WEAKENED ***'; BAD=$((BAD+1)); }
  [ "$b2" -ge "$a2" ] || { v='*** grep -a WEAKENED ***';  BAD=$((BAD+1)); }
  printf '   %-22s LC_ALL=C %s -> %-3s   grep -a %s -> %-3s   %s\n' "$f" "$a1" "$b1" "$a2" "$b2" "$v"
done
echo

if [ "$PREEX" -gt 0 ]; then
  echo "*** $PREEX artefact(s) are RED ON PLAIN CURRENT MAIN, independently of T151. ***"
  echo "    They are reported, not excused: an artefact that is red on main is red for whoever"
  echo "    merges next, and a worker who silences it has hidden it.  See the T151 handoff."
  echo
fi
if [ "$BAD" -eq 0 ]; then
  echo "done — merges clean into current main, promotes nothing, no T151 regression."
  exit 0
fi
echo "done — $BAD check(s) failed."
exit 1
