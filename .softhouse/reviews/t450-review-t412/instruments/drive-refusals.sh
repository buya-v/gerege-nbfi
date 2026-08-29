#!/bin/bash
# T450 -- independent re-drive of the T412 gate's refusal and allow arms.
# Every arm asserts BOTH the rc AND a string the gate itself printed (P-22 / the author's
# own run-1 lesson: an exit code alone cannot tell "allowed" from "never asked").
set -u
C=/tmp/t450/clone2
OUT=/tmp/t450/refusals
rm -rf "$OUT"; mkdir -p "$OUT"
cd "$C" || exit 9
BASE=$(git rev-parse drive)
PASS=0; FAIL=0

reset() {
  rm -rf /tmp/t450/remote2.git
  git init -q --bare /tmp/t450/remote2.git
  git checkout -q -B drive "$BASE"
  git clean -qfdx -e .git >/dev/null 2>&1
  git reset -q --hard "$BASE"
}

run_arm() { # $1 name  $2 expected_rc  $3 marker  [$4 extra push args]
  local n="$1" want="$2" marker="$3"; shift 3
  git push "$@" bare HEAD:refs/heads/main >"$OUT/$n.txt" 2>&1
  local rc=$?
  echo "PUSH_RC=$rc" >>"$OUT/$n.txt"
  local mk=MISSING
  if LC_ALL=C grep -qF "$marker" "$OUT/$n.txt"; then mk=PRESENT; fi
  if [ "$rc" -eq "$want" ] && [ "$mk" = PRESENT ]; then
    printf 'ARM %-28s EXPECT rc=%s GOT rc=%s  marker[%s] %s  PASS\n' "$n" "$want" "$rc" "$marker" "$mk"
    PASS=$((PASS+1))
  else
    printf 'ARM %-28s EXPECT rc=%s GOT rc=%s  marker[%s] %s  ***FAIL***\n' "$n" "$want" "$rc" "$marker" "$mk"
    FAIL=$((FAIL+1))
  fi
}

commit() { git -c user.name=T450 -c user.email=t450@local commit -q "$@"; }

########## R1 / R2 -- gitlink, without and with a bypass reason
reset
BLOB=$(git rev-parse "$BASE")
git update-index --add --cacheinfo 160000,"$BLOB",strayworktree
git -c user.name=T450 -c user.email=t450@local commit -q -m "T450 R1: a gitlink in the tree"
run_arm R1-gitlink 1 "C1 REFUSED -- THE PUSHED TREE CONTAINS A GITLINK"
SOFTHOUSE_DRIVER_GATE_BYPASS="a deliberate stray worktree, allegedly" \
  run_arm R2-gitlink-bypass 1 "THERE IS NO BYPASS FOR C1"

########## R3 / R4 / R5 -- outside the driver allowlist
reset
mkdir -p nexus/internal/apps/t450probe
printf 'package t450probe\n' > nexus/internal/apps/t450probe/probe.go
git add nexus/internal/apps/t450probe/probe.go
commit -m "T450 R3: a non-merge commit writing outside the driver allowlist"
run_arm R3-outside-allowlist 1 "C2 REFUSED -- a NON-MERGE commit"
SOFTHOUSE_DRIVER_GATE_BYPASS="T450 review drive: deliberate out-of-allowlist push" \
  run_arm R4-allowlist-bypass 0 "BYPASSED: C2 allowlist"
SOFTHOUSE_DRIVER_GATE_BYPASS="ok" \
  run_arm R5-short-bypass 1 "C2 REFUSED -- a NON-MERGE commit"
cp .git/softhouse-driver-gate/bypass.log "$OUT/bypass.log" 2>/dev/null || echo "no bypass.log" > "$OUT/bypass.log"

########## R6 -- instance 1 exactly: an undefined P-number in a DIRECTIVE file
reset
printf '\nT450 review probe, per P-150.\n' >> .softhouse/RESUME.md
git add .softhouse/RESUME.md
commit -m "T450 R6: P-150 in RESUME.md (instance 1)"
run_arm R6-bad-citation 1 "C3 REFUSED -- THE CHEAP SUBSET FAILED ON THE PUSHED TREE"

########## R7 -- a DELETION inside the STATE set
reset
git rm -q .softhouse/gates-proposed-answers.md
commit -m "T450 R7: delete a state .md"
run_arm R7-deletion 1 "C3 REFUSED -- THE PUSHED TREE WAS NEVER GRADED"

########## R8 -- HONEST WORK MUST BE ALLOWED (P-98: a gate that refuses everything is broken too)
reset
printf '\nT450 review probe %s: an honest state note.\n' "$(date -u +%s)" >> .softhouse/RESUME.md
git add .softhouse/RESUME.md
commit -m "T450 R8: an honest state-only edit"
run_arm R8-honest-allowed 0 "C3 PASS -- cheap subset clean"

########## R9 -- --no-verify walks straight past the gate
reset
git update-index --add --cacheinfo 160000,"$BLOB",strayworktree
git -c user.name=T450 -c user.email=t450@local commit -q -m "T450 R9: the same gitlink, pushed with --no-verify"
git push --no-verify bare HEAD:refs/heads/main >"$OUT/R9-no-verify.txt" 2>&1
rc=$?
echo "PUSH_RC=$rc" >>"$OUT/R9-no-verify.txt"
echo "--- gate output present? ---" >>"$OUT/R9-no-verify.txt"
LC_ALL=C grep -c 'driver-push-gate' "$OUT/R9-no-verify.txt" >>"$OUT/R9-no-verify.txt"
echo "--- does the pushed tree carry a gitlink? ---" >>"$OUT/R9-no-verify.txt"
git --git-dir=/tmp/t450/remote2.git ls-tree -r refs/heads/main 2>/dev/null | awk '$1=="160000"' >>"$OUT/R9-no-verify.txt"
if [ "$rc" -eq 0 ]; then
  echo "ARM R9-no-verify              rc=0: THE GITLINK PUSH SUCCEEDED, gate never ran.  (finding, not a pass)"
else
  echo "ARM R9-no-verify              rc=$rc: --no-verify did NOT get through."
fi

reset
printf 'arms passed: %s   arms failed: %s\n' "$PASS" "$FAIL"
echo DONE > /tmp/t450/refusals-done.txt
