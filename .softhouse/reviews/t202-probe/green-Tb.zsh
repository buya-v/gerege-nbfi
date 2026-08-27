#!/bin/zsh
# T202 GREEN for T-b, plus the T172 ANCHOR REGRESSION re-run against the
# CURRENT bytes.  Variants:
#   PRE  = shipped pre-fix guard (sed -n '239,254p' of main's file)
#   POST = patched guard         (sed -n '313,348p' of the branch file)
#   BA   = POST but pathspec left cwd-relative  (the original defect)
#   BB   = POST but the commit rc unchecked     ("rescued" printed anyway)
#   BC   = POST but ADD_RC read from the wrong command
set -uo pipefail
S=/tmp/t202/tb
STAMP=GREENTB-000000
LOGBUF=""
log() { LOGBUF="$LOGBUF$*"$'\n'; }
PASS=0; FAIL=0; CHECKED=0
ck() { (( CHECKED++ ))
  if [[ "$4" == "$5" ]]; then (( PASS++ )); print -r -- "    ok   [$1/$2] $3 = $5"
  else (( FAIL++ )); print -r -- "    FAIL [$1/$2] $3: expected $4, got $5"; fi }

build() {   # build <shape>
  rm -rf "$S"; mkdir -p "$S"
  cd "$S" || exit 1
  git init -q -b main
  mkdir -p .softhouse docs tools/deep
  print -r -- baseline > .softhouse/tasks.json
  print -r -- baseline > docs/baseline.md
  print -r -- baseline > tools/deep/keep.txt
  print -r -- '{"holder":"local-launchd"}' > .softhouse/LOCK
  git add -A
  git -c user.name=t202 -c user.email=t202@example.com commit -q -m baseline
  case "$1" in
    dirty)  print -r -- "a whole DEC-1 retry" > docs/T999-handoff.md
            print -r -- "vector capture"      > .softhouse/vector.json ;;
    clean)  : ;;
    lockonly) print -r -- churn >> .softhouse/LOCK ;;
    hookfail) # `git add` SUCCEEDS but `git commit` FAILS (a pre-commit hook).
            print -r -- "a whole DEC-1 retry" > docs/T999-handoff.md
            print -r -- '#!/bin/sh\nexit 1' > .git/hooks/pre-commit
            chmod +x .git/hooks/pre-commit ;;
    addfail)  # `git add` itself FAILS: index.lock held by someone else.
            print -r -- "a whole DEC-1 retry" > docs/T999-handoff.md
            print -r -- held > .git/index.lock ;;
    t172)   # T172's anchor regression: siblings merely PREFIXED by the LOCK path
            print -r -- churn >> .softhouse/LOCK
            print -r -- "genuine work" > .softhouse/LOCKED_STATE.md
            print -r -- "genuine work" > .softhouse/LOCK.bak
            mkdir -p .softhouse/LOCKDIR; print -r -- w > .softhouse/LOCKDIR/f.md ;;
  esac
}
run_variant() { local B=$1 shape=$2 where=$3
  build "$shape"; LOGBUF=""
  cd "$where" || return
  rg() { source "$B" }
  rg
  cd "$S" 2>/dev/null || cd /tmp }
has() { [[ "$LOGBUF" == *"$1"* ]] && print yes || print no }
head_moved() { [[ "$(git -C "$S" log --oneline -1 --format=%s)" == *"rescue uncommitted"* ]] && print yes || print no }
committed() { git -C "$S" show --name-only --format= HEAD 2>/dev/null }
incommit() { [[ "$(committed)" == *"$1"* ]] && print yes || print no }
stilldirty() { local o; o=$(git -C "$S" status --porcelain -- ':(top)'); [[ "$o" == *"$1"* ]] && print yes || print no }

for V in PRE POST BA BB BC; do
  case $V in
    PRE)  B=/tmp/t202/prefix-guard.zsh ;;
    POST) B=/tmp/t202/postfix-guard.zsh ;;
    *)    B=/tmp/t202/mut-$V.zsh ;;
  esac
  print -r -- "== variant $V ($B) =="

  # B1 dirty tree, cwd = REPO ROOT -> rescue really happens
  run_variant $B dirty "$S"
  ck $V B1-root "rescue commit made"        yes "$(head_moved)"
  ck $V B1-root "said rescued"              yes "$(has 'rescued: committed')"
  ck $V B1-root "deliverable in the commit" yes "$(incommit 'docs/T999-handoff.md')"

  # B2 dirty tree, cwd = SUBDIRECTORY -> must still rescue, or say it did not
  run_variant $B dirty "$S/tools/deep"
  ck $V B2-subdir "rescue commit made"          yes "$(head_moved)"
  ck $V B2-subdir "deliverable in the commit"   yes "$(incommit 'docs/T999-handoff.md')"
  ck $V B2-subdir "deliverable no longer dirty" no  "$(stilldirty 'T999-handoff.md')"
  ck $V B2-subdir "never claims a rescue it did not make" \
        "$(head_moved)" "$(has 'rescued: committed')"

  # B3 clean tree -> silence, no false alarm
  run_variant $B clean "$S"
  ck $V B3-clean "rescue commit made" no "$(head_moved)"
  ck $V B3-clean "ERROR logged"       no "$(has 'ERROR')"

  # B4 only LOCK dirty -> guard excludes it, stays silent (T190's Q4 property)
  run_variant $B lockonly "$S"
  ck $V B4-lockonly "rescue commit made" no "$(head_moved)"

  # B5 T172 ANCHOR REGRESSION, re-run against the CURRENT bytes:
  #    siblings merely PREFIXED by `.softhouse/LOCK` must survive and be rescued,
  #    while the real LOCK must stay out of the commit.
  run_variant $B t172 "$S"
  ck $V B5-t172 "LOCKED_STATE.md rescued" yes "$(incommit '.softhouse/LOCKED_STATE.md')"
  ck $V B5-t172 "LOCK.bak rescued"        yes "$(incommit '.softhouse/LOCK.bak')"
  ck $V B5-t172 "LOCKDIR/f.md rescued"    yes "$(incommit '.softhouse/LOCKDIR/f.md')"
  ck $V B5-t172 "real LOCK NOT committed" no  "$(incommit '.softhouse/LOCK
')"
  # B6 add succeeds, COMMIT fails (pre-commit hook) -> must NOT claim a rescue
  run_variant $B hookfail "$S"
  ck $V B6-hookfail "rescue commit made"     no  "$(head_moved)"
  ck $V B6-hookfail "said rescued"           no  "$(has 'rescued: committed')"
  ck $V B6-hookfail "named the COMMIT as the failure" yes "$(has 'COMMIT FAILED')"

  # B7 `git add` itself fails (index.lock held) -> must name the ADD, not the commit
  run_variant $B addfail "$S"
  ck $V B7-addfail "rescue commit made"      no  "$(head_moved)"
  ck $V B7-addfail "said rescued"            no  "$(has 'rescued: committed')"
  ck $V B7-addfail "named the ADD as the failure" yes "$(has 'could not stage the leftovers')"

  print -r -- ""
done
print -r -- "CHECKS INSPECTED=$CHECKED  PASS=$PASS  FAIL=$FAIL"
(( CHECKED > 0 )) || { print -r -- "ERROR: zero checks inspected (P-35)"; exit 3 }
